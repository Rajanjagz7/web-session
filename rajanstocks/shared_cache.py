"""Cross-instance cache + lock on Upstash Redis.

Vercel runs several server instances and each used to keep its own in-memory cache, so every cold instance re-downloaded
the same daily candles from Upstox (218 calls for the Picks screen alone). Data that does not change during the day now
lives here once and every instance reads it. Without Redis credentials everything degrades to "miss" (callers just fetch).
Values are JSON, zlib-compressed and base64-encoded (Upstash caps a request at ~1 MB).

Without Redis credentials the same calls fall back to small files on disk (".cache" next to the code, or /tmp on
Vercel), so a local restart does not re-download every daily candle from Upstox either. Locks stay "always granted".
"""
import base64
import builtins
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
import uuid
import zlib

_DISK = os.environ.get("RJ_CACHE_DIR") or (os.path.join("/tmp", "rj_cache") if os.environ.get("VERCEL")
                                            else os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache"))


def _file(key):
    return os.path.join(_DISK, hashlib.sha1(key.encode()).hexdigest() + ".z")


def _disk_get(key):
    try:
        with open(_file(key), "rb") as f:
            d = json.loads(zlib.decompress(f.read()).decode())
        if d["exp"] < time.time():
            try:
                os.remove(_file(key))
            except OSError:
                pass
            return None
        return d["v"]
    except Exception:
        return None


def _disk_set(key, value, ttl):
    try:
        os.makedirs(_DISK, exist_ok=True)
        tmp = _file(key) + ".tmp"
        with open(tmp, "wb") as f:
            f.write(zlib.compress(json.dumps({"exp": time.time() + ttl, "v": value}, separators=(",", ":")).encode(), 6))
        os.replace(tmp, _file(key))
    except Exception:
        pass


def sweep(max_age_days=3):
    """Delete expired / old cache files. Returns how many were removed."""
    n = 0
    try:
        for name in os.listdir(_DISK):
            fp = os.path.join(_DISK, name)
            try:
                if name.endswith(".tmp") or time.time() - os.path.getmtime(fp) > max_age_days * 86400:
                    os.remove(fp)
                    n += 1
            except OSError:
                pass
    except OSError:
        pass
    return n


def _creds():
    # URL and token always from the SAME pair - mixing UPSTASH_* with KV_* (two databases) gives WRONGPASS
    e = os.environ.get
    for u, t in (("UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN"), ("KV_REST_API_URL", "KV_REST_API_TOKEN")):
        if e(u) and e(t):
            return (e(u), e(t))
    return None


def enabled():
    return _creds() is not None


def _pipe(cmds, timeout=4.0):
    return kv(cmds, timeout)


# ---- primary + backup Upstash databases (automatic failover) ----
# BACKUP_UPSTASH_REDIS_REST_URL / _TOKEN = a second database. When the primary refuses (request limit, outage) the app
# switches to the backup on its own, re-checks the primary every 10 minutes, and when it answers again merges the saved
# state back into it and switches back. While the primary works, every save of the saved state is copied to the backup too,
# so a switch never starts from an old copy.
_FO = {"on": False, "until": 0.0, "since": None, "why": ""}
_LIMIT = ("limit exceeded", "max requests", "max daily", "rate limit")


def _backup_creds():
    # BACKUP_UPSTASH_* (added by hand) or BACKUP_KV_REST_API_* (Vercel Storage "Connect" with custom prefix BACKUP)
    url = os.environ.get("BACKUP_UPSTASH_REDIS_REST_URL") or os.environ.get("BACKUP_KV_REST_API_URL")
    tok = os.environ.get("BACKUP_UPSTASH_REDIS_REST_TOKEN") or os.environ.get("BACKUP_KV_REST_API_TOKEN")
    if not (url and tok) or (_creds() and url.rstrip("/") == _creds()[0].rstrip("/")):
        return None                                  # missing, or accidentally the same database as the primary
    return (url, tok)


def _refused(res):
    return any(isinstance(x, dict) and x.get("error") and any(m in str(x["error"]).lower() for m in _LIMIT) for x in res or [])


def _mirror(b, cmds):
    w = [c for c in cmds if c and c[0] in ("SET",) and len(c) > 1 and c[1] in STATE_KEYS]
    if b and w:
        try:
            _pipe_to(b, w, 4.0)
        except Exception:
            pass


def _resync(src, dst):
    """Merge the saved state from src into dst (used when switching back to the primary). Any read error = do nothing."""
    try:
        a, b2 = _pipe_to(src, [["GET", k] for k in STATE_KEYS]), _pipe_to(dst, [["GET", k] for k in STATE_KEYS])
        if any(x.get("error") for x in a) or any(y.get("error") for y in b2):
            _FO["resyncErr"] = "read: " + str([x.get("error") for x in a + b2 if x.get("error")])[:200]
            return False                             # never write over data we could not read
        cmds = []
        for k, x, y in zip(STATE_KEYS, a, b2):
            new, old = x.get("result"), y.get("result")
            if new and old:
                if new != old:
                    cmds.append(["SET", k, json.dumps(_merge_state(k, json.loads(old), json.loads(new)))])
            elif new:
                cmds.append(["SET", k, new])
        if cmds:
            r = _pipe_to(dst, cmds)
            if any(x.get("error") for x in r):
                _FO["resyncErr"] = "write: " + str([x.get("error") for x in r if x.get("error")])[:200] + \
                    " sizes " + str({c[1]: len(c[2]) for c in cmds})
                return False
        _FO["resyncErr"] = None
        return True
    except Exception as e:
        _FO["resyncErr"] = "exception: " + str(e)[:200]
        return False


FO_FLAG = "rajanone:fo:v1"      # kept in the BACKUP while it holds data the primary has not merged yet (survives restarts)
_FO_CHECKED = {"done": False}


def _flag_check(p, b):
    """Once per server instance: if an earlier instance switched to the backup, finish the switch-back merge here."""
    if _FO_CHECKED["done"]:
        return
    _FO_CHECKED["done"] = True
    try:
        f = _pipe_to(b, [["GET", FO_FLAG]], 3.0)[0].get("result")
    except Exception:
        return
    if not f:
        return
    try:
        r = _pipe_to(p, [["PING"]], 3.0)
        _FO["primaryPing"] = str(r[0].get("result") or r[0].get("error"))[:160] if r else None
        if not _refused(r) and r and r[0].get("result") == "PONG" and _resync(b, p):
            _pipe_to(b, [["DEL", FO_FLAG]], 3.0)
            print("[kv] primary is back - merged the backup's saved state into it")
            return
    except Exception as e:
        _FO["primaryPing"] = "exception: " + str(e)[:160]
    _FO.update(on=True, until=time.time() + 600, since=_FO["since"] or time.time(), why="primary still refusing (flag)")


def kv(cmds, timeout=6.0):
    """Run Redis commands on the active database: the primary, or the backup while the primary is refusing."""
    p, b = _creds(), _backup_creds()
    if not p:
        raise RuntimeError("no Redis configured")
    now = time.time()
    if b:
        _flag_check(p, b)
    if _FO["on"] and b:
        if now >= _FO["until"]:                                    # time to try the primary again
            try:
                r = _pipe_to(p, [["PING"]], 3.0)
                if not _refused(r) and r and r[0].get("result") == "PONG" and _resync(b, p):
                    _FO.update(on=False, since=None, why="")
                    try:
                        _pipe_to(b, [["DEL", FO_FLAG]], 3.0)
                    except Exception:
                        pass
            except Exception:
                pass
            if _FO["on"]:
                _FO["until"] = now + 600
        if _FO["on"]:
            return _pipe_to(b, cmds, timeout)
    err = None
    try:
        r = _pipe_to(p, cmds, timeout)
        if not _refused(r):
            _mirror(b, cmds)
            return r
        err = next((x.get("error") for x in r if isinstance(x, dict) and x.get("error")), "refused")
    except Exception as e:
        if not b:
            raise
        err, r = str(e)[:160], None
    if not b:
        return r
    first = not _FO["on"]
    _FO.update(on=True, until=now + 600, since=_FO["since"] or now, why=str(err)[:160])
    print(f"[kv] primary refused ({err}) - using the backup database")
    cmds2 = ([["SET", FO_FLAG, str(int(now))]] if first else []) + list(cmds)   # remember the switch (survives restarts)
    res = _pipe_to(b, cmds2, timeout)
    return res[1:] if first else res


def kv_status():
    return {"active": "backup" if _FO["on"] else "primary", "backupConfigured": bool(_backup_creds()),
            "switchBackError": _FO.get("resyncErr"), "primaryPing": _FO.get("primaryPing"),
            "since": _FO["since"], "why": _FO["why"], "backupSetup": _backup_setup(),
            "commandsThisInstance": {"total": _CMDS["total"], "minutes": round((time.time() - _CMDS["since"]) / 60),
                                     "top": dict(sorted(_CMDS["by"].items(), key=lambda x: -x[1])[:12])}}


def _ping_backup():
    """One PING to the backup: 'ok', or the error text (e.g. WRONGPASS = wrong token)."""
    b = _backup_creds()
    if not b:
        return None
    try:
        r = _pipe_to(b, [["PING"]], 4.0)[0]
        return "ok" if r.get("result") == "PONG" else str(r.get("error"))[:120]
    except Exception as e:
        return str(e)[:120]


def _backup_setup():
    """Which backup settings Vercel passed in - names and checks only, never the values."""
    e = os.environ.get
    url = e("BACKUP_UPSTASH_REDIS_REST_URL") or e("BACKUP_KV_REST_API_URL") or ""
    p = _creds()
    return {"urlSet": bool(url), "tokenSet": bool(e("BACKUP_UPSTASH_REDIS_REST_TOKEN") or e("BACKUP_KV_REST_API_TOKEN")),
            "urlLooksRight": url.startswith("https://") and ".upstash.io" in url,
            "sameAsPrimary": bool(url and p and url.rstrip("/") == p[0].rstrip("/")),
            "backupAnswers": _ping_backup(),
            "backupNames": sorted(k for k in os.environ if k.startswith("BACKUP"))}


def _enc(v):
    return base64.b64encode(zlib.compress(json.dumps(v, separators=(",", ":")).encode(), 6)).decode()


def _dec(s):
    return json.loads(zlib.decompress(base64.b64decode(s)).decode())


# Upstash budget (free plan: 500K commands a month). Only values that are expensive to rebuild AND worth sharing between
# server copies go to Redis; everything else (prices, candles, quote copies, observer, research proxy) stays in this
# instance's memory + /tmp disk. Durable state (auto trader, stock trader, push) uses its own keys, not this module.
REMOTE_PREFIXES = ("picks|", "picks:cash|", "ipo:", "bt:")
REMOTE_LOCKS = ("auto-cycle", "stockbot-cycle", "signal-push")
_MEM = {}


def _remote_key(k):
    return enabled() and k.startswith(REMOTE_PREFIXES)


def _mem_get(k):
    h = _MEM.get(k)
    if h and h[0] > time.time():
        return h[1]
    if h:
        _MEM.pop(k, None)
    v = _disk_get(k)
    return v


def get_many(keys):
    """{key: value} for the keys that exist. Shared keys: one Redis command however many keys; the rest: memory / disk."""
    keys = list(keys)
    if not keys:
        return {}
    out = {}
    remote = []
    for k in keys:
        v = _mem_get(k)
        if v is not None:
            out[k] = v
        elif _remote_key(k):
            remote.append(k)
    if remote:
        try:
            res = _pipe([["MGET", *["sc:" + k for k in remote]]])[0].get("result") or []
            for k, v in zip(remote, res):
                if v:
                    out[k] = _dec(v)
                    _MEM[k] = (time.time() + 120, out[k])         # 2 min local copy: repeat reads cost nothing
        except Exception:
            pass
    return out


def get(key):
    return get_many([key]).get(key)


def set_many(items, ttl):
    """items: {key: value}. Failures are ignored: the cache is an optimisation."""
    if not items:
        return
    remote = {}
    for k, v in items.items():
        _MEM[k] = (time.time() + min(int(ttl), 3600), v)
        if _remote_key(k):
            remote[k] = v
        elif not enabled() or len(json.dumps(v, separators=(",", ":"))) > 2000:   # no Redis: disk is the shared layer
            _disk_set(k, v, ttl)
    if len(_MEM) > 4000:                                           # keep memory bounded
        for k in sorted(_MEM, key=lambda x: _MEM[x][0])[:1000]:
            _MEM.pop(k, None)
    if remote:
        try:
            _pipe([["SET", "sc:" + k, _enc(v), "EX", int(ttl)] for k, v in remote.items()])
        except Exception:
            pass


def set(key, value, ttl):
    set_many({key: value}, ttl)


# ───────────── versioned state books (lost-update guard) ─────────────
# A state book (auto trader, share trader, push subscriptions) is one JSON text under one key and every instance used to read it,
# change it and write it back whole: whoever saved last silently erased the other's change (a manual exit, a new trade, a push
# subscription). The book now starts with a version token ({"ver": "<16 hex>", ...}); a save first reads that token back (GETRANGE of the
# first bytes, not the whole book) and refuses to write when somebody saved after this copy was read.
_VER_RE = re.compile(r'^\{"ver": "([0-9a-f]{8,32})"')


def ver_of(raw):
    """The version token a stored book starts with (None for a book saved before versions existed)."""
    m = _VER_RE.match(raw or "")
    return m.group(1) if m else None


def strip_ver(raw):
    return re.sub(r'^\{"ver": "[0-9a-f]+", ?', "{", raw or "", count=1)


def read_ver(key):
    """(known, ver) of the book as it is stored right now. known is False when the store could not answer: the check is then skipped."""
    try:
        j = kv([["GETRANGE", key, 0, 60]], 6.0)[0]
    except Exception:
        return False, None
    if not isinstance(j, dict) or j.get("error"):
        return False, None
    return True, ver_of(j.get("result") or "")


def cached_raw(key, rc, ttl=60.0, verify=False):
    """The book text this instance read less than `ttl` seconds ago, or None when it has to be read again. With verify=True the stored
    version is compared first (one tiny GETRANGE): another instance may have saved since - a closed trade, a new mark - and serving this
    instance's older copy made the Journal's totals flip between two values on every refresh. If the store cannot answer the check, the copy is used."""
    raw = rc.get("raw")
    if raw is None or time.time() - rc.get("t", 0) >= ttl:
        return None
    if verify:
        known, cur = read_ver(key)
        if known and cur != ver_of(raw):
            return None
    return raw


def versioned_set(key, rest, rc, ver0, timeout=8.0):
    """Write `rest` (the book without its version) if nobody saved since version `ver0` was read. rc is the caller's cache dict whose
    'raw' holds the text last read or written. Returns ("ok", new_ver) | ("same", ver0) | ("conflict", None) | ("error", message)."""
    if strip_ver(rc.get("raw")) == json.dumps(rest):
        return "same", ver0
    known, cur = read_ver(key)
    if known and cur != ver0:
        return "conflict", None
    new = uuid.uuid4().hex[:16]
    body = json.dumps({"ver": new, **rest})                 # the version is the FIRST key, so GETRANGE can read it cheaply
    j = kv([["SET", key, body]], timeout)[0]
    if j.get("error"):
        return "error", str(j["error"])
    rc.update(t=time.time(), raw=body)
    return "ok", new


def lock(name, ttl_s):
    """True if THIS caller now owns the lock (SET NX EX). Without Redis the lock is always granted."""
    if not enabled() or name not in REMOTE_LOCKS:
        h = _MEM.get("lock:" + name)                                # local lock: enough for caches, free of Redis calls
        if h and h[0] > time.time():
            return False
        _MEM["lock:" + name] = (time.time() + ttl_s, 1)
        return True
    try:
        return _pipe([["SET", "sl:" + name, str(time.time()), "NX", "EX", int(ttl_s)]])[0].get("result") == "OK"
    except Exception:
        return True            # Redis hiccup: do not block trading logic


def unlock(name):
    """Remote locks are NOT deleted: they expire by themselves within a minute and cycles run minutes apart,
    so the DEL was a wasted Upstash command per cycle."""
    _MEM.pop("lock:" + name, None)


def fetch(key, ttl, fn):
    """Return the shared value for key, else compute it with fn() and share it. A falsy result is never stored."""
    v = get(key)
    if v is not None:
        return v
    v = fn()
    if v:
        set(key, v, ttl)
    return v


def diagnose():
    """Read-only health check of the shared store (no keys or tokens are returned)."""
    if not _creds():
        return {"configured": False}
    import time as _t
    out = {"configured": True}
    t0 = _t.time()
    try:
        out["failover"] = kv_status()
        bk = _backup_creds()
        if bk:
            try:
                rb = _pipe_to(bk, [["PING"], ["DBSIZE"]], 4.0)
                out["backup"] = {"ping": rb[0].get("result"), "keys": rb[1].get("result"), "errors": [x.get("error") for x in rb if x.get("error")]}
            except Exception as e:
                out["backup"] = {"error": str(e)[:160]}
        r = _pipe_to(_creds(), [["PING"], ["DBSIZE"], ["EXISTS", "rajanone:auto:v1"], ["EXISTS", "rajanone:push:v1"], ["EXISTS", "rajanone:stockbot:v1"]], 4.0)
        out.update(ok=True, ms=int((_t.time() - t0) * 1000), ping=r[0].get("result"), keys=r[1].get("result"),
                   autoState=r[2].get("result"), pushState=r[3].get("result"), stockState=r[4].get("result"),
                   errors=[x.get("error") for x in r if x.get("error")])
    except urllib.error.HTTPError as e:
        out.update(ok=False, status=e.code, error=e.read().decode(errors="replace")[:300])
    except Exception as e:
        out.update(ok=False, error=str(e)[:300])
    return out


# ---- one-time move of the saved state to a new Upstash database ----
def _active_creds():
    """The database commands currently route to: the primary, or the backup while the primary is refusing."""
    p, b = _creds(), _backup_creds()
    return b if (p and b and _FO.get("on")) else p


def cleanup_prefix(match, budget_s=20.0):
    """Delete keys matching `match` (e.g. 'bhav:day|') from the ACTIVE database (failover-aware).
    About 2 commands per 1000 keys."""
    import time as _t
    c = _active_creds()
    if not c:
        return {"ok": False, "reason": "no Upstash configured"}
    t0, cur, n = _t.time(), "0", 0
    try:
        while True:
            r = _pipe_to(c, [["SCAN", cur, "MATCH", match + "*", "COUNT", 1000]])[0]
            if r.get("error"):
                return {"ok": False, "deleted": n, "reason": r["error"][:160]}
            cur, keys = r["result"][0], [k for k in r["result"][1] if k.startswith(match)]
            if keys:
                _pipe_to(c, [["DEL", *keys]]); n += len(keys)
            if cur == "0":
                return {"ok": True, "deleted": n, "done": True}
            if _t.time() - t0 > budget_s:
                return {"ok": True, "deleted": n, "done": False, "next": "call again to continue"}
    except Exception as e:
        return {"ok": False, "deleted": n, "reason": str(e)[:160]}


def cleanup_junk(budget_s=20.0):
    """Delete leftover rate-limit counters (rl2:*) from the PRIMARY database. Only keys starting with rl2: are touched.
    About 2 commands per 1000 keys. Call again until done is True."""
    return cleanup_prefix("rl2:", budget_s)


STATE_KEYS = ("rajanone:auto:v1" + os.environ.get("AUTO_BOOK_SUFFIX", ""), "rajanone:push:v1", "rajanone:stockbot:v1")   # auto trader, push subscriptions, stock trader


def _old_creds():
    url, tok = os.environ.get("OLD_UPSTASH_REDIS_REST_URL"), os.environ.get("OLD_UPSTASH_REDIS_REST_TOKEN")
    return (url, tok) if url and tok else None


_CMDS = {"since": time.time(), "total": 0, "by": {}}       # Upstash commands sent by THIS server instance (diagnostics)


def _count(cmds):
    for c in cmds:
        if not c:
            continue
        k = str(c[1]) if len(c) > 1 else ""
        kind = c[0] + " " + (k.split(":")[0] + ":" if ":" in k else k.split("|")[0] + "|" if "|" in k else k)[:24]
        _CMDS["by"][kind] = _CMDS["by"].get(kind, 0) + 1
        _CMDS["total"] += 1


def _pipe_to(creds, cmds, timeout=8.0):
    _count(cmds)
    url, tok = creds
    req = urllib.request.Request(url.rstrip("/") + "/pipeline", data=json.dumps(cmds).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _merge_state(key, old, new):
    """Old + new state in one: trades by id (the newer copy wins), push subscriptions and daily counters united, logs joined."""
    m = dict(old)
    m.update({k: v for k, v in new.items() if k not in ("trades", "log", "subs", "sent", "sentT", "seen", "cfg", "resetAt")})
    if "cfg" in old or "cfg" in new:                 # settings: the copy the user changed last (a fresh default never wins)
        oc, nc = old.get("cfg") or {}, new.get("cfg") or {}
        m["cfg"] = nc if (nc.get("cfgAt") or 0) > (oc.get("cfgAt") or 0) else (oc or nc)
    reset_at = max(str(old.get("resetAt") or ""), str(new.get("resetAt") or ""))
    if reset_at:
        m["resetAt"] = reset_at
    if "trades" in old or "trades" in new:
        def same(a, b):
            return (a.get("sym"), a.get("openedAt") or a.get("date"), a.get("entry")) == (b.get("sym"), b.get("openedAt") or b.get("date"), b.get("entry"))
        by = {t.get("id"): t for t in old.get("trades") or []}
        for t in new.get("trades") or []:
            i = t.get("id")
            if i in by and not same(by[i], t):       # two different trades got the same number in the two databases: keep both
                t = dict(t, id=f"{i}-b")
            by[t.get("id")] = t
        trades = list(by.values())
        if reset_at:                                 # a portfolio reset on either side clears what was opened before it
            trades = [t for t in trades if str(t.get("openedAt") or t.get("date") or "") >= reset_at[:len(str(t.get("openedAt") or t.get("date") or ""))]]
        m["trades"] = sorted(trades, key=lambda t: str(t.get("openedAt") or t.get("date") or ""))
    if "log" in old or "log" in new:
        m["log"] = sorted((old.get("log") or []) + (new.get("log") or []), key=lambda x: str(x.get("at") or ""))[-200:]
    if "subs" in old or "subs" in new:
        m["subs"] = {**(old.get("subs") or {}), **(new.get("subs") or {})}
    for d in ("sent", "sentT"):
        if d in old or d in new:
            m[d] = {**(old.get(d) or {}), **(new.get(d) or {})}
    if "seen" in old or "seen" in new:
        S = builtins.set                            # this module defines its own set() (cache write)
        days = S(old.get("seen") or {}) | S(new.get("seen") or {})
        m["seen"] = {day: sorted(S((old.get("seen") or {}).get(day, [])) | S((new.get("seen") or {}).get(day, []))) for day in days}
    if "seq" in old or "seq" in new:
        m["seq"] = max(old.get("seq") or 0, new.get("seq") or 0)
    return m


def migrate_state(overwrite=False):
    """Copy the saved state keys from the OLD database (OLD_UPSTASH_REDIS_REST_URL / _TOKEN) into the current one.
    Never overwrites a key that already has data in the new database unless overwrite=True. Returns what happened per key
    (sizes only - no contents, no tokens)."""
    old, new = _old_creds(), _creds()
    if not old or not new:
        return {"ok": False, "reason": "set OLD_UPSTASH_REDIS_REST_URL and OLD_UPSTASH_REDIS_REST_TOKEN (old database) next to the new UPSTASH_* values"}
    if old[0].rstrip("/") == new[0].rstrip("/"):
        return {"ok": False, "reason": "old and new database are the same"}
    try:
        got = _pipe_to(old, [["GET", k] for k in STATE_KEYS])
    except Exception as e:
        return {"ok": False, "reason": f"old database not reachable: {str(e)[:120]}"}
    errs = [g.get("error") for g in got if g.get("error")]
    if errs:
        return {"ok": False, "reason": f"old database refused the read (still over its limit?): {errs[0][:160]}"}
    have = _pipe_to(new, [["GET", k] for k in STATE_KEYS])
    out, cmds = {}, []
    for k, g, h in zip(STATE_KEYS, got, have):
        raw, cur = g.get("result"), h.get("result")
        if not raw:
            out[k] = "nothing saved in the old database"
        elif cur and not overwrite:
            try:                                   # both have data: MERGE, so nothing from either database is lost
                merged = _merge_state(k, json.loads(raw), json.loads(cur))
                cmds.append(["SET", k, json.dumps(merged)])
                out[k] = "merged old + new"
            except Exception as e:
                out[k] = f"kept new only (could not merge: {str(e)[:80]})"
        else:
            cmds.append(["SET", k, raw])
            out[k] = f"copied ({len(raw):,} bytes)"
    if cmds:
        res = _pipe_to(new, cmds)
        bad = [r.get("error") for r in res if r.get("error")]
        if bad:
            return {"ok": False, "reason": f"new database refused the write: {bad[0][:160]}", "keys": out}
    return {"ok": True, "keys": out}

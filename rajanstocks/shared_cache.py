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
import time
import urllib.error
import urllib.request
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
    url = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
    tok = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")
    return (url, tok) if url and tok else None


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
    """Merge the saved state from src into dst (used when switching back to the primary)."""
    try:
        a, b2 = _pipe_to(src, [["GET", k] for k in STATE_KEYS]), _pipe_to(dst, [["GET", k] for k in STATE_KEYS])
        cmds = []
        for k, x, y in zip(STATE_KEYS, a, b2):
            new, old = x.get("result"), y.get("result")
            if new and old and not y.get("error"):
                cmds.append(["SET", k, json.dumps(_merge_state(k, json.loads(old), json.loads(new)))])
            elif new:
                cmds.append(["SET", k, new])
        if cmds:
            _pipe_to(dst, cmds)
        return True
    except Exception:
        return False


def kv(cmds, timeout=6.0):
    """Run Redis commands on the active database: the primary, or the backup while the primary is refusing."""
    p, b = _creds(), _backup_creds()
    if not p:
        raise RuntimeError("no Redis configured")
    now = time.time()
    if _FO["on"] and b:
        if now >= _FO["until"]:                                    # time to try the primary again
            try:
                r = _pipe_to(p, [["PING"]], 3.0)
                if not _refused(r) and r and r[0].get("result") == "PONG" and _resync(b, p):
                    _FO.update(on=False, since=None, why="")
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
    _FO.update(on=True, until=now + 600, since=_FO["since"] or now, why=str(err)[:160])
    print(f"[kv] primary refused ({err}) - using the backup database")
    return _pipe_to(b, cmds, timeout)


def kv_status():
    return {"active": "backup" if _FO["on"] else "primary", "backupConfigured": bool(_backup_creds()),
            "since": _FO["since"], "why": _FO["why"]}


def _enc(v):
    return base64.b64encode(zlib.compress(json.dumps(v, separators=(",", ":")).encode(), 6)).decode()


def _dec(s):
    return json.loads(zlib.decompress(base64.b64decode(s)).decode())


# Upstash budget (free plan: 500K commands a month). Only values that are expensive to rebuild AND worth sharing between
# server copies go to Redis; everything else (prices, candles, quote copies, observer, research proxy) stays in this
# instance's memory + /tmp disk. Durable state (auto trader, stock trader, push) uses its own keys, not this module.
REMOTE_PREFIXES = ("picks|", "ipo:")
REMOTE_LOCKS = ("auto-cycle", "stockbot-cycle")
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
    _MEM.pop("lock:" + name, None)
    if enabled() and name in REMOTE_LOCKS:
        try:
            _pipe([["DEL", "sl:" + name]])
        except Exception:
            pass


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
STATE_KEYS = ("rajanone:auto:v1", "rajanone:push:v1", "rajanone:stockbot:v1")   # auto trader, push subscriptions, stock trader


def _old_creds():
    url, tok = os.environ.get("OLD_UPSTASH_REDIS_REST_URL"), os.environ.get("OLD_UPSTASH_REDIS_REST_TOKEN")
    return (url, tok) if url and tok else None


def _pipe_to(creds, cmds, timeout=8.0):
    url, tok = creds
    req = urllib.request.Request(url.rstrip("/") + "/pipeline", data=json.dumps(cmds).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _merge_state(key, old, new):
    """Old + new state in one: trades by id (the newer copy wins), push subscriptions and daily counters united, logs joined."""
    m = dict(old)
    m.update({k: v for k, v in new.items() if k not in ("trades", "log", "subs", "sent", "sentT", "seen")})
    if "trades" in old or "trades" in new:
        by = {t.get("id"): t for t in old.get("trades") or []}
        by.update({t.get("id"): t for t in new.get("trades") or []})
        m["trades"] = sorted(by.values(), key=lambda t: str(t.get("openedAt") or t.get("date") or ""))
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

"""Server-side trade-signal push notifications (Chrome / any Web Push browser).

Flow
  1. The page subscribes (existing "Enable push" switch) and POSTs the subscription to /api/push/subscribe.
  2. Every 5 minutes in market hours a cycle collects fresh BUY / SELL ideas:
        - index option calls  (BUY CALL / BUY PUT where chart + option flow agree)
        - strong stock / index picks (strength >= 75)
        - strategy flips that happened today (Trend Target Ribbon, RJ Best, Dual-Phase Reversal, ...)
  3. Ideas are de-duplicated for the day and sent best-first, never more than MAX_PER_DAY (5) pushes
     per device per IST day.

Where it runs
  - Own machine / VPS: a background thread runs the cycle (started from server.py).
  - Vercel: /api/cron/signal-push is called by Vercel Cron (see vercel.json). Vercel's disk is not
    durable, so subscriptions and the daily counter are kept in Upstash / Vercel KV when
    UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN (or KV_REST_API_URL + KV_REST_API_TOKEN) are set.
    Without it the state lives in a file, which is fine locally but resets on serverless cold starts.
"""
import json
import os
import threading
import time
from datetime import datetime, timedelta, timezone

import requests
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from push_api import _host_ok

IST = timezone(timedelta(hours=5, minutes=30))
router = APIRouter()

MAX_PER_DAY = int(os.environ.get("PUSH_MAX_PER_DAY", "2"))     # idea pushes; the rest of the 5-a-day total is kept for the auto trader's entries
MAX_LOCK_PER_DAY = int(os.environ.get("PUSH_MAX_LOCK_PER_DAY", "0"))    # "stop moved / profit locked" phone alerts: OFF by default (user 29 Oct: a push for every lock is irritating) - they stay in the app
MAX_TOTAL_PER_DAY = int(os.environ.get("PUSH_MAX_TOTAL_PER_DAY", "10"))   # HARD limit (30 Oct: 10, was 5, for testing): phone pushes per device per day, ALL kinds together (ideas + trades + locks)
MAX_TRADE_PER_DAY = int(os.environ.get("PUSH_MAX_TRADE_PER_DAY", "10"))   # user: at most 5 phone pushes a day (the auto trader's first 5 trades); after that it trades silently
CYCLE_SECONDS = 300
STATE_KEY = "rajanone:push:v1"
STATE_FILE = os.path.join(os.environ.get("BHAV_CACHE_WRITE_DIR") or os.path.dirname(__file__), "push_state.json")
STRATEGY_KEYS = ("rajan-ha-momentum", "rajan-trend-rider", "ut-bot")   # daily strategies kept by the 20 Oct 2026 audit
_lock = threading.Lock()


# ───────────────────────── state (Upstash / file) ─────────────────────────

def _remote():
    import shared_cache                                   # one place decides the URL+token pair (never mixed)
    return shared_cache._creds()


def _empty():
    return {"subs": {}, "sent": {}, "seen": {}, "log": []}


_RC = {}


def _load():
    r = _remote()
    try:
        if r:
            import shared_cache
            j = shared_cache.kv([["GET", STATE_KEY]], 8.0)[0]          # primary, or the backup database
            if j.get("error"):                                      # store refused (e.g. request limit): never treat as "empty"
                raise RuntimeError(f"state store error: {j.get('error')}")
            raw = j.get("result")
            _RC.update(t=time.time(), raw=raw)
            st = json.loads(raw) if raw else _empty()
            st["_ver0"] = shared_cache.ver_of(raw)                  # the version this copy was read at (checked again when it is saved)
            return st
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return _empty()
    except Exception as e:
        print(f"[push-signals] state load failed: {e}")
        st = _empty()
        st["_readonly"] = True                                      # a failed read must never be saved over the real state
        return st


def _save(st, merge=True):
    """True = saved; False = the store refused / the state was not read; "conflict" = another instance saved after this copy was read.
    With merge=True a conflict is resolved here: the newest book is read again and this copy's day counters, seen ids, log and
    subscriptions are united with it (no push is sent twice, nobody's subscription is lost) and the save is retried."""
    if st.get("_readonly"):
        print("[push-signals] state was not read - not saving")
        return False
    today = datetime.now(IST).date()
    keep = {(today - timedelta(days=i)).isoformat() for i in range(3)}
    st["sent"] = {d: v for d, v in st["sent"].items() if d in keep}
    st["seen"] = {d: v for d, v in st["seen"].items() if d in keep}
    st["log"] = st["log"][-60:]
    r = _remote()
    try:
        if r:
            import shared_cache
            for _ in range(3):
                rest = {k: v for k, v in st.items() if k not in ("ver", "_ver0")}
                res, info = shared_cache.versioned_set(STATE_KEY, rest, _RC, st.get("_ver0"))
                if res in ("ok", "same"):
                    if res == "ok":
                        st["_ver0"] = info
                    return True
                if res == "error":
                    print(f"[push-signals] state save refused: {info}")
                    return False
                if not merge:
                    return "conflict"
                fresh = _load()
                if fresh.get("_readonly"):
                    return False
                merged = shared_cache._merge_state(STATE_KEY, fresh, {k: v for k, v in st.items() if k != "_ver0"})
                merged["_ver0"] = fresh.get("_ver0")
                st.clear()
                st.update(merged)
            return "conflict"
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({k: v for k, v in st.items() if k != "_ver0"}, f)
        os.replace(tmp, STATE_FILE)
        return True
    except Exception as e:
        print(f"[push-signals] state save failed: {e}")
        return False


def _mutate(apply, tries=3):
    """Subscribe / unsubscribe: change a fresh copy of the book and redo the change on the newest one if another instance saved meanwhile
    (a plain merge would bring an unsubscribed device back)."""
    for attempt in range(tries):
        with _lock:
            st = _load()
            if st.get("_readonly"):
                raise HTTPException(503, "Push state is not readable right now - try again in a moment")
            apply(st)
            res = _save(st, merge=False)
        if res is True:
            return True
        if res is False:
            raise HTTPException(503, "Push state could not be saved right now - try again in a moment")
        time.sleep(0.2 * (attempt + 1))
    raise HTTPException(409, "Push state changed while saving - please try again")


# ───────────────────────── collecting ideas ─────────────────────────

def _inr(v):
    return f"{v:,.2f}" if isinstance(v, (int, float)) else "-"


def market_hours(now=None):
    n = now or datetime.now(IST)
    m = n.hour * 60 + n.minute
    return __import__("nse_calendar").is_trading_day(n.date()) and 9 * 60 + 15 <= m <= 15 * 60 + 30


def collect(today=None):
    """Fresh BUY / SELL ideas, best first. Every idea has a stable id used for same-day de-duplication."""
    import market_api
    import strategies_api

    today = today or datetime.now(IST).date().isoformat()
    out = []

    try:
        for c in market_api.day_calls().get("calls", []):
            if c.get("signal") in ("BUY CALL", "BUY PUT"):
                out.append({
                    "id": f"{today}|{c['instrument']}|calls|{c['signal']}", "rank": 1000 + (c.get("strength") or 0),
                    "side": "BUY", "sym": c["instrument"], "source": "Index option call",
                    "title": f"{c['signal']} · {c.get('contract')}",
                    "body": f"Entry ₹{_inr(c.get('entry'))} · SL ₹{_inr(c.get('stopLoss'))} · T1 ₹{_inr(c.get('target1'))} · "
                            f"T2 ₹{_inr(c.get('target2'))}. Chart and option flow agree.",
                })
    except Exception as e:
        print(f"[push-signals] index calls failed: {e}")

    top = []
    try:
        picks = market_api.picks().get("picks", [])
        strong = sorted([p for p in picks if p.get("signal") in ("BUY", "SELL") and (p.get("strength") or 0) >= 75],
                        key=lambda p: -(p.get("strength") or 0))
        top = strong[:8]
        for p in strong[:10]:
            why = (p.get("reasons") or [""])[0]
            out.append({
                "id": f"{today}|{p['s']}|picks|{p['signal']}", "rank": 500 + (p.get("strength") or 0),
                "side": p["signal"], "sym": p["s"], "source": "Pick",
                "title": f"{p['signal']} {p['s']} @ ₹{_inr(p.get('entry'))}",
                "body": f"SL ₹{_inr(p.get('stop'))} · T1 ₹{_inr(p.get('target'))} · T2 ₹{_inr(p.get('target2'))} · "
                        f"R:R 1:{p.get('rr', 1.5)}" + (f" · {why}" if why else ""),
            })
    except Exception as e:
        print(f"[push-signals] picks failed: {e}")

    syms = list(dict.fromkeys(["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"] + [p["s"] for p in top]))
    keys = [k for k in STRATEGY_KEYS if k in strategies_api.META]
    deadline = time.time() + (18 if os.environ.get("VERCEL") else 80)   # serverless caps a request at 30s

    def one(job):
        key, sym = job
        if time.time() > deadline:
            return None
        try:
            r = strategies_api.run(key, sym)
        except Exception:
            return None
        sig = r.get("signal")
        if sig not in ("BUY", "SELL") or r.get("stale") or r.get("date") != today:
            return None
        return {
            "id": f"{today}|{sym}|{key}|{sig}", "rank": 100, "side": sig, "sym": sym, "source": r.get("name"),
            "title": f"{sig} {sym} · {r.get('name')}", "body": str(r.get("headline") or "")[:200],
        }

    import concurrent.futures as cf
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        for item in ex.map(one, [(k, s) for s in syms for k in keys]):
            if item:
                out.append(item)

    out.sort(key=lambda x: -x["rank"])
    return out


# ───────────────────────── sending ─────────────────────────

def _send(sub, title, body, url="/#picks", tag=None):
    priv = os.environ.get("VAPID_PRIVATE_KEY")
    if not priv:
        return "no-key"
    if not _host_ok(sub.get("endpoint", "")):
        return "gone"
    try:
        from pywebpush import webpush
        webpush(subscription_info=sub,
                data=json.dumps({"title": title[:120], "body": body[:300], "url": url, "tag": tag, "critical": False}),
                vapid_private_key=priv,
                vapid_claims={"sub": os.environ.get("VAPID_SUBJECT", "https://rajanstocks.vercel.app")}, ttl=900)
        return "ok"
    except Exception as e:
        code = getattr(getattr(e, "response", None), "status_code", None)
        return "gone" if code in (404, 410) else f"error:{code or str(e)[:80]}"


PUSH_FROM_AUTO_ONLY = False     # 29 Oct (user: 'both'): the 5 best signal ideas a day are pushed AND the auto trader's entries / stop moves (own budgets)


def run_cycle(force=False, dry=False):
    now = datetime.now(IST)
    if PUSH_FROM_AUTO_ONLY and not dry:
        return {"ran": False, "reason": "recommendation pushes are sent when the auto trader enters a trade"}
    if not force and not market_hours(now):
        return {"ran": False, "reason": "market closed"}
    import shared_cache
    if not dry and not shared_cache.lock("signal-push", 90):      # two runs at once (cron + tick) sent the same ideas twice, one second apart
        return {"ran": False, "reason": "another run is in progress"}
    with _lock:
        st = _load()
        subs = st["subs"]
        today = now.date().isoformat()
        if not subs and not dry:
            return {"ran": False, "reason": "no subscribers"}
        cands = collect(today)
        seen = set(st["seen"].setdefault(today, []))
        sent_by = st["sent"].setdefault(today, {})
        fresh = [c for c in cands if c["id"] not in seen]
        report = {"ran": True, "candidates": len(cands), "fresh": len(fresh), "sent": [], "dry": dry}
        for c in fresh:
            if dry:
                report["sent"].append({"id": c["id"], "title": c["title"], "body": c["body"], "rank": c["rank"]})
                continue
            delivered = False
            for ep, rec in list(subs.items()):
                if sent_by.get(ep, 0) >= MAX_PER_DAY or _day_total(st, today, ep) >= MAX_TOTAL_PER_DAY:
                    continue
                res = _send(rec["sub"], c["title"], c["body"], tag=c["id"])
                if res == "ok":
                    sent_by[ep] = sent_by.get(ep, 0) + 1
                    delivered = True
                elif res == "gone":
                    subs.pop(ep, None)
                elif res == "no-key":
                    report["reason"] = "VAPID_PRIVATE_KEY is not set on this server"
            if delivered:
                seen.add(c["id"])
                st["log"].append({"at": now.isoformat(), "id": c["id"], "title": c["title"]})
                report["sent"].append({"id": c["id"], "title": c["title"]})
            if subs and all(sent_by.get(ep, 0) >= MAX_PER_DAY or _day_total(st, today, ep) >= MAX_TOTAL_PER_DAY for ep in subs):
                break
        st["seen"][today] = sorted(seen)
        if not dry:
            _save(st)
        return report


def _day_total(st, today, ep):
    """Everything this device was sent today: ideas + trade entries + lock alerts."""
    return sum(int((st.get(k) or {}).get(today, {}).get(ep, 0)) for k in ("sent", "sentT", "sentL"))


FRESH_PUSH_DAY = "2026-10-29"
NO_LIMIT_DAY = "2026-10-29"      # user 29 Oct: test day - trade-entry pushes are not limited today; the 5-a-day limit applies from tomorrow
PUSH_BUCKETS = {"index": 2, "stock": 3}   # user: 5 trade pushes a day = 2 index-option + 3 stock-option trades


def notify_all(idem, title, body, url="/#journal", kind="trade", bucket=None):
    """One push to every subscribed device, never the same id twice. Trade events (auto entries, profit locks, exits) use
    their own daily budget (MAX_TRADE_PER_DAY): they used to share the 5-a-day recommendation cap, so the first five 09:15
    entries used it up and no exit / stop alert could be sent for the rest of the day."""
    now = datetime.now(IST)
    today = now.date().isoformat()
    with _lock:
        st = _load()
        if today == FRESH_PUSH_DAY and st.get("freshPush") != FRESH_PUSH_DAY:     # one-time (user 29 Oct 12:06): the morning's alerts used the 5-a-day budget - the fresh start gets its own
            for k_ in ("sentT", "sentL", "sent", "sentB", "seen"):
                (st.get(k_) or {}).pop(today, None)
            st["freshPush"] = FRESH_PUSH_DAY
        seen = set(st["seen"].setdefault(today, []))
        if idem in seen:
            return 0
        if kind == "trade":
            sent_by, cap = st.setdefault("sentT", {}).setdefault(today, {}), MAX_TRADE_PER_DAY
            for d in [d for d in st["sentT"] if d < today]:
                st["sentT"].pop(d, None)
        elif kind == "lock":
            sent_by, cap = st.setdefault("sentL", {}).setdefault(today, {}), MAX_LOCK_PER_DAY
            for d in [d for d in st["sentL"] if d < today]:
                st["sentL"].pop(d, None)
        else:
            sent_by, cap = st["sent"].setdefault(today, {}), MAX_PER_DAY
        free = today == NO_LIMIT_DAY and kind in ("trade", "lock")
        if free:
            cap = 10 ** 6
        if bucket in PUSH_BUCKETS and not free:           # per-kind daily budget (2 index + 3 stock option trades)
            bk = st.setdefault("sentB", {})
            for d in [d for d in bk if d < today]:
                bk.pop(d, None)
            used = bk.setdefault(today, {})
            if used.get(bucket, 0) >= PUSH_BUCKETS[bucket]:
                return 0
        n = 0
        for ep, rec in list(st["subs"].items()):
            if sent_by.get(ep, 0) >= cap or (not free and _day_total(st, today, ep) >= MAX_TOTAL_PER_DAY):
                continue
            res = _send(rec["sub"], title, body, url=url, tag=idem)
            if res == "ok":
                sent_by[ep] = sent_by.get(ep, 0) + 1
                n += 1
            else:
                st["lastFail"] = {"at": now.isoformat(), "id": idem, "result": res}      # why a push did not arrive (shown by /api/push/signals)
                if res == "gone":
                    st["subs"].pop(ep, None)
        if not st["subs"]:
            st["lastFail"] = {"at": now.isoformat(), "id": idem, "result": "no subscribed device - turn 'Enable push' off and on again on the phone"}
        if n:
            if bucket in PUSH_BUCKETS and not free:
                st["sentB"][today][bucket] = st["sentB"][today].get(bucket, 0) + 1
            seen.add(idem)
            st["seen"][today] = sorted(seen)
            st["log"].append({"at": now.isoformat(), "id": idem, "title": title})
        _save(st)
        return n


# ───────────────────────── API ─────────────────────────

class SubBody(BaseModel):
    subscription: dict


@router.post("/api/push/subscribe")
def subscribe(b: SubBody):
    ep = (b.subscription or {}).get("endpoint", "")
    if not _host_ok(ep):
        raise HTTPException(400, "Unsupported push service.")

    def apply(st):
        st["subs"][ep] = {"sub": b.subscription, "at": datetime.now(IST).isoformat()}
        if len(st["subs"]) > 200:
            for k in list(st["subs"])[:-200]:
                st["subs"].pop(k, None)
    _mutate(apply)
    return {"ok": True, "maxPerDay": MAX_PER_DAY}


@router.post("/api/push/unsubscribe")
def unsubscribe(b: SubBody):
    ep = (b.subscription or {}).get("endpoint", "")
    _mutate(lambda st: st["subs"].pop(ep, None))
    return {"ok": True}


@router.get("/api/push/signals")
def status():
    st = _load()
    today = datetime.now(IST).date().isoformat()
    return {
        "subscribers": len(st["subs"]), "maxPerDay": MAX_PER_DAY, "maxTradePerDay": MAX_TRADE_PER_DAY, "maxTotalPerDay": MAX_TOTAL_PER_DAY,
        "sentToday": {"signals": len(st["sent"].get(today, {})), "tradeEvents": sum((st.get("sentT") or {}).get(today, {}).values()), "lockEvents": sum((st.get("sentL") or {}).get(today, {}).values())},
        "lastFail": st.get("lastFail"), "recent": st["log"][-10:], "configured": bool(os.environ.get("VAPID_PRIVATE_KEY")),
        "durableStore": bool(_remote()), "marketHours": market_hours(),
    }


@router.get("/api/push/signals/preview")
def preview():
    """What the next cycle would send right now (nothing is sent or recorded)."""
    return run_cycle(force=True, dry=True)


@router.api_route("/api/cron/signal-push", methods=["GET", "POST"])
def cron(authorization: str = Header(default=""), only: str = ""):
    secret = os.environ.get("CRON_SECRET")
    if secret and authorization != f"Bearer {secret}":
        raise HTTPException(401, "Unauthorized")
    if only != "push":                                    # ?only=push: just the signal pushes (the auto trader has its own tick, /api/cron/auto-cycle)
        try:
            import auto_trader
            auto_trader.run_cycle()
        except Exception as e:
            print(f"[cron] auto_trader cycle failed: {e}")
    return run_cycle()


def start_watcher():
    """Own-server mode: run a cycle every 5 minutes. (On Vercel the cron endpoint does this.)"""
    if os.environ.get("VERCEL"):
        return

    def loop():
        time.sleep(20)
        while True:
            try:
                r = run_cycle()
                if r.get("ran") and r.get("sent"):
                    print(f"[push-signals] sent {len(r['sent'])}: " + "; ".join(x["title"] for x in r["sent"]))
            except Exception as e:
                print(f"[push-signals] cycle failed: {e}")
            time.sleep(CYCLE_SECONDS)

    threading.Thread(target=loop, daemon=True, name="push-signals").start()

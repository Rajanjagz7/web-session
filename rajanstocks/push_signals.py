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

MAX_PER_DAY = int(os.environ.get("PUSH_MAX_PER_DAY", "5"))
MAX_TRADE_PER_DAY = int(os.environ.get("PUSH_MAX_TRADE_PER_DAY", "40"))   # trade events (entry / profit lock / exit) have their own budget
CYCLE_SECONDS = 300
STATE_KEY = "rajanone:push:v1"
STATE_FILE = os.path.join(os.environ.get("BHAV_CACHE_WRITE_DIR") or os.path.dirname(__file__), "push_state.json")
STRATEGY_KEYS = ("rajan-ha-momentum", "rajan-trend-rider", "ut-bot")   # daily strategies kept by the 20 Oct 2026 audit
_lock = threading.Lock()


# ───────────────────────── state (Upstash / file) ─────────────────────────

def _remote():
    url = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
    tok = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")
    return (url, tok) if url and tok else None


def _empty():
    return {"subs": {}, "sent": {}, "seen": {}, "log": []}


def _load():
    r = _remote()
    try:
        if r:
            resp = requests.post(r[0], headers={"Authorization": f"Bearer {r[1]}"}, json=["GET", STATE_KEY], timeout=8)
            raw = resp.json().get("result")
            return json.loads(raw) if raw else _empty()
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return _empty()
    except Exception as e:
        print(f"[push-signals] state load failed: {e}")
        return _empty()


def _save(st):
    today = datetime.now(IST).date()
    keep = {(today - timedelta(days=i)).isoformat() for i in range(3)}
    st["sent"] = {d: v for d, v in st["sent"].items() if d in keep}
    st["seen"] = {d: v for d, v in st["seen"].items() if d in keep}
    st["log"] = st["log"][-60:]
    r = _remote()
    try:
        if r:
            requests.post(r[0], headers={"Authorization": f"Bearer {r[1]}"},
                          json=["SET", STATE_KEY, json.dumps(st)], timeout=8)
        else:
            tmp = STATE_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(st, f)
            os.replace(tmp, STATE_FILE)
    except Exception as e:
        print(f"[push-signals] state save failed: {e}")


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


PUSH_FROM_AUTO_ONLY = True      # the 5 daily recommendation pushes are the auto trader's executed trades


def run_cycle(force=False, dry=False):
    now = datetime.now(IST)
    if PUSH_FROM_AUTO_ONLY and not dry:
        return {"ran": False, "reason": "recommendation pushes are sent when the auto trader enters a trade"}
    if not force and not market_hours(now):
        return {"ran": False, "reason": "market closed"}
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
                if sent_by.get(ep, 0) >= MAX_PER_DAY:
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
            if subs and all(sent_by.get(ep, 0) >= MAX_PER_DAY for ep in subs):
                break
        st["seen"][today] = sorted(seen)
        if not dry:
            _save(st)
        return report


def notify_all(idem, title, body, url="/#journal", kind="trade"):
    """One push to every subscribed device, never the same id twice. Trade events (auto entries, profit locks, exits) use
    their own daily budget (MAX_TRADE_PER_DAY): they used to share the 5-a-day recommendation cap, so the first five 09:15
    entries used it up and no exit / stop alert could be sent for the rest of the day."""
    now = datetime.now(IST)
    today = now.date().isoformat()
    with _lock:
        st = _load()
        seen = set(st["seen"].setdefault(today, []))
        if idem in seen:
            return 0
        if kind == "trade":
            sent_by, cap = st.setdefault("sentT", {}).setdefault(today, {}), MAX_TRADE_PER_DAY
            for d in [d for d in st["sentT"] if d < today]:
                st["sentT"].pop(d, None)
        else:
            sent_by, cap = st["sent"].setdefault(today, {}), MAX_PER_DAY
        n = 0
        for ep, rec in list(st["subs"].items()):
            if sent_by.get(ep, 0) >= cap:
                continue
            res = _send(rec["sub"], title, body, url=url, tag=idem)
            if res == "ok":
                sent_by[ep] = sent_by.get(ep, 0) + 1
                n += 1
            elif res == "gone":
                st["subs"].pop(ep, None)
        if n:
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
    with _lock:
        st = _load()
        st["subs"][ep] = {"sub": b.subscription, "at": datetime.now(IST).isoformat()}
        if len(st["subs"]) > 200:
            for k in list(st["subs"])[:-200]:
                st["subs"].pop(k, None)
        _save(st)
    return {"ok": True, "maxPerDay": MAX_PER_DAY}


@router.post("/api/push/unsubscribe")
def unsubscribe(b: SubBody):
    ep = (b.subscription or {}).get("endpoint", "")
    with _lock:
        st = _load()
        st["subs"].pop(ep, None)
        _save(st)
    return {"ok": True}


@router.get("/api/push/signals")
def status():
    st = _load()
    today = datetime.now(IST).date().isoformat()
    return {
        "subscribers": len(st["subs"]), "maxPerDay": MAX_PER_DAY, "maxTradePerDay": MAX_TRADE_PER_DAY,
        "sentToday": {"signals": len(st["sent"].get(today, {})), "tradeEvents": sum((st.get("sentT") or {}).get(today, {}).values())},
        "recent": st["log"][-10:], "configured": bool(os.environ.get("VAPID_PRIVATE_KEY")),
        "durableStore": bool(_remote()), "marketHours": market_hours(),
    }


@router.get("/api/push/signals/preview")
def preview():
    """What the next cycle would send right now (nothing is sent or recorded)."""
    return run_cycle(force=True, dry=True)


@router.api_route("/api/cron/signal-push", methods=["GET", "POST"])
def cron(authorization: str = Header(default="")):
    secret = os.environ.get("CRON_SECRET")
    if secret and authorization != f"Bearer {secret}":
        raise HTTPException(401, "Unauthorized")
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

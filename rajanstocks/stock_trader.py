"""Stock paper trader - its own Rs 10 lakh, cash stocks only, trading the Picks plans for each holding period.

Entries (09:20-14:30 on NSE trading days; intraday entries until 13:30):
  * For each horizon (intraday / swing / positional) the stocks whose own entry test passes (plans[h].ok, see
    market_api._horizon_fit) are taken in order of that horizon's score, BUY or SELL as the plan says.
  * Up to 3 new trades per horizon per day; at most 6 intraday, 10 swing and 10 positional trades open at once.
    One open trade per stock per horizon.
  * Size: risk 0.5% of capital (Rs 5,000 on Rs 10 L) between entry and stop, position value capped at 10% of capital.
    Capital blocked: delivery buys (swing / positional BUY) the full value; intraday trades and swing / positional SELLs
    (a futures short - cash stocks cannot be held short overnight) 20% margin. Skipped when the free capital is not enough,
    or when the plan's stop is more than 12% away.
Exits:
  * stop, or Target 2; when Target 1 is reached the stop moves to the entry (breakeven).
  * intraday: square off at 15:15. swing: after 15 sessions. positional: after 40 sessions.
  * costs 0.1% of the turnover (both legs).
State is kept in Upstash (same store as the option auto trader). It runs after every option auto-trader cycle and whenever its
status is read in market hours, so no separate scheduler is needed.
"""
import json
import math
import os
import threading
import time
from datetime import date, datetime, timedelta, timezone

import requests
from fastapi import APIRouter, HTTPException

import shared_cache

router = APIRouter(prefix="/api/stockbot")
IST = timezone(timedelta(hours=5, minutes=30))
KEY = "rajanone:stockbot:v1"
FILE = os.path.join(os.environ.get("BHAV_CACHE_WRITE_DIR") or os.path.dirname(__file__), "stockbot_state.json")
HZ = ("intraday", "swing", "positional")
CFG = {"capital": 1000000.0, "riskPct": 0.5, "maxValuePct": 10.0, "marginPct": 20.0, "newPerDay": {"intraday": 3, "swing": 3, "positional": 3},
       "maxOpen": {"intraday": 6, "swing": 10, "positional": 10}, "maxSessions": {"swing": 15, "positional": 40},
       "windowStart": "09:20", "lastEntry": "14:30", "lastIntraday": "13:30", "squareOff": "15:15", "costPct": 0.1}
_lock = threading.Lock()


def _now():
    return datetime.now(IST)


def _hm(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def _mins(now):
    return now.hour * 60 + now.minute


def _remote():
    url = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
    tok = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")
    return (url, tok) if url and tok else None


_RC = {}


def _load(cached=False):
    st = {"trades": [], "log": [], "seq": 0}
    try:
        r = _remote()
        if r:
            raw = _RC.get("raw") if cached and time.time() - _RC.get("t", 0) < 60 else None
            if raw is None:
                j = requests.post(r[0], headers={"Authorization": f"Bearer {r[1]}"}, json=["GET", KEY], timeout=8).json()
                if j.get("error"):
                    raise RuntimeError(f"state store error: {j['error']}")
                raw = j.get("result")
                _RC.update(t=time.time(), raw=raw)
            d = json.loads(raw) if raw else {}
        else:
            with open(FILE, encoding="utf-8") as f:
                d = json.load(f)
        st.update({k: d[k] for k in ("trades", "log", "seq", "lastRun") if k in d})
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[stockbot] load failed: {e}")
        st["_readonly"] = True
    return st


def _save(st):
    if st.get("_readonly"):
        print("[stockbot] state was not read - not saving")
        return
    st["log"] = st["log"][-150:]
    try:
        r = _remote()
        if r:
            body = json.dumps(st)
            if body == _RC.get("raw"):
                return
            j = requests.post(r[0], headers={"Authorization": f"Bearer {r[1]}"}, json=["SET", KEY, body], timeout=8).json()
            if not j.get("error"):
                _RC.update(t=time.time(), raw=body)
        else:
            with open(FILE + ".tmp", "w", encoding="utf-8") as f:
                json.dump(st, f)
            os.replace(FILE + ".tmp", FILE)
    except Exception as e:
        print(f"[stockbot] save failed: {e}")


def _sessions_between(a, b):
    import nse_calendar
    d, n = date.fromisoformat(a), 0
    end = date.fromisoformat(b)
    while d < end:
        d += timedelta(days=1)
        if nse_calendar.is_trading_day(d):
            n += 1
    return n


def _blocked(t):
    full = t["side"] == "BUY" and t["hz"] != "intraday"
    return t["entry"] * t["qty"] * (1 if full else CFG["marginPct"] / 100)


def _cash(st):
    """Free capital: capital + booked P&L - capital blocked by open trades (full value for delivery buys, margin otherwise)."""
    booked = sum(t.get("net", 0) for t in st["trades"] if t["status"] == "CLOSED")
    used = sum(_blocked(t) for t in st["trades"] if t["status"] == "OPEN")
    return CFG["capital"] + booked - used, used, booked


def _quotes(syms):
    """From the shared all-symbols batch (no extra Upstox calls); only symbols outside it are fetched, in one call."""
    import market_api
    try:
        return market_api.quote_map(syms)
    except Exception as e:
        print(f"[stockbot] quotes failed: {e}")
        return {}


def _close(st, t, px, why, now):
    gross = (px - t["entry"]) * t["qty"] * (1 if t["side"] == "BUY" else -1)
    cost = CFG["costPct"] / 100 * (t["entry"] + px) * t["qty"]
    t.update(status="CLOSED", exit=round(px, 2), exitReason=why, closedAt=now.isoformat(), gross=round(gross, 2), cost=round(cost, 2),
             net=round(gross - cost, 2), R=round((gross - cost) / t["risk"], 2) if t.get("risk") else None, last=round(px, 2))
    st["log"].append({"at": now.isoformat(), "msg": f"EXIT {t['hz']} {t['side']} {t['sym']} @ {px:.2f} ({why}) net {t['net']:+.0f}"})


def manage(st, now):
    opens = [t for t in st["trades"] if t["status"] == "OPEN"]
    if not opens:
        return
    q = _quotes([t["sym"] for t in opens])
    today = now.date().isoformat()
    for t in opens:
        x = q.get(t["sym"])
        px = float((x or {}).get("last") or 0)
        if px <= 0:
            continue
        t["last"] = round(px, 2)
        d = 1 if t["side"] == "BUY" else -1
        t["unrealised"] = round(d * (px - t["entry"]) * t["qty"], 2)
        hi, lo = float(x.get("high") or px), float(x.get("low") or px)
        if not t.get("t1Hit") and d * ((hi if d > 0 else lo) - t["t1"]) >= 0:
            t["t1Hit"] = True
            t["stop"] = t["entry"]                                    # Target 1 reached: stop to breakeven
            st["log"].append({"at": now.isoformat(), "msg": f"T1 {t['hz']} {t['sym']} - stop moved to entry {t['entry']}"})
        why = None
        if d * (px - t["stop"]) <= 0:
            why = "BREAKEVEN" if t.get("t1Hit") else "STOP"
        elif d * (px - t["t2"]) >= 0:
            why = "TARGET"
        elif t["hz"] == "intraday" and (t["date"] < today or _mins(now) >= _hm(CFG["squareOff"])):
            why = "SQUARE-OFF"
        elif t["hz"] in CFG["maxSessions"] and _sessions_between(t["date"], today) >= CFG["maxSessions"][t["hz"]]:
            why = "TIME"
        if why:
            _close(st, t, px, why, now)


def enter(st, now):
    import market_api
    today = now.date().isoformat()
    m = _mins(now)
    if not (_hm(CFG["windowStart"]) <= m <= _hm(CFG["lastEntry"])):
        return []
    try:
        P = market_api.picks()
    except Exception as e:
        print(f"[stockbot] picks failed: {e}")
        return []
    picks = [p for p in (P or {}).get("picks") or [] if p.get("kind") != "index" and p.get("plans")]
    if not picks:
        return []
    cash, _, _ = _cash(st)
    risk_amt = CFG["capital"] * CFG["riskPct"] / 100
    max_val = CFG["capital"] * CFG["maxValuePct"] / 100
    entered = []
    q = None
    for hz in HZ:
        if hz == "intraday" and m > _hm(CFG["lastIntraday"]):
            continue
        opened_today = sum(1 for t in st["trades"] if t["hz"] == hz and t["date"] == today)
        open_now = [t for t in st["trades"] if t["hz"] == hz and t["status"] == "OPEN"]
        room = min(CFG["newPerDay"][hz] - opened_today, CFG["maxOpen"][hz] - len(open_now))
        if room <= 0:
            continue
        held = {t["sym"] for t in open_now} | {t["sym"] for t in st["trades"] if t["hz"] == hz and t["date"] == today}
        cands = sorted([p for p in picks if p["plans"][hz].get("ok") and p["plans"][hz].get("side") in ("BUY", "SELL") and p["s"] not in held],
                       key=lambda p: -(p["plans"][hz].get("fit") or 0))[:room * 3]
        if not cands:
            continue
        if q is None:
            q = _quotes([p["s"] for p in picks if any(p["plans"][h].get("ok") for h in HZ)])
        for p in cands:
            if room <= 0:
                break
            pl = p["plans"][hz]
            x = q.get(p["s"]) or {}
            px = float(x.get("last") or 0)
            if px <= 0:
                continue
            d = 1 if pl["side"] == "BUY" else -1
            risk_u = abs(pl["entry"] - pl["stop"])
            stop = px - d * risk_u                                    # same distances as the plan, from the live price
            t1 = px + d * abs(pl["t1"] - pl["entry"])
            t2 = px + d * abs(pl["t2"] - pl["entry"])
            if risk_u > 0.13 * px or t2 <= 0 or t1 <= 0:
                continue                                              # an unrealistic plan is never traded
            per_unit = px * (1 if (d > 0 and hz != "intraday") else CFG["marginPct"] / 100)
            qty = int(min(risk_amt / max(risk_u, 0.01), max_val / px, max(0.0, cash) / per_unit))
            if qty < 1:
                continue
            st["seq"] = st.get("seq", 0) + 1
            t = {"id": f"S-{today.replace('-', '')}-{st['seq']}", "hz": hz, "sym": p["s"], "name": p.get("n") or p["s"], "side": pl["side"],
                 "date": today, "openedAt": now.isoformat(), "entry": round(px, 2), "qty": qty, "stop": round(stop, 2), "stop0": round(stop, 2),
                 "t1": round(t1, 2), "t2": round(t2, 2), "risk": round(risk_u * qty, 2), "why": pl.get("why") or "", "hold": pl.get("hold") or "",
                 "status": "OPEN", "last": round(px, 2), "unrealised": 0.0}
            st["trades"].append(t)
            cash -= per_unit * qty
            room -= 1
            entered.append(t["id"])
            st["log"].append({"at": now.isoformat(), "msg": f"ENTRY {hz} {pl['side']} {qty} {p['s']} @ {px:.2f} · SL {stop:.2f} · T1 {t1:.2f} · T2 {t2:.2f}"})
            try:
                import push_signals
                push_signals.notify_all(f"stock|{t['id']}", f"STOCK {hz.upper()} {pl['side']} · {p['s']}",
                                        f"{qty} @ ₹{px:,.2f} · SL ₹{stop:,.2f} · T1 ₹{t1:,.2f} · T2 ₹{t2:,.2f}", url="/#journal", kind="trade")
            except Exception:
                pass
    return entered


def run_cycle(force=False):
    import nse_calendar
    now = _now()
    if not force and not nse_calendar.session_open(now):
        return {"ran": False, "reason": "market closed"}
    if not shared_cache.lock("stockbot-cycle", 50):
        return {"ran": False, "reason": "another cycle is running"}
    try:
        with _lock:
            st = _load()
            before = {t["id"] for t in st["trades"] if t["status"] == "CLOSED"}
            manage(st, now)
            ent = enter(st, now)
            st["lastRun"] = now.isoformat()
            _save(st)
            return {"ran": True, "entered": ent, "closed": [t["id"] for t in st["trades"] if t["status"] == "CLOSED" and t["id"] not in before]}
    finally:
        shared_cache.unlock("stockbot-cycle")


def _stats(trades):
    closed = [t for t in trades if t["status"] == "CLOSED"]
    wins = [t for t in closed if t["net"] > 0]
    gp, gl = sum(t["net"] for t in wins), -sum(t["net"] for t in closed if t["net"] <= 0)
    return {"closed": len(closed), "open": sum(1 for t in trades if t["status"] == "OPEN"), "wins": len(wins),
            "winRate": round(len(wins) / len(closed) * 100, 1) if closed else None, "net": round(sum(t["net"] for t in closed)),
            "pf": round(gp / gl, 2) if gl > 0 else None, "unrealised": round(sum(t.get("unrealised", 0) for t in trades if t["status"] == "OPEN"))}


@router.get("/status")
def status():
    import nse_calendar
    now = _now()
    st = _load(cached=True)
    last = st.get("lastRun")
    if nse_calendar.session_open(now) and (not last or (now - datetime.fromisoformat(last)).total_seconds() > 180):
        try:
            run_cycle()
            st = _load(cached=True)
        except Exception as e:
            print(f"[stockbot] cycle failed: {e}")
    cash, used, booked = _cash(st)
    unr = sum(t.get("unrealised", 0) for t in st["trades"] if t["status"] == "OPEN")
    return {"capital": CFG["capital"], "cash": round(cash), "used": round(used), "booked": round(booked), "unrealised": round(unr),
            "equity": round(CFG["capital"] + booked + unr), "byHorizon": {h: _stats([t for t in st["trades"] if t["hz"] == h]) for h in HZ},
            "all": _stats(st["trades"]), "open": [t for t in st["trades"] if t["status"] == "OPEN"],
            "closed": [t for t in st["trades"] if t["status"] == "CLOSED"][-200:][::-1], "log": st["log"][-30:][::-1],
            "lastRun": st.get("lastRun"), "rules": __doc__.split("State is kept")[0].strip()}


@router.api_route("/run", methods=["GET", "POST"])
def run():
    return run_cycle()


@router.post("/trade/{tid}/exit")
def manual_exit(tid: str):
    with _lock:
        st = _load()
        t = next((x for x in st["trades"] if x["id"] == tid and x["status"] == "OPEN"), None)
        if not t:
            raise HTTPException(404, "No open trade with that id")
        q = _quotes([t["sym"]]).get(t["sym"]) or {}
        px = float(q.get("last") or t.get("last") or t["entry"])
        _close(st, t, px, "MANUAL", _now())
        _save(st)
        return {"ok": True, "exit": t["exit"], "net": t["net"]}


@router.post("/reset")
def reset():
    if _load().get("_readonly"):
        raise HTTPException(503, "The state store is not answering - reset refused so nothing is lost")
    with _lock:
        _save({"trades": [], "log": [{"at": _now().isoformat(), "msg": "Reset to Rs 10,00,000"}], "seq": 0})
    return {"ok": True}

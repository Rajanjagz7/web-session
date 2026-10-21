"""Automated PAPER executor: no daily entry limit (it used to stop at 5: 3 index + 2 stock options) - every qualifying signal is taken,
one position per symbol at a time, each sized at the same fixed risk.

No broker is involved and no real order is ever sent. Trades are simulated at live option prices.

Rules (identical to the backtest in backtest.py, so results are comparable):
  * Only strategies that PASSED the out-of-sample backtest are used, ranked by in-sample average R.
  * Signal = the fresh BUY/SELL on the last COMPLETED daily bar, acted on from the 09:15 open.
  * BUY -> ATM call, SELL -> ATM put, nearest expiry that is at least 3 days away.
  * Risk per trade = 0.5% of equity; lots = floor(budget / (lot x 0.5 delta x stop distance)), minimum 1.
  * Stop = the indicator's signal candle (beyond its low/high, 0.5-1.0 ATR) but never more than 30% of the option
    premium (backtest.plan_risk). Exit when the underlying hits that stop OR the option bid falls 30% below entry,
    2R target, 10 sessions, or one day before expiry; square-off check 15:15.
  * Stock picks are chosen automatically: proven-strategy signal agreeing with the stock's screen score.
"""
import json
import math
import os
import threading
import time
from datetime import date, datetime, timedelta, timezone

import requests
import shared_cache
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

IST = timezone(timedelta(hours=5, minutes=30))
router = APIRouter(prefix="/api/auto")
_lock = threading.Lock()

KEY = "rajanone:auto:v1"
FILE = os.path.join(os.environ.get("BHAV_CACHE_WRITE_DIR") or os.path.dirname(__file__), "auto_state.json")
NO_LIMIT = 10 ** 6                      # "maxPerDay", "indexSlots", "stockSlots": 0 (or empty) means no limit


def _cap(cfg, key):
    v = cfg.get(key)
    return NO_LIMIT if not v else int(v)


DEFAULT_CFG = {"enabled": True, "capital": 1000000.0, "riskPct": 0.5, "maxPerDay": 0, "indexSlots": 0, "stockSlots": 0, "limitRemoved": True,
               "windowStart": "09:15", "lastEntry": "14:30", "squareOff": "15:15", "minDaysToExpiry": 3,
               "maxHoldSessions": 10, "costPct": 0.1, "researchMode": True}
INDEX_SYMS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]


# ───────────────────────── state ─────────────────────────
def _remote():
    url = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
    tok = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")
    return (url, tok) if url and tok else None


def _load():
    st = {"cfg": dict(DEFAULT_CFG), "trades": [], "log": []}
    try:
        r = _remote()
        if r:
            raw = requests.post(r[0], headers={"Authorization": f"Bearer {r[1]}"}, json=["GET", KEY], timeout=8).json().get("result")
            d = json.loads(raw) if raw else {}
        else:
            with open(FILE, encoding="utf-8") as f:
                d = json.load(f)
        saved = d.get("cfg") or {}
        st["cfg"].update(saved)
        if saved and not saved.get("limitRemoved"):          # settings saved in the 5-a-day days: lift the cap once
            st["cfg"].update(maxPerDay=0, indexSlots=0, stockSlots=0, limitRemoved=True)
        st["trades"], st["log"] = d.get("trades") or [], d.get("log") or []
        import nse_calendar                               # trades "opened" on an exchange holiday used stale prices: void them
        bad = [t for t in st["trades"] if nse_calendar.holiday(t.get("date"))]
        if bad:
            st["trades"] = [t for t in st["trades"] if not nse_calendar.holiday(t.get("date"))]
            st["log"].append({"at": _now().isoformat(), "msg": f"Voided {len(bad)} paper trade(s) opened on an NSE holiday ({nse_calendar.holiday(bad[0]['date'])}) - prices were stale"})
            st["_dirty"] = True
        st["fillNext"], st["fillBackoff"] = d.get("fillNext") or 0, d.get("fillBackoff") or 0
        if d.get("cand"):
            st["cand"] = d["cand"]
        if st["cfg"].get("windowStart") == "09:20":          # old default: entries may now start at the open
            st["cfg"]["windowStart"] = "09:15"
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[auto] state load failed: {e}")
    return st


def _save(st):
    st.pop("_dirty", None)
    st["log"] = st["log"][-120:]
    try:
        r = _remote()
        if r:
            requests.post(r[0], headers={"Authorization": f"Bearer {r[1]}"}, json=["SET", KEY, json.dumps(st)], timeout=8)
        else:
            tmp = FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(st, f)
            os.replace(tmp, FILE)
    except Exception as e:
        print(f"[auto] state save failed: {e}")


def _now():
    return datetime.now(IST)


def _hm(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def _mins(now):
    return now.hour * 60 + now.minute


def _equity(st):
    return st["cfg"]["capital"] + sum(t.get("net", 0.0) for t in st["trades"] if t["status"] == "CLOSED")


# ───────────────────────── market helpers ─────────────────────────
def _quotes(keys):
    from nse_service import nse_service
    return nse_service.upstox._full_quotes(list(keys))


def _last(q):
    return float((q or {}).get("last_price") or 0)


def _sessions_between(a, b):
    n, d = 0, date.fromisoformat(a)
    end = date.fromisoformat(b)
    while d < end:
        d += timedelta(days=1)
        if __import__("nse_calendar").is_trading_day(d):
            n += 1
    return n


# ───────────────────────── signal selection ─────────────────────────
def active_set(cfg):
    """({key: score}, {key: (variant, filter)}, label). Proven strategies first; if none passed the out-of-sample
    test and research mode is on, the top 3 in-sample configs are forward-tested and clearly labelled UNPROVEN."""
    import backtest
    r = backtest.get()["result"]
    if not r:
        return {}, {}, "waiting for the backtest"
    sc = {x["key"]: x["inSample"]["avgR"] for x in r["ranking"]}
    chosen = {k: tuple(v) for k, v in r["chosen"].items()}
    if r["provenKeys"]:
        return {k: sc[k] for k in r["provenKeys"]}, chosen, "proven"
    if cfg.get("researchMode") and r.get("researchKeys"):
        return {k: sc[k] for k in r["researchKeys"]}, chosen, "unproven (forward test)"
    return {}, chosen, "no strategy passed the backtest and research mode is off"


def _trend_ok(sym, side, today):
    import bar_source
    bars = [b for b in bar_source.daily_bars(sym, 420) if b["date"] < today]
    if len(bars) < 200:
        return False
    k, e = 2 / 201, None
    for b in bars:
        e = b["close"] if e is None else b["close"] * k + e * (1 - k)
    return (side == "BUY") == (bars[-1]["close"] > e)


def candidates(today):
    """Fresh signals on the last completed daily bar from the active strategies (same logic the backtest used)."""
    import backtest
    import bar_source
    st0 = _load()
    scores, chosen, label = active_set(st0["cfg"])
    if not scores:
        return [], label
    runners = backtest._runners()
    syms = INDEX_SYMS + [s for s in backtest.STOCK_SYMS if bar_source.supports(s)]
    out, deadline = [], time.time() + (9 if os.environ.get("VERCEL") else 150)

    import concurrent.futures as cf

    def one(job):
        key, sym = job
        if time.time() > deadline:
            return None
        try:
            rows = runners[key](sym, 400).get("bars") or []
        except Exception:
            return None
        rows = [r for r in rows if r.get("date") and r["date"] < today]      # completed sessions only
        if len(rows) < 2:
            return None
        sg = backtest.norm_signal(rows[-1].get("signal"))
        prev = backtest.norm_signal(rows[-2].get("signal"))
        if not sg or sg == prev:
            return None
        variant, flt = chosen.get(key, ("fixed", "none"))
        if flt == "trend200" and not _trend_ok(sym, sg, today):
            return None
        return {"key": key, "sym": sym, "side": sg, "asOf": rows[-1]["date"], "score": scores[key], "indStop": rows[-1].get("stop"),
                "variant": variant, "filter": flt, "label": label, "kind": "index" if sym in INDEX_SYMS else "stock"}

    jobs = [(k, s) for s in syms for k in scores if k in runners]
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        for r in ex.map(one, jobs):
            if r:
                out.append(r)
    return out, label


def fill_slots(st, today, already):
    """Entries beyond the strategy signals come from the app's own screens:
       index slots  <- index CALL / PUT where the daily chart and the live option flow agree
       stock slots  <- strongest BUY / SELL stock screens among 20 liquid F&O stocks (chosen automatically)
    Every trade is tagged with its source so strategy trades and screen trades can be judged separately."""
    import backtest
    import market_api
    cfg = st["cfg"]
    todays = [t for t in st["trades"] if t["date"] == today]
    used = {t["sym"] for t in st["trades"] if t["date"] == today or t["status"] == "OPEN"} | {c["sym"] for c in already}
    have = {"index": 0, "stock": 0}
    for k in [t["kind"] for t in todays] + [c["kind"] for c in already]:
        have[k] += 1
    need = {"index": max(0, _cap(cfg, "indexSlots") - have["index"]), "stock": max(0, _cap(cfg, "stockSlots") - have["stock"])}
    room = _cap(cfg, "maxPerDay") - len(todays) - len(already)
    vercel = bool(os.environ.get("VERCEL"))
    out = []
    if room <= 0:
        return out
    if need["index"] > 0:
        try:
            calls = market_api.quick_index_calls(6 if vercel else 15)
            ranked = []
            for c in calls:
                if c["instrument"] in used:
                    continue
                if c.get("signal") in ("BUY CALL", "BUY PUT"):
                    tier = 0 if c.get("confidence") == "high" else 1               # tier 0: chart + flow agree; tier 1: flow-led
                    ranked.append((tier, -(c.get("strength") or 0), c, "BUY" if c["signal"] == "BUY CALL" else "SELL",
                                   f"index call/put ({c.get('basis', 'chart + option flow agree')})"))
            ranked.sort(key=lambda r: (r[0], r[1]))
            for tier, neg, c, side, why in ranked:
                if need["index"] <= 0:
                    break
                score = (-neg) / 100 if tier == 0 else (-neg) / 200
                out.append({"key": "index-call-put", "sym": c["instrument"], "side": side, "kind": "index", "variant": "fixed",
                            "filter": "none", "score": score, "rank": (1.0 if tier == 0 else 0.5) + score, "agree": 1,
                            "source": why, "label": "index call/put screen"})
                used.add(c["instrument"])
                need["index"] -= 1
        except Exception as e:
            st["log"].append({"at": _now().isoformat(), "msg": f"index screen failed: {str(e)[:80]}"})
    if need["stock"] > 0:
        try:
            picks = market_api.quick_screen([s for s in backtest.STOCK_SYMS], 8 if vercel else 20)
            ranked = sorted([p for p in picks if p["signal"] in ("BUY", "SELL") and p["s"] not in used and p.get("strength", 0) >= 50],
                            key=lambda p: (-(p.get("strength") or 0), -(p.get("volx") or 0)))
            for p in ranked[:need["stock"]]:
                out.append({"key": "stock-screen", "sym": p["s"], "side": p["signal"], "kind": "stock", "variant": "fixed", "filter": "none",
                            "score": (p.get("strength") or 0) / 100, "rank": 1 + (p.get("strength") or 0) / 100, "agree": 1,
                            "source": "stock screen (trend + volume + RSI)", "label": "stock screen"})
        except Exception as e:
            st["log"].append({"at": _now().isoformat(), "msg": f"stock screen failed: {str(e)[:80]}"})
    return out[:room]


def x_stop(rows):
    return rows[-1].get("stop") if rows else None


def scan_all(st, today):
    """Fresh BUY/SELL events from EVERY indicator on the last completed daily bar, for 5 indices + 20 liquid stocks.
    Completed bars only change once a day, so this is scanned ONCE per day, symbol by symbol (it resumes in the next
    cycle if it runs out of time) instead of being recomputed every 5 minutes - that was a big part of the Upstox load."""
    import backtest
    import bar_source
    cache = st.setdefault("cand", {})
    if cache.get("date") != today:
        cache.clear()
        cache.update(date=today, done=[], items=[])
    r = backtest.get()["result"]
    score = {x["key"]: x["inSample"]["avgR"] for x in (r["ranking"] if r else [])}
    chosen = {k: tuple(v) for k, v in ((r["chosen"] if r else {}) or {}).items()}
    runners = backtest._runners()
    syms = INDEX_SYMS + [x for x in backtest.STOCK_SYMS if bar_source.supports(x)]
    todo = [x for x in syms if x not in cache["done"]]
    deadline = time.time() + (8 if os.environ.get("VERCEL") else 120)

    import concurrent.futures as cf

    def one_symbol(sym):
        bar_source.completed_only(True)               # long-cached completed bars, no intraday request
        found = []
        for key, fn in runners.items():
            if time.time() > deadline:
                return sym, None                       # not finished: stays on the to-do list
            try:
                rows = fn(sym, 400).get("bars") or []
            except Exception:
                continue
            rows = [x for x in rows if x.get("date") and x["date"] < today]
            if len(rows) < 2:
                continue
            sg, prev = backtest.norm_signal(rows[-1].get("signal")), backtest.norm_signal(rows[-2].get("signal"))
            if not sg or sg == prev:
                continue
            variant, flt = chosen.get(key, ("fixed", "none"))
            if flt == "trend200" and not _trend_ok(sym, sg, today):
                continue
            found.append({"key": key, "sym": sym, "side": sg, "asOf": rows[-1]["date"], "score": score.get(key, 0.0), "indStop": x_stop(rows),
                          "variant": variant, "filter": flt, "kind": "index" if sym in INDEX_SYMS else "stock"})
        return sym, found

    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        for sym, found in ex.map(one_symbol, todo):
            if found is not None:
                cache["done"].append(sym)
                cache["items"].extend(found)
    done = len(cache["done"])
    note = f"all indicators scanned: {done}/{len(syms)} symbols, {len(cache['items'])} fresh signals"
    for c in cache["items"]:
        c["label"] = "all indicators"
    return list(cache["items"]), note


def _screen_score():
    """Stock screen score and direction from the Picks engine (used only to choose among stock signals)."""
    try:
        import market_api
        return {p["s"]: p for p in market_api.picks().get("picks", [])}
    except Exception:
        return {}


def choose(cands, st, today):
    cfg = st["cfg"]
    taken_today = [t for t in st["trades"] if t["date"] == today]
    have_idx = sum(1 for t in taken_today if t["kind"] == "index")
    have_stk = sum(1 for t in taken_today if t["kind"] == "stock")
    open_syms = {t["sym"] for t in st["trades"] if t["status"] == "OPEN"}
    by_sym = {}
    for c in cands:
        by_sym.setdefault(c["sym"], []).append(c)
    clean = []
    for sym, lst in by_sym.items():
        if sym in open_syms:
            continue                                         # already holding it
        buys, sells = [c for c in lst if c["side"] == "BUY"], [c for c in lst if c["side"] == "SELL"]
        if len(buys) == len(sells):
            continue                                         # indicators cancel out: no view
        side_list = buys if len(buys) > len(sells) else sells
        best = max(side_list, key=lambda c: c["score"])
        best["agree"] = len(side_list)                       # how many indicators point the same way
        best["against"] = len(lst) - len(side_list)
        best["strategies"] = [c["key"] for c in side_list]
        clean.append(best)
    screen = _screen_score() if any(c["kind"] == "stock" for c in clean) else {}
    for c in clean:
        p = screen.get(c["sym"])
        c["screenAgrees"] = bool(p and ((c["side"] == "BUY" and p["signal"] == "BUY") or (c["side"] == "SELL" and p["signal"] == "SELL")))
        c["rank"] = c["score"] + 0.5 * (c["agree"] - c.get("against", 0) - 1) + (0.3 if c["screenAgrees"] else 0)
    idx = sorted([c for c in clean if c["kind"] == "index"], key=lambda c: -c["rank"])[:max(0, _cap(cfg, "indexSlots") - have_idx)]
    stk = sorted([c for c in clean if c["kind"] == "stock" and c["screenAgrees"]], key=lambda c: -c["rank"])
    if len(stk) < max(0, _cap(cfg, "stockSlots") - have_stk):              # fall back to any proven stock signal
        stk += sorted([c for c in clean if c["kind"] == "stock" and not c["screenAgrees"]], key=lambda c: -c["rank"])
    stk = stk[:max(0, _cap(cfg, "stockSlots") - have_stk)]
    room = max(0, _cap(cfg, "maxPerDay") - len(taken_today))
    return (idx + stk)[:room]


# ───────────────────────── entries / exits ─────────────────────────
def _contract(sym, side, today, min_days):
    import market_api
    ch = market_api.chain(sym, "")
    exps = [e for e in (ch.get("expiries") or [ch.get("expiry")]) if e]
    pick = next((e for e in sorted(exps) if (date.fromisoformat(e) - date.fromisoformat(today)).days >= min_days), None)
    if pick and pick != ch.get("expiry"):
        ch = market_api.chain(sym, pick)
    rows, atm = ch.get("rows") or [], ch.get("atm")
    if not rows or atm is None:
        raise RuntimeError("no chain")
    row = min(rows, key=lambda r: abs(r["strike"] - atm))
    leg = row.get("ce" if side == "BUY" else "pe") or {}
    ask, bid, ltp = float(leg.get("ask") or 0), float(leg.get("bid") or 0), float(leg.get("ltp") or 0)
    px = ask or ltp
    if not leg.get("key") or px <= 0:
        raise RuntimeError("no price")
    # liquidity guard: a stale or one-sided quote is not a price you can trade at (it turned a flat MIDCPNIFTY entry into a fake -48%)
    if ask > 0 and bid > 0 and (ask - bid) / ask > 0.10:
        raise RuntimeError(f"skipped: bid/ask spread {(ask - bid) / ask * 100:.0f}% is too wide")
    if ask > 0 and ltp > 0 and abs(ask - ltp) / ltp > 0.25:
        raise RuntimeError(f"skipped: ask {ask} is far from the last traded price {ltp} (illiquid)")
    if ask > 0 and bid <= 0:
        raise RuntimeError("skipped: no bid in the market")
    return {"expiry": ch["expiry"], "strike": row["strike"], "key": leg["key"], "premium": px, "lot": int(ch.get("lot") or 1),
            "spot": float(ch.get("spot") or 0)}


def _atr_for(sym):
    import bar_source
    from ut_bot import _rma, _true_range
    bars = bar_source.daily_bars(sym, 120)
    bars = [b for b in bars if b["date"] < _now().date().isoformat()]
    a = _rma(_true_range(bars), 14)
    return a[-1], bars[-1]["close"], bars


def _premium_plan(entry, risk_u, delta=0.5):
    """Option stop and targets in premium terms: 1R = delta x underlying stop distance."""
    rp = round(delta * risk_u, 2)
    return {"premRisk": rp, "premSL": round(max(0.05, entry - rp), 2),
            "premT": [round(entry + k * rp, 2) for k in (1, 2, 3)]}


def _replan(t):
    """Trades opened under the old 1.5-2 ATR rule risked up to 90% of the premium; cap them at 30% (tighten only)."""
    if t.get("plan") == "v2" or t["status"] != "OPEN":
        return
    import backtest
    d = 1 if t["side"] == "BUY" else -1
    cap = backtest.PREM_SL * t["entry"] / backtest.DELTA
    if t["riskU"] > cap:
        t["riskU"] = round(cap, 2)
        ns = t["entryU"] - d * cap
        t["stopU"] = round(max(t["stopU"], ns) if d > 0 else min(t["stopU"], ns), 2)
        if t.get("targetU") is not None:
            t["targetU"] = round(t["entryU"] + d * backtest.TARGET_R * cap, 2)
        qty = t["lots"] * t["lot"]
        t["initialRisk"] = round(min(qty * backtest.DELTA * cap, qty * t["entry"]), 0)
    t.update(_premium_plan(t["entry"], t["riskU"]), plan="v2")


def open_trade(st, c, today):
    cfg = st["cfg"]
    import backtest
    atr, last_close, bars = _atr_for(c["sym"])
    ct = _contract(c["sym"], c["side"], today, cfg["minDaysToExpiry"])
    d = 1 if c["side"] == "BUY" else -1
    entry_u = ct["spot"] or last_close
    variant = c.get("variant", "fixed")
    # same rule as the backtest: signal-candle stop, capped at 30% of THIS option's premium
    risk_u = backtest.plan_risk(bars, atr, len(bars) - 1, c["side"], entry_u, ct["premium"], ind_stop=c.get("indStop"))
    if risk_u <= 0:
        raise RuntimeError("no valid stop")
    stop_u = entry_u - d * risk_u
    target_u = entry_u + d * backtest.TARGET_R * risk_u if variant == "fixed" else None
    budget = _equity(st) * cfg["riskPct"] / 100
    per_lot = ct["lot"] * 0.5 * risk_u
    lots = max(1, int(budget // per_lot)) if per_lot > 0 else 1
    max_out = _equity(st) * 0.2
    while lots > 1 and lots * ct["lot"] * ct["premium"] > max_out:
        lots -= 1
    t = {
        "id": f"A-{today.replace('-', '')}-{len([x for x in st['trades'] if x['date'] == today]) + 1}",
        "date": today, "openedAt": _now().isoformat(), "sym": c["sym"], "kind": c["kind"], "side": c["side"],
        "opt": "CE" if c["side"] == "BUY" else "PE", "strike": ct["strike"], "expiry": ct["expiry"], "key": ct["key"],
        "lot": ct["lot"], "lots": lots, "entry": round(ct["premium"], 2), "entryU": round(entry_u, 2),
        "stopU": round(stop_u, 2), "targetU": round(target_u, 2) if target_u is not None else None, "riskU": round(risk_u, 2),
        "variant": variant, "filter": c.get("filter", "none"), "bestU": round(entry_u, 2), "mode": c.get("label", ""),
        "initialRisk": round(min(lots * per_lot, lots * ct["lot"] * ct["premium"]), 0), "riskBudget": round(budget, 0),
        "strategy": c["key"], "agree": c.get("agree", 1),
        "screenAgrees": c.get("screenAgrees"), "indicators": c.get("strategies") or [c["key"]],
        "source": c.get("source", f"{c.get('agree', 1)} indicator(s) agree" if c.get("strategies") else "strategy signal"), "status": "OPEN", "last": round(ct["premium"], 2),
        "plan": "v2", **_premium_plan(round(ct["premium"], 2), risk_u),
    }
    st["trades"].append(t)
    st["log"].append({"at": _now().isoformat(), "msg": f"ENTER {t['sym']} {t['strike']:.0f}{t['opt']} x{lots} @ {t['entry']} [{c['key']} · {variant}]"})
    return t


def _close(st, t, px, why):
    qty = t["lots"] * t["lot"]
    gross = (px - t["entry"]) * qty
    cost = t.get("costPct", st["cfg"]["costPct"]) / 100 * (t["entry"] + px) * qty
    t.update(status="CLOSED", exit=round(px, 2), exitReason=why, closedAt=_now().isoformat(), gross=round(gross, 2),
             cost=round(cost, 2), net=round(gross - cost, 2),
             R=round((gross - cost) / t["initialRisk"], 2) if t.get("initialRisk") else None, last=round(px, 2))
    st["log"].append({"at": _now().isoformat(), "msg": f"EXIT {t['sym']} {t['strike']:.0f}{t['opt']} @ {px:.2f} ({why}) net {t['net']:+.0f}"})
    _push(f"auto-exit|{t['id']}", f"PAPER EXIT ({why}) · {t['sym']} {t['strike']:.0f} {t['opt']}",
          f"Exit @ ₹{px:.2f} (entry ₹{t['entry']}) · net {'+' if t['net'] >= 0 else '−'}₹{abs(t['net']):,.0f}")


def _push(idem, title, body):
    try:
        import push_signals
        push_signals.notify_all(idem, title, body, url="/#journal", kind="trade")
    except Exception as e:
        print(f"[auto] notify failed: {e}")


def manage(st, now):
    import market_api
    opens = [t for t in st["trades"] if t["status"] == "OPEN"]
    if not opens:
        return
    keys = {t["key"] for t in opens} | {market_api._key(t["sym"]) for t in opens}
    try:
        q = _quotes(keys)
    except Exception as e:
        print(f"[auto] quote failure: {e}")
        return
    today = now.date().isoformat()
    for t in opens:
        _replan(t)
    for t in opens:
        opt_q, und_q = q.get(t["key"]), q.get(market_api._key(t["sym"]))
        opt_px, und_px = _last(opt_q), _last(und_q)
        if opt_px > 0:
            t["last"] = round(opt_px, 2)
        bid = float((((opt_q or {}).get("depth") or {}).get("buy") or [{}])[0].get("price") or 0)
        exit_px = bid if bid > 0 else opt_px
        if exit_px <= 0 or und_px <= 0:
            continue
        d = 1 if t["side"] == "BUY" else -1
        why = None
        variant = t.get("variant", "fixed")
        if variant == "trail":                       # the stop trails the best underlying price since entry by the same distance
            t["bestU"] = max(t.get("bestU", t["entryU"]), und_px) if d > 0 else min(t.get("bestU", t["entryU"]), und_px)
            t["stopU"] = round(max(t["stopU"], t["bestU"] - t["riskU"]) if d > 0 else min(t["stopU"], t["bestU"] + t["riskU"]), 2)
        tsl = t.get("tsl")
        if tsl and tsl.get("mode") in ("trail", "breakeven", "step"):
            best = t.get("bestU", t["entryU"])
            best = max(best, und_px) if d > 0 else min(best, und_px)
            t["bestU"] = round(best, 2)
            fav = d * (best - t["entryU"])
            ns = None
            if tsl["mode"] == "trail" and tsl.get("trail"):
                ns = best - d * float(tsl["trail"])
            elif tsl["mode"] == "breakeven":
                if fav >= float(tsl.get("trigger") or 1.0) * t["riskU"]:
                    ns = t["entryU"]
            elif tsl["mode"] == "step" and tsl.get("step"):
                k = math.floor(fav / float(tsl["step"]))
                if k >= 1:
                    ns = t["entryU"] + d * (k - 1) * float(tsl["step"])        # one full step of cushion is kept
            if ns is not None:
                new = max(t["stopU"], ns) if d > 0 else min(t["stopU"], ns)    # never loosen
                if new != t["stopU"]:
                    t["stopU"] = round(new, 2)
                    t["stopMoved"] = _now().isoformat()
        _profit_lock(t, opt_px if opt_px > 0 else exit_px)
        hold = st["cfg"]["maxHoldSessions"] if variant == "fixed" else 40
        if t.get("premSL") and exit_px <= t["premSL"]:
            why = "TSL" if t.get("lock") else "STOP"   # option premium stop (30% cap) - catches time decay too
        elif d * (und_px - t["stopU"]) <= 0:
            why = "TSL" if (tsl and tsl.get("mode") in ("trail", "breakeven", "step") and t.get("stopMoved")) else "STOP"
        elif t.get("targetU") is not None and d * (und_px - t["targetU"]) >= 0:
            why = "TARGET"
        elif (date.fromisoformat(t["expiry"]) - date.fromisoformat(today)).days <= 1:
            why = "EXPIRY"
        elif _sessions_between(t["date"], today) >= hold:
            why = "TIME"
        elif variant == "reverse" and t["date"] < today and _reversed(t, today):
            why = "REVERSE"
        if why:
            _close(st, t, exit_px, why)


LOCK_BE, LOCK_TRAIL, LOCK_KEEP = 1500.0, 2000.0, 0.5


def _profit_lock(t, px):
    """Auto profit lock on the option premium: at Rs 1,500 open profit the premium stop moves to entry + charges
    (breakeven); from Rs 2,000 it trails, keeping 50% of the best profit seen. Only ever tightens."""
    qty = (t.get("lots") or 0) * (t.get("lot") or 0)
    if not (px and px > 0 and qty > 0):
        return
    pnl = (px - t["entry"]) * qty
    best = max(float(t.get("bestPnl") or 0.0), pnl)
    t["bestPnl"] = round(best, 2)
    if best < LOCK_BE:
        return
    fee_u = 80.0 / qty                                  # ~ two option legs of brokerage + taxes per lot set
    keep = LOCK_KEEP * best if best >= LOCK_TRAIL else 0.0
    stop = round(t["entry"] + fee_u + keep / qty, 2)
    if stop > float(t.get("premSL") or 0):
        first = not t.get("lock") or (keep and t["lock"].get("mode") != "trail")
        t["premSL"] = stop
        t["lock"] = {"mode": "trail" if keep else "breakeven", "keep": round(keep), "best": round(best), "at": _now().isoformat()}
        t["stopMoved"] = _now().isoformat()
        if first:
            _push(f"auto-lock|{t['id']}|{t['lock']['mode']}", f"PROFIT LOCKED · {t['sym']} {t.get('strike', 0):.0f} {t.get('opt', '')}",
                  f"Profit ₹{best:,.0f} - stop moved to ₹{stop:.2f} ({'keeps ₹' + format(round(keep), ',') if keep else 'breakeven'})")


def _reversed(t, today):
    """True when the strategy's last completed signal is now the opposite of this trade's side."""
    try:
        import backtest
        rows = backtest._runners()[t["strategy"]](t["sym"], 400).get("bars") or []
        rows = [r for r in rows if r.get("date") and t["date"] < r["date"] < today]
        for r in reversed(rows):
            sg = backtest.norm_signal(r.get("signal"))
            if sg:
                return sg != t["side"]
    except Exception:
        pass
    return False


def run_cycle(force=False, dry=False):
    now = _now()
    if not dry and not shared_cache.lock("auto-cycle", 45):
        return {"ran": False, "reason": "another cycle is already running"}
    try:
        return _run_cycle(now, force, dry)
    finally:
        if not dry:
            shared_cache.unlock("auto-cycle")
            try:                                   # the stock paper trader rides on the same schedule
                import stock_trader
                stock_trader.run_cycle()
            except Exception as e:
                print(f"[stockbot] cycle failed: {e}")


_MARK_AT = 0.0


def mark_open_positions(min_gap=15):
    """Mark the open positions to market and run their exit checks (stop, target, trailing stop, expiry, time).
    Server-side scheduling is not available on Vercel (the 5-minute cycle only runs while a browser tab with notifications on is
    open), so positions used to keep their entry price - P&L frozen at 0, stops never checked - until that happened. The status
    read now does this itself, at most once per `min_gap` seconds across all instances, only in market hours, and never while a
    full cycle is running (they share a lock). Returns True when it ran."""
    global _MARK_AT
    if time.time() - _MARK_AT < min_gap:
        return False
    import nse_calendar
    now = _now()
    if not nse_calendar.session_open(now):
        return False
    if not shared_cache.lock("auto-cycle", max(10, min_gap)):
        return False
    try:
        with _lock:
            st = _load()
            if not any(t["status"] == "OPEN" for t in st["trades"]):
                return False
            _MARK_AT = time.time()
            manage(st, now)
            _save(st)
        return True
    finally:
        shared_cache.unlock("auto-cycle")


def _run_cycle(now, force, dry):
    with _lock:
        st = _load()
        cfg = st["cfg"]
        rep = {"ran": True, "dry": dry, "entered": [], "closed": [], "note": None}
        if not cfg["enabled"] and not dry:
            return {"ran": False, "reason": "auto trader is switched off"}
        import nse_calendar
        is_open = nse_calendar.session_open(now)
        if not is_open and (not force or not nse_calendar.is_trading_day(now.date())):
            return {"ran": False, "reason": "market closed" + (f" ({nse_calendar.holiday(now.date())})" if nse_calendar.holiday(now.date()) else "")}
        before = {t["id"] for t in st["trades"] if t["status"] == "CLOSED"}
        if not dry:
            manage(st, now)
        rep["closed"] = [t["id"] for t in st["trades"] if t["status"] == "CLOSED" and t["id"] not in before]
        today = now.date().isoformat()
        in_window = _hm(cfg["windowStart"]) <= _mins(now) <= _hm(cfg["lastEntry"])
        todays = [t for t in st["trades"] if t["date"] == today]
        if (in_window or force) and len(todays) < _cap(cfg, "maxPerDay"):
            cands, why = scan_all(st, today)
            rep["note"] = why
            chosen = choose(cands, st, today)
            filled = []
            if cfg.get("fillSlots", True) and time.time() >= max(st.get("fillBackoff", 0), st.get("fillNext", 0)):
                st["fillNext"] = time.time() + 600                 # live screens at most every 10 minutes (each costs ~40 Upstox calls)
                filled = fill_slots(st, today, chosen)
                if any("rate-limiting" in (l.get("msg") or "") or "budget" in (l.get("msg") or "") for l in st["log"][-2:]):
                    st["fillBackoff"] = time.time() + 600        # Upstox pushed back: leave it alone for 10 minutes
            for c in chosen + filled:
                if dry:
                    rep["entered"].append({"sym": c["sym"], "side": c["side"], "strategy": c["key"], "kind": c["kind"], "rank": round(c["rank"], 2)})
                    continue
                try:
                    t = open_trade(st, c, today)
                    rep["entered"].append(t["id"])
                    _notify(t)
                except Exception as e:
                    st["log"].append({"at": now.isoformat(), "msg": f"skip {c['sym']}: {str(e)[:80]}"})
        if not dry:
            _save(st)
        return rep


def _notify(t):
    try:
        import push_signals
        push_signals.notify_all(f"auto|{t['id']}", f"PAPER ENTRY · {t['sym']} {t['strike']:.0f} {t['opt']}",
                                f"{t['lots']} lot(s) @ ₹{t['entry']} · stop {t['stopU']} · target {t['targetU'] if t['targetU'] else 'trailing'} · "
                                f"{len(t.get('indicators') or [])} indicator(s): {', '.join((t.get('indicators') or [t['strategy']])[:3])}")
    except Exception as e:
        print(f"[auto] notify failed: {e}")


# ───────────────────────── API ─────────────────────────
class Cfg(BaseModel):
    enabled: bool | None = None
    researchMode: bool | None = None
    riskPct: float | None = None
    maxPerDay: int | None = None


class TslBody(BaseModel):
    mode: str
    trail: float | None = None        # underlying points behind the best price
    trigger: float | None = None      # breakeven trigger, in R (multiples of the initial underlying risk)
    step: float | None = None         # underlying points per step


class StopBody(BaseModel):
    stopU: float


def _open_trade(st, tid):
    t = next((x for x in st["trades"] if x["id"] == tid), None)
    if not t:
        raise HTTPException(404, "Trade not found")
    if t["status"] != "OPEN":
        raise HTTPException(400, "This trade is already closed")
    return t


def _und_price(t):
    import market_api
    q = _quotes({market_api._key(t["sym"])})
    return _last(q.get(market_api._key(t["sym"])))


@router.post("/trade/{tid}/exit")
def manual_exit(tid: str):
    """Close an open automated paper trade right now at the live bid."""
    with _lock:
        st = _load()
        t = _open_trade(st, tid)
        try:
            q = _quotes([t["key"]]).get(t["key"]) or {}
        except Exception as e:
            raise HTTPException(503, f"Live price unavailable right now, try again in a moment ({str(e)[:80]})")
        bid = float((((q or {}).get("depth") or {}).get("buy") or [{}])[0].get("price") or 0)
        px = bid if bid > 0 else _last(q)
        if px <= 0:
            raise HTTPException(503, "No live price for this contract right now, try again in a moment")
        _close(st, t, px, "MANUAL")
        _save(st)
        return {"ok": True, "exit": t["exit"], "net": t["net"], "R": t["R"]}


@router.post("/trade/{tid}/tsl")
def set_tsl(tid: str, b: TslBody):
    """Attach (or remove) your own trailing stop. It only ever tightens the stop."""
    mode = (b.mode or "").lower()
    if mode not in ("off", "trail", "breakeven", "step"):
        raise HTTPException(400, "mode must be off, trail, breakeven or step")
    with _lock:
        st = _load()
        t = _open_trade(st, tid)
        if mode == "off":
            t["tsl"] = None
        elif mode == "trail":
            if not (b.trail and b.trail > 0):
                raise HTTPException(400, "Enter the trail distance (underlying points)")
            t["tsl"] = {"mode": "trail", "trail": b.trail}
        elif mode == "breakeven":
            t["tsl"] = {"mode": "breakeven", "trigger": b.trigger if (b.trigger and b.trigger > 0) else 1.0}
        else:
            if not (b.step and b.step > 0):
                raise HTTPException(400, "Enter the step size (underlying points)")
            t["tsl"] = {"mode": "step", "step": b.step}
        st["log"].append({"at": _now().isoformat(), "msg": f"TSL {mode} set on {t['sym']} {t['strike']:.0f}{t['opt']} by user"})
        _save(st)
        return {"ok": True, "tsl": t["tsl"], "stopU": t["stopU"]}


@router.post("/trade/{tid}/stop")
def tighten_stop(tid: str, b: StopBody):
    with _lock:
        st = _load()
        t = _open_trade(st, tid)
        d = 1 if t["side"] == "BUY" else -1
        try:
            und = _und_price(t)
        except Exception as e:
            raise HTTPException(503, f"Live price unavailable right now, try again in a moment ({str(e)[:80]})")
        if d * (b.stopU - t["stopU"]) <= 0:
            raise HTTPException(400, f"A stop can only be tightened: it is {t['stopU']} now")
        if und > 0 and d * (und - b.stopU) <= 0:
            raise HTTPException(400, f"That stop is already beyond the current price ({und}); use Exit now instead")
        t["stopU"] = round(b.stopU, 2)
        t["stopMoved"] = _now().isoformat()
        st["log"].append({"at": _now().isoformat(), "msg": f"Stop moved to {t['stopU']} on {t['sym']} {t['strike']:.0f}{t['opt']} by user"})
        _save(st)
        return {"ok": True, "stopU": t["stopU"]}


@router.get("/status")
def status():
    try:
        mark_open_positions()
    except Exception as e:                                 # a failed mark must never break the status screen
        print(f"[auto] mark-to-market failed: {e}")
    st = _load()
    if st.get("_dirty"):
        with _lock:
            _save(st)
    now = _now()
    today = now.date().isoformat()
    closed = [t for t in st["trades"] if t["status"] == "CLOSED"]
    wins = [t for t in closed if t["net"] > 0]
    opens = [t for t in st["trades"] if t["status"] == "OPEN"]
    for t in opens:
        _replan(t)
        t["unrealised"] = round((t["last"] - t["entry"]) * t["lots"] * t["lot"], 2)
    import backtest
    bt = backtest.get()["result"]
    import backtest
    r0 = backtest.get()["result"]
    chosen = {k: tuple(v) for k, v in ((r0["chosen"] if r0 else {}) or {}).items()}
    keys = list(chosen) or []
    proven = bool(r0 and r0["provenKeys"])
    label = ("proven indicators" if proven else "all indicators, ranked by how many agree · unproven (forward test)")
    return {
        "activeStrategies": [{"key": k, "variant": chosen.get(k, ("fixed", "none"))[0], "filter": chosen.get(k, ("fixed", "none"))[1]} for k in keys],
        "mode": label,
        "cfg": st["cfg"], "today": today, "marketOpen": __import__("nse_calendar").session_open(now),
        "todayCount": len([t for t in st["trades"] if t["date"] == today]),
        "open": opens, "closed": closed[-120:][::-1], "log": st["log"][-120:][::-1],
        "summary": {"trades": len(closed), "net": round(sum(t["net"] for t in closed), 0),
                    "winRate": round(len(wins) / len(closed), 2) if closed else 0,
                    "avgR": round(sum(t["R"] or 0 for t in closed) / len(closed), 2) if closed else 0,
                    "openPnL": round(sum(t.get("unrealised", 0) for t in opens), 0), "equity": round(_equity(st), 0)},
        "backtest": {"provenKeys": bt["provenKeys"] if bt else [], "twoMonth": (bt["executor"] or bt["executorResearch"] or {}).get("twoMonth") if bt else None,
                     "researchReplay": bt["executorResearch"] if bt else None,
                     "generatedAt": bt["generatedAt"] if bt else None},
    }


@router.post("/config")
def config(c: Cfg):
    with _lock:
        st = _load()
        if c.enabled is not None:
            st["cfg"]["enabled"] = c.enabled
        if c.researchMode is not None:
            st["cfg"]["researchMode"] = c.researchMode
        if c.riskPct is not None:
            if not (0.05 <= c.riskPct <= 2):
                raise HTTPException(400, "riskPct must be between 0.05 and 2")
            st["cfg"]["riskPct"] = c.riskPct
        if c.maxPerDay is not None:                                     # 0 = no limit
            if c.maxPerDay < 0:
                raise HTTPException(400, "maxPerDay must be 0 (no limit) or a positive number")
            st["cfg"]["maxPerDay"] = c.maxPerDay
        _save(st)
        return st["cfg"]


@router.post("/log/clear")
def clear_log():
    with _lock:
        st = _load()
        st["log"] = []
        _save(st)
        return {"ok": True}


@router.post("/reset")
def reset_portfolio():
    """Journal 'Reset portfolio': drop every paper trade (open and closed) so equity starts again from capital.
    Settings are kept. Today's entries count restarts too."""
    with _lock:
        st = _load()
        n = len(st["trades"])
        st["trades"], st["cand"] = [], {}
        st["log"] = [{"at": _now().isoformat(), "msg": f"Portfolio reset by the user ({n} paper trades cleared)"}]
        _save(st)
        return {"ok": True, "cleared": n}


@router.api_route("/run", methods=["GET", "POST"])
def run():
    return run_cycle()


@router.get("/preview")
def preview():
    return run_cycle(force=True, dry=True)


def start_watcher():
    if os.environ.get("VERCEL"):
        return

    def loop():
        time.sleep(45)
        import backtest
        while True:
            try:
                if backtest.get()["result"] is None and not backtest.get()["running"]:
                    backtest.start()
                r = run_cycle()
                if r.get("entered") or r.get("closed"):
                    print(f"[auto] {r}")
            except Exception as e:
                print(f"[auto] cycle failed: {e}")
            time.sleep(300)

    threading.Thread(target=loop, daemon=True, name="auto-trader").start()

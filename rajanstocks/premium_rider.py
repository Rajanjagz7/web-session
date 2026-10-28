"""Premium Rider (user, 29 Oct): option PREMIUM patterns on 5-minute candles, with a sudden volume surge.

  support bounce  - a premium falls to a support it has held (e.g. 30), a volume surge (>= 2.5x the last 10 bars) shows up, and the bar closes back up
                    through the previous bar's high  ->  BUY that contract, small stop just under the support, target = the recent high (>= 1.2R).
  heavy selling   - a premium that ran up (e.g. to 100) is dumped (e.g. from 80) on a volume surge and closes >= 20% under its peak / breaks the last
                    6 closes  ->  option sellers are in control of THAT contract; as the app only buys, the idea is to BUY THE OPPOSITE option
                    (a put dumped = bullish = buy the call) with a small stop under its recent low and a 2R target.
Index options only (ATM +/- 2 strikes), looked at on every auto-trader cycle; nothing is written or sold. Pure detection lives in bounce() / dump() so
it is unit-tested; scan() reads the live chain and candles. The auto trader records every signal as a paper "premium-rider" trade (Testing week table)."""
from __future__ import annotations

import concurrent.futures
import os

from fastapi import APIRouter

import shared_cache

router = APIRouter(prefix="/api/m/rider")

SURGE = 2.5             # last bar's volume vs the average of the 10 bars before it
TOUCH = 0.04            # a bar "touches" the support when its low is within 4% of it
DUMP_FROM_PEAK = 0.20   # the premium closes at least 20% under its recent peak
MIN_RR = 1.2
SYMS = ("NIFTY", "BANKNIFTY")
WIDTH = 2               # strikes either side of ATM


def _surge(bars):
    prev = [b["volume"] for b in bars[-11:-1] if b.get("volume")]
    if len(prev) < 5:
        return 0.0
    avg = sum(prev) / len(prev)
    return bars[-1]["volume"] / avg if avg > 0 else 0.0


def bounce(bars):
    """Support bounce on the LAST bar of `bars` (closed bars, oldest first). Returns {entry, stop, target, rr, volx, support, why} or None."""
    bars = [b for b in (bars or []) if b.get("close") and b.get("low") is not None]
    if len(bars) < 14:
        return None
    last, prev = bars[-1], bars[-2]
    base = bars[-13:-1]
    support = min(b["low"] for b in base)
    if support <= 0:
        return None
    vx = _surge(bars)
    if vx < SURGE or last["low"] > support * (1 + TOUCH) or not (last["close"] > last["open"] and last["close"] > prev["high"]):
        return None
    entry = last["close"]
    stop = round(min(last["low"], support) * 0.97, 2)
    risk = entry - stop
    if risk <= 0 or risk / entry > 0.15:                     # a SMALL stop only
        return None
    target = round(max(max(b["high"] for b in bars[-24:]), entry + 1.5 * risk), 2)
    rr = (target - entry) / risk
    if rr < MIN_RR:
        return None
    return {"entry": round(entry, 2), "stop": stop, "target": target, "rr": round(rr, 2), "volx": round(vx, 1), "support": round(support, 2),
            "why": f"premium held support {support:.2f}, volume {vx:.1f}x, closed back above the previous high"}


def dump(bars):
    """Heavy selling on the LAST bar: returns {peak, close, volx, why} or None."""
    bars = [b for b in (bars or []) if b.get("close") and b.get("high") is not None]
    if len(bars) < 14:
        return None
    last = bars[-1]
    peak = max(b["high"] for b in bars[-24:-1])
    vx = _surge(bars)
    if vx < SURGE or not last["close"] < last["open"] or last["close"] > peak * (1 - DUMP_FROM_PEAK) or last["close"] >= min(b["close"] for b in bars[-7:-1]):
        return None
    return {"peak": round(peak, 2), "close": round(last["close"], 2), "volx": round(vx, 1),
            "why": f"premium dumped from {peak:.2f} to {last['close']:.2f} on {vx:.1f}x volume (sellers in control)"}


def opposite_levels(bars):
    """Small-stop / 2R plan for buying the contract OPPOSITE to a dumped one, from its own recent bars."""
    bars = [b for b in (bars or []) if b.get("close") and b.get("low") is not None]
    if len(bars) < 8:
        return None
    entry = bars[-1]["close"]
    stop = round(min(b["low"] for b in bars[-6:]) * 0.97, 2)
    risk = entry - stop
    if risk <= 0 or risk / entry > 0.20:
        return None
    return {"entry": round(entry, 2), "stop": stop, "target": round(entry + 2 * risk, 2), "rr": 2.0}


def _bars(key):
    import nse_service
    rows = nse_service.nse_service.upstox.fetch_intraday_candles(key, "minutes", "5")
    return sorted(rows, key=lambda c: c["time"])


def scan(force=False):
    """Live scan of ATM +/- WIDTH index option premiums. Cached for 2 minutes (shared across instances)."""
    import market_api
    if not market_api.market_open():
        return {"open": False, "signals": []}
    ck = "rider:prem"
    if not force:
        hit = shared_cache.get(ck)
        if hit:
            return hit
    todo = []
    for sym in SYMS:
        try:
            ch = market_api.chain(sym, "")
        except Exception:
            continue
        rows, atm = ch.get("rows") or [], ch.get("atm")
        if not rows or atm is None:
            continue
        ai = min(range(len(rows)), key=lambda i: abs(rows[i]["strike"] - atm))
        for r in rows[max(0, ai - WIDTH): ai + WIDTH + 1]:
            for side in ("ce", "pe"):
                leg = r.get(side) or {}
                if leg.get("key"):
                    todo.append({"sym": sym, "strike": r["strike"], "opt": side.upper(), "key": leg["key"], "expiry": ch.get("expiry")})

    def one(t):
        try:
            return t, _bars(t["key"])
        except Exception:
            return t, []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        got = list(pool.map(one, todo))
    bars_by = {(t["sym"], t["strike"], t["opt"]): b for t, b in got}
    signals = []
    for t, b in got:
        name = f"{t['sym']} {int(t['strike'])} {t['opt']}"
        bo = bounce(b)
        if bo:
            signals.append({**bo, "pattern": "support-bounce", "label": "Support bounce", "contract": name, "sym": t["sym"], "key": t["key"], "opt": t["opt"], "strike": t["strike"]})
        dp = dump(b)
        if dp:
            op = "CE" if t["opt"] == "PE" else "PE"
            ob = bars_by.get((t["sym"], t["strike"], op)) or []
            lv = opposite_levels(ob)
            okey = next((x["key"] for x, _ in got if x["sym"] == t["sym"] and x["strike"] == t["strike"] and x["opt"] == op), None)
            if lv and okey:
                signals.append({**lv, "pattern": "heavy-selling", "label": f"{t['opt']} dumped, buy {op}", "contract": f"{t['sym']} {int(t['strike'])} {op}", "sym": t["sym"],
                                "key": okey, "opt": op, "strike": t["strike"], "volx": dp["volx"], "why": dp["why"] + f" - buy the {op}"})
    signals.sort(key=lambda s: -(s.get("volx") or 0))
    out = {"open": True, "signals": signals, "asOf": __import__("time").time()}
    shared_cache.set(ck, out, 120)
    return out


@router.get("/premium")
def premium(refresh: bool = False):
    try:
        return scan(force=refresh)
    except Exception as e:
        return {"open": False, "signals": [], "error": str(e)[:120]}

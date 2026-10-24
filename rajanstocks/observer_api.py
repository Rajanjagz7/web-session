"""God's Eye - The Observer.

One card per instrument (Nifty, Sensex, Bank Nifty, Gold, Silver, Crude Oil, Bitcoin, Nasdaq) with a single
momentum score from -10 to +10, a Bullish / Neutral / Bearish label, a divergence flag and a sparkline.

Everything is computed from daily candles (TradingView history, no login) with plain, explainable maths:

    score = day move (+/-3) + intraday pressure (+/-2) + position vs the 20-day average (+/-3) + RSI(14) bias (+/-2)

    * day move   : today's % change divided by the instrument's own average daily range, squashed with tanh,
                   so a 1% day means more for Nifty than for Bitcoin.
    * vs EMA20   : how far the close sits above/below its 20-day EMA, in the same range-adjusted units.
    * intraday   : how far price has come back from today's high versus up from today's low, in range units - a big
                   slide off the high (sellers in control) pulls the score down even when the close-to-close change is small.
    * RSI bias   : (RSI14 - 50) / 25, limited to +/-1, times 2.
    * action     : the short-term part (day move + intraday) decides SELL ON RISE / BUY ON DIPS; when it is quiet the
                   trend part (20-day average + RSI) decides; otherwise WAIT. Zone, stop and targets are sized from the
                   instrument's own average daily range and today's high / low.
    * label      : score >= +2 Bullish, <= -2 Bearish, otherwise Neutral.
    * divergence : price makes a higher high while RSI makes a lower high (bearish), or price makes a
                   lower low while RSI makes a higher low (bullish), comparing the last 10 daily bars
                   with the 10 before them.

This is an informational read of recent price action. It is not a prediction and not advice.
"""
import math
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

import shared_cache

router = APIRouter(prefix="/api")

IST = timezone(timedelta(hours=5, minutes=30))

# key, display name, TradingView symbol, currency prefix
INSTRUMENTS = [
    ("NIFTY", "NIFTY", "NSE:NIFTY", "₹"),
    ("SENSEX", "SENSEX", "BSE:SENSEX", "₹"),
    ("BANKNIFTY", "BANKNIFTY", "NSE:BANKNIFTY", "₹"),
    ("GOLD", "GOLD", "COMEX:GC1!", "$"),
    ("SILVER", "SILVER", "COMEX:SI1!", "$"),
    ("CRUDEOIL", "CRUDEOIL", "NYMEX:CL1!", "$"),
    ("BITCOIN", "BITCOIN", "BITSTAMP:BTCUSD", "$"),
    ("NASDAQ", "NASDAQ", "NASDAQ:NDX", ""),
]

BULL_AT, BEAR_AT = 2.0, -2.0
BARS = 90
TTL = 90  # seconds
BUDGET = 18 if os.environ.get("VERCEL") else 45     # seconds to wait for all eight instruments
_cache = {"ts": 0.0, "data": None, "ttl": 90}
_lock = threading.Lock()

METHOD = {
    "summary": "Score = day move (±3) + intraday pressure — slide from today's high vs bounce from today's low (±2) + position vs 20-day average (±3) + RSI(14) bias (±2). Range −10 to +10.",
    "action": "Sell on rise / Buy on dips comes from today's move and intraday pressure first; if today is quiet, from the 20-day trend and RSI; otherwise Wait. Zone, stop-loss and targets are sized from the instrument's average daily range and today's high/low.",
    "label": "Bullish at +2 or more, Bearish at −2 or less, otherwise Neutral.",
    "divergence": "Bearish: price makes a higher high but RSI makes a lower high. Bullish: price makes a lower low but RSI makes a higher low (last 10 daily bars vs the 10 before).",
    "sparkline": "Closing prices of the last 14 daily candles.",
    "source": "Daily candles from the TradingView feed. Indian indices and stocks use the live quote for today (the free feed is about 15 min late); crypto is live; US indices, gold, silver and crude are about 10 min delayed.",
    "note": "Informational read of recent price action only. Not a prediction, not advice.",
}


def market_open(now=None):
    now = now or datetime.now(IST)
    if now.weekday() >= 5:
        return False
    return (now.hour, now.minute) >= (9, 15) and (now.hour, now.minute) <= (15, 30)


def ema(vals, n):
    k, e, out = 2 / (n + 1), None, []
    for v in vals:
        e = v if e is None else v * k + e * (1 - k)
        out.append(e)
    return out


def rsi_series(closes, n=14):
    """Wilder RSI. Returns a list the same length as closes (None until enough data)."""
    out = [None] * len(closes)
    if len(closes) <= n:
        return out
    gains = losses = 0.0
    for i in range(1, n + 1):
        d = closes[i] - closes[i - 1]
        gains += max(d, 0)
        losses += max(-d, 0)
    ag, al = gains / n, losses / n
    out[n] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    for i in range(n + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        ag = (ag * (n - 1) + max(d, 0)) / n
        al = (al * (n - 1) + max(-d, 0)) / n
        out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def analyse(bars):
    """bars: list of [t, o, h, l, c, v] oldest to newest. Returns the card payload or None."""
    bars = [b for b in bars if b and b[4]]
    if len(bars) < 30:
        return None
    closes = [b[4] for b in bars]
    highs, lows = [b[2] for b in bars], [b[3] for b in bars]
    last, prev = closes[-1], closes[-2]
    chg_pct = (last - prev) / prev * 100 if prev else 0.0
    rng = [(h - l) / c * 100 for h, l, c in zip(highs[-14:], lows[-14:], closes[-14:]) if c]
    avg_rng = max(sum(rng) / len(rng), 0.05) if rng else 1.0

    e20 = ema(closes, 20)[-1]
    dev = (last - e20) / e20 * 100 if e20 else 0.0
    rs = rsi_series(closes)
    rsi = rs[-1] if rs[-1] is not None else 50.0

    o_d, h_d, l_d = bars[-1][1] or last, max(highs[-1], last), min(lows[-1], last)
    from_hi = (h_d - last) / last * 100 if last else 0.0     # how far it has slid off today's high
    from_lo = (last - l_d) / last * 100 if last else 0.0     # how far it has bounced off today's low
    a = 3 * math.tanh(chg_pct / avg_rng)
    d = 2 * math.tanh(1.2 * (from_lo - from_hi) / avg_rng)
    b = 3 * math.tanh(dev / (1.5 * avg_rng))
    c = 2 * max(-1.0, min(1.0, (rsi - 50) / 25))
    score = round(a + d + b + c, 1)
    play = _play(a + d, b + c, last, h_d, l_d, avg_rng, from_hi, from_lo)
    label = "BULLISH" if score >= BULL_AT else "BEARISH" if score <= BEAR_AT else "NEUTRAL"

    # divergence: last 10 bars vs the 10 before
    div = None
    if len(closes) >= 40 and all(r is not None for r in rs[-20:]):
        r_hi, p_hi = max(highs[-10:]), max(highs[-20:-10])
        r_lo, p_lo = min(lows[-10:]), min(lows[-20:-10])
        rr_hi, pr_hi = max(rs[-10:]), max(rs[-20:-10])
        rr_lo, pr_lo = min(rs[-10:]), min(rs[-20:-10])
        if r_hi > p_hi and rr_hi < pr_hi - 2:
            div = "BEARISH"
        elif r_lo < p_lo and rr_lo > pr_lo + 2:
            div = "BULLISH"

    reasons = []
    reasons.append(f"Day move {chg_pct:+.2f}% against a normal daily range of {avg_rng:.2f}%")
    reasons.append(f"Intraday: {from_hi:.2f}% off today's high {h_d:,.2f}, {from_lo:.2f}% above today's low {l_d:,.2f}"
                   + (" - sellers in control" if d <= -0.8 else " - buyers in control" if d >= 0.8 else ""))
    reasons.append(f"Close is {abs(dev):.2f}% {'above' if dev >= 0 else 'below'} its 20-day average")
    reasons.append(f"RSI(14) is {rsi:.0f} ({'strong' if rsi >= 60 else 'weak' if rsi <= 40 else 'balanced'})")
    if div:
        reasons.append(f"{div.title()} divergence: price and RSI disagree over the last 20 bars")

    return {
        "price": round(last, 2),
        "chgPct": round(chg_pct, 2),
        "score": score,
        "label": label,
        "divergence": div,
        "spark": [round(x, 2) for x in closes[-14:]],
        "action": play,
        "detail": {
            "rsi": round(rsi, 1),
            "ema20": round(e20, 2),
            "vsEma20Pct": round(dev, 2),
            "avgRangePct": round(avg_rng, 2),
            "high20": round(max(highs[-20:]), 2),
            "low20": round(min(lows[-20:]), 2),
            "dayHigh": round(h_d, 2), "dayLow": round(l_d, 2), "dayOpen": round(o_d, 2),
            "parts": {"dayMove": round(a, 1), "intraday": round(d, 1), "trend": round(b, 1), "rsi": round(c, 1)},
            "reasons": reasons,
        },
    }


def _play(short, trend, last, hi, lo, avg_rng, from_hi, from_lo):
    """SELL ON RISE / BUY ON DIPS / WAIT with a zone, stop and two targets sized from one normal day's range (u)."""
    u = last * avg_rng / 100
    r = lambda v: round(v, 2)
    if short <= -1.5 or (abs(short) < 1.5 and trend <= -2):
        side, why = "SELL", (f"Sold off today - {from_hi:.1f}% off the high {hi:,.2f}" if short <= -1.5 else "Below its 20-day average with weak RSI")
        z_lo, z_hi = last + 0.15 * u, min(max(hi, last + 0.3 * u), last + 0.6 * u)
        sl = max(hi, z_hi) + 0.15 * u
        out = {"side": side, "label": "SELL ON RISE", "zone": [r(z_lo), r(z_hi)], "sl": r(sl), "targets": [r(last - 0.5 * u), r(min(lo - 0.25 * u, last - u))]}
        if trend >= 1:
            why += " - counter-trend: the 20-day trend is still up, keep it quick"
    elif short >= 1.5 or (abs(short) < 1.5 and trend >= 2):
        side, why = "BUY", (f"Strong today - {from_lo:.1f}% up from the low {lo:,.2f}" if short >= 1.5 else "Above its 20-day average with firm RSI")
        z_hi, z_lo = last - 0.15 * u, max(min(lo, last - 0.3 * u), last - 0.6 * u)
        sl = min(lo, z_lo) - 0.15 * u
        out = {"side": side, "label": "BUY ON DIPS", "zone": [r(z_lo), r(z_hi)], "sl": r(sl), "targets": [r(last + 0.5 * u), r(max(hi + 0.25 * u, last + u))]}
        if trend <= -1:
            why += " - counter-trend: the 20-day trend is still down, keep it quick"
    else:
        return {"side": "WAIT", "label": "WAIT", "range": [r(lo), r(hi)],
                "why": f"No clear edge - range {lo:,.2f} to {hi:,.2f}; act only on a break of either side"}
    out["why"] = why
    return out


def live_overlay(bars, q):
    """Indian indices and stocks: the free chart feed is ~15 min late, so today's candle is rebuilt from the app's live
    quote (Upstox). If the feed's last bar is yesterday (its close = today's previous close) a new bar is added."""
    if not q or not (q.get("last") or 0) > 0 or not bars:
        return bars
    last, prev = float(q["last"]), float(q.get("prev") or 0)
    o = float(q.get("open") or 0) or last
    h = max(float(q.get("high") or 0) or last, last)
    l = min(float(q.get("low") or 0) or last, last)
    bars = [list(x) for x in bars]
    if prev > 0 and abs(bars[-1][4] - prev) / prev < 0.0005:
        bars.append([bars[-1][0] + 86400, o, h, l, last, 0])          # feed has no bar for today yet
    else:
        bars[-1][1:5] = [o, h, l, last]                               # live quote is the truth for today
    return bars


def _live_quote(key, sym):
    if not (sym.startswith("NSE:") or sym.startswith("BSE:")):
        return None
    try:
        import market_api
        return market_api.quote_map([key]).get(key)            # shared batch - no extra Upstox call
    except Exception:
        return None


def _compute(item):
    import market_api  # heavy module; imported lazily so tests of analyse() stay light
    key, name, sym, ccy = item
    last_err = "no data"
    for attempt in range(3):
        try:
            bars = market_api._tv_history(sym, "1D", BARS)
            lq = _live_quote(key, sym)
            if lq:
                bars = live_overlay(bars, lq)
            res = analyse(bars)
            if res:
                res.update(key=key, name=name, symbol=sym, ccy=ccy)
                return res
            last_err = "not enough history"
        except Exception as e:  # 429 / network: back off and retry
            last_err = str(e)[:80]
        time.sleep(1.2 * (attempt + 1))
    return {"key": key, "name": name, "symbol": sym, "ccy": ccy, "error": last_err}


def _fetch(item):
    """One instrument, shared across instances for TTL seconds (and kept 6 h as a stale fallback)."""
    key = item[0]
    got = shared_cache.get(f"obs|{key}")
    if got:
        return got
    res = _compute(item)
    if "error" not in res:
        shared_cache.set(f"obs|{key}", res, TTL)
        shared_cache.set(f"obs-stale|{key}", res, 6 * 3600)
    return res


def build():
    """All instruments within a time budget. Anything still running is answered from the stale copy, or marked
    `pending` so the page asks again in a few seconds (a serverless function must answer inside ~30 s)."""
    pool = ThreadPoolExecutor(max_workers=8)
    futs = {pool.submit(_fetch, it): it for it in INSTRUMENTS}
    done, _ = wait(futs, timeout=BUDGET)
    pool.shutdown(wait=False)
    items = []
    for it in INSTRUMENTS:
        fut = next(f for f, i in futs.items() if i is it)
        res = fut.result() if fut in done else None
        if res is None or "error" in res:
            old = shared_cache.get(f"obs-stale|{it[0]}")
            if old:
                res = dict(old, stale=True)
            elif res is None:
                res = {"key": it[0], "name": it[1], "symbol": it[2], "ccy": it[3], "pending": True}
        items.append(res)
    return {
        "items": items,
        "marketOpen": market_open(),
        "asOf": datetime.now(IST).isoformat(timespec="seconds"),
        "method": METHOD,
    }


def warm():
    """Own-server mode: build once in the background so the first visit is instant."""
    threading.Thread(target=lambda: observer(refresh=True), daemon=True, name="observer-warm").start()


@router.get("/observer")
def observer(refresh: bool = False):
    with _lock:
        fresh = _cache["data"] and time.time() - _cache["ts"] < _cache["ttl"]
        if refresh or not fresh:
            data = build()
            if any("error" not in i and not i.get("pending") for i in data["items"]) or not _cache["data"]:
                pending = any(i.get("pending") for i in data["items"])
                effective_ttl = 4 if pending else (300 if market_open() else 1800)
                _cache.update(ts=time.time(), data=data, ttl=effective_ttl)
            else:                       # every instrument failed: keep showing the last good read
                data = _cache["data"]
        else:
            data = _cache["data"]
    return data

# ---- any single stock or index (Trade screen) ----
TV_INDEX = {"NIFTY": "NSE:NIFTY", "BANKNIFTY": "NSE:BANKNIFTY", "FINNIFTY": "NSE:CNXFINANCE", "MIDCPNIFTY": "NSE:NIFTY_MID_SELECT",
            "NIFTYNXT50": "NSE:NIFTYJR", "SENSEX": "BSE:SENSEX", "BANKEX": "BSE:BANKEX", "INDIAVIX": "NSE:INDIAVIX"}


def tv_symbol(sym):
    s = (sym or "").upper().strip()
    if s in TV_INDEX:
        return TV_INDEX[s]
    return "NSE:" + "".join(c if c.isalnum() else "_" for c in s)


@router.get("/observer/one")
def observer_one(symbol: str):
    import re
    s = (symbol or "").upper().strip()
    if not re.fullmatch(r"[A-Z0-9&\-]{1,20}", s):
        return {"symbol": s, "error": "bad symbol"}
    key = f"obs1|{s}"
    got = shared_cache.get(key)
    if got:
        return got
    res = _compute((s, s, tv_symbol(s), "₹"))
    if "error" not in res:
        res["method"] = METHOD
        shared_cache.set(key, res, TTL)
    return res

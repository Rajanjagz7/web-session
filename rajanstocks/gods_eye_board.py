"""GOD'S EYE - The Observer: one score per market from real daily price history.

How a score is made (all from the instrument's own daily bars, no fixed numbers):

  component                     reading                                   points
  ----------------------------  ----------------------------------------  -------
  Price vs 20-day EMA           (close - EMA20) / ATR14                   -1 .. +1
  20 vs 50-day EMA              (EMA20 - EMA50) / ATR14                   -1 .. +1
  Momentum (RSI 14)             (RSI - 50) / 12.5                         -2 .. +2
  MACD histogram                hist / (0.25 x ATR14)                     -2 .. +2
  5-day move                    5-day change / (ATR14 x sqrt 5)           -2 .. +2
  Place in 20-day range         (position 0..1 - 0.5) x 4                 -2 .. +2
                                                                  total   -10 .. +10

  Bias: score >= +2.5 BULLISH, <= -2.5 BEARISH, otherwise NEUTRAL.
  Divergence (flag only, not added to the score): the last two swing highs (lows) of price
  versus RSI over the last 40 bars - price higher high + RSI lower high = bearish divergence,
  price lower low + RSI higher low = bullish divergence - reported only if the latest swing is
  within the last 10 bars.

Everything is ATR-normalised, so a quiet index and a volatile coin are judged on the same scale.
Informational only - a summary of trend and momentum, not a forecast or advice.
"""
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import requests
from fastapi import APIRouter, HTTPException

import shared_cache

router = APIRouter()
IST = timezone(timedelta(hours=5, minutes=30))
_http = requests.Session()
_http.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"})

MARKETS = [
    # key, display name, Yahoo symbol, group, live-app symbol (for the browser to overlay live ticks)
    ("NIFTY", "Nifty 50", "^NSEI", "India", "NIFTY"),
    ("SENSEX", "Sensex", "^BSESN", "India", "SENSEX"),
    ("BANKNIFTY", "Bank Nifty", "^NSEBANK", "India", "BANKNIFTY"),
    ("GOLD", "Gold", "GC=F", "Commodities", None),
    ("SILVER", "Silver", "SI=F", "Commodities", None),
    ("CRUDEOIL", "Crude Oil", "CL=F", "Commodities", None),
    ("BITCOIN", "Bitcoin", "BTC-USD", "Crypto", None),
    ("NASDAQ", "Nasdaq", "^IXIC", "US", None),
    ("DOW", "Dow Jones", "^DJI", "US", None),
]
BULL, BEAR = 2.5, -2.5

_mem = {}
_lock = threading.Lock()


# ----------------------------------------------------------------------------- indicators
def ema(vals, n):
    k, out, e = 2 / (n + 1), [], None
    for v in vals:
        e = v if e is None else v * k + e * (1 - k)
        out.append(e)
    return out


def rsi(closes, n=14):
    out = [None] * len(closes)
    if len(closes) <= n:
        return out
    gains = [max(closes[i] - closes[i - 1], 0) for i in range(1, len(closes))]
    losses = [max(closes[i - 1] - closes[i], 0) for i in range(1, len(closes))]
    ag, al = sum(gains[:n]) / n, sum(losses[:n]) / n
    out[n] = 100 - 100 / (1 + ag / al) if al else 100.0
    for i in range(n + 1, len(closes)):
        ag = (ag * (n - 1) + gains[i - 1]) / n
        al = (al * (n - 1) + losses[i - 1]) / n
        out[i] = 100 - 100 / (1 + ag / al) if al else 100.0
    return out


def atr(bars, n=14):
    tr = [bars[0]["h"] - bars[0]["l"]]
    for i in range(1, len(bars)):
        p = bars[i - 1]["c"]
        tr.append(max(bars[i]["h"] - bars[i]["l"], abs(bars[i]["h"] - p), abs(bars[i]["l"] - p)))
    out, a = [], None
    for i, t in enumerate(tr):
        a = t if a is None else (a * (n - 1) + t) / n
        out.append(a)
    return out


def macd_hist(closes):
    e12, e26 = ema(closes, 12), ema(closes, 26)
    line = [a - b for a, b in zip(e12, e26)]
    sig = ema(line, 9)
    return [a - b for a, b in zip(line, sig)]


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _pivots(vals, k=3, kind="high"):
    out = []
    for i in range(k, len(vals) - k):
        w = vals[i - k:i + k + 1]
        if None in w:
            continue
        if (kind == "high" and vals[i] == max(w)) or (kind == "low" and vals[i] == min(w)):
            out.append(i)
    return out


def divergence(bars, rs, look=40, recent=10):
    n = len(bars)
    lo = max(0, n - look)
    highs = [b["h"] for b in bars]
    lows = [b["l"] for b in bars]
    ph = [i for i in _pivots(highs, 3, "high") if i >= lo and rs[i] is not None]
    pl = [i for i in _pivots(lows, 3, "low") if i >= lo and rs[i] is not None]
    if len(ph) >= 2 and ph[-1] >= n - recent:
        a, b = ph[-2], ph[-1]
        if highs[b] > highs[a] and rs[b] < rs[a] - 1:
            return {"type": "bearish", "text": f"Price made a higher high ({highs[b]:,.2f} vs {highs[a]:,.2f}) but RSI made a lower high ({rs[b]:.0f} vs {rs[a]:.0f}) - momentum is fading under the rally",
                    "dates": [bars[a]["d"], bars[b]["d"]]}
    if len(pl) >= 2 and pl[-1] >= n - recent:
        a, b = pl[-2], pl[-1]
        if lows[b] < lows[a] and rs[b] > rs[a] + 1:
            return {"type": "bullish", "text": f"Price made a lower low ({lows[b]:,.2f} vs {lows[a]:,.2f}) but RSI made a higher low ({rs[b]:.0f} vs {rs[a]:.0f}) - selling pressure is weakening",
                    "dates": [bars[a]["d"], bars[b]["d"]]}
    return None


def score_at(bars, i, e20, e50, rs, mh, at):
    """Score for bar i (uses only bars up to i)."""
    c, a = bars[i]["c"], at[i] or 1e-9
    w = bars[max(0, i - 19):i + 1]
    hi, lo = max(b["h"] for b in w), min(b["l"] for b in w)
    pos = (c - lo) / (hi - lo) if hi > lo else 0.5
    c5 = bars[i - 5]["c"] if i >= 5 else bars[0]["c"]
    comps = [
        ("Price vs 20-day EMA", _clamp((c - e20[i]) / a, -1, 1), 1, f"{'above' if c >= e20[i] else 'below'} EMA20 {e20[i]:,.2f} by {abs(c - e20[i]) / a:.1f} ATR"),
        ("20 vs 50-day EMA", _clamp((e20[i] - e50[i]) / a, -1, 1), 1, f"EMA20 {'over' if e20[i] >= e50[i] else 'under'} EMA50 ({e50[i]:,.2f}) - {'uptrend' if e20[i] >= e50[i] else 'downtrend'} structure"),
        ("Momentum (RSI 14)", _clamp(((rs[i] or 50) - 50) / 12.5, -2, 2), 2, f"RSI {rs[i] or 50:.1f}" + (" - overbought zone" if (rs[i] or 50) >= 70 else " - oversold zone" if (rs[i] or 50) <= 30 else "")),
        ("MACD histogram", _clamp(mh[i] / (0.25 * a), -2, 2), 2, f"{mh[i]:+,.2f} and {'rising' if i and mh[i] > mh[i - 1] else 'falling'}"),
        ("5-day move", _clamp((c - c5) / (a * math.sqrt(5)), -2, 2), 2, f"{(c / c5 - 1) * 100:+.2f}% over 5 sessions"),
        ("Place in 20-day range", _clamp((pos - 0.5) * 4, -2, 2), 2, f"{pos * 100:.0f}% of the way from the 20-day low {lo:,.2f} to the high {hi:,.2f}"),
    ]
    return sum(p for _, p, _, _ in comps), comps, {"hi": hi, "lo": lo, "pos": pos}


def analyse(bars):
    closes = [b["c"] for b in bars]
    e20, e50, rs, mh, at = ema(closes, 20), ema(closes, 50), rsi(closes), macd_hist(closes), atr(bars)
    i = len(bars) - 1
    total, comps, rng = score_at(bars, i, e20, e50, rs, mh, at)
    hist = []
    for j in range(max(60, i - 29), i + 1):
        hist.append(round(score_at(bars, j, e20, e50, rs, mh, at)[0], 1))
    sc = round(total, 1)
    bias = "BULLISH" if sc >= BULL else "BEARISH" if sc <= BEAR else "NEUTRAL"
    strength = "strong" if abs(sc) >= 6 else "moderate" if abs(sc) >= BULL else "weak"
    return {
        "score": sc, "bias": bias, "strength": strength,
        "components": [{"name": n, "points": round(p, 2), "max": mx, "text": t} for n, p, mx, t in comps],
        "divergence": divergence(bars, rs),
        "score_hist": hist,
        "indicators": {"rsi": round(rs[i] or 50, 1), "ema20": round(e20[i], 2), "ema50": round(e50[i], 2), "macd_hist": round(mh[i], 3),
                       "atr": round(at[i], 2), "atr_pct": round(at[i] / bars[i]["c"] * 100, 2),
                       "range20": {"hi": round(rng["hi"], 2), "lo": round(rng["lo"], 2), "pos": round(rng["pos"] * 100, 1)}},
    }


# ----------------------------------------------------------------------------- data
def _yahoo(ysym):
    r = _http.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ysym}", params={"range": "1y", "interval": "1d"}, timeout=10)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    q, meta = res["indicators"]["quote"][0], res.get("meta") or {}
    bars = []
    for k, ts in enumerate(res.get("timestamp") or []):
        o, h, l, c = (q[f][k] for f in ("open", "high", "low", "close"))
        if None in (o, h, l, c):
            continue
        bars.append({"d": datetime.fromtimestamp(ts, timezone.utc).astimezone(IST).date().isoformat(), "o": o, "h": h, "l": l, "c": c})
    live = meta.get("regularMarketPrice")
    if bars and live:
        b = bars[-1]  # keep the last bar's close at the live print so today's move is included
        b["c"] = live
        b["h"], b["l"] = max(b["h"], live), min(b["l"], live)
    prev = meta.get("chartPreviousClose") if len(bars) < 2 else bars[-2]["c"]
    return bars, {"price": live or (bars[-1]["c"] if bars else None), "prev": prev, "currency": meta.get("currency"),
                  "exchange": meta.get("exchangeName"), "market_time": meta.get("regularMarketTime")}


def _one(m):
    key, name, ysym, group, app_sym = m
    try:
        bars, meta = _yahoo(ysym)
        if len(bars) < 70:
            raise ValueError("not enough history")
        a = analyse(bars)
        px, pv = meta["price"], meta["prev"]
        a.update({"key": key, "name": name, "group": group, "app_sym": app_sym, "source": f"Yahoo Finance {ysym}",
                  "price": round(px, 2), "prev": round(pv, 2) if pv else None, "chg_pct": round((px / pv - 1) * 100, 2) if pv else None,
                  "currency": meta["currency"], "as_of_bar": bars[-1]["d"],
                  "spark": [round(b["c"], 2) for b in bars[-30:]], "ok": True})
        return a
    except Exception as e:
        return {"key": key, "name": name, "group": group, "app_sym": app_sym, "ok": False, "error": str(e)[:160]}


def _nse_open(now):
    try:
        from vedic_astro_report import NSE_HOLIDAYS
        hol = NSE_HOLIDAYS.get(now.year, {}).get(now.date().isoformat())
    except Exception:
        hol = None
    return now.weekday() < 5 and not hol and (9, 15) <= (now.hour, now.minute) < (15, 30), hol


def build_board():
    with ThreadPoolExecutor(8) as ex:
        items = list(ex.map(_one, MARKETS))
    now = datetime.now(IST)
    is_open, hol = _nse_open(now)
    ok = [x for x in items if x.get("ok")]
    return {"as_of": now.isoformat(timespec="seconds"), "nse_open": is_open, "holiday": hol, "items": items,
            "summary": {"bullish": sum(1 for x in ok if x["bias"] == "BULLISH"), "bearish": sum(1 for x in ok if x["bias"] == "BEARISH"),
                        "neutral": sum(1 for x in ok if x["bias"] == "NEUTRAL"),
                        "divergences": sum(1 for x in ok if x.get("divergence"))},
            "method": {"thresholds": {"bullish": BULL, "bearish": BEAR}, "range": [-10, 10]}}


@router.get("/api/godseye/board")
def board(refresh: bool = False):
    now = datetime.now(IST)
    ttl = 60 if _nse_open(now)[0] else 300
    key = "godseye:board:v1"
    with _lock:
        hit = _mem.get(key)
    if hit and not refresh and time.time() - hit[0] < ttl:
        return hit[1]
    data = None if refresh else shared_cache.get(key)
    if not data:
        data = build_board()
        if not any(x.get("ok") for x in data["items"]):
            raise HTTPException(502, "No market data could be loaded right now")
        shared_cache.set(key, data, ttl)
    with _lock:
        _mem[key] = (time.time(), data)
    return data

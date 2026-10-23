"""Gann intraday time cycles + price "vibration" zones for any index / F&O stock, or one of its ATM option premiums.

Time cycles (trading minutes, 09:15-15:30 IST):
  - counted from today's open (09:15)
  - counted from the previous session's HIGH bar and LOW bar (carrying over the close into today)
  - counted from today's high / low so far (live)
  Gann counts: 15, 30, 45, 60, 90, 120, 135, 180, 225, 270, 315, 360 minutes. Times that land within 5 minutes of each other
  are merged; more sources = stronger. 90 / 180 / 360 counts are "major".
Price zones:
  - Square-of-9 levels around the previous close of the chosen series (45 deg steps): nearest support = "vibration zone"
  - index / stock option chain: max pain strike, highest call OI (resistance) and highest put OI (support)
Traditional Gann technique - a timing guide, not a validated forecast. Act only when price confirms at the time.
"""
import math
from datetime import datetime, timedelta

import market_api

IST = market_api.IST
OPEN, CLOSE = 9 * 60 + 15, 15 * 60 + 30
SESSION = CLOSE - OPEN                      # 375 trading minutes
COUNTS = (15, 30, 45, 60, 90, 120, 135, 180, 225, 270, 315, 360)
MAJOR = {90, 180, 360}


def _hm(m):
    return f"{int(m) // 60:02d}:{int(m) % 60:02d}"


def _bars(symbol="", ikey=""):
    r = market_api.candles(symbol=symbol, ikey=ikey, tf="5m", frm="", to="", recent=5) or {}
    out = {}
    for b in r.get("bars") or []:
        t = datetime.fromtimestamp(b["t"] / 1000, IST)
        m = t.hour * 60 + t.minute
        if OPEN <= m < CLOSE:
            out.setdefault(t.date().isoformat(), []).append({"m": m, "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]})
    return out


def _carry(start_m, n):
    """Minute-of-day `n` trading minutes after start_m in a previous session -> minute of TODAY (or None if not today)."""
    left = CLOSE - start_m
    if n <= left:
        return None                                  # lands in that earlier session
    rest = n - left
    return OPEN + rest if rest < SESSION else None


def max_pain(rows):
    strikes = [r["strike"] for r in rows]
    best, bp = None, None
    for P in strikes:
        pain = 0.0
        for r in rows:
            k = r["strike"]
            pain += (r.get("ce") or {}).get("oi", 0) * max(0.0, P - k) + (r.get("pe") or {}).get("oi", 0) * max(0.0, k - P)
        if bp is None or pain < bp:
            best, bp = P, pain
    return best


def build(symbol, mode="underlying", strike=None):
    """mode: underlying | ce | pe. strike: option strike (default ATM)."""
    sym = symbol.upper().strip()
    label, ikey, ch = sym, "", None
    try:
        ch = market_api.chain(sym, "")
    except Exception:
        ch = None
    if mode in ("ce", "pe"):
        if not ch or not ch.get("rows"):
            raise ValueError(f"{sym} has no option chain")
        k = float(strike) if strike else ch.get("atm")
        row = min(ch["rows"], key=lambda r: abs(r["strike"] - k))
        leg = row.get(mode) or {}
        if not leg.get("key"):
            raise ValueError("no such contract")
        ikey, label = leg["key"], f"{sym} {row['strike']:.0f} {mode.upper()} ({ch.get('expiry')})"
    days = _bars(symbol="" if ikey else sym, ikey=ikey)
    if not days:
        raise ValueError("no intraday candles")
    dates = sorted(days)
    now = datetime.now(IST)
    today = now.date().isoformat()
    cur = days.get(today) or []
    prev = days[dates[-1]] if dates[-1] != today else (days[dates[-2]] if len(dates) > 1 else [])
    if not prev:
        raise ValueError("no previous session")

    hits = []                                         # (minute today, source, count)
    for n in COUNTS:
        if OPEN + n < CLOSE:
            hits.append((OPEN + n, "open 09:15", n))
    ph = max(prev, key=lambda b: b["h"])
    pl = min(prev, key=lambda b: b["l"])
    for name, b in (("prev-day high " + _hm(ph["m"]), ph), ("prev-day low " + _hm(pl["m"]), pl)):
        for n in COUNTS:
            m = _carry(b["m"], n)
            if m is not None:
                hits.append((m, name, n))
    if cur:
        th = max(cur, key=lambda b: b["h"])
        tl = min(cur, key=lambda b: b["l"])
        for name, b in (("today's high " + _hm(th["m"]), th), ("today's low " + _hm(tl["m"]), tl)):
            for n in COUNTS:
                m = b["m"] + n
                if m < CLOSE:
                    hits.append((m, name, n))
    hits.sort()
    groups = []
    for m, src, n in hits:
        if groups and m - groups[-1]["m0"] <= 5:
            g = groups[-1]
        else:
            g = {"m0": m, "items": []}
            groups.append(g)
        g["items"].append((m, src, n))
    now_m = now.hour * 60 + now.minute if today == now.date().isoformat() else 0
    # price at each cycle time: the close of the 5-minute bar covering it (None while the cycle is still ahead)
    px_at = {}
    for b in cur:
        px_at[b["m"]] = b["c"]
    def _price_at(m):
        if m > now_m:
            return None
        for back in range(6):                          # the bar that covers the cycle time (bars are 5 min)
            if m - back in px_at:
                return px_at[m - back]
        return None
    cycles = []
    for g in groups:
        ms = [x[0] for x in g["items"]]
        mid = round(sum(ms) / len(ms))
        srcs = sorted({f"{n} min from {src}" for _, src, n in g["items"]})
        major = any(n in MAJOR for _, _, n in g["items"])
        score = len({src for _, src, _ in g["items"]}) + (1 if major else 0)
        p = _price_at(mid)
        cycles.append({"time": _hm(mid), "m": mid, "sources": srcs, "score": score,
                       "strength": "strong" if score >= 3 else "medium" if score == 2 else "minor",
                       "passed": bool(cur) and mid < now_m,
                       "price": round(p, 2) if p else None})
    pc = prev[-1]["c"]
    last = (cur[-1]["c"] if cur else pc)
    zones = []
    for nstep in range(-8, 9):
        if nstep == 0:
            continue
        r = math.sqrt(pc) + nstep * 0.25
        if r > 0:
            zones.append({"level": round(r * r, 2), "angle": f"{abs(nstep) * 45} deg {'above' if nstep > 0 else 'below'} prev close"})
    below = [z for z in zones if z["level"] < last]
    above = [z for z in zones if z["level"] > last]
    vib = max(below, key=lambda z: z["level"]) if below else None
    out = {"symbol": sym, "series": label, "mode": mode, "prevClose": round(pc, 2), "last": round(last, 2),
           "prevHigh": {"price": round(ph["h"], 2), "time": _hm(ph["m"])}, "prevLow": {"price": round(pl["l"], 2), "time": _hm(pl["m"])},
           "cycles": cycles, "zones": sorted(zones, key=lambda z: -z["level"]),
           "vibration": vib, "nextResistance": min(above, key=lambda z: z["level"]) if above else None,
           "asOf": now.isoformat(),
           "how": "Cycles: Gann minute counts (15-360) from the 09:15 open, the previous day's high/low bar and today's high/low; "
                  "times within 5 minutes are merged - more sources = stronger. Zones: Square-of-9 steps (45 deg) around the previous close; "
                  "the nearest one under the price is the vibration zone. Watch for price reaching a zone AT a cycle time."}
    if ch and ch.get("rows"):
        rows = ch["rows"]
        mce = max(rows, key=lambda r: (r.get("ce") or {}).get("oi", 0))
        mpe = max(rows, key=lambda r: (r.get("pe") or {}).get("oi", 0))
        out["chain"] = {"expiry": ch.get("expiry"), "spot": ch.get("spot"), "maxPain": max_pain(rows),
                        "maxCallOI": mce["strike"], "maxPutOI": mpe["strike"]}
    return out

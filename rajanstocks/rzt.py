"""Rajan Zone Trend (Z Trend) - one engine, three consumers.

The chart draws it client-side (rztCalc in static/index.html); this module is the
server-side copy so the Signals tab and the Auto Trader read the SAME numbers.

  1. GET /api/m/rzt          - live readout for the Trade > Signals card: state (BUY/SELL),
                               the trail line (= stop), zone-1 resistance / support, the last
                               flip and how every recent flip would have ended.
  2. rzt_scan()              - a daily-bar runner with the same shape as the other strategy
                               runners, so backtest.py ranks it and auto_trader.scan_all()
                               takes its signals with every other indicator.
  3. intraday_cands()        - fresh 5-minute flips on the indices for the auto trader.

Algorithm (identical to the chart and to rzt_backtest.py): an ATR trailing stop on the
close - trend is up while closes hold above the line, down while below; a flip is only
confirmed when the momentum bar (EMA 9/21 + RSI 14) is not STRONGLY the other way.
Zone-1 / Zone-2 resistance and support come from the last confirmed swing high / low.
"""
import math
import time
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

import market_api

IST = market_api.IST
OPEN_MIN, CLOSE_MIN = 9 * 60 + 15, 15 * 60 + 30

router = APIRouter(prefix="/api/m")

_cache: dict = {}


def ema(v, n):
    """Chart parity (index.html emaA): SMA seed over the first n values, then the EMA factor.
    The old first-value seed made the backend's Z Trend drift from the chart (different early
    flips, up to ~5 points on the trail line on short series)."""
    a, out, p, s, k = 2 / (n + 1), [], None, 0.0, 0
    for x in v:
        if p is None:
            s += x
            k += 1
            if k == n:
                p = s / n
                out.append(p)
            else:
                out.append(None)
        else:
            p = x * a + p * (1 - a)
            out.append(p)
    return out


def rsi(c, n=14):
    """Chart parity: Wilder smoothing with an SMA seed over the first n changes (NaN before that)."""
    out = [None] * len(c)
    g = l = 0.0
    for i in range(1, len(c)):
        d = c[i] - c[i - 1]
        u, dn = max(d, 0), max(-d, 0)
        if i <= n:
            g += u
            l += dn
            if i == n:
                g /= n
                l /= n
                out[i] = 100.0 if l == 0 else 100 - 100 / (1 + g / l)
        else:
            g = (g * (n - 1) + u) / n
            l = (l * (n - 1) + dn) / n
            out[i] = 100.0 if l == 0 else 100 - 100 / (1 + g / l)
    return out


def _rma_skip(vals, n):
    """Chart emaA with alpha=1/n: SMA seed over the first n finite values (None/NaN entries skipped)."""
    out, p, s, k = [None] * len(vals), None, 0.0, 0
    al = 1.0 / n
    for i, x in enumerate(vals):
        if x is None or x != x:
            continue
        if p is None:
            s += x
            k += 1
            if k == n:
                p = s / n
                out[i] = p
        else:
            p = x * al + p * (1 - al)
            out[i] = p
    return out


def adx(bars, n=14):
    """Chart parity (index.html adx): +DM/−DM/TR arrays, rma-smoothed, dx with (x+y)||1."""
    n_b = len(bars)
    if n_b < 2:
        return [None] * n_b
    pdm, mdm, tr = [None] * n_b, [None] * n_b, [None] * n_b
    for i in range(1, n_b):
        u = bars[i]["h"] - bars[i - 1]["h"]
        dn = bars[i - 1]["l"] - bars[i]["l"]
        pdm[i] = u if (u > dn and u > 0) else 0.0
        mdm[i] = dn if (dn > u and dn > 0) else 0.0
        tr[i] = max(bars[i]["h"] - bars[i]["l"], abs(bars[i]["h"] - bars[i - 1]["c"]), abs(bars[i]["l"] - bars[i - 1]["c"]))
    a = _rma_skip(tr, n)
    p = _rma_skip(pdm, n)
    m = _rma_skip(mdm, n)
    pdi = [None if (a[i] is None or p[i] is None) else 100 * p[i] / a[i] for i in range(n_b)]
    mdi = [None if (a[i] is None or m[i] is None) else 100 * m[i] / a[i] for i in range(n_b)]
    dx = [None if (pdi[i] is None or mdi[i] is None) else 100 * abs(pdi[i] - mdi[i]) / ((pdi[i] + mdi[i]) or 1) for i in range(n_b)]
    return _rma_skip(dx, n)


def momentum(bars):
    """Momentum bar: +2 strong up, 1 mild up, 0 sideways, -1 mild down, -2 strong down."""
    c = [b["c"] for b in bars]
    n = len(c)
    e9, e21, r, ax = ema(c, 9), ema(c, 21), rsi(c, 14), adx(bars, 14)
    out = []
    for i in range(n):
        s = 0
        if e9[i] is not None and e21[i] is not None:
            s += 1 if e9[i] > e21[i] else -1
        if r[i] is not None:
            s += 1 if r[i] > 55 else -1 if r[i] < 45 else 0
        strong = ax[i] is not None and ax[i] > 20
        out.append((2 if strong else 1) if s >= 2 else (-2 if strong else -1) if s <= -2 else (1 if s == 1 else -1 if s == -1 else 0))
    return out


def true_ranges(bars):
    tr = []
    for i, b in enumerate(bars):
        if i == 0:
            tr.append(b["h"] - b["l"])
        else:
            pc = bars[i - 1]["c"]
            tr.append(max(b["h"] - b["l"], abs(b["h"] - pc), abs(b["l"] - pc)))
    return tr


def atr_series(bars, n=14):
    """Wilder ATR with the chart's SMA seed (index.html: rma(trA(d), n) over emaA)."""
    trs = true_ranges(bars)
    out, p, s, k = [], None, 0.0, 0
    al = 1.0 / n
    for t in trs:
        if p is None:
            s += t
            k += 1
            if k == n:
                p = s / n
                out.append(p)
            else:
                out.append(None)
        else:
            p = t * al + p * (1 - al)
            out.append(p)
    return out


def swings(bars, k=5):
    """Last confirmed swing high and low (k bars each side)."""
    n = len(bars)
    ph = pl = -1
    for j in range(n - 1 - k, k - 1, -1):
        if ph >= 0 and pl >= 0:
            break
        h_ok = all(bars[j]["h"] >= bars[x]["h"] for x in range(j - k, j + k + 1) if x != j and 0 <= x < n)
        l_ok = all(bars[j]["l"] <= bars[x]["l"] for x in range(j - k, j + k + 1) if x != j and 0 <= x < n)
        if h_ok and ph < 0:
            ph = j
        if l_ok and pl < 0:
            pl = j
    return ph, pl


def zones_from(bars, a, k=5):
    """Zone-1 / Zone-2 bands around the last confirmed swing high / low (chart parity)."""
    n = len(bars)
    ph, pl = swings(bars, k)
    z = {}
    if 0 <= ph < n:
        A = a[ph] or a[-1] or 0
        H = bars[ph]["h"]
        z["r1"] = [round(H - 0.6 * A, 2), round(H, 2)]
        z["r2"] = [round(H, 2), round(H + 1.2 * A, 2)]
    if 0 <= pl < n:
        A = a[pl] or a[-1] or 0
        L = bars[pl]["l"]
        z["s1"] = [round(L, 2), round(L + 0.6 * A, 2)]
        z["s2"] = [round(L - 1.2 * A, 2), round(L, 2)]
    return z


def compute(bars, ln=14, mult=2.0, flt=1, sw=5):
    """Per-bar Z Trend state. Returns dict with sig (flip per bar: 1 B / -1 S), dir (trend), lvl (trail line = stop),
    zones, momentum."""
    n = len(bars)
    a = atr_series(bars, ln)
    mb = momentum(bars)
    tr, d, sig = [None] * n, [0] * n, [0] * n
    lvl = [None] * n
    c = [b["c"] for b in bars]
    for i in range(1, n):
        L = mult * (a[i] or 0)
        pt = tr[i - 1] if tr[i - 1] is not None else c[i] - L
        if c[i] > pt and c[i - 1] > pt:
            tr[i] = max(pt, c[i] - L)
        elif c[i] < pt and c[i - 1] < pt:
            tr[i] = min(pt, c[i] + L)
        else:
            tr[i] = c[i] - L if c[i] > pt else c[i] + L
        dd = d[i - 1]
        if c[i - 1] <= pt and c[i] > tr[i]:
            dd = 1
        elif c[i - 1] >= pt and c[i] < tr[i]:
            dd = -1
        d[i] = dd
        if dd != d[i - 1] and i > ln:
            ok = (not flt) or (dd > 0 and mb[i] > -2) or (dd < 0 and mb[i] < 2)
            if ok:
                sig[i] = dd
        # the drawn STOP LINE is the chart's step line (rztCalc's lvl): the flip candle's low (B) /
        # high (S), carried forward until the next flip - NOT the continuous ATR trail (tr)
        lvl[i] = bars[i]["l"] if sig[i] > 0 else bars[i]["h"] if sig[i] < 0 else lvl[i - 1]
    return {"sig": sig, "dir": d, "lvl": lvl, "trail": tr, "zones": zones_from(bars, a, sw), "mb": mb, "atr": a}


def flip_history(bars, res, i0=0):
    """Every recent flip with the outcome it would have given: entry at the flip candle's close,
    stop at that candle's low (B) / high (S), exit at the stop, the next opposite flip, or the
    session end - the same rule the live backtest (rzt_backtest.py) used. i0 limits it to the
    last session so the card shows one coherent timeline."""
    sig = res["sig"]
    n = len(bars)
    flips = [i for i in range(max(0, i0), n) if sig[i]]
    out = []
    for i in flips[-8:]:
        b = bars[i]
        up = sig[i] > 0
        entry = b["c"]
        stop = b["l"] if up else b["h"]
        # find the exit bar for this flip: the stop first (a stop order fills before a flip on the same bar), then the opposite flip
        j_end = n - 1
        for j in range(i + 1, n):
            bb = bars[j]
            if (bb["l"] <= stop if up else bb["h"] >= stop):
                j_end = j
                break
            if sig[j] == -sig[i]:
                j_end = j
                break
        exit_px = bars[j_end]["c"]
        pts = (exit_px - entry) if up else (entry - exit_px)
        stop_hit = j_end < n - 1 and (bars[j_end]["l"] <= stop if up else bars[j_end]["h"] >= stop) and not sig[j_end]
        out.append({
            "time": _hm(bars[i]["m"]) if "m" in bars[i] else str(bars[i].get("date", "")),
            "signal": "B" if up else "S",
            "entry": round(entry, 2), "stop": round(stop, 2),
            "exit": round(exit_px, 2), "pts": round(pts, 2),
            "result": "STOP" if stop_hit else ("FLIP" if sig[j_end] == -sig[i] else "OPEN" if j_end == n - 1 else "FLIP"),
            "bars": j_end - i,
        })
    return out


def _hm(m):
    return f"{int(m) // 60:02d}:{int(m) % 60:02d}"


def _bars(symbol="", ikey="", tf="5m", recent=5):
    try:
        r = market_api.candles(symbol=symbol, ikey=ikey, tf=tf, frm="", to="", recent=recent) or {}
    except Exception:
        time.sleep(0.6)                                    # Upstox throttles in bursts: one patient retry
        r = market_api.candles(symbol=symbol, ikey=ikey, tf=tf, frm="", to="", recent=recent) or {}
    out = []
    for b in r.get("bars") or []:
        t = datetime.fromtimestamp(b["t"] / 1000, IST)
        m = t.hour * 60 + t.minute
        out.append({"m": m, "d": t.date().isoformat(), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "t": b["t"]})
    return out


def last_session_start(bars):
    """Index of the first bar of the most recent session in the series."""
    if not bars:
        return 0
    d = bars[-1]["d"]
    for i in range(len(bars) - 1, -1, -1):
        if bars[i]["d"] != d:
            return i + 1
    return 0


def readout(symbol, mode="underlying", strike=None, tf="5m", ln=14, mult=2.0, flt=1, sw=5, fresh=False):
    """Live Z Trend readout for the Signals card. mode: underlying | ce | pe (strike defaults to ATM)."""
    sym = str(symbol or "NIFTY").upper().strip()
    label, ikey = sym, ""
    ch = None
    if mode in ("ce", "pe"):
        ch = market_api.chain(sym, "")
        if not ch or not ch.get("rows"):
            raise ValueError(f"{sym} has no option chain")
        k = float(strike) if strike else ch.get("atm")
        row = min(ch["rows"], key=lambda r: abs(r["strike"] - k))
        leg = row.get(mode) or {}
        if not leg.get("key"):
            raise ValueError("no such contract")
        ikey, label = leg["key"], f"{sym} {row['strike']:.0f} {mode.upper()}"
    bars = _bars(symbol="" if ikey else sym, ikey=ikey, tf=tf)
    if len(bars) < ln + 5:
        raise ValueError(f"not enough {tf} bars yet ({len(bars)})")
    res = compute(bars, ln, mult, flt, sw)
    i0 = last_session_start(bars)
    last = bars[-1]
    d = res["dir"][-1]
    sig = res["sig"]
    last_flip = max((i for i in range(i0, len(sig)) if sig[i]), default=None)
    z = res["zones"]
    trail = res["lvl"][-1]
    out = {
        "symbol": sym, "series": label, "mode": mode, "tf": tf,
        "params": {"atrLen": ln, "mult": mult, "filter": bool(flt), "swing": sw},
        "state": "BUY" if d > 0 else "SELL" if d < 0 else "WAIT",
        "price": round(last["c"], 2),
        "sl": round(trail, 2) if trail is not None and math.isfinite(trail) else None,
        "atrTrail": round(res["trail"][-1], 2) if res["trail"][-1] is not None and math.isfinite(res["trail"][-1]) else None,
        "resistance": round(sum(z["r1"]) / 2, 2) if z.get("r1") else None,
        "support": round(sum(z["s1"]) / 2, 2) if z.get("s1") else None,
        "zones": z,
        "momentum": res["mb"][-1],
        "momentumLabel": {2: "strong up", 1: "mild up", 0: "sideways", -1: "mild down", -2: "strong down"}.get(res["mb"][-1], "—"),
        "lastFlip": None,
        "flips": flip_history(bars, res, i0),
        "session": bars[i0]["d"] if i0 < len(bars) else None,
        "asOf": datetime.now(IST).isoformat(),
        "how": "B when the ATR trend line flips under price (that line is the stop); S when it flips above. "
               "Zones come from the last confirmed swing high / low. Same engine as the chart and the backtest.",
    }
    if last_flip is not None:
        fb = bars[last_flip]
        up = sig[last_flip] > 0
        flip_stop = res["lvl"][last_flip]
        if flip_stop is None or not math.isfinite(flip_stop):
            flip_stop = fb["l"] if up else fb["h"]
        out["lastFlip"] = {"time": _hm(fb["m"]), "signal": "B" if up else "S",
                           "price": round(fb["c"], 2), "stop": round(flip_stop, 2),
                           "barsAgo": len(bars) - 1 - last_flip}
    return out


# ───────────────────────── daily runner (backtest + auto trader) ─────────────────────────
def rzt_scan(symbol: str, lookback_days: int = 400, ln=14, mult=2.0, flt=1, sw=5):
    """Daily-bar runner with the same output shape as the other strategy runners:
    {"symbol", "columns", "current", "bars": [{date, close, signal, stop, ...}]}. The auto trader reads
    bars[-1].signal / bars[-1].stop exactly like every other indicator."""
    import bar_source
    bars = bar_source.daily_bars(symbol, lookback_days)
    if len(bars) < ln + 10:
        return {"symbol": symbol, "columns": [{"key": "trail", "label": "Z Trend line"}], "current": None, "bars": []}
    res = compute([{"m": 0, "o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]} for b in bars], ln, mult, flt, sw)
    rows = []
    for i, b in enumerate(bars):
        sg = res["sig"][i]
        rows.append({"date": b["date"], "open": b["open"], "high": b["high"], "low": b["low"], "close": b["close"],
                     "signal": "BUY" if sg > 0 else "SELL" if sg < 0 else "",
                     "stop": round(res["lvl"][i], 2) if res["lvl"][i] is not None and math.isfinite(res["lvl"][i]) else None,
                     "trail": round(res["trail"][i], 2) if res["trail"][i] is not None and math.isfinite(res["trail"][i]) else None})
    last = rows[-1]
    return {"symbol": symbol,
            "columns": [{"key": "trail", "label": "Z Trend line"}],
            "current": {"date": last["date"], "close": last["close"], "signal": last["signal"],
                        "state": "BUY" if res["dir"][-1] > 0 else "SELL" if res["dir"][-1] < 0 else "WAIT",
                        "stop": last["stop"], "trail": last["trail"]},
            "bars": rows[-300:]}


def intraday_cands(syms=None, fresh_min=15):
    """Fresh 5-minute Z Trend flips on the given symbols (default: the 5 indices) - the intraday
    signal the auto trader can act on. Returns candidate dicts in scan_all's shape."""
    syms = syms or ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]
    out = []
    now = datetime.now(IST)
    now_m = now.hour * 60 + now.minute
    for s in syms:
        try:
            key = ("rzt:intra", s, now.date().isoformat())
            hit = _cache.get(key)
            if hit and time.time() - hit[0] < 240:
                rows = hit[1]
            else:
                bars = [b for b in _bars(symbol=s, tf="5m", recent=3) if OPEN_MIN <= b["m"] < CLOSE_MIN]
                if len(bars) < 20:
                    continue
                res = compute(bars)
                rows = []
                for i in range(len(bars)):
                    if res["sig"][i]:
                        up = res["sig"][i] > 0
                        rows.append({"m": bars[i]["m"], "signal": "BUY" if up else "SELL",
                                     "price": round(bars[i]["c"], 2), "stop": round(bars[i]["l"] if up else bars[i]["h"], 2)})
                _cache[key] = (time.time(), rows)
                if len(_cache) > 200:
                    _cache.clear()
            for r in rows:
                if 0 <= now_m - r["m"] <= fresh_min:
                    out.append({"key": "rzt-intraday", "sym": s, "side": r["signal"], "asOf": now.date().isoformat(),
                                "score": 0.55, "indStop": r["stop"], "variant": "fixed", "filter": "none",
                                "kind": "index", "source": f"Z Trend {r['signal']} flip on the 5-minute chart at {_hm(r['m'])}",
                                "label": "Z Trend (intraday)"})
        except Exception:
            continue
    return out


@router.get("/rzt")
def rzt(symbol: str = "NIFTY", mode: str = "underlying", strike: float = 0, tf: str = "5m",
        ln: int = Query(14, ge=2, le=100), mult: float = Query(2.0, ge=.5, le=6),
        flt: int = Query(1, ge=0, le=1), sw: int = Query(5, ge=2, le=30), refresh: bool = False):
    """Live Z Trend readout for the Trade > Signals card."""
    mode = mode.lower() if mode.lower() in ("underlying", "ce", "pe") else "underlying"
    tf = tf if tf in ("1m", "3m", "5m", "15m") else "5m"
    k = (symbol.upper(), mode, strike, tf, ln, mult, flt, sw)
    hit = _cache.get(("rzt:ro", k))
    ttl = 90 if market_api.market_open() else 600
    if not refresh and hit and time.time() - hit[0] <= ttl:
        return hit[1]
    try:
        r = readout(symbol, mode, strike or None, tf, ln, mult, flt, sw)
        _cache[("rzt:ro", k)] = (time.time(), r)
        _cache[("rzt:stale", k)] = (time.time(), r)        # last good copy: served when a rebuild fails
        if len(_cache) > 400:
            _cache.clear()
        return r
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        stale = _cache.get(("rzt:stale", k)) or hit
        if stale and time.time() - stale[0] < 6 * 3600:
            out = dict(stale[1])
            out["stale"] = True
            return out                                     # degrade to the last good readout, never 502
        raise HTTPException(502, f"Z Trend unavailable: {str(e)[:160]}")

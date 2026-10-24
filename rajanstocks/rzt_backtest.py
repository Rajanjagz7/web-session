"""Rajan Zone Trend on real 1-minute prices of expired NIFTY / BANKNIFTY / SENSEX options (ATM / OTM only; same data and
cache as premium_backtest.py).

NOTE (2026-10-25 audit): this offline grid keeps its own simpler seeding (first-value EMA/ATR, immediate
Wilder RSI). The LIVE engine (rzt.py) was since aligned to the chart's SMA-seeded math, so numbers here
are not directly comparable to the live Signals card / auto trader. Stored JSON predates that change;
kept as-is by decision (no re-run).

Option premiums can only be BOUGHT here, so: B = buy the premium at the signal candle's close, stop = the B candle's low
(the signal line), exit on the next S (at its close), the stop, or 15:25. One position at a time per contract, entries
09:20-15:00. Grid: timeframe 1 / 3 / 5 minutes, ATR length 10 / 14, multiplier 1.5 / 2 / 3, momentum filter off / on.
"""
import json
import os
import sys
import time
import concurrent.futures as cf
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import premium_backtest as PB  # noqa: E402

GRID = [(tf, ln, mu, fl) for tf in (1, 3, 5) for ln in (10, 14) for mu in (1.5, 2.0, 3.0) for fl in (0, 1)]
FIRST, LAST, EOD = 9 * 60 + 20, 15 * 60, 15 * 60 + 25


def resample(bars, k):
    if k == 1:
        return bars
    out, cur = [], None
    for m, o, h, l, c in bars:
        b = (m - 555) // k
        if cur is None or cur[0] != b:
            if cur:
                out.append(tuple(cur[1:]))
            cur = [b, m, o, h, l, c]
        else:
            cur[3] = max(cur[3], h); cur[4] = min(cur[4], l); cur[5] = c
    if cur:
        out.append(tuple(cur[1:]))
    return out


def ema(v, n):
    a, o, e = 2 / (n + 1), [], None
    for x in v:
        e = x if e is None else e + a * (x - e)
        o.append(e)
    return o


def rsi(c, n=14):
    o, g, l = [50.0] * len(c), 0.0, 0.0
    for i in range(1, len(c)):
        d = c[i] - c[i - 1]
        g = (g * (n - 1) + max(d, 0)) / n
        l = (l * (n - 1) + max(-d, 0)) / n
        o[i] = 100 - 100 / (1 + g / l) if l > 0 else 100.0
    return o


def mb(bars):
    c = [b[4] for b in bars]
    e9, e21, r = ema(c, 9), ema(c, 21), rsi(c)
    out = []
    for i in range(len(c)):
        s = (1 if e9[i] > e21[i] else -1) + (1 if r[i] > 55 else -1 if r[i] < 45 else 0)
        out.append(2 if s >= 2 else -2 if s <= -2 else s)
    return out


def signals(bars, ln, mu, fl):
    n = len(bars)
    if n < ln + 3:
        return [0] * n                   # too few candles (short day on 3m / 5m): no signals
    tr, a, prev = [], [], None
    for i, (m, o, h, l, c) in enumerate(bars):
        t = h - l if i == 0 else max(h - l, abs(h - bars[i - 1][4]), abs(l - bars[i - 1][4]))
        prev = t if prev is None else (prev * (ln - 1) + t) / ln
        a.append(prev)
    m_ = mb(bars) if fl else None
    c = [b[4] for b in bars]
    trail, d, sig = [None] * n, [0] * n, [0] * n
    for i in range(1, n):
        L = mu * a[i]
        pt = trail[i - 1] if trail[i - 1] is not None else c[i] - L
        if c[i] > pt and c[i - 1] > pt:
            trail[i] = max(pt, c[i] - L)
        elif c[i] < pt and c[i - 1] < pt:
            trail[i] = min(pt, c[i] + L)
        else:
            trail[i] = c[i] - L if c[i] > pt else c[i] + L
        dd = d[i - 1]
        if c[i - 1] <= pt and c[i] > trail[i]:
            dd = 1
        elif c[i - 1] >= pt and c[i] < trail[i]:
            dd = -1
        d[i] = dd
        if dd != d[i - 1] and i > ln:
            if not fl or (dd > 0 and m_[i] > -2) or (dd < 0 and m_[i] < 2):
                sig[i] = dd
    return sig


def trades(bars, sig):
    out, i, n = [], 0, len(bars)
    while i < n:
        m = bars[i][0]
        if sig[i] > 0 and FIRST <= m <= LAST:
            entry, stop = bars[i][4], bars[i][3]
            if entry - stop <= 0 or entry < 5:
                i += 1
                continue
            res = None
            for j in range(i + 1, n):
                mj, o, h, l, c = bars[j]
                if l <= stop:
                    res = stop - entry; break
                if sig[j] < 0:
                    res = c - entry; break
                if mj >= EOD:
                    res = c - entry; break
            if res is None:
                res = bars[-1][4] - entry; j = n
            out.append({"pts": round(res, 2), "risk": round(entry - stop, 2), "entry": round(entry, 2)})
            i = j + 1
        else:
            i += 1
    return out


SPLIT = "2026-04-01"      # older = before, recent = from this date (about the last 30% of the data)


def _acc():
    return {"n": 0, "w": 0, "pts": 0.0, "gw": 0.0, "gl": 0.0, "r": 0.0}


def _add(a, pts, risk):
    a["n"] += 1; a["pts"] += pts; a["r"] += pts / risk
    if pts > 0:
        a["w"] += 1; a["gw"] += pts
    else:
        a["gl"] -= pts


def _fin(a):
    if not a["n"]:
        return {"n": 0}
    return {"n": a["n"], "win": round(a["w"] / a["n"], 3), "avgPts": round(a["pts"] / a["n"], 2),
            "pf": round(a["gw"] / a["gl"], 2) if a["gl"] else 99.0, "avgR": round(a["r"] / a["n"], 2)}


def run():
    """Running totals only (storing every trade of 36 setting combinations ran the GitHub runner out of memory)."""
    jobs = []
    for sym in PB.INDEX:
        w = PB.option_weeks(sym)
        print(f"{sym}: {len(w)} contracts", flush=True)
        jobs += w
    A = {g: {k: _acc() for k in ["all", "older", "recent"] + list(PB.INDEX)} for g in GRID}
    done = 0
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for j, days in ex.map(PB.fetch_contract, jobs):
            done += 1
            if done % 250 == 0:
                print(f"  {done}/{len(jobs)}", flush=True)
            for d in sorted(days):
                bars = days[d]
                if len(bars) < 60 or not PB.atm_otm(j, d):
                    continue
                per = "older" if d < SPLIT else "recent"
                for tf in (1, 3, 5):
                    bb = resample(bars, tf)
                    for g in GRID:
                        if g[0] != tf:
                            continue
                        for t in trades(bb, signals(bb, g[1], g[2], g[3])):
                            for k in ("all", per, j["sym"]):
                                _add(A[g][k], t["pts"], t["risk"])
    return A


def _main():
    t0 = time.time()
    A = run()
    rows = []
    for (tf, ln, mu, fl), acc in A.items():
        if not acc["all"]["n"]:
            continue
        rows.append({"tf": f"{tf}m", "atrLen": ln, "mult": mu, "filter": bool(fl), "all": _fin(acc["all"]),
                     "older": _fin(acc["older"]), "recent": _fin(acc["recent"]), "bySym": {s: _fin(acc[s]) for s in PB.INDEX}})
    rows.sort(key=lambda r: -min(r["older"].get("pf", 0), r["recent"].get("pf", 0)))
    res = {"generatedAt": datetime.now(PB.IST).isoformat(), "method": __doc__, "split": SPLIT, "rows": rows,
           "best": rows[0] if rows else None, "runtimeSec": round(time.time() - t0)}
    with open(os.path.join(HERE, "static", "rzt_backtest.json"), "w") as f:
        json.dump(res, f)
    for r in rows[:10]:
        print(r["tf"], r["atrLen"], r["mult"], r["filter"], r["all"], "| older", r["older"].get("pf"), "| recent", r["recent"].get("pf"))
    print(f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    try:
        _main()
    except Exception:
        import traceback
        for ln in traceback.format_exc().splitlines()[-12:]:
            print("::error::" + ln.replace("%", "%25"), flush=True)
        raise

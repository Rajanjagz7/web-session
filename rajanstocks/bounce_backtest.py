"""Premium support-bounce indicator: three ways to draw the support (blue) / resistance (red) lines, tested on real
1-minute prices of expired NIFTY / BANKNIFTY / SENSEX options (same contracts and cache as premium_backtest.py).

Only ATM / OTM options (calls at or above the day's ATM strike, puts at or below it).
Setup (option BUY - CE or PE premium):
  1. The premium trades down to the support line (low <= support + touch band).
  2. Then a 1-minute candle CLOSES above support + offset  -> buy at that close  ("BUY @ 190 ABOVE").
  3. Stop = support - stop buffer ("STOP LOSS 180"). One trade per contract per day, entries 09:30-15:00.
Exits compared: resistance line, 1:2 and 1:3 of the risk, or hold to 15:25.

Support / resistance variants:
  PDL   previous day's premium low / high
  ORB   low / high of today's first 15 minutes (09:15-09:29)
  SWING last confirmed intraday swing low / high (5 bars each side)
Offset / stop variants: entry at support +3% or +5%, stop 1% or 2% under support.
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

FIRST_ENTRY, LAST_ENTRY = 9 * 60 + 30, 15 * 60
OFFSETS = (0.03, 0.05)
STOPS = (0.01, 0.02)
TOUCH = 0.01          # "at support" = low within 1% above it
MIN_PREM = 10.0


def swing_levels(bars, i, k=5):
    """Last swing low / high confirmed by bar i (pivot at j with k bars each side, j + k <= i)."""
    lo = hi = None
    for j in range(i - k, k - 1, -1):
        if lo is None and all(bars[j][3] <= bars[x][3] for x in range(j - k, j + k + 1)):
            lo = bars[j][3]
        if hi is None and all(bars[j][2] >= bars[x][2] for x in range(j - k, j + k + 1)):
            hi = bars[j][2]
        if lo is not None and hi is not None:
            break
    return lo, hi


def bounce(bars, sup_fn, off, stp):
    """One bounce trade for the day (or none). sup_fn(i) -> (support, resistance) known at bar i."""
    touched_at = None
    for i, (m, o, h, l, c) in enumerate(bars):
        if m < FIRST_ENTRY or m > LAST_ENTRY:
            continue
        S, R = sup_fn(i)
        if not S or S < MIN_PREM:
            continue
        if l <= S * (1 + TOUCH):
            touched_at = S                      # premium came down to support
            continue
        if touched_at is None or abs(touched_at - S) > S * 0.02:
            continue
        trig = S * (1 + off)
        if c >= trig:
            stop = S * (1 - stp)
            sl = c - stop
            if sl <= 0:
                return None
            tg = {"1:2": c + 2 * sl, "1:3": c + 3 * sl, "hold to 15:25": None}
            if R and R > c + 0.5 * sl:
                tg["resistance"] = R
            res = PB.manage(bars, i, c, "BUY", sl, tg, at_close=True)
            return {"entry": round(c, 2), "support": round(S, 2), "res": res, "slPts": round(sl, 2), "time": f"{m // 60:02d}:{m % 60:02d}"}
    return None


def run():
    jobs = []
    for sym in PB.INDEX:
        w = PB.option_weeks(sym)
        print(f"{sym}: {len(w)} contracts", flush=True)
        jobs += w
    trades = {v: [] for v in ("PDL", "ORB", "SWING")}
    done = 0
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for j, days in ex.map(PB.fetch_contract, jobs):
            done += 1
            if done % 250 == 0:
                print(f"  {done}/{len(jobs)}", flush=True)
            prev = None
            for d in sorted(days):
                bars = days[d]
                if len(bars) < 60 or bars[0][0] > 9 * 60 + 20:
                    prev = bars if bars else prev
                    continue
                if not PB.atm_otm(j, d):
                    prev = bars
                    continue
                tag = {"sym": j["sym"], "date": d, "type": j["type"], "lot": j["lot"], "expiryDay": d == j["expiry"]}
                orb = [b for b in bars if b[0] < 9 * 60 + 30]
                variants = {"ORB": (lambda i, lo=min(b[3] for b in orb), hi=max(b[2] for b in orb): (lo, hi))}
                if prev:
                    pl, ph = min(b[3] for b in prev), max(b[2] for b in prev)
                    variants["PDL"] = (lambda i, lo=pl, hi=ph: (lo, hi))
                variants["SWING"] = (lambda i, bs=bars: swing_levels(bs, i))
                for v, fn in variants.items():
                    for off in OFFSETS:
                        for stp in STOPS:
                            t = bounce(bars, fn, off, stp)
                            if t:
                                trades[v].append({**tag, **t, "offset": f"+{off * 100:g}%", "stop": f"-{stp * 100:g}%"})
                prev = bars
    return trades


if __name__ == "__main__":
    t0 = time.time()
    T = run()
    res = {"generatedAt": datetime.now(PB.IST).isoformat(), "method": __doc__,
           "variants": {v: PB.summarize(ts, ["offset", "stop"]) for v, ts in T.items()},
           "bySym": {v: PB.summarize(ts, ["sym"]) for v, ts in T.items()},
           "counts": {v: len(ts) for v, ts in T.items()}, "runtimeSec": round(time.time() - t0)}
    with open(os.path.join(HERE, "public", "static" if os.path.exists(os.path.join(HERE, "public", "static")) else "static", "bounce_backtest.json"), "w") as f:
        json.dump(res, f)
    for v, rows in res["variants"].items():
        print("==", v, res["counts"][v])
        for r in rows:
            print(r["offset"], r["stop"], r["exit"], "ALL", r["all"], "| OOS", r["oos"])
    print(f"{time.time() - t0:.0f}s")

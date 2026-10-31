"""Small stop, big target: stop set by ATR (not by the swing / premium cap), target as a multiple of that stop, optional trail. Same entries (every single
indicator signal, 4 years), same decay / cost model as the backtest. Results in R (1R = the stop), so they are what a fixed-risk account would see.

    python atr_lab.py [days]   -> mock_round/atr_lab.csv
"""
import csv
import os
import sys
from collections import defaultdict
from datetime import date

import backtest as bt
import exit_lab as xl

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mock_round")


def atr_walk(bars, atr, i, side, kind, k, target_r=None, trail_m=None, trail_from=1.0):
    """Stop = k x ATR(14) of the signal bar. target_r: fixed target in R (None = no target). trail_m: after +trail_from R the stop trails the best price by
    trail_m R (and never sits below the entry once +1R was reached). Max 10 sessions, out one day before expiry. Returns net R."""
    if i + 1 >= len(bars) or atr[i] is None or atr[i] <= 0:
        return None
    d = 1 if side == "BUY" else -1
    entry = bars[i + 1]["open"]
    exp = bt.expiry_for(bars[i + 1]["date"], kind)
    dte = lambda j, frac: (exp - date.fromisoformat(bars[j]["date"])).days + frac
    d_entry = dte(i + 1, 0.26)
    risk = k * atr[i]
    if risk <= 0:
        return None
    prem = bt.est_premium(atr[i], kind, d_entry)
    cost_r = bt.COST * entry / risk
    stop, best = entry - d * risk, entry
    last = min(len(bars) - 1, i + bt.MAX_HOLD)

    def fin(u, j, why, when="mid"):
        frac = {"open": 0.26, "mid": 0.13, "close": 0.0}[when]
        return (d * (u - entry) / risk - cost_r - bt.theta_r(atr[i], kind, risk, d_entry, dte(j, frac)), j, why, risk * 0.5 / prem)
    for j in range(i + 1, last + 1):
        b = bars[j]
        if j > i + 1 and ((d > 0 and b["open"] <= stop) or (d < 0 and b["open"] >= stop)):
            return fin(b["open"], j, "SL", "open")
        if (b["low"] <= stop) if d > 0 else (b["high"] >= stop):
            return fin(stop, j, "SL")
        tgt = entry + d * target_r * risk if target_r else None
        if tgt is not None and ((b["high"] >= tgt) if d > 0 else (b["low"] <= tgt)):
            return fin(tgt, j, "T")
        best = max(best, b["high"]) if d > 0 else min(best, b["low"])
        bR = d * (best - entry) / risk
        if trail_m is not None and bR >= trail_from:
            t = max(entry, best - d * trail_m * risk) if d > 0 else min(entry, best - d * trail_m * risk)
            stop = max(stop, t) if d > 0 else min(stop, t)
        if dte(j, 0.0) <= 1:
            return fin(b["close"], j, "EXP", "close")
    if last == len(bars) - 1 and last < i + bt.MAX_HOLD:
        return None
    return fin(bars[last]["close"], last, "TIME", "close")


def main(days=1460):
    ents, full, atr, ix, first, last_day = xl.build(days)
    print(f"{first} .. {last_day}: {len(ents)} entries", flush=True)
    rows = []
    for k in (0.5, 0.75, 1.0, 1.5, 2.0):
        for name, tr, tm in (("target 2R", 2.0, None), ("target 3R", 3.0, None), ("target 4R", 4.0, None), ("target 6R", 6.0, None),
                             ("no target, trail 1R behind", None, 1.0), ("no target, trail 2R behind", None, 2.0), ("target 4R + trail 1.5R", 4.0, 1.5)):
            busy = defaultdict(lambda: -1)
            Rs, sl_prem = [], []
            for s, key, d, side, ist in ents:
                i = ix[s][d]
                if i <= busy[(s, key)]:
                    continue
                r = atr_walk(full[s], atr[s], i, side, "index" if s in bt.INDEX_SYMS else "stock", k, tr, tm)
                if not r:
                    continue
                busy[(s, key)] = r[1]
                Rs.append(r[0])
                sl_prem.append(r[3])
            n = len(Rs)
            w = [x for x in Rs if x > 0]
            l = [-x for x in Rs if x < 0]
            cum = pk = dd = 0.0
            for x in Rs:
                cum += x
                pk = max(pk, cum)
                dd = max(dd, pk - cum)
            sp = sorted(sl_prem)[n // 2]
            rows.append({"stop_ATR": k, "exit": name, "n": n, "win": round(100 * len(w) / n), "avgR": round(sum(Rs) / n, 3), "sumR": round(sum(Rs), 1),
                         "pf": round(sum(w) / sum(l), 2), "maxDD_R": round(dd, 1), "avgWin": round(sum(w) / len(w), 2), "avgLoss": round(-sum(l) / len(l), 2),
                         "median_stop_pct_of_premium": round(100 * sp)})
    with open(os.path.join(OUT, "atr_lab.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    print(f"{'stop':>6} {'exit':28}{'n':>5}{'win%':>5}{'avgR':>7}{'sumR':>8}{'PF':>6}{'maxDD':>7}{'avgWin':>7}{'avgLoss':>8}{'stop=%prem':>11}")
    for r in rows:
        print(f"{r['stop_ATR']:>5}A {r['exit']:28}{r['n']:>5}{r['win']:>5}{r['avgR']:>7}{r['sumR']:>8}{r['pf']:>6}{r['maxDD_R']:>7}{r['avgWin']:>7}{r['avgLoss']:>8}{r['median_stop_pct_of_premium']:>10}%")
    best = sorted(rows, key=lambda r: -r["avgR"])[:5]
    print("\nbest 5 by average R:", [(r['stop_ATR'], r['exit'], r['avgR'], r['pf']) for r in best])


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1460)

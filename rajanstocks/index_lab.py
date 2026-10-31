"""Index-option accuracy of EVERY daily indicator (27) on the 5 indices over ~4 years, with the engine's own option model (premium-capped stop, time decay,
real expiry calendar, 0.05 % cost). Each indicator picks its best exit (fixed 2R / trailing x trend filter) on the first 70 % of its trades and is judged on the
last 30 %, and gets a coin-flip control (same entry days, random side).

    python index_lab.py     -> mock_round/index_lab.csv
"""
import csv
import os
import random
import time
from collections import defaultdict

import backtest as bt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mock_round")
SYMS = list(bt.INDEX_SYMS)
CONFIGS = [("fixed", "none"), ("fixed", "trend200"), ("trail", "none"), ("trail", "trend200")]


def pf(rs):
    w, l = sum(x for x in rs if x > 0), -sum(x for x in rs if x < 0)
    return round(w / l, 2) if l else (99.0 if w else 0.0)


def main():
    import bar_source
    import market_api
    market_api.ensure_universe()
    runners = bt._runners(include_hidden=True)
    orig, full = bar_source.daily_bars, {}
    for s in SYMS:
        full[s] = orig(s, 1700)
    atr = {s: bt._atr(full[s]) for s in SYMS}
    ix = {s: {b["date"]: i for i, b in enumerate(full[s])} for s in SYMS}
    ema = {}
    for s in SYMS:
        k, e, o = 2 / 201, None, []
        for b in full[s]:
            e = b["close"] if e is None else b["close"] * k + e * (1 - k)
            o.append(e)
        ema[s] = o
    bt.ASOF_OFFSETS = [0, 380, 760, 1140]
    t0 = time.time()
    signals, istops = bt.collect_signals(runners, SYMS, full, None, orig)
    print(f"{len(runners)} indicators x {len(SYMS)} indices: signals collected in {time.time() - t0:.0f}s", flush=True)

    def trades(key, cfg, flip=None):
        variant, flt = cfg
        out = []
        for s in SYMS:
            m = signals.get((key, s), {})
            order = sorted(m)
            busy = -1
            for n_, d in enumerate(order):
                i = ix[s].get(d)
                if i is None or i <= busy or i + 1 >= len(full[s]):
                    continue
                side = m[d]
                if flt == "trend200" and (i < 200 or (side == "BUY") != (full[s][i]["close"] > ema[s][i])):
                    continue
                ist = istops.get((key, s), {}).get(d)
                if flip is not None:
                    side, ist = flip.choice(["BUY", "SELL"]), None
                opp_i = None
                r = bt.simulate(full[s], atr[s], i, side, variant, opp_i, "index", ist)
                if not r:
                    continue
                busy = r[1]
                out.append((full[s][i + 1]["date"], r[0], r[2], s))
        return out

    rows = []
    for key in sorted(runners):
        base = {c: trades(key, c) for c in CONFIGS}
        alld = sorted(t[0] for t in base[CONFIGS[0]])
        if len(alld) < 15:
            rows.append({"indicator": key, "n": len(alld), "verdict": "too few signals"})
            continue
        cut = alld[int(len(alld) * 0.7)]
        best = None
        for c, tr in base.items():
            is_ = [r for dt, r, w, s in tr if dt < cut]
            if len(is_) >= 12 and (best is None or pf(is_) > best[0]):
                best = (pf(is_), c, tr)
        if not best:
            rows.append({"indicator": key, "n": len(alld), "verdict": "too few signals"})
            continue
        _, cfg, tr = best
        allr = [r for dt, r, w, s in tr]
        oos = [r for dt, r, w, s in tr if dt >= cut]
        rnd = [pf([t[1] for t in trades(key, cfg, random.Random(sd))]) for sd in range(12)]
        row = {"indicator": key, "exit": f"{cfg[0]}/{cfg[1]}", "n": len(allr), "winPct": round(100 * sum(x > 0 for x in allr) / len(allr)), "avgR": round(sum(allr) / len(allr), 3),
               "pf": pf(allr), "isPF": best[0], "oosN": len(oos), "oosPF": pf(oos) if oos else 0, "randomPF": round(sum(rnd) / len(rnd), 2),
               "stopPct": round(100 * sum(1 for t in tr if t[2] == "SL") / len(tr)), "splitDate": cut}
        edge = row["oosN"] >= 12 and row["oosPF"] >= 1.2 and row["pf"] >= row["randomPF"] + 0.15
        row["verdict"] = "EDGE" if edge else ("maybe" if row["pf"] > 1 and row["oosPF"] > 1 else "no edge")
        rows.append(row)
    keys = ["indicator", "exit", "n", "winPct", "avgR", "pf", "isPF", "oosN", "oosPF", "randomPF", "stopPct", "splitDate", "verdict"]
    with open(os.path.join(OUT, "index_lab.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"\n{'indicator':26}{'exit':16}{'n':>5}{'win%':>5}{'stop%':>6}{'avgR':>7}{'PF':>6}{'OOS n':>6}{'OOS PF':>7}{'coin':>6}  verdict")
    for r in sorted(rows, key=lambda r: -(r.get("oosPF") or 0)):
        if "exit" not in r:
            print(f"{r['indicator']:26}{'':16}{r['n']:>5}  {r['verdict']}")
            continue
        print(f"{r['indicator']:26}{r['exit']:16}{r['n']:>5}{r['winPct']:>5}{r['stopPct']:>6}{r['avgR']:>7}{r['pf']:>6}{r['oosN']:>6}{r['oosPF']:>7}{r['randomPF']:>6}  {r['verdict']}")


if __name__ == "__main__":
    main()

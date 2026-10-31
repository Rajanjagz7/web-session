"""Does the mirrored SHORT side of RSI(2) Pullback and IBS Reversion work? Turns RSI2_SHORTS / IBS_SHORTS on, takes only the new SELL signals over ~4 years
(5 indices + 20 stocks), and measures them as cash trades (1 ATR stop, 2R target / trailing) and as index options, against a coin flip on the same days.

    python short_side_test.py
"""
import random
from collections import defaultdict

import backtest as bt
import cash_lab as cl
import exit_lab as xl
import rajan_new_indicators as rni


def pf(rs):
    w, l = sum(x for x in rs if x > 0), -sum(x for x in rs if x < 0)
    return round(w / l, 2) if l else 99.0


def main():
    rni.RSI2_SHORTS = True
    rni.IBS_SHORTS = True
    ents, full, atr, ix, first, last = xl.build(1460)
    print(f"{first} .. {last}: {len(ents)} entries with the short side ON", flush=True)
    for key, name in (("rajan-rsi2-pullback", "RSI(2) Pullback"), ("rajan-ibs-reversion", "IBS Reversion")):
        for side in ("BUY", "SELL"):
            lst = [e for e in ents if e[1] == key and e[3] == side]
            dates = sorted(full[s][ix[s][d] + 1]["date"] for s, k, d, sd, ist in lst if ix[s][d] + 1 < len(full[s]))
            if len(dates) < 10:
                print(f"{name:16}{side:5} only {len(dates)} signals")
                continue
            cut = dates[int(len(dates) * 0.7)]
            for label, kw in (("2R target", dict(target=2.0)), ("trail 1R/1.5R", dict(be=1.0, trail=1.5))):
                busy, res = defaultdict(lambda: -1), []
                for s, k, d, sd, ist in lst:
                    i = ix[s][d]
                    if i <= busy[s]:
                        continue
                    r = cl.walk(full[s], atr[s], i, side, 1.0, **kw)
                    if r:
                        busy[s] = r[1]
                        res.append((full[s][i + 1]["date"], r[0], s))
                allr = [r for _, r, _ in res]
                oos = [r for dt, r, _ in res if dt >= cut]
                rnd = []
                for sd_ in range(15):
                    rr, busy2, rg = [], defaultdict(lambda: -1), random.Random(sd_)
                    for s, k, d, sd, ist in lst:
                        i = ix[s][d]
                        if i <= busy2[s]:
                            continue
                        r = cl.walk(full[s], atr[s], i, rg.choice(["BUY", "SELL"]), 1.0, **kw)
                        if r:
                            busy2[s] = r[1]
                            rr.append(r[0])
                    rnd.append(pf(rr))
                idx = [r for _, r, s in res if s in bt.INDEX_SYMS]
                print(f"{name:16}{side:5}{label:15} n={len(allr):>4} win={round(100 * sum(x > 0 for x in allr) / len(allr)):>3}% avgR={sum(allr) / len(allr):+.3f} PF={pf(allr):>5} | last30%: n={len(oos):>3} PF={pf(oos) if oos else 0:>5} | coin flip PF={sum(rnd) / len(rnd):.2f} | index n={len(idx)} PF={pf(idx) if idx else 0}")


if __name__ == "__main__":
    main()

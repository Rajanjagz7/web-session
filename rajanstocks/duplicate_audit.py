"""Which indicators are duplicates of each other? Compares the signals of every daily indicator over ~4 years on 25 symbols.

For a pair A, B: containment A-in-B = share of A's signals (same symbol, same day, same side) that B also gives; "lift" = how many times more often than
chance (if A and B fired independently on the same days) - a duplicate needs a high containment AND a lift well above 1, otherwise a busy indicator would
"contain" any quiet one just because it fires a lot.

    python duplicate_audit.py    -> mock_round/duplicate_audit.csv
"""
import csv
import os
from collections import defaultdict

import backtest as bt
import exit_lab as xl

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mock_round")
VISIBLE = {"ut-bot", "rajan-ibs-reversion", "rajan-rsi2-pullback", "rajan-trend-rider", "rajan-ha-momentum", "rzt"}


def main():
    import bar_source
    import market_api
    market_api.ensure_universe()
    runners = bt._runners(include_hidden=True)
    syms = bt.INDEX_SYMS + [s for s in bt.STOCK_SYMS if bar_source.supports(s)]
    orig, full = bar_source.daily_bars, {}
    for s in syms:
        try:
            b = orig(s, 1700)
            if len(b) > 260:
                full[s] = b
        except Exception:
            pass
    syms = [s for s in syms if s in full]
    bt.ASOF_OFFSETS = [0, 380, 760, 1140]
    signals, _ = bt.collect_signals(runners, syms, full, None, orig)
    S = defaultdict(set)
    days = set()
    for (key, s), m in signals.items():
        for d, side in m.items():
            S[key].add((s, d, side))
    for s in syms:
        days |= {(s, b["date"]) for b in full[s][-1100:]}
    N = len(days) * 2                                   # a (symbol, day, side) slot
    keys = sorted(k for k in S if len(S[k]) >= 15)
    rows = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            inter = len(S[a] & S[b])
            if not inter:
                continue
            ab, ba = inter / len(S[a]), inter / len(S[b])
            lift = inter / (len(S[a]) * len(S[b]) / N)
            jac = inter / len(S[a] | S[b])
            rows.append({"a": a, "b": b, "nA": len(S[a]), "nB": len(S[b]), "both": inter, "aInB": round(ab, 2), "bInA": round(ba, 2), "jaccard": round(jac, 2), "lift": round(lift, 1),
                         "visibleA": a in VISIBLE, "visibleB": b in VISIBLE})
    rows.sort(key=lambda r: -max(r["aInB"], r["bInA"]))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "duplicate_audit.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(keys)} indicators with 15+ signals; slots={N}")
    print(f"\n{'A':24}{'B':24}{'nA':>5}{'nB':>6}{'both':>6}{'A in B':>8}{'B in A':>8}{'jacc':>6}{'lift':>7}")
    for r in rows:
        if max(r["aInB"], r["bInA"]) >= 0.5 and r["lift"] >= 2:
            print(f"{r['a']:24}{r['b']:24}{r['nA']:>5}{r['nB']:>6}{r['both']:>6}{r['aInB']:>8}{r['bInA']:>8}{r['jaccard']:>6}{r['lift']:>7}")
    print("\nsignal counts:", {k: len(S[k]) for k in keys})


if __name__ == "__main__":
    main()

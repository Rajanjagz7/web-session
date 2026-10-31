"""How late does each daily indicator fire? For every BUY signal: the nearest swing low before it (lowest low of +-5 sessions) and the next swing high after it;
lag = how much of that swing had already been made when the signal bar closed (0 % = fired at the low, 100 % = fired at the top). SELL mirrors.
Only swings of at least 1.5 ATR are counted. ~4 years, 25 symbols.

    python lag_audit.py     -> mock_round/lag_audit.csv
"""
import csv
import os
import statistics as S

import backtest as bt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mock_round")
LIVE = {"ut-bot", "rajan-ibs-reversion", "rajan-rsi2-pullback", "rajan-trend-rider", "rajan-ha-momentum", "rzt"}      # the daily indicators that are working live


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
    atr = {s: bt._atr(full[s]) for s in syms}
    ix = {s: {b["date"]: i for i, b in enumerate(full[s])} for s in syms}
    piv = {}
    for s in syms:
        B, n, lo, hi = full[s], len(full[s]), [], []
        for i in range(5, n - 5):
            if B[i]["low"] <= min(b["low"] for b in B[i - 5:i + 6]):
                lo.append(i)
            if B[i]["high"] >= max(b["high"] for b in B[i - 5:i + 6]):
                hi.append(i)
        piv[s] = (lo, hi)
    rows = []
    for key in sorted(runners):
        lags, bars_after, n_sig = [], [], 0
        for s in syms:
            m = signals.get((key, s), {})
            B, (lo, hi) = full[s], piv[s]
            for d, side in m.items():
                i = ix[s].get(d)
                if i is None or i < 10 or i > len(B) - 12 or not atr[s][i]:
                    continue
                n_sig += 1
                if side == "BUY":
                    a = [p for p in lo if i - 40 <= p <= i]
                    z = [p for p in hi if i < p <= i + 40]
                    if not a or not z:
                        continue
                    base, top = B[a[-1]]["low"], B[z[0]]["high"]
                    move, done = top - base, B[i]["close"] - base
                    since = i - a[-1]
                else:
                    a = [p for p in hi if i - 40 <= p <= i]
                    z = [p for p in lo if i < p <= i + 40]
                    if not a or not z:
                        continue
                    base, top = B[a[-1]]["high"], B[z[0]]["low"]
                    move, done = base - top, base - B[i]["close"]
                    since = i - a[-1]
                if move < 1.5 * atr[s][i]:
                    continue
                lags.append(max(0.0, min(1.2, done / move)))
                bars_after.append(since)
        if len(lags) >= 25:
            late = sum(1 for x in lags if x >= 0.5) / len(lags)
            rows.append({"indicator": key, "live": key in LIVE, "signals": n_sig, "swings": len(lags), "medianLagPct": round(100 * S.median(lags)), "lateSharePct": round(100 * late),
                         "medianBarsAfterLow": S.median(bars_after)})
    rows.sort(key=lambda r: r["medianLagPct"])
    with open(os.path.join(OUT, "lag_audit.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{'indicator':26}{'live':>6}{'swings':>8}{'median lag %':>14}{'fired after 50% of the move':>29}{'bars after the low/high':>25}")
    for r in rows:
        print(f"{r['indicator']:26}{'LIVE' if r['live'] else '':>6}{r['swings']:>8}{r['medianLagPct']:>14}{r['lateSharePct']:>28}%{r['medianBarsAfterLow']:>25}")


if __name__ == "__main__":
    main()

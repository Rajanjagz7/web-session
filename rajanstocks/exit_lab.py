"""Exit lab: which stop width / trailing design keeps the winners and misses fewer big moves? Replays every single-indicator signal of the last N days
(default 180) with the live entry rule and tries different exits on the same entries. Results are in R (1R = the initial stop distance), so they
are what a fixed-risk-per-trade account would see: net of option time decay and 0.05 % cost.

    python exit_lab.py [days]     -> mock_round/exit_lab.csv and a printed table
"""
import csv
import os
import sys
from collections import defaultdict
from datetime import date, timedelta

import backtest as bt
import mock_round as mr

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mock_round")


def trail_walk(bars, atr, i, side, kind, ind_stop, sl_pct, be_at, trail_at, trail_m, partial=False, target=None):
    """Underlying-based exit: stop = signal-candle stop capped at sl_pct of the premium; at +be_at R the stop moves to the entry; from +trail_at R it
    trails the best price by trail_m R; optional: book half at +1.5R (partial), optional fixed target. Same decay / cost as backtest.simulate."""
    if i + 1 >= len(bars) or atr[i] is None or atr[i] <= 0:
        return None
    d = 1 if side == "BUY" else -1
    entry = bars[i + 1]["open"]
    exp = bt.expiry_for(bars[i + 1]["date"], kind)
    dte = lambda j, frac: (exp - date.fromisoformat(bars[j]["date"])).days + frac
    d_entry = dte(i + 1, 0.26)
    old = bt.PREM_SL
    bt.PREM_SL = sl_pct
    try:
        risk = bt.plan_risk(bars, atr[i], i, side, entry, bt.est_premium(atr[i], kind, d_entry), ind_stop=ind_stop)
    finally:
        bt.PREM_SL = old
    if risk <= 0:
        return None
    cost_r = bt.COST * entry / risk
    stop, best, booked, half = entry - d * risk, entry, 0.0, False
    last = min(len(bars) - 1, i + bt.MAX_HOLD)
    th = lambda j, f: bt.theta_r(atr[i], kind, risk, d_entry, dte(j, f))

    def fin(u, j, why, when="mid"):
        frac = {"open": 0.26, "mid": 0.13, "close": 0.0}[when]
        rest = d * (u - entry) / risk
        net_rest = rest - cost_r - th(j, frac)
        if half:
            return (booked + 0.5 * net_rest, j, why, mfe(j))
        return (net_rest, j, why, mfe(j))

    def mfe(j):                                         # the best the underlying did in the whole holding window, in R (what a perfect exit could have caught)
        seg = bars[i + 1:last + 1]
        hi = max(b["high"] for b in seg) if d > 0 else min(b["low"] for b in seg)
        return d * (hi - entry) / risk
    for j in range(i + 1, last + 1):
        b = bars[j]
        if j > i + 1 and ((d > 0 and b["open"] <= stop) or (d < 0 and b["open"] >= stop)):
            return fin(b["open"], j, "TSL" if (best != entry) else "SL", "open")
        if (b["low"] <= stop) if d > 0 else (b["high"] >= stop):
            return fin(stop, j, "TSL" if stop != entry - d * risk else "SL")
        if target is not None and ((b["high"] >= entry + d * target * risk) if d > 0 else (b["low"] <= entry + d * target * risk)):
            return fin(entry + d * target * risk, j, "T")
        best = max(best, b["high"]) if d > 0 else min(best, b["low"])
        bR = d * (best - entry) / risk
        if partial and not half and bR >= 1.5:
            half, booked = True, 0.5 * (1.5 - cost_r - th(j, 0.13))
            stop = max(stop, entry) if d > 0 else min(stop, entry)
        if bR >= be_at:
            stop = max(stop, entry) if d > 0 else min(stop, entry)
        if bR >= trail_at:
            t = best - d * trail_m * risk
            stop = max(stop, t) if d > 0 else min(stop, t)
        if dte(j, 0.0) <= 1:
            return fin(b["close"], j, "EXP", "close")
    if last == len(bars) - 1 and last < i + bt.MAX_HOLD:
        return None
    return fin(bars[last]["close"], last, "TIME", "close")


def stats(Rs, mf):
    n = len(Rs)
    if not n:
        return {}
    w = [x for x in Rs if x > 0]
    l = [-x for x in Rs if x < 0]
    cum = pk = dd = 0.0
    for x in Rs:
        cum += x
        pk = max(pk, cum)
        dd = max(dd, pk - cum)
    cap = [r / m for r, m in zip(Rs, mf) if r > 0 and m > 0.5]
    return {"n": n, "win": round(100 * len(w) / n), "sumR": round(sum(Rs), 1), "avgR": round(sum(Rs) / n, 2), "pf": round(sum(w) / sum(l), 2) if l else 99.0,
            "maxDD_R": round(dd, 1), "avgWin": round(sum(w) / len(w), 2) if w else 0, "avgLoss": round(-sum(l) / len(l), 2) if l else 0,
            "captured": round(100 * sum(cap) / len(cap)) if cap else 0}


def build(days=180):
    import bar_source
    import market_api
    market_api.ensure_universe()
    runners = {k: v for k, v in bt._runners().items() if k in mr.FILTERS}
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
    atr = {s: bt._atr(full[s]) for s in syms}
    ix = {s: {b["date"]: i for i, b in enumerate(full[s])} for s in syms}
    ema = {}
    for s in syms:
        k, e, o = 2 / 201, None, []
        for b in full[s]:
            e = b["close"] if e is None else b["close"] * k + e * (1 - k)
            o.append(e)
        ema[s] = o
    bt.ASOF_OFFSETS = [0, 380, 760, 1140]      # each replay only sees ~400 days of signals: four as-of dates cover ~4 years (a single one covered only ~13 months)
    signals, istops = bt.collect_signals(runners, syms, full, None, orig)
    last_day = max(b["date"] for b in full["NIFTY"])
    first = (date.fromisoformat(last_day) - timedelta(days=days)).isoformat()
    ents = []
    for (key, s), m in signals.items():
        for d, side in m.items():
            i = ix[s].get(d)
            if i is None or i + 1 >= len(full[s]) or full[s][i + 1]["date"] < first:
                continue
            if mr.FILTERS[key] == "trend200" and (i < 200 or (side == "BUY") != (full[s][i]["close"] > ema[s][i])):
                continue
            ents.append((s, key, d, side, istops.get((key, s), {}).get(d)))
    ents.sort(key=lambda e: e[2])
    return ents, full, atr, ix, first, last_day


def main(days=180):
    ents, full, atr, ix, first, last_day = build(days)
    print(f"{first} .. {last_day}: {len(ents)} single-indicator entries on {len(full)} symbols", flush=True)

    EX = [("2R target (OLD live exit)", lambda *a: _w2(*a, ladder=False)), ("T1-T7 ladder (NEW live exit)", lambda *a: _w2(*a, ladder=True))]
    for be, ta, tm in ((1.0, 1.5, 1.0), (1.0, 2.0, 1.5), (1.5, 2.0, 2.0), (1.0, 3.0, 2.0)):
        EX.append((f"breakeven +{be}R, trail from +{ta}R at {tm}R behind", (lambda be, ta, tm: lambda s, bars, a, i, side, k, ist, sp: trail_walk(bars, a, i, side, k, ist, sp, be, ta, tm))(be, ta, tm)))
    EX.append(("PARTIAL: half at +1.5R, rest BE + trail 1.5R", lambda s, bars, a, i, side, k, ist, sp: trail_walk(bars, a, i, side, k, ist, sp, 0.0, 1.5, 1.5, partial=True)))
    EX.append(("PARTIAL half at +1.5R, rest BE + trail 1.0R", lambda s, bars, a, i, side, k, ist, sp: trail_walk(bars, a, i, side, k, ist, sp, 0.0, 1.5, 1.0, partial=True)))

    rows, tbl = [], []
    for sp in (0.125, 0.20, 0.30):
        for name, fn in EX:
            busy = defaultdict(lambda: -1)
            Rs, mf, why = [], [], defaultdict(int)
            for s, key, d, side, ist in ents:
                i = ix[s][d]
                if i <= busy[(s, key)]:
                    continue
                kind = "index" if s in bt.INDEX_SYMS else "stock"
                r = fn(s, full[s], atr[s], i, side, kind, ist, sp)
                if not r:
                    continue
                busy[(s, key)] = r[1]
                Rs.append(r[0])
                mf.append(r[3])
                why[r[2]] += 1
            st = stats(Rs, mf)
            tbl.append({"stop_pct_of_premium": sp, "exit": name, **st, "reasons": dict(why)})
    with open(os.path.join(OUT, "exit_lab.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(tbl[0].keys()))
        w.writeheader()
        w.writerows(tbl)
    for sp in (0.125, 0.20, 0.30):
        print(f"\n=== stop = {sp * 100:.1f}% of the premium ===")
        print(f"{'exit':52}{'n':>5}{'win%':>5}{'sumR':>8}{'avgR':>7}{'PF':>6}{'maxDD':>7}{'avgWin':>8}{'avgLoss':>8}{'captured*':>10}")
        for r in [x for x in tbl if x["stop_pct_of_premium"] == sp]:
            print(f"{r['exit']:52}{r['n']:>5}{r['win']:>5}{r['sumR']:>8}{r['avgR']:>7}{r['pf']:>6}{r['maxDD_R']:>7}{r['avgWin']:>8}{r['avgLoss']:>8}{r['captured']:>9}%")
    print("\n* captured = on winning trades, the share of the best move (in R) that the exit actually kept")


def _w2(s, bars, a, i, side, kind, ist, sp, ladder):
    """The live 2R and ladder exits (mock_round.walk) at stop width sp, plus the best move available in the holding window (for 'captured')."""
    old = bt.PREM_SL
    bt.PREM_SL = sp
    try:
        r = mr.walk(bars, a, i, side, kind, ist, 1, ladder=ladder, target_r=None if ladder else 2.0, lock=None)
        entry = bars[i + 1]["open"]
        exp = bt.expiry_for(bars[i + 1]["date"], kind)
        risk = bt.plan_risk(bars, a[i], i, side, entry, bt.est_premium(a[i], kind, (exp - date.fromisoformat(bars[i + 1]["date"])).days + 0.26), ind_stop=ist)
    finally:
        bt.PREM_SL = old
    if not r or risk <= 0:
        return None
    R, j, why, hit, inr = r
    d = 1 if side == "BUY" else -1
    seg = bars[i + 1:min(len(bars) - 1, i + bt.MAX_HOLD) + 1]
    hi = max(b["high"] for b in seg) if d > 0 else min(b["low"] for b in seg)
    return (R, j, why, d * (hi - entry) / risk)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 180)

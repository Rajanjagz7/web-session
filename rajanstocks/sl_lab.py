"""How to cut the stop-hit rate without cutting the winners. Cash model, 4 years, every active indicator signal.

    python sl_lab.py            -> mock_round/sl_lab.csv + printed tables

For each trade (entry = next open, stop = 1 ATR, T1 = +1.5R, T2 = +2R, max 10 sessions, a tie in one candle = stop) it records whether the stop or T1 came first,
and the net R of a 2R-target exit. It then looks at (1) stop width, (2) one feature at a time (gap, strength of the signal candle, volatility, RSI, trend,
room to the 20-day extreme, volume, agreement between indicators, weekday, index / stock), (3) a confirmation entry (wait for the next candle to break the
signal candle), and (4) rules chosen on the FIRST 70 % of trades and judged on the LAST 30 %, against random subsets of the same size.
"""
import csv
import os
import random
import statistics as S
from collections import defaultdict
from datetime import date

import backtest as bt
import exit_lab as xl

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mock_round")
COST = 0.001


def outcome(bars, atr_v, start, entry, side, k=1.0, hold=10):
    """-> (first, R2): first = 'SL' | 'T1' | 'NONE'; R2 = net R with a 2R target, the stop and a 10-session limit. None while the trade is still open."""
    d = 1 if side == "BUY" else -1
    risk = k * atr_v
    stop, t1, t2 = entry - d * risk, entry + d * 1.5 * risk, entry + d * 2 * risk
    cost_r = COST * entry / risk
    first, last = None, min(len(bars) - 1, start + hold - 1)
    for j in range(start, last + 1):
        b = bars[j]
        gap = j > start and ((d > 0 and b["open"] <= stop) or (d < 0 and b["open"] >= stop))
        if gap or ((b["low"] <= stop) if d > 0 else (b["high"] >= stop)):
            return first or "SL", (d * ((b["open"] if gap else stop) - entry) / risk) - cost_r
        if first is None and ((b["high"] >= t1) if d > 0 else (b["low"] <= t1)):
            first = "T1"
        if (b["high"] >= t2) if d > 0 else (b["low"] <= t2):
            return first or "T1", 2.0 - cost_r
    if last == len(bars) - 1 and last < start + hold - 1:
        return None
    return first or "NONE", d * (bars[last]["close"] - entry) / risk - cost_r


def rsi(closes, n=14):
    out, g, l = [None] * len(closes), 0.0, 0.0
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i - 1]
        u, dn = max(ch, 0), max(-ch, 0)
        if i <= n:
            g += u / n
            l += dn / n
        else:
            g, l = (g * (n - 1) + u) / n, (l * (n - 1) + dn) / n
        if i >= n:
            out[i] = 100.0 if l == 0 else 100 - 100 / (1 + g / l)
    return out


def pf(rs):
    w, l = sum(x for x in rs if x > 0), -sum(x for x in rs if x < 0)
    return round(w / l, 2) if l else 99.0


def row_stats(rows):
    n = len(rows)
    if not n:
        return {"n": 0, "sl": 0, "t1": 0, "pf": 0, "avgR": 0}
    R = [r["R2"] for r in rows]
    return {"n": n, "sl": round(100 * sum(r["first"] == "SL" for r in rows) / n), "t1": round(100 * sum(r["first"] == "T1" for r in rows) / n), "pf": pf(R), "avgR": round(sum(R) / n, 2)}


def main():
    ents, full, atr, ix, first_day, last_day = xl.build(1460)
    ema50 = {}
    rs_ = {}
    for s in full:
        k, e, o = 2 / 51, None, []
        for b in full[s]:
            e = b["close"] if e is None else b["close"] * k + e * (1 - k)
            o.append(e)
        ema50[s] = o
        rs_[s] = rsi([b["close"] for b in full[s]])
    agree = defaultdict(set)
    for s, key, d, side, ist in ents:
        agree[(s, side, d)].add(key)
    rows, busy = [], defaultdict(lambda: -1)
    for s, key, d, side, ist in ents:
        i, bars = ix[s][d], full[s]
        if i <= busy[(s, key)] or i + 1 >= len(bars) or not atr[s][i] or atr[s][i] <= 0:
            continue
        dd = 1 if side == "BUY" else -1
        a = atr[s][i]
        o = outcome(bars, a, i + 1, bars[i + 1]["open"], side)
        if not o:
            continue
        busy[(s, key)] = i + 1
        b0, b1 = bars[i], bars[i + 1]
        rng = (b0["high"] - b0["low"]) or 1e-9
        pos = (b0["close"] - b0["low"]) / rng if dd > 0 else (b0["high"] - b0["close"]) / rng        # 1 = closed at the extreme in the trade's direction
        h20 = max(b["high"] for b in bars[max(0, i - 19):i + 1]) if dd > 0 else min(b["low"] for b in bars[max(0, i - 19):i + 1])
        vols = [b.get("volume") or 0 for b in bars[max(0, i - 20):i]]
        vr = (b0.get("volume") or 0) / (sum(vols) / len(vols)) if vols and sum(vols) > 0 else None
        rows.append({"s": s, "key": key, "side": side, "date": b1["date"], "kind": "index" if s in bt.INDEX_SYMS else "stock", "first": o[0], "R2": o[1],
                     "gap": dd * (b1["open"] - b0["close"]) / a, "pos": pos, "atrp": 100 * a / b0["close"], "rsi": rs_[s][i], "t50": dd * (b0["close"] - ema50[s][i]) / a,
                     "room": dd * (h20 - b0["close"]) / a, "vol": vr, "isidx": 1 if s in bt.INDEX_SYMS else 0, "agree": len(agree[(s, side, d)]), "dow": date.fromisoformat(b1["date"]).weekday(), "i": i})
    rows.sort(key=lambda r: r["date"])
    cut = rows[int(len(rows) * 0.7)]["date"]
    IS, OOS = [r for r in rows if r["date"] < cut], [r for r in rows if r["date"] >= cut]
    b = row_stats(rows)
    print(f"{first_day} .. {last_day}: {len(rows)} trades | baseline (1 ATR stop): stop first {b['sl']}%, T1 first {b['t1']}%, PF(2R) {b['pf']}, avgR {b['avgR']}")
    print(f"split at {cut}: first 70% = {len(IS)} trades, last 30% = {len(OOS)}")

    print("\n(1) STOP WIDTH - the stop hit rate falls as it widens, but so does the reward the winners pay")
    print(f"{'stop':>8}{'n':>6}{'stop first':>11}{'T1 first':>9}{'PF(2R)':>8}{'avgR':>7}")
    for k in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
        rr = []
        for r in rows:
            bars = full[r["s"]]
            o = outcome(bars, atr[r["s"]][r["i"]], r["i"] + 1, bars[r["i"] + 1]["open"], r["side"], k)
            if o:
                rr.append({"first": o[0], "R2": o[1]})
        st = row_stats(rr)
        print(f"{k:>6}A {st['n']:>6}{st['sl']:>10}%{st['t1']:>8}%{st['pf']:>8}{st['avgR']:>7}")

    print("\n(2) ONE FEATURE AT A TIME (all trades; stop first % / T1 first % / PF) - look for a bucket where the stop rate drops and T1 does not")
    FEATS = {"gap": [(-9, -0.3, "gap against"), (-0.3, 0.3, "no gap"), (0.3, 9, "gap with trade")], "pos": [(0, 0.35, "weak close"), (0.35, 0.7, "mid close"), (0.7, 1.01, "strong close")],
             "atrp": [(0, 1.5, "ATR<1.5%"), (1.5, 2.5, "ATR 1.5-2.5%"), (2.5, 99, "ATR>2.5%")], "rsi": [(0, 40, "RSI<40"), (40, 60, "RSI 40-60"), (60, 101, "RSI>60")],
             "t50": [(-99, 0, "against EMA50"), (0, 1.5, "above EMA50 <1.5ATR"), (1.5, 99, "far with EMA50")], "room": [(-99, 1, "room<1ATR"), (1, 3, "room 1-3ATR"), (3, 99, "room>3ATR")],
             "agree": [(1, 2, "1 indicator"), (2, 9, "2+ indicators")], "dow": [(0, 1, "Mon"), (1, 2, "Tue"), (2, 3, "Wed"), (3, 4, "Thu"), (4, 5, "Fri")],
             "isidx": [(1, 2, "index trade")], "vol": [(0, 0.8, "volume<0.8x"), (0.8, 1.3, "volume 0.8-1.3x"), (1.3, 99, "volume>1.3x")]}
    good = []
    for f, buckets in FEATS.items():
        for lo, hi, name in buckets:
            sub = [r for r in rows if r[f] is not None and lo <= r[f] < hi]
            st = row_stats(sub)
            if st["n"] >= 40:
                print(f"  {name:24}{st['n']:>5}  stop {st['sl']:>3}%  T1 {st['t1']:>3}%  PF {st['pf']:>5}  avgR {st['avgR']:>6}")
                good.append((f, lo, hi, name, st))
    for kd in ("index", "stock"):
        st = row_stats([r for r in rows if r["kind"] == kd])
        print(f"  {kd:24}{st['n']:>5}  stop {st['sl']:>3}%  T1 {st['t1']:>3}%  PF {st['pf']:>5}  avgR {st['avgR']:>6}")

    print("\n(3) CONFIRMATION ENTRY - skip the blind open; enter only when the next 2 candles break the signal candle (entry at the break, stop 1 ATR from it)")
    cr = []
    for r in rows:
        bars, i = full[r["s"]], r["i"]
        dd = 1 if r["side"] == "BUY" else -1
        trig = bars[i]["high"] if dd > 0 else bars[i]["low"]
        for j in (i + 1, i + 2):
            if j >= len(bars):
                break
            bj = bars[j]
            if (bj["high"] >= trig) if dd > 0 else (bj["low"] <= trig):
                ent = max(bj["open"], trig) if dd > 0 else min(bj["open"], trig)
                o = outcome(bars, atr[r["s"]][i], j, ent, r["side"])
                if o:
                    cr.append({"first": o[0], "R2": o[1], "date": r["date"]})
                break
    st = row_stats(cr)
    print(f"  taken {st['n']} of {len(rows)} signals ({round(100 * st['n'] / len(rows))}%): stop first {st['sl']}%, T1 first {st['t1']}%, PF(2R) {st['pf']}, avgR {st['avgR']}")

    print("\n(4) RULES CHOSEN ON THE FIRST 70 %, JUDGED ON THE LAST 30 % (a rule = a bucket that cut the stop rate by 5+ points on the first 70 %, with 40+ trades)")
    bi = row_stats(IS)
    cand = []
    for f, lo, hi, name, _ in good:
        sub = [r for r in IS if r[f] is not None and lo <= r[f] < hi]
        st = row_stats(sub)
        if st["n"] >= 40 and st["sl"] <= bi["sl"] - 5 and st["t1"] >= bi["t1"] - 3:
            cand.append((st["sl"], f, lo, hi, name, st))
    cand.sort()
    random.seed(3)
    boo = row_stats(OOS)
    print(f"  last 30 % baseline: n={boo['n']} stop {boo['sl']}%  T1 {boo['t1']}%  PF {boo['pf']}")
    out_rows = []
    for sl, f, lo, hi, name, st in cand[:8]:
        sub = [r for r in OOS if r[f] is not None and lo <= r[f] < hi]
        so = row_stats(sub)
        rnd = [row_stats(random.sample(OOS, so["n"]))["sl"] for _ in range(300)] if so["n"] else [0]
        z = (boo["sl"] - so["sl"]) / (S.pstdev(rnd) or 1) if so["n"] else 0
        print(f"  {name:24} first70: n={st['n']} stop {st['sl']}% T1 {st['t1']}% | last30: n={so['n']} stop {so['sl']}% T1 {so['t1']}% PF {so['pf']} | beats random by {z:.1f} sd")
        out_rows.append({"rule": name, "isN": st["n"], "isStop": st["sl"], "isT1": st["t1"], "oosN": so["n"], "oosStop": so["sl"], "oosT1": so["t1"], "oosPF": so["pf"], "sd_vs_random": round(z, 1)})
    if len(cand) >= 2:
        rules = [(f, lo, hi) for _, f, lo, hi, _, _ in cand[:3]]
        sub = [r for r in OOS if all(r[f] is not None and lo <= r[f] < hi for f, lo, hi in rules)]
        so = row_stats(sub)
        print(f"  COMBINED top-3 rules ({', '.join(c[4] for c in cand[:3])}): last30 n={so['n']} stop {so['sl']}% T1 {so['t1']}% PF {so['pf']}")
    print()
    print("(5) EXCLUDE THE BAD BUCKETS - chosen on the first 70 % (stop rate 6+ points worse than average and a lower T1 rate), judged on the last 30 %")
    bad = []
    for f, lo, hi, name, _ in good:
        sub = [r for r in IS if r[f] is not None and lo <= r[f] < hi]
        st = row_stats(sub)
        if st["n"] >= 40 and st["sl"] >= bi["sl"] + 6 and st["t1"] <= bi["t1"] - 3:
            bad.append((f, lo, hi, name, st))
    def kept(r, rules):
        return not any(r[f] is not None and lo <= r[f] < hi for f, lo, hi, _, _ in rules)
    print(f"  buckets to exclude: {[b[3] for b in bad]}")
    for label, rules in [(b[3], [b]) for b in bad] + [("ALL of them", bad)]:
        a, o = [r for r in IS if kept(r, rules)], [r for r in OOS if kept(r, rules)]
        sa, so = row_stats(a), row_stats(o)
        rnd = [row_stats(random.sample(OOS, so["n"]))["pf"] for _ in range(300)] if so["n"] else [0]
        z = (so["pf"] - S.mean(rnd)) / (S.pstdev(rnd) or 1)
        print(f"  without {label:22} first70: n={sa['n']} stop {sa['sl']}% T1 {sa['t1']}% PF {sa['pf']} | last30: n={so['n']} ({round(100 * so['n'] / boo['n'])}% kept) stop {so['sl']}% T1 {so['t1']}% PF {so['pf']} avgR {so['avgR']} | PF vs random subset {z:+.1f} sd")
    if out_rows:
        with open(os.path.join(OUT, "sl_lab.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
            w.writeheader()
            w.writerows(out_rows)


if __name__ == "__main__":
    main()

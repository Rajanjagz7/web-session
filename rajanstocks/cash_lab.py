"""Cash / futures version of every active indicator over 4 years (no option decay), judged out-of-sample and against a coin-flip control.

    python cash_lab.py [days]
        -> mock_round/cash_lab.csv                (per indicator: best stop / exit on the first 70 %, result on the last 30 %, random control)
        -> public/static/backtest_4y.json         (every trade with SL / T1..T7 hits + what happened after the stop; shown in Journal > Picks log > Backtest)

Entry = next session's open after the indicator's signal (its own trend200 filter applied). Stop = k x ATR(14) of the signal bar. Targets T1..T7 = 1.5R, 2R, 3R,
4R, 5R, 6R, 10R (the auto trader's ladder). Cost 0.1 % round trip. A candle that touches the stop and a target counts as the stop. Max 10 sessions.
"""
import csv
import json
import os
import random
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import backtest as bt
import exit_lab as xl

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mock_round")
JSON_OUT = os.path.join(HERE, "public", "static", "backtest_4y.json")
IST = timezone(timedelta(hours=5, minutes=30))
LADDER = (1.5, 2, 3, 4, 5, 6, 10)
COST = 0.001
KS = (0.75, 1.0, 1.5, 2.0)
MODES = {"T2": (2.0, None, None), "T3": (3.0, None, None), "TRAIL": (None, 1.0, 1.5)}     # (fixed target R, breakeven / trail starts at +R, trail distance R)
NAMES = {"rajan-ha-momentum": "HA Momentum", "rajan-rsi2-pullback": "RSI2 Pullback", "rzt": "Z Trend", "ut-bot": "UT Bot", "rajan-ibs-reversion": "IBS Reversion",
         "rajan-trend-rider": "Trend Rider"}


def walk(bars, atr, i, side, k, target=None, be=None, trail=None, hold=10):
    """Net R of one cash trade; None while it is still open at the end of the data."""
    if i + 1 >= len(bars) or atr[i] is None or atr[i] <= 0:
        return None
    d = 1 if side == "BUY" else -1
    entry = bars[i + 1]["open"]
    risk = k * atr[i]
    cost_r = COST * entry / risk
    stop, best = entry - d * risk, entry
    last = min(len(bars) - 1, i + hold)
    for j in range(i + 1, last + 1):
        b = bars[j]
        if j > i + 1 and ((d > 0 and b["open"] <= stop) or (d < 0 and b["open"] >= stop)):
            return d * (b["open"] - entry) / risk - cost_r, j
        if (b["low"] <= stop) if d > 0 else (b["high"] >= stop):
            return d * (stop - entry) / risk - cost_r, j
        if target:
            t = entry + d * target * risk
            if (b["high"] >= t) if d > 0 else (b["low"] <= t):
                return target - cost_r, j
        best = max(best, b["high"]) if d > 0 else min(best, b["low"])
        if be is not None and d * (best - entry) / risk >= be:
            t = max(entry, best - d * trail * risk) if d > 0 else min(entry, best - d * trail * risk)
            if trail is None:
                t = entry
            stop = max(stop, t) if d > 0 else min(stop, t)
    if last == len(bars) - 1 and last < i + hold:
        return None
    return d * (bars[last]["close"] - entry) / risk - cost_r, last


def track(bars, atr, i, side, k=1.0, hold=10):
    """SL / T1..T7 hit dates (a same-candle tie counts as the stop) and what happened in the 5 sessions after a stop."""
    d = 1 if side == "BUY" else -1
    entry = bars[i + 1]["open"]
    risk = k * atr[i]
    stop = entry - d * risk
    tg = [entry + d * r * risk for r in LADDER]
    hit, best, end = {}, entry, None
    last = min(len(bars) - 1, i + hold)
    for j in range(i + 1, last + 1):
        b = bars[j]
        gap = j > i + 1 and ((d > 0 and b["open"] <= stop) or (d < 0 and b["open"] >= stop))
        if gap or ((b["low"] <= stop) if d > 0 else (b["high"] >= stop)):
            hit["sl"] = b["date"]
            end = j
            break
        for n, t in enumerate(tg, 1):
            if f"t{n}" not in hit and ((b["high"] >= t) if d > 0 else (b["low"] <= t)):
                hit[f"t{n}"] = b["date"]
        best = max(best, b["high"]) if d > 0 else min(best, b["low"])
        if "t7" in hit:
            end = j
            break
    out = {"entry": entry, "risk": risk, "stop": stop, "t": tg, "hit": hit, "best": best, "end": bars[end]["date"] if end is not None else bars[last]["date"]}
    if "sl" in hit and end is not None:
        seg = bars[end + 1:end + 6]
        if seg:
            hi, lo = max(b["high"] for b in seg), min(b["low"] for b in seg)
            out["post"] = hi if d > 0 else lo               # best price in the trade's favour after the stop
            out["pa"] = lo if d > 0 else hi                 # worst price against it
            out["cl"] = seg[-1]["close"]
            out["afterDays"] = len(seg)
    return out


def pf(rs):
    w = sum(x for x in rs if x > 0)
    l = -sum(x for x in rs if x < 0)
    return round(w / l, 2) if l else (99.0 if w else 0.0)


def main(days=1460):
    ents, full, atr, ix, first, last_day = xl.build(days)
    print(f"{first} .. {last_day}: {len(ents)} entries", flush=True)
    by_key = defaultdict(list)
    for e in ents:
        by_key[e[1]].append(e)
    rows, trades = [], []

    def run(lst, k, mode, flip=None):
        tr, target, be, trail = k, *MODES[mode]
        busy, out = defaultdict(lambda: -1), []
        for s, key, d, side, ist in lst:
            i = ix[s][d]
            if i <= busy[s]:
                continue
            sd = side if flip is None else flip.choice(["BUY", "SELL"])
            r = walk(full[s], atr[s], i, sd, tr, target, be, trail)
            if not r:
                continue
            busy[s] = r[1]
            out.append((full[s][i + 1]["date"], r[0], s))
        return out

    for key, lst in sorted(by_key.items()):
        dates = sorted(set(full[s][ix[s][d] + 1]["date"] for s, _, d, _, _ in lst if ix[s][d] + 1 < len(full[s])))
        cut = dates[int(len(dates) * 0.7)]
        best = None
        for k in KS:
            for mode in MODES:
                res = run(lst, k, mode)
                is_ = [r for dt, r, s in res if dt < cut]
                if len(is_) < 30:
                    continue
                if best is None or pf(is_) > best[0]:
                    best = (pf(is_), k, mode, res)
        if not best:
            continue
        _, k, mode, res = best
        oos = [r for dt, r, s in res if dt >= cut]
        allr = [r for dt, r, s in res]
        rnd = [pf([r for dt, r, s in run(lst, k, mode, random.Random(sd))]) for sd in range(20)]
        idx = [r for dt, r, s in res if s in bt.INDEX_SYMS]
        stk = [r for dt, r, s in res if s not in bt.INDEX_SYMS]
        row = {"indicator": NAMES.get(key, key), "key": key, "stop_ATR": k, "exit": mode, "n": len(allr), "winPct": round(100 * sum(x > 0 for x in allr) / len(allr)),
               "avgR": round(sum(allr) / len(allr), 3), "pf": pf(allr), "isPF": best[0], "oosN": len(oos), "oosPF": pf(oos) if oos else 0,
               "randomPF": round(sum(rnd) / len(rnd), 2), "indexN": len(idx), "indexPF": pf(idx) if idx else 0, "stockN": len(stk), "stockPF": pf(stk) if stk else 0,
               "splitDate": cut}
        edge = row["oosN"] >= 20 and row["oosPF"] >= 1.2 and row["pf"] >= row["randomPF"] + 0.15
        row["verdict"] = "EDGE" if edge else ("maybe" if row["pf"] > 1.0 and row["oosPF"] > 1.0 else "no edge")
        rows.append(row)

    with open(os.path.join(OUT, "cash_lab.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\n{'indicator':16}{'stop':>6}{'exit':>7}{'n':>5}{'win%':>5}{'avgR':>7}{'PF':>6}{'inPF':>6}{'OOS n':>6}{'OOS PF':>7}{'random':>7}{'idxPF':>6}{'stkPF':>6}  verdict")
    for r in sorted(rows, key=lambda r: -r["oosPF"]):
        print(f"{r['indicator']:16}{r['stop_ATR']:>5}A{r['exit']:>7}{r['n']:>5}{r['winPct']:>5}{r['avgR']:>7}{r['pf']:>6}{r['isPF']:>6}{r['oosN']:>6}{r['oosPF']:>7}{r['randomPF']:>7}{r['indexPF']:>6}{r['stockPF']:>6}  {r['verdict']}")

    # ---- every trade with its SL / T1..T7 hits, for the Picks log backtest view (fixed 1.0 ATR stop, ladder targets) ----
    busy = defaultdict(lambda: -1)
    for s, key, d, side, ist in ents:
        i = ix[s][d]
        if i <= busy[(s, key)] or i + 1 >= len(full[s]):
            continue
        if atr[s][i] is None or atr[s][i] <= 0:
            continue
        t = track(full[s], atr[s], i, side)
        busy[(s, key)] = ix[s].get(t["end"], i)
        r2 = walk(full[s], atr[s], i, side, 1.0, 2.0)
        rt = walk(full[s], atr[s], i, side, 1.0, None, 1.0, 1.5)
        dp = 2 if t["entry"] < 1000 else 1
        trades.append({"s": s, "key": key, "side": side, "sig": d, "ent": full[s][i + 1]["date"], "kind": "index" if s in bt.INDEX_SYMS else "stock", "e": round(t["entry"], dp),
                       "sl": round(t["stop"], dp), "t": [round(x, dp) for x in t["t"]], "h": t["hit"], "b": round(t["best"], dp), "end": t["end"], "dp": dp,
                       **({"po": round(t["post"], dp), "pa": round(t["pa"], dp), "cl": round(t["cl"], dp), "ad": t["afterDays"]} if "post" in t else {}),
                       "r2": round(r2[0], 2) if r2 else None, "rt": round(rt[0], 2) if rt else None})
    trades.sort(key=lambda x: (x["ent"], x["s"]))
    json.dump({"generatedAt": datetime.now(IST).isoformat(), "from": first, "to": last_day, "model": "cash / futures, no option decay", "stop": "1.0 x ATR(14)",
               "ladder": list(LADDER), "cost": COST, "names": NAMES, "summary": rows, "trades": trades}, open(JSON_OUT, "w", encoding="utf-8"), separators=(",", ":"))
    print(f"\n{len(trades)} trades -> {JSON_OUT} ({os.path.getsize(JSON_OUT) // 1024} KB)")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1460)

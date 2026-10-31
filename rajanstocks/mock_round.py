"""Mock round: OLD FILT vs NEW IND over the last month, replayed on daily candles.

    python mock_round.py [days]      # default 31 -> mock_round/trades.csv, mock_round/summary.csv, mock_round/mock_round.json

What is compared (the same engine and rules the auto trader uses, backtest.py):
  entries  OLD  = the 6 active daily indicators, an entry needs 2+ of them pointing the same way (auto_trader: minAgreeStock / indexMinAgree = 2),
                  one trade per symbol per signal day, majority only (cancelling votes = no trade)
           NEW  = every indicator signal on its own (a single source), the way the NEW IND sources enter (Z Trend, Picks, Eagle, Gann, time cycle ...)
  exits    OLD  = ONE target at 2R, stop = signal-candle stop (auto_trader old_rules), max 10 sessions
           NEW  = target ladder 1.5R, 2R, 3R, 4R, 5R, 6R, 10R: T1 moves the stop to cost, every further target moves it one target behind, 10R closes
  Both use the live 12.5 % premium cap on the stop (backtest.PREM_SL), 1 lot per trade, theta + 0.05 % cost.
Not replayable from daily candles (so not in this file): Today's Picks, Eagle (Open = Low / High), intraday Z Trend, time cycle, Gann, the stock screen
and the index call / put screen. Those only show up in the live Journal numbers.
"""
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import backtest as bt

IST = timezone(timedelta(hours=5, minutes=30))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mock_round")
LADDER = (1.5, 2, 3, 4, 5, 6, 10)
FILTERS = {"rajan-ha-momentum": "none", "rajan-rsi2-pullback": "trend200", "rzt": "trend200", "ut-bot": "none",
           "rajan-ibs-reversion": "trend200", "rajan-trend-rider": "none"}      # as set in the live auto trader (activeStrategies)
INDEX_LOT = {"NIFTY": 65, "BANKNIFTY": 30, "FINNIFTY": 60, "MIDCPNIFTY": 120, "SENSEX": 20}


def lots_map():
    try:
        from nse_service import nse_service
        return nse_service.upstox.fo_universe().get("lots") or {}
    except Exception:
        return {}


LOCKS = {"old": (1500.0, 2000.0, 0.5, ((6000.0, 0.7), (4000.0, 0.6))),          # auto_trader.LOCKS: breakeven Rs, trail from Rs, base keep, steps
         "new": (2500.0, 3500.0, 0.4, ((10000.0, 0.65), (6000.0, 0.5)))}
EXITS = {                                                                          # name -> (ladder, single target R, lock mode)
    "2R": (False, 2.0, None),
    "2R+LOCK1500": (False, 2.0, "old"),         # what OLD FILT trades live (lockMode "old")
    "2R+LOCK2500": (False, 2.0, "new"),
    "LADDER": (True, None, None),               # what the NEW IND ladder trades live (no rupee lock)
    "LADDER+LOCK1500": (True, None, "old"),
}


def walk(bars, atr, i, side, kind, ind_stop, lot, ladder=False, target_r=None, lock=None):
    """One trade on daily candles with the live entry / stop / theta / cost of backtest.simulate, and an exit built from: a single target, the T1-T7 ladder
    (stop moves to cost at T1, then one target behind) and / or the rupee profit lock (auto_trader._profit_lock, 1 lot, premium moves 0.5 x underlying).
    Within a candle the stop in force at its start is checked first (same as the backtest); the lock and ladder then update for the next candle.
    Returns (R, exit_index, reason, targets_hit, rupees)."""
    if i + 1 >= len(bars) or atr[i] is None or atr[i] <= 0:
        return None
    d = 1 if side == "BUY" else -1
    entry = bars[i + 1]["open"]
    exp = bt.expiry_for(bars[i + 1]["date"], kind)
    dte = lambda j, frac: (exp - date.fromisoformat(bars[j]["date"])).days + frac
    d_entry = dte(i + 1, 0.26)
    risk = bt.plan_risk(bars, atr[i], i, side, entry, bt.est_premium(atr[i], kind, d_entry), ind_stop=ind_stop)
    if risk <= 0:
        return None
    per_pt = lot * 0.5                                                  # rupees per underlying point (1 lot, delta 0.5)
    stop, hit, best_pnl, locked = entry - d * risk, 0, 0.0, None
    tgts = [entry + d * r * risk for r in LADDER] if ladder else None
    target = entry + d * target_r * risk if target_r else None
    last = min(len(bars) - 1, i + bt.MAX_HOLD)
    cost_inr = bt.COST * entry * per_pt                                  # = cost_r * risk * per_pt
    theta_inr = lambda j, frac: bt.theta_r(atr[i], kind, risk, d_entry, dte(j, frac)) * risk * per_pt

    def fin(u_exit, j, why, when="mid"):
        frac = {"open": 0.26, "mid": 0.13, "close": 0.0}[when]
        inr = d * (u_exit - entry) * per_pt - theta_inr(j, frac) - cost_inr
        return (inr / (risk * per_pt), j, why, hit, inr)
    for j in range(i + 1, last + 1):
        b = bars[j]
        tag = "TSL" if (hit or locked) else "SL"
        if j > i + 1 and ((d > 0 and b["open"] <= stop) or (d < 0 and b["open"] >= stop)):
            return fin(b["open"], j, tag, "open")
        if (b["low"] <= stop) if d > 0 else (b["high"] >= stop):
            return fin(stop, j, tag)
        if target is not None and ((b["high"] >= target) if d > 0 else (b["low"] <= target)):
            return fin(target, j, "T")
        if tgts:
            while hit < len(tgts) and ((b["high"] >= tgts[hit]) if d > 0 else (b["low"] <= tgts[hit])):
                hit += 1
                if hit == len(tgts):
                    return fin(tgts[-1], j, "T10")
                stop = max(stop, entry if hit == 1 else tgts[hit - 2]) if d > 0 else min(stop, entry if hit == 1 else tgts[hit - 2])
        if dte(j, 0.0) <= 1:
            return fin(b["close"], j, "EXP", "close")
        if lock:                                                        # best open profit this candle (its high / low), net of the decay so far
            be, trail, base, steps = LOCKS[lock]
            fav = b["high"] if d > 0 else b["low"]
            best_pnl = max(best_pnl, d * (fav - entry) * per_pt - theta_inr(j, 0.13))
            if best_pnl >= be:
                frac = next((f for lvl, f in steps if best_pnl >= lvl), base)
                keep = frac * best_pnl if best_pnl >= trail else 0.0
                lock_pnl = 80.0 + keep                                  # charges + the share of the best profit that is kept
                u_stop = entry + d * (lock_pnl + theta_inr(j, 0.13) + cost_inr) / per_pt
                if (u_stop > stop) if d > 0 else (u_stop < stop):
                    stop, locked = u_stop, ("trail" if keep else "breakeven")
    if last == len(bars) - 1 and last < i + bt.MAX_HOLD:
        return None
    return fin(bars[last]["close"], last, "TIME", "close")


def after_stop(bars, j, side, entry, risk, look=5):
    """What the underlying did in the sessions after the stop day (daily candles; the stop day itself is not counted, its order is unknown):
    best / worst price in R from the entry (stop = -1R, T1 = +1.5R). Verdict: RECOVERED reached +1.5R, BOUNCED got back to the entry,
    FELL ended up 1R or more beyond the stop, FLAT otherwise."""
    d = 1 if side == "BUY" else -1
    seg = bars[j + 1:j + 1 + look]
    if not seg:
        return {"after_days": 0, "after_best_R": "", "after_worst_R": "", "after_verdict": "NO DATA"}
    hi = max(b["high"] for b in seg)
    lo = min(b["low"] for b in seg)
    best = d * ((hi if d > 0 else lo) - entry) / risk
    worst = d * ((lo if d > 0 else hi) - entry) / risk
    close = d * (seg[-1]["close"] - entry) / risk
    v = "RECOVERED" if best >= 1.5 else "BOUNCED" if best >= 0 else "FELL" if worst <= -2.0 else "FLAT"
    return {"after_days": len(seg), "after_best_R": round(best, 2), "after_worst_R": round(worst, 2), "after_close_R": round(close, 2), "after_verdict": v}


def stats(rows, key="inr"):
    n = len(rows)
    if not n:
        return {"n": 0}
    v = [r[key] for r in rows]
    R = [r["R"] for r in rows]
    w = sum(x for x in v if x > 0)
    l = -sum(x for x in v if x < 0)
    cum = pk = dd = 0.0
    for x in v:
        cum += x
        pk = max(pk, cum)
        dd = max(dd, pk - cum)
    return {"n": n, "wins": sum(x > 0 for x in v), "winPct": round(100 * sum(x > 0 for x in v) / n), "netInr": round(sum(v)), "avgR": round(sum(R) / n, 2),
            "sumR": round(sum(R), 1), "pf": round(w / l, 2) if l else (99.0 if w else 0), "maxDDInr": round(dd), "stopped": sum(1 for r in rows if r["why"] in ("SL",)),
            "target": sum(1 for r in rows if r["why"] in ("T", "T10", "TSL"))}


def run(days=31):
    import bar_source
    import market_api
    market_api.ensure_universe()
    runners = {k: v for k, v in bt._runners().items() if k in FILTERS}
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
    bt.ASOF_OFFSETS = [0]
    signals, istops = bt.collect_signals(runners, syms, full, None, orig)
    last_day = max(b["date"] for b in full["NIFTY"])
    first = (date.fromisoformat(last_day) - timedelta(days=days)).isoformat()
    lots = lots_map()
    lot_of = lambda s: lots.get(s) or INDEX_LOT.get(s) or 1

    # votes[(sym, signal date)] = {key: side}; each indicator's own filter (trend200) applied to its own vote
    votes = defaultdict(dict)
    for (key, s), m in signals.items():
        for d, side in m.items():
            i = ix[s].get(d)
            if i is None:
                continue
            if FILTERS[key] == "trend200" and (i < 200 or (side == "BUY") != (full[s][i]["close"] > ema[s][i])):
                continue
            votes[(s, d)][key] = side

    entries = {"OLD": [], "NEW": []}
    for (s, d), v in sorted(votes.items(), key=lambda x: x[0][1]):
        i = ix[s][d]
        if i + 1 >= len(full[s]) or full[s][i + 1]["date"] < first:
            continue
        buys = [k for k, x in v.items() if x == "BUY"]
        sells = [k for k, x in v.items() if x == "SELL"]
        for k, x in v.items():                                                       # NEW: every signal on its own
            entries["NEW"].append((s, d, x, [k]))
        if len(buys) != len(sells):                                                  # OLD: majority, 2+ agreeing
            side, lst = ("BUY", buys) if len(buys) > len(sells) else ("SELL", sells)
            if len(lst) >= 2:
                entries["OLD"].append((s, d, side, lst))

    rows = []
    for ent_name, lst in entries.items():
        for exit_name, (lad, tr, lk) in EXITS.items():
            busy = defaultdict(lambda: -1)                                           # one open trade per symbol (and per indicator for NEW entries)
            for s, d, side, keys in lst:
                i = ix[s][d]
                kind = "index" if s in bt.INDEX_SYMS else "stock"
                bk = (s, keys[0]) if ent_name == "NEW" else (s,)
                if i <= busy[bk]:
                    continue
                ist = next((istops.get((k, s), {}).get(d) for k in keys if istops.get((k, s), {}).get(d)), None)
                res = walk(full[s], atr[s], i, side, kind, ist, lot_of(s), lad, tr, lk)
                if not res:
                    continue
                R, j, why, th, inr = res
                busy[bk] = j
                entry = full[s][i + 1]["open"]
                exp = bt.expiry_for(full[s][i + 1]["date"], kind)
                prem = bt.est_premium(atr[s][i], kind, (exp - date.fromisoformat(full[s][i + 1]["date"])).days + 0.26)
                risk = bt.plan_risk(full[s], atr[s][i], i, side, entry, prem, ind_stop=ist)
                aft = after_stop(full[s], j, side, entry, risk) if why == "SL" else {}
                rows.append({**aft, "entries": ent_name, "exits": exit_name, "sym": s, "kind": kind, "side": side, "signal": d, "entry_date": full[s][i + 1]["date"],
                             "exit_date": full[s][j]["date"], "indicators": "+".join(keys), "agree": len(keys), "underlying_entry": round(entry, 2),
                             "risk_pts": round(risk, 2), "prem_est": round(prem, 2), "lot": lot_of(s), "targets_hit": th, "why": why, "R": round(R, 3), "inr": round(inr)})
    os.makedirs(OUT, exist_ok=True)
    rows.sort(key=lambda r: (r["entries"], r["exits"], r["entry_date"], r["sym"]))
    with open(os.path.join(OUT, "trades.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    summ = []
    for en in ("OLD", "NEW"):
        for ex in EXITS:
            for kind in ("all", "index", "stock"):
                sub = [r for r in rows if r["entries"] == en and r["exits"] == ex and (kind == "all" or r["kind"] == kind)]
                summ.append({"entries": en, "exits": ex, "market": kind, **stats(sub)})
    with open(os.path.join(OUT, "summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["entries", "exits", "market", "n", "wins", "winPct", "netInr", "avgR", "sumR", "pf", "maxDDInr", "stopped", "target"])
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in w.fieldnames} for r in summ)
    per = []
    for k in FILTERS:
        for ex in EXITS:
            sub = [r for r in rows if r["entries"] == "NEW" and r["exits"] == ex and r["indicators"] == k]
            per.append({"indicator": k, "exits": ex, **stats(sub)})
    json.dump({"generatedAt": datetime.now(IST).isoformat(), "from": first, "to": last_day, "symbols": syms, "summary": summ, "perIndicator": per,
               "note": "daily candles; Picks / Eagle / intraday Z Trend / time cycle / Gann / stock screen / index call-put not replayable"},
              open(os.path.join(OUT, "mock_round.json"), "w"), indent=1)
    return summ, per, first, last_day


if __name__ == "__main__":
    summ, per, a, b = run(int(sys.argv[1]) if len(sys.argv) > 1 else 31)
    print(f"{a} .. {b}")
    for r in summ:
        print(r)

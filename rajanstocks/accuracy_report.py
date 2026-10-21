"""Accuracy of every indicator - and of the Picks screen - with a stop-loss and a target on every trade (paper research, not advice).

    python accuracy_report.py            # writes static/accuracy_report.json and docs/INDICATOR_ACCURACY.md

Method (the same engine the Auto Trader's own backtest uses, see backtest.py):
  * Every daily-bar indicator is replayed "as of" many past dates on 5 indices + 20 liquid stocks (~4 years), so each signal
    only uses data that existed on that day. Entry = the next session's open. One open trade per indicator and symbol.
  * Two ways of trading each signal, both with a stop-loss AND a target:
      options : the app's own rule - the indicator's stop (else the signal candle, 0.5-1.0 ATR) capped at 30% of the ATM option
                premium, real expiry calendar, time decay, 0.05% cost, out 1 day before expiry.
      cash    : plain shares / futures - the indicator's stop (else signal candle +0.1 ATR, kept between 0.75 and 2 ATR),
                no time decay, 0.1% round-trip cost.
  * Targets 1R, 1.5R, 2R, 3R; maximum 10 sessions; a candle that touches both stop and target counts as the stop.
  * The first 70% of trades (by date) choose the best target; the last 30% judge it (out-of-sample).
  * "Accuracy" = share of trades that ended in profit. Also shown: share that hit the target, share stopped out, average R,
    profit factor, and how often price was simply further in the signal's direction after 5 sessions.
  * Picks: the Picks screen's own scoring (trend vs 20/50-day EMA, today's range, volume, RSI) and its own stop (1.5-3 ATR beyond
    the 5-session swing) and targets (1.5R / 2.5R) are replayed on every F&O stock + index, at the close or at the next open.
"""
import json
import math
import os
import time
from datetime import date, datetime, timedelta, timezone

import backtest as bt

IST = timezone(timedelta(hours=5, minutes=30))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(HERE, "static", "accuracy_report.json")
OUT_MD = os.path.join(HERE, "docs", "INDICATOR_ACCURACY.md")
TARGETS = (1.0, 1.5, 2.0, 3.0)
HOLD = 10
CASH_COST = 0.001
MIN_IS, MIN_OOS = 40, 20
RISK_RS = bt.RISK_RS

# daily-bar indicators that the engine cannot replay without peeking, and why
NOT_REPLAYABLE = {
    "quantum-matrix": "built on 1-minute bars; minute history for past years is not available",
    "ha-dancing-trend": "built on 1-minute bars; minute history for past years is not available",
    "heikin-ashi-channel": "built on 1-minute bars; minute history for past years is not available",
    "orb-15m": "needs the first 15 minutes of each past session (minute bars)",
    "vwap-rsi": "needs intraday VWAP (minute bars)",
    "candle-oh-ol": "Open = Low / High is only known during the session, so a daily bar would let the test peek at the future",
    "volume-buzzer-15m": "needs 15-minute bars for past years",
    "volume-buzzer-daily": "an alert (no entry / direction), not a trade signal",
    "potential-breakout": "an alert (no entry / direction), not a trade signal",
    "vix-range": "an expected-range band, not a buy / sell signal",
}


# ───────────────────────── statistics ─────────────────────────
def wilson(w, n, z=1.96):
    if not n:
        return [0.0, 0.0]
    p = w / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(max(0, c - h), 3), round(min(1, c + h), 3)]


def stats(T):
    """T: list of trades {R, why, hold}. Net of costs, so R can be a loss even when the price moved the right way."""
    n = len(T)
    if not n:
        return {"n": 0, "winRate": 0, "ci95": [0, 0], "targetHit": 0, "stopped": 0, "timeExit": 0, "avgR": 0, "pf": 0, "sumR": 0, "maxDD_R": 0, "avgHold": 0, "perTradeRs": 0}
    Rs = [t["R"] for t in T]
    wins = sum(1 for r in Rs if r > 0)
    gp, gl = sum(r for r in Rs if r > 0), -sum(r for r in Rs if r < 0)
    cum = pk = dd = 0.0
    for r in Rs:
        cum += r
        pk = max(pk, cum)
        dd = max(dd, pk - cum)
    return {"n": n, "winRate": round(wins / n, 3), "ci95": wilson(wins, n),
            "targetHit": round(sum(1 for t in T if t["why"] == "T") / n, 3),
            "stopped": round(sum(1 for t in T if t["why"] == "SL") / n, 3),
            "timeExit": round(sum(1 for t in T if t["why"] not in ("T", "SL")) / n, 3),
            "avgR": round(sum(Rs) / n, 3), "pf": round(gp / gl, 2) if gl > 0 else (99.0 if gp else 0), "sumR": round(sum(Rs), 1),
            "maxDD_R": round(dd, 1), "avgHold": round(sum(t.get("hold", 0) for t in T) / n, 1), "perTradeRs": round(sum(Rs) / n * RISK_RS)}


# ───────────────────────── cash / futures simulation ─────────────────────────
def sim_levels(bars, i0, side, entry, stop, targets, hold=HOLD, cost=CASH_COST, exit_mode="all", t_idx=0):
    """Walk forward from bar i0 (first session after entry). targets: price levels (ascending R). Returns (R, exit_bar, why, sessions).
    exit_mode 'all'  : exit everything at targets[t_idx];
              'split': half at targets[0], then the stop moves to entry, the other half runs to targets[-1]."""
    d = 1 if side == "BUY" else -1
    risk = d * (entry - stop)
    if risk <= 0 or entry <= 0:
        return None
    cost_r = cost * entry / risk
    last = min(len(bars) - 1, i0 + hold - 1)
    if last == len(bars) - 1 and last < i0 + hold - 1:
        return None                                              # not enough future bars to judge
    half_done, locked = False, 0.0
    cur_stop = stop
    for j in range(i0, last + 1):
        b = bars[j]
        hit_stop = b["low"] <= cur_stop if d > 0 else b["high"] >= cur_stop
        if hit_stop:
            gap = (d > 0 and b["open"] <= cur_stop) or (d < 0 and b["open"] >= cur_stop)
            px = b["open"] if gap else cur_stop                    # a gap through the stop fills at the open (worse than the stop)
            r = d * (px - entry) / risk
            tot = locked + (0.5 * r if half_done else r)
            return (tot - cost_r, j, "SL" if not half_done or r < 0 else "T", j - i0 + 1)
        if exit_mode == "all":
            tg = targets[t_idx]
            if (b["high"] >= tg) if d > 0 else (b["low"] <= tg):
                return (d * (tg - entry) / risk - cost_r, j, "T", j - i0 + 1)
        else:
            if not half_done and ((b["high"] >= targets[0]) if d > 0 else (b["low"] <= targets[0])):
                half_done, locked, cur_stop = True, 0.5 * d * (targets[0] - entry) / risk, entry
            if half_done and ((b["high"] >= targets[-1]) if d > 0 else (b["low"] <= targets[-1])):
                return (locked + 0.5 * d * (targets[-1] - entry) / risk - cost_r, j, "T", j - i0 + 1)
    r = d * (bars[last]["close"] - entry) / risk
    tot = locked + (0.5 * r if half_done else r)
    return (tot - cost_r, last, "TIME", last - i0 + 1)


def cash_plan(bars, atr_v, i, side, entry, ind_stop=None):
    d = 1 if side == "BUY" else -1
    own = d * (entry - ind_stop) if ind_stop else None
    if own is not None and 0.2 * atr_v < own <= 3 * atr_v:
        return own
    lo = min(b["low"] for b in bars[max(0, i - 1):i + 1])
    hi = max(b["high"] for b in bars[max(0, i - 1):i + 1])
    swing = d * (entry - (lo if d > 0 else hi)) + 0.1 * atr_v
    return min(max(swing, 0.75 * atr_v), 2.0 * atr_v)


# ───────────────────────── indicators ─────────────────────────
def _extra_runners():
    """Daily-bar indicators that are not in backtest._runners()."""
    import strategies_api

    def volume_spurt(sym, lb):
        raw = strategies_api._raw_volume_spurt(sym)
        return {"bars": [{"date": r["date"], "signal": "BUY" if r.get("signal") == "SPURT" else None} for r in raw["bars"]]}
    return {"volume-spurt": volume_spurt}


def run_indicators(full, syms, progress=None):
    import strategies_api
    runners = bt._runners(include_hidden=True)
    runners.update(_extra_runners())
    meta = strategies_api.META
    atr = {s: bt._atr(full[s]) for s in syms}
    idx_of = {s: {b["date"]: i for i, b in enumerate(full[s])} for s in syms}
    ema200 = {}
    for s in syms:
        k, e, out = 2 / 201, None, []
        for b in full[s]:
            e = b["close"] if e is None else b["close"] * k + e * (1 - k)
            out.append(e)
        ema200[s] = out
    signals, istops = bt.collect_signals(runners, syms, full, progress)
    kind = lambda s: "index" if s in bt.INDEX_SYMS else "stock"

    # directional accuracy and the trade lists (bucketed once: key, model, filter, target)
    from collections import defaultdict
    trades, direction = [], {}
    buckets = defaultdict(list)
    for (key, s), m in signals.items():
        bars, ix = full[s], idx_of[s]
        order = sorted(m)
        for flt in ("none", "trend200"):
            for model in ("options", "cash"):
                for tr in TARGETS:
                    busy = -1
                    for d in order:
                        i = ix.get(d)
                        if i is None or i <= busy:
                            continue
                        side = m[d]
                        if flt == "trend200" and (i < 200 or (side == "BUY") != (bars[i]["close"] > ema200[s][i])):
                            continue
                        ist = istops.get((key, s), {}).get(d)
                        if model == "options":
                            res = bt.simulate(bars, atr[s], i, side, "fixed", None, kind(s), ist, target_r=tr)
                        else:
                            if i + 1 >= len(bars) or not atr[s][i]:
                                continue
                            entry = bars[i + 1]["open"]
                            risk = cash_plan(bars, atr[s][i], i, side, entry, ist)
                            dd_ = 1 if side == "BUY" else -1
                            res4 = sim_levels(bars, i + 1, side, entry, entry - dd_ * risk, [entry + dd_ * tr * risk], exit_mode="all")
                            res = (res4[0], res4[1], res4[2]) if res4 else None
                        if not res:
                            continue
                        R, j, why = res
                        busy = j
                        t_ = {"key": key, "sym": s, "kind": kind(s), "side": side, "model": model, "filter": flt, "tr": tr,
                              "entry": bars[i + 1]["date"], "R": round(R, 3), "why": why,
                              "hold": max(0, (date.fromisoformat(bars[j]["date"]) - date.fromisoformat(bars[i + 1]["date"])).days)}
                        trades.append(t_)
                        buckets[(key, model, flt, tr)].append(t_)
        # price direction after the signal (independent of any stop / target)
        for d in order:
            i = ix.get(d)
            if i is None or i + 6 >= len(bars):
                continue
            side = m[d]
            e = bars[i + 1]["open"]
            for k in (1, 5, 10):
                if i + k < len(bars):
                    ok = (bars[i + k]["close"] > e) == (side == "BUY")
                    c = direction.setdefault(key, {}).setdefault(k, [0, 0])
                    c[0] += 1 if ok else 0
                    c[1] += 1
    if not trades:
        raise RuntimeError("no simulated trades - history unavailable")
    allbase = [t for k_, v_ in buckets.items() if k_[1:] == ("cash", "none", 2.0) for t in v_]
    dates = sorted(t["entry"] for t in allbase)
    split = dates[int(len(dates) * 0.7)]
    out = []
    for key in sorted({k for k, _s in signals}):
        mt = meta.get(key) or {}
        entry = {"key": key, "name": mt.get("name", key), "group": mt.get("group", ""), "visible": key not in strategies_api.HIDDEN,
                 "signals": sum(len(m) for (k, _s), m in signals.items() if k == key), "models": {}}
        for model in ("options", "cash"):
            rules = []
            for flt in ("none", "trend200"):
                for tr in TARGETS:
                    T = buckets.get((key, model, flt, tr), [])
                    rules.append({"label": f"SL + {tr:g}R target" + (" · with 200-EMA trend" if flt == "trend200" else ""), "targetR": tr, "filter": flt,
                                  "all": stats(T), "inSample": stats([t for t in T if t["entry"] <= split]),
                                  "outOfSample": stats([t for t in T if t["entry"] > split]),
                                  "index": stats([t for t in T if t["kind"] == "index"]), "stock": stats([t for t in T if t["kind"] == "stock"]),
                                  "buy": stats([t for t in T if t["side"] == "BUY"]), "sell": stats([t for t in T if t["side"] == "SELL"])})
            elig = [r for r in rules if r["inSample"]["n"] >= MIN_IS]
            best = max(elig, key=lambda r: r["inSample"]["avgR"]) if elig else max(rules, key=lambda r: r["inSample"]["n"])
            o = best["outOfSample"]
            verdict = ("not enough trades" if best["inSample"]["n"] < MIN_IS or o["n"] < MIN_OOS else
                       "edge held out-of-sample" if o["avgR"] >= 0.05 and o["pf"] >= 1.1 and best["inSample"]["avgR"] > 0 else
                       "no edge out-of-sample")
            entry["models"][model] = {"rules": rules, "best": best["label"], "verdict": verdict, "bestAll": best["all"], "bestOOS": o}
        dr = direction.get(key, {})
        entry["directional"] = {f"{k}d": {"n": v[1], "accuracy": round(v[0] / v[1], 3) if v[1] else 0, "ci95": wilson(v[0], v[1])} for k, v in dr.items()}
        out.append(entry)
    out.sort(key=lambda e: (-(e["models"]["cash"]["bestAll"]["avgR"] if e["models"]["cash"]["bestAll"]["n"] >= MIN_IS else -9)))
    return out, split


# ───────────────────────── Picks screen ─────────────────────────
def run_picks(full_all, progress=None):
    import market_api
    kind = lambda s: "index" if s in bt.INDEX_SYMS else "stock"
    trades = []
    n_sym = len(full_all)
    for n, (s, bars) in enumerate(full_all.items()):
        if progress and n % 20 == 0:
            progress(f"picks {n}/{n_sym}")
        busy = {"close": -1, "open": -1}
        for i in range(60, len(bars) - HOLD - 1):
            b = bars[i]
            d0 = date.fromisoformat(b["date"]) - timedelta(days=90)
            j0 = i
            while j0 > 0 and bars[j0 - 1]["date"] >= d0.isoformat():
                j0 -= 1
            rows = bars[j0:i + 1]
            q = {"last_price": b["close"], "ohlc": {"open": b["open"], "high": b["high"], "low": b["low"]},
                 "prev_close_price": bars[i - 1]["close"], "volume": b.get("volume") or 0}
            try:
                p = market_api._pick(s, q, rows)
            except Exception:
                continue
            if not p or p["signal"] not in ("BUY", "SELL"):
                continue
            side = p["signal"]
            sgn = 1 if side == "BUY" else -1
            risk = abs(p["entry"] - p["stop"])
            if risk <= 0:
                continue
            for entry_mode in ("close", "open"):
                if i <= busy[entry_mode]:
                    continue
                if entry_mode == "close":
                    entry = p["entry"]
                    first = i + 1
                else:
                    entry = bars[i + 1]["open"]
                    first = i + 1
                stop = entry - sgn * risk
                t1, t2 = entry + sgn * 1.5 * risk, entry + sgn * 2.5 * risk
                for mode, args in (("T1", dict(exit_mode="all", t_idx=0)), ("T2", dict(exit_mode="all", t_idx=1)), ("T1+T2", dict(exit_mode="split"))):
                    res = sim_levels(bars, first, side, entry, stop, [t1, t2], hold=HOLD, **args)
                    if not res:
                        continue
                    R, j, why, sess = res
                    if mode == "T1":
                        busy[entry_mode] = max(busy[entry_mode], j)
                    trades.append({"sym": s, "kind": kind(s), "side": side, "entryMode": entry_mode, "exit": mode, "date": b["date"],
                                   "R": round(R, 3), "why": why, "hold": sess, "strength": p["strength"], "volx": p["volx"], "score": p["score"]})
    if not trades:
        raise RuntimeError("no picks trades")
    dates = sorted(t["date"] for t in trades if t["exit"] == "T1" and t["entryMode"] == "close")
    split = dates[int(len(dates) * 0.7)]
    blocks = []
    for em in ("close", "open"):
        for ex in ("T1", "T2", "T1+T2"):
            T = [t for t in trades if t["entryMode"] == em and t["exit"] == ex]
            blocks.append({"entryAt": "screening price (the day's close)" if em == "close" else "next session's open",
                           "exit": {"T1": "all at target 1 (1.5R)", "T2": "all at target 2 (2.5R)", "T1+T2": "half at 1.5R, stop to entry, rest at 2.5R"}[ex],
                           "all": stats(T), "inSample": stats([t for t in T if t["date"] <= split]), "outOfSample": stats([t for t in T if t["date"] > split]),
                           "buy": stats([t for t in T if t["side"] == "BUY"]), "sell": stats([t for t in T if t["side"] == "SELL"]),
                           "index": stats([t for t in T if t["kind"] == "index"]), "stock": stats([t for t in T if t["kind"] == "stock"]),
                           "strength75plus": stats([t for t in T if t["strength"] >= 75]), "strengthBelow75": stats([t for t in T if t["strength"] < 75]),
                           "volumeSurge": stats([t for t in T if t["volx"] >= 1.5]),
                           "byYear": {y: stats([t for t in T if t["date"].startswith(y)]) for y in sorted({t["date"][:4] for t in T})}})
    return {"symbols": n_sym, "from": dates[0], "to": dates[-1], "splitDate": split, "trades": len([t for t in trades if t["exit"] == "T1" and t["entryMode"] == "close"]),
            "rules": {"signal": "the Picks screen's own score (>= +2 BUY, <= -2 SELL) on the day's close, rows = last 90 calendar days (as the live screen)",
                      "stop": "the pick's own stop (1.5-3 ATR, beyond the 5-session swing)", "targets": "1.5R and 2.5R of that risk", "maxHold": f"{HOLD} sessions",
                      "cost": f"{CASH_COST * 100:.1f}% round trip", "tieBreak": "stop wins a same-candle tie"},
            "variants": blocks}


# ───────────────────────── report ─────────────────────────
def run(progress=None, include_picks=True):
    import bar_source
    import market_api
    from upstox_service import background
    t0 = time.time()
    market_api.ensure_universe()
    syms = bt.INDEX_SYMS + [s for s in bt.STOCK_SYMS if bar_source.supports(s)]
    full = {}
    with background():
        for s in syms:
            try:
                b = bar_source.daily_bars(s, 1700)
                if len(b) > 260:
                    full[s] = b
            except Exception:
                pass
    syms = [s for s in syms if s in full]
    ind, split = run_indicators(full, syms, progress)
    picks = None
    if include_picks:
        universe = list(bt.INDEX_SYMS) + [s for s, _n, _sec in market_api.STOCKS]
        full_all = dict(full)
        with background():
            for s in universe:
                if s in full_all:
                    continue
                try:
                    b = bar_source.daily_bars(s, 1700)
                    if len(b) > 200:
                        full_all[s] = b
                except Exception:
                    pass
        picks = run_picks(full_all, progress)
    import strategies_api
    nr = [{"key": k, "name": (strategies_api.META.get(k) or {}).get("name", k), "why": w} for k, w in NOT_REPLAYABLE.items() if k in strategies_api.META]
    report = {"generatedAt": datetime.now(IST).isoformat(), "symbols": syms, "splitDate": split,
              "history": {"from": min(full[s][0]["date"] for s in syms), "to": max(full[s][-1]["date"] for s in syms)},
              "method": __doc__, "indicators": ind, "picks": picks, "notReplayable": nr,
              "caveats": ["Backtests describe the past; they do not predict the future. Paper research, not advice.",
                          "Options results are modelled on the underlying's daily candles (expired option candles are unavailable): spreads, gaps and slippage are not included beyond the stated cost.",
                          "Choosing the best of 8 rules per indicator in-sample then judging out-of-sample reduces, but does not remove, selection luck.",
                          "Win rate alone is not the whole story: with a 1R target a 55% win rate can still lose money after costs; read it together with avg R and profit factor."],
              "tookSeconds": round(time.time() - t0, 1)}
    return report


def write(report):
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, separators=(",", ":"))
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(to_markdown(report))


def _pct(x):
    return f"{x * 100:.0f}%"


def to_markdown(r):
    L = ["# Indicator & Picks accuracy (with stop-loss and target)",
         f"_Generated {r['generatedAt'][:16].replace('T', ' ')} IST · history {r['history']['from']} → {r['history']['to']} · {len(r['symbols'])} symbols · "
         f"out-of-sample from {r['splitDate']}_", "",
         "**Read this first.** Every trade has a stop-loss and a target. *Win rate* = share of trades that ended in profit (after costs). *Target hit* / *Stopped* = how they ended. "
         "*Avg R* = average result in multiples of the money risked (+0.30R = 30% of the risk won per trade); *PF* = profit factor (> 1.2 is healthy). "
         "The 95% range shows how uncertain the win rate is for that many trades. Past results do not predict the future.", ""]
    for model, title in (("cash", "A. Shares / futures (stop = indicator or signal candle, no option decay)"), ("options", "B. Options, as the Auto Trader trades (stop capped at 30% of the premium, time decay)")):
        L += [f"## {title}", "",
              "| Indicator | Best exit rule (chosen in-sample) | Trades | Win rate (95% range) | Target hit | Stopped | Avg R | PF | Out-of-sample: trades · win · avg R · PF | Verdict |",
              "|---|---|---:|---|---:|---:|---:|---:|---|---|"]
        for e in r["indicators"]:
            m = e["models"][model]
            b = next((x for x in m["rules"] if x["label"] == m["best"]), m["rules"][0])
            a, o = b["all"], b["outOfSample"]
            if not a["n"]:
                continue
            L.append(f"| {e['name']}{'' if e['visible'] else ' *(hidden)*'} | {m['best']} | {a['n']} | {_pct(a['winRate'])} ({_pct(a['ci95'][0])}-{_pct(a['ci95'][1])}) | {_pct(a['targetHit'])} | {_pct(a['stopped'])} | "
                     f"{a['avgR']:+.2f} | {a['pf']} | {o['n']} · {_pct(o['winRate'])} · {o['avgR']:+.2f} · {o['pf']} | {m['verdict']} |")
        L.append("")
    L += ["## C. Direction only (no stop, no target): was price further in the signal's direction?", "",
          "| Indicator | Signals | After 1 session | After 5 sessions | After 10 sessions |", "|---|---:|---:|---:|---:|"]
    for e in r["indicators"]:
        d = e["directional"]
        if "5d" in d:
            L.append(f"| {e['name']} | {d['5d']['n']} | {_pct(d.get('1d', {}).get('accuracy', 0))} | {_pct(d['5d']['accuracy'])} ({_pct(d['5d']['ci95'][0])}-{_pct(d['5d']['ci95'][1])}) | {_pct(d.get('10d', {}).get('accuracy', 0))} |")
    L.append("")
    p = r.get("picks")
    if p:
        L += ["## D. The Picks screen (BUY / SELL ideas with their own stop and targets)", "",
              f"_{p['symbols']} instruments, {p['from']} → {p['to']}, {p['trades']} BUY/SELL ideas. {p['rules']['signal']}. Stop: {p['rules']['stop']}. Targets: {p['rules']['targets']}. Max hold {p['rules']['maxHold']}, cost {p['rules']['cost']}._", "",
              "| Entry | Exit | Trades | Win rate (95% range) | Target hit | Stopped | Avg R | PF | Out-of-sample: trades · win · avg R | BUY win · avg R | SELL win · avg R |",
              "|---|---|---:|---|---:|---:|---:|---:|---|---|---|"]
        for v in p["variants"]:
            a, o = v["all"], v["outOfSample"]
            L.append(f"| {v['entryAt']} | {v['exit']} | {a['n']} | {_pct(a['winRate'])} ({_pct(a['ci95'][0])}-{_pct(a['ci95'][1])}) | {_pct(a['targetHit'])} | {_pct(a['stopped'])} | {a['avgR']:+.2f} | {a['pf']} | "
                     f"{o['n']} · {_pct(o['winRate'])} · {o['avgR']:+.2f} | {_pct(v['buy']['winRate'])} · {v['buy']['avgR']:+.2f} | {_pct(v['sell']['winRate'])} · {v['sell']['avgR']:+.2f} |")
        best = max(p["variants"], key=lambda v: v["all"]["avgR"])
        L += ["", f"Strength split for the best variant ({best['entryAt']}, {best['exit']}): strength ≥ 75 → {best['strength75plus']['n']} trades, win {_pct(best['strength75plus']['winRate'])}, avg R {best['strength75plus']['avgR']:+.2f}; "
              f"below 75 → {best['strengthBelow75']['n']} trades, win {_pct(best['strengthBelow75']['winRate'])}, avg R {best['strengthBelow75']['avgR']:+.2f}; "
              f"volume surge (≥ 1.5x) → {best['volumeSurge']['n']} trades, win {_pct(best['volumeSurge']['winRate'])}, avg R {best['volumeSurge']['avgR']:+.2f}.",
              "", "By year (same variant): " + " · ".join(f"{y}: {_pct(s['winRate'])} / {s['avgR']:+.2f}R ({s['n']})" for y, s in best["byYear"].items()), ""]
    L += ["## Indicators that cannot be replayed honestly", ""] + [f"- **{x['name']}** - {x['why']}" for x in r["notReplayable"]] + ["", "## Caveats", ""] + [f"- {c}" for c in r["caveats"]] + [""]
    return "\n".join(L)


if __name__ == "__main__":
    rep = run(progress=lambda m: print(m, flush=True) if str(m).split()[-1].endswith(("00", "50")) else None)
    write(rep)
    print(f"written {OUT_JSON} and {OUT_MD} in {rep['tookSeconds']} s")

"""Last-month replay: every kept strategy's signals of the past N days, followed to their stop / targets, for index options and stock options.

    python month_replay.py [days]        # default 31 -> writes public/static/month_replay.json (shown in Journal > Picks log > Last month)

Same engine and rules as backtest.py (signal-candle stop capped at PREM_SL of the option premium, entry = next session's open, one open trade per
strategy and symbol, 10 sessions max, out 1 day before expiry), so the numbers match what the auto trader would have done. Daily candles only: a hit
carries its DATE, not its time (the option premium history of expired contracts is not available).

Per trade it records the underlying's entry / stop / 1R / 2R / 3R, which of them were reached and in what order, and the net option result in R
(after time decay and cost) for a grid of stop widths, targets and a trailing stop - so the log shows what hit and where a change would have helped.
"""
import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone

import backtest as bt

IST = timezone(timedelta(hours=5, minutes=30))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "public", "static", "month_replay.json")
NAMES = {}
SL_GRID = (0.10, 0.125, 0.20, 0.30)          # stop as a share of the option premium (live = 0.125)
TGT_GRID = (1.0, 1.5, 2.0, 3.0)              # target in R (live trader = 2R)


def _names():
    try:
        import strategies_api
        for k, v in getattr(strategies_api, "NAMES", {}).items():
            NAMES[k] = v
    except Exception:
        pass
    try:
        import rajan_pavan_indicators as rp
        for k in rp.RAJAN_PAVAN_KEYS:
            NAMES.setdefault(k, k.replace("-", " ").title())
    except Exception:
        pass


def _levels(bars, atr, i, side, kind, ind_stop, sl_pct):
    """(entry, risk) on the underlying for a signal on bar i, with the stop capped at sl_pct of the option premium."""
    entry = bars[i + 1]["open"]
    exp = bt.expiry_for(bars[i + 1]["date"], kind)
    d_entry = (exp - date.fromisoformat(bars[i + 1]["date"])).days + 0.26
    old = bt.PREM_SL
    bt.PREM_SL = sl_pct
    try:
        risk = bt.plan_risk(bars, atr[i], i, side, entry, bt.est_premium(atr[i], kind, d_entry), ind_stop=ind_stop)
    finally:
        bt.PREM_SL = old
    return entry, risk, exp


def _walk(bars, i, side, entry, risk, exp):
    """Follow the underlying after entry: the order in which the stop and 1R / 2R / 3R were reached (a same-candle tie counts as the stop)."""
    d = 1 if side == "BUY" else -1
    stop = entry - d * risk
    tg = [entry + d * k * risk for k in (1, 2, 3)]
    hit, best, j_end, state = {}, entry, None, "open"
    last = min(len(bars) - 1, i + bt.MAX_HOLD)
    for j in range(i + 1, last + 1):
        b = bars[j]
        gap_stop = j > i + 1 and ((d > 0 and b["open"] <= stop) or (d < 0 and b["open"] >= stop))
        if gap_stop or (b["low"] <= stop if d > 0 else b["high"] >= stop):
            hit["sl"] = b["date"]
            state, j_end = "stopped", j
            break
        for n, t in enumerate(tg, 1):
            if f"t{n}" not in hit and (b["high"] >= t if d > 0 else b["low"] <= t):
                hit[f"t{n}"] = b["date"]
        best = max(best, b["high"]) if d > 0 else min(best, b["low"])
        if (exp - date.fromisoformat(b["date"])).days <= 1:
            state, j_end = "expiry", j
            break
    if state == "open":
        if last < len(bars) - 1 or last >= i + bt.MAX_HOLD:
            state, j_end = "time", last
        else:
            j_end = len(bars) - 1
    if hit.get("t3") or hit.get("t2") or hit.get("t1"):
        state = "target" if state in ("open", "time", "expiry") or "sl" not in hit else state
    return {"stop": stop, "t": tg, "hit": hit, "best": best, "state": state, "end": bars[j_end]["date"]}


def run(days=31, progress=print):
    import bar_source
    import market_api
    market_api.ensure_universe()
    _names()
    runners = bt._runners()
    syms = bt.INDEX_SYMS + [s for s in bt.STOCK_SYMS if bar_source.supports(s)]
    orig = bar_source.daily_bars
    full = {}
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
    bt.ASOF_OFFSETS = [0]                     # only today's replay: the last month sits inside its 400-day window
    t0 = time.time()
    signals, istops = bt.collect_signals(runners, syms, full, lambda p: progress(p.get("msg", "")) if p.get("done", 0) % 100 == 0 else None, orig)
    progress(f"signals collected in {time.time() - t0:.0f}s")
    last_day = max(b["date"] for b in full["NIFTY"])
    first_day = (date.fromisoformat(last_day) - timedelta(days=days)).isoformat()

    trades = []
    for (key, s_), m in signals.items():
        kind = "index" if s_ in bt.INDEX_SYMS else "stock"
        bars, busy = full[s_], -1
        for d in sorted(m):
            i = ix[s_].get(d)
            if i is None or i + 1 >= len(bars) or bars[i + 1]["date"] < first_day:
                continue
            if i <= busy:
                continue
            side, ist = m[d], istops.get((key, s_), {}).get(d)
            if atr[s_][i] is None or atr[s_][i] <= 0:
                continue
            entry, risk, exp = _levels(bars, atr[s_], i, side, kind, ist, bt.PREM_SL)
            if risk <= 0 or not entry:
                continue
            w = _walk(bars, i, side, entry, risk, exp)
            busy = ix[s_].get(w["end"], i)
            # net option result (theta + cost included) for each stop width x target, plus trailing
            grid = {}
            for sp in SL_GRID:
                for tr in TGT_GRID:
                    bt.PREM_SL = sp
                    try:
                        r = bt.simulate(bars, atr[s_], i, side, "fixed", None, kind, ist, target_r=tr)
                        rt = bt.simulate(bars, atr[s_], i, side, "trail", None, kind, ist)
                    finally:
                        bt.PREM_SL = 0.125
                    if r:
                        grid[f"{sp}|{tr}"] = [round(r[0], 3), r[2]]
                    if rt and f"{sp}|trail" not in grid:
                        grid[f"{sp}|trail"] = [round(rt[0], 3), rt[2]]
            live = grid.get(f"{bt.PREM_SL}|{bt.TARGET_R}")
            trades.append({
                "key": key, "name": NAMES.get(key, key), "sym": s_, "kind": kind, "side": side, "signal": d, "entry_date": bars[i + 1]["date"],
                "entry": round(entry, 2), "stop": round(w["stop"], 2), "t": [round(x, 2) for x in w["t"]], "risk": round(risk, 2),
                "hit": w["hit"], "state": w["state"], "end": w["end"], "best": round(w["best"], 2), "live": live, "grid": grid,
            })
    trades.sort(key=lambda t: (t["entry_date"], t["sym"], t["key"]))
    out = {"generatedAt": datetime.now(IST).isoformat(), "from": first_day, "to": last_day, "days": days, "symbols": syms,
           "strategies": len(runners), "slGrid": SL_GRID, "tgtGrid": TGT_GRID, "liveRule": {"sl": bt.PREM_SL, "target": bt.TARGET_R},
           "note": "Daily candles: a hit carries its date, not its time. Net R includes option time decay and 0.05% cost.", "trades": trades}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    progress(f"{len(trades)} trades {first_day}..{last_day} -> {OUT} ({os.path.getsize(OUT) // 1024} KB, {time.time() - t0:.0f}s)")
    return out


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 31)

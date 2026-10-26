"""Eagle Trades backtest: strength >= 75 (+ good risk/reward) AND Open = Low (BUY) / Open = High (SELL), every qualifying stock, no daily cap.

    python eagle_backtest.py [N_STOCKS=213] [MONTHS=13]      # writes docs/EAGLE_TRADES_BACKTEST.md

Same morning replay as morning_backtest.py (5-minute candles: the Picks screen as it reads at the decision time, entry 5 minutes later),
but on every F&O stock and WITHOUT the shortlist's 15-a-day / 4-per-sector caps, so every Eagle setup is counted.
"""
import json
import os
import sys
import time
from collections import defaultdict

import bar_source
import market_api
import morning_backtest as mb
import morning_picks as mp
from upstox_service import background

TIMES = [("09:20", 9 * 60 + 20), ("09:30", 9 * 60 + 30), ("09:45", 9 * 60 + 45), ("10:15", 10 * 60 + 15)]


def collect(daily, m5, sector, decide, gate=True):
    """Eagle trades for one decision time over every stock/day."""
    mb.DECIDE_MIN = decide
    trades = []
    for s, bars in daily.items():
        if s not in m5:
            continue
        idx = {b["date"]: i for i, b in enumerate(bars)}
        for d, p, ctx in mb.build_morning(s, bars, idx, m5[s], sector.get(s, "")):
            c = mp.classify(p) if gate else None
            if gate:
                if not (c and c["tier"] == 1 and c["both"]):
                    continue
                side = c["side"]
            else:                                           # strength >= 75 and Open = Low / High agreeing, ignoring the risk/reward gate
                ol, oh = mp.open_flags(p)
                sig = p.get("signal")
                if (p.get("strength") or 0) < mp.STRENGTH_MIN or not ((ol and sig == "BUY") or (oh and sig == "SELL")):
                    continue
                side = sig
            tr = mb.trade_morning(dict(p, s=s), ctx, bars, side, None)
            if tr and tr.get("swing"):
                trades.append({"date": d, "sym": s, "side": side, **tr})
    return trades


def row(trades, split):
    out = {}
    for ek in ("swing", "intraday", "intraday1"):
        a = mb.block(trades, ek)
        a["ci95"] = mb.wilson(round(a["winRate"] * a["n"]), a["n"])
        out[ek] = {"all": a, "oos": mb.block([t for t in trades if t["date"] > split], ek),
                   "buy": mb.block([t for t in trades if t["side"] == "BUY"], ek), "sell": mb.block([t for t in trades if t["side"] == "SELL"], ek)}
    return out


def main(n=213, months=13):
    t0 = time.time()
    market_api.ensure_universe()
    sector = {s: sec for s, _n, sec in market_api.STOCKS}
    daily = {}
    with background():
        for s, _n, _sec in market_api.STOCKS:
            try:
                b = bar_source.daily_bars(s, 1700)
                if len(b) > 300:
                    daily[s] = b
            except Exception:
                pass
    liq = sorted(daily, key=lambda s: -sum(b["close"] * (b.get("volume") or 0) for b in daily[s][-60:]))[:n]
    daily = {s: daily[s] for s in liq}
    m5 = {}
    for i, s in enumerate(liq):
        try:
            m5[s] = mb.load_5m(s, months)
        except Exception as e:
            print(f"  {s}: {str(e)[:80]}", flush=True)
        if i % 20 == 0:
            print(f"5-minute history {i}/{len(liq)} ({time.time() - t0:.0f}s)", flush=True)
    res = {}
    for name, dm in TIMES:
        for gate in (True, False):
            tr = collect(daily, m5, sector, dm, gate)
            dates = sorted({t["date"] for t in tr})
            split = dates[int(len(dates) * 0.7)] if dates else ""
            key = f"{name}{'' if gate else ' (no risk/reward gate)'}"
            res[key] = {"split": split, "days": len(dates), "sessions": len({d for s in m5 for d in m5[s]}), **row(tr, split)}
            if name == "09:30" and gate:
                bymonth = defaultdict(list)
                for t in tr:
                    bymonth[t["date"][:7]].append(t)
                res[key]["byMonth"] = {m: mb.block(v, "swing") for m, v in sorted(bymonth.items())}
                res[key]["trades"] = [{"date": t["date"], "sym": t["sym"], "side": t["side"], "R": round(t["swing"][0], 2), "why": t["swing"][1]} for t in tr]
            a = res[key]["swing"]["all"]
            print(f"{key}: {a['n']} trades on {len(dates)} days  win={a['winRate']} avgR={a['avgR']} PF={a['pf']} | OOS {res[key]['swing']['oos']}", flush=True)
    res["_meta"] = {"stocks": len(m5), "months": months, "tookSeconds": round(time.time() - t0)}
    json.dump(res, open(os.path.join(mb.HERE, ".cache", "eagle_backtest.json"), "w"), separators=(",", ":"))
    write_md(res)
    print("done", round(time.time() - t0), "s", flush=True)


def _p(x):
    return f"{x * 100:.0f}%"


def write_md(res):
    meta = res["_meta"]
    L = ["# Eagle Trades - backtest",
         f"_{meta['stocks']} F&O stocks, last {meta['months']} months of 5-minute candles. The Picks screen is read at the decision time; entry 5 minutes later; stop-loss and targets on every trade; 0.1% round-trip cost; "
         "a candle touching both stop and target counts as the stop. No daily cap: every qualifying stock is a trade. Paper research, not advice._", "",
         "**Eagle (as shipped)** = strength >= 75% AND Open = Low (BUY) / Open = High (SELL) with the Picks signal agreeing - the rows marked \"(no risk/reward gate)\". "
         f"The other rows add a risk/reward gate (stop <= {mp.MAX_RISK_PCT:g}% of price and >= {mp.MIN_ROOM_R:g}R of room to the last 20 sessions' high/low), which leaves only about one trade a day. "
         "SWING exit = the pick's own stop, half at 1.5R, rest at 2.5R, up to 10 sessions. INTRADAY = stop beyond today's extreme, flat 15:15.", "",
         "| Screen read at | Trades (days) | Win rate (95% range) | Target hit | Stopped | Avg R | PF | Out-of-sample trades · win · avg R · PF | BUY win · avg R | SELL win · avg R |", "|---|---:|---|---:|---:|---:|---:|---|---|---|"]
    for k, v in res.items():
        if k == "_meta":
            continue
        a, o, b, s = v["swing"]["all"], v["swing"]["oos"], v["swing"]["buy"], v["swing"]["sell"]
        if not a["n"]:
            continue
        L.append(f"| {k} | {a['n']} ({v['days']}) | {_p(a['winRate'])} ({_p(a['ci95'][0])}-{_p(a['ci95'][1])}) | {_p(a['targetHit'])} | {_p(a['stopped'])} | {a['avgR']:+.2f} | {a['pf']} | "
                 f"{o['n']} · {_p(o['winRate'])} · {o['avgR']:+.2f} · {o['pf']} | {_p(b['winRate'])} · {b['avgR']:+.2f} ({b['n']}) | {_p(s['winRate'])} · {s['avgR']:+.2f} ({s['n']}) |")
    L += ["", "## Intraday exit (stop beyond today's extreme, 2R target, flat 15:15)", "", "| Screen read at | Trades | Win rate | Avg R | PF |", "|---|---:|---:|---:|---:|"]
    for k, v in res.items():
        if k == "_meta" or not v["intraday"]["all"]["n"]:
            continue
        a = v["intraday"]["all"]
        L.append(f"| {k} | {a['n']} | {_p(a['winRate'])} | {a['avgR']:+.2f} | {a['pf']} |")
    key = "09:30"
    if key in res and res[key].get("byMonth"):
        L += ["", "## By month (09:30 read, swing exit)", "", "| Month | Trades | Win rate | Avg R |", "|---|---:|---:|---:|"]
        for m, a in res[key]["byMonth"].items():
            L.append(f"| {m} | {a['n']} | {_p(a['winRate'])} | {a['avgR']:+.2f} |")
    open(os.path.join(mb.HERE, "docs", "EAGLE_TRADES_BACKTEST.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 213, int(sys.argv[2]) if len(sys.argv) > 2 else 13)

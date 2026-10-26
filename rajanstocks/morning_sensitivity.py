"""How much do the shortlist's knobs matter?  Re-runs the MORNING replay of morning_backtest.py with one rule changed at a time
(5-minute history comes from the cache that morning_backtest.py filled).

    python morning_sensitivity.py [N_STOCKS=100]
"""
import json
import os
import sys
import time

import bar_source
import market_api
import morning_backtest as mb
import morning_picks as mp
from upstox_service import background

VARIANTS = [
    ("baseline (as shipped)", {}),
    ("no risk/reward gate", {"MIN_ROOM_R": 0.0, "MAX_RISK_PCT": 100.0}),
    ("room >= 1.0R", {"MIN_ROOM_R": 1.0}),
    ("room >= 2.0R", {"MIN_ROOM_R": 2.0}),
    ("Open=Low tolerance exact (0%)", {"OPEN_TOL": 0.0}),
    ("Open=Low tolerance 0.1%", {"OPEN_TOL": 0.001}),
    ("fill-up from strength 25 (score 1)", {"FILL_STRENGTH_MIN": 25}),
    ("read the screen at 09:20", {"_decide": 9 * 60 + 20}),
    ("read the screen at 09:45", {"_decide": 9 * 60 + 45}),
    ("read the screen at 10:15", {"_decide": 10 * 60 + 15}),
]


def main(n=100):
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
    m5 = {s: mb.load_5m(s, 13) for s in liq}
    base = {k: getattr(mp, k) for k in ("MIN_ROOM_R", "MAX_RISK_PCT", "OPEN_TOL", "FILL_STRENGTH_MIN")}
    out = []
    for name, ch in VARIANTS:
        for k, v in base.items():
            setattr(mp, k, v)
        mb.DECIDE_MIN = 9 * 60 + 30
        for k, v in ch.items():
            if k == "_decide":
                mb.DECIDE_MIN = v
            else:
                setattr(mp, k, v)
        t0 = time.time()
        morn = {}
        for s in liq:
            idx = {b["date"]: i for i, b in enumerate(daily[s])}
            for d, p, ctx in mb.build_morning(s, daily[s], idx, m5[s], sector.get(s, "")):
                morn.setdefault(d, []).append((s, p, ctx))
        trades, per_day = [], {}
        for d in sorted(morn):
            plist = [dict(p, s=s) for s, p, _c in morn[d]]
            ctx_of = {s: c for s, _p, c in morn[d]}
            short = mp.select(plist)
            per_day[d] = len(short)
            for p in short:
                tr = mb.trade_morning(p, ctx_of[p["s"]], daily[p["s"]], p["side"], None)
                if tr and tr.get("swing"):
                    trades.append({"date": d, "tier": p["tier"], "both": p["both"], "side": p["side"], **tr})
        dates = sorted(per_day)
        split = dates[int(len(dates) * 0.7)]
        row = {"variant": name, "perDay": round(sum(per_day.values()) / max(1, len(per_day)), 1),
               "daysWith10plus": round(sum(1 for v in per_day.values() if v >= 10) / max(1, len(per_day)), 2)}
        for ek in ("swing", "intraday"):
            row[ek] = {"all": mb.block(trades, ek), "oos": mb.block([t for t in trades if t["date"] > split], ek)}
        out.append(row)
        print(f"{name}: {row['perDay']}/day  swing n={row['swing']['all']['n']} win={row['swing']['all']['winRate']} avgR={row['swing']['all']['avgR']} PF={row['swing']['all']['pf']}"
              f" | OOS n={row['swing']['oos']['n']} avgR={row['swing']['oos']['avgR']} | intraday avgR={row['intraday']['all']['avgR']} ({time.time() - t0:.0f}s)", flush=True)
    for k, v in base.items():
        setattr(mp, k, v)
    json.dump(out, open(os.path.join(mb.HERE, ".cache", "morning_sensitivity.json"), "w"), indent=1)
    L = ["# Morning shortlist - what each rule changes (MORNING replay, 5-minute candles, swing exit)", "",
         f"_{len(liq)} most liquid F&O stocks, {dates[0]} -> {dates[-1]}, entry 5 minutes after the screen is read. Out-of-sample = last 30% of the days. Paper research, not advice._", "",
         "| Variant | Trades / day | Days with 10+ | Trades | Win rate | Avg R | PF | Out-of-sample avg R | Intraday-exit avg R |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in out:
        a, o = r["swing"]["all"], r["swing"]["oos"]
        L.append(f"| {r['variant']} | {r['perDay']} | {r['daysWith10plus'] * 100:.0f}% | {a['n']} | {a['winRate'] * 100:.0f}% | {a['avgR']:+.2f} | {a['pf']} | {o['avgR']:+.2f} | {r['intraday']['all']['avgR']:+.2f} |")
    open(os.path.join(mb.HERE, "docs", "MORNING_PICKS_SENSITIVITY.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)

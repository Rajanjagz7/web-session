"""Health check of every daily-bar indicator on every index (and a few stocks): does it run, does it return a usable signal series, is it up to date,
does every signal carry a stop, and does it ever fire. Prints the problems and writes mock_round/indicator_audit.csv.

    python indicator_audit.py
"""
import csv
import math
import os
import time
from datetime import date, timedelta

import backtest as bt
import bar_source

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mock_round")
SYMS = bt.INDEX_SYMS + ["RELIANCE", "SBIN", "TCS"]


def main():
    import market_api
    market_api.ensure_universe()
    runners = bt._runners(include_hidden=True)
    latest = max(b["date"] for b in bar_source.daily_bars("NIFTY", 30))
    print(f"{len(runners)} indicators x {len(SYMS)} symbols; latest NIFTY daily bar = {latest}", flush=True)
    rows, problems = [], []
    for key, fn in sorted(runners.items()):
        for s in SYMS:
            t0 = time.time()
            r = {"indicator": key, "sym": s, "status": "ok", "bars": 0, "signals": 0, "flips": 0, "withStop": 0, "lastDate": "", "badValues": 0, "sec": 0.0, "note": ""}
            try:
                res = fn(s, 400)
                bars = (res or {}).get("bars") or []
                r["bars"] = len(bars)
                if not bars:
                    r["status"], r["note"] = "EMPTY", "no bars returned"
                else:
                    r["lastDate"] = max((b.get("date") or "") for b in bars)
                    prev = None
                    for b in bars:
                        sg = bt.norm_signal(b.get("signal"))
                        if sg:
                            r["signals"] += 1
                            if sg != prev:
                                r["flips"] += 1
                                if b.get("stop"):
                                    r["withStop"] += 1
                        prev = sg
                        for k in ("open", "high", "low", "close", "stop"):
                            v = b.get(k)
                            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                                r["badValues"] += 1
                    if r["flips"] == 0:
                        r["status"], r["note"] = "NO SIGNALS", "never fired in the window"
                    elif r["lastDate"] < (date.fromisoformat(latest) - timedelta(days=5)).isoformat():
                        r["status"], r["note"] = "STALE", f"last bar {r['lastDate']} vs {latest}"
                    elif r["badValues"]:
                        r["status"], r["note"] = "BAD VALUES", f"{r['badValues']} NaN / inf"
            except Exception as e:
                r["status"], r["note"] = "ERROR", f"{type(e).__name__}: {str(e)[:90]}"
            r["sec"] = round(time.time() - t0, 2)
            rows.append(r)
            if r["status"] != "ok":
                problems.append(r)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "indicator_audit.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    ok = sum(1 for r in rows if r["status"] == "ok")
    print(f"\n{ok} of {len(rows)} runs OK; {len(problems)} with a problem")
    by = {}
    for p in problems:
        by.setdefault((p["indicator"], p["status"], p["note"]), []).append(p["sym"])
    for (k, st, note), syms in sorted(by.items()):
        print(f"  {st:11} {k:26} {','.join(syms)[:60]:60} {note}")
    stopless = [(r["indicator"], r["sym"], r["flips"], r["withStop"]) for r in rows if r["flips"] and r["withStop"] < r["flips"] * 0.5]
    print(f"\nindicators where fewer than half of the signal flips carry their own stop (the engine then uses the signal candle): {len(set(s[0] for s in stopless))}")
    for k in sorted(set(s[0] for s in stopless)):
        print("  ", k)
    slow = sorted(rows, key=lambda r: -r["sec"])[:5]
    print("\nslowest:", [(r["indicator"], r["sym"], r["sec"]) for r in slow])


if __name__ == "__main__":
    main()

"""How Day Power would have scored on past Nifty sessions (Yahoo daily candles, GitHub Actions).

Each session is scored with day_power.score_day using only candles BEFORE that day, then compared with what Nifty
did: the day's close vs the previous close (direction) and close vs open. Also checks every ingredient on its own.
"""
import json
import os
import statistics
import sys
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_backtest_ci as CI  # noqa: E402
import day_power  # noqa: E402
import nse_calendar  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))

if __name__ == "__main__":
    bars = CI._yahoo("NIFTY")
    start = (datetime.now(IST).date() - timedelta(days=730)).isoformat()
    rows = []
    for i, b in enumerate(bars):
        if b["date"] < start or i < 100:
            continue
        d = date.fromisoformat(b["date"])
        r = day_power.score_day(d, nse_calendar.HOLIDAYS, bars[:i])
        prev = bars[i - 1]["close"]
        rows.append({"date": b["date"], "label": r["label"], "side": r["side"], "score": r["score"],
                     "ret": (b["close"] / prev - 1) * 100, "oc": (b["close"] / b["open"] - 1) * 100,
                     "range": (b["high"] - b["low"]) / prev * 100, "parts": {p["name"]: p["pts"] for p in r["parts"]}})
    def summ(rs, key="ret"):
        if not rs:
            return {"n": 0}
        v = [x[key] for x in rs]
        return {"n": len(v), "up": round(sum(1 for x in v if x > 0) / len(v), 3), "avg": round(statistics.mean(v), 3)}
    base = summ(rows)
    by_label = {lab: {"closeVsPrev": summ([x for x in rows if x["label"] == lab]), "closeVsOpen": summ([x for x in rows if x["label"] == lab], "oc"),
                      "rangePct": round(statistics.mean(x["range"] for x in rows if x["label"] == lab), 3)}
                for lab in sorted({x["label"] for x in rows})}
    hits = [x for x in rows if x["side"] in ("bull", "bear")]
    correct = sum(1 for x in hits if (x["ret"] > 0) == (x["side"] == "bull"))
    comps = {}
    for name in rows[0]["parts"]:
        sig = [x for x in rows if x["parts"][name] != 0]
        ok = sum(1 for x in sig if (x["ret"] > 0) == (x["parts"][name] > 0))
        comps[name] = {"days": len(sig), "rightDirection": round(ok / len(sig), 3) if sig else None}
    mix = [x for x in rows if x["side"] == "mix"]
    res = {"generatedAt": datetime.now(IST).isoformat(), "sessions": len(rows), "from": rows[0]["date"], "to": rows[-1]["date"],
           "baseline": base, "directionalCalls": len(hits), "directionalHitRate": round(correct / len(hits), 3) if hits else None,
           "byLabel": by_label, "components": comps,
           "mixDaysRange": round(statistics.mean(x["range"] for x in mix), 3) if mix else None,
           "allDaysRange": round(statistics.mean(x["range"] for x in rows), 3)}
    with open(os.path.join(HERE, "public", "static" if os.path.exists(os.path.join(HERE, "public", "static")) else "static", "day_power_backtest.json"), "w") as f:
        json.dump(res, f)
    print(json.dumps(res, indent=1))

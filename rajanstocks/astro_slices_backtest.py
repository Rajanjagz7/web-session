"""How the astro intraday slices matched Nifty (Yahoo 5-minute candles, last ~60 days, GitHub Actions).

For each session and each slice (rounded out to 5-minute bars, slices under 5 minutes skipped) the Nifty move is
close(at slice end) vs open(at slice start). An "up" label is right when Nifty rose, "down" when it fell. Each label is
compared with the plain base rate of rising slices, and Volatile/Sideways labels with the average size of the move.
Writes static/astro_slices_backtest.json.
"""
import json
import os
import statistics
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import astro_slices  # noqa: E402
import vedic_panchang  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))


def bars5():
    for attempt in range(3):
        try:
            r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI", params={"range": "60d", "interval": "5m"},
                             headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            res = r.json()["chart"]["result"][0]
            q = res["indicators"]["quote"][0]
            days = defaultdict(dict)
            for k, ts in enumerate(res["timestamp"]):
                o, c = q["open"][k], q["close"][k]
                if o is None or c is None:
                    continue
                t = datetime.fromtimestamp(ts, IST)
                days[t.date()][t.hour * 60 + t.minute] = (o, c)
            return days
        except Exception as e:
            print("retry", attempt, e)
            time.sleep(3)
    return {}


def main():
    days = bars5()
    rows = []
    for d in sorted(days):
        b = days[d]
        if len(b) < 60:
            continue
        p = vedic_panchang.compute_panchang(datetime(d.year, d.month, d.day, 9, 15, tzinfo=IST).astimezone(timezone.utc))
        for s in astro_slices.build(d, p)["slices"]:
            a5, e5 = s["a"] // 5 * 5, -(-s["b"] // 5) * 5
            if s["b"] - s["a"] < 5 or a5 not in b or (e5 - 5) not in b:
                continue
            o, c = b[a5][0], b[e5 - 5][1]
            rows.append({"date": d.isoformat(), "label": s["projection"], "tone": s["tone"], "mins": s["b"] - s["a"],
                         "pts": c - o, "pct": (c / o - 1) * 100})
    up_base = sum(1 for r in rows if r["pts"] > 0) / len(rows)
    by = {}
    for lab in sorted({r["label"] for r in rows}):
        rs = [r for r in rows if r["label"] == lab]
        tone = rs[0]["tone"]
        right = None
        if tone == "up":
            right = sum(1 for r in rs if r["pts"] > 0) / len(rs)
        elif tone == "down":
            right = sum(1 for r in rs if r["pts"] < 0) / len(rs)
        by[lab] = {"slices": len(rs), "tone": tone, "rightDirection": round(right, 3) if right is not None else None,
                   "avgPts": round(statistics.mean(r["pts"] for r in rs), 1),
                   "avgAbsPtsPerHour": round(statistics.mean(abs(r["pts"]) / r["mins"] * 60 for r in rs), 1)}
    dirs = [r for r in rows if r["tone"] in ("up", "down")]
    hit = sum(1 for r in dirs if (r["pts"] > 0) == (r["tone"] == "up")) / len(dirs) if dirs else None
    res = {"generatedAt": datetime.now(IST).isoformat(), "sessions": len({r["date"] for r in rows}), "slices": len(rows),
           "from": rows[0]["date"] if rows else None, "to": rows[-1]["date"] if rows else None,
           "baseRateUp": round(up_base, 3), "directionalSlices": len(dirs), "directionalHitRate": round(hit, 3) if hit else None,
           "byLabel": by,
           "readMe": "rightDirection near 0.5 (or near the base rate) = no better than a coin flip. avgAbsPtsPerHour shows whether "
                     "Volatile/Sideways slices really move more or less than the others."}
    with open(os.path.join(HERE, "public", "static" if os.path.exists(os.path.join(HERE, "public", "static")) else "static", "astro_slices_backtest.json"), "w") as f:
        json.dump(res, f)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

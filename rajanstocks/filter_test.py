"""Which risk filters actually help? Replays each one on the last-month mock round (mock_round/trades.csv) and compares it with dropping the same number of
trades at random - a filter that only trades less loses less, a filter with real selection value beats the random drop.

    python filter_test.py      -> mock_round/filter_test.csv + a printed table
"""
import csv
import os
import random
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mock_round")
EXITS = ("2R+LOCK1500", "LADDER")


def load():
    rows = list(csv.DictReader(open(os.path.join(OUT, "trades.csv"), encoding="utf-8")))
    for r in rows:
        for k in ("risk_pts", "prem_est", "lot", "R", "inr", "agree"):
            r[k] = float(r[k])
        r["loss1"] = r["lot"] * 0.5 * r["risk_pts"]                 # 1-lot rupee loss at the stop (12.5 % premium cap)
        r["outlay"] = r["prem_est"] * r["lot"]
    return rows


def prepare(rows, exit_name):
    base = [r for r in rows if r["entries"] == "NEW" and r["exits"] == exit_name]
    votes = defaultdict(set)
    for r in base:
        votes[(r["sym"], r["side"], r["signal"])].add(r["indicators"])
    for r in base:
        r["agree_day"] = len(votes[(r["sym"], r["side"], r["signal"])])
    bias = defaultdict(int)
    seen = set()
    for r in base:
        if r["kind"] == "index" and (r["sym"], r["side"], r["signal"]) not in seen:
            seen.add((r["sym"], r["side"], r["signal"]))
            bias[r["entry_date"]] += 1 if r["side"] == "BUY" else -1
    return base, bias


def stats(rs):
    n = len(rs)
    if not n:
        return {"n": 0, "net": 0, "per": 0, "win": 0, "pf": 0, "worstDay": 0, "dd": 0}
    v = [r["inr"] for r in rs]
    w, l = sum(x for x in v if x > 0), -sum(x for x in v if x < 0)
    day = defaultdict(float)
    for r in rs:
        day[r["exit_date"]] += r["inr"]
    cum = pk = dd = 0.0
    for d in sorted(day):
        cum += day[d]
        pk = max(pk, cum)
        dd = max(dd, pk - cum)
    return {"n": n, "net": round(sum(v)), "per": round(sum(v) / n), "win": round(100 * sum(x > 0 for x in v) / n), "pf": round(w / l, 2) if l else 99.0,
            "worstDay": round(min(day.values())), "dd": round(dd)}


def apply(base, bias, f):
    keep = []
    by_day = defaultdict(list)
    for r in base:
        if "loss" in f and r["loss1"] > f["loss"]:
            continue
        if "outlay" in f and r["outlay"] > f["outlay"]:
            continue
        if f.get("agree") and r["agree_day"] < f["agree"]:
            continue
        if f.get("index"):
            b = bias.get(r["entry_date"], 0)
            if r["kind"] == "stock" and (b == 0 if f["index"] == "strict" else (b != 0 and (b > 0) != (r["side"] == "BUY"))):
                continue
        by_day[r["entry_date"]].append(r)
    for d, lst in by_day.items():
        lst.sort(key=lambda r: (-r["agree_day"], r["loss1"]))                  # best agreement first, then the smaller risk
        if "side_cap" in f:
            cnt, kept = defaultdict(int), []
            for r in lst:
                if cnt[r["side"]] < f["side_cap"]:
                    cnt[r["side"]] += 1
                    kept.append(r)
            lst = kept
        if "heat" in f:
            tot, kept = 0.0, []
            for r in lst:
                if tot + r["loss1"] <= f["heat"]:
                    tot += r["loss1"]
                    kept.append(r)
            lst = kept
        keep += lst
    return keep


FILTERS = [
    ("baseline (no filter)", {}),
    ("1 skip 1-lot stop loss > Rs2,500", {"loss": 2500}),
    ("1 skip 1-lot stop loss > Rs1,800", {"loss": 1800}),
    ("2 need 2+ indicators agreeing", {"agree": 2}),
    ("3a max 4 same-side trades a day", {"side_cap": 4}),
    ("3b stock must not fight the index bias", {"index": "loose"}),
    ("3c stock needs index bias to agree", {"index": "strict"}),
    ("4a open-risk cap Rs10,000 a day", {"heat": 10000}),
    ("4b open-risk cap Rs15,000 a day", {"heat": 15000}),
    ("5 skip premium outlay > Rs20,000", {"outlay": 20000}),
    ("COMBO 1+3a+4b", {"loss": 2500, "side_cap": 4, "heat": 15000}),
    ("COMBO 1+2+3b+4b", {"loss": 2500, "agree": 2, "index": "loose", "heat": 15000}),
]


def main():
    rows = load()
    out = []
    random.seed(7)
    for ex in EXITS:
        base, bias = prepare(rows, ex)
        b = stats(base)
        print(f"\n=== exit {ex} - {len(base)} baseline trades ===")
        print(f"{'filter':42}{'n':>4}{'net Rs':>10}{'Rs/trade':>9}{'win%':>5}{'PF':>6}{'worst day':>10}{'maxDD':>9}  {'beats random drop'}")
        for name, f in FILTERS:
            kept = apply(base, bias, f)
            s = stats(kept)
            beat = ""
            if f and 0 < s["n"] < len(base):
                better = 0
                N = 2000
                for _ in range(N):
                    smp = random.sample(base, s["n"])
                    if sum(r["inr"] for r in smp) < s["net"]:
                        better += 1
                beat = f"{100 * better / N:.0f}%"
            print(f"{name:42}{s['n']:>4}{s['net']:>10,}{s['per']:>9,}{s['win']:>5}{s['pf']:>6}{s['worstDay']:>10,}{s['dd']:>9,}  {beat}")
            out.append({"exit": ex, "filter": name, **s, "beatsRandomPct": beat})
    with open(os.path.join(OUT, "filter_test.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)


if __name__ == "__main__":
    main()

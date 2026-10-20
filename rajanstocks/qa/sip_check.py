"""Independent re-computation of the SIP calculator from the raw NAV history, compared with /api/funds/sip."""
import json
import sys
import urllib.request
from datetime import date, datetime

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")


def get(p):
    with urllib.request.urlopen(BASE + p, timeout=90) as r:
        return json.load(r)


def xirr(flows):
    t0 = flows[0][0]

    def f(r):
        return sum(c / (1 + r) ** ((d - t0).days / 365.0) for d, c in flows)
    lo, hi = -0.99, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


funds = get("/api/funds/list")
items = funds.get("funds") or funds.get("items") or funds
codes = [x.get("code") or x.get("schemeCode") for x in (items if isinstance(items, list) else [])][:4]
print("funds:", len(items), "testing", codes)
bad = 0
for code in codes:
    raw = json.load(urllib.request.urlopen(f"https://api.mfapi.in/mf/{code}", timeout=60))       # the same public source, read directly
    s = get(f"/api/funds/sip?code={code}&amount=10000&years=3&day=5")
    print(code, s.get("scheme", "")[:40], {k: v for k, v in s.items() if not isinstance(v, (list, dict))})
    series = sorted((datetime.strptime(r["date"], "%d-%m-%Y").date(), float(r["nav"])) for r in raw["data"])
    if not series:
        print("  no NAV rows from the public source")
        bad += 1
        continue
    start = date.fromisoformat(s["requested_start"])
    d = start.replace(day=5)
    flows, units, n = [], 0.0, 0
    end = series[-1][0]
    while d <= end and n < 36:
        nxt = next(((dd, v) for dd, v in series if dd >= d), None)
        if not nxt:
            break
        units += 10000 / nxt[1]
        flows.append((nxt[0], -10000.0))
        n += 1
        y, m = (d.year + (d.month // 12), d.month % 12 + 1)
        d = date(y, m, 5)
    value = units * series[-1][1]
    flows.append((end, value))
    mine = {"invested": n * 10000.0, "value": round(value, 2), "xirr": round(xirr(flows) * 100, 2)}
    theirs = {"invested": s.get("invested"), "value": s.get("value"), "xirr": s.get("xirr")}
    print("  mine  :", mine)
    print("  theirs:", theirs)
    if theirs["value"] and abs(theirs["value"] / mine["value"] - 1) > 0.005:
        print("  >>> value differs by more than 0.5%")
        bad += 1
sys.exit(1 if bad else 0)

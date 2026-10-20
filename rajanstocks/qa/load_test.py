"""Small concurrency test: N simulated users hit the feeds the app polls, for a few seconds. Prints p50 / p95 / max latency and errors.

    python qa/load_test.py [base_url] [users] [seconds]
"""
import concurrent.futures as cf
import statistics
import sys
import time
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
USERS = int(sys.argv[2]) if len(sys.argv) > 2 else 8
SECONDS = int(sys.argv[3]) if len(sys.argv) > 3 else 20
FEEDS = [
    "/api/m/quotes", "/api/m/picks", "/api/m/global", "/api/news", "/api/m/chain?symbol=NIFTY",
    "/api/m/candles?symbol=NIFTY&tf=5m&recent=8", "/api/m/candles?symbol=TCS&tf=1D", "/api/m/strategy?key=ut-bot&symbol=RELIANCE",
    "/api/auto/status", "/api/m/health",
]
lat, errs = {f: [] for f in FEEDS}, {}


def user(n):
    end = time.time() + SECONDS
    i = n
    while time.time() < end:
        f = FEEDS[i % len(FEEDS)]
        i += 1
        t = time.time()
        try:
            with urllib.request.urlopen(BASE + f, timeout=60) as r:
                r.read()
            lat[f].append(time.time() - t)
        except urllib.error.HTTPError as e:
            errs[f"{e.code} {f}"] = errs.get(f"{e.code} {f}", 0) + 1
        except Exception:
            errs[f"ERR {f}"] = errs.get(f"ERR {f}", 0) + 1
        time.sleep(0.15)


with cf.ThreadPoolExecutor(USERS) as pool:
    list(pool.map(user, range(USERS)))
print(f"{USERS} users x {SECONDS}s")
tot = 0
for f, v in lat.items():
    if not v:
        continue
    tot += len(v)
    v.sort()
    print(f"  {f[:52]:52s} n={len(v):4d}  p50={statistics.median(v) * 1000:6.0f}ms  p95={v[int(len(v) * 0.95) - 1] * 1000:6.0f}ms  max={v[-1] * 1000:6.0f}ms")
print(f"{tot} requests ({tot / SECONDS:.0f}/s), errors: {errs or 'none'}")
sys.exit(1 if errs else 0)

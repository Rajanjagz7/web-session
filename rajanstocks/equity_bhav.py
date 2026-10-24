"""NSE equity bhavcopy - daily OHLCV for EVERY listed equity in ONE download.

The whole-market Picks walk needs daily history for ~2,700 non-F&O stocks; fetching that
per-symbol from Upstox blew the shared rate budget (26 calls/min measured). The exchange's
public bhavcopy archive (archives.nseindia.com, no cookies) solves it: one ~400KB CSV per
session covers all equities. Files are immutable once published, so each date is fetched at
most once per day and cached in the shared store; the recent sessions warm progressively
(a few downloads per request) until the full 60-session window is available.
"""
import csv
import io
import threading
import time
from datetime import date, datetime, timedelta, timezone

import requests

import shared_cache

IST = timezone(timedelta(hours=5, minutes=30))
URL = "https://archives.nseindia.com/products/content/sec_bhavdata_full_{d}.csv"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
_target = {"sessions": 0}
_lock = threading.Lock()


def _fetch_day(d: date):
    """Parse one session's bhavcopy: {SYMBOL: {"date","open","high","low","close","prev","volume"}} (EQ series only)."""
    key = f"bhav:day2|{d.isoformat()}"
    hit = shared_cache.get(key)
    if hit:
        return hit, True
    if d.weekday() >= 5:
        return None, True                                  # weekend: no file, no retry today
    for attempt in range(2):                               # one transient retry: archives flake occasionally
        try:
            r = requests.get(URL.format(d=d.strftime("%d%m%Y")), timeout=20, headers=UA)
            if r.status_code == 200 and len(r.content) > 5000:
                break
            if r.status_code == 404:
                return None, True                          # holiday/no session: permanent for that date
            print(f"[bhav] {d} -> HTTP {r.status_code} ({len(r.content)}b)")
        except Exception as ex:
            print(f"[bhav] {d} -> {type(ex).__name__}: {str(ex)[:100]}")
        if attempt == 0:
            time.sleep(1.0)
    else:
        return None, False                                 # still failing: transient, retry in the next warm()
    rows = {}
    for row in csv.DictReader(io.StringIO(r.text), skipinitialspace=True):   # NSE writes ", " separators
        if (row.get("SERIES") or "").strip() != "EQ":
            continue
        sym = (row.get("SYMBOL") or "").strip().upper()
        if not sym:
            continue

        def num(field):
            v = (row.get(field) or "").replace(",", "").strip()
            try:
                return float(v)
            except ValueError:
                return 0.0

        rows[sym] = {"date": d.isoformat(), "open": num("OPEN_PRICE"), "high": num("HIGH_PRICE"),
                     "low": num("LOW_PRICE"), "close": num("CLOSE_PRICE"), "prev": num("PREV_CLOSE"),
                     "volume": num("TTL_TRD_QNTY") or num("TTLTRDQV")}
    if rows:
        shared_cache.set(key, rows, 30 * 86400)            # published files are immutable - cache a month
    return rows, bool(rows)


def _dates_back(target_sessions, already):
    """Calendar dates going back from the last session until `target_sessions` new ones are found."""
    d = datetime.now(IST).date()
    out, tries = [], 0
    while len(out) < target_sessions and tries < target_sessions * 2 + 12:
        if d.isoformat() not in already:
            out.append(d)
        d -= timedelta(days=1)
        tries += 1
    return out


def warm(max_downloads=6, target_sessions=60):
    """Fetch a few missing bhavcopy sessions (call repeatedly - it advances). Returns
    {"have": n_REAL_sessions_cached (holidays don't count), "target", "downloaded"}."""
    with _lock:
        idx = shared_cache.get("bhav:index") or {}
        sessions = set(shared_cache.get("bhav:sessions") or [])
        wanted = _dates_back(max(0, target_sessions - len(sessions)), idx)
        got = misses = 0
        for d in wanted[:max(0, max_downloads)]:
            rows, permanent = _fetch_day(d)
            if rows:
                idx[d.isoformat()] = True
                sessions.add(d.isoformat())
                got += 1
            elif permanent:
                idx[d.isoformat()] = True                  # holiday/weekend: marked so it is never refetched
                misses += 1
            else:
                continue                                   # transient: leave unmarked, retry in the next warm()
            if misses >= 8:                                # 8 straight non-sessions = walked past all listings
                break
        shared_cache.set("bhav:index", idx, 30 * 86400)
        shared_cache.set("bhav:sessions", sorted(sessions), 30 * 86400)
        return {"have": len(sessions), "target": target_sessions, "downloaded": got}


def history(symbol, window=60):
    """Daily rows (oldest -> newest) for one symbol from the cached bhavcopy sessions, in the
    shape the Picks screen consumes ({date, open, high, low, close, volume}). None when the
    history is not warmed yet or the symbol has too few sessions."""
    sessions = shared_cache.get("bhav:sessions") or []
    if len(sessions) < 25:
        return None                                        # history not warmed yet
    rows = []
    for d in sorted(sessions):
        day = shared_cache.get(f"bhav:day2|{d}") or {}
        r = day.get(symbol)
        if r and r.get("volume"):
            rows.append(r)
    if len(rows) < 25:
        return None
    return rows[-window:]

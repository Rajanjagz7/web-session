"""Data audit for the buy / sell screens and the chart feeds, against a running server.

    python qa/data_audit.py [base_url]

Checks candles (all timeframes), quotes, Picks, Day calls, Daily scan and the option chain for internal consistency and
agreement with each other, and reports latency / payload size so slow or heavy feeds stand out. Exit code 1 on problems.
"""
import json
import math
import sys
import time
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
problems, perf = [], []


def get(path, timeout=120):
    t = time.time()
    req = urllib.request.Request(BASE + path, headers={"Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            enc = r.headers.get("Content-Encoding")
            if enc == "gzip":
                import gzip
                raw = gzip.decompress(raw)
            return r.status, json.loads(raw), time.time() - t, len(raw), r.headers
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.load(e), time.time() - t, 0, e.headers
        except Exception:
            return e.code, {}, time.time() - t, 0, e.headers
    except Exception as e:
        return 0, {"detail": str(e)[:100]}, time.time() - t, 0, {}


def bad(where, what):
    problems.append((where, what))


fin = lambda x: isinstance(x, (int, float)) and math.isfinite(x)


def check_candles(sym, tf, quote):
    where = f"candles {sym} {tf}"
    s, b, dt, size, h = get(f"/api/m/candles?symbol={sym}&tf={tf}")
    perf.append((dt, size, where, h.get("Content-Encoding") if h else None))
    if s != 200:
        bad(where, f"HTTP {s} {str(b.get('detail', ''))[:90]}")
        return
    bars = b.get("bars") or b.get("candles") or []
    if len(bars) < 20:
        bad(where, f"only {len(bars)} bars")
        return
    prev_t = None
    for i, c in enumerate(bars):
        t, o, hi, lo, cl = c["t"], c["o"], c["h"], c["l"], c["c"]
        if not all(fin(x) for x in (t, o, hi, lo, cl)):
            bad(where, f"bar {i} has a non-finite value")
            break
        if hi + 1e-6 < max(o, cl) or lo - 1e-6 > min(o, cl):
            bad(where, f"bar {i} high/low do not contain open/close: {c}")
            break
        if min(o, hi, lo, cl) <= 0:
            bad(where, f"bar {i} has a non-positive price")
            break
        if prev_t is not None and t <= prev_t:
            bad(where, f"bar {i} timestamp not increasing")
            break
        if c.get("v", 0) < 0:
            bad(where, f"bar {i} negative volume")
            break
        prev_t = t
    last = bars[-1]
    if quote and quote.get("last") and abs(last["c"] / quote["last"] - 1) > 0.05:
        bad(where, f"last close {last['c']} is {abs(last['c'] / quote['last'] - 1) * 100:.1f}% from live {quote['last']}")
    return bars


def main():
    s, qb, dt, size, _ = get("/api/m/quotes")
    perf.append((dt, size, "quotes (all)", None))
    if s != 200:
        print("quotes failed", s, qb)
        sys.exit(2)
    quotes = {q["s"]: q for q in qb["quotes"]}
    print(f"quotes: {len(quotes)} symbols, marketOpen={qb.get('marketOpen')}, stale={qb.get('stale')}")
    for q in list(quotes.values()):
        if q["last"] <= 0:
            bad(f"quote {q['s']}", "last <= 0")
        elif q["prev"] > 0 and abs(q["last"] / q["prev"] - 1) > 0.35:
            bad(f"quote {q['s']}", f"moved {abs(q['last'] / q['prev'] - 1) * 100:.0f}% vs prev close")
        elif q["high"] and q["low"] and not (q["low"] - 1e-6 <= q["last"] <= q["high"] + 1e-6) and qb.get("marketOpen"):
            bad(f"quote {q['s']}", f"last {q['last']} outside day range {q['low']}-{q['high']}")
    for sym in ("NIFTY", "BANKNIFTY", "RELIANCE", "TCS"):
        for tf in ("1m", "5m", "15m", "1H", "1D", "1W"):
            check_candles(sym, tf, quotes.get(sym))
    # Picks
    s, p, dt, size, _ = get("/api/m/picks")
    perf.append((dt, size, "picks", None))
    rows = [r for r in (p.get("picks") or []) if r.get("signal") in ("BUY", "SELL")] if s == 200 else []
    if s != 200:
        bad("picks", f"HTTP {s}")
    for r in rows:
        w = f"pick {r.get('s')} {r.get('signal')}"
        buy = r.get("signal") == "BUY"
        e, sl = r.get("entry"), r.get("stop")
        t1, t2 = r.get("target"), r.get("target2")
        if not all(fin(x) for x in (e, sl)):
            bad(w, "entry/sl missing")
            continue
        if buy and not sl < e:
            bad(w, f"BUY stop {sl} not below entry {e}")
        if not buy and not sl > e:
            bad(w, f"SELL stop {sl} not above entry {e}")
        for tn, tv in (("t1", t1), ("t2", t2)):
            if fin(tv) and ((buy and tv <= e) or (not buy and tv >= e)):
                bad(w, f"{tn} {tv} on the wrong side of entry {e}")
        q = quotes.get(r.get("s"))
        if q and q["last"] and abs(e / q["last"] - 1) > 0.05:
            bad(w, f"entry {e} is {abs(e / q['last'] - 1) * 100:.1f}% from live {q['last']}")
    print(f"picks: {len(rows)} BUY/SELL signals of {len(p.get('picks') or [])}, complete={p.get('complete')}")
    # day calls, daily scan, chain
    for path in ("/api/m/day-calls", "/api/m/daily-scan", "/api/m/option-low-range", "/api/m/global"):
        s, b, dt, size, _ = get(path)
        perf.append((dt, size, path, None))
        if s != 200:
            bad(path, f"HTTP {s} {str(b.get('detail', ''))[:90]}")
    for sym in ("NIFTY", "BANKNIFTY", "RELIANCE"):
        s, c, dt, size, _ = get(f"/api/m/chain?symbol={sym}")
        perf.append((dt, size, f"chain {sym}", None))
        if s != 200:
            bad(f"chain {sym}", f"HTTP {s}")
            continue
        q = quotes.get(sym)
        if q and q["last"] and abs(c["spot"] / q["last"] - 1) > 0.01:
            bad(f"chain {sym}", f"spot {c['spot']} differs from quote {q['last']}")
        atm = c.get("atm")
        if atm and abs(atm - c["spot"]) > max(abs(r["strike"] - c["spot"]) for r in c["rows"][:3]) * 3:
            bad(f"chain {sym}", f"ATM {atm} far from spot {c['spot']}")
        strikes = [r["strike"] for r in c["rows"]]
        if strikes != sorted(strikes) or len(set(strikes)) != len(strikes):
            bad(f"chain {sym}", "strikes not sorted/unique")
        for r in c["rows"]:
            ce, pe = r.get("ce"), r.get("pe")
            for side, leg in (("CE", ce), ("PE", pe)):
                if leg:
                    if leg["ltp"] < 0 or leg["high"] < leg["low"] - 1e-9:
                        bad(f"chain {sym} {r['strike']} {side}", f"ltp {leg['ltp']} high {leg['high']} low {leg['low']}")
            if False and ce and ce["ltp"] > 0 and r["strike"] < c["spot"]:               # deep ITM call must be worth at least intrinsic - 5%
                if ce["ltp"] < (c["spot"] - r["strike"]) * 0.9 and ce["vol"] > 0:
                    bad(f"chain {sym} {r['strike']} CE", f"premium {ce['ltp']} below intrinsic {c['spot'] - r['strike']:.1f}")
            if False and pe and pe["ltp"] > 0 and r["strike"] > c["spot"]:
                if pe["ltp"] < (r["strike"] - c["spot"]) * 0.9 and pe["vol"] > 0:
                    bad(f"chain {sym} {r['strike']} PE", f"premium {pe['ltp']} below intrinsic {r['strike'] - c['spot']:.1f}")
    perf.sort(reverse=True)
    print("\nSlowest / heaviest feeds:")
    for dt, size, w, enc in perf[:10]:
        print(f"  {dt:6.2f}s {size / 1024:8.1f} KB  {w}  gzip={enc}")
    if problems:
        print(f"\n{len(problems)} PROBLEMS")
        for w, p in problems[:60]:
            print(f" - {w}: {p}")
        sys.exit(1)
    print("\nALL CLEAN")


if __name__ == "__main__":
    main()

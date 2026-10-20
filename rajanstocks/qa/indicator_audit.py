"""Indicator / strategy audit against a running server.

    python qa/indicator_audit.py [base_url]            # default http://127.0.0.1:8000

For every strategy x symbol it calls /api/m/strategy and checks the payload is complete, finite, fresh and
internally consistent (signal vs bias, SL / target on the right side of the price, last bar = last trading day,
close close to the live quote). Option scans are checked row by row. Prints a table of problems and exits 1 if any.
"""
import concurrent.futures as cf
import json
import math
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
SYMS = ["NIFTY", "BANKNIFTY", "SENSEX", "RELIANCE", "TCS", "HDFCBANK", "INFY", "SBIN"]
problems, timings, stats = [], [], {"calls": 0, "ok": 0}


def get(path, timeout=120):
    t = time.time()
    try:
        with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
            body = json.load(r)
            return r.status, body, time.time() - t
    except urllib.error.HTTPError as e:
        try:
            body = json.load(e)
        except Exception:
            body = {}
        return e.code, body, time.time() - t
    except Exception as e:  # network / timeout
        return 0, {"detail": str(e)[:120]}, time.time() - t


def bad(where, what):
    problems.append((where, what))


def finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


def walk_numbers(o, path=""):
    """Yield (path, value) for numbers that are NaN / inf anywhere in the payload."""
    if isinstance(o, float) and not math.isfinite(o):
        yield path, o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from walk_numbers(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o[:400]):
            yield from walk_numbers(v, f"{path}[{i}]")


def last_session():
    """Most recent trading day on or before today (server's own NSE calendar)."""
    d = date.today()
    for _ in range(10):
        s, b, _t = get(f"/api/v1/calendar/session?date={d.isoformat()}")
        if s == 200 and (b.get("isTradingDay") or b.get("is_trading_day")):
            return d
        d -= timedelta(days=1)
    return date.today()


def check_strategy(key, sym, meta, quote, lastday):
    where = f"{key} · {sym}"
    s, b, dt = get(f"/api/m/strategy?key={key}&symbol={sym}")
    stats["calls"] += 1
    timings.append((dt, where))
    if s != 200:
        if s == 400 and meta.get("indexOnly") and sym not in ("NIFTY", "BANKNIFTY", "SENSEX", "FINNIFTY", "MIDCPNIFTY"):
            return                                                     # index-only strategy asked about a stock: expected
        bad(where, f"HTTP {s}: {str(b.get('detail', b))[:110]}")
        return
    stats["ok"] += 1
    for f in ("signal", "bias", "headline", "date", "close"):
        if b.get(f) in (None, ""):
            bad(where, f"missing '{f}'")
    for p, v in walk_numbers(b):
        bad(where, f"non-finite number at {p}")
    if b.get("bias") not in ("bull", "bear", "neutral"):
        bad(where, f"bias '{b.get('bias')}' not bull/bear/neutral")
    sig = str(b.get("signal") or "")
    opt = "PUT" in sig.upper() or "CALL" in sig.upper()          # option signals: SELL PUT is bullish, BUY PUT is bearish
    if not opt and sig.upper().startswith("BUY") and b.get("bias") == "bear":
        bad(where, f"signal {sig} but bias bear")
    if not opt and sig.upper().startswith("SELL") and b.get("bias") == "bull":
        bad(where, f"signal {sig} but bias bull")
    if not finite(b.get("close")) or b.get("close", 0) <= 0:
        bad(where, f"close {b.get('close')} invalid")
    try:
        bd = datetime.fromisoformat(str(b["date"])[:10]).date()
        if (lastday - bd).days > 3 and not b.get("stale"):
            bad(where, f"last bar {bd} is {(lastday - bd).days} days older than the last session {lastday}, not flagged stale")
    except Exception:
        bad(where, f"unparseable date {b.get('date')}")
    if quote and finite(b.get("close")) and quote.get("last"):
        ref = quote["last"]
        if abs(b["close"] / ref - 1) > 0.06:
            bad(where, f"close {b['close']} is {abs(b['close'] / ref - 1) * 100:.1f}% away from live {ref}")
    lv = b.get("levels") or {}
    if isinstance(lv, dict) and finite(lv.get("sl")) and finite(b.get("close")):
        long_ = b.get("bias") == "bull"
        short = b.get("bias") == "bear"
        px = lv.get("entry") if finite(lv.get("entry")) else b["close"]
        if long_ and not lv["sl"] < px * 1.0001:
            bad(where, f"BUY but stop {lv['sl']} is not below entry {px}")
        if short and not lv["sl"] > px * 0.9999:
            bad(where, f"SELL but stop {lv['sl']} is not above entry {px}")
        for tk in ("t1", "t2", "target"):
            if finite(lv.get(tk)):
                if long_ and lv[tk] < px * 0.9999:
                    bad(where, f"BUY but {tk} {lv[tk]} is below entry {px}")
                if short and lv[tk] > px * 1.0001:
                    bad(where, f"SELL but {tk} {lv[tk]} is above entry {px}")
    for ev in (b.get("events") or [])[:20]:
        if not ev.get("date") or not ev.get("text"):
            bad(where, f"event missing date/text: {ev}")
            break
    for ln in meta.get("lines") or []:
        k = ln.get("k")
        if b.get("chart", True) and meta.get("chart", True) and b.get("bars"):
            vals = [bar.get(k) for bar in b["bars"] if isinstance(bar, dict) and k in bar]
            if vals and not any(finite(v) for v in vals):
                bad(where, f"line '{k}' has no numeric values")


def check_option_scan(key, scope):
    where = f"option-scan {key} ({scope})"
    s, b, dt = get(f"/api/m/option-scan?key={key}&scope={scope}", timeout=180)
    stats["calls"] += 1
    timings.append((dt, where))
    if s != 200:
        bad(where, f"HTTP {s}: {str(b.get('detail', b))[:110]}")
        return
    stats["ok"] += 1
    rows = b.get("rows") or []
    if b.get("failed"):
        bad(where, f"{len(b['failed'])} underlyings failed: {b['failed'][:4]}")
    for p, v in walk_numbers(b):
        bad(where, f"non-finite number at {p}")
        break
    for r in rows[:200]:
        label = f"{where} · {r.get('symbol') or r.get('sym') or r.get('contract') or '?'}"
        for f in ("signal", "reason"):
            pass
        px = r.get("ltp") or r.get("price") or r.get("premium")
        if px is not None and (not finite(px) or px <= 0):
            bad(label, f"price {px} invalid")
        sl, buy = r.get("sl"), r.get("buy") or r.get("entry")
        if finite(sl) and finite(buy) and sl >= buy:
            bad(label, f"SL {sl} not below buy {buy}")
        for tk in ("t1", "t2", "t3", "target", "targets"):
            v = r.get(tk)
            if finite(v) and finite(buy) and v <= buy:
                bad(label, f"{tk} {v} not above buy {buy}")
    return len(rows)


def main():
    s, meta, _ = get("/api/m/strategies?all=true")
    if s != 200:
        print("cannot read strategies", s, meta)
        sys.exit(2)
    metas = {m["key"]: m for m in meta["strategies"]}
    chart_keys = [k for k, m in metas.items() if m.get("kind") != "optscan"]
    opt_keys = [k for k, m in metas.items() if m.get("kind") == "optscan"]
    lastday = last_session()
    qs, qb, _ = get("/api/m/quotes?symbols=" + ",".join(SYMS))
    quotes = {q["s"]: q for q in (qb.get("quotes") or [])} if qs == 200 else {}
    print(f"{len(chart_keys)} chart strategies x {len(SYMS)} symbols, {len(opt_keys)} option scans; last session {lastday}; quotes for {len(quotes)} symbols")
    jobs = [(k, sym) for k in chart_keys for sym in SYMS]
    with cf.ThreadPoolExecutor(4) as pool:
        list(pool.map(lambda j: check_strategy(j[0], j[1], metas[j[0]], quotes.get(j[1]), lastday), jobs))
    for k in opt_keys:
        n = check_option_scan(k, "indices")
        print(f"  option scan {k:22s} rows: {n}")
    timings.sort(reverse=True)
    print(f"\n{stats['ok']}/{stats['calls']} calls returned 200. Slowest 6:")
    for dt, w in timings[:6]:
        print(f"  {dt:6.2f}s  {w}")
    if problems:
        print(f"\n{len(problems)} PROBLEMS")
        seen = set()
        for w, p in problems:
            if (w, p) not in seen:
                seen.add((w, p))
                print(f" - {w}: {p}")
        sys.exit(1)
    print("\nALL CLEAN")


if __name__ == "__main__":
    main()

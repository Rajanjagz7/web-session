"""Upstox-backed bar source for the strategy modules.

The ported strategies (UT Bot, Donchian, Rajan/Pavan pack, ...) were written
against a handful of indices. They all pull bars through two functions, so
swapping the source here makes every one of them work on any NSE stock/index
in the app's universe, using the same real Upstox candles as the charts.
"""
import threading
import time

import shared_cache
from datetime import date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
_lock = threading.Lock()
_cache = {}


def _universe():
    import market_api  # lazy: avoids a circular import at module load
    market_api.ensure_universe()
    return {s for s, _, _ in market_api.STOCKS} | {s for s, _ in market_api.INDICES} | {c for c, _n, _g, _k in market_api.MORE_INDICES}


def supports(symbol):
    try:
        return (symbol or "").upper() in _universe()
    except Exception:
        return False


def _up():
    from nse_service import nse_service
    return nse_service.upstox


def _cached(key, ttl, fn):
    with _lock:
        hit = _cache.get(key)
        if hit and time.time() - hit[0] < ttl:
            return hit[1]
    val = fn()
    with _lock:
        _cache[key] = (time.time(), val)
    return val


def _market_started(now):
    return now.weekday() < 5 and now.hour * 60 + now.minute >= 9 * 60 + 15


FULL_DAYS = 1900     # one shared fetch per symbol; every strategy slices what it needs from it
_tl = threading.local()


def completed_only(on=True):
    """Per-thread switch for scanners that only need COMPLETED sessions: history is cached for an hour and the
    extra intraday request for today's forming bar is skipped (about 2 upstream calls fewer per symbol)."""
    _tl.co = bool(on)


def daily_bars(symbol, lookback_days=180):
    """[{date, open, high, low, close, volume}] oldest -> newest, incl. today's
    forming session when the market has opened. The upstream history is fetched ONCE per symbol
    (not once per strategy / look-back), which is what keeps the Upstox request budget healthy."""
    symbol = symbol.upper()
    full = _full_daily(symbol, getattr(_tl, "co", False))
    cut = (date.today() - timedelta(days=int(lookback_days))).isoformat()
    return [b for b in full if b["date"] >= cut]


def _full_daily(symbol, completed=False):
    lookback_days = FULL_DAYS

    def fetch():
        up = _up()
        key, _ = up._resolve_underlying(symbol)
        to_d = date.today().isoformat()
        from_d = (date.today() - timedelta(days=int(lookback_days))).isoformat()
        hist_key = f"dfull|{symbol}|{date.today().isoformat()}"
        rows = shared_cache.get(hist_key)
        if rows is None:
            rows = up.fetch_historical_candles(key, "days", "1", to_d, from_d)
            if rows:
                shared_cache.set(hist_key, rows, 20 * 3600)
        out = {}
        for c in rows:
            d = c["time"][:10]
            out[d] = {"date": d, "open": c["open"], "high": c["high"], "low": c["low"],
                      "close": c["close"], "volume": c["volume"]}
        now = datetime.now(IST)
        today = now.date().isoformat()
        if completed:
            out = {k: v for k, v in out.items() if k < today}
        elif today not in out and _market_started(now):
            try:
                mins = sorted(up.fetch_intraday_candles(key, "minutes", "1"), key=lambda c: c["time"])
            except Exception:
                mins = []
            if mins:
                out[today] = {"date": today, "open": mins[0]["open"], "high": max(m["high"] for m in mins),
                              "low": min(m["low"] for m in mins), "close": mins[-1]["close"],
                              "volume": sum(m["volume"] for m in mins)}
        return [out[k] for k in sorted(out)]

    return _cached(f"dfull{'c' if completed else ''}|{symbol}", 3600 if completed else 60, fetch)


def bars_1m(symbol, days=5):
    """[{dt(IST), open, high, low, close}] for the last few sessions."""
    symbol = symbol.upper()

    def fetch():
        up = _up()
        key, _ = up._resolve_underlying(symbol)
        to_d = date.today().isoformat()
        from_d = (date.today() - timedelta(days=days)).isoformat()
        rows = up.fetch_historical_candles(key, "minutes", "1", to_d, from_d)
        try:
            rows += up.fetch_intraday_candles(key, "minutes", "1")
        except Exception:
            pass
        seen, out = set(), []
        for c in rows:
            if c["time"] in seen:
                continue
            seen.add(c["time"])
            out.append({"dt": datetime.fromisoformat(c["time"]).astimezone(IST), "open": c["open"],
                        "high": c["high"], "low": c["low"], "close": c["close"]})
        out.sort(key=lambda b: b["dt"])
        return out

    return _cached(f"m|{symbol}|{days}", 30, fetch)

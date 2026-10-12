"""Stock-universe scanners — the "Stocks" section, run against individual
NSE equities rather than the indices/commodities the rest of this app's
indicators use. Ported from Rajan's "Top 50 Block Deal Scanner" Pine v6
script (unusual-volume detection against a 20-day average), plus a second,
simpler High Volume Stocks leaderboard built the same way.

None of this app's other daily-bar sources cover individual stocks (the NSE
index archive is index-only, see ut_bot.py; the bundled bhavcopy is options
contracts, not the underlying's own OHLCV) — so this fetches each stock's
own daily history directly from Yahoo Finance's `SYMBOL.NS` tickers instead,
concurrently across the whole universe, with a short cache since a 50-stock
fetch is too slow to repeat on every UI interaction.
"""

import concurrent.futures
import threading
import time
from datetime import datetime

import requests

# The exact 50-stock universe from the shared Pine script (its TradingView
# list use "_" in place of "&"/"-"; restored here to each stock's real NSE
# symbol, which is also what Yahoo's own .NS tickers use unchanged).
STOCK_UNIVERSE = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "BHARTIARTL", "SBIN", "ITC",
    "LT", "KOTAKBANK", "AXISBANK", "HINDUNILVR", "BAJFINANCE", "M&M", "MARUTI",
    "SUNPHARMA", "HCLTECH", "TITAN", "ULTRACEMCO", "NTPC", "TMPV", "POWERGRID",
    "ONGC", "TATASTEEL", "ADANIPORTS",
    "ADANIENT", "ASIANPAINT", "BAJAJFINSV", "BAJAJ-AUTO", "BEL", "COALINDIA",
    "JSWSTEEL", "NESTLEIND", "GRASIM", "HINDALCO", "TECHM", "WIPRO", "CIPLA",
    "DRREDDY", "EICHERMOT", "SBILIFE", "HDFCLIFE", "APOLLOHOSP", "TATACONSUM",
    "TRENT", "ETERNAL", "JIOFIN", "SHRIRAMFIN", "INDIGO", "MAXHEALTH",
]

REQUEST_TIMEOUT = 12
CACHE_TTL_SECONDS = 300  # 5 minutes — a 50-symbol fetch is too slow to repeat per click

_session = requests.Session()
_session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
    ),
})

_cache_lock = threading.Lock()
_cache = {}  # universe key -> {"bars": {symbol: [...]}, "fetchedAt": float}


def _fetch_stock_bars(symbol, lookback_days=40):
    """Daily OHLCV for one stock via Yahoo's SYMBOL.NS ticker. Returns [] on
    any failure (unknown symbol, network hiccup, etc.) rather than raising,
    so one bad symbol in the universe doesn't sink the whole scan."""
    yahoo_symbol = f"{symbol}.NS"
    try:
        resp = _session.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}",
            params={"range": "3mo", "interval": "1d"},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        result = resp.json()["chart"]["result"][0]
        timestamps = result["timestamp"]
        quote = result["indicators"]["quote"][0]
        volumes = quote.get("volume") or [None] * len(timestamps)

        bars = []
        for i, ts in enumerate(timestamps):
            o, h, l, c = quote["open"][i], quote["high"][i], quote["low"][i], quote["close"][i]
            v = volumes[i] if i < len(volumes) else None
            if None in (o, h, l, c, v):
                continue
            bars.append({
                "date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                "open": o, "high": h, "low": l, "close": c, "volume": v,
            })
        return bars[-lookback_days:] if len(bars) > lookback_days else bars
    except Exception:
        return []


def _fetch_universe(universe, max_workers=16):
    """Concurrently fetches every symbol's bars, cached for CACHE_TTL_SECONDS
    keyed by the exact universe list (so Block Deal and High Volume — same
    default universe — share one cache entry and one fetch)."""
    key = ",".join(universe)
    with _cache_lock:
        cached = _cache.get(key)
        if cached and (time.time() - cached["fetchedAt"]) < CACHE_TTL_SECONDS:
            return cached["bars"]

    bars_by_symbol = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_fetch_stock_bars, sym): sym for sym in universe}
        for fut in concurrent.futures.as_completed(futures):
            sym = futures[fut]
            bars_by_symbol[sym] = fut.result()

    with _cache_lock:
        _cache[key] = {"bars": bars_by_symbol, "fetchedAt": time.time()}
    return bars_by_symbol


def _avg_volume_and_change(bars, avg_length):
    """Mirrors the Pine script exactly: av = sma(volume, len)[1] (the average
    of the `avg_length` days BEFORE today, excluding it) and chg = today's
    % change vs yesterday's close."""
    if len(bars) < avg_length + 2:
        return None
    window = bars[-(avg_length + 1):-1]
    avg_vol = sum(b["volume"] for b in window) / avg_length
    today, prev = bars[-1], bars[-2]
    chg_pct = ((today["close"] - prev["close"]) / prev["close"] * 100) if prev["close"] else 0.0
    return today, avg_vol, chg_pct


def block_deal_scan(vol_mult=3.0, avg_length=20, only_hits=False, max_rows=25, universe=None):
    universe = universe or STOCK_UNIVERSE
    bars_by_symbol = _fetch_universe(universe)

    rows = []
    for sym in universe:
        bars = bars_by_symbol.get(sym) or []
        computed = _avg_volume_and_change(bars, avg_length)
        if not computed:
            continue
        today, avg_vol, chg_pct = computed
        ratio = (today["volume"] / avg_vol) if avg_vol else 0.0
        is_hit = ratio >= vol_mult
        is_watch = (not is_hit) and ratio >= vol_mult / 2
        signal = "BLOCK BUY" if (is_hit and chg_pct >= 0) else "BLOCK SELL" if is_hit else "Watch" if is_watch else "-"
        rows.append({
            "symbol": sym,
            "close": today["close"],
            "changePct": chg_pct,
            "volume": today["volume"],
            "avgVolume": avg_vol,
            "ratio": ratio,
            "isHit": is_hit,
            "signal": signal,
            "date": today["date"],
        })

    rows.sort(key=lambda r: r["ratio"], reverse=True)
    hits = sum(1 for r in rows if r["isHit"])
    if only_hits:
        rows = [r for r in rows if r["isHit"]]
    rows = rows[:max_rows]

    return {
        "results": rows,
        "universeSize": len(universe),
        "loaded": sum(1 for s in universe if bars_by_symbol.get(s)),
        "hits": hits,
        "volMult": vol_mult,
        "avgLength": avg_length,
    }


def high_volume_scan(avg_length=20, max_rows=25, universe=None):
    universe = universe or STOCK_UNIVERSE
    bars_by_symbol = _fetch_universe(universe)

    rows = []
    for sym in universe:
        bars = bars_by_symbol.get(sym) or []
        computed = _avg_volume_and_change(bars, avg_length)
        if not computed:
            continue
        today, avg_vol, chg_pct = computed
        ratio = (today["volume"] / avg_vol) if avg_vol else 0.0
        rows.append({
            "symbol": sym,
            "close": today["close"],
            "changePct": chg_pct,
            "volume": today["volume"],
            "avgVolume": avg_vol,
            "ratio": ratio,
            "date": today["date"],
        })

    rows.sort(key=lambda r: r["ratio"], reverse=True)
    rows = rows[:max_rows]

    return {
        "results": rows,
        "universeSize": len(universe),
        "loaded": sum(1 for s in universe if bars_by_symbol.get(s)),
        "avgLength": avg_length,
    }

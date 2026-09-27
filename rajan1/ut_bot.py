"""UT Bot Alerts, ported from the well-known Pine Script (ATR trailing-stop
Buy/Sell indicator), applied to an index's daily closing series. NSE doesn't
expose per-index history through the JSON APIs used elsewhere in this app
(that path returns 503s), so history is rebuilt from NSE's public per-day
"all index close" CSV archive (nsearchives.nseindia.com/content/indices/),
fetched concurrently to keep this fast enough for one request.

SENSEX is a BSE index, and BSE's own API (api.bseindia.com) hard-blocks this
app's requests with a WAF-level 403 — not something that resolves by retrying
or waiting. Its daily history comes from Yahoo Finance's public chart API
instead (no auth needed, one request covers a year of bars). This only
covers the index's own price series, not actual BSE option contracts, so
SENSEX is available here (UT Bot + Charts) but not in the options-chain
scanner tabs or the OH/OL options table, which need real BSE F&O data this
app still doesn't have a source for.
"""

import concurrent.futures
import csv
import io
import threading
from datetime import date, datetime, timedelta

import requests

from nse_service import nse_service

INDEX_CSV_NAME = {
    "NIFTY": "Nifty 50",
    "BANKNIFTY": "Nifty Bank",
    "FINNIFTY": "Nifty Financial Services",
    "MIDCPNIFTY": "Nifty Midcap Select",
}

YAHOO_SYMBOL = {
    "SENSEX": "^BSESN",
    "BITCOIN": "BTC-USD",       # spot, USD
    "CRUDEOIL": "CL=F",         # NYMEX WTI front-month future, USD/barrel
    "GOLD": "GC=F",             # COMEX front-month future, USD/oz troy
    # Internal-only: not part of the app's normal selectable symbol universe,
    # used by rajan_pavan_indicators.india_vix_range_scan to pull India VIX's
    # own daily series alongside whichever index the user picked.
    "INDIAVIX": "^INDIAVIX",
}

_yahoo_session = requests.Session()
_yahoo_session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
    ),
})


def _yahoo_range_for(lookback_days):
    if lookback_days <= 25:
        return "1mo"
    if lookback_days <= 75:
        return "3mo"
    if lookback_days <= 150:
        return "6mo"
    if lookback_days <= 300:
        return "1y"
    return "2y"


def fetch_yahoo_history(symbol, lookback_days=60):
    yahoo_symbol = YAHOO_SYMBOL[symbol.upper()]
    resp = _yahoo_session.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}",
        params={"range": _yahoo_range_for(lookback_days), "interval": "1d"},
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    timestamps = result["timestamp"]
    quote = result["indicators"]["quote"][0]
    volumes = quote.get("volume") or [None] * len(timestamps)

    bars = []
    for i, ts in enumerate(timestamps):
        o, h, l, c = quote["open"][i], quote["high"][i], quote["low"][i], quote["close"][i]
        if None in (o, h, l, c):
            continue
        bars.append({
            "date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
            "open": o, "high": h, "low": l, "close": c,
            "volume": volumes[i] if i < len(volumes) and volumes[i] is not None else 0,
        })
    return bars[-lookback_days:] if len(bars) > lookback_days else bars


# Every indicator that needs daily index history (UT Bot, Donchian, Trade
# Predictor, Quantum Matrix) ends up requesting the same calendar days for
# the same handful of indices, and a published day's archive never changes —
# so cache raw CSV text by date for the life of the process instead of
# re-downloading it on every indicator call.
_day_csv_cache = {}
_day_csv_cache_lock = threading.Lock()


def _fetch_day_csv(session, d):
    key = d.isoformat()
    with _day_csv_cache_lock:
        cached = _day_csv_cache.get(key)
    if cached is not None:
        return cached

    url = f"https://nsearchives.nseindia.com/content/indices/ind_close_all_{d.strftime('%d%m%Y')}.csv"
    try:
        resp = session.get(url, timeout=8)
    except Exception:
        return None
    if resp.status_code != 200:
        return None

    text = resp.text
    with _day_csv_cache_lock:
        _day_csv_cache[key] = text
    return text


def _parse_index_row(csv_text, index_name):
    reader = csv.DictReader(io.StringIO(csv_text))
    for row in reader:
        if (row.get("Index Name") or "").strip().lower() == index_name.lower():
            try:
                dd, mm, yyyy = row["Index Date"].strip().split("-")
                volume_raw = (row.get("Volume") or "").strip()
                try:
                    volume = float(volume_raw) if volume_raw else 0.0
                except ValueError:
                    volume = 0.0
                return {
                    "date": f"{yyyy}-{mm}-{dd}",
                    "open": float(row["Open Index Value"]),
                    "high": float(row["High Index Value"]),
                    "low": float(row["Low Index Value"]),
                    "close": float(row["Closing Index Value"]),
                    "volume": volume,
                }
            except (KeyError, ValueError):
                return None
    return None


def fetch_index_history(symbol, lookback_days=60, max_workers=20):
    symbol = symbol.upper()
    if symbol in YAHOO_SYMBOL:
        return fetch_yahoo_history(symbol, lookback_days=lookback_days)

    index_name = INDEX_CSV_NAME.get(symbol)
    if not index_name:
        supported = ', '.join(list(INDEX_CSV_NAME) + list(YAHOO_SYMBOL))
        raise RuntimeError(f"UT Bot only supports {supported} in this app")

    today = date.today()
    candidates = [today - timedelta(days=i) for i in range(lookback_days)]
    candidates = [d for d in candidates if d.weekday() < 5]  # skip weekends outright

    nse_service.refresh_cookies()
    session = nse_service.session

    bars_by_date = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_fetch_day_csv, session, d): d for d in candidates}
        for fut in concurrent.futures.as_completed(futures):
            text = fut.result()
            if not text:
                continue
            row = _parse_index_row(text, index_name)
            if row:
                bars_by_date[row["date"]] = row

    return sorted(bars_by_date.values(), key=lambda b: b["date"])


def _true_range(bars):
    trs = []
    for i, b in enumerate(bars):
        if i == 0:
            trs.append(b["high"] - b["low"])
        else:
            prev_close = bars[i - 1]["close"]
            trs.append(max(
                b["high"] - b["low"],
                abs(b["high"] - prev_close),
                abs(b["low"] - prev_close),
            ))
    return trs


def _rma(values, length):
    """Wilder's smoothing — what Pine's ta.atr() actually uses, not a plain SMA."""
    out = [None] * len(values)
    if len(values) < length:
        return out
    seed = sum(values[:length]) / length
    out[length - 1] = seed
    prev = seed
    for i in range(length, len(values)):
        prev = (prev * (length - 1) + values[i]) / length
        out[i] = prev
    return out


def compute_signals(bars, key_value=1.0, atr_period=10):
    closes = [b["close"] for b in bars]
    atrs = _rma(_true_range(bars), atr_period)

    stops = [None] * len(bars)
    positions = [0] * len(bars)
    signals = [None] * len(bars)

    for i in range(len(bars)):
        if atrs[i] is None:
            continue
        n_loss = key_value * atrs[i]
        src = closes[i]
        prev_stop = stops[i - 1] if i > 0 and stops[i - 1] is not None else 0.0
        prev_src = closes[i - 1] if i > 0 else src

        if src > prev_stop and prev_src > prev_stop:
            stop = max(prev_stop, src - n_loss)
        elif src < prev_stop and prev_src < prev_stop:
            stop = min(prev_stop, src + n_loss)
        elif src > prev_stop:
            stop = src - n_loss
        else:
            stop = src + n_loss
        stops[i] = stop

        prev_pos = positions[i - 1] if i > 0 else 0
        if prev_src < prev_stop and src > stop:
            positions[i] = 1
        elif prev_src > prev_stop and src < stop:
            positions[i] = -1
        else:
            positions[i] = prev_pos

        if i > 0 and stops[i - 1] is not None:
            crossover = closes[i - 1] <= stops[i - 1] and src > stop
            crossunder = closes[i - 1] >= stops[i - 1] and src < stop
            if src > stop and crossover:
                signals[i] = "BUY"
            elif src < stop and crossunder:
                signals[i] = "SELL"

    return stops, positions, signals


def ut_bot_scan(symbol, key_value=1.0, atr_period=10, lookback_days=60):
    bars = fetch_index_history(symbol, lookback_days=lookback_days)
    if len(bars) <= atr_period:
        raise RuntimeError(
            f"Not enough historical sessions returned by NSE ({len(bars)}) to compute "
            f"ATR({atr_period}) — try a longer lookback"
        )

    stops, positions, signals = compute_signals(bars, key_value=key_value, atr_period=atr_period)

    rows = []
    for i, b in enumerate(bars):
        rows.append({
            "date": b["date"],
            "open": b["open"],
            "high": b["high"],
            "low": b["low"],
            "close": b["close"],
            "trailingStop": stops[i],
            "position": {1: "LONG", -1: "SHORT", 0: "FLAT"}[positions[i]],
            "signal": signals[i],
        })

    last_signal_idx = next((i for i in range(len(rows) - 1, -1, -1) if signals[i]), None)
    current = {
        "date": rows[-1]["date"],
        "close": rows[-1]["close"],
        "trailingStop": rows[-1]["trailingStop"],
        "position": rows[-1]["position"],
        "lastSignal": rows[last_signal_idx]["signal"] if last_signal_idx is not None else None,
        "lastSignalDate": rows[last_signal_idx]["date"] if last_signal_idx is not None else None,
        "barsSinceSignal": (len(rows) - 1 - last_signal_idx) if last_signal_idx is not None else None,
    }

    return {
        "symbol": symbol.upper(),
        "keyValue": key_value,
        "atrPeriod": atr_period,
        "bars": rows,
        "current": current,
    }

"""3-Minute Heikin Ashi 'Dancing Channel' Buy/Sell, ported from
3m_heikin_ashi_dancing_channel_{buy,sell}.pine. Both files are mirror images
of each other (green-HA/upper-band vs red-HA/lower-band), so this runs both
signal tracks together off one shared 3-minute Heikin Ashi series.

Needs real intraday bars, which nothing else in this app sources — NSE's own
intraday history endpoints aren't accessible here (see ut_bot.py), so this
uses Yahoo Finance's 1-minute chart data (available for the last ~5 sessions)
resampled into 3-minute candles. MIDCPNIFTY has no reliably-matching intraday
ticker on Yahoo (unlike its exact daily "Nifty Midcap Select" series used
elsewhere), so it's intentionally left out here rather than approximated.
"""

import math
from datetime import datetime, timedelta, timezone

import requests

IST = timezone(timedelta(hours=5, minutes=30))
SESSION_START_MIN = 9 * 60 + 15

YAHOO_INTRADAY_SYMBOL = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
    "SENSEX": "^BSESN",
}

_session = requests.Session()
_session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
    ),
})


def fetch_1m_bars(symbol):
    import bar_source
    if bar_source.supports(symbol):
        try:
            bars = bar_source.bars_1m(symbol)
            if bars:
                return bars
        except Exception as exc:
            print(f"[bar_source] Upstox 1m bars failed for {symbol}: {exc}")
    yahoo_symbol = YAHOO_INTRADAY_SYMBOL[symbol.upper()]
    resp = _session.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}",
        params={"range": "5d", "interval": "1m"},
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    timestamps = result["timestamp"]
    q = result["indicators"]["quote"][0]

    bars = []
    for i, ts in enumerate(timestamps):
        o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        if None in (o, h, l, c):
            continue
        bars.append({"dt": datetime.fromtimestamp(ts, tz=IST), "open": o, "high": h, "low": l, "close": c})
    return bars


def resample_3m(bars_1m):
    buckets = {}
    order = []
    for b in bars_1m:
        dt = b["dt"]
        minutes_since_open = (dt.hour * 60 + dt.minute) - SESSION_START_MIN
        if minutes_since_open < 0:
            continue
        bucket_offset = (minutes_since_open // 3) * 3
        bucket_minute = SESSION_START_MIN + bucket_offset
        h, m = divmod(bucket_minute, 60)
        key_dt = dt.replace(hour=h, minute=m, second=0, microsecond=0)
        key = key_dt.isoformat()
        if key not in buckets:
            buckets[key] = {"dt": key_dt, "open": b["open"], "high": b["high"], "low": b["low"], "close": b["close"]}
            order.append(key)
        else:
            bk = buckets[key]
            bk["high"] = max(bk["high"], b["high"])
            bk["low"] = min(bk["low"], b["low"])
            bk["close"] = b["close"]
    return [buckets[k] for k in order]


def to_heikin_ashi(bars):
    ha = []
    ha_open_prev = None
    ha_close_prev = None
    for b in bars:
        ha_close = (b["open"] + b["high"] + b["low"] + b["close"]) / 4
        if ha_open_prev is None:
            ha_open = (b["open"] + b["close"]) / 2
        else:
            ha_open = (ha_open_prev + ha_close_prev) / 2
        ha_high = max(b["high"], ha_open, ha_close)
        ha_low = min(b["low"], ha_open, ha_close)
        ha.append({
            "dt": b["dt"], "open": b["open"], "high": b["high"], "low": b["low"], "close": b["close"],
            "haOpen": ha_open, "haHigh": ha_high, "haLow": ha_low, "haClose": ha_close,
        })
        ha_open_prev, ha_close_prev = ha_open, ha_close
    return ha


def _population_stdev(values):
    n = len(values)
    mean = sum(values) / n
    return math.sqrt(sum((v - mean) ** 2 for v in values) / n)


def compute_channel(ha, length=20, mult=2.0, channel_type="bollinger"):
    n = len(ha)
    upper = [None] * n
    lower = [None] * n
    basis = [None] * n
    for i in range(n):
        if i + 1 < length:
            continue
        if channel_type == "donchian":
            window_h = [ha[j]["haHigh"] for j in range(i - length + 1, i + 1)]
            window_l = [ha[j]["haLow"] for j in range(i - length + 1, i + 1)]
            u, l = max(window_h), min(window_l)
            upper[i], lower[i], basis[i] = u, l, (u + l) / 2
        else:
            window_c = [ha[j]["haClose"] for j in range(i - length + 1, i + 1)]
            b = sum(window_c) / length
            dev = _population_stdev(window_c) * mult
            upper[i], lower[i], basis[i] = b + dev, b - dev, b
    return upper, lower, basis


def simulate_trades(ha, upper, lower, side):
    """side: 'buy' (green-HA / upper-band target) or 'sell' (red-HA / lower-band target)."""
    n = len(ha)
    events = []
    active = None  # {entryIdx, entryPrice, stopLoss, target}

    def is_green(i):
        return ha[i]["haClose"] > ha[i]["haOpen"]

    def is_red(i):
        return ha[i]["haClose"] < ha[i]["haOpen"]

    for i in range(n):
        if active is None:
            if upper[i] is None:
                continue
            if side == "buy":
                raw = is_green(i) and (i == 0 or not is_green(i - 1))
                qualifies = raw and upper[i] > ha[i]["close"]
            else:
                raw = is_red(i) and (i == 0 or not is_red(i - 1))
                qualifies = raw and lower[i] < ha[i]["close"]
            if qualifies:
                entry_price = ha[i]["close"]
                stop_loss = ha[i]["haLow"] if side == "buy" else ha[i]["haHigh"]
                target = upper[i] if side == "buy" else lower[i]
                active = {"entryIdx": i, "entryPrice": entry_price, "stopLoss": stop_loss, "target": target}
                events.append({"dt": ha[i]["dt"], "type": side.upper(), "event": "ENTRY", "price": entry_price})
        else:
            if i <= active["entryIdx"]:
                continue
            if side == "buy":
                sl_hit = ha[i]["low"] <= active["stopLoss"]
                tgt_hit = (not sl_hit) and ha[i]["high"] >= active["target"]
            else:
                sl_hit = ha[i]["high"] >= active["stopLoss"]
                tgt_hit = (not sl_hit) and ha[i]["low"] <= active["target"]
            if sl_hit:
                events.append({"dt": ha[i]["dt"], "type": side.upper(), "event": "SL_HIT", "price": active["stopLoss"]})
                active = None
            elif tgt_hit:
                events.append({"dt": ha[i]["dt"], "type": side.upper(), "event": "TARGET_HIT", "price": active["target"]})
                active = None

    return events, active


def dancing_channel_scan(symbol, length=20, mult=2.0, channel_type="bollinger"):
    symbol = symbol.upper()
    import bar_source
    if symbol not in YAHOO_INTRADAY_SYMBOL and not bar_source.supports(symbol):
        raise RuntimeError(
            f"3M Heikin Ashi Dancing Channel supports {', '.join(YAHOO_INTRADAY_SYMBOL)} only "
            "(MIDCPNIFTY has no matching intraday data source)"
        )

    bars_1m = fetch_1m_bars(symbol)
    if not bars_1m:
        raise RuntimeError("No intraday data returned from Yahoo Finance right now")
    bars_3m = resample_3m(bars_1m)
    if len(bars_3m) <= length:
        raise RuntimeError(f"Not enough intraday 3-minute bars ({len(bars_3m)}) for a {length}-period channel")

    ha = to_heikin_ashi(bars_3m)
    upper, lower, basis = compute_channel(ha, length=length, mult=mult, channel_type=channel_type)

    buy_events, buy_active = simulate_trades(ha, upper, lower, "buy")
    sell_events, sell_active = simulate_trades(ha, upper, lower, "sell")

    rows = []
    for i, h in enumerate(ha):
        rows.append({
            "time": h["dt"].strftime("%Y-%m-%d %H:%M"),
            "open": h["open"], "high": h["high"], "low": h["low"], "close": h["close"],
            "haOpen": h["haOpen"], "haHigh": h["haHigh"], "haLow": h["haLow"], "haClose": h["haClose"],
            "upper": upper[i], "lower": lower[i], "basis": basis[i],
        })

    all_events = sorted(buy_events + sell_events, key=lambda e: e["dt"])
    for e in all_events:
        e["time"] = e.pop("dt").strftime("%Y-%m-%d %H:%M")

    def clean_active(active):
        if not active:
            return None
        return {
            "entryPrice": active["entryPrice"],
            "stopLoss": active["stopLoss"],
            "target": active["target"],
            "entryTime": ha[active["entryIdx"]]["dt"].strftime("%Y-%m-%d %H:%M"),
        }

    return {
        "symbol": symbol,
        "length": length,
        "mult": mult,
        "channelType": channel_type,
        "bars": rows[-240:],
        "events": all_events[-40:],
        "buyActive": clean_active(buy_active),
        "sellActive": clean_active(sell_active),
        "lastPrice": ha[-1]["close"],
        "lastTime": ha[-1]["dt"].strftime("%Y-%m-%d %H:%M"),
    }

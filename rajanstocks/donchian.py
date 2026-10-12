"""Donchian Channels, ported from the standard Pine Script (Richard Donchian):
upper = highest high over N periods, lower = lowest low, basis = their average.
Runs on the same daily index bars ut_bot.py already sources (NSE archive for
NIFTY/BANKNIFTY/FINNIFTY/MIDCPNIFTY, Yahoo Finance for SENSEX).
"""

from ut_bot import fetch_index_history


def compute_donchian(bars, length=20):
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]
    upper = [None] * len(bars)
    lower = [None] * len(bars)
    basis = [None] * len(bars)
    for i in range(len(bars)):
        if i + 1 < length:
            continue
        window_h = highs[i - length + 1:i + 1]
        window_l = lows[i - length + 1:i + 1]
        u = max(window_h)
        l = min(window_l)
        upper[i] = u
        lower[i] = l
        basis[i] = (u + l) / 2
    return upper, lower, basis


def donchian_scan(symbol, length=20, lookback_days=120):
    fetch_days = max(lookback_days + length + 10, 60)
    bars = fetch_index_history(symbol, lookback_days=fetch_days)
    if len(bars) <= length:
        raise RuntimeError(
            f"Not enough historical sessions returned ({len(bars)}) to compute a "
            f"{length}-period Donchian channel — try a shorter length or longer lookback"
        )

    upper, lower, basis = compute_donchian(bars, length=length)

    rows = []
    for i, b in enumerate(bars):
        signal = None
        if i > 0 and upper[i - 1] is not None:
            prev_close = bars[i - 1]["close"]
            if b["close"] > upper[i - 1] and prev_close <= upper[i - 1]:
                signal = "BREAK_ABOVE"
            elif b["close"] < lower[i - 1] and prev_close >= lower[i - 1]:
                signal = "BREAK_BELOW"
        rows.append({
            "date": b["date"],
            "open": b["open"], "high": b["high"], "low": b["low"], "close": b["close"],
            "upper": upper[i], "lower": lower[i], "basis": basis[i],
            "signal": signal,
        })

    rows = rows[-lookback_days:] if len(rows) > lookback_days else rows

    last_signal_idx = next((i for i in range(len(rows) - 1, -1, -1) if rows[i]["signal"]), None)
    current = {
        "date": rows[-1]["date"],
        "close": rows[-1]["close"],
        "upper": rows[-1]["upper"],
        "lower": rows[-1]["lower"],
        "basis": rows[-1]["basis"],
        "lastSignal": rows[last_signal_idx]["signal"] if last_signal_idx is not None else None,
        "lastSignalDate": rows[last_signal_idx]["date"] if last_signal_idx is not None else None,
        "barsSinceSignal": (len(rows) - 1 - last_signal_idx) if last_signal_idx is not None else None,
    }

    return {
        "symbol": symbol.upper(),
        "length": length,
        "bars": rows,
        "current": current,
    }

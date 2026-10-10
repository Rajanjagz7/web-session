"""Quantum Matrix Strategy, ported from the Pine v6 indicator. It bundles
several sub-systems onto one chart; here each is computed as data instead of
chart drawings:
  - Support/resistance from an N-bar lookback, with ATR-projected SL/TP1/TP2
    for a bullish setup off support and a bearish setup off resistance.
  - The UT trailing-stop Buy/Sell signal — this is the exact same 4-branch
    formula as ut_bot.py's UT Bot Alerts port, so it's reused directly rather
    than re-implemented.
  - Open=Low / Open=High / Open=PrevClose flags for the latest session.
  - An EMA ribbon (8/13/21/34) on daily close.
  - 09:15 opening-candle fractional levels (H/2, H/3, H/4, L/2, L/3, L/4) —
    this genuinely needs the first intraday candle of the session, so it
    reuses the Yahoo 1-minute intraday fetch built for the Heikin Ashi
    indicator (same symbol coverage: no MIDCPNIFTY).
"""

from heikin_ashi import YAHOO_INTRADAY_SYMBOL, fetch_1m_bars
from ut_bot import _rma, _true_range, compute_signals, fetch_index_history
from trade_predictor import _ema


def compute_key_levels(bars, lookback=20, atr_mult_sl=1.5, reward_risk=2.0, tp1_mult=1.5, tp2_mult=2.0):
    atr = _rma(_true_range(bars), 14)
    i = len(bars) - 1
    window = bars[max(0, i - lookback + 1):i + 1]
    support = min(b["low"] for b in window)
    resistance = max(b["high"] for b in window)
    a = atr[i] or 0

    return {
        "support": support,
        "resistance": resistance,
        "atr": atr[i],
        "bullish": {
            "sl": support - a * atr_mult_sl,
            "tp1": support + a * reward_risk * tp1_mult,
            "tp2": support + a * reward_risk * tp2_mult,
        },
        "bearish": {
            "sl": resistance + a * atr_mult_sl,
            "tp1": resistance - a * reward_risk * tp1_mult,
            "tp2": resistance - a * reward_risk * tp2_mult,
        },
    }


def compute_ema_ribbon(bars):
    closes = [b["close"] for b in bars]
    return {
        "ema8": _ema(closes, 8)[-1],
        "ema13": _ema(closes, 13)[-1],
        "ema21": _ema(closes, 21)[-1],
        "ema34": _ema(closes, 34)[-1],
    }


def compute_opening_levels(symbol):
    import bar_source
    if symbol.upper() not in YAHOO_INTRADAY_SYMBOL and not bar_source.supports(symbol):
        return None
    try:
        bars_1m = fetch_1m_bars(symbol)
    except Exception:
        return None
    if not bars_1m:
        return None

    last_date = bars_1m[-1]["dt"].date()
    todays = [b for b in bars_1m if b["dt"].date() == last_date]
    opening = todays[0] if todays else bars_1m[0]

    h, l = opening["high"], opening["low"]
    return {
        "date": opening["dt"].strftime("%Y-%m-%d"),
        "time": opening["dt"].strftime("%H:%M"),
        "open": opening["open"], "high": h, "low": l, "close": opening["close"],
        "levels": {
            "H/2": h / 2, "L/2": l / 2,
            "H/3": h / 3, "L/3": l / 3,
            "H/4": h / 4, "L/4": l / 4,
        },
    }


def quantum_matrix_scan(symbol, key_value=1.0, atr_period=10, lookback=20, lookback_days=120):
    fetch_days = max(lookback_days + 60, lookback + 40)
    bars = fetch_index_history(symbol, lookback_days=fetch_days)
    if len(bars) <= max(lookback, 34):
        raise RuntimeError(f"Not enough historical sessions returned ({len(bars)}) for this scan")

    key_levels = compute_key_levels(bars, lookback=lookback)
    ema_ribbon = compute_ema_ribbon(bars)

    stops, positions, signals = compute_signals(bars, key_value=key_value, atr_period=atr_period)
    last_signal_idx = next((i for i in range(len(bars) - 1, -1, -1) if signals[i]), None)
    ut_current = {
        "position": {1: "LONG", -1: "SHORT", 0: "FLAT"}[positions[-1]],
        "trailingStop": stops[-1],
        "lastSignal": signals[last_signal_idx] if last_signal_idx is not None else None,
        "lastSignalDate": bars[last_signal_idx]["date"] if last_signal_idx is not None else None,
    }

    last = bars[-1]
    prev_close = bars[-2]["close"] if len(bars) > 1 else None
    flags = {
        "openEqLow": last["open"] == last["low"],
        "openEqHigh": last["open"] == last["high"],
        "openEqPrevClose": prev_close is not None and last["open"] == prev_close,
    }

    opening = compute_opening_levels(symbol)

    return {
        "symbol": symbol.upper(),
        "lastDate": last["date"],
        "lastClose": last["close"],
        "keyLevels": key_levels,
        "emaRibbon": ema_ribbon,
        "utSignal": ut_current,
        "flags": flags,
        "opening": opening,
    }

"""Trade Predictor, ported from the Pine v6 strategy: a UT-Bot-style ATR
trailing stop (a simpler 2-branch trail/dir state machine than the original
UT Bot Alerts script, so implemented separately rather than reused), gated
by a long EMA trend filter, with fixed ATR-multiple SL/TP set at entry and
held for the life of the trade. Runs on the same daily index bars as UT Bot
and Donchian (NSE archive + Yahoo for SENSEX), so SENSEX is supported here
for free.
"""

from ut_bot import _rma, _true_range, fetch_index_history


def _ema(values, length):
    out = [None] * len(values)
    if not values:
        return out
    k = 2 / (length + 1)
    out[0] = values[0]
    for i in range(1, len(values)):
        out[i] = values[i] * k + out[i - 1] * (1 - k)
    return out


def compute_trail(closes, atr, factor):
    n = len(closes)
    trail = [None] * n
    direction = [None] * n
    for i in range(n):
        if atr[i] is None:
            continue
        src = closes[i]
        if trail[i - 1] is None if i > 0 else True:
            # first bar with a defined ATR seeds the trail
            trail[i] = src
            direction[i] = True
            continue
        upper = src + factor * atr[i]
        lower = src - factor * atr[i]
        prev_trail = trail[i - 1]
        prev_dir = direction[i - 1]
        if src > prev_trail and prev_dir:
            trail[i] = max(prev_trail, lower)
        elif src < prev_trail and not prev_dir:
            trail[i] = min(prev_trail, upper)
        else:
            trail[i] = prev_trail
        direction[i] = src > trail[i]
    return trail, direction


def trade_predictor_scan(
    symbol,
    atr_length=10,
    factor=1.5,
    ema_length=200,
    use_trend_filter=True,
    sl_mult=1.5,
    tp_mult=2.0,
    lookback_days=180,
):
    fetch_days = max(lookback_days + ema_length + 20, ema_length + 60)
    bars = fetch_index_history(symbol, lookback_days=fetch_days)
    if len(bars) <= max(atr_length, ema_length):
        raise RuntimeError(
            f"Not enough historical sessions returned ({len(bars)}) for a "
            f"{ema_length}-period EMA — try disabling the trend filter or a shorter EMA length"
        )

    closes = [b["close"] for b in bars]
    atr = _rma(_true_range(bars), atr_length)
    ema_trend = _ema(closes, ema_length) if use_trend_filter else [None] * len(bars)
    trail, direction = compute_trail(closes, atr, factor)

    events = []
    active = None  # {side, entryIdx, entryPrice, sl, tp}
    rows_signal = [None] * len(bars)

    for i in range(1, len(bars)):
        if trail[i] is None or trail[i - 1] is None:
            continue
        src, prev_src = closes[i], closes[i - 1]
        t, prev_t = trail[i], trail[i - 1]

        buy_raw = prev_t >= prev_src and t < src   # crossunder(trail, src)
        sell_raw = prev_t <= prev_src and t > src  # crossover(trail, src)

        trend_ok_buy = (not use_trend_filter) or (ema_trend[i] is not None and src > ema_trend[i])
        trend_ok_sell = (not use_trend_filter) or (ema_trend[i] is not None and src < ema_trend[i])

        final_buy = buy_raw and trend_ok_buy
        final_sell = sell_raw and trend_ok_sell

        if active is not None:
            side = active["side"]
            if side == "long":
                sl_hit = bars[i]["low"] <= active["sl"]
                tp_hit = (not sl_hit) and bars[i]["high"] >= active["tp"]
            else:
                sl_hit = bars[i]["high"] >= active["sl"]
                tp_hit = (not sl_hit) and bars[i]["low"] <= active["tp"]
            if sl_hit:
                events.append({"date": bars[i]["date"], "side": side, "event": "SL_HIT", "price": active["sl"]})
                active = None
            elif tp_hit:
                events.append({"date": bars[i]["date"], "side": side, "event": "TP_HIT", "price": active["tp"]})
                active = None

        if final_buy and (active is None or active["side"] != "long"):
            if active is not None:
                events.append({"date": bars[i]["date"], "side": active["side"], "event": "REVERSED", "price": src})
            sl = src - atr[i] * sl_mult
            tp = src + atr[i] * tp_mult
            active = {"side": "long", "entryIdx": i, "entryPrice": src, "sl": sl, "tp": tp}
            events.append({"date": bars[i]["date"], "side": "long", "event": "ENTRY", "price": src})
            rows_signal[i] = "BUY"
        elif final_sell and (active is None or active["side"] != "short"):
            if active is not None:
                events.append({"date": bars[i]["date"], "side": active["side"], "event": "REVERSED", "price": src})
            sl = src + atr[i] * sl_mult
            tp = src - atr[i] * tp_mult
            active = {"side": "short", "entryIdx": i, "entryPrice": src, "sl": sl, "tp": tp}
            events.append({"date": bars[i]["date"], "side": "short", "event": "ENTRY", "price": src})
            rows_signal[i] = "SELL"

    rows = []
    for i, b in enumerate(bars):
        rows.append({
            "date": b["date"], "close": b["close"],
            "trail": trail[i], "emaTrend": ema_trend[i], "signal": rows_signal[i],
        })
    rows = rows[-lookback_days:] if len(rows) > lookback_days else rows

    active_clean = None
    if active:
        active_clean = {
            "side": active["side"], "entryPrice": active["entryPrice"],
            "sl": active["sl"], "tp": active["tp"],
            "entryDate": bars[active["entryIdx"]]["date"],
        }

    return {
        "symbol": symbol.upper(),
        "bars": rows,
        "events": events[-40:],
        "active": active_clean,
        "lastClose": bars[-1]["close"],
        "lastDate": bars[-1]["date"],
        "useTrendFilter": use_trend_filter,
    }

"""HA 3-Min Dancing Trend Channel + BUY/SELL, ported from the Pine v6
indicator of the same name. Runs on the same 3-minute Heikin Ashi bars as the
3M Heikin Ashi Dancing Channel indicator (heikin_ashi.py), but is a different,
fuller algorithm layered on top: an EMA9/EMA21 trend gate, an EMA+ATR
"dancing" channel used only as the crossover trigger (not the trade target
like the other indicator), an ADX/DI false-signal filter, and a fixed
ATR-multiple stop with a configurable risk:reward target instead of the
channel band itself.
"""

from heikin_ashi import YAHOO_INTRADAY_SYMBOL, fetch_1m_bars, resample_3m, to_heikin_ashi
from trade_predictor import _ema
from ut_bot import _rma, _true_range


def _dmi(bars, length):
    """Wilder's +DI/-DI/ADX off the bars' real OHLC (not Heikin Ashi) — Pine's
    ta.dmi() always reads the chart's actual high/low/close, never a
    HA-substituted series."""
    n = len(bars)
    plus_dm = [0.0] * n
    minus_dm = [0.0] * n
    for i in range(1, n):
        up = bars[i]["high"] - bars[i - 1]["high"]
        down = bars[i - 1]["low"] - bars[i]["low"]
        plus_dm[i] = up if (up > down and up > 0) else 0.0
        minus_dm[i] = down if (down > up and down > 0) else 0.0

    tr_s = _rma(_true_range(bars), length)
    plus_dm_s = _rma(plus_dm, length)
    minus_dm_s = _rma(minus_dm, length)

    plus_di = [None] * n
    minus_di = [None] * n
    dx = [None] * n
    for i in range(n):
        if tr_s[i] is None:
            continue
        p_di = 100 * plus_dm_s[i] / tr_s[i] if tr_s[i] else 0.0
        m_di = 100 * minus_dm_s[i] / tr_s[i] if tr_s[i] else 0.0
        plus_di[i] = p_di
        minus_di[i] = m_di
        denom = p_di + m_di
        dx[i] = 100 * abs(p_di - m_di) / denom if denom else 0.0

    first_valid = next((i for i, d in enumerate(dx) if d is not None), None)
    if first_valid is None:
        adx = [None] * n
    else:
        adx = [None] * first_valid + _rma(dx[first_valid:], length)

    return plus_di, minus_di, adx


def ha_dancing_trend_scan(
    symbol,
    ema_fast_len=9,
    ema_slow_len=21,
    channel_len=20,
    atr_len=14,
    atr_mult=1.5,
    rr=2.0,
    adx_len=14,
    adx_min=18.0,
    use_di=False,
    reverse=True,
):
    symbol = symbol.upper()
    if symbol not in YAHOO_INTRADAY_SYMBOL:
        raise RuntimeError(
            f"HA Dancing Trend Channel supports {', '.join(YAHOO_INTRADAY_SYMBOL)} only "
            "(MIDCPNIFTY has no matching intraday data source)"
        )

    bars_1m = fetch_1m_bars(symbol)
    if not bars_1m:
        raise RuntimeError("No intraday data returned from Yahoo Finance right now")
    bars_3m = resample_3m(bars_1m)
    min_needed = max(ema_slow_len, channel_len, atr_len, adx_len) + 5
    if len(bars_3m) <= min_needed:
        raise RuntimeError(f"Not enough intraday 3-minute bars ({len(bars_3m)}) for these settings")

    ha = to_heikin_ashi(bars_3m)
    ha_closes = [b["haClose"] for b in ha]
    n = len(ha)

    ema_fast = _ema(ha_closes, ema_fast_len)
    ema_slow = _ema(ha_closes, ema_slow_len)
    basis = _ema(ha_closes, channel_len)
    atr = _rma(_true_range(ha), atr_len)
    plus_di, minus_di, adx = _dmi(ha, adx_len)

    upper = [None] * n
    lower = [None] * n
    for i in range(n):
        if basis[i] is None or atr[i] is None:
            continue
        upper[i] = basis[i] + atr[i] * atr_mult
        lower[i] = basis[i] - atr[i] * atr_mult

    def is_bull_candle(i):
        return ha[i]["haClose"] > ha[i]["haOpen"] and ha[i]["haClose"] > ha[i - 1]["haClose"]

    def is_bear_candle(i):
        return ha[i]["haClose"] < ha[i]["haOpen"] and ha[i]["haClose"] < ha[i - 1]["haClose"]

    events = []
    signals = [None] * n
    buy_active = None   # {entryIdx, entryPrice, sl, target}
    sell_active = None

    for i in range(1, n):
        if (
            atr[i] is None or basis[i] is None or basis[i - 1] is None
            or adx[i] is None
        ):
            continue

        bull_trend = ema_fast[i] > ema_slow[i]
        bear_trend = ema_fast[i] < ema_slow[i]
        strong_trend = adx[i] >= adx_min
        crossover_basis = ha_closes[i - 1] <= basis[i - 1] and ha_closes[i] > basis[i]
        crossunder_basis = ha_closes[i - 1] >= basis[i - 1] and ha_closes[i] < basis[i]
        di_ok_buy = (not use_di) or (plus_di[i] is not None and minus_di[i] is not None and plus_di[i] > minus_di[i])
        di_ok_sell = (not use_di) or (plus_di[i] is not None and minus_di[i] is not None and minus_di[i] > plus_di[i])

        buy_signal = bull_trend and is_bull_candle(i) and strong_trend and crossover_basis and di_ok_buy
        sell_signal = bear_trend and is_bear_candle(i) and strong_trend and crossunder_basis and di_ok_sell

        # Phase 1 — exits, evaluated against the state carried INTO this bar
        # (mirrors the Pine script's ordering: SL/target/opposite-signal exits
        # are resolved before any new entry is considered on the same bar).
        buy_sl_hit = buy_active is not None and i > buy_active["entryIdx"] and ha[i]["low"] <= buy_active["sl"]
        buy_tp_hit = (
            buy_active is not None and i > buy_active["entryIdx"]
            and not buy_sl_hit and ha[i]["high"] >= buy_active["target"]
        )
        sell_sl_hit = sell_active is not None and i > sell_active["entryIdx"] and ha[i]["high"] >= sell_active["sl"]
        sell_tp_hit = (
            sell_active is not None and i > sell_active["entryIdx"]
            and not sell_sl_hit and ha[i]["low"] <= sell_active["target"]
        )
        buy_rev_exit = reverse and buy_active is not None and sell_signal and not (buy_sl_hit or buy_tp_hit)
        sell_rev_exit = reverse and sell_active is not None and buy_signal and not (sell_sl_hit or sell_tp_hit)

        if buy_sl_hit or buy_tp_hit or buy_rev_exit:
            event = "SL_HIT" if buy_sl_hit else "TARGET_HIT" if buy_tp_hit else "EXIT_OPPOSITE"
            price = buy_active["sl"] if buy_sl_hit else buy_active["target"] if buy_tp_hit else ha[i]["close"]
            events.append({"dt": ha[i]["dt"], "type": "BUY", "event": event, "price": price})
            buy_active = None

        if sell_sl_hit or sell_tp_hit or sell_rev_exit:
            event = "SL_HIT" if sell_sl_hit else "TARGET_HIT" if sell_tp_hit else "EXIT_OPPOSITE"
            price = sell_active["sl"] if sell_sl_hit else sell_active["target"] if sell_tp_hit else ha[i]["close"]
            events.append({"dt": ha[i]["dt"], "type": "SELL", "event": event, "price": price})
            sell_active = None

        # Phase 2 — new entries, evaluated against the POST-exit state, so a
        # same-bar reversal (close BUY, open SELL) can happen just like Pine.
        if buy_signal and buy_active is None:
            entry = ha[i]["close"]
            sl = entry - atr[i] * atr_mult
            target = entry + (entry - sl) * rr
            buy_active = {"entryIdx": i, "entryPrice": entry, "sl": sl, "target": target}
            events.append({"dt": ha[i]["dt"], "type": "BUY", "event": "ENTRY", "price": entry})
            signals[i] = "BUY"

        if sell_signal and sell_active is None:
            entry = ha[i]["close"]
            sl = entry + atr[i] * atr_mult
            target = entry - (sl - entry) * rr
            sell_active = {"entryIdx": i, "entryPrice": entry, "sl": sl, "target": target}
            events.append({"dt": ha[i]["dt"], "type": "SELL", "event": "ENTRY", "price": entry})
            signals[i] = "SELL"

    rows = []
    for i, h in enumerate(ha):
        rows.append({
            "time": h["dt"].strftime("%Y-%m-%d %H:%M"),
            "open": h["open"], "high": h["high"], "low": h["low"], "close": h["close"],
            "haOpen": h["haOpen"], "haHigh": h["haHigh"], "haLow": h["haLow"], "haClose": h["haClose"],
            "emaFast": ema_fast[i], "emaSlow": ema_slow[i],
            "basis": basis[i], "upper": upper[i], "lower": lower[i],
            "adx": adx[i], "signal": signals[i],
        })

    for e in events:
        e["time"] = e.pop("dt").strftime("%Y-%m-%d %H:%M")

    def clean_active(active):
        if not active:
            return None
        return {
            "entryPrice": active["entryPrice"],
            "stopLoss": active["sl"],
            "target": active["target"],
            "entryTime": ha[active["entryIdx"]]["dt"].strftime("%Y-%m-%d %H:%M"),
        }

    return {
        "symbol": symbol,
        "emaFastLen": ema_fast_len,
        "emaSlowLen": ema_slow_len,
        "channelLen": channel_len,
        "atrLen": atr_len,
        "atrMult": atr_mult,
        "rr": rr,
        "adxLen": adx_len,
        "adxMin": adx_min,
        "useDI": use_di,
        "reverse": reverse,
        "bars": rows[-240:],
        "events": events[-40:],
        "buyActive": clean_active(buy_active),
        "sellActive": clean_active(sell_active),
        "lastPrice": ha[-1]["close"],
        "lastTime": ha[-1]["dt"].strftime("%Y-%m-%d %H:%M"),
    }

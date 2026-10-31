"""The 5 new Rajan strategies (Oct 2026), ported from their TradingView Pine
scripts (see ../pine-indicators/) onto this app's daily-bar strategy engine.

Each *_scan(symbol) walks the daily bar series with the SAME state machine as
its Pine script: entry condition -> initial stop -> T1/T2/T3 (R-multiples of
the initial risk) -> stop moves to breakeven after T1, trails the
strategy's own line after that. Only a completed bar can open or manage a
trade (no repainting), matching auto_trader.py's "last COMPLETED daily bar"
convention.

Reuses the same shared math already in this app rather than reimplementing
it: ut_bot._true_range/_rma (ATR), trade_predictor._ema, ha_dancing_trend._dmi
(ADX/DI), rajan_pavan_indicators._pivot_high/_pivot_low/_rolling_min/_rolling_max,
donchian.compute_donchian, indicators.get_india_vix/vix_tier.

A 6th script (Rajan Premium Levels) isn't here - it scans individual option
CONTRACTS intraday, which doesn't fit this daily-underlying-bar engine. It's
wired into the option-chain scanners in strategies_api.py (OPT_SCANS) instead.
"""
import math

import ha_dancing_trend as _hadt
import rajan_pavan_indicators as rp
import trade_predictor as _tp
import ut_bot
from indicators import get_india_vix, vix_tier

NEW_CATALOG = [
    ("rajan-ibs-reversion", "IBS Reversion (Internal Bar Strength)", "Reversal",
     "UNPROVEN, backtest only. Long-only: buy after a day that closes in the bottom 10% of its own high-low range (IBS under 0.10), exit when a day closes in the top 10% (IBS over 0.90); wide 2.5 ATR stop. Published tests report about 67-74% winners on S&P/Nasdaq (see docs/IBS_REVERSION.md); average win is only about the size of the average loss, and nothing is measured on NSE data yet.", "new"),
    ("rajan-rsi2-pullback", "RSI(2) Pullback (Connors)", "Reversal",
     "UNPROVEN forward test. Long-only mean reversion: close above the 200-day average, 2-day RSI under 10 and close under the 5-day average; wide 2.5 ATR stop, exit when price closes back above the 5-day average. Published US-index backtests report roughly 74-75% winners with small average wins (see docs/RSI2_PULLBACK.md); not yet measured on NSE data.", "new"),
    ("rajan-trend-rider", "Rajan Trend Rider", "Trend",
     "UT Bot ATR trail + EMA200/ADX/ALMA(34) slope filters, structure stop, 1R-3R targets. Pine: Rajan_Trend_Rider.pine.", "new"),
    ("rajan-ha-momentum", "Rajan HA Momentum", "Trend",
     "Heikin Ashi EMA channel cross + EMA9/21 trend + ADX filter, ATR stop, 1R-3R targets (daily-bar adaptation of the 3m/5m intraday Pine script).", "new"),
    ("rajan-breakout-trap", "Rajan Breakout & Trap", "Breakout",
     "Donchian(20) breakout plus fake-breakout/breakdown traps at swing pivots, ADX filter, ATR-clamped stop. Pine: Rajan_Breakout_Trap.pine.", "new"),
    ("rajan-ohol-options", "Rajan OH-OL Options", "Options",
     "Open=Low (bullish) / Open=High (bearish) with India VIX tiering for stop/target width. Works on any F&O stock or index - use Scan stocks for the full-universe view with ATM CE/PE legs. Pine: Rajan_OHOL_Options.pine.", "new"),
    ("rajan-gann-sq9", "Rajan Gann Square of 9", "Trend",
     "Gann Square of 9 levels from previous close, Gann HiLo trend filter (daily-bar adaptation of the intraday day-open Pine script).", "new"),
]
NEW_KEYS_SET = {k for k, *_ in NEW_CATALOG}

NEW_CHART_LINES = {
    "rajan-trend-rider": [("emaTrend", "EMA 200"), ("utTrail", "UT trail")],
    "rajan-ha-momentum": [("basis", "HA channel basis"), ("ema9", "EMA 9"), ("ema21", "EMA 21")],
    "rajan-breakout-trap": [("upper", "Donchian upper"), ("lower", "Donchian lower")],
    "rajan-gann-sq9": [("base", "Gann base"), ("u1", "Buy above (U1)"), ("d1", "Sell below (D1)")],
    "rajan-rsi2-pullback": [("sma200", "SMA 200"), ("sma5", "SMA 5")],
    "rajan-ibs-reversion": [],
}
NO_CHART_NEW = {"rajan-ohol-options"}


def _alma(values, length=34, offset=0.85, sigma=6):
    """Arnaud Legoux Moving Average - same weighting Pine's ta.alma() uses."""
    out = [None] * len(values)
    m = offset * (length - 1)
    s = length / sigma
    weights = [math.exp(-((j - m) ** 2) / (2 * s * s)) for j in range(length)]
    wsum = sum(weights)
    for i in range(length - 1, len(values)):
        window = values[i - length + 1:i + 1]
        out[i] = sum(w * v for w, v in zip(weights, window)) / wsum
    return out


def _atr(bars, period):
    return ut_bot._rma(ut_bot._true_range(bars), period)


def _plan_row(side, entry, init_sl, r1, r2, r3):
    risk = abs(entry - init_sl)
    sign = 1 if side == "LONG" else -1
    return {
        "entry": entry, "stop": init_sl,
        "t1": entry + sign * risk * r1, "t2": entry + sign * risk * r2, "t3": entry + sign * risk * r3,
    }


def _walk(bars, raw_long, raw_short, init_sl_fn, trail_fn, r1=1.0, r2=2.0, r3=3.0):
    """Generic non-repainting trade-engine walk, shared by every new strategy.
    raw_long(i)/raw_short(i)/init_sl_fn(i, side)/trail_fn(i, side, stop) read only bars[0..i].
    Returns (rows, position_state) where rows[i] carries signal/entry/stop/t1/t2/t3/hit1/hit2/hit3
    for charting, and position_state is the live open-trade dict (or None if flat)."""
    n = len(bars)
    rows = [dict(date=b["date"], signal="NONE") for b in bars]
    pos = None  # {side, entry, initSL, stop, t1, t2, t3, hit1, hit2, hit3, entryDate}
    for i in range(1, n):  # bar 0 can't look back; mirrors Pine's bar_index>entryBar guard
        b = bars[i]
        if pos:
            hi, lo = b["high"], b["low"]
            exited = False
            if pos["side"] == "LONG":
                if lo <= pos["stop"]:
                    exited = True
                else:
                    if not pos["hit1"] and hi >= pos["t1"]:
                        pos["hit1"] = True
                    if not pos["hit2"] and hi >= pos["t2"]:
                        pos["hit2"] = True
                    if not pos["hit3"] and hi >= pos["t3"]:
                        pos["hit3"] = True
            else:
                if hi >= pos["stop"]:
                    exited = True
                else:
                    if not pos["hit1"] and lo <= pos["t1"]:
                        pos["hit1"] = True
                    if not pos["hit2"] and lo <= pos["t2"]:
                        pos["hit2"] = True
                    if not pos["hit3"] and lo <= pos["t3"]:
                        pos["hit3"] = True
            if exited:
                rows[i]["signal"] = "EXIT"  # neutral marker - "LONG"/"SHORT" in the name would get mis-read as a fresh directional signal by _bias()
                pos = None
            else:
                cand = trail_fn(i, pos["side"], pos["stop"])
                if cand is not None:
                    pos["stop"] = max(pos["stop"], cand) if pos["side"] == "LONG" else min(pos["stop"], cand)
                if pos["hit1"]:  # breakeven after T1, matching every Pine script's default
                    pos["stop"] = max(pos["stop"], pos["entry"]) if pos["side"] == "LONG" else min(pos["stop"], pos["entry"])
                if pos["hit2"]:  # lock to T1 after T2
                    pos["stop"] = max(pos["stop"], pos["t1"]) if pos["side"] == "LONG" else min(pos["stop"], pos["t1"])
        if pos is None:
            side = "LONG" if raw_long(i) else "SHORT" if raw_short(i) else None
            if side:
                entry = b["close"]
                init_sl = init_sl_fn(i, side)
                if init_sl is not None and ((side == "LONG" and init_sl < entry) or (side == "SHORT" and init_sl > entry)):
                    plan = _plan_row(side, entry, init_sl, r1, r2, r3)
                    pos = {"side": side, "entry": entry, "initSL": init_sl, "stop": init_sl,
                           "t1": plan["t1"], "t2": plan["t2"], "t3": plan["t3"],
                           "hit1": False, "hit2": False, "hit3": False, "entryDate": b["date"]}
                    rows[i]["signal"] = "BUY" if side == "LONG" else "SELL"
                    rows[i]["stop"] = round(init_sl, 2)      # the strategy's own initial stop (used by the backtest / auto trader)
    return rows, pos


def _current_from_pos(last_bar, pos, rows):
    cur = {"date": last_bar["date"], "close": last_bar["close"], "signal": rows[-1]["signal"]}
    if pos:
        cur.update(positionStatus="ACTIVE", positionSide=pos["side"], entry=round(pos["entry"], 2),
                    stopLoss=round(pos["stop"], 2), target1=round(pos["t1"], 2), target2=round(pos["t2"], 2),
                    target3=round(pos["t3"], 2), entryDate=pos["entryDate"])
    return cur


# ───────────────────────── Rajan Trend Rider ─────────────────────────
def rajan_trend_rider_scan(symbol, utKey=1.5, utAtr=10, lookback_days=400):
    bars = ut_bot.fetch_index_history(symbol, lookback_days=lookback_days)
    if len(bars) < 210:
        raise RuntimeError(f"Not enough daily history for Trend Rider ({len(bars)} bars, need 200+ for the trend EMA)")
    closes = [b["close"] for b in bars]
    n = len(bars)

    atr10 = _atr(bars, utAtr)
    atr14 = _atr(bars, 14)
    trail = [None] * n
    for i in range(n):
        if atr10[i] is None:
            continue
        nloss = utKey * atr10[i]
        c = closes[i]
        if trail[i - 1] is None:
            trail[i] = c - nloss
            continue
        prev = trail[i - 1]
        if c > prev and closes[i - 1] > prev:
            trail[i] = max(prev, c - nloss)
        elif c < prev and closes[i - 1] < prev:
            trail[i] = min(prev, c + nloss)
        else:
            trail[i] = c - nloss if c > prev else c + nloss

    ema200 = _tp._ema(closes, 200)
    alma34 = _alma(closes, 34)
    _pdi, _mdi, adx = _hadt._dmi(bars, 14)
    lows = [b["low"] for b in bars]
    highs = [b["high"] for b in bars]
    low10 = rp._rolling_min(lows, 10)
    high10 = rp._rolling_max(highs, 10)

    def ut_buy(i):
        return trail[i] is not None and trail[i - 1] is not None and closes[i] > trail[i] and closes[i - 1] <= trail[i - 1]

    def ut_sell(i):
        return trail[i] is not None and trail[i - 1] is not None and closes[i] < trail[i] and closes[i - 1] >= trail[i - 1]

    def raw_long(i):
        return (ut_buy(i) and ema200[i] is not None and closes[i] > ema200[i] and adx[i] is not None and adx[i] >= 20
                and alma34[i] is not None and alma34[i - 3] is not None and atr14[i] and (alma34[i] - alma34[i - 3]) / atr14[i] > 0) if i >= 3 else False

    def raw_short(i):
        return (ut_sell(i) and ema200[i] is not None and closes[i] < ema200[i] and adx[i] is not None and adx[i] >= 20
                and alma34[i] is not None and alma34[i - 3] is not None and atr14[i] and (alma34[i] - alma34[i - 3]) / atr14[i] < 0) if i >= 3 else False

    def init_sl(i, side):
        if atr14[i] is None or low10[i] is None or high10[i] is None:
            return None
        c = closes[i]
        if side == "LONG":
            risk = min(max(c - low10[i], 0.75 * atr14[i]), 3 * atr14[i])
            return c - risk
        risk = min(max(high10[i] - c, 0.75 * atr14[i]), 3 * atr14[i])
        return c + risk

    def trail_fn(i, side, stop):
        if trail[i] is None:
            return None
        return trail[i] if (side == "LONG" and closes[i] > trail[i]) or (side == "SHORT" and closes[i] < trail[i]) else None

    rows_core, pos = _walk(bars, raw_long, raw_short, init_sl, trail_fn)
    rows = [{**rows_core[i], "emaTrend": ema200[i], "utTrail": trail[i]} for i in range(n)]
    return {"symbol": symbol, "columns": [{"key": "emaTrend", "label": "EMA 200"}, {"key": "utTrail", "label": "UT trail"}],
            "current": _current_from_pos(bars[-1], pos, rows), "bars": rows[-300:], "events": rp._events_from_bars(rows)}


# ───────────────────────── Rajan HA Momentum ─────────────────────────
def rajan_ha_momentum_scan(symbol, lookback_days=300):
    bars = ut_bot.fetch_index_history(symbol, lookback_days=lookback_days)
    if len(bars) < 60:
        raise RuntimeError(f"Not enough daily history for HA Momentum ({len(bars)} bars)")
    n = len(bars)
    ha_bars = [{"dt": b["date"], **b} for b in bars]
    ha = _hadt.to_heikin_ashi(ha_bars) if hasattr(_hadt, "to_heikin_ashi") else __import__("heikin_ashi").to_heikin_ashi(ha_bars)
    ha_close = [h["haClose"] for h in ha]
    ha_open = [h["haOpen"] for h in ha]
    ema9 = _tp._ema(ha_close, 9)
    ema21 = _tp._ema(ha_close, 21)
    basis = _tp._ema(ha_close, 20)
    atr14 = _atr(bars, 14)
    _pdi, _mdi, adx = _hadt._dmi(bars, 14)
    closes = [b["close"] for b in bars]
    lows = [b["low"] for b in bars]
    highs = [b["high"] for b in bars]
    swlo = rp._rolling_min(lows, 3)
    swhi = rp._rolling_max(highs, 3)

    def bull_c(i):
        return ha_close[i] > ha_open[i] and ha_close[i] > ha_close[i - 1]

    def bear_c(i):
        return ha_close[i] < ha_open[i] and ha_close[i] < ha_close[i - 1]

    def x_up(i):
        return basis[i] is not None and basis[i - 1] is not None and ha_close[i] > basis[i] and ha_close[i - 1] <= basis[i - 1]

    def x_dn(i):
        return basis[i] is not None and basis[i - 1] is not None and ha_close[i] < basis[i] and ha_close[i - 1] >= basis[i - 1]

    def raw_long(i):
        return (ema9[i] is not None and ema21[i] is not None and ema9[i] > ema21[i] and bull_c(i)
                and adx[i] is not None and adx[i] >= 18 and x_up(i))

    def raw_short(i):
        return (ema9[i] is not None and ema21[i] is not None and ema9[i] < ema21[i] and bear_c(i)
                and adx[i] is not None and adx[i] >= 18 and x_dn(i))

    def init_sl(i, side):
        if atr14[i] is None:
            return None
        return closes[i] - atr14[i] * 1.5 if side == "LONG" else closes[i] + atr14[i] * 1.5

    def trail_fn(i, side, stop):
        if side == "LONG":
            return swlo[i] if swlo[i] is not None else None
        return swhi[i] if swhi[i] is not None else None

    rows_core, pos = _walk(bars, raw_long, raw_short, init_sl, trail_fn)
    rows = [{**rows_core[i], "basis": basis[i], "ema9": ema9[i], "ema21": ema21[i]} for i in range(n)]
    return {"symbol": symbol, "columns": [{"key": "basis", "label": "HA channel basis"}, {"key": "ema9", "label": "EMA 9"}, {"key": "ema21", "label": "EMA 21"}],
            "current": _current_from_pos(bars[-1], pos, rows), "bars": rows[-300:], "events": rp._events_from_bars(rows)}


# ───────────────────────── Rajan Breakout & Trap ─────────────────────────
def rajan_breakout_trap_scan(symbol, don_len=20, piv_len=10, conf_bars=3, lookback_days=300):
    bars = ut_bot.fetch_index_history(symbol, lookback_days=lookback_days)
    if len(bars) < don_len + piv_len * 2 + 10:
        raise RuntimeError(f"Not enough daily history for Breakout & Trap ({len(bars)} bars)")
    n = len(bars)
    closes = [b["close"] for b in bars]
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]
    upper, lower, _basis = __import__("donchian").compute_donchian(bars, don_len)
    atr14 = _atr(bars, 14)
    _pdi, _mdi, adx = _hadt._dmi(bars, 14)
    ph = rp._pivot_high(highs, piv_len, piv_len)
    pl = rp._pivot_low(lows, piv_len, piv_len)

    res = [None] * n
    sup = [None] * n
    for i in range(n):
        res[i] = ph[i] if ph[i] is not None else (res[i - 1] if i else None)
        sup[i] = pl[i] if pl[i] is not None else (sup[i - 1] if i else None)

    # Fake breakout / breakdown, as in Rajan_Breakout_Trap.pine: a WICK trap pierces the swing level and closes back inside on
    # the same bar; a CONFIRMED trap closes beyond the level and then closes back inside within `conf_bars` bars.
    wick_long = [False] * n
    wick_short = [False] * n
    conf_long = [False] * n
    conf_short = [False] * n
    brk_up = brk_dn = None
    for i in range(n):
        if i and res[i] is not None and res[i - 1] is not None and closes[i] > res[i] and closes[i - 1] <= res[i - 1]:
            brk_up = i
        if i and sup[i] is not None and sup[i - 1] is not None and closes[i] < sup[i] and closes[i - 1] >= sup[i - 1]:
            brk_dn = i
        wick_short[i] = res[i] is not None and highs[i] > res[i] and closes[i] < res[i]
        wick_long[i] = sup[i] is not None and lows[i] < sup[i] and closes[i] > sup[i]
        conf_short[i] = (brk_up is not None and i > brk_up and i - brk_up <= conf_bars
                         and res[i] is not None and closes[i] < res[i])
        conf_long[i] = (brk_dn is not None and i > brk_dn and i - brk_dn <= conf_bars
                        and sup[i] is not None and closes[i] > sup[i])
        if conf_short[i] or (brk_up is not None and i - brk_up > conf_bars):
            brk_up = None
        if conf_long[i] or (brk_dn is not None and i - brk_dn > conf_bars):
            brk_dn = None

    def trap_long(i):  # fake breakdown (bear trap): BUY
        return wick_long[i] or conf_long[i]

    def trap_short(i):  # fake breakout (bull trap): SELL
        return wick_short[i] or conf_short[i]

    def bo_long(i):
        return i > 0 and upper[i - 1] is not None and closes[i] > upper[i - 1] and closes[i - 1] <= upper[i - 1]

    def bo_short(i):
        return i > 0 and lower[i - 1] is not None and closes[i] < lower[i - 1] and closes[i - 1] >= lower[i - 1]

    def _long_any(i):
        adx_ok = adx[i] is not None and adx[i] >= 18
        return (bo_long(i) and adx_ok) or trap_long(i)

    def _short_any(i):
        adx_ok = adx[i] is not None and adx[i] >= 18
        return (bo_short(i) and adx_ok) or trap_short(i)

    def raw_long(i):          # a bar where long and short both fire is dropped (Pine: rawLong = ... and not short)
        return _long_any(i) and not _short_any(i)

    def raw_short(i):
        return _short_any(i) and not _long_any(i)

    def init_sl(i, side):
        if atr14[i] is None:
            return None
        if side == "LONG":
            stop_l = lows[i] if trap_long(i) else (min(lows[max(0, i - 2):i + 1]) if i >= 2 else lows[i])
            risk = min(max(closes[i] - (stop_l - 0.2 * atr14[i]), 0.5 * atr14[i]), 2.5 * atr14[i])
            return closes[i] - risk
        stop_h = highs[i] if trap_short(i) else (max(highs[max(0, i - 2):i + 1]) if i >= 2 else highs[i])
        risk = min(max((stop_h + 0.2 * atr14[i]) - closes[i], 0.5 * atr14[i]), 2.5 * atr14[i])
        return closes[i] + risk

    low10 = rp._rolling_min(lows, 10)
    high10 = rp._rolling_max(highs, 10)

    def trail_fn(i, side, stop):
        return low10[i] if side == "LONG" else high10[i]

    rows_core, pos = _walk(bars, raw_long, raw_short, init_sl, trail_fn)
    rows = [{**rows_core[i], "upper": upper[i], "lower": lower[i]} for i in range(n)]
    return {"symbol": symbol, "columns": [{"key": "upper", "label": "Donchian upper"}, {"key": "lower", "label": "Donchian lower"}],
            "current": _current_from_pos(bars[-1], pos, rows), "bars": rows[-300:], "events": rp._events_from_bars(rows)}


# ───────────────────────── Rajan OH-OL Options ─────────────────────────
# Works on any F&O underlying, not just indices - the Open=High/Open=Low
# read and the India-VIX-tiered stop/target % apply the same way to a stock's
# own options as to an index's.
def rajan_ohol_options_scan(symbol, lookback_days=120):
    symbol = symbol.upper()
    bars = ut_bot.fetch_index_history(symbol, lookback_days=lookback_days)
    if len(bars) < 5:
        raise RuntimeError("Not enough daily history for the OH/OL setup")
    vix = get_india_vix()
    tier = vix_tier(vix)
    rows = []
    for b in bars:
        tol = max(0.05, b["close"] * 0.0005)
        is_ol = b["high"] > b["low"] and abs(b["open"] - b["low"]) <= tol
        is_oh = b["high"] > b["low"] and abs(b["open"] - b["high"]) <= tol
        # BULL_CALL = buy a call; BEAR_PUT = buy a put. (The old SELL_PUT_BIAS name was read as "sell a put" = bullish by the
        # Strategies screen's direction reader, while the trader read it as SELL. These names make both readers agree.)
        rows.append({"date": b["date"], "signal": "BULL_CALL" if is_ol and not is_oh else "BEAR_PUT" if is_oh and not is_ol else "NONE",
                     "openEqLow": is_ol, "openEqHigh": is_oh})
    last_bar = bars[-1]
    cur_row = rows[-1]
    slpct = {1: 5.0, 2: 9.0, 3: 18.0}.get(tier or 2, 9.0)
    t1pct = {1: 9.0, 2: 18.0, 3: 18.0}.get(tier or 2, 18.0)
    current = {
        "date": last_bar["date"], "close": last_bar["close"], "signal": cur_row["signal"],
        "openEqLow": cur_row["openEqLow"], "openEqHigh": cur_row["openEqHigh"],
        "vix": vix, "vixTier": tier, "slPct": slpct, "t1Pct": t1pct,
        "note": "Options-side setup: a BULL_CALL (buy call) / BEAR_PUT (buy put) day means buy the underlying's ATM option on that "
                "side; size the option's own stop/target from slPct/t1Pct off its own entry premium, not the "
                "underlying's points.",
    }
    return {"symbol": symbol, "columns": [], "current": current, "bars": rows[-120:], "events": rp._events_from_bars(rows)}


# ───────────────────────── Rajan Gann Square of 9 ─────────────────────────
def rajan_gann_sq9_scan(symbol, angle_step=0.25, lookback_days=250):
    """Daily-bar adaptation: levels built off each day's PREVIOUS close (the
    Pine script uses day-open on an intraday chart; no generic per-symbol
    intraday-open feed exists in this scan engine, so previous close is the
    closest daily equivalent - same (sqrt(base) +/- n*step)^2 spiral)."""
    bars = ut_bot.fetch_index_history(symbol, lookback_days=lookback_days)
    if len(bars) < 30:
        raise RuntimeError(f"Not enough daily history for Gann Square of 9 ({len(bars)} bars)")
    n = len(bars)
    closes = [b["close"] for b in bars]

    def lvl(base, k):
        return (math.sqrt(base) + k * angle_step) ** 2

    base = [None] * n
    u1 = [None] * n
    d1 = [None] * n
    u2 = [None] * n
    d2 = [None] * n
    hima = rp._rolling_max([b["high"] for b in bars], 3)
    loma = rp._rolling_min([b["low"] for b in bars], 3)
    hilo = [0] * n
    for i in range(1, n):
        hilo[i] = 1 if hima[i - 1] is not None and bars[i]["close"] > hima[i - 1] else \
            -1 if loma[i - 1] is not None and bars[i]["close"] < loma[i - 1] else hilo[i - 1]
        base[i] = closes[i - 1]
        u1[i], d1[i] = lvl(base[i], 1), lvl(base[i], -1)
        u2[i], d2[i] = lvl(base[i], 2), lvl(base[i], -2)

    # Track morning bearish signals for "sell on rise"
    morning_bearish = [None] * n
    for i in range(1, n):
        if base[i] is not None:
            # Check for "sell on rise" - price rises to resistance in morning session
            # In daily bars, we check if open is near resistance and closes lower
            open_px = bars[i]["open"]
            close_px = bars[i]["close"]
            
            # Morning bearish: Open near d1 (resistance) and price falls
            if d1[i] is not None and open_px is not None:
                dist_to_d1 = abs(open_px - d1[i]) / d1[i] * 100
                if dist_to_d1 <= 1.5 and close_px < open_px:
                    morning_bearish[i] = True
            
            # Also check for gap up to resistance
            if d1[i] is not None and open_px is not None and close_px is not None:
                if open_px > d1[i] and close_px < d1[i]:
                    morning_bearish[i] = True

    def raw_long(i):
        return base[i] is not None and closes[i - 1] <= u1[i] and closes[i] > u1[i] and closes[i] < u2[i] and hilo[i] == 1

    def raw_short(i):
        return base[i] is not None and closes[i - 1] >= d1[i] and closes[i] < d1[i] and closes[i] > d2[i] and hilo[i] == -1

    def init_sl(i, side):
        return base[i] if side == "LONG" else base[i]

    def trail_fn(i, side, stop):
        if base[i] is None:
            return None
        dist = (math.sqrt(closes[i]) - math.sqrt(base[i])) / angle_step
        return lvl(base[i], math.floor(dist) - 1) if side == "LONG" else lvl(base[i], math.ceil(dist) + 1)

    rows_core, pos = _walk(bars, raw_long, raw_short, init_sl, trail_fn)
    
    # Add morning bearish signals to rows
    rows = []
    for i in range(n):
        row = {**rows_core[i], "base": base[i], "u1": u1[i], "d1": d1[i]}
        if morning_bearish[i]:
            row["signal"] = "SELL_ON_RISE" if row["signal"] == "NONE" else row["signal"]
            row["note"] = "Morning sell on rise - Open near resistance"
        rows.append(row)
    
    return {"symbol": symbol, "columns": [{"key": "base", "label": "Gann base"}, {"key": "u1", "label": "Buy above"}, {"key": "d1", "label": "Sell below"}, {"key": "signal", "label": "Signal"}],
            "current": _current_from_pos(bars[-1], pos, rows), "bars": rows[-300:], "events": rp._events_from_bars(rows)}


# ───────────────────────── Rajan RSI(2) Pullback (Larry Connors style) ─────────────────────────
RSI2_ENTRY, RSI2_STOP_ATR = 10.0, 2.5


def _sma_list(values, n):
    out = [None] * len(values)
    run = 0.0
    for i, v in enumerate(values):
        run += v
        if i >= n:
            run -= values[i - n]
        if i >= n - 1:
            out[i] = run / n
    return out


def _rsi_wilder(closes, n=2):
    """Wilder RSI (what Connors' RSI(2) uses). None until n+1 closes exist."""
    out = [None] * len(closes)
    if len(closes) <= n:
        return out
    gains = [max(closes[i] - closes[i - 1], 0.0) for i in range(1, len(closes))]
    losses = [max(closes[i - 1] - closes[i], 0.0) for i in range(1, len(closes))]
    ag, al = sum(gains[:n]) / n, sum(losses[:n]) / n
    out[n] = 100.0 if al == 0 else 100.0 - 100.0 / (1 + ag / al)
    for i in range(n + 1, len(closes)):
        ag = (ag * (n - 1) + gains[i - 1]) / n
        al = (al * (n - 1) + losses[i - 1]) / n
        out[i] = 100.0 if al == 0 else 100.0 - 100.0 / (1 + ag / al)
    return out


RSI2_SHORTS = False        # 31 Oct: mirrored short side (close < SMA200, RSI(2) > 100 - RSI2_ENTRY, close > SMA5; stop 2.5 ATR above; exit on a close back below SMA5). OFF = the published long-only rule.


def rajan_rsi2_pullback_scan(symbol, lookback_days=450):
    """Buy a sharp 2-day dip inside a long-term uptrend (UNPROVEN here; published backtests are on US indices).
    Entry (completed bar): close > SMA200, RSI(2) < 10, close < SMA5. Initial stop 2.5 ATR(14) below the close.
    Exit: the stop is pulled up to the close of any day that closes back above the SMA5 (the published exit), plus the engine's
    breakeven-after-T1 rule. Long-only, as in the published tests."""
    bars = ut_bot.fetch_index_history(symbol, lookback_days=lookback_days)
    if len(bars) < 210:
        raise RuntimeError(f"Not enough daily history for RSI(2) Pullback ({len(bars)} bars, need 200+ for the trend average)")
    n = len(bars)
    closes = [b["close"] for b in bars]
    sma200, sma5 = _sma_list(closes, 200), _sma_list(closes, 5)
    rsi2 = _rsi_wilder(closes, 2)
    atr14 = _atr(bars, 14)

    def raw_long(i):
        return (sma200[i] is not None and sma5[i] is not None and rsi2[i] is not None and atr14[i] is not None
                and closes[i] > sma200[i] and rsi2[i] < RSI2_ENTRY and closes[i] < sma5[i])

    def raw_short(i):
        return (RSI2_SHORTS and sma200[i] is not None and sma5[i] is not None and rsi2[i] is not None and atr14[i] is not None
                and closes[i] < sma200[i] and rsi2[i] > 100 - RSI2_ENTRY and closes[i] > sma5[i])      # long-only unless RSI2_SHORTS

    def init_sl(i, side):
        if atr14[i] is None:
            return None
        return closes[i] - RSI2_STOP_ATR * atr14[i] if side == "LONG" else closes[i] + RSI2_STOP_ATR * atr14[i]

    def trail_fn(i, side, stop):
        if sma5[i] is None:
            return None
        if side == "SHORT":
            return closes[i] if closes[i] < sma5[i] else None          # the rebound has faded: exit at this close
        return closes[i] if closes[i] > sma5[i] else None      # bounce confirmed: exit at this close

    rows_core, pos = _walk(bars, raw_long, raw_short, init_sl, trail_fn)
    rows = [{**rows_core[i], "sma200": sma200[i], "sma5": sma5[i], "rsi2": rsi2[i]} for i in range(n)]
    return {"symbol": symbol, "columns": [{"key": "sma200", "label": "SMA 200"}, {"key": "sma5", "label": "SMA 5"}, {"key": "rsi2", "label": "RSI(2)"}],
            "current": _current_from_pos(bars[-1], pos, rows), "bars": rows[-300:], "events": rp._events_from_bars(rows)}


# ───────────────────────── Rajan IBS Reversion (Internal Bar Strength) ─────────────────────────
IBS_ENTRY, IBS_EXIT, IBS_STOP_ATR = 0.10, 0.90, 2.5
IBS_SHORTS = False         # 31 Oct: mirrored short side (a day that closed in the top 10 % of its range; exit when a day closes in the bottom 10 %). OFF = the published long-only rule.


def _ibs(b):
    rng = b["high"] - b["low"]
    return (b["close"] - b["low"]) / rng if rng > 0 else 0.5


def rajan_ibs_reversion_scan(symbol, lookback_days=450):
    """UNPROVEN. Buy a day that closed in the bottom 10% of its range (IBS < 0.10); exit when a day closes in the top 10% (IBS > 0.90).
    Published rule (vendor + futures-blog tests, US indices): enter next open, exit next open. Here: entry on the signal bar's close,
    2.5 ATR(14) stop, and the stop is pulled to the close of the first day with IBS > 0.90 (exit). Long-only."""
    bars = ut_bot.fetch_index_history(symbol, lookback_days=lookback_days)
    if len(bars) < 30:
        raise RuntimeError(f"Not enough daily history for IBS Reversion ({len(bars)} bars)")
    n = len(bars)
    closes = [b["close"] for b in bars]
    ibs = [_ibs(b) for b in bars]
    atr14 = _atr(bars, 14)

    def raw_long(i):
        return atr14[i] is not None and ibs[i] < IBS_ENTRY

    def raw_short(i):
        return IBS_SHORTS and atr14[i] is not None and ibs[i] > 1 - IBS_ENTRY

    def init_sl(i, side):
        if atr14[i] is None:
            return None
        return closes[i] - IBS_STOP_ATR * atr14[i] if side == "LONG" else closes[i] + IBS_STOP_ATR * atr14[i]

    def trail_fn(i, side, stop):
        if side == "SHORT":
            return closes[i] if ibs[i] < 1 - IBS_EXIT else None
        return closes[i] if ibs[i] > IBS_EXIT else None

    rows_core, pos = _walk(bars, raw_long, raw_short, init_sl, trail_fn)
    rows = [{**rows_core[i], "ibs": round(ibs[i], 3)} for i in range(n)]
    return {"symbol": symbol, "columns": [{"key": "ibs", "label": "IBS"}],
            "current": _current_from_pos(bars[-1], pos, rows), "bars": rows[-300:], "events": rp._events_from_bars(rows)}


NEW_KEYS = {
    "rajan-trend-rider": rajan_trend_rider_scan,
    "rajan-ha-momentum": rajan_ha_momentum_scan,
    "rajan-breakout-trap": rajan_breakout_trap_scan,
    "rajan-ohol-options": rajan_ohol_options_scan,
    "rajan-gann-sq9": rajan_gann_sq9_scan,
    "rajan-rsi2-pullback": rajan_rsi2_pullback_scan,
    "rajan-ibs-reversion": rajan_ibs_reversion_scan,
}

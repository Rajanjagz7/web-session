"""Catalog + runner + scanner for the user's own strategies and indicators.

Every strategy here is the existing, already-ported module (ut_bot, donchian,
heikin_ashi, ha_dancing_trend, quantum_matrix, trade_predictor, the 15
Rajan/Pavan Pine ports and the OH/OL setup) -- this file only normalises their
output so the UI can chart, list and scan them uniformly.
"""
import concurrent.futures
import time
from datetime import datetime

from fastapi import APIRouter, HTTPException

import bar_source
import donchian
import ha_dancing_trend
import heikin_ashi
import indicators
import quantum_matrix
import rajan_pavan_indicators as rp
import trade_predictor
import ut_bot
import market_api

router = APIRouter(prefix="/api/m")

# key -> (name, group, description, source)
CATALOG = [
    ("ut-bot", "UT Bot Alerts", "Trend", "ATR trailing-stop Buy/Sell signals (key value 1, ATR 10). Price crossing the trailing stop flips the position.", "core"),
    ("trade-predictor", "Trade Predictor", "Trend", "ATR trailing stop with a 200-EMA trend filter. Shows the active trade with its stop-loss and take-profit.", "core"),
    ("donchian", "Donchian Channel Breakout", "Breakout", "20-bar highest-high / lowest-low channel. Break above or below the channel flags a breakout.", "core"),
    ("quantum-matrix", "Quantum Matrix", "Trend", "Combines UT Bot position, EMA ribbon (8/13/21/34), support / resistance and ATR-based stop and targets.", "core"),
    ("heikin-ashi-channel", "3M Heikin Ashi Dancing Channel", "Intraday", "3-minute Heikin Ashi candles inside a Bollinger channel; entries on channel breaks, last 5 sessions.", "core"),
    ("ha-dancing-trend", "HA Dancing Trend Channel", "Intraday", "3-minute Heikin Ashi trend channel with EMA 9/21, ADX filter, ATR stop and 1:2 target.", "core"),
    ("hammer-support", "Uptrend Hammer Support Entry", "Reversal", "Uptrend (higher highs and lows) pulls back to a swing-low support and prints a hammer candle.", "rp"),
    ("w-pattern", "W Pattern Support Entry", "Reversal", "Double-bottom (W) forming at support inside an uptrend.", "rp"),
    ("ema-9-15", "9 / 15 EMA Setup", "Trend", "9 EMA crossing the 15 EMA with trend confirmation (daily-bar adaptation of the intraday rule).", "rp"),
    ("tight-range", "Tight Range + EMA Compression", "Breakout", "Narrow-range days with EMAs compressed together, ahead of an expansion move.", "rp"),
    ("breakout-15m", "Stock Breakout", "Breakout", "Close above the previous N-bar high on above-average volume (daily-bar adaptation of the 15-minute rule).", "rp"),
    ("breakdown-15m", "Stock Breakdown", "Breakout", "Close below the previous N-bar low on above-average volume (daily-bar adaptation).", "rp"),
    ("volume-buzzer-15m", "Volume Buzzer (short-term)", "Volume", "Volume spike versus its recent average with a short EMA trend filter.", "rp"),
    ("volume-buzzer-daily", "Daily Volume Buzzer", "Volume", "Daily volume well above its average together with a large price move.", "rp"),
    ("rsi-divergence", "RSI Divergence", "Reversal", "Bullish / bearish divergence between price pivots and RSI pivots.", "rp"),
    ("nr7-breakout", "NR-7 Breakout", "Breakout", "Narrowest range of the last 7 sessions followed by a breakout of that bar.", "rp"),
    ("potential-breakout", "Potential Breakout (200D High)", "Breakout", "Price near its 200-day high after a 30-day consolidation.", "rp"),
    ("darvas-supertrend", "Darvas + Supertrend Momentum", "Trend", "Darvas box breakout confirmed by Supertrend, RSI and volume.", "rp"),
    ("bottom-reversal", "Bottom Reversal Confluence", "Reversal", "Multi-condition bottoming setup: EMA, RSI, MACD and 50-SMA confirmation.", "rp"),
    ("confluence", "9/15 + Hammer + W Confluence", "Reversal", "Fires when the 9/15 EMA setup coincides with a hammer or W pattern at support.", "rp"),
    ("vix-range", "India VIX Next-Day Range", "Volatility", "Indicative next-day range = close ± (India VIX ÷ 1600) × close.", "rp"),
    ("oh-ol", "Open = High / Open = Low", "Options", "Index Open=High / Open=Low with VIX tier and call/put volume confirmation. Indices only.", "oh"),
    ("supertrend-mtf", "Supertrend Multi-Timeframe", "Trend", "Supertrend (10, 3) with higher-timeframe confirmation. Buy / Sell on a direction flip; shows whether the weekly trend agrees (daily-bar adaptation of the 15-minute rule).", "core"),
    ("candle-oh-ol", "Open = High / Open = Low Candles", "Reversal", "Flags days that opened exactly at the low (bullish demand drive) or at the high (bearish supply drive).", "core"),
    ("volume-spurt", "Volume Spurt", "Volume", "Volume more than 2x its 20-bar average on a bullish candle - an abnormal institutional spurt.", "core"),
    ("orb-15m", "15-Min Opening Range Breakout", "Intraday", "High and low of the 09:15-09:30 candle range with breakout status and 0.5x / 1.0x extension targets.", "core"),
    ("vwap-rsi", "VWAP + RSI Mean Reversion", "Intraday", "VWAP with 1.5 standard-deviation bands on 5-minute bars; buys a bounce off the lower band with RSI < 40, sells a rejection at the upper band with RSI > 60.", "core"),
]
# Price-scale fields drawn on the chart per strategy (daily-dated results only).
CHART_LINES = {
    "ut-bot": [("trailingStop", "UT trail")], "trade-predictor": [("trail", "Trail"), ("emaTrend", "EMA trend")],
    "donchian": [("upper", "Upper"), ("lower", "Lower"), ("basis", "Basis")],
    "hammer-support": [("emaTrend", "EMA trend"), ("support", "Support")],
    "w-pattern": [("emaTrend", "EMA trend"), ("support", "Support"), ("neckline", "Neckline")],
    "ema-9-15": [("ema9", "EMA 9"), ("ema15", "EMA 15"), ("trendEma", "Trend EMA")],
    "tight-range": [("emaFast", "EMA fast"), ("emaSlow", "EMA slow")],
    "breakout-15m": [("breakoutLevel", "Breakout level")], "breakdown-15m": [("breakdownLevel", "Breakdown level")],
    "volume-buzzer-15m": [("ema", "EMA")], "nr7-breakout": [("nrHigh", "NR7 high"), ("nrLow", "NR7 low")],
    "potential-breakout": [("high200", "200D high")], "darvas-supertrend": [("supertrend", "Supertrend")],
    "bottom-reversal": [("support", "Support")],
    "confluence": [("ema9", "EMA 9"), ("ema15", "EMA 15"), ("support", "Support")],
    "vix-range": [("upperRange", "Upper range"), ("lowerRange", "Lower range")],
    "volume-buzzer-daily": [], "rsi-divergence": [],
    "supertrend-mtf": [("supertrend", "Supertrend")], "candle-oh-ol": [], "volume-spurt": [],
}
NO_CHART = {"quantum-matrix", "heikin-ashi-channel", "ha-dancing-trend", "oh-ol", "orb-15m", "vwap-rsi"}
META = {k: {"key": k, "name": n, "group": g, "desc": d, "indexOnly": src == "oh",
            "chart": k not in NO_CHART, "lines": [{"k": f, "label": l} for f, l in CHART_LINES.get(k, [])]}
        for k, n, g, d, src in CATALOG}
INDEX_SET = {s for s, _ in market_api.INDICES} | {c for c, _n, _g, _k in market_api.MORE_INDICES}

# bar fields to draw on the price chart (daily bars). rp strategies expose theirs via "columns".
CORE_LINES = {
    "ut-bot": [{"k": "trailingStop", "label": "UT trailing stop"}],
    "trade-predictor": [{"k": "trail", "label": "Trail"}, {"k": "emaTrend", "label": "EMA trend"}],
    "donchian": [{"k": "upper", "label": "Upper"}, {"k": "lower", "label": "Lower"}, {"k": "basis", "label": "Basis"}],
}

_cache = {}


def _bias(sig):
    s = (sig or "").upper()
    if any(x in s for x in ("SELL", "SHORT", "BELOW", "BEAR", "DOWN")):
        return "bear"
    if any(x in s for x in ("BUY", "LONG", "ABOVE", "BULL", "UP", "SPURT")):
        return "bull"
    return "neutral"


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _flat(d, prefix=""):
    out = []
    for k, v in (d or {}).items():
        if isinstance(v, dict):
            out += _flat(v, f"{prefix}{k} ")
        elif v is not None and not isinstance(v, (list, bool)):
            out.append({"label": (prefix + k).strip(), "value": round(v, 2) if isinstance(v, float) else v})
    return out



# ----------------------------- additional strategies (ported from the Pine library) -----------------------------
import math
import statistics


def _sma_list(vals, n):
    out = [None] * len(vals)
    for i in range(n - 1, len(vals)):
        out[i] = sum(vals[i - n + 1:i + 1]) / n
    return out


def _raw_supertrend_mtf(symbol):
    bars = bar_source.daily_bars(symbol, 700)
    if len(bars) < 40:
        raise RuntimeError("Not enough daily history for Supertrend")
    line, up = rp._supertrend(bars, 3.0, 10)
    groups, bucket = rp._resample_with_map(bars, "W")
    _wl, wup = rp._supertrend(groups, 3.0, 10)
    htf = rp._htf_prev_value(bucket, wup)
    rows, last_sig_i, last_sig = [], None, None
    for i, b in enumerate(bars):
        sig = None
        if i and up[i] is not None and up[i - 1] is not None and up[i] != up[i - 1]:
            sig = "BUY" if up[i] else "SELL"
            last_sig_i, last_sig = i, sig
        rows.append({"date": b["date"], "supertrend": line[i], "signal": sig, "up": up[i], "htf": htf[i]})
    n = len(bars) - 1
    cur = rows[-1]
    trend = "UP" if cur["up"] else "DOWN"
    htf_t = None if cur["htf"] is None else ("UP" if cur["htf"] else "DOWN")
    return {"bars": rows[-300:], "current": {"date": bars[-1]["date"], "close": bars[-1]["close"], "supertrend": cur["supertrend"],
            "trend": trend, "weeklyTrend": htf_t, "aligned": htf_t == trend if htf_t else None,
            "lastSignal": last_sig, "barsSince": (n - last_sig_i) if last_sig_i is not None else None}}


def _raw_candle_oh_ol(symbol):
    bars = bar_source.daily_bars(symbol, 200)
    rows = []
    for b in bars:
        tol = 0.0 if False else max(0.05, b["close"] * 0.0001)
        ol = b["high"] > b["low"] and abs(b["open"] - b["low"]) <= tol
        oh = b["high"] > b["low"] and abs(b["open"] - b["high"]) <= tol
        rows.append({"date": b["date"], "signal": "BUY" if ol and not oh else "SELL" if oh and not ol else None, "ol": ol, "oh": oh})
    last = bars[-1]
    return {"bars": rows[-120:], "current": {"date": last["date"], "close": last["close"], "open": last["open"], "high": last["high"], "low": last["low"],
            "openEqLow": rows[-1]["ol"], "openEqHigh": rows[-1]["oh"], "signal": rows[-1]["signal"],
            "sessionsWithSignal": sum(1 for r in rows[-20:] if r["signal"])}}


def _raw_volume_spurt(symbol):
    bars = bar_source.daily_bars(symbol, 200)
    vols = [b["volume"] or 0 for b in bars]
    sma = _sma_list(vols, 20)
    rows = []
    for i, b in enumerate(bars):
        spurt = sma[i] is not None and sma[i] > 0 and vols[i] > sma[i] * 2.0 and b["close"] > b["open"]
        rows.append({"date": b["date"], "signal": "SPURT" if spurt else None, "ratio": (vols[i] / sma[i]) if sma[i] else None})
    if not any(vols):
        raise RuntimeError(f"{symbol} has no volume data (indices do not report volume)")
    last = bars[-1]
    return {"bars": rows[-120:], "current": {"date": last["date"], "close": last["close"], "volume": vols[-1], "avgVolume20": sma[-1],
            "ratio": rows[-1]["ratio"], "signal": rows[-1]["signal"]}}


def _session_days(m1):
    days = {}
    for b in m1:
        days.setdefault(b["dt"].date(), []).append(b)
    return days


def _raw_orb(symbol):
    m1 = bar_source.bars_1m(symbol, 5)
    if not m1:
        raise RuntimeError("No intraday data available")
    days = _session_days(m1)
    d = max(days)
    sess = days[d]
    window = [b for b in sess if (b["dt"].hour, b["dt"].minute) < (9, 30)]
    if len(window) < 5:
        raise RuntimeError("The 09:15-09:30 opening range is not complete in the data yet")
    hi, lo = max(b["high"] for b in window), min(b["low"] for b in window)
    rng = hi - lo
    after = [b for b in sess if (b["dt"].hour, b["dt"].minute) >= (9, 30)]
    events, prev = [], None
    state = "INSIDE"
    for b in after:
        c = b["close"]
        if prev is not None and prev <= hi < c:
            events.append({"date": b["dt"].strftime("%d %b %H:%M"), "text": f"ORB BUY - close {c:,.2f} above {hi:,.2f}"}); state = "ORB BUY"
        elif prev is not None and prev >= lo > c:
            events.append({"date": b["dt"].strftime("%d %b %H:%M"), "text": f"ORB SELL - close {c:,.2f} below {lo:,.2f}"}); state = "ORB SELL"
        prev = c
    last = sess[-1]["close"]
    now_state = "ORB BUY" if last > hi else "ORB SELL" if last < lo else "INSIDE"
    return {"date": str(d), "close": last, "orbHigh": hi, "orbLow": lo, "range": rng, "state": now_state, "everBroke": state,
            "long": {"target1": hi + rng * 0.5, "target2": hi + rng * 1.0, "stop": lo}, "short": {"target1": lo - rng * 0.5, "target2": lo - rng * 1.0, "stop": hi},
            "events": events}


def _raw_vwap_rsi(symbol):
    m1 = bar_source.bars_1m(symbol, 5)
    if not m1:
        raise RuntimeError("No intraday data available")
    five = []
    for dday, bars in sorted(_session_days(m1).items()):
        for i in range(0, len(bars), 5):
            ch = bars[i:i + 5]
            five.append({"dt": ch[0]["dt"], "open": ch[0]["open"], "high": max(x["high"] for x in ch), "low": min(x["low"] for x in ch),
                         "close": ch[-1]["close"], "volume": sum(x.get("volume", 0) or 0 for x in ch), "day": dday})
    if len(five) < 40:
        raise RuntimeError("Not enough 5-minute bars yet")
    vw, pv, vv, cur_day = [], 0.0, 0.0, None
    for b in five:
        if b["day"] != cur_day:
            cur_day, pv, vv = b["day"], 0.0, 0.0
        tp = (b["high"] + b["low"] + b["close"]) / 3
        w = b["volume"] or 1.0                           # indices report no volume: equal weights
        pv += tp * w; vv += w
        vw.append(pv / vv)
    closes = [b["close"] for b in five]
    rsi = rp._rsi(closes, 14)
    dev = [None] * len(five)
    for i in range(19, len(five)):
        diffs = [closes[j] - vw[j] for j in range(i - 19, i + 1)]
        dev[i] = statistics.pstdev(diffs)
    events = []
    for i in range(20, len(five)):
        if dev[i] is None or dev[i - 1] is None or rsi[i] is None:
            continue
        lo_b, lo_p = vw[i] - 1.5 * dev[i], vw[i - 1] - 1.5 * dev[i - 1]
        up_b, up_p = vw[i] + 1.5 * dev[i], vw[i - 1] + 1.5 * dev[i - 1]
        if closes[i - 1] <= lo_p and closes[i] > lo_b and rsi[i] < 40:
            events.append((i, "BUY"))
        elif closes[i - 1] >= up_p and closes[i] < up_b and rsi[i] > 60:
            events.append((i, "SELL"))
    i = len(five) - 1
    return {"five": five, "vwap": vw[i], "upper": vw[i] + 1.5 * (dev[i] or 0), "lower": vw[i] - 1.5 * (dev[i] or 0), "rsi": rsi[i], "close": closes[i],
            "date": str(five[i]["day"]), "events": [{"date": five[k]["dt"].strftime("%d %b %H:%M"), "text": f"{sg} - close {closes[k]:,.2f}, RSI {rsi[k]:.0f}"} for k, sg in events][-12:],
            "last": ({"signal": events[-1][1], "when": five[events[-1][0]]["dt"].strftime("%d %b %H:%M")} if events else None)}

def _run_raw(key, symbol):
    symbol = symbol.upper()
    if key == "ut-bot":
        return ut_bot.ut_bot_scan(symbol)
    if key == "donchian":
        return donchian.donchian_scan(symbol)
    if key == "trade-predictor":
        return trade_predictor.trade_predictor_scan(symbol)
    if key == "quantum-matrix":
        return quantum_matrix.quantum_matrix_scan(symbol)
    if key == "heikin-ashi-channel":
        return heikin_ashi.dancing_channel_scan(symbol)
    if key == "ha-dancing-trend":
        return ha_dancing_trend.ha_dancing_trend_scan(symbol)
    if key == "oh-ol":
        return indicators.oh_ol_setup(symbol, {})
    if key == "supertrend-mtf":
        return _raw_supertrend_mtf(symbol)
    if key == "candle-oh-ol":
        return _raw_candle_oh_ol(symbol)
    if key == "volume-spurt":
        return _raw_volume_spurt(symbol)
    if key == "orb-15m":
        return _raw_orb(symbol)
    if key == "vwap-rsi":
        return _raw_vwap_rsi(symbol)
    if key in rp.RAJAN_PAVAN_KEYS:
        return rp.RAJAN_PAVAN_KEYS[key](symbol)
    raise HTTPException(400, f"Unknown strategy '{key}'")


def _recent_event(bars, n=3, fields=("signal",)):
    """Latest non-empty signal within the last n bars (date, signal)."""
    for r in reversed(bars[-n:]):
        sg = r.get("signal")
        if sg and sg not in ("NONE", "RANGE", "FLAT"):
            return {"date": r.get("date"), "signal": sg}
    return None


def summarize(key, symbol, raw):
    meta = META[key]
    out = {"key": key, "symbol": symbol, "name": meta["name"], "group": meta["group"],
           "signal": "NONE", "bias": "neutral", "headline": "", "date": None, "close": None,
           "details": [], "events": [], "lines": [], "bars": []}
    bars = raw.get("bars") or []
    has_date = bool(bars) and "date" in bars[-1]

    if key in rp.RAJAN_PAVAN_KEYS:
        cur = raw.get("current") or {}
        out["date"], out["close"] = cur.get("date"), cur.get("close")
        out["lines"] = meta["lines"]
        out["details"] = _flat({k: v for k, v in cur.items() if k not in ("date", "signal")})
        ev = _recent_event(bars)
        sig = cur.get("signal") or "NONE"
        out["signal"] = sig if sig not in ("NONE",) else (ev["signal"] if ev else "NONE")
        out["bias"] = _bias(out["signal"])
        out["headline"] = (f"{out['signal']} signal today" if cur.get("signal") not in (None, "NONE")
                           else f"Last {ev['signal']} on {ev['date']}" if ev else "No active signal")
        if key == "vix-range":
            out["headline"] = f"Expected range {cur.get('lowerRange', 0):,.2f} – {cur.get('upperRange', 0):,.2f} (VIX {cur.get('vix')})"
        out["events"] = [{"date": e["date"], "text": e["signal"] + (f" · {e['note']}" if e.get("note") else "")} for e in raw.get("events", [])][-12:]

    elif key == "ut-bot":
        c = raw.get("current") or {}
        out.update(date=c.get("date"), close=c.get("close"))
        out["signal"] = c.get("lastSignal") or "NONE"
        out["bias"] = _bias(c.get("position"))
        out["headline"] = f"{c.get('position')} · {c.get('lastSignal')} {c.get('barsSinceSignal')} bar(s) ago · trail {c.get('trailingStop', 0):,.2f}"
        out["details"] = _flat({k: v for k, v in c.items() if k not in ("date",)})
        out["events"] = [{"date": r["date"], "text": r["signal"]} for r in bars if r.get("signal")][-12:]

    elif key == "donchian":
        c = raw.get("current") or {}
        out.update(date=c.get("date"), close=c.get("close"))
        out["signal"] = c.get("lastSignal") or "NONE"
        fresh = (c.get("barsSinceSignal") or 99) <= 3
        out["bias"] = _bias(out["signal"]) if fresh else "neutral"
        out["headline"] = f"Last {c.get('lastSignal')} {c.get('barsSinceSignal')} bar(s) ago · channel {c.get('lower', 0):,.2f} – {c.get('upper', 0):,.2f}"
        out["details"] = _flat({k: v for k, v in c.items() if k != "date"})
        out["events"] = [{"date": r["date"], "text": r["signal"]} for r in bars if r.get("signal")][-12:]

    elif key == "trade-predictor":
        a = raw.get("active") or {}
        out.update(date=raw.get("lastDate"), close=raw.get("lastClose"))
        out["signal"] = (a.get("side") or "none").upper()
        out["bias"] = "bull" if a.get("side") == "long" else "bear" if a.get("side") == "short" else "neutral"
        out["headline"] = (f"Active {a['side']} from {a['entryPrice']:,.2f} · SL {a['sl']:,.2f} · TP {a['tp']:,.2f}" if a else "No active trade")
        out["details"] = _flat(a) + [{"label": "EMA trend filter", "value": "on" if raw.get("useTrendFilter") else "off"}]
        out["events"] = [{"date": e["date"], "text": f"{e['side']} {e['event']} @ {e['price']:,.2f}"} for e in raw.get("events", [])][-12:]

    elif key == "quantum-matrix":
        u = raw.get("utSignal") or {}
        kl = raw.get("keyLevels") or {}
        out.update(date=raw.get("lastDate"), close=raw.get("lastClose"))
        out["signal"] = u.get("lastSignal") or "NONE"
        out["bias"] = _bias(u.get("position"))
        out["headline"] = f"UT {u.get('position')} · support {kl.get('support', 0):,.2f} · resistance {kl.get('resistance', 0):,.2f}"
        out["details"] = _flat(kl) + _flat(raw.get("emaRibbon")) + _flat(u)
        out["levels"] = {"support": kl.get("support"), "resistance": kl.get("resistance")}

    elif key in ("heikin-ashi-channel", "ha-dancing-trend"):
        ba, sa = raw.get("buyActive"), raw.get("sellActive")
        act = ba or sa
        out.update(date=(raw.get("lastTime") or "")[:10], close=raw.get("lastPrice"))
        if act:
            side = "BUY" if ba else "SELL"
            out["signal"], out["bias"] = side, _bias(side)
            out["headline"] = f"Active {side.lower()} since {act.get('entryTime')} @ {act.get('entryPrice', 0):,.2f}"
            out["details"] = _flat(act)
        else:
            evs = raw.get("events") or []
            out["headline"] = f"No active trade · last event {evs[-1].get('event')} {evs[-1].get('time')}" if evs else "No active trade"
        out["events"] = [{"date": e.get("time"), "text": f"{e.get('type')} {e.get('event')} @ {e.get('price', 0):,.2f}"} for e in (raw.get("events") or [])][-12:]

    elif key == "supertrend-mtf":
        c = raw["current"]
        out.update(date=c["date"], close=c["close"])
        fresh = c["barsSince"] is not None and c["barsSince"] <= 3
        out["signal"] = c["lastSignal"] if fresh else ("UPTREND" if c["trend"] == "UP" else "DOWNTREND")
        out["bias"] = "bull" if c["trend"] == "UP" else "bear"
        out["headline"] = (f"{c['trend']}TREND" + (f" - weekly trend {'agrees' if c['aligned'] else 'disagrees'}" if c["aligned"] is not None else "")
                           + (f" - last {c['lastSignal']} {c['barsSince']} bar(s) ago" if c["lastSignal"] else ""))
        out["details"] = _flat({k: v for k, v in c.items() if k not in ("date", "aligned")})
        out["events"] = [{"date": r["date"], "text": r["signal"]} for r in raw["bars"] if r.get("signal")][-12:]

    elif key == "candle-oh-ol":
        c = raw["current"]
        out.update(date=c["date"], close=c["close"])
        out["signal"] = c["signal"] or "NONE"
        out["bias"] = _bias(c["signal"])
        out["headline"] = ("Open = Low today - buyers in control" if c["openEqLow"] else "Open = High today - sellers in control" if c["openEqHigh"]
                           else f"Neither today ({c['sessionsWithSignal']} of the last 20 sessions had one)")
        out["details"] = _flat({k: v for k, v in c.items() if k not in ("date", "signal", "openEqLow", "openEqHigh")})
        out["events"] = [{"date": r["date"], "text": "Open = Low" if r["signal"] == "BUY" else "Open = High"} for r in raw["bars"] if r.get("signal")][-12:]

    elif key == "volume-spurt":
        c = raw["current"]
        out.update(date=c["date"], close=c["close"])
        out["signal"] = c["signal"] or "NONE"
        out["bias"] = _bias(c["signal"])
        out["headline"] = (f"Volume spurt today: {c['ratio']:.1f}x the 20-day average" if c["signal"] else f"Volume {c['ratio']:.1f}x the 20-day average - no spurt" if c["ratio"] else "No volume data")
        out["details"] = _flat({k: v for k, v in c.items() if k not in ("date", "signal")})
        out["events"] = [{"date": r["date"], "text": f"Spurt {r['ratio']:.1f}x"} for r in raw["bars"] if r.get("signal")][-12:]

    elif key == "orb-15m":
        out.update(date=raw["date"], close=raw["close"])
        out["signal"] = raw["state"] if raw["state"] != "INSIDE" else "NONE"
        out["bias"] = "bull" if raw["state"] == "ORB BUY" else "bear" if raw["state"] == "ORB SELL" else "neutral"
        out["headline"] = f"Opening range {raw['orbLow']:,.2f} - {raw['orbHigh']:,.2f}: price is {'above (ORB BUY)' if raw['state']=='ORB BUY' else 'below (ORB SELL)' if raw['state']=='ORB SELL' else 'inside'}"
        out["details"] = _flat({"orbHigh": raw["orbHigh"], "orbLow": raw["orbLow"], "range": raw["range"], "longTarget1": raw["long"]["target1"], "longTarget2": raw["long"]["target2"],
                                "shortTarget1": raw["short"]["target1"], "shortTarget2": raw["short"]["target2"]})
        out["events"] = raw["events"][-12:]
        out["levels"] = {"date": raw["date"], "orbHigh": raw["orbHigh"], "orbLow": raw["orbLow"], "t1l": raw["long"]["target1"], "t2l": raw["long"]["target2"],
                         "t1s": raw["short"]["target1"], "t2s": raw["short"]["target2"]}

    elif key == "vwap-rsi":
        out.update(date=raw["date"], close=raw["close"])
        l = raw["last"]
        out["signal"] = l["signal"] if l else "NONE"
        out["bias"] = _bias(out["signal"])
        out["headline"] = (f"Last {l['signal']} at {l['when']}" if l else "No mean-reversion signal in the last 5 sessions") + f" - RSI {raw['rsi']:.0f}, VWAP {raw['vwap']:,.2f}"
        out["details"] = _flat({"vwap": raw["vwap"], "upperBand": raw["upper"], "lowerBand": raw["lower"], "rsi": raw["rsi"]})
        out["events"] = raw["events"]

    elif key == "oh-ol":
        out.update(close=(raw.get("index") or {}).get("last"))
        out["headline"] = raw.get("indexSignal", "")
        out["signal"] = "CALL" if raw.get("doCall") else "PUT" if raw.get("doPut") else "NONE"
        out["bias"] = "bull" if raw.get("doCall") else "bear" if raw.get("doPut") else "neutral"
        out["details"] = _flat(raw.get("index")) + _flat({"vix": raw.get("vix"), "vixTier": raw.get("vixTier")}) + _flat(raw.get("volumeSignal"))

    if key not in rp.RAJAN_PAVAN_KEYS and has_date:
        out["lines"] = meta["lines"]
    # compact bars for the chart overlay (daily-dated strategies only)
    if has_date:
        keep = [l["k"] for l in out["lines"]] + ["signal"]
        out["bars"] = [{"date": b["date"], **{k: b.get(k) for k in keep if b.get(k) is not None}} for b in bars[-400:]]
    return out


def run(key, symbol):
    if key not in META:
        raise HTTPException(400, f"Unknown strategy '{key}'")
    symbol = symbol.upper()
    if META[key]["indexOnly"] and symbol not in INDEX_SET:
        raise HTTPException(400, f"{META[key]['name']} works on indices only")
    if not bar_source.supports(symbol) and symbol not in ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"):
        raise HTTPException(400, f"{symbol} is not in the supported universe")
    ck = f"{key}|{symbol}"
    hit = _cache.get(ck)
    if hit and time.time() - hit[0] < 45:
        return hit[1]
    try:
        raw = _run_raw(key, symbol)
        res = summarize(key, symbol, raw)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, str(exc))
    res["asOf"] = datetime.now().isoformat(timespec="seconds")
    _cache[ck] = (time.time(), res)
    return res



# ----------------------------- option-contract scans (Strategy 1 / 3, Open=Low / Open=High, volume + OI spike) -----------------------------
OPT_SCANS = [
    ("opt-strat1", "Strategy 1: Low Range Setup", "Option scans", "Option contracts with a day low of Rs 5.80-8.45 and a previous close of Rs 38-48."),
    ("opt-premium", "Strategy 3: Premium / 8 and / 6.5", "Option scans", "Previous-close premium Rs 300-349 with a day low of Rs 52-58, or a low inside the previous close / 8 to / 6.5 formula band (AlphaScan)."),
    ("opt-ol", "Bullish Open = Low (contracts)", "Option scans", "Option contracts that opened exactly at their day low - buyers in control."),
    ("opt-oh", "Bearish Open = High (contracts)", "Option scans", "Option contracts that opened exactly at their day high - sellers in control."),
    ("opt-spike", "Volume Spurt and OI Spike (contracts)", "Option scans", "Contracts trading over 2x the typical strike volume on a rising candle while open interest builds."),
]
OPT_META = {k: {"key": k, "name": n, "group": g, "desc": d, "kind": "optscan", "chart": False, "indexOnly": False, "lines": []} for k, n, g, d in OPT_SCANS}
SCAN_INDICES = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50", "SENSEX"]
TICK = 0.05


def _opt_rule(key, leg, prev_close):
    """-> (matched, tag) for one contract leg."""
    ltp, op, hi, lo, vol = leg["ltp"], leg["open"], leg["high"], leg["low"], leg["vol"]
    if ltp <= 0 or vol <= 0:                                  # untraded contracts are excluded
        return False, ""
    if key == "opt-strat1":
        ok = 5.80 <= lo <= 8.45 and 38.0 <= prev_close <= 48.0
        return ok, "Low Rs 5.80-8.45 and prev close Rs 38-48" if ok else ""
    if key == "opt-premium":
        f1, f2 = prev_close / 8.0, prev_close / 6.5
        prem = 300.0 <= prev_close <= 349.0
        fixed = 52.0 <= lo <= 58.0
        formula = min(f1, f2) <= lo <= max(f1, f2)
        ok = prem and (fixed or formula)
        return ok, (f"Prem {prev_close:,.2f}; low {lo:,.2f} " + ("in Rs 52-58" if fixed else "") + (" and " if fixed and formula else "") + (f"in /8-/6.5 band {min(f1, f2):,.2f}-{max(f1, f2):,.2f}" if formula else "")) if ok else ""
    if key == "opt-ol":
        ok = hi > lo and abs(op - lo) <= TICK
        return ok, "Open = Low" if ok else ""
    if key == "opt-oh":
        ok = hi > lo and abs(op - hi) <= TICK
        return ok, "Open = High" if ok else ""
    return False, ""


@router.get("/option-scan")
def option_scan(key: str, scope: str = "indices", offset: int = 0, only: str = ""):
    if key not in OPT_META:
        raise HTTPException(400, f"Unknown option scan '{key}'")
    market_api.ensure_universe()
    syms = list(SCAN_INDICES)
    nxt, total = None, None
    if scope == "core":
        syms += market_api.CORE[:30]
    elif scope == "all":                              # every F&O stock, in batches the client stitches together
        full = list(SCAN_INDICES) + [x for x, _, _ in market_api.STOCKS]
        total = len(full)
        syms = full[offset:offset + 30]
        nxt = offset + 30 if offset + 30 < total else None
    if only.strip():                                   # retry a specific set of underlyings
        syms = [x.strip().upper() for x in only.split(",") if x.strip()][:40]
        nxt = None
    deadline = time.time() + 22
    failed = []

    @market_api.bg
    def one(sym):
        out = []
        if time.time() > deadline:
            failed.append(sym)
            return out
        try:
            first = market_api.chain(symbol=sym, expiry="")
        except Exception:
            failed.append(sym)
            return out
        expiries = [first["expiry"]] + [e for e in first["expiries"] if e != first["expiry"]][: (2 if sym in SCAN_INDICES else 0)]
        for ex in expiries:
            try:
                c = first if ex == first["expiry"] else market_api.chain(symbol=sym, expiry=ex)
            except Exception:
                continue
            legs = [(side.upper(), r["strike"], r[side]) for r in c["rows"] for side in ("ce", "pe") if r.get(side)]
            vols = sorted(l["vol"] for _, _, l in legs if l["vol"] > 0)
            med = vols[len(vols) // 2] if vols else 0
            for side, strike, leg in legs:
                if key == "opt-spike":
                    ok = med > 0 and leg["vol"] > 2.0 * med and leg["ltp"] > leg["open"] > 0 and leg["oiChg"] > 0
                    tag = f"Volume {leg['vol'] / med:.1f}x the typical strike, OI +{leg['oiChg']:,.0f}" if ok else ""
                else:
                    ok, tag = _opt_rule(key, leg, leg["prev"])
                if ok:
                    out.append({"symbol": sym, "expiry": c["expiry"], "strike": strike, "side": side, "key": leg["key"], "ltp": leg["ltp"],
                                "open": leg["open"], "high": leg["high"], "low": leg["low"], "prev": leg["prev"], "oi": leg["oi"],
                                "oiChg": leg["oiChg"], "vol": leg["vol"], "tag": tag})
        return out

    ck = f"optscan|{key}|{scope}|{offset}|{only}"
    hit = _cache.get(ck)
    if hit and time.time() - hit[0] < (30 if market_api.market_open() else 300):
        return hit[1]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        parts = list(pool.map(one, syms))
    rows = sorted([r for part in parts for r in part], key=lambda r: -r["vol"])[:6000]
    res = {"key": key, "name": OPT_META[key]["name"], "scope": scope, "scanned": len(syms), "rows": rows, "next": nxt, "total": total or len(syms),
           "marketOpen": market_api.market_open(), "asOf": datetime.now().isoformat(timespec="seconds")}
    res["failed"] = sorted(set(failed))
    if not failed:                                     # only complete scans are cached
        _cache[ck] = (time.time(), res)
    return res

@router.get("/strategies")
def strategies():
    groups = []
    for k, m in META.items():
        if m["group"] not in groups:
            groups.append(m["group"])
    groups = groups + ["Option scans"]
    return {"strategies": list(META.values()) + list(OPT_META.values()), "groups": groups}


@router.get("/strategy")
def strategy(key: str, symbol: str = "NIFTY"):
    return run(key, symbol)


@router.get("/strategy-scan")
def strategy_scan(key: str, symbols: str = ""):
    if key not in META:
        raise HTTPException(400, f"Unknown strategy '{key}'")
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    market_api.ensure_universe()
    if symbols.strip().upper() == "ALL":
        syms = [s for s, _, _ in market_api.STOCKS]
    elif not syms:
        syms = ([s for s, _ in market_api.INDICES if s != "INDIAVIX"] if META[key]["indexOnly"] else list(market_api.CORE))
    syms = syms[:260]
    deadline = time.time() + 24

    @market_api.bg
    def one(sym):
        if time.time() > deadline:
            return {"symbol": sym, "error": "skipped (time budget)", "skipped": True}
        try:
            r = run(key, sym)
            return {"symbol": sym, "signal": r["signal"], "bias": r["bias"], "headline": r["headline"],
                    "close": r["close"], "date": r["date"]}
        except Exception as e:
            return {"symbol": sym, "error": str(getattr(e, "detail", e))}

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(one, syms))
    order = {"bull": 0, "bear": 1, "neutral": 2}
    rows.sort(key=lambda r: (1 if r.get("error") else 0, order.get(r.get("bias"), 3), r["symbol"]))
    skipped = sum(1 for r in rows if r.get("skipped"))
    rows = [r for r in rows if not r.get("skipped")]
    return {"key": key, "name": META[key]["name"], "rows": rows, "count": len(rows), "skipped": skipped,
            "asOf": datetime.now().isoformat(timespec="seconds")}

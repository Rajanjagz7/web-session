"""Extra strategies added to the merged app:

  16. Trend Target Ribbon [BOSWaves]  - ALMA trend, structure stop, 1R..4R targets
  17. Dual-Phase Reversal (DGT)       - Momentum Exhaustion (9) + Terminal Exhaustion (13)

Both run on the same daily OHLCV series as every other indicator (fetch_index_history)
and return the shape the Indicators screen already understands:
{symbol, columns, current{date, close, signal, ...}, bars[...], events[...]}.
"""

import math

from ut_bot import _rma, _true_range, fetch_index_history

ALLOWED_SYMBOLS = ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX")


def _clamp(value, lo, hi, default):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, v))


def _clampi(value, lo, hi, default):
    return int(_clamp(value, lo, hi, default))


def _validate_symbol(symbol):
    symbol = (symbol or "").upper()
    import bar_source
    if symbol not in ALLOWED_SYMBOLS and not bar_source.supports(symbol):
        raise ValueError(f"{symbol or 'symbol'} is not in this app's universe")
    return symbol


def _events(rows, n=40):
    out = [{"date": r["date"], "signal": r["signal"], "note": r.get("phase")}
           for r in rows if r.get("signal") and r["signal"] != "NONE"]
    return out[-n:]


# ───────────────────────── Trend Target Ribbon [BOSWaves] ─────────────────────────

def _alma(values, length, offset, sigma):
    """Pine ta.alma: Gaussian-weighted MA over the window (oldest -> newest)."""
    out = [None] * len(values)
    m = offset * (length - 1)
    sd = length / sigma
    w = [math.exp(-((i - m) ** 2) / (2 * sd * sd)) for i in range(length)]
    norm = sum(w)
    for i in range(length - 1, len(values)):
        win = values[i - length + 1:i + 1]
        out[i] = sum(win[k] * w[k] for k in range(length)) / norm
    return out


def _stdev(values, length):
    """Pine ta.stdev (population)."""
    out = [None] * len(values)
    for i in range(length - 1, len(values)):
        win = values[i - length + 1:i + 1]
        mu = sum(win) / length
        out[i] = math.sqrt(sum((x - mu) ** 2 for x in win) / length)
    return out


def trend_target_ribbon_scan(
    symbol, alma_length=34, alma_offset=0.85, alma_sigma=6.0, dev_length=34, dev_mult=0.65,
    slope_length=3, slope_min=0.08, atr_length=14, stop_lookback=12, min_stop_atr=0.75,
    max_stop_atr=3.0, target_count=4, lookback_days=250,
):
    symbol = _validate_symbol(symbol)
    alma_length = _clampi(alma_length, 5, 200, 34)
    alma_offset = _clamp(alma_offset, 0.0, 1.0, 0.85)
    alma_sigma = _clamp(alma_sigma, 1.0, 15.0, 6.0)
    dev_length = _clampi(dev_length, 5, 200, 34)
    dev_mult = _clamp(dev_mult, 0.1, 3.0, 0.65)
    slope_length = _clampi(slope_length, 1, 10, 3)
    slope_min = _clamp(slope_min, 0.0, 1.0, 0.08)
    atr_length = _clampi(atr_length, 5, 100, 14)
    stop_lookback = _clampi(stop_lookback, 3, 50, 12)
    min_stop_atr = _clamp(min_stop_atr, 0.25, 3.0, 0.75)
    max_stop_atr = _clamp(max_stop_atr, 1.0, 8.0, 3.0)
    target_count = _clampi(target_count, 2, 4, 4)
    lookback_days = _clampi(lookback_days, 30, 500, 250)

    bars = fetch_index_history(symbol, lookback_days=lookback_days + alma_length + dev_length + 40)
    if len(bars) <= max(alma_length, dev_length, atr_length) + slope_length + 2:
        raise RuntimeError(f"Not enough historical sessions returned ({len(bars)}) for Trend Target Ribbon")

    closes = [b["close"] for b in bars]
    n = len(bars)
    alma = _alma(closes, alma_length, alma_offset, alma_sigma)
    dev = _stdev(closes, dev_length)
    atr = _rma(_true_range(bars), atr_length)

    trend = 0
    pos = None
    rows = []
    for i in range(n):
        a, d, r = alma[i], dev[i], atr[i]
        sig = "NONE"
        slope = conviction = None
        edge = a
        if a is not None and d is not None and r is not None and i >= slope_length and alma[i - slope_length] is not None:
            slope = (a - alma[i - slope_length]) / r if r > 0 else 0.0
            bull_setup = slope > slope_min and closes[i] > a + d * dev_mult
            bear_setup = slope < -slope_min and closes[i] < a - d * dev_mult
            flip = 0
            if trend != 1 and bull_setup:
                trend, flip = 1, 1
            elif trend != -1 and bear_setup:
                trend, flip = -1, -1
            dist = abs(closes[i] - a) / r if r > 0 else 0.0
            conviction = max(0.0, min(1.0, abs(slope) * 2.0 + dist * 0.35))
            edge = a - d * 0.55 if trend == 1 else a + d * 0.55 if trend == -1 else a

            # stop / target tracking for the open position (bars after entry only)
            if pos and pos["status"] == "ACTIVE" and i > pos["entryIdx"]:
                if (pos["dir"] == 1 and bars[i]["low"] <= pos["stop"]) or (pos["dir"] == -1 and bars[i]["high"] >= pos["stop"]):
                    pos["status"] = "STOPPED"
                else:
                    for k, t in enumerate(pos["targets"]):
                        if (pos["dir"] == 1 and bars[i]["high"] >= t) or (pos["dir"] == -1 and bars[i]["low"] <= t):
                            pos["hit"][k] = True
            if flip:
                if pos and pos["status"] == "ACTIVE":
                    pos["status"] = "REVERSED"
                entry = closes[i]
                lo_i = max(0, i - stop_lookback)
                if i - lo_i >= 1:
                    struct = min(b["low"] for b in bars[lo_i:i]) if flip == 1 else max(b["high"] for b in bars[lo_i:i])
                    raw_risk = entry - struct if flip == 1 else struct - entry
                else:
                    raw_risk = r * min_stop_atr
                risk = min(max(raw_risk, r * min_stop_atr), r * max_stop_atr)
                pos = {
                    "dir": flip, "entryIdx": i, "entry": entry, "risk": risk, "status": "ACTIVE",
                    "stop": entry - flip * risk,
                    "targets": [entry + flip * risk * (k + 1) for k in range(target_count)],
                    "hit": [False] * target_count, "date": bars[i]["date"],
                }
                sig = "BUY" if flip == 1 else "SELL"

        live = pos is not None and pos["status"] == "ACTIVE"
        rows.append({
            "date": bars[i]["date"], "open": bars[i]["open"], "high": bars[i]["high"],
            "low": bars[i]["low"], "close": closes[i],
            "alma": a, "ribbonEdge": edge, "trend": {1: "BULL", -1: "BEAR", 0: "NONE"}[trend],
            "slope": slope, "conviction": conviction,
            "activeStop": pos["stop"] if live else None, "signal": sig,
        })

    rows = rows[-lookback_days:]
    last = rows[-1]
    cur = {"date": last["date"], "close": last["close"], "signal": last["signal"],
           "trend": last["trend"], "alma": last["alma"], "conviction": last["conviction"]}
    if pos:
        cur.update({
            "positionSide": "LONG" if pos["dir"] == 1 else "SHORT", "positionStatus": pos["status"],
            "entry": round(pos["entry"], 2), "stopLoss": round(pos["stop"], 2),
            "riskPerUnit": round(pos["risk"], 2), "entryDate": pos["date"],
        })
        for k, t in enumerate(pos["targets"]):
            cur[f"target{k + 1}"] = round(t, 2)
            cur[f"target{k + 1}Hit"] = pos["hit"][k]
    return {
        "symbol": symbol,
        "columns": [
            {"key": "alma", "label": "ALMA"}, {"key": "ribbonEdge", "label": "Ribbon edge"},
            {"key": "trend", "label": "Trend"}, {"key": "activeStop", "label": "Stop"},
        ],
        "current": cur, "bars": rows, "events": _events(rows),
    }


# ───────────────────────── Dual-Phase Reversal (DGT) ─────────────────────────

def _range_pivot(o, h, l, c):
    x = h + 2 * l + c if c < o else 2 * h + l + c if c > o else h + l + 2 * c
    return {"pivot": x / 4, "r1": x / 2 - l, "s1": x / 2 - h}


def dual_phase_reversal_scan(symbol, lookback_days=250):
    """Momentum Exhaustion (9 closes vs close[4]) then Terminal Exhaustion (13 count), with the
    S/R, invalidation and range-pivot levels of the DGT script. On daily bars the range pivot uses
    the previous completed calendar month (the script's 'Auto' range for a 1D chart).
    A completed buy-side sequence (price kept closing lower) is exhaustion of the down move = BUY;
    a completed sell-side sequence = SELL. Terminal (13) is the stronger of the two phases."""
    symbol = _validate_symbol(symbol)
    lookback_days = _clampi(lookback_days, 30, 500, 250)
    bars = fetch_index_history(symbol, lookback_days=lookback_days + 60)
    n = len(bars)
    if n < 30:
        raise RuntimeError(f"Not enough historical sessions returned ({n}) for Dual-Phase Reversal")

    C = [b["close"] for b in bars]
    H = [b["high"] for b in bars]
    L = [b["low"] for b in bars]

    buy_cnt = sell_cnt = 0
    b_res = s_sup = 0.0
    b_stop = s_stop = 0.0
    b_lowest = b_high = s_highest = s_low = 0.0
    te_b_cnt = te_s_cnt = 0
    te_b_on = te_s_on = False
    te_b_ref8 = te_s_ref8 = 0.0
    te_b_hi = te_b_lo = te_b_hh = te_b_ll = 0.0
    te_s_hi = te_s_lo = te_s_hh = te_s_ll = 0.0
    te_b_stop = te_s_stop = 0.0
    te_b_tgt = te_s_tgt = 0.0

    rows = []
    for i in range(n):
        sig, phase, qual = "NONE", None, False
        if i >= 5:
            b_cond, s_cond = C[i] < C[i - 4], C[i] > C[i - 4]
            b_shift = b_cond and C[i - 1] > C[i - 5]
            s_shift = s_cond and C[i - 1] < C[i - 5]
            if b_cond:
                buy_cnt = (1 if b_shift else 0) if buy_cnt in (0, 9) else buy_cnt + 1
                sell_cnt = 0
            elif s_cond:
                sell_cnt = (1 if s_shift else 0) if sell_cnt in (0, 9) else sell_cnt + 1
                buy_cnt = 0
            else:
                buy_cnt = sell_cnt = 0

            b_qual = (L[i] <= L[i - 3] and L[i] <= L[i - 2]) or (L[i - 1] <= L[i - 3] and L[i - 1] <= L[i - 2])
            s_qual = (H[i] >= H[i - 3] and H[i] >= H[i - 2]) or (H[i - 1] >= H[i - 3] and H[i - 1] >= H[i - 2])
            hi9 = max(H[max(0, i - 8):i + 1])
            lo9 = min(L[max(0, i - 8):i + 1])

            # momentum exhaustion: support/resistance + invalidation (buy side)
            b_res = hi9 if buy_cnt == 9 else (0.0 if C[i] > b_res else b_res)
            if buy_cnt == 1:
                b_lowest = L[i]
            if buy_cnt > 0:
                b_lowest = min(L[i], b_lowest)
                if L[i] == b_lowest:
                    b_high = H[i]
            b_stop = (2 * b_lowest - b_high) if buy_cnt == 9 else (0.0 if C[i] < b_stop else b_stop)

            # momentum exhaustion (sell side)
            s_sup = lo9 if sell_cnt == 9 else (0.0 if C[i] < s_sup else s_sup)
            if sell_cnt == 1:
                s_highest = H[i]
            if sell_cnt > 0:
                s_highest = max(H[i], s_highest)
                if H[i] == s_highest:
                    s_low = L[i]
            s_stop = (2 * s_highest - s_low) if sell_cnt == 9 else (0.0 if C[i] > s_stop else s_stop)

            # terminal exhaustion (13-count), buy side
            prev_b = te_b_cnt
            b_te = C[i] <= L[i - 2]
            b_fail = b_te and L[i] >= te_b_ref8
            if buy_cnt == 9 and te_b_cnt == 0:
                te_b_on = True
            elif sell_cnt == 9 or te_b_cnt == 13 or C[i] > b_res:
                te_b_on = False
            if te_b_on:
                te_b_cnt = (1 if b_te else 0) if buy_cnt == 9 else (te_b_cnt + 1 if b_te else te_b_cnt)
            else:
                te_b_cnt = 0
            if te_b_cnt == 13 and b_fail:
                te_b_cnt -= 1
            if te_b_cnt == 8 and te_b_cnt != prev_b:
                te_b_ref8 = C[i]
            if te_b_cnt == 1:
                te_b_ll, te_b_hh = L[i], H[i]
            if te_b_on:
                te_b_hh = max(H[i], te_b_hh)
                te_b_ll = min(L[i], te_b_ll)
                if H[i] == te_b_hh:
                    te_b_lo = L[i]
                if L[i] == te_b_ll:
                    te_b_hi = H[i]
            te_b_tgt = (2 * te_b_hh - te_b_lo) if te_b_cnt == 13 else (
                0.0 if (C[i] > te_b_tgt or (te_b_stop == 0 and te_s_cnt == 13)) else te_b_tgt)
            te_b_stop = (2 * te_b_ll - te_b_hi) if te_b_cnt == 13 else (
                0.0 if (C[i] < te_b_stop or (te_b_tgt == 0 and te_s_cnt == 13)) else te_b_stop)

            # terminal exhaustion, sell side (mirror of the buy side)
            prev_s = te_s_cnt
            s_te = C[i] >= H[i - 2]
            s_fail = s_te and H[i] <= te_s_ref8
            if sell_cnt == 9 and te_s_cnt == 0:
                te_s_on = True
            elif buy_cnt == 9 or te_s_cnt == 13 or C[i] < s_sup:
                te_s_on = False
            if te_s_on:
                te_s_cnt = (1 if s_te else 0) if sell_cnt == 9 else (te_s_cnt + 1 if s_te else te_s_cnt)
            else:
                te_s_cnt = 0
            if te_s_cnt == 13 and s_fail:
                te_s_cnt -= 1
            if te_s_cnt == 8 and te_s_cnt != prev_s:
                te_s_ref8 = C[i]
            if te_s_cnt == 1:
                te_s_hh, te_s_ll = H[i], L[i]
            if te_s_on:
                te_s_hh = max(H[i], te_s_hh)
                te_s_ll = min(L[i], te_s_ll)
                if L[i] == te_s_ll:
                    te_s_hi = H[i]
                if H[i] == te_s_hh:
                    te_s_lo = L[i]
            te_s_tgt = (2 * te_s_ll - te_s_hi) if te_s_cnt == 13 else (
                0.0 if (C[i] < te_s_tgt or (te_s_stop == 0 and te_b_cnt == 13)) else te_s_tgt)
            te_s_stop = (2 * te_s_hh - te_s_lo) if te_s_cnt == 13 else (
                0.0 if (C[i] > te_s_stop or (te_s_tgt == 0 and te_b_cnt == 13)) else te_s_stop)

            if te_b_cnt == 13 and prev_b != 13:
                sig, phase = "BUY", "TE"
            elif te_s_cnt == 13 and prev_s != 13:
                sig, phase = "SELL", "TE"
            elif buy_cnt == 9:
                sig, phase, qual = "BUY", "ME", b_qual
            elif sell_cnt == 9:
                sig, phase, qual = "SELL", "ME", s_qual

        rows.append({
            "date": bars[i]["date"], "open": bars[i]["open"], "high": H[i], "low": L[i], "close": C[i],
            "buyCount": buy_cnt, "sellCount": sell_cnt, "teBuyCount": te_b_cnt, "teSellCount": te_s_cnt,
            "meResistance": b_res or None, "meSupport": s_sup or None,
            "buyInvalidation": b_stop or None, "sellInvalidation": s_stop or None,
            "phase": phase, "qualified": qual, "signal": sig,
        })

    piv = {}
    by_month = {}
    for b in bars:
        by_month.setdefault(b["date"][:7], []).append(b)
    months = sorted(by_month)
    if len(months) >= 2:
        pm = by_month[months[-2]]
        p = _range_pivot(pm[0]["open"], max(x["high"] for x in pm), min(x["low"] for x in pm), pm[-1]["close"])
        piv = {"rangePivot": round(p["pivot"], 2), "rangeR1": round(p["r1"], 2),
               "rangeS1": round(p["s1"], 2), "pivotPeriod": months[-2]}

    rows = rows[-lookback_days:]
    last = rows[-1]
    stage = ("Terminal buy exhaustion complete" if last["teBuyCount"] == 13 else
             "Terminal sell exhaustion complete" if last["teSellCount"] == 13 else
             f"Buy sequence {last['buyCount']}/9" if last["buyCount"] else
             f"Sell sequence {last['sellCount']}/9" if last["sellCount"] else "No sequence")
    cur = {"date": last["date"], "close": last["close"], "signal": last["signal"], "phase": last["phase"],
           "stage": stage, "buyCount": last["buyCount"], "sellCount": last["sellCount"],
           "teBuyCount": last["teBuyCount"], "teSellCount": last["teSellCount"],
           "meResistance": last["meResistance"], "meSupport": last["meSupport"],
           "buyInvalidation": last["buyInvalidation"], "sellInvalidation": last["sellInvalidation"],
           "buyTarget": te_b_tgt or None, "sellTarget": te_s_tgt or None, **piv}
    return {
        "symbol": symbol,
        "columns": [
            {"key": "buyCount", "label": "Buy count"}, {"key": "sellCount", "label": "Sell count"},
            {"key": "teBuyCount", "label": "TE buy"}, {"key": "teSellCount", "label": "TE sell"},
            {"key": "meResistance", "label": "ME resistance"}, {"key": "meSupport", "label": "ME support"},
        ],
        "current": cur, "bars": rows, "events": _events(rows),
    }


# ───────────────────────── RJ Best ─────────────────────────

def _ema_series(values, length):
    out = [None] * len(values)
    k = 2.0 / (length + 1)
    prev = None
    for i, v in enumerate(values):
        prev = v if prev is None else v * k + prev * (1 - k)
        out[i] = prev if i >= length - 1 else None
    return out


def rj_best_scan(symbol, lookback=20, atr_period=14, sl_mult=1.5, tp1_mult=1.5, tp2_mult=2.0,
                 reward_risk=2.0, ut_key=1.0, ut_atr=10, lookback_days=250):
    """Daily-bar port of the 'RJ Best' script: 20-bar support/resistance with an ATR buffer and a
    volume filter (entry zones), ATR-based SL / TP1 / TP2, UT Bot buy-sell flips and the 8/13/21/34 EMAs.
    BUY = call side (stock call / index call), SELL = put side (index put)."""
    from ut_bot import compute_signals
    symbol = _validate_symbol(symbol)
    lookback = _clampi(lookback, 5, 100, 20)
    atr_period = _clampi(atr_period, 5, 50, 14)
    sl_mult = _clamp(sl_mult, 0.5, 5, 1.5)
    tp1_mult = _clamp(tp1_mult, 0.5, 5, 1.5)
    tp2_mult = _clamp(tp2_mult, 0.5, 8, 2.0)
    reward_risk = _clamp(reward_risk, 0.5, 5, 2.0)
    ut_key = _clamp(ut_key, 0.1, 10, 1.0)
    ut_atr = _clampi(ut_atr, 2, 50, 10)
    lookback_days = _clampi(lookback_days, 30, 500, 250)

    bars = fetch_index_history(symbol, lookback_days=lookback_days + lookback + 50)
    n = len(bars)
    if n <= max(lookback, atr_period, ut_atr, 34) + 2:
        raise RuntimeError(f"Not enough historical sessions returned ({n}) for RJ Best")

    closes = [b["close"] for b in bars]
    atr = _rma(_true_range(bars), atr_period)
    stops, positions, ut_sig = compute_signals(bars, key_value=ut_key, atr_period=ut_atr)
    e8, e13, e21, e34 = (_ema_series(closes, k) for k in (8, 13, 21, 34))

    rows = []
    for i in range(n):
        sig, note = "NONE", None
        support = resistance = None
        zone = None
        levels = {}
        if i >= lookback and atr[i] is not None:
            win = bars[i - lookback:i]   # the PREVIOUS `lookback` bars - including today made today's low the support itself
            support = min(b["low"] for b in win)
            resistance = max(b["high"] for b in win)
            a = atr[i]
            vols = [b["volume"] for b in bars[max(0, i - atr_period + 1):i + 1]]
            vol_ok = (sum(vols) / len(vols)) < bars[i]["volume"] if vols and sum(vols) > 0 else True
            # key-level rejection: price pierces the prior 20-bar low/high intrabar and closes back inside it
            bull = bars[i]["low"] <= support and closes[i] > support and vol_ok
            bear = bars[i]["high"] >= resistance and closes[i] < resistance and vol_ok
            levels = {
                "bullSL": support - a * sl_mult,
                "bullTP1": support + a * reward_risk * tp1_mult,
                "bullTP2": support + a * reward_risk * tp2_mult,
                "bearSL": resistance + a * sl_mult,
                "bearTP1": resistance - a * reward_risk * tp1_mult,
                "bearTP2": resistance - a * reward_risk * tp2_mult,
            }
            zone = "BULL" if bull else "BEAR" if bear else None
            if ut_sig[i] == "BUY":
                sig, note = "BUY", "UT"
            elif ut_sig[i] == "SELL":
                sig, note = "SELL", "UT"
            elif bull and not bear:
                sig, note = "BUY", "KEY LEVEL"
            elif bear and not bull:
                sig, note = "SELL", "KEY LEVEL"
        rows.append({
            "date": bars[i]["date"], "open": bars[i]["open"], "high": bars[i]["high"],
            "low": bars[i]["low"], "close": closes[i],
            "support": support, "resistance": resistance, "utStop": stops[i],
            "ema8": e8[i], "ema13": e13[i], "ema21": e21[i], "ema34": e34[i],
            "utPosition": {1: "LONG", -1: "SHORT", 0: "FLAT"}[positions[i]],
            "zone": zone, "phase": note, "signal": sig, **levels,
        })

    rows = rows[-lookback_days:]
    last = rows[-1]
    side = "BUY" if last["utPosition"] == "LONG" else "SELL" if last["utPosition"] == "SHORT" else None
    cur = {
        "date": last["date"], "close": last["close"], "signal": last["signal"], "source": last["phase"],
        "utPosition": last["utPosition"], "zone": last["zone"],
        "support": last["support"], "resistance": last["resistance"], "utStop": last["utStop"],
        "ema8": last["ema8"], "ema13": last["ema13"], "ema21": last["ema21"], "ema34": last["ema34"],
        "emaAligned": ("BULL" if (last["ema8"] or 0) > (last["ema13"] or 0) > (last["ema21"] or 0) > (last["ema34"] or 0)
                       else "BEAR" if (last["ema8"] or 0) < (last["ema13"] or 0) < (last["ema21"] or 0) < (last["ema34"] or 0) else "MIXED"),
    }
    if side == "BUY":
        cur.update({"slLevel": last.get("bullSL"), "tp1": last.get("bullTP1"), "tp2": last.get("bullTP2")})
    elif side == "SELL":
        cur.update({"slLevel": last.get("bearSL"), "tp1": last.get("bearTP1"), "tp2": last.get("bearTP2")})
    return {
        "symbol": symbol,
        "columns": [
            {"key": "support", "label": "Support"}, {"key": "resistance", "label": "Resistance"},
            {"key": "utStop", "label": "UT stop"}, {"key": "utPosition", "label": "UT position"},
            {"key": "ema8", "label": "EMA 8"}, {"key": "ema21", "label": "EMA 21"},
        ],
        "current": cur, "bars": rows, "events": _events(rows),
    }


# ───────────────────────── Fake Breakout / Fake Breakdown (key: fake) ─────────────────────────

def fake_scan(symbol, pivot_len=10, confirm_bars=3, use_volume=False, volume_mult=1.5, lookback_days=250):
    """Daily-bar port of 'Fake Breakout / Fake Breakdown Detector'.
    Levels: the latest confirmed swing high (resistance) and swing low (support), pivots of `pivot_len` bars each side.
      Wick signal      : price pokes through the level intrabar but closes back inside it (same bar).
      Confirmed signal : price CLOSES through the level, then closes back inside within `confirm_bars` bars.
    Fake breakout  (bull trap)  -> SELL / put side.   Fake breakdown (bear trap) -> BUY / call side."""
    symbol = _validate_symbol(symbol)
    pivot_len = _clampi(pivot_len, 1, 50, 10)
    confirm_bars = _clampi(confirm_bars, 1, 20, 3)
    volume_mult = _clamp(volume_mult, 1.0, 10.0, 1.5)
    lookback_days = _clampi(lookback_days, 30, 500, 250)

    bars = fetch_index_history(symbol, lookback_days=lookback_days + pivot_len * 2 + 40)
    n = len(bars)
    if n < pivot_len * 2 + 25:
        raise RuntimeError(f"Not enough historical sessions returned ({n}) for the Fake detector")
    H = [b["high"] for b in bars]
    L = [b["low"] for b in bars]
    C = [b["close"] for b in bars]
    V = [b["volume"] for b in bars]

    res = [None] * n          # resistance level in force on each bar (as Pine's var series)
    sup = [None] * n
    r_lvl = s_lvl = None
    for i in range(n):
        j = i - pivot_len                              # a pivot at j is only confirmed pivot_len bars later
        if j >= pivot_len:
            if H[j] == max(H[j - pivot_len:j + pivot_len + 1]) and all(H[j] > H[k] for k in range(j - pivot_len, j)) \
                    and all(H[j] >= H[k] for k in range(j + 1, j + pivot_len + 1)):
                r_lvl = H[j]
            if L[j] == min(L[j - pivot_len:j + pivot_len + 1]) and all(L[j] < L[k] for k in range(j - pivot_len, j)) \
                    and all(L[j] <= L[k] for k in range(j + 1, j + pivot_len + 1)):
                s_lvl = L[j]
        res[i], sup[i] = r_lvl, s_lvl

    brk_up = brk_dn = None
    rows = []
    for i in range(n):
        vol_ok = True
        if use_volume:
            avg = sum(V[max(0, i - 19):i + 1]) / min(20, i + 1)
            vol_ok = avg > 0 and V[i] > avg * volume_mult
        r, sp = res[i], sup[i]
        fbo_wick = r is not None and H[i] > r and C[i] < r and vol_ok
        fbd_wick = sp is not None and L[i] < sp and C[i] > sp and vol_ok

        crossed_up = i > 0 and r is not None and res[i - 1] is not None and C[i] > r and C[i - 1] <= res[i - 1]
        crossed_dn = i > 0 and sp is not None and sup[i - 1] is not None and C[i] < sp and C[i - 1] >= sup[i - 1]
        if crossed_up:
            brk_up = i
        if crossed_dn:
            brk_dn = i
        fbo_conf = brk_up is not None and i > brk_up and (i - brk_up) <= confirm_bars and r is not None and C[i] < r and vol_ok
        fbd_conf = brk_dn is not None and i > brk_dn and (i - brk_dn) <= confirm_bars and sp is not None and C[i] > sp and vol_ok
        if fbo_conf or (brk_up is not None and (i - brk_up) > confirm_bars):
            brk_up = None
        if fbd_conf or (brk_dn is not None and (i - brk_dn) > confirm_bars):
            brk_dn = None

        fbo, fbd = fbo_wick or fbo_conf, fbd_wick or fbd_conf
        sig, kind = "NONE", None
        stop = target = None
        if fbd and not fbo:
            sig, kind = "BUY", "wick" if fbd_wick else "confirmed"
            stop, target = L[i], r
        elif fbo and not fbd:
            sig, kind = "SELL", "wick" if fbo_wick else "confirmed"
            stop, target = H[i], sp
        rows.append({
            "date": bars[i]["date"], "open": bars[i]["open"], "high": H[i], "low": L[i], "close": C[i],
            "resistance": r, "support": sp, "fakeBreakout": fbo, "fakeBreakdown": fbd, "phase": kind, "signal": sig,
            "stopLoss": stop, "target": target,
        })

    rows = rows[-lookback_days:]
    last = rows[-1]
    recent = next((x for x in reversed(rows[-10:]) if x["signal"] != "NONE"), None)
    cur = {"date": last["date"], "close": last["close"], "signal": last["signal"], "type": last["phase"],
           "resistance": last["resistance"], "support": last["support"],
           "lastFakeSignal": recent["signal"] if recent else None, "lastFakeDate": recent["date"] if recent else None}
    if last["signal"] != "NONE":
        cur.update({"stopLoss": last["stopLoss"], "target": last["target"]})
    return {
        "symbol": symbol,
        "columns": [{"key": "resistance", "label": "Resistance"}, {"key": "support", "label": "Support"},
                    {"key": "phase", "label": "Type"}],
        "current": cur, "bars": rows, "events": _events(rows),
    }


KEYS = {
    "trend-target-ribbon": trend_target_ribbon_scan,
    "dual-phase-reversal": dual_phase_reversal_scan,
    "rj-best": rj_best_scan,
    "fake": fake_scan,
}

PARAM_MAP = {
    "trend-target-ribbon": {
        "lookbackDays": "lookback_days", "almaLength": "alma_length", "almaOffset": "alma_offset",
        "almaSigma": "alma_sigma", "devLength": "dev_length", "devMult": "dev_mult",
        "slopeLength": "slope_length", "slopeMin": "slope_min", "atrLength": "atr_length",
        "stopLookback": "stop_lookback", "minStopAtr": "min_stop_atr", "maxStopAtr": "max_stop_atr",
        "targetCount": "target_count",
    },
    "dual-phase-reversal": {"lookbackDays": "lookback_days"},
    "fake": {"lookbackDays": "lookback_days", "pivotLen": "pivot_len", "confirmBars": "confirm_bars",
             "useVolume": "use_volume", "volumeMult": "volume_mult"},
    "rj-best": {
        "lookbackDays": "lookback_days", "lookback": "lookback", "atrPeriod": "atr_period",
        "slMult": "sl_mult", "tp1Mult": "tp1_mult", "tp2Mult": "tp2_mult", "rewardRisk": "reward_risk",
        "utKey": "ut_key", "utAtr": "ut_atr",
    },
}

CATALOG = [
    ("trend-target-ribbon", "Trend Target Ribbon [BOSWaves]", "Trend",
     "ALMA trend with deviation-band confirmation. Each flip opens a position with a structure stop "
     "(ATR-clamped) and 1R-4R targets, tracked until stopped or reversed.", "rp"),
    ("dual-phase-reversal", "Dual-Phase Reversal (DGT)", "Reversal",
     "Momentum Exhaustion (9-sequence) then Terminal Exhaustion (13-count) with support/resistance, "
     "invalidation and range-pivot levels.", "rp"),
    ("rj-best", "RJ Best (Key Levels + UT Bot + EMAs)", "Trend",
     "20-bar support/resistance entry zones with ATR buffer and volume filter, ATR stop / TP1 / TP2, UT Bot flips "
     "and 8/13/21/34 EMAs. BUY = stock / index call, SELL = index put.", "rp"),
    ("fake", "Fake Breakout / Breakdown", "Reversal",
     "Spots bull and bear traps at the latest swing high / low: price breaks the level but closes back inside it "
     "(same bar = wick, or within 3 bars = confirmed). Fake breakdown = BUY, fake breakout = SELL.", "rp"),
]

CHART_LINES = {
    "trend-target-ribbon": [("alma", "ALMA"), ("ribbonEdge", "Ribbon edge"), ("activeStop", "Stop")],
    "dual-phase-reversal": [("meResistance", "ME resistance"), ("meSupport", "ME support")],
    "fake": [("resistance", "Resistance"), ("support", "Support")],
    "rj-best": [("support", "Support"), ("resistance", "Resistance"), ("utStop", "UT stop"),
                ("ema8", "EMA 8"), ("ema13", "EMA 13"), ("ema21", "EMA 21"), ("ema34", "EMA 34")],
}

"""Web ports of the 'OH / OL Option Setup + VIX' and 'NIFTY Premium Scanner'
TradingView Pine indicators, driven by the same live NSE data used elsewhere
in this app instead of Pine's request.security(). SENSEX is intentionally out
of scope here: it trades on the BSE and this app only integrates with NSE
data sources (bhavcopy + nseindia.com), so the premium scanner is NIFTY-only.
"""

import calendar
from datetime import date, timedelta

from data_store import live_row_to_record, store
from nse_service import nse_service

INDEX_DISPLAY_NAME = {
    "NIFTY": "NIFTY 50",
    "BANKNIFTY": "NIFTY BANK",
    "FINNIFTY": "NIFTY FINANCIAL SERVICES",
    "MIDCPNIFTY": "NIFTY MIDCAP SELECT",
}


def get_index_ohlc(symbol):
    name = INDEX_DISPLAY_NAME.get(symbol.upper())
    if not name:
        return None
    row = nse_service.get_all_indices().get(name)
    if not row:
        return None
    return {
        "open": row.get("open"),
        "high": row.get("high"),
        "low": row.get("low"),
        "last": row.get("last"),
    }


def get_india_vix():
    row = nse_service.get_all_indices().get("INDIA VIX")
    return row.get("last") if row else None


def vix_tier(vix, vix_low=14.0, vix_high=20.0):
    if vix is None:
        return 2
    if vix < vix_low:
        return 1
    if vix > vix_high:
        return 3
    return 2


def fmt_vol(v):
    if v is None:
        return "–"
    if v >= 1e7:
        return f"{v / 1e7:.2f} Cr"
    if v >= 1e5:
        return f"{v / 1e5:.2f} L"
    if v >= 1e3:
        return f"{v / 1e3:.1f} K"
    return str(int(v))


def volume_signal(call_vol, put_vol, threshold, dir_mode):
    total = (call_vol or 0) + (put_vol or 0)
    call_pct = (call_vol / total * 100) if total else None
    put_pct = (100 - call_pct) if call_pct is not None else None
    follow = dir_mode != "contrarian"

    if call_pct is None:
        signal = "none"
    elif call_pct >= threshold:
        signal = "BUY CALL" if follow else "BUY PUT"
    elif put_pct is not None and put_pct >= threshold:
        signal = "BUY PUT" if follow else "BUY CALL"
    else:
        signal = "none"

    return {
        "callPct": call_pct,
        "putPct": put_pct,
        "callVol": call_vol,
        "putVol": put_vol,
        "callVolFmt": fmt_vol(call_vol),
        "putVolFmt": fmt_vol(put_vol),
        "signal": signal,
    }


def _last_weekday_of_month(year, month, weekday):
    last_day = calendar.monthrange(year, month)[1]
    d = date(year, month, last_day)
    offset = (d.weekday() - weekday) % 7
    return d - timedelta(days=offset)


def _computed_monthly_tuesday(today):
    candidate = _last_weekday_of_month(today.year, today.month, 1)
    if candidate < today:
        y, m = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
        candidate = _last_weekday_of_month(y, m, 1)
    return candidate


def resolve_weekly_monthly(symbol):
    available = sorted({
        r["expiry"] for r in store.today_rows
        if r["symbol"] == symbol and r["expiry"]
    })
    if not available:
        return None, None

    today = date.today()
    today_iso = today.isoformat()
    upcoming = [e for e in available if e >= today_iso] or [available[-1]]
    weekly = upcoming[0]

    computed = _computed_monthly_tuesday(today).isoformat()
    if computed in available:
        monthly = computed
    else:
        # NSE shifts an expiry off its usual weekday for market holidays, so the
        # computed Tuesday may not be a real listed contract — fall back to
        # whichever upcoming expiry sits closest to it.
        monthly = min(upcoming, key=lambda e: abs(date.fromisoformat(e) - date.fromisoformat(computed)))
    return weekly, monthly


def oh_ol_setup(symbol, params):
    symbol = symbol.upper()
    idx = get_index_ohlc(symbol)
    if not idx:
        raise RuntimeError(f"No live index data available for {symbol}")

    idx_tol = params.get("idxTol", 0.0)
    idx_oh = idx["open"] is not None and idx["high"] is not None and abs(idx["open"] - idx["high"]) <= idx_tol
    idx_ol = idx["open"] is not None and idx["low"] is not None and abs(idx["open"] - idx["low"]) <= idx_tol

    side_mode = params.get("sideMode", "auto")
    do_put = side_mode == "puts" or side_mode == "both" or (side_mode == "auto" and idx_oh)
    do_call = side_mode == "calls" or side_mode == "both" or (side_mode == "auto" and idx_ol)

    vix = get_india_vix()
    tier = vix_tier(vix, params.get("vixLow", 14.0), params.get("vixHigh", 20.0))

    pts = params.get("pts", 10.0)
    rule = params.get("rule", "open_or_prev")
    pc_tol = params.get("pcTol", 0.0)
    only_qualifying = params.get("onlyQualifying", True)

    live_rows, _trade_date = nse_service.get_live_records(symbol)
    baseline_lookup = store.today_lookup()
    records = [live_row_to_record(r, baseline_lookup) for r in live_rows]

    call_vol_total = 0.0
    put_vol_total = 0.0
    results = []
    match_count = 0

    for r in records:
        vol = r.get("volume") or 0
        if r["type"] == "CE":
            call_vol_total += vol
        else:
            put_vol_total += vol

        show_side = (r["type"] == "CE" and do_call) or (r["type"] == "PE" and do_put)

        open_ = r.get("open")
        low = r.get("low")
        prev_close = r.get("prevCloseUsed")

        near_open = open_ is not None and low is not None and low >= open_ - pts
        near_prev = prev_close is not None and low is not None and low >= prev_close - pts
        open_eq_prev = open_ is not None and prev_close is not None and abs(open_ - prev_close) <= pc_tol

        if rule == "open_only":
            qualifies = near_open
        elif rule == "prev_only":
            qualifies = near_prev
        elif rule == "open_and_prev":
            qualifies = near_open and near_prev
        elif rule == "open_eq_prev":
            qualifies = near_open and open_eq_prev
        else:
            qualifies = near_open or near_prev
        qualifies = show_side and qualifies

        if qualifies:
            match_count += 1

        if show_side and (qualifies or not only_qualifying) and low is not None:
            # Dynamic SL/TGT based on ATR and market conditions
            # Calculate ATR-like measure for better SL/TGT sizing
            atr_proxy = max(low * 0.02, 5.0)  # Minimum 2% or 5 points
            
            # Dynamic multipliers based on VIX tier
            if tier == 1:  # Low volatility
                sl_mult = 1.5
                tgt_mult = 2.5
            elif tier == 2:  # Medium volatility
                sl_mult = 2.0
                tgt_mult = 3.0
            else:  # High volatility
                sl_mult = 2.5
                tgt_mult = 3.5
            
            # Calculate dynamic SL/TGT
            dynamic_sl = round(low - (atr_proxy * sl_mult), 2)
            dynamic_tgt = round(low + (atr_proxy * tgt_mult), 2)
            
            # Original levels for reference
            orig_sl_s5 = round(low * 0.95, 2)
            orig_sl_s9 = round(low * 0.91, 2)
            orig_sl_s18 = round(low * 0.82, 2)
            orig_tgt_t9 = round(low * 1.09, 2)
            orig_tgt_t18 = round(low * 1.18, 2)
            
            # Use the better of dynamic or original (whichever gives wider SL/TGT)
            sl_final = min(dynamic_sl, orig_sl_s5) if tier == 1 else min(dynamic_sl, orig_sl_s9) if tier == 2 else min(dynamic_sl, orig_sl_s18)
            tgt_final = max(dynamic_tgt, orig_tgt_t9) if tier == 1 else max(dynamic_tgt, orig_tgt_t9) if tier == 2 else max(dynamic_tgt, orig_tgt_t18)
            
            results.append({
                "type": "CALL" if r["type"] == "CE" else "PUT",
                "strike": r["strike"],
                "prevClose": prev_close,
                "open": open_,
                "low": low,
                "ltp": r.get("close"),
                "nearOpen": near_open,
                "nearPrev": near_prev,
                "openEqPrev": open_eq_prev,
                "qualifies": qualifies,
                "buyAtLow": low,
                "buyLowPlus9": round(low * 1.09, 2),
                "buyAtOpen": open_,
                "targetT18": orig_tgt_t18,
                "targetT9": orig_tgt_t9,
                "slS5": orig_sl_s5,
                "slS9": orig_sl_s9,
                "slS18": orig_sl_s18,
                # NEW: Dynamic SL/TGT based on market conditions
                "dynamicSL": sl_final,
                "dynamicTarget": tgt_final,
                "atrProxy": round(atr_proxy, 2),
                "slMultiplier": sl_mult,
                "tgtMultiplier": tgt_mult,
                "useT18": tier >= 2,
                "useT9": tier == 1,
                "useS5": tier == 1,
                "useS9": tier == 2,
                "useS18": tier == 3,
                "volume": vol,
            })

    vol_sig = volume_signal(call_vol_total, put_vol_total, params.get("thr", 71.0), params.get("dirMode", "follow"))
    confirmed = (vol_sig["signal"] == "BUY CALL" and idx_ol) or (vol_sig["signal"] == "BUY PUT" and idx_oh)

    if idx_oh and idx_ol:
        index_signal = "OPEN = HIGH = LOW"
    elif idx_oh:
        index_signal = "OPEN = HIGH → bearish → PUT setup"
    elif idx_ol:
        index_signal = "OPEN = LOW → bullish → CALL setup"
    else:
        index_signal = "No Open=High / Open=Low on index"

    return {
        "symbol": symbol,
        "index": idx,
        "idxOH": idx_oh,
        "idxOL": idx_ol,
        "indexSignal": index_signal,
        "vix": vix,
        "vixTier": tier,
        "doCall": do_call,
        "doPut": do_put,
        "results": results,
        "matchCount": match_count,
        "volumeSignal": vol_sig,
        "confirmed": confirmed,
    }


def premium_scanner(params):
    symbol = "NIFTY"
    weekly_iso, monthly_iso = resolve_weekly_monthly(symbol)
    if not weekly_iso:
        raise RuntimeError("No expiry data available for NIFTY — load a bhavcopy first")

    exp_sel = params.get("expSel", "both")
    want_weekly = exp_sel != "monthly"
    want_monthly = exp_sel != "weekly"
    same = weekly_iso == monthly_iso

    prem_src = params.get("premSrc", "prevclose")
    prem_from = params.get("premFrom", 300.0)
    prem_to = params.get("premTo", 349.0)
    low_from = params.get("lowFrom", 52.0)
    low_to = params.get("lowTo", 58.0)
    div1 = params.get("div1", 8.0)
    div2 = params.get("div2", 6.5)
    low_mode = params.get("lowMode", "fixed")
    only_matches = params.get("onlyMatches", False)

    baseline_lookup = store.today_lookup()

    def fetch_for_expiry(expiry_iso, expiry_tag):
        live_rows, _ = nse_service.get_live_records(symbol, expiry_override=expiry_iso)
        records = [live_row_to_record(r, baseline_lookup) for r in live_rows]
        out = []
        cv = pv = 0.0
        for r in records:
            vol = r.get("volume") or 0
            if r["type"] == "CE":
                cv += vol
            else:
                pv += vol

            prem = r.get("prevCloseUsed") if prem_src == "prevclose" else r.get("open")
            low = r.get("low")
            f1 = (prem / div1) if prem is not None else None
            f2 = (prem / div2) if prem is not None else None
            prem_ok = prem is not None and prem_from <= prem <= prem_to
            low_fixed_ok = low is not None and low_from <= low <= low_to
            low_formula_ok = f1 is not None and low is not None and min(f1, f2) <= low <= max(f1, f2)

            if low_mode == "formula":
                low_ok = low_formula_ok
            elif low_mode == "both":
                low_ok = low_fixed_ok and low_formula_ok
            elif low_mode == "either":
                low_ok = low_fixed_ok or low_formula_ok
            else:
                low_ok = low_fixed_ok

            match = prem_ok and low_ok
            if match or not only_matches:
                out.append({
                    "expiryTag": expiry_tag,
                    "type": "CALL" if r["type"] == "CE" else "PUT",
                    "strike": r["strike"],
                    "premium": prem,
                    "open": r.get("open"),
                    "high": r.get("high"),
                    "low": low,
                    "ltp": r.get("close"),
                    "formula1": f1,
                    "formula2": f2,
                    "premOk": prem_ok,
                    "lowOk": low_ok,
                    "match": match,
                    "volume": vol,
                })
        vol_sig = volume_signal(cv, pv, params.get("thr", 71.0), params.get("dirMode", "follow"))
        return out, vol_sig

    results = []
    signals = {}
    if want_weekly:
        rows, sig = fetch_for_expiry(weekly_iso, "weekly")
        results.extend(rows)
        signals["weekly"] = sig
    if want_monthly and not (want_weekly and same):
        rows, sig = fetch_for_expiry(monthly_iso, "monthly")
        results.extend(rows)
        signals["monthly"] = sig

    return {
        "symbol": symbol,
        "weeklyExpiry": weekly_iso,
        "monthlyExpiry": monthly_iso,
        "sameContract": same,
        "results": results,
        "matchCount": sum(1 for r in results if r["match"]),
        "signals": signals,
    }

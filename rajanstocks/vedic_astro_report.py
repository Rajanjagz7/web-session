"""Assembles the Daily NIFTY 50 Vedic Astro Intraday Watch Report.

Per the report's own rules: never fabricate market data. Every market-context
field is either pulled from the app's existing live services (market_api.py,
which wraps nse_service/Upstox) or explicitly marked unavailable - it does not
guess, estimate, or carry over a previous day's numbers.

Astrology (Panchang, Rahu Kaal, planetary positions) is informational context
only. It never decides a BUY/SELL recommendation by itself - the watch-window
action plan is pure price action / VWAP / volume, evaluated against live data
by the caller (this module only emits the static rule text + whatever live
numbers are available to check them against).
"""
from datetime import datetime, timezone, timedelta

import vedic_panchang

# Fixed-offset, not ZoneInfo("Asia/Kolkata") - that needs the IANA tzdata
# package, which isn't guaranteed to be present (fails on this Windows dev
# box, and isn't certain on Vercel's runtime either). Matches the IST
# convention already used everywhere else in this app (market_api.py etc.).
IST = timezone(timedelta(hours=5, minutes=30))

WATCH_WINDOWS_TEMPLATE = [
    {
        "key": "opening_range", "label": "OPENING RANGE", "window_ist": "09:15-09:30",
        "focus": "Define range & key levels",
        "bullish": "If price holds above OR high with strong volume -> plan BUY above OR high on breakout. Stop-loss below OR low.",
        "bearish": "If price rejects OR high and breaks below OR low on strong volume -> plan SELL below OR low. Stop-loss above OR high.",
        "no_trade": "Inside narrow range (<0.3%) with low volume.",
        "key_checks": ["OR High/Low", "Volume", "Opening Gap", "VWAP position"],
    },
    {
        "key": "observation", "label": "OBSERVATION WINDOW", "window_ist": "09:30-10:45",
        "focus": "Trend setup & confirmation",
        "bullish": "Trade direction of strength. Take BUY on breakout of structure with volume above VWAP. Trail SL below structure / VWAP.",
        "bearish": "Trade direction of weakness. Take SELL on breakdown with volume below VWAP. Trail SL above structure / VWAP.",
        "no_trade": "Choppy price action, no follow-through, volume dry-up.",
        "key_checks": ["VWAP slope", "Volume vs avg", "Structure break", "Market breadth"],
    },
    {
        "key": "rahu_kaal", "label": "MUMBAI RAHU KAAL", "window_ist": None,  # filled in per-day
        "focus": "Caution period - avoid new risk",
        "bullish": "Prefer to be FLAT or manage existing positions only. No fresh longs.",
        "bearish": "Avoid fresh shorts. Manage or reduce existing positions.",
        "no_trade": "Best time to stay flat. High whipsaw probability.",
        "key_checks": ["Volatility", "Whipsaw risk", "Discipline"],
        "astrology_note": "Traditional/non-scientific caution window. Never a BUY/SELL signal by itself - stop-loss and exit rules still apply as normal.",
    },
    {
        "key": "confirmation", "label": "CONFIRMATION WINDOW", "window_ist": "12:25-13:45",
        "focus": "Validate trend & re-align",
        "bullish": "If price reclaims VWAP and makes higher high with volume -> continue longs / add on dips above VWAP.",
        "bearish": "If price stays below VWAP and makes lower low with volume -> continue shorts / add on rallies below VWAP.",
        "no_trade": "Fails to reclaim VWAP (bull case) or rejects VWAP (bear case).",
        "key_checks": ["VWAP reclaim", "Volume surge", "Structure"],
    },
    {
        "key": "trend_reversal", "label": "TREND / REVERSAL WATCH", "window_ist": "13:50-15:20",
        "focus": "Ride trend or look for reversal",
        "bullish": "Ride the trend with trailing SL. Look for bullish reversal patterns near support / VWAP.",
        "bearish": "Ride the trend with trailing SL. Look for bearish reversal patterns near resistance / VWAP.",
        "no_trade": "Exhaustion signals near highs/lows before 15:20.",
        "key_checks": ["Momentum", "Reversal candlestick", "Volume climax"],
    },
]

RISK_MANAGEMENT = [
    "Define the stop-loss BEFORE entry.",
    "Risk per trade: illustrative default 0.5%-1.5% of capital (not personalized advice).",
    "Use position sizing by volatility (ATR).",
    "Avoid overtrading.",
    "No revenge trading.",
    "Account for slippage, brokerage & taxes.",
    "Protect capital first.",
    "Stay disciplined.",
]

DISCLAIMER = (
    "Market data must be verified against current sources. Astronomical positions are ephemeris "
    "calculations; Panchang and Rahu Kaal are traditional astrological conventions. Astrology is not "
    "scientifically validated for predicting stock prices. This report is educational information, not "
    "financial advice. All BUY/SELL setups are conditional on price action, volume, VWAP, risk controls, "
    "and verified live data."
)


def _na(reason: str):
    return {"available": False, "value": None, "reason": reason}


def _ok(value):
    return {"available": True, "value": value}


def _market_context():
    """Pulls from the app's existing live services. Degrades to NOT AVAILABLE per field, never fabricates."""
    out = {}
    try:
        import market_api
        q = market_api.quotes(symbols="NIFTY")
        row = next((r for r in q["quotes"] if r["s"] == "NIFTY"), None)
        if row:
            out["nifty_prev_close"] = _ok(row["prev"])
            out["nifty_today_ohlc"] = _ok({"open": row["open"], "high": row["high"], "low": row["low"]})
            out["nifty_last"] = _ok(row["last"])
            out["market_open"] = _ok(q["marketOpen"])
            out["quotes_as_of"] = _ok(q["asOf"])
            out["quotes_stale"] = _ok(q.get("stale", False))
        else:
            out["nifty_prev_close"] = out["nifty_today_ohlc"] = out["nifty_last"] = _na("NIFTY not in quote response")
    except Exception as e:
        reason = f"Live quotes unavailable: {str(e)[:160]}"
        out["nifty_prev_close"] = out["nifty_today_ohlc"] = out["nifty_last"] = _na(reason)
        out["market_open"] = out["quotes_as_of"] = _na(reason)

    try:
        import market_api
        g = market_api.global_markets()
        rows = {r.get("n"): r for r in g.get("rows", g if isinstance(g, list) else [])} if g else {}
        gift = rows.get("GIFT Nifty")
        crude = rows.get("Crude Oil (MCX)") or rows.get("Crude (NYMEX)")
        out["gift_nifty"] = _ok(gift) if gift else _na("GIFT Nifty not in /global response")
        out["crude_oil"] = _ok(crude) if crude else _na("Crude oil not in /global response")
    except Exception as e:
        reason = f"Global markets unavailable: {str(e)[:160]}"
        out["gift_nifty"] = out["crude_oil"] = _na(reason)

    out["fpi_flow"] = _na("No FPI flow data source wired into this app yet")
    out["live_vwap"] = _na("VWAP needs intraday 5m candles computed during market hours - not run here")
    out["opening_range"] = _na("Computed live after 09:30 IST from the first three 5-min candles - not available outside that window")
    return out


def _stocks_to_watch(limit: int = 5):
    """Reuses the existing /daily-scan (Open=High/Open=Low bias scanner) that already backs the live #picks page."""
    try:
        import market_api
        scan = market_api.daily_scan(refresh=False, limit=limit)
        rows = scan["rows"][:limit]
        if not rows:
            return _na("Daily scan returned no candidates (markets likely closed or no OH/OL setups today)")
        picks = []
        for r in rows:
            picks.append({
                "symbol": r["symbol"], "name": r["name"], "reason": r["status"].replace("_", "=").title(),
                "bias": r["bias"], "ltp": r["ltp"], "prev": r["prev"], "chg_pct": r["chg"],
                "today_ohlc": {"open": r["open"], "high": r["high"], "low": r["low"]},
                "idea": r["idea"],
                "note": "Watchlist candidate from the live Open=High/Open=Low scan, not a standing BUY/SELL recommendation.",
            })
        return _ok(picks)
    except Exception as e:
        return _na(f"Daily scan unavailable: {str(e)[:160]}")


def generate_report(now_utc: datetime | None = None) -> dict:
    now_utc = now_utc or datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST)

    panchang = vedic_panchang.compute_panchang(now_utc)
    rk_start, rk_end = vedic_panchang.rahu_kaal_window(
        panchang["sunrise_utc"], panchang["sunset_utc"], now_ist.weekday()
    )
    rk_start_ist = datetime.fromisoformat(rk_start).astimezone(IST).strftime("%H:%M") if rk_start else None
    rk_end_ist = datetime.fromisoformat(rk_end).astimezone(IST).strftime("%H:%M") if rk_end else None

    windows = []
    for w in WATCH_WINDOWS_TEMPLATE:
        w = dict(w)
        if w["key"] == "rahu_kaal":
            w["window_ist"] = f"{rk_start_ist}-{rk_end_ist}" if rk_start_ist else "NOT AVAILABLE"
        windows.append(w)

    is_weekday = now_ist.weekday() < 5  # Mon-Fri; NOT a holiday calendar check - flagged below
    session_phase = (
        "pre-market" if now_ist.hour < 9 or (now_ist.hour == 9 and now_ist.minute < 15)
        else "during session" if (now_ist.hour, now_ist.minute) < (15, 30)
        else "post-market"
    )

    return {
        "header": {
            "report_date": now_ist.strftime("%A, %d %B %Y"),
            "report_generated_ist": now_ist.strftime("%H:%M:%S IST"),
            "nse_trading_day": _ok("Likely (weekday)") if is_weekday else _ok("No - weekend"),
            "nse_holiday_check": _na("No NSE holiday calendar wired into this app - verify against the official NSE calendar before relying on this"),
            "session": "09:15-15:30 IST (Equity Cash)",
            "session_phase": session_phase,
        },
        "market_context": _market_context(),
        "panchang": {
            "day": f"{now_ist.strftime('%A')} / {panchang['weekday_sanskrit']}",
            "tithi": f"{panchang['paksha']} {panchang['tithi_name']} (#{panchang['tithi_number']})",
            "nakshatra": panchang["nakshatra"],
            "moon_sign": panchang["moon_rashi"],
            "sunrise_ist": datetime.fromisoformat(panchang["sunrise_utc"]).astimezone(IST).strftime("%H:%M") if panchang["sunrise_utc"] else None,
            "sunset_ist": datetime.fromisoformat(panchang["sunset_utc"]).astimezone(IST).strftime("%H:%M") if panchang["sunset_utc"] else None,
            "mumbai_rahu_kaal_ist": f"{rk_start_ist}-{rk_end_ist}" if rk_start_ist else "NOT AVAILABLE",
            "ayanamsa": f"Lahiri {panchang['ayanamsa_lahiri_deg']} deg",
            "node_type": "MEAN lunar node (not true/osculating node - see module docstring)",
        },
        "sidereal_positions": {
            "reference_time_ist": now_ist.strftime("%H:%M IST"),
            "planets_deg": panchang["planets_sidereal_deg"],
            "source": "Skyfield / JPL DE421, Lahiri ayanamsa (computed here, not a third-party API)",
        },
        "watch_windows": windows,
        "stocks_to_watch": _stocks_to_watch(5),
        "risk_management": RISK_MANAGEMENT,
        "disclaimer": DISCLAIMER,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(generate_report(), indent=2, default=str))

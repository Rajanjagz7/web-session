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

import gann_levels
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

# NSE equity-segment trading holidays. Compiled from public holiday listings
# cross-checked against each other (NSE's own site blocks automated
# fetches), not pulled live from an official feed - update this list each
# year and verify independently before relying on it for anything beyond
# informational display. Year -> {iso date: holiday name}.
NSE_HOLIDAYS = {
    2026: {
        "2026-01-26": "Republic Day",
        "2026-03-03": "Holi",
        "2026-03-26": "Shri Ram Navami",
        "2026-03-31": "Shri Mahavir Jayanti",
        "2026-04-03": "Good Friday",
        "2026-04-14": "Dr. Baba Saheb Ambedkar Jayanti",
        "2026-05-01": "Maharashtra Day",
        "2026-05-28": "Bakri Id",
        "2026-06-26": "Muharram",
        "2026-09-14": "Ganesh Chaturthi",
        "2026-10-02": "Mahatma Gandhi Jayanti",
        "2026-10-20": "Dussehra",
        "2026-11-10": "Diwali-Balipratipada",
        "2026-11-24": "Guru Nanak Jayanti",
        "2026-12-25": "Christmas",
    },
}

DISCLAIMER = (
    "Market data must be verified against current sources. Astronomical positions are ephemeris "
    "calculations; Panchang and Rahu Kaal are traditional astrological conventions. Astrology is not "
    "scientifically validated for predicting stock prices. This report is educational information, not "
    "financial advice. All BUY/SELL setups are conditional on price action, volume, VWAP, risk controls, "
    "and verified live data."
)


def _day_bias(paksha: str, tithi_number: int) -> dict:
    """Traditional Vedic market-astrology headline bias from the lunar fortnight.

    Shukla Paksha (waxing moon) is traditionally read as a bullish/expansion
    half-month, Krishna Paksha (waning moon) as bearish/contraction - hence
    "buy on dip" vs "sell on rise" as a day-opening posture. Purnima/Amavasya
    (the paksha turning points) are flagged separately since they're
    traditionally treated as higher-volatility, directionless days. This is
    NOT a trading signal - it's the same traditional-astrology caveat that
    applies to the rest of this report.
    """
    if tithi_number in (15, 30):
        return {
            "label": "TRANSITION DAY", "tone": "neutral",
            "basis": "Purnima (full moon)" if tithi_number == 15 else "Amavasya (new moon)",
            "note": "Traditionally a higher-volatility, directionless day in Vedic market astrology - not a signal. Wait for price confirmation before acting.",
        }
    if paksha == "Shukla":
        return {
            "label": "BUY ON DIP", "tone": "bullish", "basis": "Shukla Paksha - waxing moon",
            "note": "Traditional Vedic market-astrology bias only, not a trading signal. Confirm with price action, VWAP and volume before acting.",
        }
    return {
        "label": "SELL ON RISE", "tone": "bearish", "basis": "Krishna Paksha - waning moon",
        "note": "Traditional Vedic market-astrology bias only, not a trading signal. Confirm with price action, VWAP and volume before acting.",
    }


def _na(reason: str):
    return {"available": False, "value": None, "reason": reason}


def _ok(value):
    return {"available": True, "value": value}


INDEX_DISPLAY_NAME = {"NIFTY": "Nifty 50", "BANKNIFTY": "Nifty Bank", "SENSEX": "BSE Sensex"}


def _market_context(symbol: str = "NIFTY"):
    """Pulls from the app's existing live services. Degrades to NOT AVAILABLE per field, never fabricates."""
    out = {}
    try:
        import market_api
        q = market_api.quotes(symbols=symbol)
        row = next((r for r in q["quotes"] if r["s"] == symbol), None)
        if row:
            out["index_prev_close"] = _ok(row["prev"])
            out["index_today_ohlc"] = _ok({"open": row["open"], "high": row["high"], "low": row["low"]})
            out["index_last"] = _ok(row["last"])
            out["market_open"] = _ok(q["marketOpen"])
            out["quotes_as_of"] = _ok(q["asOf"])
            out["quotes_stale"] = _ok(q.get("stale", False))
        else:
            out["index_prev_close"] = out["index_today_ohlc"] = out["index_last"] = _na(f"{symbol} not in quote response")
    except Exception as e:
        reason = f"Live quotes unavailable: {str(e)[:160]}"
        out["index_prev_close"] = out["index_today_ohlc"] = out["index_last"] = _na(reason)
        out["market_open"] = out["quotes_as_of"] = _na(reason)

    try:
        import market_api
        g = market_api.global_markets()
        items = g.get("items") or [] if isinstance(g, dict) else (g or [])
        rows = {(r.get("name") or r.get("n")): r for r in items}

        def _gl(r):
            return {"price": r.get("price"), "chg_pct": r.get("chgPct"), "chg": r.get("chg"), "name": r.get("name"),
                    "mode": r.get("mode"), "delay": r.get("delay")}
        gift = rows.get("GIFT Nifty")
        crude = rows.get("Crude Oil (MCX)") or rows.get("Crude (NYMEX)")
        out["gift_nifty"] = _ok(_gl(gift)) if gift else _na("GIFT Nifty not returned by the global markets feed right now")
        out["crude_oil"] = _ok(_gl(crude)) if crude else _na("Crude oil not returned by the global markets feed right now")
    except Exception as e:
        reason = f"Global markets unavailable: {str(e)[:160]}"
        out["gift_nifty"] = out["crude_oil"] = _na(reason)

    out["fpi_flow"] = _na("No FPI flow data source wired into this app yet")
    out.update(_session_stats(symbol))
    return out


def _session_stats(symbol):
    """VWAP and the 15-minute opening range from the latest session's 5-minute candles.

    Index candles carry no volume, so for an index the "VWAP" falls back to the session's
    average typical price (equal weight per 5-min bar) and says so. Outside market hours both
    numbers describe the last completed session and are labelled with its date.
    """
    try:
        import market_api
        up = market_api.upstox_service
        key = market_api._key(symbol)
        bars = []
        try:  # today's live session first (cheap: one call)
            bars = market_api._dedupe(up.fetch_intraday_candles(key, "minutes", "5"))
        except Exception:
            bars = []
        if not bars:  # holiday / weekend / pre-open: the last completed session from the last week only
            t = datetime.now(IST).date()
            bars = market_api._dedupe(up.fetch_historical_candles(key, "minutes", "5", to_date=t.isoformat(),
                                                                  from_date=(t - timedelta(days=7)).isoformat()))
    except Exception as e:
        reason = f"5-minute candles unavailable: {str(e)[:120]}"
        return {"live_vwap": _na(reason), "opening_range": _na(reason)}
    bars = sorted(bars or [], key=lambda b: b["t"])
    if not bars:
        return {"live_vwap": _na("No 5-minute candles returned"), "opening_range": _na("No 5-minute candles returned")}
    day = lambda b: datetime.fromtimestamp(b["t"] / 1000, IST).date()
    last_day = day(bars[-1])
    sess = [b for b in bars if day(b) == last_day]
    today = datetime.now(IST).date()
    live = last_day == today
    tag = "today" if live else last_day.strftime("%a %d %b")
    vol = sum((b.get("v") or 0) for b in sess)
    tp = [((b["h"] + b["l"] + b["c"]) / 3, b.get("v") or 0) for b in sess]
    if vol > 0:
        vwap, kind = sum(p * v for p, v in tp) / vol, "vwap"
    else:
        vwap, kind = sum(p for p, _ in tp) / len(tp), "session_avg"
    first = sess[:3]
    orh, orl = max(b["h"] for b in first), min(b["l"] for b in first)
    last = sess[-1]["c"]
    return {
        "live_vwap": _ok({"value": round(vwap, 2), "kind": kind, "session": last_day.isoformat(), "session_tag": tag, "live": live,
                          "vs_price_pct": round((last / vwap - 1) * 100, 2), "bars": len(sess)}),
        "opening_range": _ok({"high": round(orh, 2), "low": round(orl, 2), "width": round(orh - orl, 2), "session": last_day.isoformat(),
                              "session_tag": tag, "live": live, "complete": len(first) == 3,
                              "price_vs": "above" if last > orh else "below" if last < orl else "inside"}),
    }


def _stocks_to_watch(limit: int = 5):
    """Reuses the existing /daily-scan (Open=High/Open=Low bias scanner) that already backs the live #picks page.

    daily_scan() runs off Upstox's current quote snapshot regardless of whether
    the market is open right now - on a weekend/holiday that snapshot is simply
    frozen at Friday's close, which is correct (same "last session" convention
    the Picks page uses), but needs to say so explicitly or it reads as if it
    were today's live data.
    """
    try:
        import market_api
        scan = market_api.daily_scan(refresh=False, limit=limit)
        rows = scan["rows"][:limit]
        session_note = "Live - updates through the trading session." if scan.get("marketOpen") else "Market closed - showing the last completed session, not today's live data."
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
        return {"available": True, "value": picks, "as_of": scan.get("asOf"), "market_open": scan.get("marketOpen"), "session_note": session_note}
    except Exception as e:
        return _na(f"Daily scan unavailable: {str(e)[:160]}")


def generate_report(now_utc: datetime | None = None, symbol: str = "NIFTY") -> dict:
    symbol = symbol.upper()
    if symbol not in INDEX_DISPLAY_NAME:
        raise ValueError(f"Unsupported index {symbol!r} - choose one of {sorted(INDEX_DISPLAY_NAME)}")
    now_utc = now_utc or datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST)

    panchang = vedic_panchang.compute_panchang(now_utc)
    rk_start, rk_end = vedic_panchang.rahu_kaal_window(
        panchang["sunrise_utc"], panchang["sunset_utc"], now_ist.weekday()
    )
    rk_start_ist = datetime.fromisoformat(rk_start).astimezone(IST).strftime("%H:%M") if rk_start else None
    rk_end_ist = datetime.fromisoformat(rk_end).astimezone(IST).strftime("%H:%M") if rk_end else None

    def _mins(hhmm):
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)

    windows = []
    for w in WATCH_WINDOWS_TEMPLATE:
        w = dict(w)
        if w["key"] == "rahu_kaal":
            w["window_ist"] = f"{rk_start_ist}-{rk_end_ist}" if rk_start_ist else "NOT AVAILABLE"
        if w["window_ist"] and "-" in w["window_ist"] and w["window_ist"] != "NOT AVAILABLE":
            a, b = w["window_ist"].split("-")
            w["start_min"], w["end_min"] = _mins(a), _mins(b)
            w["in_session"] = w["end_min"] > 555 and w["start_min"] < 930   # overlaps 09:15-15:30
        else:
            w["start_min"] = w["end_min"] = None
            w["in_session"] = False
        if w["key"] == "rahu_kaal" and not w["in_session"]:
            w["focus"] = "Outside market hours today - no effect on the session"
        windows.append(w)
    windows.sort(key=lambda w: (not w["in_session"], w["start_min"] if w["start_min"] is not None else 9999))

    today_iso = now_ist.date().isoformat()
    is_weekday = now_ist.weekday() < 5
    is_weekend = not is_weekday
    weekend_message = None
    if is_weekend:
        next_monday = (now_ist + timedelta(days=(-now_ist.weekday()) % 7)).date()
        weekend_message = f"Markets are closed for the weekend. This report updates again Monday, {next_monday.strftime('%d %B %Y')} at 08:00 IST."
    holiday_name = NSE_HOLIDAYS.get(now_ist.year, {}).get(today_iso)
    have_calendar = now_ist.year in NSE_HOLIDAYS
    if holiday_name:
        trading_day = _ok(f"No - {holiday_name}")
    elif not is_weekday:
        trading_day = _ok("No")
    elif have_calendar:
        trading_day = _ok("Yes - scheduled trading day")
    else:
        trading_day = _ok("Likely (weekday) - no holiday calendar for this year, verify independently")
    holiday_check = (
        _ok(f"Holiday calendar found - {holiday_name}" if holiday_name else "No holiday on this date in our calendar")
        if have_calendar else
        _na(f"No NSE holiday calendar wired in for {now_ist.year} - verify against the official NSE calendar before relying on this")
    )
    session_phase = (
        "Market closed" if (holiday_name or not is_weekday)
        else "Pre-market" if now_ist.hour < 9 or (now_ist.hour == 9 and now_ist.minute < 15)
        else "During session" if (now_ist.hour, now_ist.minute) < (15, 30)
        else "Post-market"
    )

    # Seller / buyer windows for the session this report is for (today, or the next trading day once closed)
    try:
        import vedic_timing
        hol = NSE_HOLIDAYS.get(now_ist.year, {}) | NSE_HOLIDAYS.get(now_ist.year + 1, {})
        sdate = vedic_timing.next_session(now_ist, hol)
        s_open = datetime(sdate.year, sdate.month, sdate.day, 9, 15, tzinfo=IST).astimezone(timezone.utc)
        special_timing = vedic_timing.build(sdate, vedic_panchang.compute_panchang(s_open), hol)
    except Exception as e:
        special_timing = {"available": False, "reason": f"Special timing unavailable: {str(e)[:160]}"}

    mc = _market_context(symbol)
    spot = mc["index_last"]["value"] if mc.get("index_last", {}).get("available") else None
    prev = mc["index_prev_close"]["value"] if mc.get("index_prev_close", {}).get("available") else None
    ohlc = mc["index_today_ohlc"]["value"] if mc.get("index_today_ohlc", {}).get("available") else None
    today_open = ohlc.get("open") if (ohlc and mc.get("market_open", {}).get("value")) else None
    # Outside the live session the next session's previous close IS the last traded price, so the
    # Gann ladder (and the "prev close" the page shows) must use it - not the close before it.
    in_session = session_phase == "During session" and bool(mc.get("market_open", {}).get("value"))
    if spot and not in_session:
        last_sess = None
        try:
            last_sess = mc.get("live_vwap", {}).get("value", {}).get("session")
        except Exception:
            last_sess = None
        mc["levels_base"] = _ok({"price": spot, "kind": "last close", "session": last_sess, "for": "next session",
                                 "note": "Market not in session - the last close is the next session's previous close"})
        prev, today_open = spot, None
    elif prev:
        mc["levels_base"] = _ok({"price": prev, "kind": "previous close", "session": None, "for": "today",
                                 "note": "Live session - levels from the previous close"})
    bars = None
    try:
        from ut_bot import fetch_index_history
        bars = fetch_index_history(symbol, lookback_days=400)
    except Exception:
        bars = None
    try:
        gann = gann_levels.build(spot, prev, today_open, panchang["planets_sidereal_deg"], panchang["ayanamsa_lahiri_deg"], bars, now_ist.date(),
                                 base_kind=(mc.get("levels_base") or {}).get("value", {}).get("kind"))
    except Exception as e:
        gann = {"available": False, "reason": f"Gann levels unavailable: {str(e)[:160]}"}
    bias = _day_bias(panchang["paksha"], panchang["tithi_number"])
    votes = []
    votes.append(("Vedic lunar bias", {"bullish": 1, "bearish": -1}.get(bias["tone"], 0), bias["label"]))
    if gann.get("available"):
        base = gann["base"]["price"]
        votes.append(("Price vs Gann base (0°)", 1 if spot > base else -1 if spot < base else 0, f"{'above' if spot > base else 'below'} {base:,.2f}"))
        if gann.get("hilo_trend"):
            votes.append(("Gann HiLo trend (daily)", {"up": 1, "down": -1}.get(gann["hilo_trend"], 0), gann["hilo_trend"]))
    score = sum(v for _, v, _ in votes)
    lean = "BULLISH LEAN" if score >= 2 else "BEARISH LEAN" if score <= -2 else "MIXED / WAIT"
    confluence = {"lean": lean, "score": score, "max": len(votes),
                  "factors": [{"name": n, "vote": v, "detail": d} for n, v, d in votes],
                  "note": "Counts traditional and technical cues only. Not a signal - act only on live price action, VWAP and volume."}

    return {
        "header": {
            "symbol": symbol,
            "symbol_name": INDEX_DISPLAY_NAME[symbol],
            "report_date": now_ist.strftime("%A, %d %B %Y"),
            "report_generated_ist": now_ist.strftime("%H:%M:%S IST"),
            "nse_trading_day": trading_day,
            "nse_holiday_check": holiday_check,
            "session": "09:15-15:30 IST (Equity Cash)",
            "session_phase": session_phase,
            "is_weekend": is_weekend,
            "weekend_message": weekend_message,
        },
        "day_bias": bias,
        "market_context": mc,
        "gann": gann,
        "confluence": confluence,
        "panchang": {
            "day": f"{now_ist.strftime('%A')} / {panchang['weekday_sanskrit']}",
            "tithi": f"{panchang['paksha']} {panchang['tithi_name']} (#{panchang['tithi_number']})",
            "nakshatra": panchang["nakshatra"],
            "moon_sign": panchang["moon_rashi"],
            "yoga": panchang["yoga"],
            "paksha": panchang["paksha"],
            "tithi_number": panchang["tithi_number"],
            "tithi_remaining": panchang["tithi_ends_fraction_of_day_remaining"],
            "nakshatra_remaining": panchang["nakshatra_ends_fraction_remaining"],
            "sunrise_ist": datetime.fromisoformat(panchang["sunrise_utc"]).astimezone(IST).strftime("%H:%M") if panchang["sunrise_utc"] else None,
            "sunset_ist": datetime.fromisoformat(panchang["sunset_utc"]).astimezone(IST).strftime("%H:%M") if panchang["sunset_utc"] else None,
            "mumbai_rahu_kaal_ist": f"{rk_start_ist}-{rk_end_ist}" if rk_start_ist else "NOT AVAILABLE",
            "ayanamsa": f"Lahiri {panchang['ayanamsa_lahiri_deg']} deg",
            "node_type": "TRUE (osculating) lunar node - see vedic_panchang module docstring",
        },
        "sidereal_positions": {
            "reference_time_ist": now_ist.strftime("%H:%M IST"),
            "planets_deg": {k: float(v) for k, v in panchang["planets_sidereal_deg"].items()},
            "source": "Skyfield / JPL DE421, Lahiri ayanamsa (computed here, not a third-party API)",
        },
        "watch_windows": windows,
        "special_timing": special_timing,
        "stocks_to_watch": _stocks_to_watch(5),
        "risk_management": RISK_MANAGEMENT,
        "disclaimer": DISCLAIMER,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(generate_report(), indent=2, default=str))

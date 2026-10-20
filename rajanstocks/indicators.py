"""Web ports of the 'OH / OL Option Setup + VIX' and 'NIFTY Premium Scanner'
TradingView Pine indicators, driven by the same live NSE data used elsewhere
in this app instead of Pine's request.security(). SENSEX is intentionally out
of scope here: it trades on the BSE and this app only integrates with NSE
data sources (bhavcopy + nseindia.com), so the premium scanner is NIFTY-only.
"""

import calendar
from datetime import date, timedelta

from data_store import store
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



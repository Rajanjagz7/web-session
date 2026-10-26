"""Exposes the Daily NIFTY 50 Vedic Astro report as a JSON endpoint.

Astrology here is informational context only (Panchang, Rahu Kaal, sidereal
planetary positions) - it never decides a BUY/SELL signal by itself. See
vedic_astro_report.py's own docstring.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

import vedic_astro_report

router = APIRouter(prefix="/api/vedic")

import time

_cache: dict[str, tuple[str, float, dict]] = {}  # symbol -> (date, built_at, report)


def _ttl():
    """2 minutes while NSE is in session (live price, VWAP, opening range move), 30 minutes otherwise."""
    now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30)))
    in_session = __import__("nse_calendar").is_trading_day(now.date()) and (9, 15) <= (now.hour, now.minute) < (15, 30)
    return 120 if in_session else 1800


@router.get("/report")
def report(refresh: bool = False, symbol: str = "NIFTY"):
    symbol = symbol.upper()
    today = datetime.now(timezone.utc).date().isoformat()
    cached = _cache.get(symbol)
    if refresh or not cached or cached[0] != today or time.time() - cached[1] > _ttl():
        try:
            _cache[symbol] = (today, time.time(), vedic_astro_report.generate_report(symbol=symbol))
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(502, f"Could not generate the Vedic Astro report: {e}")
    return _cache[symbol][2]


_tc: dict = {}


@router.get("/timecycle")
def timecycle(symbol: str = "NIFTY", mode: str = "underlying", strike: str = ""):
    """Gann intraday time cycles + vibration zones for an index / F&O stock or its ATM option premium."""
    import time_cycle
    mode = mode.lower() if mode.lower() in ("underlying", "ce", "pe") else "underlying"
    try:                                              # accept "22,700", " 22700 " etc. instead of a raw 422
        strike = float(str(strike or "0").replace(",", "").strip() or 0)
    except ValueError:
        raise HTTPException(400, "Strike must be a number, e.g. 22700")
    k = (symbol.upper(), mode, strike)
    hit = _tc.get(k)
    if hit and time.time() - hit[0] < 120:
        return hit[1]
    try:
        r = time_cycle.build(symbol, mode, strike or None)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except time_cycle.Unavailable as e:              # upstream candles missing right now: retryable, not a client error
        raise HTTPException(503, f"Time cycle unavailable: {str(e)[:160]}")
    except Exception as e:
        raise HTTPException(502, f"Time cycle unavailable: {str(e)[:160]}")
    if len(_tc) > 300:
        _tc.clear()
    _tc[k] = (time.time(), r)
    return r

"""Exposes the Daily NIFTY 50 Vedic Astro report as a JSON endpoint.

Astrology here is informational context only (Panchang, Rahu Kaal, sidereal
planetary positions) - it never decides a BUY/SELL signal by itself. See
vedic_astro_report.py's own docstring.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

import vedic_astro_report

router = APIRouter(prefix="/api/vedic")

_cache: dict[str, tuple[str, dict]] = {}  # symbol -> (date, report)


@router.get("/report")
def report(refresh: bool = False, symbol: str = "NIFTY"):
    symbol = symbol.upper()
    today = datetime.now(timezone.utc).date().isoformat()
    cached = _cache.get(symbol)
    if refresh or not cached or cached[0] != today:
        try:
            _cache[symbol] = (today, vedic_astro_report.generate_report(symbol=symbol))
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(502, f"Could not generate the Vedic Astro report: {e}")
    return _cache[symbol][1]

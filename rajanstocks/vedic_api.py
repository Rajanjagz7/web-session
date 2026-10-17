"""Exposes the Daily NIFTY 50 Vedic Astro report as a JSON endpoint.

Astrology here is informational context only (Panchang, Rahu Kaal, sidereal
planetary positions) - it never decides a BUY/SELL signal by itself. See
vedic_astro_report.py's own docstring.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

import vedic_astro_report

router = APIRouter(prefix="/api/vedic")

_cache = {"date": None, "report": None}


@router.get("/report")
def report(refresh: bool = False):
    today = datetime.now(timezone.utc).date().isoformat()
    if refresh or _cache["date"] != today:
        try:
            _cache["report"] = vedic_astro_report.generate_report()
            _cache["date"] = today
        except Exception as e:
            raise HTTPException(502, f"Could not generate the Vedic Astro report: {e}")
    return _cache["report"]

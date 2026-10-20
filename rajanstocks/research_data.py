"""Read-only data proxy for offline backtests (GitHub Actions cannot use the Upstox token or reach NSE directly).

  /api/research/expired/expiries?symbol=NIFTY           Upstox expired-instrument expiry dates
  /api/research/expired/contracts?symbol=NIFTY&expiry=  option contracts of a past expiry
  /api/research/expired/candles?key=...&interval=5minute&frm=&to=   candles of an expired contract
  /api/research/bhav?date=YYYY-MM-DD&symbols=NIFTY,BANKNIFTY        NSE F&O bhavcopy rows (options only) for one day
Responses are cached in Upstash; nothing here places orders or changes state.
"""
import csv
import io
import re
import zipfile
from datetime import date

import shared_cache
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/research")


def _up():
    from nse_service import nse_service
    return nse_service.upstox


def _cache(key, ttl, fn):
    hit = shared_cache.get(key)
    if hit is not None:
        return hit
    val = fn()
    shared_cache.set(key, val, ttl)
    return val


@router.get("/expired/expiries")
def expired_expiries(symbol: str = "NIFTY"):
    up = _up()
    key, _ = up._resolve_underlying(symbol.upper())
    try:
        return _cache(f"rx:exp:{key}", 6 * 3600, lambda: up._get(f"{up.BASE_V2}/expired-instruments/expiries", params={"instrument_key": key}, timeout=15))
    except Exception as e:
        raise HTTPException(502, f"expiries failed: {str(e)[:300]}")


@router.get("/expired/contracts")
def expired_contracts(symbol: str = "NIFTY", expiry: str = ""):
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", expiry):
        raise HTTPException(400, "expiry=YYYY-MM-DD")
    up = _up()
    key, _ = up._resolve_underlying(symbol.upper())
    try:
        return _cache(f"rx:oc:{key}:{expiry}", 30 * 86400, lambda: up._get(f"{up.BASE_V2}/expired-instruments/option/contract",
                                                                         params={"instrument_key": key, "expiry_date": expiry}, timeout=20))
    except Exception as e:
        raise HTTPException(502, f"contracts failed: {str(e)[:300]}")


@router.get("/expired/candles")
def expired_candles(key: str, interval: str = "5minute", frm: str = "", to: str = ""):
    if interval not in ("1minute", "3minute", "5minute", "15minute", "30minute", "day"):
        raise HTTPException(400, "bad interval")
    if not (re.match(r"^\d{4}-\d{2}-\d{2}$", frm) and re.match(r"^\d{4}-\d{2}-\d{2}$", to)):
        raise HTTPException(400, "frm/to=YYYY-MM-DD")
    up = _up()
    from urllib.parse import quote
    try:
        return up._get(f"{up.BASE_V2}/expired-instruments/historical-candle/{quote(key, safe='')}/{interval}/{to}/{frm}", timeout=20)
    except Exception as e:
        raise HTTPException(502, f"candles failed: {str(e)[:300]}")


@router.get("/bhav")
def bhav(date_: str = "", symbols: str = "NIFTY,BANKNIFTY,FINNIFTY,MIDCPNIFTY"):
    d = date_ or ""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        raise HTTPException(400, "date_=YYYY-MM-DD")
    want = {s.strip().upper() for s in symbols.split(",") if s.strip()}

    def fetch():
        from nse_service import nse_service
        url = f"https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{d.replace('-', '')}_F_0000.csv.zip"
        r = nse_service.session.get(url, timeout=20)
        if r.status_code == 404:
            return {"date": d, "rows": [], "missing": True}
        r.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(r.content))
        txt = z.read(z.namelist()[0]).decode("utf-8", "ignore")
        rows = []
        for row in csv.DictReader(io.StringIO(txt)):
            if row.get("FinInstrmTp") not in ("IDO", "STO") or (want and row.get("TckrSymb") not in want):
                continue
            rows.append([row["TckrSymb"], row["XpryDt"], float(row["StrkPric"] or 0), row["OptnTp"], float(row["OpnPric"] or 0),
                         float(row["HghPric"] or 0), float(row["LwPric"] or 0), float(row["ClsPric"] or 0),
                         float(row.get("PrvsClsgPric") or 0), float(row.get("UndrlygPric") or 0), int(float(row.get("TtlTradgVol") or 0))])
        return {"date": d, "cols": ["sym", "expiry", "strike", "type", "open", "high", "low", "close", "prevClose", "spot", "vol"], "rows": rows}
    try:
        return _cache(f"rx:bhav:{d}:{','.join(sorted(want))}", 60 * 86400, fetch)
    except Exception as e:
        raise HTTPException(502, f"bhav failed: {str(e)[:300]}")


@router.get("/candles")
def stock_candles(symbol: str, frm: str, to: str, interval: str = "1"):
    """Intraday candles of a stock / index for a date range (Upstox v3; 1-minute ranges up to one month)."""
    if interval not in ("1", "3", "5", "15"):
        raise HTTPException(400, "interval 1/3/5/15")
    if not (re.match(r"^\d{4}-\d{2}-\d{2}$", frm) and re.match(r"^\d{4}-\d{2}-\d{2}$", to)):
        raise HTTPException(400, "frm/to=YYYY-MM-DD")
    up = _up()
    key, _ = up._resolve_underlying(symbol.upper())
    try:
        rows = up.fetch_historical_candles(key, "minutes", interval, to, frm)
    except Exception as e:
        raise HTTPException(502, f"candles failed: {str(e)[:300]}")
    return {"symbol": symbol.upper(), "candles": [[c["time"], c["open"], c["high"], c["low"], c["close"], c.get("volume", 0)] for c in rows]}

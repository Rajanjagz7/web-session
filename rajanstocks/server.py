import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import donchian
import ha_dancing_trend
import heikin_ashi
import indicators
import market_news
import quantum_matrix
import stock_scanner
import rajan_pavan_indicators as rajan_pavan
import scan_engine
import trade_predictor
import market_api
import bar_source
import strategies_api
import ut_bot
from data_store import INDEX_SYMBOLS, live_row_to_record, store
from nse_service import TOP_FO_STOCKS, nse_service

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Bumped on every deploy so the frontend's update-check banner can detect a
# newer build is live and prompt the user to refresh instead of silently
# running stale cached JS.
APP_VERSION = "2026.10.14-merged"

app = FastAPI(title="Bhavcopy & Live Option Scanner")


@app.on_event("startup")
def _warm_on_start():
    import threading
    threading.Timer(3.0, market_api.warm_picks).start()
    push_signals.start_watcher()
    auto_trader.start_watcher()

app.include_router(market_api.router)
app.include_router(strategies_api.router)
import push_api  # noqa: E402
app.include_router(push_api.router)
import push_signals  # noqa: E402
app.include_router(push_signals.router)
import backtest  # noqa: E402
app.include_router(backtest.router)
import auto_trader  # noqa: E402
app.include_router(auto_trader.router)
import stocks_api  # noqa: E402
app.include_router(stocks_api.router)
import vedic_api  # noqa: E402
app.include_router(vedic_api.router)
import ipo_funds  # noqa: E402
app.include_router(ipo_funds.router)
import gods_eye_api  # noqa: E402
app.include_router(gods_eye_api.router)
import gods_eye_board  # noqa: E402
app.include_router(gods_eye_board.router)
import research_data  # noqa: E402
app.include_router(research_data.router)

@app.middleware("http")
async def _no_stale_assets(request, call_next):
    """HTML / JS / CSS / manifest are revalidated on every load, so a phone never keeps running an old build."""
    resp = await call_next(request)
    p = request.url.path
    if p == "/" or p.endswith((".html", ".js", ".css", ".webmanifest")) or p.startswith("/static/"):
        resp.headers["Cache-Control"] = "no-cache, must-revalidate"
    return resp


app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/sw.js")
def service_worker():
    return FileResponse(os.path.join(STATIC_DIR, "sw.js"), media_type="application/javascript",
                        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"})


@app.get("/manifest.webmanifest")
def web_manifest():
    return FileResponse(os.path.join(STATIC_DIR, "manifest.webmanifest"), media_type="application/manifest+json")


_ICON_CACHE = {"Cache-Control": "public, max-age=604800"}   # 7 days - these only change on an explicit icon edit


@app.get("/icon-192.png")
def app_icon():
    return FileResponse(os.path.join(STATIC_DIR, "icon-192.png"), media_type="image/png", headers=_ICON_CACHE)


@app.get("/favicon.svg")
def favicon_svg():
    return FileResponse(os.path.join(STATIC_DIR, "favicon.svg"), media_type="image/svg+xml", headers=_ICON_CACHE)


@app.get("/favicon-32.png")
def favicon_png():
    return FileResponse(os.path.join(STATIC_DIR, "favicon-32.png"), media_type="image/png", headers=_ICON_CACHE)


@app.get("/icon-512.png")
def icon_512():
    return FileResponse(os.path.join(STATIC_DIR, "icon-512.png"), media_type="image/png", headers=_ICON_CACHE)


@app.get("/favicon.ico")
def favicon():
    return FileResponse(os.path.join(STATIC_DIR, "favicon.svg"), media_type="image/svg+xml", headers=_ICON_CACHE)


_IST = timezone(timedelta(hours=5, minutes=30))


@app.get("/api/cache-version")
def cache_version():
    """Drives the client's auto cache-clear: a version string that flips exactly
    twice a day (08:30 IST, before market open; 15:45 IST, after market close) so
    stale cached pages/assets get dropped around those two boundaries without
    needing a cron job - it's just a pure function of the current IST time."""
    now = datetime.now(_IST)
    mins = now.hour * 60 + now.minute
    bucket = "pre" if mins < 8 * 60 + 30 else "open" if mins < 15 * 60 + 45 else "post"
    return {"version": f"{now.date().isoformat()}-{bucket}"}


@app.get("/api/status")
def api_status():
    status = nse_service.get_market_status()
    status["todayDateLoaded"] = store.today_date
    status["prevDateLoaded"] = store.prev_date
    status["totalLoaded"] = len(store.today_rows)
    status["appVersion"] = APP_VERSION
    return status


@app.get("/api/version")
def api_version():
    return {"version": APP_VERSION}


@app.get("/api/news")
def api_news(limit: int = 40):
    limit = max(5, min(limit, 100))
    try:
        return market_news.get_market_news(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/api/symbols")
def api_symbols():
    if store.is_loaded():
        symbols = sorted(set(store.symbols()) | INDEX_SYMBOLS)
    else:
        symbols = sorted(set(TOP_FO_STOCKS) | INDEX_SYMBOLS)
    return {"symbols": symbols}


@app.post("/api/scan")
def api_scan(filters: dict = Body(default={})):
    """Live market scan — fetches NSE option chains in parallel for all requested symbols."""
    sym_filter = filters.get("symSelect", "__ALL__") or "__ALL__"
    inst_idx = bool(filters.get("instIdx", True))
    inst_stk = bool(filters.get("instStk", True))

    try:
        live_rows, trade_date, errors = nse_service.scan_live_all(
            inst_idx=inst_idx,
            inst_stk=inst_stk,
            sym_filter=sym_filter,
            max_stocks=40,
        )
    except Exception as exc:
        return {
            "results": [], "totalContracts": 0, "statMatch": 0,
            "statOL": 0, "statOH": 0, "poolSize": 0,
            "storeTotal": 0, "todayDate": "",
            "error": f"Live scan failed: {exc}",
        }

    if not live_rows and errors:
        return {
            "results": [], "totalContracts": 0, "statMatch": 0,
            "statOL": 0, "statOH": 0, "poolSize": 0,
            "storeTotal": 0, "todayDate": trade_date,
            "error": f"NSE data unavailable: {errors[0]}",
        }

    baseline_lookup = store.today_lookup()
    records = [live_row_to_record(r, baseline_lookup) for r in live_rows]

    result = scan_engine.scan(records, filters)
    result["storeTotal"] = len(live_rows)
    result["todayDate"] = trade_date
    result["liveTimestamp"] = datetime.now().strftime("%H:%M:%S")
    if errors:
        result["partialErrors"] = len(errors)
    return result


@app.post("/api/fetch-latest")
def api_fetch_latest(force: bool = False):
    # Bhavcopy is no longer used — this endpoint is kept for backward compatibility.
    # It warms the NSE session so subsequent live scans have fresh cookies.
    try:
        nse_service.refresh_cookies(force=True)
    except Exception:
        pass
    return {"success": True, "totalContracts": 0, "todayDate": ""}


@app.post("/api/admin/bhavcopy-refresh")
def api_bhavcopy_refresh():
    """Manual-only: pulls the latest NSE F&O bhavcopy and reloads the option-OI
    baseline store. Nothing calls this automatically - the old cron/upload path
    was dead (bhav_fetch.py had zero importers, store was always empty in
    production). Use this only if a feature that reads store.today_lookup()
    (live-scan OI baselines) actually needs it."""
    import bhav_fetch
    try:
        path, trade_date = bhav_fetch.fetch_latest_bhavcopy(nse_service)
    except Exception as exc:
        raise HTTPException(502, f"Bhavcopy fetch failed: {exc}")
    store.reload()
    return {"loaded": store.is_loaded(), "todayDate": store.today_date, "prevDate": store.prev_date, "rows": len(store.today_rows), "file": path}


@app.get("/api/live/scan")
def api_live_scan(
    symbol: str = "NIFTY",
    optType: str = "BOTH",
    lowOn: bool = True,
    lowFrom: float = 0,
    lowTo: float = 0,
    prevOn: bool = True,
    prevFrom: float = 0,
    prevTo: float = 0,
    tol: float = 0,
    minOi: float = 0,
    includeUntraded: bool = False,
    showMode: str = "matches",
    cheapOn: bool = False,
    cheapFrom: float = 0.80,
    cheapTo: float = 1.50,
):
    try:
        live_rows, _trade_date = nse_service.get_live_records(symbol)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch live chain from NSE: {exc}")

    baseline_lookup = store.today_lookup()
    records = [live_row_to_record(r, baseline_lookup) for r in live_rows]

    filters = {
        "symSelect": "__ALL__",
        "instIdx": True,
        "instStk": True,
        "optType": optType,
        "expSelect": "all",
        "lowOn": lowOn,
        "lowFrom": lowFrom,
        "lowTo": lowTo,
        "prevOn": prevOn,
        "prevFrom": prevFrom,
        "prevTo": prevTo,
        "tol": tol,
        "minOi": minOi,
        "includeUntraded": includeUntraded,
        "showMode": showMode,
        "cheapOn": cheapOn,
        "cheapFrom": cheapFrom,
        "cheapTo": cheapTo,
    }
    result = scan_engine.scan(records, filters)
    result["liveTimestamp"] = datetime.now().strftime("%H:%M:%S")
    return result


@app.get("/api/indicators/oh-ol")
def api_indicator_oh_ol(
    symbol: str = "NIFTY",
    sideMode: str = "auto",
    idxTol: float = 0,
    pts: float = 10,
    rule: str = "open_or_prev",
    pcTol: float = 0,
    onlyQualifying: bool = True,
    thr: float = 71,
    dirMode: str = "follow",
    vixLow: float = 14,
    vixHigh: float = 20,
):
    try:
        result = indicators.oh_ol_setup(symbol, {
            "sideMode": sideMode,
            "idxTol": idxTol,
            "pts": pts,
            "rule": rule,
            "pcTol": pcTol,
            "onlyQualifying": onlyQualifying,
            "thr": thr,
            "dirMode": dirMode,
            "vixLow": vixLow,
            "vixHigh": vixHigh,
        })
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    result["liveTimestamp"] = datetime.now().strftime("%H:%M:%S")
    return result


@app.get("/api/indicators/premium-scanner")
def api_indicator_premium_scanner(
    expSel: str = "both",
    premSrc: str = "prevclose",
    premFrom: float = 300,
    premTo: float = 349,
    lowFrom: float = 52,
    lowTo: float = 58,
    div1: float = 8,
    div2: float = 6.5,
    lowMode: str = "fixed",
    onlyMatches: bool = False,
    thr: float = 71,
    dirMode: str = "follow",
):
    try:
        result = indicators.premium_scanner({
            "expSel": expSel,
            "premSrc": premSrc,
            "premFrom": premFrom,
            "premTo": premTo,
            "lowFrom": lowFrom,
            "lowTo": lowTo,
            "div1": div1,
            "div2": div2,
            "lowMode": lowMode,
            "onlyMatches": onlyMatches,
            "thr": thr,
            "dirMode": dirMode,
        })
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    result["liveTimestamp"] = datetime.now().strftime("%H:%M:%S")
    return result


@app.get("/api/indicators/ut-bot")
def api_indicator_ut_bot(
    symbol: str = "NIFTY",
    keyValue: float = 1.0,
    atrPeriod: int = 10,
    lookbackDays: int = 60,
):
    lookbackDays = max(30, min(lookbackDays, 180))
    atrPeriod = max(2, min(atrPeriod, 50))
    try:
        result = ut_bot.ut_bot_scan(
            symbol, key_value=keyValue, atr_period=atrPeriod, lookback_days=lookbackDays
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    result["liveTimestamp"] = datetime.now().strftime("%H:%M:%S")
    return result


@app.get("/api/cron/morning-refresh")
def api_cron_morning_refresh():
    """Hit automatically by Vercel Cron at market open (see vercel.json — two
    entries call this, 9:16 and 9:21 IST Mon-Fri, so a transient NSE hiccup on
    the first run gets a same-morning retry 5 minutes later). Warms the NSE
    session/cookies so the first real user request of the day doesn't pay
    that cold-start cost, and snapshots each index's opening price. Idempotent
    — re-running it just re-fetches the same day's data. There's no
    notification channel wired up — it just runs server-side; check Vercel's
    Cron Jobs dashboard to confirm it fired."""
    summary = {"ranAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    try:
        nse_service.refresh_cookies(force=True)
        all_indices = nse_service.get_all_indices()
        snapshot = {}
        for sym, name in indicators.INDEX_DISPLAY_NAME.items():
            row = all_indices.get(name)
            if row:
                snapshot[sym] = {
                    "open": row.get("open"),
                    "high": row.get("high"),
                    "low": row.get("low"),
                    "last": row.get("last"),
                }
        summary["indexSnapshot"] = snapshot
        summary["vix"] = indicators.get_india_vix()
    except Exception as exc:
        summary["liveWarmup"] = {"status": "failed", "error": str(exc)}

    return summary


@app.get("/api/indicators/donchian")
def api_indicator_donchian(
    symbol: str = "NIFTY",
    length: int = 20,
    lookbackDays: int = 120,
):
    length = max(2, min(length, 100))
    lookbackDays = max(30, min(lookbackDays, 365))
    try:
        result = donchian.donchian_scan(symbol, length=length, lookback_days=lookbackDays)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    result["liveTimestamp"] = datetime.now().strftime("%H:%M:%S")
    return result


@app.get("/api/indicators/heikin-ashi-channel")
def api_indicator_heikin_ashi_channel(
    symbol: str = "NIFTY",
    length: int = 20,
    mult: float = 2.0,
    channelType: str = "bollinger",
):
    length = max(2, min(length, 100))
    mult = max(0.5, min(mult, 5.0))
    try:
        result = heikin_ashi.dancing_channel_scan(symbol, length=length, mult=mult, channel_type=channelType)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    result["liveTimestamp"] = datetime.now().strftime("%H:%M:%S")
    return result


@app.get("/api/indicators/ha-dancing-trend")
def api_indicator_ha_dancing_trend(
    symbol: str = "NIFTY",
    emaFastLen: int = 9,
    emaSlowLen: int = 21,
    channelLen: int = 20,
    atrLen: int = 14,
    atrMult: float = 1.5,
    rr: float = 2.0,
    adxLen: int = 14,
    adxMin: float = 18.0,
    useDI: bool = False,
    reverse: bool = True,
):
    emaFastLen = max(2, min(emaFastLen, 100))
    emaSlowLen = max(2, min(emaSlowLen, 200))
    channelLen = max(2, min(channelLen, 100))
    atrLen = max(2, min(atrLen, 50))
    atrMult = max(0.1, min(atrMult, 5.0))
    rr = max(0.5, min(rr, 10.0))
    adxLen = max(2, min(adxLen, 50))
    adxMin = max(0.0, min(adxMin, 60.0))
    try:
        result = ha_dancing_trend.ha_dancing_trend_scan(
            symbol,
            ema_fast_len=emaFastLen, ema_slow_len=emaSlowLen, channel_len=channelLen,
            atr_len=atrLen, atr_mult=atrMult, rr=rr,
            adx_len=adxLen, adx_min=adxMin, use_di=useDI, reverse=reverse,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    result["liveTimestamp"] = datetime.now().strftime("%H:%M:%S")
    return result


@app.get("/api/indicators/trade-predictor")
def api_indicator_trade_predictor(
    symbol: str = "NIFTY",
    atrLength: int = 10,
    factor: float = 1.5,
    emaLength: int = 200,
    useTrendFilter: bool = True,
    slMultiplier: float = 1.5,
    tpMultiplier: float = 2.0,
    lookbackDays: int = 180,
):
    atrLength = max(2, min(atrLength, 50))
    emaLength = max(5, min(emaLength, 300))
    lookbackDays = max(30, min(lookbackDays, 365))
    try:
        result = trade_predictor.trade_predictor_scan(
            symbol, atr_length=atrLength, factor=factor, ema_length=emaLength,
            use_trend_filter=useTrendFilter, sl_mult=slMultiplier, tp_mult=tpMultiplier,
            lookback_days=lookbackDays,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    result["liveTimestamp"] = datetime.now().strftime("%H:%M:%S")
    return result


@app.get("/api/indicators/quantum-matrix")
def api_indicator_quantum_matrix(
    symbol: str = "NIFTY",
    keyValue: float = 1.0,
    atrPeriod: int = 10,
    lookback: int = 20,
    lookbackDays: int = 120,
):
    lookback = max(5, min(lookback, 100))
    lookbackDays = max(30, min(lookbackDays, 365))
    try:
        result = quantum_matrix.quantum_matrix_scan(
            symbol, key_value=keyValue, atr_period=atrPeriod, lookback=lookback, lookback_days=lookbackDays
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    result["liveTimestamp"] = datetime.now().strftime("%H:%M:%S")
    return result


@app.get("/api/indicators/rajan-pavan")
def api_indicator_rajan_pavan(
    key: str,
    symbol: str = "NIFTY",
    lookbackDays: Optional[int] = None,
    emaLength: Optional[int] = None,
    trendLength: Optional[int] = None,
    fastLength: Optional[int] = None,
    slowLength: Optional[int] = None,
    pivotLeft: Optional[int] = None,
    pivotRight: Optional[int] = None,
    useStructure: Optional[bool] = None,
    maxBodyPct: Optional[float] = None,
    minLowerWickBody: Optional[float] = None,
    maxUpperWickBody: Optional[float] = None,
    supportDistancePct: Optional[float] = None,
    supportTolerancePct: Optional[float] = None,
    useTrend: Optional[bool] = None,
    useVolume: Optional[bool] = None,
    volumeLength: Optional[int] = None,
    volumeMultiplier: Optional[float] = None,
    signalMode: Optional[str] = None,
    rangeLength: Optional[int] = None,
    emaDistancePct: Optional[float] = None,
    volumeFactor: Optional[float] = None,
    lookback: Optional[int] = None,
    useEMA: Optional[bool] = None,
    useRSI: Optional[bool] = None,
    rsiLength: Optional[int] = None,
    rsiMax: Optional[float] = None,
    useMACD: Optional[bool] = None,
    useSMA50: Optional[bool] = None,
    useWeeklyTrend: Optional[bool] = None,
    weeklyEmaLength: Optional[int] = None,
    priceMovePct: Optional[float] = None,
    nrLength: Optional[int] = None,
    nearHighPct: Optional[float] = None,
    consolidationLength: Optional[int] = None,
    minimumClose: Optional[float] = None,
    stAtrLength: Optional[int] = None,
    stFactor: Optional[float] = None,
    rsiMinimum: Optional[float] = None,
    bigVolumeMultiplier: Optional[float] = None,
    lowVolumeMultiplier: Optional[float] = None,
    supportLength: Optional[int] = None,
    contractionBars: Optional[int] = None,
    vixDivisor: Optional[float] = None,
    supportLookback: Optional[int] = None,
):
    if key not in rajan_pavan.RAJAN_PAVAN_KEYS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown Rajan/Pavan indicator key '{key}' — supported: {', '.join(rajan_pavan.RAJAN_PAVAN_KEYS)}",
        )
    if symbol.upper() not in rajan_pavan.ALLOWED_SYMBOLS and not bar_source.supports(symbol):
        raise HTTPException(
            status_code=400,
            detail=f"Rajan/Pavan indicators support {', '.join(rajan_pavan.ALLOWED_SYMBOLS)} only",
        )

    raw = {
        "lookbackDays": lookbackDays, "emaLength": emaLength, "trendLength": trendLength,
        "fastLength": fastLength, "slowLength": slowLength, "pivotLeft": pivotLeft, "pivotRight": pivotRight,
        "useStructure": useStructure, "maxBodyPct": maxBodyPct, "minLowerWickBody": minLowerWickBody,
        "maxUpperWickBody": maxUpperWickBody, "supportDistancePct": supportDistancePct,
        "supportTolerancePct": supportTolerancePct, "useTrend": useTrend, "useVolume": useVolume,
        "volumeLength": volumeLength, "volumeMultiplier": volumeMultiplier, "signalMode": signalMode,
        "rangeLength": rangeLength, "emaDistancePct": emaDistancePct, "volumeFactor": volumeFactor,
        "lookback": lookback, "useEMA": useEMA, "useRSI": useRSI, "rsiLength": rsiLength, "rsiMax": rsiMax,
        "useMACD": useMACD, "useSMA50": useSMA50, "useWeeklyTrend": useWeeklyTrend,
        "weeklyEmaLength": weeklyEmaLength, "priceMovePct": priceMovePct, "nrLength": nrLength,
        "nearHighPct": nearHighPct, "consolidationLength": consolidationLength, "minimumClose": minimumClose,
        "stAtrLength": stAtrLength, "stFactor": stFactor, "rsiMinimum": rsiMinimum,
        "bigVolumeMultiplier": bigVolumeMultiplier, "lowVolumeMultiplier": lowVolumeMultiplier,
        "supportLength": supportLength, "contractionBars": contractionBars, "vixDivisor": vixDivisor,
        "supportLookback": supportLookback,
    }
    kwargs = rajan_pavan.build_kwargs(key, raw)
    try:
        result = rajan_pavan.RAJAN_PAVAN_KEYS[key](symbol, **kwargs)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    result["key"] = key
    result["liveTimestamp"] = datetime.now().strftime("%H:%M:%S")
    return result


@app.get("/api/stocks/block-deal")
def api_stocks_block_deal(
    volMult: float = 3.0,
    avgLength: int = 20,
    onlyHits: bool = False,
    maxRows: int = 25,
):
    volMult = max(1.0, min(volMult, 20.0))
    avgLength = max(5, min(avgLength, 100))
    maxRows = max(5, min(maxRows, 50))
    try:
        result = stock_scanner.block_deal_scan(
            vol_mult=volMult, avg_length=avgLength, only_hits=onlyHits, max_rows=maxRows,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    result["liveTimestamp"] = datetime.now().strftime("%H:%M:%S")
    return result


@app.get("/api/stocks/high-volume")
def api_stocks_high_volume(
    avgLength: int = 20,
    maxRows: int = 25,
):
    avgLength = max(5, min(avgLength, 100))
    maxRows = max(5, min(maxRows, 50))
    try:
        result = stock_scanner.high_volume_scan(avg_length=avgLength, max_rows=maxRows)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    result["liveTimestamp"] = datetime.now().strftime("%H:%M:%S")
    return result


@app.get("/api/cron/weekly-cleanup")
def api_cron_weekly_cleanup():
    """Cron endpoint kept for Vercel scheduling compatibility. Warms NSE cookies."""
    try:
        nse_service.refresh_cookies(force=True)
    except Exception:
        pass
    return {"status": "ok", "ranAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

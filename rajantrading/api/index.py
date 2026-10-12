import os
import concurrent.futures
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

def _load_env_file():
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", ".env"),
        os.path.join(os.path.dirname(__file__), "..", ".env.local"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.getcwd(), ".env.local"),
        ".env",
        ".env.local"
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'").strip('"')
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass

_load_env_file()

from .nse_service import nse_service, now_ist_iso, get_stock_picks as _get_stock_picks, TOP_FO_STOCKS_FALLBACK
from .upstox_service import upstox_service
from . import market_api
from . import push_api
from . import stocks_api

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        print("[STARTUP] Auto-fetching latest Bhavcopy from NSE...")
        res = nse_service.fetch_latest_bhavcopy(force_refresh=False)
        print(f"[STARTUP] Successfully loaded {res['totalContracts']} contracts for {res['todayDate']}.")
    except Exception as e:
        print(f"[STARTUP] Notice: Startup fetch: {e}")
    yield

app = FastAPI(title="NSE Bhavcopy & Live Option Scanner API", version="2.0.0", lifespan=lifespan)
app.include_router(market_api.router)
app.include_router(push_api.router)
app.include_router(stocks_api.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    symSelect: Optional[str] = "__ALL__"
    instIdx: Optional[bool] = True
    instStk: Optional[bool] = True
    optType: Optional[str] = "BOTH"
    expSelect: Optional[str] = "nearest"
    lowOn: Optional[bool] = True
    lowFrom: Optional[float] = 5.80
    lowTo: Optional[float] = 8.45
    prevOn: Optional[bool] = True
    prevFrom: Optional[float] = 38.0
    prevTo: Optional[float] = 48.0
    tol: Optional[float] = 0.0
    minOi: Optional[float] = 0.0
    includeUntraded: Optional[bool] = False
    showMode: Optional[str] = "matches"
    indicator: Optional[str] = None

@app.get("/api/status")
def get_status():
    status = nse_service.get_market_status()
    if isinstance(status, dict):
        status["version"] = "2.2.0"
        status["buildTime"] = "2026-09-27T07:30:00Z"
    return status

@app.get("/api/upstox/status")
def get_upstox_status():
    """Authenticated Upstox REST integration status."""
    return upstox_service.health()

@app.get("/api/news")
def get_news(limit: int = 40, refresh: bool = False):
    from . import market_news
    return market_news.get_market_news(limit=limit, force_refresh=refresh)


@app.get("/api/market/global")
def get_market_global():
    return market_api.global_markets_legacy()


@app.get("/api/indices/pulse")
def get_indices_pulse():
    try:
        return nse_service.get_indices_pulse()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quotes/fast")
def get_quotes_fast():
    try:
        status = nse_service.get_market_status()
        indices = status.get("indices", {})
        quotes = {
            sym: {"last": v["last"], "change": v["change"], "pct": v["pct"]}
            for sym, v in indices.items()
            if isinstance(v, dict) and "last" in v
        }
        return {"configured": bool(quotes), "quotes": quotes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fetch-latest")
def fetch_latest_get(force: bool = False):
    return fetch_latest_post(force)

@app.post("/api/fetch-latest")
def fetch_latest_post(force: bool = False):
    try:
        res = nse_service.fetch_latest_bhavcopy(force_refresh=force)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/symbols")
def get_symbols():
    detailed = nse_service.get_symbols_detailed()
    existing = {s["symbol"] for s in detailed}
    # Always include the top F&O stocks even if bhavcopy only loaded index chains
    for stock in TOP_FO_STOCKS_FALLBACK:
        if stock not in existing:
            detailed.append({"symbol": stock, "instr": "Stock"})
    detailed = sorted(detailed, key=lambda x: x["symbol"])
    symbols = sorted({s["symbol"] for s in detailed})
    return {"symbols": symbols, "detailed": detailed}

@app.get("/api/chain")
def get_chain(symbol: str = "NIFTY", expiry: Optional[str] = None, indicator: Optional[str] = None):
    try:
        res = nse_service.get_option_chain_for_symbol(symbol=symbol, expiry=expiry, indicator=indicator)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chain/summary")
def get_chain_summary(symbols: str = "NIFTY,BANKNIFTY,FINNIFTY,MIDCPNIFTY,SENSEX", indicator: Optional[str] = None):
    try:
        sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        res = nse_service.get_option_chain_summary(symbols=sym_list, indicator=indicator)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock-picks")
def get_stock_picks_route(force_refresh: bool = False):
    try:
        res = _get_stock_picks(force_refresh=force_refresh)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scan")
def scan_bhavcopy(req: ScanRequest):
    filters = req.model_dump()
    sym = filters.get("symSelect", "__ALL__")
    inst_stk = filters.get("instStk", True)
    inst_idx = filters.get("instIdx", True)

    # For a specific symbol, always fetch a fresh Upstox chain (live OHLC + OI)
    if sym != "__ALL__" and upstox_service.is_configured():
        try:
            live = upstox_service.fetch_option_chain(sym)
            if live and live.get("rows"):
                result = nse_service.scan(live["rows"], filters)
                result["todayDate"] = datetime.now().strftime("%d-%m-%Y")
                result["source"] = "upstox_live"
                return result
        except Exception as e:
            print(f"[Scan] Upstox live scan failed for {sym}: {e}")

    # For ALL symbols: start with index chains (from startup or live fetch)
    if not nse_service.today_rows:
        try:
            nse_service.fetch_latest_bhavcopy()
        except Exception as e:
            print(f"[Scan] Bhavcopy unavailable: {e}")
        if not nse_service.today_rows:
            # No index data – try live Upstox index fetch directly
            if upstox_service.is_configured():
                try:
                    live_rows = nse_service._fetch_bhavcopy_from_upstox()
                    if live_rows:
                        nse_service.today_rows = live_rows
                except Exception as e2:
                    print(f"[Scan] Live index fetch failed: {e2}")
            if not nse_service.today_rows:
                err_msg = "Live data unavailable – Upstox token may have expired. Please refresh your token."
                return JSONResponse(content={
                    "results": [], "totalContracts": 0, "resultCount": 0,
                    "statMatch": 0, "statOL": 0, "statOH": 0,
                    "error": err_msg, "source": "error"
                })

    scan_rows = list(nse_service.today_rows)  # index chains

    # When stocks are requested, fetch top F&O stock chains from Upstox in parallel
    if inst_stk and upstox_service.is_configured():
        top_stocks = TOP_FO_STOCKS_FALLBACK[:25]  # top 25 most liquid
        def _fetch_chain(s):
            try:
                chain = upstox_service.fetch_option_chain(s)
                return chain.get("rows", []) if chain else []
            except Exception:
                return []
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as ex:
            for rows in ex.map(_fetch_chain, top_stocks):
                scan_rows.extend(rows)

    result = nse_service.scan(scan_rows, filters)
    result["todayDate"] = nse_service.today_date or datetime.now().strftime("%d-%m-%Y")
    result["prevDate"] = nse_service.prev_date
    result["source"] = "upstox_live"
    return result

class BatchScanRequest(ScanRequest):
    symbols: List[str] = []

@app.post("/api/scan/batch")
def scan_batch(req: BatchScanRequest):
    """Scan an explicit list of underlyings (used by the scanner to cover every F&O stock in small batches)."""
    filters = req.model_dump()
    syms = [x.upper() for x in (filters.pop("symbols", None) or [])][:20]
    filters["symSelect"] = "__ALL__"
    rows, failed, scanned = [], [], 0
    if not upstox_service.is_configured():
        return JSONResponse(content={"results": [], "totalContracts": 0, "resultCount": 0, "failed": syms, "scanned": 0,
                                     "error": "Live data unavailable - Upstox token missing or expired."})
    def _one(sym):
        try:
            chain = upstox_service.fetch_option_chain(sym)
            return sym, (chain.get("rows") if chain else None)
        except Exception:
            return sym, None
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for sym, r in ex.map(_one, syms):
            if r:
                rows.extend(r); scanned += 1
            else:
                failed.append(sym)
    result = nse_service.scan(rows, filters) if rows else {"results": [], "totalContracts": 0, "resultCount": 0}
    result["failed"] = failed
    result["scanned"] = scanned
    result["source"] = "upstox_live"
    return result

@app.get("/api/live/scan")
def live_scan(
    symbol: str = "NIFTY",
    expiry: Optional[str] = None,
    optType: str = "BOTH",
    lowOn: bool = True,
    lowFrom: float = 5.80,
    lowTo: float = 8.45,
    prevOn: bool = True,
    prevFrom: float = 38.0,
    prevTo: float = 48.0,
    tol: float = 0.0,
    minOi: float = 0.0,
    includeUntraded: bool = False,
    showMode: str = "matches",
    indicator: Optional[str] = None
):
    try:
        live_res = nse_service.fetch_live_option_chain(symbol=symbol, expiry=expiry)
        filters = {
            "symSelect": symbol.upper(),
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
            "indicator": indicator
        }
        scan_output = nse_service.scan(live_res["rows"], filters)
        scan_output["symbol"] = live_res["symbol"]
        scan_output["targetExpiry"] = live_res["targetExpiry"]
        scan_output["expiryDates"] = live_res["expiryDates"]
        scan_output["liveTimestamp"] = live_res["timestamp"]
        scan_output["provider"] = live_res.get("provider", "NSE")
        scan_output["dataMode"] = live_res.get("mode", "NSE")
        return scan_output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Live scan error: {str(e)}")

@app.get("/api/live/chain")
def get_live_chain(symbol: str = "NIFTY", expiry: Optional[str] = None):
    try:
        live_res = nse_service.fetch_live_option_chain(symbol=symbol, expiry=expiry)
        raw_rows = live_res.get("rows", [])
        if not raw_rows:
            return live_res

        strikes_map = {}
        spot = 0.0
        for r in raw_rows:
            if r.get("spot"):
                spot = float(r["spot"])
            k = float(r["strike"])
            if k not in strikes_map:
                strikes_map[k] = {"strike": k, "ce": None, "pe": None}
            opt_type = r["type"].upper()
            if opt_type == "CE":
                strikes_map[k]["ce"] = r
            elif opt_type == "PE":
                strikes_map[k]["pe"] = r

        sorted_strikes = sorted(strikes_map.keys())
        if spot <= 0 and sorted_strikes:
            spot = sorted_strikes[len(sorted_strikes) // 2]

        atm_strike = min(sorted_strikes, key=lambda x: abs(x - spot)) if sorted_strikes else 0
        atm_idx = sorted_strikes.index(atm_strike) if atm_strike in sorted_strikes else 0
        min_i = max(0, atm_idx - 18)
        max_i = min(len(sorted_strikes), atm_idx + 19)
        window_strikes = sorted_strikes[min_i:max_i]

        chain_table = [strikes_map[k] for k in window_strikes]

        total_ce_vol = sum((r["ce"]["vol"] if r["ce"] else 0) for r in chain_table)
        total_pe_vol = sum((r["pe"]["vol"] if r["pe"] else 0) for r in chain_table)
        tot_vol = total_ce_vol + total_pe_vol
        call_pct = round((total_ce_vol / tot_vol * 100), 1) if tot_vol > 0 else 50.0
        put_pct = round(100.0 - call_pct, 1)

        return {
            "symbol": live_res.get("symbol", symbol.upper()),
            "spot": spot,
            "atmStrike": atm_strike,
            "expiry": live_res.get("targetExpiry"),
            "allExpiries": live_res.get("expiryDates", []),
            "rows": chain_table,
            "totalContracts": len(raw_rows),
            "provider": live_res.get("provider", "Upstox"),
            "mode": live_res.get("mode", "REST"),
            "timestamp": live_res.get("timestamp"),
            "volumeShare": {
                "callVol": total_ce_vol,
                "putVol": total_pe_vol,
                "callPct": call_pct,
                "putPct": put_pct,
                "sentiment": "BULLISH" if call_pct >= 60 else ("BEARISH" if call_pct <= 40 else "NEUTRAL")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Live chain error: {str(e)}")

@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...), isToday: bool = Form(True)):
    try:
        content = (await file.read()).decode("utf-8", errors="ignore")
        count = nse_service.load_user_csv(content, is_today=isToday)
        return {
            "success": True,
            "filename": file.filename,
            "isToday": isToday,
            "contractsLoaded": count
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tv/status")
@app.get("/api/tv")
def tv_status(action: str = "status", symbol: str = "NSE:NIFTY"):
    return {
        "status": "online",
        "provider": "TradingView-API (@mathieuc/tradingview)",
        "gateway": "Node.js + Python Fallback",
        "symbol": symbol,
        "action": action,
        "chartUrl": f"https://in.tradingview.com/chart/?symbol={symbol}",
        "supportedActions": ["quote", "ta", "search", "status"],
        "version": "1.0.0"
    }

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
@app.api_route("/", methods=["GET", "HEAD"])
def serve_index():
    for fname in ["new_ui.html", "index.html"]:
        f = os.path.join(PUBLIC_DIR, fname)
        if os.path.exists(f):
            return FileResponse(f, media_type="text/html")
    return {"message": "NSE Option Scanner API running."}

if __name__ == "__main__":
    uvicorn.run("api.index:app", host="0.0.0.0", port=8000, reload=False)

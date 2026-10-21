import os
import threading
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import indicators
import market_api
import market_news
import shared_cache
import strategies_api
from nse_service import nse_service

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="Bhavcopy & Live Option Scanner")


@app.on_event("startup")
def _warm_on_start():
    threading.Timer(3.0, market_api.warm_picks).start()
    push_signals.start_watcher()
    auto_trader.start_watcher()
    if not os.environ.get("VERCEL"):
        threading.Timer(12.0, ipo_funds.warm_dashboard).start()

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
import observer_api  # noqa: E402
app.include_router(observer_api.router)
import stock_trader  # noqa: E402
app.include_router(stock_trader.router)

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
    build = (os.environ.get("VERCEL_GIT_COMMIT_SHA") or "")[:8]     # a new deploy also counts: open tabs reload onto it
    return {"version": f"{now.date().isoformat()}-{bucket}-{build}"}


@app.get("/api/news")
def api_news(limit: int = 40):
    limit = max(5, min(limit, 100))
    try:
        return market_news.get_market_news(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


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


@app.get("/api/cron/weekly-cleanup")
def api_cron_weekly_cleanup():
    """Weekly housekeeping (Vercel cron): drops stale disk-cache files and warms the NSE session."""
    try:
        nse_service.refresh_cookies(force=True)
    except Exception:
        pass
    return {"status": "ok", "cacheFilesRemoved": shared_cache.sweep(), "ranAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

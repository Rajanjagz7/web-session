# API audit - 20 Oct 2026

Method: every route was matched against the frontend (`static/*.js`, `static/index.html`), `vercel.json` cron entries,
README and tests, then called against a running server. Final sweep: every screen visited on desktop and phone width,
**0 failing API calls, 0 JavaScript errors**.

## Removed (no caller anywhere, legacy bhavcopy/NSE scanner)
| Route | Why |
|---|---|
| `GET /api/status`, `GET /api/version`, `GET /api/symbols` | Nothing called them (frontend uses `/api/cache-version`). |
| `POST /api/scan`, `GET /api/live/scan`, `POST /api/fetch-latest`, `POST /api/admin/bhavcopy-refresh` | Old NSE option-chain scanner. Replaced by `/api/m/daily-scan` and `/api/m/chain` (Upstox). |
| `GET /api/indicators/oh-ol`, `premium-scanner`, `ut-bot`, `donchian`, `heikin-ashi-channel`, `ha-dancing-trend`, `trade-predictor`, `quantum-matrix`, `rajan-pavan` | The Indicators screen uses `/api/m/strategy`. `premium-scanner` was also **broken** (502, needed a bhavcopy that is never loaded) and `rajan-pavan` needs a `key` nobody sends. |
| `GET /api/stocks/block-deal`, `GET /api/stocks/high-volume` | Duplicates of `stocks_api` routes, no caller. |

Dead code removed with them: `scan_engine.py`, `stock_scanner.py`, `bhav_fetch.py`, `live_row_to_record`, `parse_bhavcopy_text`,
`oh_ol_setup`, `premium_scanner`, `build_kwargs`, `parse_bool`, `parse_float`, `global_markets_legacy`, plus every unused
import / variable (`pyflakes` is clean on all modules).

## Kept but flagged
| Route | Status | Note |
|---|---|---|
| `GET /api/m/option-low-range` | working | Documented in README, no screen calls it yet. |
| `GET /api/m/budget` | working | Diagnostics. Now also reports Upstox calls per endpoint and per caller. |
| `GET /api/auto/preview` | working | Dry-run of the auto trader. Debug only. |
| `GET /api/push/key`, `/api/push/signals`, `/api/push/signals/preview` | working | Push diagnostics. `signals/preview` takes ~6 s. |
| `POST /api/auto/trade/{id}/exit|tsl|stop` | working | Called by the Journal with a built URL (looks unused to a text search). |
| `/api/v1/admin/*`, `/api/v1/evaluation/calibration` | working | God's Eye (pre-market) admin / report API, covered by `test_gods_eye.py`. |
| `GET /api/cron/morning-refresh`, `/api/cron/weekly-cleanup` | working | Vercel crons. They only warm NSE cookies, which nothing on the Upstox path needs - candidates to drop from `vercel.json`. `weekly-cleanup` now also sweeps the local cache. |

## Cold-start slowness
- `/api/ipo/dashboard` took ~7 s whenever its 15-minute cache expired. It now serves the last good copy at once (0.14 s, flagged `stale`) and rebuilds in the background; it is also pre-built at server start. On Vercel (no background work) it rebuilds inline, which fits the 30 s cap.
- `/api/m/quotes` is ~16 s only the first time each day (52-week range per stock), then cached on disk.

## Upstox request volume
| Scenario | Before | After |
|---|---|---|
| Server start, no browser, first 75 s | 226 calls | 226 (cold) / **22 (warm restart)** |
| Browser touring every screen for 6 min | ~200 calls/min at start-up | **18.7 calls/min** |

What changed: `shared_cache.py` now falls back to small files in `.cache/` when Upstash Redis is not configured, so daily
candles, 52-week ranges and the backtest result survive a restart (20 h TTL, same keys Vercel already used). After hours the
quote cache lives 45 s instead of 3 s. Upstox calls are counted per endpoint/caller in `GET /api/m/budget`.

## Frontend fixes found while testing the Trade tab
- Order ticket showed **"Commission ₹0.00"** while every fill deducted brokerage + STT + exchange + stamp + GST. It now shows **Charges (est.)**.
- `volume-spurt` on an index returned HTTP 400 on every Options open. It now returns "Not applicable: indices report no volume".
- Phones: sticky Buy / Sell bar, compact toolbar, signal pill no longer covers the chart legend, Options header no longer clipped, Markets list no longer overflows on desktop.
- Dead frontend code removed: `hash`, `notify`, `indPreview`, `G`, `VD_TRADE_COND`, `VD_VWAP_CHECKLIST`.

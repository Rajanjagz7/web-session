# Rajan Algo

The single app (live: rajanstocks.vercel.app / algostocks.vercel.app). Replaces the old rajantrading app.
Run locally: double-click `start.bat` (http://localhost:8000). Needs `UPSTOX_ACCESS_TOKEN` in `.env.local`.

## Screens
- **Picks** - all F&O stocks + indices screened (EMA 20/50, range, volume, RSI; structure-aware SL, 1.5R / 2.5R targets),
  Stocks / Index filter, own-chart Market overview, and **Index F&O calls** (BUY CALL / BUY PUT only when chart + option flow agree).
- **Trade / Markets / Options / Stocks / Daily / Indicators** - charts (1 mo ... All, up to 40 years), 35+ strategies incl.
  Trend Target Ribbon, Dual-Phase Reversal, RJ Best, Option Low-Range scanner (`/api/m/option-low-range`).
- **Portfolio** - what you hold now (paper positions, P&L, allocation).
- **Journal** - paper-trading validation per the BRD (`docs/brd/`): risk-sized planning, 5 entries/day, mandatory SL,
  partial exits, stop history, TSL Lab on real candles, strategy lab, reports/CSV. `static/journal.js`.

## Notifications
- Your own alerts: unlimited, in-app or push. Dismiss one, Clear all, close with x / Esc.
- Recommendation pushes (server): max 5 per device per day, de-duplicated (`push_signals.py`).
  Cycle runs every 5 min in market hours: locally via a background thread; on Vercel Hobby (no 5-min cron) the open app pings
  `/api/cron/signal-push`, or point any free pinger at it. Set Upstash/KV env vars to keep subscriptions durable on Vercel.

## Notes
- `.env.local` holds a live token. Never commit it.
- Backup of the retired app: `../_archive/rajantrading-backup-2026-10-14.zip`.

## Accuracy of every indicator and of the Picks screen
`python accuracy_report.py` replays every daily-bar indicator (24 + Volume Spurt) on 5 indices + 20 liquid stocks (about 4 years) and the Picks
screen on every F&O stock + index, each trade with a stop-loss and a target (1R / 1.5R / 2R / 3R, picks: 1.5R / 2.5R), as shares/futures and as
options (the Auto Trader's rule). Results: `docs/INDICATOR_ACCURACY.md`, `static/accuracy_report.json`, `GET /api/backtest/accuracy` (`?full=true`
for every rule). Indicators that need minute bars or peek at the session are listed as not replayable.

## Auto Trader
No daily entry limit (it used to stop at 5: 3 index + 2 stock). Every qualifying signal is taken, one position per symbol, each risking the same
fixed amount. `maxPerDay`, `indexSlots`, `stockSlots` in `POST /api/auto/config` accept a number to cap it again; 0 = no limit.

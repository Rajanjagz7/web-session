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

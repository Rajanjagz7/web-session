# Smoke + sanity checklist — 2026-10-24 build

Everything below was click-tested on the local server (127.0.0.1:8010) before deploy; repeat on the
LIVE site (rajanstocks.vercel.app) after the deploy. Market closed checks are marked; the in-session
ones (marked ☀) should be spot-checked during market hours.

## Header
- [x] No lone "Nifty" index chip next to Search (removed).

## Trade screen
- [x] Right panel: Order | Signals tabs (desktop shows the tab bar now; one pane at a time).
- [x] Signals sub-tabs: All indicators | God's Eye | Time cycle | Z Trend | Hedge | Buy signals — each renders, each loads its own data.
- [x] "All indicators" = indicator readings + full strategy table in one view; strategy table keeps its All/Active/Bullish/Bearish filters and 5/10/20/All pagination.
- [x] Z Trend card: state, price/stop/resistance/support chips, last flip, flip table (single-session timeline).
- [x] Time cycle card: TIME | PRICE | STRENGTH table, paginated (8/page, opens on the next cycle), zone chips (Vibration/Next resistance/Max pain/Call wall/Put wall), Square-of-9 ladder + "How to read · disclaimer" collapsed.
- [x] "Old expiry" button opens the expiry-diary panel; expiry/strike/CE-PE selects + Show load daily candles for a recorded contract. ☀ passed expiries start appearing once their chain was fetched live.
- [x] What-If card: no Black-Scholes note line.
- [ ] ☀ Chain KPI chips wrap on mobile; chain re-renders OI | LTP | Strike | LTP | OI on resize.

## Journal → Portfolio
- [x] Equity curve / Drawdown / Daily P&L / Rule compliance charts removed.
- [x] Compact "Day +₹x" chip next to "Open paper positions" (live).
- [x] Every trade table: entry time next to the date, exit time next to the exit type, live Held column.
- [x] Trade IDs show as just the number (A43 / 9001) with the A/T/M tag; full ID in tooltip.

## Journal → Algo
- [x] Three blocks only: Auto Trader Status | Backtest Results | Auto trade exits.
- [x] Auto Trader Status shows the Day P&L guard row (±₹30,000, mode off/soft/blocked).
- [x] Backtest Results: real /api/backtest data (verdict, simulated trades, 2-month replay, top rows).
- [x] Reset button clears the stored result (card returns to "No backtest has been run yet").
- [x] "Backtest by filter": strategy chips stay open across re-renders; Run (n selected) executes POST /api/backtest/run?only=...; the filtered result shows in its own block and never replaces the full result.
- [x] "Upcoming trades" block: dry run of the real entry engine — candidate count, per-source breakdown, top 10 by conviction, Re-check now (first check ~20s, then ~1s).
- [x] Auto trade exits: per-reason counts (Trades / Net P&L / Win %) + filter chips (All/SL/TSL/Target/Time/Expiry/Manual) + the 5/10/15/1000 pager on the trade list.

## Journal → Stock trader
- [x] Rules text block removed (rules still enforced in code).
- [x] Open AND closed lists both have the 5/10/15/1000 pager.

## Vedic Astro
- [x] Tabs: Plan | Vedic | Gann | Watchlist (Time cycle tab removed — it lives in Trade).
- [x] Failed first load auto-retries twice (cold-server fix) instead of stranding the error shell.

## Auto trader behaviour (paper, needs market hours ☀)
- [ ] Scans all ~218 F&O stocks with every indicator (incl. Z Trend daily runner + rzt-intraday flips).
- [ ] Z Trend flips open HEDGED credit spreads when cfg.zTrendHedge is on (SPREAD-STOP at 2x credit, SPREAD-T1 at 50% banked) — check the Algo exits breakdown for SPREAD-* rows.
- [ ] Option SELL legs (paired shorts) deferred until 09:20; buys from 09:15.
- [ ] No re-entry into a symbol that stopped out TODAY (incl. swing trades closed today).
- [ ] Time-cycle trigger: at a strong/medium cycle time only, price at a zone, R:R >= 1.2, max one per cycle.
- [ ] Stock trader: auto profit lock (₹1,500 breakeven, ₹2,000 trail) marks stops with L.

## Known / watch
- Backtest card numbers are legitimately red right now: every strategy's avgR is negative in-sample AND out-of-sample (wins exist per trade, but the averages are negative). Red = negative value, not an error.
- "Upcoming trades" currently shows ~180 candidates because maxPerDay = 0 (no cap). Set maxPerDay / indexSlots / stockSlots via POST /api/auto/config to limit entries per day.
- Old-expiry diary fills up from the deploy onward — past expiries appear only after their chain was fetched once while live.

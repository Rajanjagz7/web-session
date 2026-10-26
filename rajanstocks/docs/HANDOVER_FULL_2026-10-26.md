# Rajan Algo — complete handover, day 1 to now (written 2026-10-26)

Everything built and fixed from my side, in order, with the request behind each item.
Companion docs: `AUDIT_2026-10-25.md` (full audit), `WORKLOG_2026-10-24_25.md` (detailed two-day log with root causes).

---

## Project snapshot

- **App:** Rajan Algo — paper-trading + signal platform (rajanstocks.vercel.app, alias rajan-algo.vercel.app)
- **Source:** `C:\Users\Baps\Downloads\Automation\rajanstocks` (local is the live source), monorepo `github.com/Rajanjagz7/web-session`, **production branch = `rajan-web-session`** (Vercel git integration builds on push; the Vercel CLI prod deploy is broken — always deploy via git push)
- **Stack:** FastAPI (`server.py` + routers), Vercel serverless Python (30s cap), single-file frontend `static/index.html` (3 inline script blocks + one big IIFE), `static/journal.js`, `observer.js` (God's Eye), `godseye.js`, Upstox market data with a shared rate budget, Upstash KV shared cache (primary + backup failover)
- **PWA:** manifest + sw.js (network-first for HTML/static), install button, iOS guide, push notifications

---

## Day 1 — 2026-10-23: Z Trend engine + auto-trader overhaul

You asked for: a Z Trend indicator usable for signals (not just charts), Z Trend hedged strategy in the auto trader, day P&L limit with trailing, sells only from 09:20, the auto trader to use ALL indicators, re-entry-after-SL fix, stock-trader TSL, journal timestamps + short trade IDs, expiry diary, Trade signals sub-tabs.

Done (all live):
- **Z Trend (Rajan Zone Trend)** — full ATR-trailing-stop engine in 3 places kept in exact parity: chart JS, backend `rzt.py`, offline `rzt_backtest.py`. Shows BUY/SELL, resistance, support and the stop line; feeds the auto trader and the Trade Signals card.
- **Z Trend hedged credit spreads in the auto trader** (`zTrendHedge`) — sell OTM + buy a further hedge, measured accuracy from backtests.
- **Day P&L guard ₹30,000** — fewer trades / trailing once hit (`_day_guard`).
- **Sell timing rule** — option selling starts 09:20, everything else from 09:15.
- **Auto trader uses all indicators** (full-universe `scan_all`), **re-entry after SL fixed** (closed-today symbols included in the open guard), **stock trader auto TSL** at ₹1,500/₹2,000 profit locks.
- **Journal**: entry/exit timestamps, Held column, short numeric trade IDs.
- **Expiry diary** (`expiry_book.py`) — records every contract key while chains are live so old expiries can be reviewed later.
- **Trade signals sub-tabs** — All indicators / God's Eye / Time cycle / Z Trend / Hedge / Buy signals.

## Day 2 — 2026-10-24: the big UI + correctness day

You asked for: clean trade screens (web+mobile), dynamic Vedic report, Z Trend in Trade Signals, compact Time Cycle (drop "counted from", add price), God's Eye + Time Cycle + Hedge side by side, old-expiry review charts, ALL F&O stocks in stock option trading, remove Journal equity-curve/drawdown/rules UI, daily P&L chip next to open paper positions, fix Algo backtest/Vedic cards, DD/exit-reason filter, stock pagination, remove Time Cycle from Vedic, restructured Trade work panel, IDs as numbers only, remove lone Nifty chip, Algo pagination, backtest Reset + filter-based backtests, remove stock-trader Rules section (UI only), remove Vedic Gann card from Algo, upcoming trades in Backtest, fix the filter dropdown auto-close, push everything live, smoke-test all buttons, investigate backtest showing red despite wins, review/optimize code.

Done (all live):
- **Trade screen cleanup**: compact Time Cycle (price shown, "counted from" removed, zone chips, pagination, collapsed ladder), God's Eye + Time Cycle + Hedge + Z Trend side-by-side sub-tab cards, What-If without the Black-Scholes note, trade IDs numeric-only, header Nifty chip removed.
- **Algo tab**: DD/exit-reason filter chips (styled `.jv-exitf`), Reset button, filter-based backtests, Upcoming trades in the Backtest card, single pager (double-pagination bug fixed — `tradeTable()` embeds its own pager, never wrap it), Vedic Gann card removed.
- **Vedic report fully dynamic** (live price/VWAP/session data); Time Cycle removed from Vedic (lives in Trade).
- **Old-expiry review**: expiry diary + review panel (pick old expiry → strike → CE/PE → that contract's daily candles).
- **Journal**: equity-curve/drawdown/rule-compliance UI removed; daily P&L as a compact chip next to "Open paper positions".
- **Backtest dropdown auto-close fixed** (`SV.openDet` + `data-jvopen`); backtest red-despite-wins investigated and explained.
- **Filter dropdown persistence** across re-renders.
- QA: smoke checklist `qa/SMOKE_CHECKLIST_2026-10-24_25.md`, all buttons tested live.

## Day 3 — 2026-10-25: full regression audit + whole-market Picks

You asked for: a structured full audit (regression, API audit with no deletions without approval, indicator validation, UI/button audit, NSE/BSE coverage as priority, fixes with tests, detailed report), the IPO closed-data bug fixed, Upstash limit health, horizon filter showing indices (bug).

Done (all live, report in `AUDIT_2026-10-25.md`):
- **Coverage: 213/213 F&O stocks exact** vs the Upstox instrument master + 4 indices added (NIFTYFPI, BANKEX, SENSEX50, FOCIT). BSE stock options don't exist on Upstox (4 indices only). Pinned by `test_coverage.py`.
- **Z Trend parity defect found & fixed** (backend seeding + stop-line differed from the chart) — `test_rzt_parity.py` runs the real chart JS against the backend; flips/stop-line identical.
- **IPO closed-data vanish fixed** (degenerate-build guard + stale serve + NSE retry) — `test_ipo_resilience.py`.
- **Picks scans the WHOLE NSE market**: F&O 218 first, then every listed equity via **NSE bhavcopy archive** (`equity_bhav.py`, rate-budget-free), live-bar append during market hours (cash picks are never last-day data), cash floors ≥25k shares / ≥₹20 / strength ≥55, Market filter chips (All/F&O/Cash), coverage walk paced (~120 symbols/build).
- **Upstash primary hit its 500K request cap → auto-failover to backup** (transparent; `/api/m/kv-health` shows state). Bhav history reads batched to 1 GET/session.
- **Horizon filter fixed** (indices no longer leak into Intraday/Swing/Positional — stocks only).
- Exit-chip styling, God's Eye mobile 2-column restored, **PWA install button** (delegated clicks, iOS Add-to-Home-Screen guide sheet).
- 24 automated tests green; user decisions recorded: `/api/v1/*` family KEPT, offline Z-Trend grid NOT re-run, auto-trader index set stays at the 5 NSE majors.

## Day 4 — 2026-10-24/25 late (this session): the stuck loader and everything after

You asked for: caches cleared (Vercel/Upstash/website), the install button tested on mobile + made attractive, the loader fixed AT PRIORITY (you could access nothing), Picks methodology hidden ("no one should know how it's made"), the bhav master download confirmed safe, the Picks gap/divider and Buy+Cash/F&O filters fixed, the Hedge card error + scroll fixed (Z-Trend-compact), GIFT Nifty chart data fixed, watchlist clipping fixed, old expiry moved into the filter row, the Vedic Rahu-Kaal timeline + 5 rows hidden, God's Eye edges (then reverted to the old look), the horizon-table overflow fixed and verified in a fresh tab, and this complete day-1 handover.

Done (all live):
- **THE STUCK LOADER — root cause + fix** (`0ecfc83`): the PWA block in the notifications script block called `pwaRefresh()` at load time; it referenced `I` which is defined in a LATER script block → block B died before `global.RN=` → block C died at `RN.init` → **boot never ran**. Fixed by guarding the icon render + exposing `pwaRefresh` on window. Verified with headless Chrome before (2 pageerrors, frozen) and after (0 errors, boots ~6s). Lesson: index.html's 3 script blocks run in order — an earlier block must never touch a later block's bindings.
- **Picks methodology hidden** (`d72420a`, `33e79e4`): coverage counter, method disclaimer, RSI/Vol card stats removed from the UI; `coverage`/`bhav_diag` stripped from the public API (serve-time sanitization too); diagnostics go to server logs only.
- **Install button**: gradient pill + pulse + "App" label; click flow tested on a mobile viewport (guide sheet opens; Android gets the native prompt). Master-download backoff (90s) confirmed safe.
- **Caches**: Upstash junk purged (912 keys + 0 remaining), **SW shell bumped** and old caches deleted on activation, Vercel needs no manual purge (immutable deploys). API timings healthy (0.6–1.8s).
- **Picks fixes** (`d6864fb`, `b64cdbf`): divider `grid-column:1/-1` un-trapped from a mobile media query (no more floating text/gap on desktop); `liveUpdate` `data-chg/chga` guarded against unknown symbols (the 4 new indices crashed every Picks render and killed price updates); unknown payload symbols registered; lambda memory TTL 240s closed-market (instances stop serving hour-old copies); the **cash walk re-warmed** after the bhav:sessions clobber (spaced refreshes; ~120 symbols/build, cash picks accumulating again); empty-Cash state explains the scan is progressing.
- **Hedge card** (`285adf9`): raw `${Math.round(...)}` template fixed (was printed literally); rule/backtest text collapsed into a "How is this made?" details; table 8→7 columns — no horizontal scroll.
- **GIFT Nifty charts** (`32052f7`): bars-per-day now uses each market's own session (GIFT ~21h, crypto 24h — was NSE's 6.25h, so ranges loaded a third of the window); failed history refresh retries in ~15s. Verified: 2,506 bars spanning 31.8 days. (TV free feed caps 5,000 bars/request.)
- **Watchlist clipping** fixed (`minmax(0,1fr)` + ticker ellipsis + nowrap prices).
- **Old expiry in the filter row** (`8522cd6`): the separate button is gone; past expiries appear as dashed ⏳ chips + an "Old (expired)" dropdown group; picking one opens the review panel (its own expiry select removed). Past entries appear from Oct 27 once the first recorded expiry passes.
- **Vedic Plan tab** (`c3493b0`): Rahu Kaal timeline bar + the 5 numbered session rows hidden; the news section follows the special-timing strip (09:44 tithi line) directly.
- **God's Eye width**: made full-width (`da46bc5`), then **reverted to the old centered 1100px look at your instruction** (`3a1a64a`) — final state = the centered board you approved. The persistence of the old look was a cache issue — `?v=` bumps are now mandatory for every static-file change.
- **Horizon-plan table overflow** (`0439c94`): `table-layout:fixed` + column widths; T2 no longer spills between cards. Verified with your exact filter combo in a fresh tab on production: 0px overhang.

---

## Parallel-session work in the repo (not mine — listed so the handover is complete)

Git history shows another session worked 2026-10-25/26 in parallel: KP Lagna Sub-Lord Method 2 (18 slices) toggle + Monday Rahu-Kaal fix, Time Cycle revamp matching the Z Trend layout, weekly Day-Power matrix updates, SW shell bumps v5→v18, journal LTP column + live refresh + manual-trade log/delete (with removed trade IDs 27/1004/1009 date-bound), auto-trade 9:15 BUY / 9:20 SELL enforcement + unblock after 09:45, TSL breathing room, picks 30s-timeout + rate-budget fixes on Vercel, static-serving hardening, PWA "install → hide button", "No feed" poll fix, boot deadlock fixes (v18). Treat those as part of the current codebase.

## Operational rules (do not break)

1. **Deploy = `git push origin rajan-web-session`** (Vercel CLI prod deploy is broken — root-directory error).
2. **Never `Query(min=/max=`** in FastAPI routers — Vercel's older FastAPI throws and 500s the whole lambda; use `ge=/le=`.
3. **Every static-file content change ships with its `?v=` bump** in index.html in the same commit (cache-busting).
4. index.html's 3 script blocks run in order — earlier blocks must never touch later blocks' bindings at load time.
5. Serverless: refreshes when closed are gated to 1/120s; picks builds ≤30s; bhav warm downloads 8/refresh; `bhav:sessions` writes are union-only (concurrent instances).
6. Upstash: shared rate budget is finite — bhavcopy/batched reads for anything whole-market; check `/api/m/kv-health` for failover state.
7. `tradeTable()` embeds its own pager — never wrap it in another one.
8. `test_rzt_parity.py` + `test_coverage.py` must run after any rzt.py or index-list change.

## Watch / next

- ☀ In-session checks on a trading day: sells at 09:20, hedged spreads firing, time-cycle triggers, cash picks moving live, stock trader taking cash candidates.
- Old-expiry review fills with real data from **Oct 27** (first recorded expiry passes).
- Upstash primary stays capped at 500K — backup is carrying everything (transparent failover); consider a plan upgrade if you want the primary back.
- Z Trend offline grid JSON uses the older seeding (kept by decision — don't compare to live numbers).

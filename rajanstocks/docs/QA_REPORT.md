# QA report - 20 Oct 2026 (indicators, buy/sell screens, data, speed, e2e)

How to re-run everything (server on http://127.0.0.1:8000):

| What | Command |
|---|---|
| Indicators / strategies (35 strategies x 8 symbols, 12 option scans) | `python qa/indicator_audit.py` |
| Data feeds (candles x 6 timeframes, quotes, picks, chain, latency) | `python qa/data_audit.py` |
| Click-through monkey test (web + mobile, every screen) | `python qa/monkey.py http://127.0.0.1:8000 30` |
| End-to-end suite (15 tests, web 1366x800 + mobile 390x844) | `python -m pytest test_e2e_smoke.py -q` |
| Rate-limit logic (fake Redis, 21 tests) | `python -m pytest test_rate_limit.py -q` |
| 10-user concurrency test (latency + Upstox calls) | `python qa/load_test.py http://127.0.0.1:8000 10 25` |
| SIP calculator vs the raw fund NAV history | `python qa/sip_check.py` |
| Read-only browser smoke test of a deployed site (web + mobile) | `python qa/live_smoke.py https://rajanstocks.vercel.app` |

## Indicators
- **35 backend strategies x 8 symbols = 280 calls, all HTTP 200**; every payload complete, finite, fresh (last bar = last trading day,
  flagged stale otherwise), close within 6% of the live quote, stop-loss / targets on the correct side of the price.
- **12 option scans** return rows with finite prices and sane SL / targets (a few scans correctly return 0 rows: they only fire on expiry day or at specific levels).
- **Chart indicator library**: all 19 classic indicators (SMA, EMA, WMA, Bollinger, Donchian, Keltner, RSI, MACD, ATR, Stochastic, CCI,
  Williams %R, OBV, ROC, ...) were recomputed independently in the test and **match to 4+ digits** on 1,242 daily bars; all produce finite
  output on 6,000+ intraday bars and on option-contract charts.
- Strategy overlays (UT Bot, ORB, HA Dancing Trend, VIX range, Rajan Trend Rider, ...) draw the server's values (last bar equals the API value).

## Bugs found and fixed
1. **Market Buy with "Attach stop-loss and target" ticked opened the position with no stop-loss and no target** whenever the contract's
   plan read WAIT (limit orders already had a fallback). It now always attaches (plan levels, else stop -30% / target +60%).
2. **`/#stocks` (old link / bookmark / notification) showed a blank page** - there is no Stocks screen any more. It now opens Markets.
3. **First quote request of the day took ~23 s** and starved the charts: it made ~100 sequential 52-week-range candle calls in the foreground.
   Now cached values are used and the missing ones are filled by one background worker (quotes answer in 0.7 s).
4. **Order ticket showed "Commission ₹0.00"** while fills deducted real charges (old Trade screen; now "Charges (est.)").
5. Background jobs could take 260 of the 420 requests per minute and make charts fail with "temporarily unavailable"; they now get 150.
6. The Upstox call counter counted requests the throttle had held back; it now counts real requests only.

7. **Refresh on Daily scan / Picks / Day calls re-ran the whole scan every click** (hundreds of Upstox calls each; mashing it burned the 30-minute
   budget for everyone). A refresh inside a 15-30 s (live) / 2-3 min (closed) cooldown is answered from the cache, and if Upstox is busy the last
   scan is shown (flagged stale) instead of a 502.
8. **The Indicators screen offered stocks the strategy engine rejected** (HTTP 400 `not in the supported universe`, e.g. a stock found through
   Search). Strategies now accept any real NSE equity (Upstox instrument master); REITs/typos are refused up front.
9. **Quotes for a symbol Upstox does not know** (e.g. the EMBASSY REIT from an alert) returned HTTP 503 as if the feed were down; they now answer
   an empty list with `missing`, and such symbols are never sent to Upstox.

## Speed
| Chart (cold cache) | Before | After |
|---|---|---|
| Stock 5m / 15m / 1H first candles | 1.2 - 9 s (waited for all history) | **0.3 - 0.8 s** (last few days first, full history swaps in behind it) |
| Option contract 1m / 5m / 15m | 1 - 2 s | **0.24 - 0.33 s** |
| First `/api/m/quotes` of the day | 23 s | **0.7 s** |

## Other checks that passed
- **Picks**: 166 BUY/SELL ideas of 218; every one has its stop-loss on the correct side, target < target 2 in the trade direction, RR >= 1, entry within 5% of the live price.
- **Option chains (NIFTY, BANKNIFTY, RELIANCE)**: spot equals the live quote, strikes sorted/unique, ATM correct, lot size and expiries present, header premium equals the chain leg.
- **Candles**: 4 symbols x 6 timeframes - OHLC consistent, strictly increasing timestamps, last close within 5% of the live price.
- **SIP calculator**: invested, final value and XIRR equal an independent calculation from the raw NAV history for 4 funds (value within Rs 1, XIRR identical).
- **Concurrency**: 10 users, 923 requests in 25 s, 0 errors, p50 40-160 ms, p95 <= 0.7 s, and the whole run cost 23 Upstox calls.
- **Monkey test**: 25 random clicks on each of 11 screens on web and mobile - no JavaScript error, no blank screen, no horizontal overflow.
- **E2E**: 15 tests on web 1366x800 and mobile 390x844, all pass.

## Live site after deploying (6a3b77d)
Boot 3.0-3.6 s (web / mobile), option chart ready in 0-2.4 s, 0 JavaScript errors, 0 failing API calls; Upstox budget 95 of 1,850 used in 30 minutes.
Cold serverless numbers: first candles 1.1 s (`recent`) vs 3.3 s (full history), Vedic report 2.1 s once then 0.4 s.

## Notes (not bugs in the app)
- Deep in-the-money option legs that have not traded for a while show a last price below intrinsic value (stale last-traded price from Upstox);
  they are not flagged on screen.
- Trade screen: on this branch "Trade" opens the option-chain screen; the old full-chart ticket screen only opens for symbols without options.

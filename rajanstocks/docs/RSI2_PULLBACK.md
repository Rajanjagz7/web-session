# RSI(2) Pullback (Connors style) - UNPROVEN forward test

Added 27 Oct 2026 as `rajan-rsi2-pullback` (Reversal group). Long-only mean reversion on daily bars.

## Rules (as built)
- Entry on a completed bar: close above the 200-day average, 2-day Wilder RSI under 10, close under the 5-day average.
- Initial stop: 2.5 x ATR(14) below the close (wide on purpose; a mean-reversion dip needs room).
- Exit: any day that closes back above the 5-day average pulls the stop up to that close, so the trade ends the next session.
  The engine's breakeven-after-T1 rule also applies.
- No shorts (the published tests are long-only). No repainting: only completed bars are used.

## What the public sources report (US markets, NOT NSE, not verified by us)
- QuantifiedStrategies, RSI(2) on QQQ (Nasdaq-100), combined-strategy figures: 196 trades, 75% winners, average winner 2.5%,
  average loser 2.18%, profit factor 3.15, max drawdown 19.5%, in the market 14% of the time.
  https://quantifiedstrategies.substack.com/p/rsi-mean-reversion-trading-strategy
- Algomatic Trading, Connors 2RSI on the Nasdaq-100, 25-year test (out-of-sample since 2017): win rate 73.94%, gain/loss ratio 2.38,
  about 11 trades a year, CAGR 4.88%, max drawdown 13.64%; exact parameters are behind a paywall.
  https://algomatictrading.substack.com/p/strategy-6-my-take-on-larry-connors
- MQL5 article "Day Trading Larry Connors RSI2 Mean-Reversion Strategies": the rule set above (RSI(2) under 5 or 10, close above the
  200-period average, exit above the 5-period average); no performance numbers in the text.
  https://www.mql5.com/en/articles/17636

## Why it will not match those numbers here
- The auto trader trades OPTIONS and caps the option stop at 30% of the premium, so stops are much tighter than the wide / no-stop
  tests above; the win rate will be lower.
- The backtest replays the UNDERLYING's daily candles; theta, spreads and gaps are not modelled.
- Indian stocks and indices are not the Nasdaq-100. The edge is documented on US index products and may have faded.
- A high win rate with small wins can still lose money (one big loser erases many small winners). Judge it by average R and
  profit factor, not win rate.

## How it is tested
1. The weekly / on-push GitHub backtest (`.github/workflows/backtest.yml`) replays it on 5 indices + 20 liquid stocks, with
   the same in-sample / out-of-sample split as every other strategy.
2. Once it is in `backtest_result.json`, the auto trader forward-tests it beside the top 3 research strategies
   (`FORWARD_TEST_EXTRA` in `auto_trader.py`) while research mode is ON. Remove it from that tuple to stop.
3. Judge it after 2-3 weeks of live paper trades by average R, profit factor and the Journal's "By strategy / setup" table.

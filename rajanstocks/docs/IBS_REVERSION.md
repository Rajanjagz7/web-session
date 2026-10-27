# IBS Reversion (Internal Bar Strength) - UNPROVEN

IBS = (close - low) / (high - low). Rule: buy after a day that closes in the bottom 10% of its range (IBS < 0.10); exit when a day closes in the top 10% (IBS > 0.90). Long-only. Stop here: 2.5 ATR(14) below the signal close.

## What the published sources say (none tested on NSE data)
- WealthLab (vendor blog): QQQ, 10 years, daily bars, 164 trades, 74% winners, +0.9% average per trade, ~36% in the market. No costs or profit factor stated.
- Alpha Algo Trading Research (futures blog): ES, 765 trades, 67.3% winners, profit factor 1.72, average trade $383. No costs stated; best parameter combos were chosen in-sample.
- The win rate is high because wins are small and frequent: average win is roughly the size of the average loss, not 2x. Nothing near 80-90% was found in any source that shows its trade list.

## Why it may fail here
- Options wrapper: RSI(2) Pullback, the same type of signal, measured -0.35R per trade as an option buy in this engine. Short-hold mean reversion pays the option spread and costs on every trade.
- The engine exit is bar-based, not "next open".
- Indian cash-market costs (STT) bite a +0.9% average edge.

## Test plan
1. Backtest runs it on all symbols (GitHub Actions).
2. Judge it on the underlying (cash) model first, with and without the trend200 filter, including out-of-sample.
3. Only add it to FORWARD_TEST_EXTRA in auto_trader.py if the cash model is positive out-of-sample.

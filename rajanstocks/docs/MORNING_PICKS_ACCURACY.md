# Morning shortlist - backtest (strength >= 75 first, Open = Low / High second, 10-15 trades)
_Generated 2026-10-26 21:00 IST. Paper research, not advice. Underlying price with a stop-loss and targets on every trade, 0.1% round-trip cost; a candle touching both stop and target counts as the stop. Out-of-sample = the last 30% of the days, which no rule was tuned on._

Shortlist rule (morning_picks.py): tier 1 = strength >= 75 and good risk/reward (stop <= 5% of price and >= 1R of room to the last 20 sessions' high/low), tier 1 that is also Open = Low (BUY) / Open = High (SELL) first; tier 2 = Open = Low BUY / Open = High SELL with good risk/reward; tier 3 = fill-up (strength >= 50) only to reach 10; at most 15, at most 4 per sector.

## A. MORNING replay (what the live screen shows at 09:30, entry 09:35) - 5-minute candles
_2025-09-25 → 2026-10-12 · 265 sessions · shortlist averaged 10.4 trades a day · out-of-sample from 2026-06-22_

### SWING: pick's own stop, half at 1.5R, rest at 2.5R, up to 10 sessions

| Group | Trades | Win rate (95% range) | Target hit | Stopped | Avg R | PF | Out-of-sample: trades · win · avg R · PF |
|---|---:|---|---:|---:|---:|---:|---|
| all picks (no priority, strength >= 50) | 13948 | 49% (48%-50%) | 6% | 32% | +0.01 | 1.02 | 4159 · 52% · +0.07 · 1.18 |
| SHORTLIST (10-15) | 2757 | 46% (44%-48%) | 12% | 43% | -0.01 | 0.97 | 886 · 49% · +0.01 · 1.03 |
|   tier 1: strength >= 75 + good R:R | 636 | 48% (44%-52%) | 9% | 38% | +0.01 | 1.03 | 203 · 53% · +0.05 · 1.14 |
|   tier 1 + Open=Low/High agrees | 144 | 56% (47%-63%) | 10% | 35% | +0.06 | 1.14 | 47 · 64% · +0.10 · 1.32 |
|   tier 2: Open=Low BUY / Open=High SELL | 1907 | 45% (43%-47%) | 13% | 45% | -0.02 | 0.97 | 643 · 47% · +0.00 · 1.01 |
|   tier 3: fill-up | 214 | 44% (38%-51%) | 9% | 47% | -0.09 | 0.84 | 40 · 48% · -0.02 · 0.96 |
|   shortlist BUY | 1274 | 45% (42%-47%) | 12% | 45% | -0.04 | 0.92 | 398 · 41% · -0.14 · 0.74 |
|   shortlist SELL | 1483 | 46% (44%-49%) | 12% | 42% | +0.01 | 1.02 | 488 · 55% · +0.14 · 1.38 |

### INTRADAY: stop beyond today's extreme, 2R target, flat 15:15

| Group | Trades | Win rate (95% range) | Target hit | Stopped | Avg R | PF | Out-of-sample: trades · win · avg R · PF |
|---|---:|---|---:|---:|---:|---:|---|
| all picks (no priority, strength >= 50) | 13948 | 43% (43%-44%) | 10% | 36% | -0.07 | 0.85 | 4159 · 43% · -0.08 · 0.83 |
| SHORTLIST (10-15) | 2757 | 44% (42%-46%) | 10% | 32% | -0.04 | 0.9 | 886 · 45% · -0.01 · 0.98 |
|   tier 1: strength >= 75 + good R:R | 636 | 44% (40%-48%) | 6% | 33% | -0.07 | 0.85 | 203 · 46% · +0.01 · 1.03 |
|   tier 1 + Open=Low/High agrees | 144 | 45% (37%-53%) | 10% | 30% | +0.02 | 1.04 | 47 · 45% · +0.05 · 1.11 |
|   tier 2: Open=Low BUY / Open=High SELL | 1907 | 44% (42%-46%) | 11% | 32% | -0.04 | 0.9 | 643 · 44% · -0.03 · 0.94 |
|   tier 3: fill-up | 214 | 46% (39%-52%) | 14% | 29% | +0.02 | 1.05 | 40 · 45% · +0.19 · 1.46 |
|   shortlist BUY | 1274 | 42% (39%-45%) | 11% | 32% | -0.07 | 0.86 | 398 · 41% · -0.04 · 0.91 |
|   shortlist SELL | 1483 | 46% (44%-48%) | 9% | 31% | -0.03 | 0.94 | 488 · 48% · +0.02 · 1.05 |

### INTRADAY: same stop, 1R target

| Group | Trades | Win rate (95% range) | Target hit | Stopped | Avg R | PF | Out-of-sample: trades · win · avg R · PF |
|---|---:|---|---:|---:|---:|---:|---|
| all picks (no priority, strength >= 50) | 13948 | 49% (48%-49%) | 35% | 33% | -0.08 | 0.81 | 4159 · 48% · -0.10 · 0.78 |
| SHORTLIST (10-15) | 2757 | 49% (47%-51%) | 35% | 30% | -0.07 | 0.84 | 886 · 50% · -0.04 · 0.9 |
|   tier 1: strength >= 75 + good R:R | 636 | 47% (43%-51%) | 34% | 31% | -0.08 | 0.81 | 203 · 49% · -0.04 · 0.91 |
|   tier 1 + Open=Low/High agrees | 144 | 47% (39%-55%) | 34% | 29% | -0.06 | 0.85 | 47 · 47% · -0.07 · 0.83 |
|   tier 2: Open=Low BUY / Open=High SELL | 1907 | 49% (46%-51%) | 35% | 30% | -0.07 | 0.83 | 643 · 50% · -0.05 · 0.87 |
|   tier 3: fill-up | 214 | 53% (47%-60%) | 37% | 27% | +0.01 | 1.04 | 40 · 55% · +0.12 · 1.34 |
|   shortlist BUY | 1274 | 47% (45%-50%) | 34% | 30% | -0.08 | 0.81 | 398 · 47% · -0.05 · 0.87 |
|   shortlist SELL | 1483 | 50% (47%-52%) | 35% | 30% | -0.05 | 0.87 | 488 · 52% · -0.03 · 0.93 |

## B. OVERNIGHT replay (evening list, entered next open) - daily candles, long history
_2022-05-31 → 2026-10-07 · 1081 sessions · shortlist averaged 8.2 trades a day · out-of-sample from 2025-06-17_

### SWING: pick's own stop, half at 1.5R, rest at 2.5R, up to 10 sessions

| Group | Trades | Win rate (95% range) | Target hit | Stopped | Avg R | PF | Out-of-sample: trades · win · avg R · PF |
|---|---:|---|---:|---:|---:|---:|---|
| all picks (no priority, strength >= 50) | 128343 | 47% (47%-48%) | 6% | 30% | -0.01 | 0.98 | 39623 · 46% · -0.05 · 0.87 |
| SHORTLIST (10-15) | 8896 | 47% (46%-48%) | 9% | 39% | -0.01 | 0.98 | 2747 · 44% · -0.09 · 0.81 |
|   tier 1: strength >= 75 + good R:R | 4895 | 48% (47%-50%) | 8% | 36% | +0.02 | 1.04 | 1585 · 46% · -0.05 · 0.89 |
|   tier 3: fill-up | 4001 | 45% (43%-46%) | 10% | 44% | -0.04 | 0.92 | 1162 · 42% · -0.14 · 0.73 |
|   shortlist BUY | 5128 | 48% (47%-50%) | 10% | 37% | +0.03 | 1.07 | 1443 · 42% · -0.12 · 0.76 |
|   shortlist SELL | 3768 | 44% (43%-46%) | 7% | 42% | -0.06 | 0.88 | 1304 · 46% · -0.06 · 0.88 |

# Eagle Trades - backtest
_212 F&O stocks, last 13 months of 5-minute candles. The Picks screen is read at the decision time; entry 5 minutes later; stop-loss and targets on every trade; 0.1% round-trip cost; a candle touching both stop and target counts as the stop. No daily cap: every qualifying stock is a trade. Paper research, not advice._

**Eagle (as shipped)** = strength >= 75% AND Open = Low (BUY) / Open = High (SELL) with the Picks signal agreeing - the rows marked "(no risk/reward gate)". The other rows add a risk/reward gate (stop <= 5% of price and >= 1R of room to the last 20 sessions' high/low), which leaves only about one trade a day. SWING exit = the pick's own stop, half at 1.5R, rest at 2.5R, up to 10 sessions. INTRADAY = stop beyond today's extreme, flat 15:15.

| Screen read at | Trades (days) | Win rate (95% range) | Target hit | Stopped | Avg R | PF | Out-of-sample trades · win · avg R · PF | BUY win · avg R | SELL win · avg R |
|---|---:|---|---:|---:|---:|---:|---|---|---|
| 09:20 | 360 (171) | 48% (43%-54%) | 12% | 41% | +0.01 | 1.02 | 128 · 56% · +0.08 · 1.2 | 42% · -0.01 (163) | 53% · +0.02 (197) |
| 09:20 (no risk/reward gate) | 4009 (256) | 47% (46%-49%) | 5% | 33% | -0.05 | 0.89 | 1215 · 56% · +0.09 · 1.28 | 45% · -0.05 (1405) | 48% · -0.05 (2604) |
| 09:30 | 311 (154) | 50% (45%-56%) | 9% | 42% | -0.03 | 0.94 | 104 · 62% · +0.06 · 1.19 | 44% · -0.13 (108) | 54% · +0.03 (203) |
| 09:30 (no risk/reward gate) | 3476 (257) | 49% (47%-51%) | 5% | 31% | -0.02 | 0.96 | 1109 · 57% · +0.10 · 1.3 | 44% · -0.07 (1137) | 52% · +0.01 (2339) |
| 09:45 | 283 (143) | 52% (46%-57%) | 8% | 36% | +0.07 | 1.17 | 101 · 56% · +0.10 · 1.32 | 50% · +0.09 (82) | 52% · +0.06 (201) |
| 09:45 (no risk/reward gate) | 3363 (256) | 48% (46%-50%) | 4% | 30% | -0.02 | 0.95 | 1070 · 56% · +0.11 · 1.34 | 45% · -0.06 (1030) | 50% · -0.01 (2333) |
| 10:15 | 265 (154) | 52% (46%-58%) | 8% | 35% | +0.05 | 1.13 | 88 · 59% · +0.16 · 1.49 | 41% · -0.17 (93) | 58% · +0.17 (172) |
| 10:15 (no risk/reward gate) | 3199 (257) | 47% (46%-49%) | 4% | 30% | -0.04 | 0.9 | 998 · 55% · +0.09 · 1.29 | 43% · -0.09 (1007) | 49% · -0.02 (2192) |

## Intraday exit (stop beyond today's extreme, 2R target, flat 15:15)

| Screen read at | Trades | Win rate | Avg R | PF |
|---|---:|---:|---:|---:|
| 09:20 | 360 | 45% | -0.03 | 0.94 |
| 09:20 (no risk/reward gate) | 4009 | 43% | -0.07 | 0.85 |
| 09:30 | 311 | 47% | -0.02 | 0.94 |
| 09:30 (no risk/reward gate) | 3476 | 44% | -0.06 | 0.85 |
| 09:45 | 283 | 41% | -0.10 | 0.76 |
| 09:45 (no risk/reward gate) | 3363 | 44% | -0.07 | 0.84 |
| 10:15 | 265 | 42% | -0.14 | 0.63 |
| 10:15 (no risk/reward gate) | 3199 | 44% | -0.08 | 0.77 |

## By month (09:30 read, swing exit)

| Month | Trades | Win rate | Avg R |
|---|---:|---:|---:|
| 2025-09 | 4 | 25% | -0.43 |
| 2025-10 | 21 | 29% | -0.34 |
| 2025-11 | 24 | 62% | +0.30 |
| 2025-12 | 40 | 48% | -0.04 |
| 2026-01 | 27 | 74% | +0.48 |
| 2026-02 | 35 | 31% | -0.28 |
| 2026-03 | 13 | 15% | -0.70 |
| 2026-04 | 7 | 14% | -0.67 |
| 2026-05 | 26 | 35% | -0.28 |
| 2026-06 | 10 | 80% | +0.59 |
| 2026-07 | 20 | 55% | -0.06 |
| 2026-08 | 46 | 59% | -0.03 |
| 2026-09 | 29 | 69% | +0.22 |
| 2026-10 | 9 | 78% | +0.31 |

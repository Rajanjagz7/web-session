# Morning shortlist - what each rule changes (MORNING replay, 5-minute candles, swing exit)

_100 most liquid F&O stocks, 2025-09-25 -> 2026-10-23, entry 5 minutes after the screen is read. Out-of-sample = last 30% of the days. Paper research, not advice._

| Variant | Trades / day | Days with 10+ | Trades | Win rate | Avg R | PF | Out-of-sample avg R | Intraday-exit avg R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline (as shipped) | 10.7 | 80% | 2757 | 46% | -0.01 | 0.97 | +0.01 | -0.04 |
| no risk/reward gate | 15.0 | 100% | 3845 | 50% | +0.02 | 1.06 | +0.10 | -0.06 |
| room >= 1.0R | 10.7 | 80% | 2757 | 46% | -0.01 | 0.97 | +0.01 | -0.04 |
| room >= 2.0R | 5.6 | 14% | 1450 | 45% | -0.03 | 0.93 | -0.02 | -0.06 |
| Open=Low tolerance exact (0%) | 9.6 | 69% | 2474 | 45% | -0.02 | 0.95 | +0.01 | -0.04 |
| Open=Low tolerance 0.1% | 11.7 | 84% | 3006 | 45% | -0.03 | 0.95 | -0.05 | -0.06 |
| fill-up from strength 25 (score 1) | 10.7 | 80% | 2757 | 46% | -0.01 | 0.97 | +0.01 | -0.04 |
| read the screen at 09:20 | 11.5 | 84% | 2947 | 45% | -0.02 | 0.96 | +0.02 | -0.10 |
| read the screen at 09:45 | 10.1 | 75% | 2616 | 43% | -0.07 | 0.86 | -0.11 | -0.05 |
| read the screen at 10:15 | 9.7 | 70% | 2521 | 46% | -0.03 | 0.93 | -0.02 | -0.11 |

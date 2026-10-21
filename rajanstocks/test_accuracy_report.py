"""The accuracy backtest's own arithmetic: stop / target / gap / tie handling, costs and statistics."""
import math

import accuracy_report as ar


def bar(o, h, l, c, d="2026-01-01"):
    return {"date": d, "open": o, "high": h, "low": l, "close": c, "volume": 1}


FLAT = bar(100, 100.5, 99.5, 100)


def run(bars, side="BUY", entry=100, risk=2, target_r=2, **kw):
    d = 1 if side == "BUY" else -1
    return ar.sim_levels(bars, 0, side, entry, entry - d * risk, [entry + d * target_r * risk], cost=0, hold=len(bars), **kw)


def test_long_target_hit_pays_exactly_the_target_multiple():
    R, j, why, n = run([FLAT, bar(100, 105, 99.8, 104)])
    assert (round(R, 6), why, n) == (2.0, "T", 2)


def test_long_stop_hit_loses_exactly_one_r():
    R, j, why, n = run([FLAT, bar(100, 101, 97.9, 98)])
    assert (round(R, 6), why) == (-1.0, "SL")


def test_candle_touching_both_stop_and_target_counts_as_the_stop():
    R, j, why, n = run([bar(100, 106, 97, 101)])
    assert why == "SL" and round(R, 6) == -1.0


def test_gap_down_through_the_stop_fills_at_the_open_not_the_stop():
    R, j, why, n = run([FLAT, bar(95, 96, 94, 95)])
    assert why == "SL" and round(R, 6) == -2.5          # (95 - 100) / 2


def test_short_side_mirrors_the_long_side():
    assert round(run([FLAT, bar(100, 100.2, 95, 96)], "SELL")[0], 6) == 2.0
    assert round(run([FLAT, bar(100, 103, 99.5, 102)], "SELL")[0], 6) == -1.0


def test_time_exit_marks_to_the_last_close():
    R, j, why, n = run([FLAT, bar(100, 101, 99.5, 101), bar(101, 102, 100.5, 101)])
    assert why == "TIME" and round(R, 6) == 0.5


def test_cost_reduces_every_result():
    cost = ar.sim_levels([FLAT, bar(100, 105, 99.8, 104)], 0, "BUY", 100, 98, [104], cost=0.001, hold=2)[0]
    assert math.isclose(cost, 2.0 - 0.001 * 100 / 2)


def test_not_enough_future_bars_returns_nothing():
    assert ar.sim_levels([FLAT], 0, "BUY", 100, 98, [104], hold=10) is None


def test_split_exit_takes_half_at_target_one_then_protects_with_breakeven():
    bars = [FLAT, bar(100, 103.1, 99.9, 103), bar(103, 103.2, 99.5, 100)]       # T1 = 103 (1.5R), then price falls back to entry
    R, j, why, n = ar.sim_levels(bars, 0, "BUY", 100, 98, [103, 105], cost=0, hold=3, exit_mode="split")
    assert round(R, 6) == 0.75 and why == "T"                                   # half won 1.5R, half stopped at entry (0)


def test_stats_win_rate_pf_and_drawdown():
    T = [{"R": 2, "why": "T"}, {"R": -1, "why": "SL"}, {"R": -1, "why": "SL"}, {"R": 0.5, "why": "TIME"}]
    s = ar.stats(T)
    assert s["n"] == 4 and s["winRate"] == 0.5 and s["targetHit"] == 0.25 and s["stopped"] == 0.5 and s["timeExit"] == 0.25
    assert s["avgR"] == 0.125 and s["pf"] == 1.25 and s["maxDD_R"] == 2.0
    assert ar.stats([])["n"] == 0


def test_wilson_interval_brackets_the_rate_and_narrows_with_more_trades():
    lo, hi = ar.wilson(50, 100)
    assert lo < 0.5 < hi
    lo2, hi2 = ar.wilson(500, 1000)
    assert (hi2 - lo2) < (hi - lo)


def test_cash_plan_keeps_the_stop_between_075_and_2_atr():
    bars = [bar(100, 101, 99, 100) for _ in range(5)]
    r = ar.cash_plan(bars, 2.0, 3, "BUY", 100)
    assert 1.5 <= r <= 4.0
    assert ar.cash_plan(bars, 2.0, 3, "BUY", 100, ind_stop=95) == 5      # the indicator's own stop (2.5 ATR) is respected

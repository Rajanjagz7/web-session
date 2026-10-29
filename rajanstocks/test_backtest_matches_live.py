"""The backtest must test the stop the live trader actually uses (it tested a 30% premium stop while live trading used 12.5%)."""
import auto_trader as at
import backtest


def test_backtest_premium_stop_equals_the_live_default():
    assert backtest.PREM_SL == at.PREM_SL_PCT == at.DEFAULT_CFG["premSlPct"]


def test_plan_risk_is_capped_by_that_percent_of_premium():
    bars = [{"low": 90.0, "high": 110.0}] * 3
    # a huge ATR makes the signal-candle stop wide; the cap is PREM_SL x premium / delta
    r = backtest.plan_risk(bars, 1000.0, 2, "BUY", 100.0, 80.0)
    assert r == backtest.PREM_SL * 80.0 / backtest.DELTA
    assert r == 20.0                                     # 12.5% of an 80 premium at delta 0.5

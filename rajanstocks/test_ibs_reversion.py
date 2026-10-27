import rajan_new_indicators as ni
import ut_bot


def _bars():
    out = []
    for i in range(80):
        c = 100 + 0.1 * i
        out.append({"date": f"d{i:03d}", "open": c, "high": c + 1, "low": c - 1, "close": c})
    out[50] = {"date": "d050", "open": 105, "high": 106, "low": 100, "close": 100.2}       # IBS ~0.03
    out[53] = {"date": "d053", "open": 105, "high": 107, "low": 103, "close": 106.9}       # IBS ~0.97 -> exit
    return out


def _run(monkeypatch):
    monkeypatch.setattr(ut_bot, "fetch_index_history", lambda sym, lookback_days=0: _bars())
    return ni.rajan_ibs_reversion_scan("TEST")


def test_buys_the_low_close_and_exits_on_the_high_close(monkeypatch):
    r = _run(monkeypatch)
    buys = [b for b in r["bars"] if b["signal"] == "BUY"]
    assert buys and buys[0]["date"] == "d050" and buys[0]["stop"] < 100.2
    assert any(b["signal"] == "EXIT" for b in r["bars"])


def test_long_only_and_registered(monkeypatch):
    import backtest
    r = _run(monkeypatch)
    assert not [b for b in r["bars"] if b["signal"] == "SELL"]
    assert "rajan-ibs-reversion" in ni.NEW_KEYS and "rajan-ibs-reversion" in ni.NEW_KEYS_SET
    assert "rajan-ibs-reversion" in backtest._runners()

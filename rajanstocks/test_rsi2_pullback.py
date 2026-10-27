import rajan_new_indicators as ni
import ut_bot


def _bars(closes):
    out = []
    for i, c in enumerate(closes):
        out.append({"date": f"d{i:04d}", "open": c, "high": c * 1.004, "low": c * 0.996, "close": c})
    return out


def _uptrend_with_dip():
    c = [100 + 0.25 * i for i in range(260)]           # steady uptrend (above SMA200)
    c[240] = c[239] * 0.985                            # two sharp down days -> RSI(2) collapses, close < SMA5
    c[241] = c[240] * 0.985
    return c


def _run(monkeypatch, closes):
    monkeypatch.setattr(ut_bot, "fetch_index_history", lambda sym, lookback_days=0: _bars(closes))
    return ni.rajan_rsi2_pullback_scan("TEST")


def test_signal_fires_on_the_dip_in_an_uptrend_and_exits_on_the_bounce(monkeypatch):
    r = _run(monkeypatch, _uptrend_with_dip() + [100 + 0.25 * 262, 100 + 0.25 * 263, 100 + 0.25 * 264])
    buys = [b for b in r["bars"] if b["signal"] == "BUY"]
    assert buys and buys[0]["date"] in ("d0240", "d0241", "d0242")      # the first sharp down day already drives RSI(2) under 10
    assert buys[0]["stop"] < 100 + 0.25 * 240            # initial stop sits below the entry close (2.5 ATR)
    assert any(b["signal"] == "EXIT" for b in r["bars"])  # closes back above SMA5 -> stop pulled to that close -> exit next bar


def test_no_signal_in_a_downtrend(monkeypatch):
    c = [200 - 0.25 * i for i in range(260)]
    c[240] = c[239] * 0.985
    c[241] = c[240] * 0.985
    r = _run(monkeypatch, c)
    assert not [b for b in r["bars"] if b["signal"] == "BUY"]         # below the 200-day average: no entry


def test_never_shorts_and_does_not_repaint(monkeypatch):
    c = _uptrend_with_dip()
    full = _run(monkeypatch, c)
    assert not [b for b in full["bars"] if b["signal"] == "SELL"]
    part = _run(monkeypatch, c[:250])                                 # same series cut earlier gives the same signals on the shared bars
    shared = {b["date"]: b["signal"] for b in part["bars"]}
    assert all(full_b["signal"] == shared[full_b["date"]] for full_b in full["bars"] if full_b["date"] in shared)


def test_registered_and_forward_tested():
    import strategies_api, auto_trader, backtest
    assert "rajan-rsi2-pullback" in ni.NEW_KEYS and "rajan-rsi2-pullback" in ni.NEW_KEYS_SET
    assert "rajan-rsi2-pullback" in backtest._runners()                # picked up by the full backtest
    assert "rajan-rsi2-pullback" in auto_trader.FORWARD_TEST_EXTRA
    assert any(m["key"] == "rajan-rsi2-pullback" for m in strategies_api.CATALOG_META()) if hasattr(strategies_api, "CATALOG_META") else True


def test_active_set_adds_it_beside_the_top_three(monkeypatch):
    import auto_trader, backtest
    res = {"ranking": [{"key": k, "inSample": {"avgR": 0.1}} for k in ("a", "b", "c", "rajan-rsi2-pullback")],
           "chosen": {"a": ["fixed", "none"]}, "provenKeys": [], "researchKeys": ["a", "b", "c"]}
    monkeypatch.setattr(backtest, "get", lambda: {"result": res})
    scores, chosen, label = auto_trader.active_set({"researchMode": True})
    assert set(scores) == {"a", "b", "c", "rajan-rsi2-pullback"} and "unproven" in label
    res["ranking"] = res["ranking"][:3]                                # not in the backtest result yet -> not forward tested yet
    scores, _, _ = auto_trader.active_set({"researchMode": True})
    assert "rajan-rsi2-pullback" not in scores

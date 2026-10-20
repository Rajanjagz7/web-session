"""Unit tests for God's Eye - The Observer scoring (observer_api.analyse). No network needed."""
import math

import pytest

import observer_api as ob


def bars_from(closes, spread=0.01):
    """[t, o, h, l, c, v] bars with a fixed high/low spread around each close."""
    return [[i, c, c * (1 + spread), c * (1 - spread), c, 1000] for i, c in enumerate(closes)]


def trend(start, step, n=60):
    return [start + step * i for i in range(n)]


def test_needs_enough_history():
    assert ob.analyse(bars_from([100] * 10)) is None
    assert ob.analyse([]) is None


def test_score_is_bounded_and_rounded():
    for closes in (trend(100, 2), trend(300, -2), [100] * 60):
        r = ob.analyse(bars_from(closes))
        assert -10 <= r["score"] <= 10
        assert r["score"] == round(r["score"], 1)


def test_strong_uptrend_is_bullish():
    closes = trend(100, 1.5) + [100 + 1.5 * 59 * 1.04]          # then a strong up day
    r = ob.analyse(bars_from(closes))
    assert r["label"] == "BULLISH" and r["score"] >= ob.BULL_AT and r["chgPct"] > 0


def test_strong_downtrend_is_bearish():
    closes = trend(300, -1.5) + [300 - 1.5 * 59 * 1.04]
    r = ob.analyse(bars_from(closes))
    assert r["label"] == "BEARISH" and r["score"] <= ob.BEAR_AT and r["chgPct"] < 0


def test_flat_market_is_neutral():
    r = ob.analyse(bars_from([100 + (0.1 if i % 2 else -0.1) for i in range(60)]))
    assert r["label"] == "NEUTRAL" and ob.BEAR_AT < r["score"] < ob.BULL_AT


def test_score_parts_add_up():
    r = ob.analyse(bars_from(trend(100, 1)))
    p = r["detail"]["parts"]
    assert math.isclose(p["dayMove"] + p["trend"] + p["rsi"], r["score"], abs_tol=0.25)


def test_bearish_divergence_higher_high_lower_rsi():
    # sharp rally (RSI pinned near 100), then a weak grind to a slightly higher high (RSI far lower)
    closes = [100 + 0.2 * i for i in range(30)] + [106 + 2.0 * i for i in range(10)] + [121, 119, 118, 119, 120, 121, 122, 123, 124, 124.6]
    assert ob.analyse(bars_from(closes, 0.005))["divergence"] == "BEARISH"


def test_bullish_divergence_lower_low_higher_rsi():
    closes = [200 - 0.2 * i for i in range(30)] + [194 - 2.0 * i for i in range(10)] + [177, 179, 180, 179, 178, 177, 176, 175, 174.5, 173.8]
    assert ob.analyse(bars_from(closes, 0.005))["divergence"] == "BULLISH"


def test_no_divergence_in_a_clean_trend():
    assert ob.analyse(bars_from(trend(100, 1.0)))["divergence"] is None


def test_spark_has_14_points_and_detail_fields():
    r = ob.analyse(bars_from(trend(100, 1)))
    assert len(r["spark"]) == 14
    for k in ("rsi", "ema20", "vsEma20Pct", "avgRangePct", "high20", "low20", "parts", "reasons"):
        assert k in r["detail"]
    assert r["detail"]["high20"] >= r["detail"]["low20"]


def test_rsi_extremes():
    assert ob.rsi_series([100 + i for i in range(40)])[-1] == 100.0
    assert ob.rsi_series([100 - i for i in range(40)])[-1] == pytest.approx(0.0, abs=1e-6)


def test_market_open_window():
    from datetime import datetime
    ist = ob.IST
    assert ob.market_open(datetime(2026, 10, 20, 10, 0, tzinfo=ist)) is True        # Tuesday 10:00
    assert ob.market_open(datetime(2026, 10, 20, 15, 45, tzinfo=ist)) is False      # after close
    assert ob.market_open(datetime(2026, 10, 17, 11, 0, tzinfo=ist)) is False       # Saturday


def test_zero_priced_bars_are_ignored():
    bars = bars_from(trend(100, 1)) + [[99, 0, 0, 0, 0, 0]]
    assert ob.analyse(bars) is not None


def test_endpoint_shape(monkeypatch):
    monkeypatch.setattr(ob, "_fetch", lambda item: {"key": item[0], "name": item[1], "symbol": item[2], "ccy": item[3], "error": "offline"})
    ob._cache.update(ts=0.0, data=None)
    data = ob.observer(refresh=True)
    assert [i["key"] for i in data["items"]] == [k for k, *_ in ob.INSTRUMENTS]
    assert {"marketOpen", "asOf", "method"} <= set(data)


def _fake_item(item, ok=True):
    key, name, sym, ccy = item
    base = {"key": key, "name": name, "symbol": sym, "ccy": ccy}
    return dict(base, price=1.0, chgPct=0.0, score=1.0, label="NEUTRAL", divergence=None, spark=[1, 2], detail={}) if ok else dict(base, error="boom")


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    import shared_cache
    monkeypatch.setattr(shared_cache, "_DISK", str(tmp_path))
    monkeypatch.setattr(shared_cache, "_creds", lambda: None)
    ob._cache.update(ts=0.0, data=None, ttl=90)
    return tmp_path


def test_slow_instruments_come_back_pending_then_complete(isolated, monkeypatch):
    """A serverless request must answer inside its budget: slow instruments are `pending`, the next call finds them cached."""
    import time as _t
    slow = {"GOLD", "SILVER"}

    def compute(item):
        if item[0] in slow:
            _t.sleep(1.5)
        return _fake_item(item)

    monkeypatch.setattr(ob, "_compute", compute)
    monkeypatch.setattr(ob, "BUDGET", 0.4)
    first = ob.observer(refresh=True)
    pend = {i["key"] for i in first["items"] if i.get("pending")}
    assert pend == slow and len(first["items"]) == len(ob.INSTRUMENTS)
    _t.sleep(2.0)                                       # the worker threads finish and fill the shared cache
    second = ob.observer(refresh=True)
    assert not any(i.get("pending") for i in second["items"])


def test_failed_instrument_falls_back_to_stale_copy(isolated, monkeypatch):
    import shared_cache
    shared_cache.set("obs-stale|NIFTY", _fake_item(ob.INSTRUMENTS[0]), 3600)
    monkeypatch.setattr(ob, "_compute", lambda item: _fake_item(item, ok=item[0] != "NIFTY"))
    data = ob.observer(refresh=True)
    nifty = next(i for i in data["items"] if i["key"] == "NIFTY")
    assert nifty.get("stale") is True and "error" not in nifty


def test_total_outage_keeps_last_good_payload(isolated, monkeypatch):
    monkeypatch.setattr(ob, "_compute", lambda item: _fake_item(item))
    good = ob.observer(refresh=True)
    monkeypatch.setattr(ob, "_compute", lambda item: _fake_item(item, ok=False))
    import shared_cache
    monkeypatch.setattr(shared_cache, "get", lambda k: None)       # nothing cached anywhere
    again = ob.observer(refresh=True)
    assert again["asOf"] == good["asOf"]

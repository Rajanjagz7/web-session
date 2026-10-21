"""Open auto positions are marked to market (and their exits checked) whenever the status is read - no scheduler needed."""
import json
from datetime import datetime, timedelta, timezone

import pytest

import auto_trader as at

IST = timezone(timedelta(hours=5, minutes=30))
OPEN_NOW = datetime(2026, 10, 21, 11, 0, tzinfo=IST)             # a Wednesday, inside 09:15-15:30
CLOSED_NOW = datetime(2026, 10, 21, 20, 0, tzinfo=IST)


def trade(**kw):
    t = {"id": "A-1", "date": "2026-10-21", "sym": "NIFTY", "side": "BUY", "kind": "index", "key": "NSE_FO|111", "strategy": "ut-bot", "strike": 22900.0,
         "opt": "CE", "expiry": "2026-10-27", "lot": 65, "lots": 2, "entry": 100.0, "last": 100.0, "entryU": 22900.0, "stopU": 22800.0, "riskU": 100.0,
         "targetU": 23100.0, "variant": "fixed", "initialRisk": 6500.0, "plan": "v2", "premSL": 70.0, "status": "OPEN", "openedAt": "2026-10-21T09:20:00+05:30"}
    t.update(kw)
    return t


@pytest.fixture
def env(tmp_path, monkeypatch):
    import market_api
    import shared_cache
    monkeypatch.setattr(at, "FILE", str(tmp_path / "state.json"))
    monkeypatch.setattr(at, "_remote", lambda: None)
    monkeypatch.setattr(shared_cache, "_DISK", str(tmp_path))
    monkeypatch.setattr(shared_cache, "_creds", lambda: None)
    monkeypatch.setattr(market_api, "_key", lambda s: "NSE_INDEX|" + s)
    monkeypatch.setattr(at, "_MARK_AT", 0.0)
    clock = {"now": OPEN_NOW}
    monkeypatch.setattr(at, "_now", lambda: clock["now"])
    prices = {"opt": 100.0, "und": 22900.0}
    monkeypatch.setattr(at, "_quotes", lambda keys: {"NSE_FO|111": {"last_price": prices["opt"], "depth": {"buy": [{"price": prices["opt"] - 0.2}]}},
                                                     "NSE_INDEX|NIFTY": {"last_price": prices["und"]}})
    st = {"cfg": dict(at.DEFAULT_CFG), "trades": [trade()], "log": []}
    json.dump(st, open(at.FILE, "w"))
    return clock, prices


def load():
    return json.load(open(at.FILE))["trades"][0]


def test_pnl_follows_the_option_price_when_the_status_is_read(env):
    clock, prices = env
    prices["opt"] = 130.0
    s = at.status()
    t = s["open"][0]
    assert t["last"] == 130.0 and t["unrealised"] == (130.0 - 100.0) * 2 * 65 and s["summary"]["openPnL"] == 3900
    assert load()["last"] == 130.0                                  # and it is saved


def test_a_second_read_inside_the_gap_does_not_hit_upstox_again(env, monkeypatch):
    clock, prices = env
    calls = {"n": 0}
    real = at._quotes
    monkeypatch.setattr(at, "_quotes", lambda keys: (calls.__setitem__("n", calls["n"] + 1), real(keys))[1])
    at.status()
    at.status()
    at.status()
    assert calls["n"] == 1


def test_premium_stop_closes_the_position_from_a_status_read(env):
    clock, prices = env
    prices["opt"] = 65.0                                            # below premSL 70
    s = at.status()
    assert not s["open"] and s["closed"][0]["exitReason"] == "STOP" and s["summary"]["trades"] == 1


def test_underlying_target_closes_the_position(env):
    clock, prices = env
    prices.update(opt=150.0, und=23150.0)
    s = at.status()
    assert not s["open"] and s["closed"][0]["exitReason"] == "TARGET" and s["closed"][0]["net"] > 0


def test_nothing_is_marked_outside_market_hours(env):
    clock, prices = env
    clock["now"] = CLOSED_NOW
    prices["opt"] = 130.0
    s = at.status()
    assert s["open"][0]["last"] == 100.0 and s["summary"]["openPnL"] == 0


def test_a_quote_failure_never_breaks_the_status(env, monkeypatch):
    def boom(keys):
        raise RuntimeError("upstox down")
    monkeypatch.setattr(at, "_quotes", boom)
    s = at.status()
    assert len(s["open"]) == 1

"""The index call/put screen must say WHY an index was not traded (it used to drop the reason silently)."""
import time

import pytest

import auto_trader as at
import market_api

TODAY = "2026-10-29"


def book():
    return {"cfg": dict(at.DEFAULT_CFG, fillSlots=True), "trades": [], "log": []}


def idx(sym, signal, **kw):
    return dict({"instrument": sym, "signal": signal, "reason": "Chart says BUY but option flow is neutral", "strength": 80, "callPct": 60, "putPct": 40,
                 "confidence": "high", "entry": 100.0, "stopLoss": 95.0, "target1": 109.0}, **kw)


@pytest.fixture
def screen(monkeypatch):
    box = {"calls": []}
    monkeypatch.setattr(market_api, "quick_index_calls", lambda n=6: box["calls"])
    monkeypatch.setattr(at, "_picks", lambda: {"picks": []})
    monkeypatch.setattr(at, "_now", lambda: __import__("datetime").datetime(2026, 10, 29, 9, 40, tzinfo=at.IST))
    return box


def lines(st):
    return [l["msg"] for l in st["log"] if l["msg"].startswith("index ")]


def test_each_quiet_index_says_why(screen):
    screen["calls"] = [idx("NIFTY", "WATCH"), idx("BANKNIFTY", "NO SIGNAL", reason="Option chain not available right now"), idx("SENSEX", "WATCH")]
    st = book()
    at.fill_slots(st, TODAY, [])
    L = lines(st)
    assert any("NIFTY: no entry - WATCH" in m and "option flow is neutral" in m for m in L)
    assert any("BANKNIFTY: no entry - NO SIGNAL: Option chain not available" in m for m in L)
    assert any("SENSEX" in m for m in L)


def test_the_same_reason_is_not_repeated_every_cycle(screen):
    screen["calls"] = [idx("NIFTY", "WATCH")]
    st = book()
    at.fill_slots(st, TODAY, [])
    at.fill_slots(st, TODAY, [])
    assert len([m for m in lines(st) if "NIFTY" in m]) == 1
    st["idxWhy"]["NIFTY"]["t"] -= at.IDX_NOTE_EVERY + 1               # 15 minutes later it is said again
    at.fill_slots(st, TODAY, [])
    assert len([m for m in lines(st) if "NIFTY" in m]) == 2


def test_a_weak_reward_to_risk_and_a_held_index_are_explained(screen):
    screen["calls"] = [idx("NIFTY", "BUY CALL", target1=104.0), idx("BANKNIFTY", "BUY CALL")]
    st = book()
    st["trades"] = [{"id": "A-1", "sym": "BANKNIFTY", "status": "OPEN", "date": TODAY, "kind": "index", "side": "BUY"}]
    at.fill_slots(st, TODAY, [])
    L = lines(st)
    assert any("NIFTY: BUY CALL skipped - reward to target 1" in m for m in L)
    assert any("BANKNIFTY: not looked at - already holding" in m for m in L)


def test_a_good_signal_is_a_candidate_and_needs_no_excuse(screen):
    screen["calls"] = [idx("NIFTY", "BUY CALL")]
    st = book()
    out = at.fill_slots(st, TODAY, [])
    assert [c["sym"] for c in out if c["kind"] == "index"] == ["NIFTY"] and not [m for m in lines(st) if "NIFTY" in m]

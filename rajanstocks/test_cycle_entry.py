"""A whole trading cycle at the open, with the versioned book store: a signal becomes a saved trade (index and stock option),
for realistic opening-minute bid/ask spreads, and a concurrent save is recovered on the next cycle."""
import json
from datetime import datetime

import pytest

import auto_trader as at
import nse_calendar
import shared_cache
from test_book_integrity import FakeStore

NOW = datetime(2026, 10, 29, 9, 25, tzinfo=at.IST)


def cand(sym="NIFTY", kind="index", side="BUY"):
    return {"sym": sym, "side": side, "kind": kind, "key": "rajan-rsi2-pullback", "variant": "fixed", "score": 3, "source": "test", "label": "test"}


@pytest.fixture
def world(monkeypatch):
    import backtest
    import premium_rider
    import rzt
    fs = FakeStore()
    monkeypatch.setattr(shared_cache, "kv", fs.kv)
    monkeypatch.setattr(at, "_remote", lambda: ("https://x.upstash.io", "t"))
    monkeypatch.setattr(shared_cache, "lock", lambda *a, **k: True)
    monkeypatch.setattr(shared_cache, "unlock", lambda *a, **k: None)
    at._RC.clear()
    monkeypatch.setattr(at, "_now", lambda: NOW)
    monkeypatch.setattr(nse_calendar, "session_open", lambda now=None: True)
    box = {"cands": [cand()], "bid": 99.0, "ask": 100.0}
    monkeypatch.setattr(at, "scan_all", lambda st, today: (list(box["cands"]), "ok"))
    monkeypatch.setattr(at, "choose", lambda c, st, today: c)
    monkeypatch.setattr(at, "fill_slots", lambda st, today, chosen: [])
    monkeypatch.setattr(at, "eagle_cands", lambda *a, **k: [])
    monkeypatch.setattr(at, "_timecycle_cands", lambda now: [])
    monkeypatch.setattr(at, "_gann_cands", lambda now, seen: [])
    monkeypatch.setattr(at, "_screen_score", lambda: {})
    monkeypatch.setattr(at, "shadow_resolve", lambda st, now: None)
    monkeypatch.setattr(at, "shadow_record", lambda *a, **k: None)
    monkeypatch.setattr(at, "_notify", lambda t: None)
    monkeypatch.setattr(rzt, "intraday_cands", lambda: [])
    monkeypatch.setattr(premium_rider, "scan", lambda: {})
    monkeypatch.setattr(at, "_atr_for", lambda sym: (100.0, 25000.0, [{"date": "2026-10-28"}] * 30))
    monkeypatch.setattr(backtest, "plan_risk", lambda *a, **k: 100.0)

    def contract(*a, **k):
        return {"expiry": "2026-11-10", "strike": 25000, "key": "OPT1", "premium": box["ask"], "lot": 75, "spot": 25000.0,
                "bid": box["bid"], "ask": box["ask"], "ltp": box["ask"]}
    monkeypatch.setattr(at, "_contract", contract)
    st = at._load()
    st["cfg"]["enabled"] = True
    assert at._save(st) is True
    yield box, fs
    at._RC.clear()


def saved(fs):
    return json.loads(fs.d[at.KEY])


def test_signal_at_the_open_becomes_a_saved_trade(world):
    box, fs = world
    rep = at.run_cycle()
    assert rep.get("ran") and len(rep["entered"]) == 1 and not rep.get("saveConflict")
    assert [t["sym"] for t in saved(fs)["trades"]] == ["NIFTY"] and saved(fs)["trades"][0]["status"] == "OPEN"


@pytest.mark.parametrize("bid,ask,expect_trade", [(99.8, 100.0, True), (98.0, 100.0, True), (96.0, 100.0, True), (94.0, 100.0, True),
                                                  (92.0, 100.0, True), (90.5, 100.0, True), (88.0, 100.0, False)])
def test_realistic_opening_spreads_do_not_stop_entries(world, bid, ask, expect_trade):
    """0.2%-9.5% spreads are normal in the first minutes; only a book wider than 10% (already refused before 29 Oct) is skipped."""
    box, fs = world
    box.update(bid=bid, ask=ask)
    rep = at.run_cycle()
    assert bool(saved(fs)["trades"]) is expect_trade
    if not expect_trade:
        assert any("too wide" in l["msg"] for l in saved(fs)["log"])


def test_stock_option_entry_is_saved_too(world):
    box, fs = world
    box["cands"] = [cand("RELIANCE", "stock")]
    box.update(bid=19.4, ask=20.0)
    at.run_cycle()
    assert [t["sym"] for t in saved(fs)["trades"]] == ["RELIANCE"]


def test_a_save_conflict_loses_nothing_the_next_cycle_enters(world, monkeypatch):
    box, fs = world
    real_save, hits = at._save, []

    def racing_save(st):
        if not hits:                                  # another instance saves just before this cycle does
            hits.append(1)
            other = at._load()
            other["log"].append({"at": "x", "msg": "rival write"})
            assert real_save(other) is True
        return real_save(st)
    monkeypatch.setattr(at, "_save", racing_save)
    r1 = at.run_cycle()
    assert r1.get("saveConflict") and saved(fs)["trades"] == []              # refused, nothing half-written
    r2 = at.run_cycle()
    assert not r2.get("saveConflict") and len(saved(fs)["trades"]) == 1       # the next cycle redoes the entry
    assert any(l["msg"] == "rival write" for l in saved(fs)["log"])           # and the rival's write survived


def test_two_cycles_back_to_back_do_not_conflict_with_themselves(world):
    box, fs = world
    box["cands"] = []
    assert not at.run_cycle().get("saveConflict") and not at.run_cycle().get("saveConflict")

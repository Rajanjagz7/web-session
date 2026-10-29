"""A whole trading cycle at the open, with the versioned book store: a signal becomes a saved trade (index and stock option),
for realistic opening-minute bid/ask spreads, and a concurrent save is recovered on the next cycle."""
import json
import time
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

    def contract(sym, *a, **k):
        return {"expiry": "2026-11-10", "strike": 25000, "key": f"OPT-{sym}", "premium": box["ask"], "lot": 75, "spot": 25000.0,
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


# ───────────── index entries are not starved by the stock entries, and untried screen candidates are carried over ─────────────
def screen(sym, kind, rank, key="stock-screen"):
    return {"_fill": True, "key": key, "sym": sym, "side": "BUY", "kind": kind, "variant": "fixed", "filter": "none", "score": 0.5, "rank": rank,
            "agree": 1, "source": "t", "label": "t"}


def test_index_screen_entries_go_before_better_ranked_stock_entries(world, monkeypatch):
    box, fs = world
    box["cands"] = []
    monkeypatch.setattr(at, "fill_slots", lambda st, today, chosen: [screen("TCS", "stock", 2.0), screen("INFY", "stock", 1.9), screen("NIFTY", "index", 0.6, "index-call-put")])
    monkeypatch.setattr(at, "CYCLE_BUDGET", 0.0)                       # time for ONE entry per cycle
    at.run_cycle()
    assert [t["sym"] for t in saved(fs)["trades"]] == ["NIFTY"]        # the index went first although it ranks lowest


def test_what_the_cycle_did_not_get_to_is_carried_to_the_next_cycle(world, monkeypatch):
    box, fs = world
    box["cands"] = []
    calls = {"n": 0}

    def once(st, today, chosen):
        calls["n"] += 1
        return [screen("NIFTY", "index", 0.6, "index-call-put"), screen("BANKNIFTY", "index", 0.6, "index-call-put"), screen("SENSEX", "index", 0.6, "index-call-put")] if calls["n"] == 1 else []
    monkeypatch.setattr(at, "fill_slots", once)
    monkeypatch.setattr(at, "CYCLE_BUDGET", 0.0)
    for _ in range(4):
        monkeypatch.setattr(at, "FILL_EVERY", 0)
        at.run_cycle()
    assert {t["sym"] for t in saved(fs)["trades"]} == {"NIFTY", "BANKNIFTY", "SENSEX"}      # one per cycle, none lost
    assert saved(fs).get("carry") == []


def test_carried_candidates_expire_and_skip_symbols_already_held(world, monkeypatch):
    box, fs = world
    box["cands"] = []
    monkeypatch.setattr(at, "fill_slots", lambda st, today, chosen: [])
    st = at._load()
    st["carry"] = [dict(screen("NIFTY", "index", 0.6, "index-call-put"), _exp=time.time() - 1), dict(screen("SENSEX", "index", 0.6, "index-call-put"), _exp=time.time() + 100)]
    assert at._save(st) is True
    at.run_cycle()
    assert [t["sym"] for t in saved(fs)["trades"]] == ["SENSEX"]       # the expired one is dropped


def test_strength_100_stocks_with_volume_come_before_the_rest():
    q = at._quality
    s100_vol, s100, s90_vol, s75 = ({"strength": 100, "volx": 2.5}, {"strength": 100, "volx": 0.8}, {"strength": 90, "volx": 3.0}, {"strength": 75, "volx": 1.0})
    assert q(s100_vol) > q(s100) > q(s90_vol) > q(s75)
    assert q({"strength": 100, "volx": 2.5}) - q({"strength": 99, "volx": 2.5}) > 1.0        # 100 is a different class, not a rounding step


def test_order_is_index_options_then_100_strength_volume_stocks_then_the_rest(world, monkeypatch):
    box, fs = world
    box["cands"] = []
    mk = lambda sym, kind, q: screen(sym, kind, 1.0 + q, "stock-screen" if kind == "stock" else "index-call-put")
    monkeypatch.setattr(at, "fill_slots", lambda st, today, chosen: [mk("AAA", "stock", at._quality({"strength": 80, "volx": 1})), mk("BBB", "stock", at._quality({"strength": 100, "volx": 2.5})),
                                                                       mk("NIFTY", "index", -0.4), mk("CCC", "stock", at._quality({"strength": 100, "volx": 0.9}))])
    order = []
    real = at.open_trade
    monkeypatch.setattr(at, "open_trade", lambda st, c, today: (order.append(c["sym"]), real(st, c, today))[1])
    at.run_cycle()
    assert order[:4] == ["NIFTY", "BBB", "CCC", "AAA"]

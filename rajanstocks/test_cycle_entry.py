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
    monkeypatch.setattr(at, "index_expiry_today", lambda today: False)        # a regular day unless a test says otherwise
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
    st["cfg"]["indexMinAgree"] = 1                      # the 3-indicator index rule has its own tests (test_index_unlimited.py)
    st["cfg"]["indexMaxPerDay"] = 0
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
    box["cands"] = [dict(cand("RELIANCE", "stock"), agree=2)]                    # 2 indicators agree (a stock option needs 2+, or strength 75+)
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
    monkeypatch.setattr(at, "INDEX_ONE_OPEN_PER_SIDE", False)         # this test is about carrying, not about the one-index-per-side rule
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
    _set_cfg(fs, soloStrength=75.0, indexMinAgree=1)       # this test is about the ORDER: allow single-indicator entries
    box["cands"] = []
    mk = lambda sym, kind, q: screen(sym, kind, 1.0 + q, "stock-screen" if kind == "stock" else "index-call-put")
    monkeypatch.setattr(at, "fill_slots", lambda st, today, chosen: [mk("AAA", "stock", at._quality({"strength": 80, "volx": 1})), mk("BBB", "stock", at._quality({"strength": 100, "volx": 2.5})),
                                                                       mk("NIFTY", "index", -0.4), mk("CCC", "stock", at._quality({"strength": 100, "volx": 0.9}))])
    monkeypatch.setattr(at, "_screen_score", lambda: {"AAA": {"strength": 80}, "BBB": {"strength": 100}, "CCC": {"strength": 100}})
    import morning_picks
    monkeypatch.setattr(morning_picks, "good_rr", lambda *a, **k: True)
    order = []
    real = at.open_trade
    monkeypatch.setattr(at, "open_trade", lambda st, c, today: (order.append(c["sym"]), real(st, c, today))[1])
    at.run_cycle()
    assert order[:4] == ["BBB", "CCC", "AAA", "NIFTY"]      # 30 Oct priority: strength-100 stocks, Eagle, strength 75+, then index options


def test_stock_option_needs_two_agreeing_indicators_unless_a_solo_strength_is_configured(world, monkeypatch):
    """User 30 Oct: 2+ agreeing indicators for every stock and index; the old 'one indicator with strength 75+' exception is off unless soloStrength is set."""
    box, fs = world
    one = dict(cand("AAA", "stock"), agree=1)
    two = dict(cand("BBB", "stock"), agree=2)
    strong = dict(cand("CCC", "stock"), agree=1)
    box["cands"] = [one, two, strong, dict(cand("NIFTY", "index"), agree=2)]
    monkeypatch.setattr(at, "_screen_score", lambda: {"AAA": {"strength": 60}, "CCC": {"strength": 80}})
    import morning_picks
    monkeypatch.setattr(morning_picks, "good_rr", lambda *a, **k: True)
    rep = at.run_cycle()
    assert sorted(t["sym"] for t in saved(fs)["trades"]) == ["BBB", "NIFTY"] and "2 skipped (stock option needs 2+" in rep["note"]


def _set_cfg(fs, **kw):
    d = saved(fs)
    d["cfg"].update(kw)
    fs.d[at.KEY] = json.dumps(d)
    at._RC.clear()


def test_index_needs_two_indicators(world):
    box, fs = world
    _set_cfg(fs, indexMinAgree=2, indexMaxPerDay=3)
    box["cands"] = [dict(cand(), agree=1)]
    at.run_cycle()
    assert saved(fs)["trades"] == []                          # one indicator is not enough for an index
    box["cands"] = [dict(cand(), agree=2)]
    at.run_cycle()
    assert [t["sym"] for t in saved(fs)["trades"]] == ["NIFTY"]


def test_one_name_takes_at_most_three_trades_a_day(world):
    box, fs = world
    _set_cfg(fs, indexMinAgree=1, indexMaxPerDay=3)
    d = saved(fs)
    d["trades"] = [{"id": f"A-{i}", "sym": "NIFTY", "date": NOW.date().isoformat(), "status": "CLOSED", "kind": "index", "opt": "CE", "key": f"K{i}",
                    "closedAt": NOW.date().isoformat() + "T09:20:00+05:30"} for i in range(3)]
    fs.d[at.KEY] = json.dumps(d)
    at._RC.clear()
    box["cands"] = [cand(), cand("BANKNIFTY")]
    at.run_cycle()
    assert sorted(t["sym"] for t in saved(fs)["trades"] if t["status"] == "OPEN") == ["BANKNIFTY"]      # NIFTY already has its 3 today


def test_after_a_stop_hit_a_new_entry_in_another_strike_is_taken(world):
    box, fs = world
    _set_cfg(fs, indexMinAgree=1, indexMaxPerDay=3)
    d = saved(fs)
    d["trades"] = [{"id": "A-1", "sym": "NIFTY", "date": NOW.date().isoformat(), "status": "CLOSED", "kind": "index", "opt": "CE", "key": "OLD-K1", "exitReason": "STOP",
                    "closedAt": NOW.date().isoformat() + "T09:20:00+05:30"}]
    fs.d[at.KEY] = json.dumps(d)
    at._RC.clear()
    box["cands"] = [cand("NIFTY", side="BUY")]
    at.run_cycle()
    assert [t["opt"] for t in saved(fs)["trades"] if t["status"] == "OPEN"] == ["CE"]     # the earlier call hit its stop; a new call (other contract) is taken


def test_a_reversed_exit_does_not_block_a_fresh_entry_on_either_side(world):
    box, fs = world
    _set_cfg(fs, indexMinAgree=1, indexMaxPerDay=3)
    d = saved(fs)
    d["trades"] = [{"id": "A-1", "sym": "NIFTY", "date": NOW.date().isoformat(), "status": "CLOSED", "kind": "index", "opt": "CE", "key": "K1", "exitReason": "REVERSE",
                    "closedAt": NOW.date().isoformat() + "T09:20:00+05:30"}]
    fs.d[at.KEY] = json.dumps(d)
    at._RC.clear()
    box["cands"] = [cand("NIFTY", side="BUY")]
    at.run_cycle()
    assert [t["opt"] for t in saved(fs)["trades"] if t["status"] == "OPEN"] == ["CE"]     # a new call entry after the reversal is taken


def test_majority_side_wins_and_a_tie_does_not_trade(world, monkeypatch):
    box, fs = world
    _set_cfg(fs, indexMinAgree=2, indexMaxPerDay=0)
    monkeypatch.setattr(at, "_screen_score", lambda: {})
    box["cands"] = [dict(cand("NIFTY", "index", "SELL"), agree=5, key="a"), dict(cand("NIFTY", "index", "BUY"), agree=2, key="b")]
    at.run_cycle()
    assert [t["opt"] for t in saved(fs)["trades"] if t["status"] == "OPEN"] == ["PE"]       # 5 bearish v 2 bullish: the put side
    d = saved(fs)
    d["trades"] = []
    fs.d[at.KEY] = json.dumps(d)
    at._RC.clear()
    box["cands"] = [dict(cand("BANKNIFTY", "index", "SELL"), agree=2, key="a"), dict(cand("BANKNIFTY", "index", "BUY"), agree=2, key="b")]
    at.run_cycle()
    assert not saved(fs)["trades"]                                                          # equal numbers: no view, no trade


def test_all_indices_with_the_same_signal_make_one_trade(world, monkeypatch):
    box, fs = world
    _set_cfg(fs, indexMinAgree=1, indexMaxPerDay=0)
    monkeypatch.setattr(at, "_screen_score", lambda: {})
    box["cands"] = [dict(cand("NIFTY", "index", "BUY"), agree=2, rank=1.0), dict(cand("SENSEX", "index", "BUY"), agree=3, rank=1.2),
                    dict(cand("FINNIFTY", "index", "BUY"), agree=2, rank=0.9), dict(cand("BANKNIFTY", "index", "SELL"), agree=2, rank=1.1)]
    at.run_cycle()
    got = sorted((t["sym"], t["opt"]) for t in saved(fs)["trades"] if t["status"] == "OPEN")
    assert got == [("BANKNIFTY", "PE"), ("SENSEX", "CE")]          # the best call, and the index that diverges (its own put); the other two calls are duplicates


def test_on_an_expiry_day_two_indices_may_take_the_same_side(world, monkeypatch):
    box, fs = world
    monkeypatch.setattr(at, "index_expiry_today", lambda today: True)
    _set_cfg(fs, indexMinAgree=1, indexMaxPerDay=0)
    monkeypatch.setattr(at, "_screen_score", lambda: {})
    box["cands"] = [dict(cand("NIFTY", "index", "BUY"), agree=2, rank=1.0), dict(cand("SENSEX", "index", "BUY"), agree=3, rank=1.2),
                    dict(cand("FINNIFTY", "index", "BUY"), agree=2, rank=0.9)]
    at.run_cycle()
    got = sorted(t["sym"] for t in saved(fs)["trades"] if t["status"] == "OPEN")
    assert got == ["NIFTY", "SENSEX"]                               # the two best calls; the third would be a third copy of the same view


def test_a_stock_is_not_bought_again_on_the_side_it_already_holds(world, monkeypatch):
    box, fs = world
    _set_cfg(fs, indexMinAgree=1, indexMaxPerDay=0, minAgreeStock=1)
    d = saved(fs)
    d["trades"] = [{"id": "A-1", "sym": "AAA", "date": NOW.date().isoformat(), "status": "OPEN", "kind": "stock", "opt": "CE", "key": "K-OLD", "side": "BUY", "entry": 100.0, "last": 100.0, "lot": 100, "lots": 1}]
    fs.d[at.KEY] = json.dumps(d)
    at._RC.clear()
    monkeypatch.setattr(at, "manage", lambda *a, **k: None)           # the held trade is only a marker here
    monkeypatch.setattr(at, "_screen_score", lambda: {"AAA": {"strength": 80}, "BBB": {"strength": 80}})
    import morning_picks
    monkeypatch.setattr(morning_picks, "good_rr", lambda *a, **k: True)
    box["cands"] = [dict(cand("AAA", "stock"), agree=2), dict(cand("BBB", "stock"), agree=2)]
    at.run_cycle()
    opened = sorted(t["sym"] for t in saved(fs)["trades"] if t["status"] == "OPEN" and t["id"] != "A-1")
    assert opened == ["BBB"]                                         # AAA already holds a call: the trade goes to another stock

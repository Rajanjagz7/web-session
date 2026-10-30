import auto_trader as at


def _t():
    return {"entry": 100.0, "lots": 1, "lot": 100, "pos": "long"}


def test_old_lock_breakeven_then_trail():
    t = _t(); at._profit_lock(t, 116.0, "old")          # +1,600 -> breakeven + charges
    assert t["lock"]["mode"] == "breakeven" and abs(t["premSL"] - 100.8) < 1e-6
    at._profit_lock(t, 122.0, "old")                    # +2,200 -> trail keeps 50%
    assert t["lock"]["mode"] == "trail" and t["lock"]["keep"] == 1100
    assert abs(t["premSL"] - (100 + 0.8 + 11)) < 1e-6
    at._profit_lock(t, 150.0, "old")                    # +5,000 -> 60% from 4k
    assert t["lock"]["keep"] == 3000


def test_new_lock_waits_for_2500():
    t = _t(); at._profit_lock(t, 122.0, "new")
    assert "lock" not in t and not t.get("premSL")
    at._profit_lock(t, 126.0, "new")                    # +2,600 -> breakeven
    assert t["lock"]["mode"] == "breakeven"


def test_defaults_eagle_off_old_lock():
    assert at.DEFAULT_CFG["eagleOn"] is True and at.DEFAULT_CFG["lockMode"] == "old"


def _screen_world(monkeypatch, hh, mm):
    import market_api
    from datetime import datetime
    calls = [{"instrument": "NIFTY", "signal": "BUY CALL", "entry": 100, "stopLoss": 90, "target1": 120, "strength": 80, "confidence": "high"},
             {"instrument": "BANKNIFTY", "signal": "BUY PUT", "entry": 100, "stopLoss": 90, "target1": 120, "strength": 70},
             {"instrument": "MIDCPNIFTY", "signal": "BUY CALL", "entry": 100, "stopLoss": 90, "target1": 120, "strength": 60}]
    monkeypatch.setattr(market_api, "quick_index_calls", lambda n: calls)
    monkeypatch.setattr(at, "_screen_score", lambda: {})
    monkeypatch.setattr(at, "_picks", lambda: {"picks": []})
    monkeypatch.setattr(at, "_now", lambda: datetime(2026, 10, 27, hh, mm, tzinfo=at.IST))
    today = "2026-10-27"
    stopped = {"id": "A-1", "sym": "NIFTY", "date": today, "status": "CLOSED", "closedAt": today + "T09:30:00+05:30", "kind": "index"}   # opened today, stopped out
    carried = {"id": "A-0", "sym": "MIDCPNIFTY", "date": "2026-10-23", "status": "CLOSED", "closedAt": today + "T09:07:00+05:30", "kind": "index"}   # opened earlier
    return today, {"cfg": {**at.DEFAULT_CFG, "stockOnly": False}, "trades": [stopped, carried], "log": []}


def test_index_can_be_entered_again_after_a_stop_and_in_the_same_option(monkeypatch):
    """user, 29 Oct: no restriction - the same index / stock option may be taken again once the earlier trade has closed."""
    today, st = _screen_world(monkeypatch, 9, 45)                       # stopped at 09:30, 15 minutes ago
    syms = {c["sym"] for c in at.fill_slots(st, today, []) if c.get("kind") == "index"}
    assert {"NIFTY", "MIDCPNIFTY"} <= syms
    st["trades"][0]["key"] = "NSE_FO|111"
    monkeypatch.setattr(at, "_contract", lambda *a, **k: {"expiry": "2026-11-10", "strike": 25000, "key": "NSE_FO|111", "premium": 100.0, "lot": 75, "spot": 25000.0, "bid": 99.0, "ask": 100.0})
    monkeypatch.setattr(at, "_atr_for", lambda sym: (100.0, 25000.0, [{"date": "2026-10-26"}] * 30))
    import backtest
    monkeypatch.setattr(backtest, "plan_risk", lambda *a, **k: 100.0)
    import pytest
    with pytest.raises(RuntimeError, match="already traded today"):      # 30 Oct (user): the very contract stopped out earlier today is refused, any other strike is fine
        at.open_trade(st, {"sym": "NIFTY", "side": "BUY", "kind": "index", "key": "x", "variant": "fixed"}, today)


def test_an_index_with_an_open_trade_is_still_screened(monkeypatch):
    """30 Oct (user): an open trade does not hide the index from the screen; open_trade refuses a second entry in the same direction / same contract."""
    today, st = _screen_world(monkeypatch, 9, 45)
    st["trades"][0].update(status="OPEN", closedAt=None)
    assert "NIFTY" in {c["sym"] for c in at.fill_slots(st, today, []) if c.get("kind") == "index"}


def test_day_break_is_45k_and_works_in_research_mode():
    st = {"cfg": {**at.DEFAULT_CFG}, "trades": [], "log": []}
    assert st["cfg"]["researchMode"] is True and st["cfg"]["dayPnlLimit"] == 45000.0

    def day(net):
        st["trades"] = [{"date": "2026-10-27", "status": "CLOSED", "net": net}]
        return at._day_guard(st, "2026-10-27")[0]
    assert day(-20000.0) == "off"
    assert day(-34000.0) == "soft"          # 75% of 45,000 = 33,750
    assert day(-45000.0) == "blocked"
    assert day(45500.0) == "blocked"        # the guard is symmetric: it also stops after +45k


def test_closing_a_short_at_a_missing_price_never_books_the_whole_premium():
    t = {"id": "A-1-W", "sym": "NIFTY", "pos": "short", "side": "BUY", "opt": "PE", "strike": 25000, "lot": 25, "lots": 2, "entry": 100.0,
         "last": 80.0, "status": "OPEN", "initialRisk": 1000}
    st = {"cfg": {**at.DEFAULT_CFG}, "trades": [t], "log": []}
    at._close(st, t, 0.0, "MANUAL")
    assert t["exit"] == 80.0                      # fell back to the last seen price, not 0
    assert t["gross"] == (100.0 - 80.0) * 50      # +1,000 (not +5,000 = the whole premium)


def test_pair_sell_setting_defaults_off_and_is_configurable():
    assert at.DEFAULT_CFG["pairSell"] is False
    assert "pairSell" in at.Cfg.model_fields


def test_stock_only_skips_the_index_screen(monkeypatch):
    import market_api
    calls = [{"instrument": "NIFTY", "signal": "BUY CALL", "entry": 100, "stopLoss": 90, "target1": 120, "strength": 80, "confidence": "high"}]
    called = []
    monkeypatch.setattr(at, "_picks", lambda: {"picks": []})
    monkeypatch.setattr(market_api, "quick_index_calls", lambda n: called.append(n) or calls)
    st = {"cfg": {**at.DEFAULT_CFG, "stockOnly": True}, "trades": [], "log": []}
    assert not at.DEFAULT_CFG["stockOnly"] and at.DEFAULT_CFG["buyOnly"] and at.DEFAULT_CFG["capital"] == 1000000.0
    assert at.fill_slots(st, "2026-10-28", []) == [] and not called


def test_sleeves_split_the_10_lakh_option_book():
    assert at.DEFAULT_CFG["sleeves"] == {"picks": 400000.0, "eagle": 200000.0, "signals": 400000.0, "old": 500000.0}
    assert sum(v for k, v in at.DEFAULT_CFG["sleeves"].items() if k != "old") == at.DEFAULT_CFG["capital"]      # the Rs 5 L OLD FILT sleeve is on top of the Rs 10 L
    assert at._sleeve_of("morning-pick") == "picks" and at._sleeve_of("Eagle Trades") == "eagle" and at._sleeve_of("Z Trend") == "signals" and at._sleeve_of({"key": "x", "strategies": ["a", "b"]}) == "old" and at._sleeve_of({"key": "stock-screen"}) == "old"
    st = {"cfg": {**at.DEFAULT_CFG}, "trades": [
        {"sleeve": "picks", "status": "CLOSED", "net": -12000.0}, {"sleeve": "eagle", "status": "CLOSED", "net": 5000.0},
        {"status": "CLOSED", "net": 99999.0},                                  # an old trade with no sleeve moves no sleeve
        {"sleeve": "picks", "status": "OPEN", "entry": 50.0, "lots": 2, "lot": 500, "last": 55.0}], "log": []}
    assert at._sleeve_equity(st, "picks") == 388000.0 and at._sleeve_equity(st, "eagle") == 205000.0 and at._sleeve_equity(st, "signals") == 400000.0
    assert at._sleeve_deployed(st, "picks") == 50000.0
    rows = {r["key"]: r for r in at.sleeve_report(st)}
    assert rows["picks"]["open"] == 1 and rows["picks"]["openPnL"] == 5000.0 and rows["eagle"]["net"] == 5000.0


def test_share_trader_opens_nothing_while_switched_off(monkeypatch):
    import stock_trader as sb, nse_calendar
    assert at.DEFAULT_CFG["stockTrader"] is True
    monkeypatch.setattr(nse_calendar, "session_open", lambda n: True)
    monkeypatch.setattr(sb.shared_cache, "lock", lambda *a, **k: True)
    monkeypatch.setattr(sb.shared_cache, "unlock", lambda *a, **k: None)
    monkeypatch.setattr(sb, "_load", lambda: {"trades": []})
    monkeypatch.setattr(sb, "_save", lambda st: True)
    monkeypatch.setattr(sb, "manage", lambda st, now: None)
    calls = []
    monkeypatch.setattr(sb, "enter", lambda st, now: calls.append(1) or ["X"])
    monkeypatch.setattr(at, "_load", lambda cached=False: {"cfg": {**at.DEFAULT_CFG, "stockTrader": False}})
    assert sb.run_cycle()["entered"] == [] and not calls
    monkeypatch.setattr(at, "_load", lambda cached=False: {"cfg": {**at.DEFAULT_CFG}})
    assert sb.run_cycle()["entered"] == ["X"] and calls


def test_index_options_are_bought_by_default(monkeypatch):
    import market_api
    calls = [{"instrument": "NIFTY", "signal": "BUY CALL", "entry": 100, "stopLoss": 90, "target1": 120, "strength": 80, "confidence": "high"}]
    monkeypatch.setattr(at, "_picks", lambda: {"picks": []})
    monkeypatch.setattr(market_api, "quick_index_calls", lambda n: calls)
    st = {"cfg": {**at.DEFAULT_CFG}, "trades": [], "log": []}
    out = at.fill_slots(st, "2026-10-28", [])
    assert [c["sym"] for c in out] == ["NIFTY"] and out[0]["kind"] == "index" and out[0]["side"] == "BUY"
    assert at._sleeve_of(out[0]["key"]) == "signals"


def test_entry_priority_by_strength_band_with_eagle_first_inside_a_band():
    pm = {"A": {"strength": 100}, "B": {"strength": 96}, "C": {"strength": 88}, "D": {"strength": 80}, "E": {"strength": 80}, "F": {"strength": 70}, "G": {"strength": 55}, "H": {"strength": 30}}
    rows = [{"kind": "stock", "sym": s, "key": "x"} for s in "HGFDCBA"] + [{"kind": "index", "sym": "NIFTY", "key": "x", "agree": 2}, {"kind": "stock", "sym": "E", "key": at.EAGLE}]
    assert [c["sym"] for c in sorted(rows, key=lambda c: at.entry_priority(c, pm))] == ["A", "B", "C", "E", "NIFTY", "D", "F", "G", "H"]

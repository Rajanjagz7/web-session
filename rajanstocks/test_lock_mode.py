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
    assert at.DEFAULT_CFG["eagleOn"] is False and at.DEFAULT_CFG["lockMode"] == "old"


def test_index_screen_never_reenters_same_index_after_a_stop(monkeypatch):
    import market_api
    calls = [{"instrument": "NIFTY", "signal": "BUY CALL", "entry": 100, "stopLoss": 90, "target1": 120, "strength": 80, "confidence": "high"},
             {"instrument": "BANKNIFTY", "signal": "BUY PUT", "entry": 100, "stopLoss": 90, "target1": 120, "strength": 70},
             {"instrument": "MIDCPNIFTY", "signal": "BUY CALL", "entry": 100, "stopLoss": 90, "target1": 120, "strength": 60}]
    monkeypatch.setattr(market_api, "quick_index_calls", lambda n: calls)
    monkeypatch.setattr(at, "_screen_score", lambda: {})
    import morning_picks
    monkeypatch.setattr(at, "_picks", lambda: {"picks": []})
    today = "2026-10-27"
    stopped = {"id": "A-1", "sym": "NIFTY", "date": today, "status": "CLOSED", "closedAt": today + "T09:30:00+05:30", "kind": "index"}   # opened today, stopped out
    carried = {"id": "A-0", "sym": "MIDCPNIFTY", "date": "2026-10-23", "status": "CLOSED", "closedAt": today + "T09:07:00+05:30", "kind": "index"}   # opened earlier
    st = {"cfg": {**at.DEFAULT_CFG}, "trades": [stopped, carried], "log": []}
    out = at.fill_slots(st, today, [])
    syms = {c["sym"] for c in out if c.get("kind") == "index"}
    assert "NIFTY" not in syms                # no re-entry after today's stop
    assert "MIDCPNIFTY" in syms               # a carried trade that exited at 09:07 does not block it


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

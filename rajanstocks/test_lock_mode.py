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

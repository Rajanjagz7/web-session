"""Morning shortlist: strength >= 75 first, Open = Low (BUY) / Open = High (SELL) second, 10-15 trades, good risk/reward only."""
import auto_trader
import morning_picks as mp


def pick(s, signal="BUY", strength=85, ltp=100.0, stop=97.0, atr=2.0, hi20=120.0, lo20=80.0, op=99.0, hi=101.0, lo=98.5, sec="A", **kw):
    return {"s": s, "kind": "stock", "universe": "fno", "sec": sec, "signal": signal, "strength": strength, "ltp": ltp, "stop": stop, "atr": atr,
            "hi20": hi20, "lo20": lo20, "open": op, "high": hi, "low": lo, "volx": 1.0, **kw}


def test_strength_75_with_room_is_tier_1():
    c = mp.classify(pick("A", strength=75))
    assert c["tier"] == 1 and c["side"] == "BUY"
    assert mp.classify(pick("A", strength=74))["tier"] == 3          # just below: only a fill-up
    assert mp.classify(pick("A", strength=100))["tier"] == 1


def test_open_low_buys_and_open_high_sells_as_tier_2():
    ol = pick("OL", signal="NEUTRAL", strength=25, op=100.0, lo=100.0, hi=101.0, ltp=100.6)
    oh = pick("OH", signal="NEUTRAL", strength=25, op=100.0, hi=100.0, lo=99.0, ltp=99.4)
    assert mp.open_flags(ol) == (True, False) and mp.open_flags(oh) == (False, True)
    assert (mp.classify(ol)["tier"], mp.classify(ol)["side"]) == (2, "BUY")
    assert (mp.classify(oh)["tier"], mp.classify(oh)["side"]) == (2, "SELL")


def test_open_equals_low_needs_price_above_the_open_and_a_signal_that_does_not_disagree():
    below = pick("X", signal="NEUTRAL", strength=25, op=100.0, lo=100.0, ltp=99.9)          # not trading above the open any more
    assert mp.open_flags(below)[0] is False
    against = pick("Y", signal="SELL", strength=50, op=100.0, lo=100.0, ltp=100.5, stop=103.0)
    assert mp.classify(against) is None or mp.classify(against)["side"] == "SELL"            # the screen says SELL: never BUY just because open = low


def test_tier_1_that_also_has_open_equals_low_ranks_above_plain_tier_1():
    plain = pick("P", strength=100, op=99.0, lo=98.0)
    both = pick("B", strength=80, op=100.0, lo=100.0, hi=101.0, ltp=100.6, stop=97.6)
    out = mp.select([plain, both])
    assert [r["s"] for r in out] == ["B", "P"] and out[0]["both"] is True


def test_priority_order_tier1_then_tier2_then_fill():
    t1 = pick("T1", strength=80)
    t2 = pick("T2", signal="NEUTRAL", strength=25, op=100.0, lo=100.0, hi=101.0, ltp=100.6)
    t3 = pick("T3", strength=60)
    out = mp.select([t3, t2, t1], min_n=3)
    assert [r["tier"] for r in out] == [1, 2, 3]


def test_poor_risk_reward_is_dropped():
    blocked = pick("W", ltp=100.0, hi20=102.0)            # the last 20 sessions' high is 0.7R away: no room for a 1.5R target
    assert mp.classify(blocked) is None
    wide = pick("V", ltp=100.0, stop=90.0, atr=4.0)       # stop 10% away
    assert mp.classify(wide) is None
    assert mp.classify(pick("F", ltp=100.0, hi20=99.0))["tier"] == 1         # already above the 20-session high: free air
    sell_blocked = pick("S", signal="SELL", ltp=100.0, stop=103.0, lo20=99.0)
    assert mp.classify(sell_blocked) is None


def test_fill_up_only_until_ten_and_never_more_than_fifteen():
    picks = [pick(f"S{i}", strength=80, sec=f"sec{i}") for i in range(20)]
    assert len(mp.select(picks)) == mp.MAX_PICKS
    weak = [pick(f"W{i}", strength=55, sec=f"sec{i}") for i in range(30)]
    assert len(mp.select(weak)) == mp.MIN_PICKS                  # tier 3 stops at 10
    mixed = [pick(f"S{i}", strength=80, sec=f"a{i}") for i in range(12)] + weak
    assert len(mp.select(mixed)) == 12                           # already above 10: no fill-up at all


def test_at_most_four_from_one_sector():
    picks = [pick(f"B{i}", strength=90, sec="BANKS") for i in range(8)] + [pick(f"I{i}", strength=70, sec="IT") for i in range(3)]
    out = mp.select(picks, max_n=15)
    assert sum(1 for r in out if r["sec"] == "BANKS") == mp.MAX_PER_SECTOR


def test_indices_are_not_in_the_stock_shortlist_and_levels_follow_the_side():
    idx = dict(pick("NIFTY", strength=100), kind="index")
    assert mp.select([idx]) == []
    oh = pick("OH", signal="BUY", strength=25, op=100.0, hi=100.0, lo=99.0, ltp=99.4, stop=96.0, atr=2.0)
    oh["signal"] = "NEUTRAL"
    r = mp.select([oh])[0]
    assert r["side"] == "SELL" and r["stop"] > r["entry"] > r["target"] > r["target2"]       # a short: stop above, targets below


def test_fill_slots_takes_the_shortlist_in_priority_order_and_at_most_15_a_day(monkeypatch):
    import market_api
    monkeypatch.setattr(market_api, "quick_index_calls", lambda n: [])
    picks = [pick("OLY", signal="NEUTRAL", strength=25, op=100.0, lo=100.0, hi=101.0, ltp=100.6),
             pick("TOP", strength=100), pick("MID", strength=80), pick("FILL", strength=60)]
    monkeypatch.setattr(market_api, "picks", lambda: {"picks": picks})
    st = {"cfg": dict(auto_trader.DEFAULT_CFG), "trades": [], "log": []}
    out = auto_trader.fill_slots(st, "2026-10-27", [])
    ranked = sorted(out, key=lambda c: -c["rank"])
    assert [c["sym"] for c in ranked] == ["TOP", "MID", "OLY", "FILL"]
    assert all(c["key"] == "morning-pick" for c in ranked)
    st["trades"] = [{"date": "2026-10-27", "kind": "stock", "strategy": "morning-pick", "sym": f"X{i}", "status": "OPEN"} for i in range(15)]
    assert auto_trader.fill_slots(st, "2026-10-27", []) == []                 # the day's 15 are already taken


def test_rows_without_hi20_use_the_spark_not_free_air():
    p = pick("C", ltp=100.0, spark=[96, 97, 98, 101.5, 99, 100])
    p.pop("hi20"); p.pop("lo20")
    assert mp.classify(p) is None                          # the 101.5 close 0.5R above blocks a BUY
    p["spark"] = [90, 91, 92, 93, 94, 100]
    assert mp.classify(p)["tier"] == 1                     # above every earlier close: room
    p.pop("spark")
    assert mp.classify(p) is None                          # nothing to judge the room by: not taken


def test_fill_slots_passes_the_shortlist_stop_to_the_trade(monkeypatch):
    import market_api
    monkeypatch.setattr(market_api, "quick_index_calls", lambda n: [])
    monkeypatch.setattr(market_api, "picks", lambda: {"picks": [pick("TOP", strength=100, stop=97.0)]})
    st = {"cfg": dict(auto_trader.DEFAULT_CFG), "trades": [], "log": []}
    c = auto_trader.fill_slots(st, "2026-10-27", [])[0]
    assert c["indStop"] == 97.0 and c["side"] == "BUY"

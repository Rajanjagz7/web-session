import pytest
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
    from datetime import datetime
    from datetime import timezone, timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    monkeypatch.setattr(auto_trader, "_now", lambda: datetime(2026, 10, 27, 11, 0, tzinfo=IST))   # tier 2 only after 09:20: fix the clock
    st = {"cfg": {**auto_trader.DEFAULT_CFG, "buyOnly": False, "stockOnly": False, "classicOnly": False}, "trades": [], "log": []}
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
    st = {"cfg": {**auto_trader.DEFAULT_CFG, "buyOnly": False, "stockOnly": False, "classicOnly": False}, "trades": [], "log": []}
    c = auto_trader.fill_slots(st, "2026-10-27", [])[0]
    assert c["indStop"] == 97.0 and c["side"] == "BUY"


def _eagle_pick(s, strength=85, **kw):
    return pick(s, strength=strength, op=100.0, lo=100.0, hi=101.0, ltp=100.6, stop=97.6, **kw)


def test_eagle_is_strength_75_with_open_equals_low_or_high_agreeing():
    assert mp.eagle(_eagle_pick("E"))["side"] == "BUY"
    sell = pick("S", signal="SELL", strength=85, op=100.0, hi=100.0, lo=99.0, ltp=99.4, stop=102.4)
    assert mp.eagle(sell)["side"] == "SELL"
    assert mp.eagle(_eagle_pick("W", strength=70)) is None                         # open = low but not strong enough
    assert mp.eagle(pick("P", strength=100)) is None                               # strong but price has already traded below the open
    assert mp.eagle(_eagle_pick("N", signal="NEUTRAL", strength=25)) is None
    assert mp.eagle(_eagle_pick("R", hi20=100.8))["side"] == "BUY"                  # no risk/reward gate: a 20-day high right above price does not block it
    assert mp.eagle(pick("X", signal="SELL", strength=90, op=100.0, lo=100.0, ltp=100.5)) is None   # open = low but the screen says SELL


def test_eagle_cands_have_no_cap_are_tagged_and_ranked_first(monkeypatch):
    import market_api
    from datetime import datetime
    picks = [_eagle_pick(f"E{i}", sec=f"s{i % 3}") for i in range(30)] + [pick("PLAIN", strength=100)]
    monkeypatch.setattr(market_api, "picks", lambda: {"picks": picks})
    monkeypatch.setattr(auto_trader, "_now", lambda: datetime(2026, 10, 27, 9, 35, tzinfo=auto_trader.IST))
    st = {"cfg": {**auto_trader.DEFAULT_CFG, "buyOnly": False, "stockOnly": False, "classicOnly": False}, "trades": [{"date": "2026-10-27", "sym": "E0", "status": "OPEN"}], "log": []}
    out = auto_trader.eagle_cands(st, "2026-10-27")
    assert len(out) == 29 and "E0" not in {c["sym"] for c in out}                  # all 30 qualify, minus the one already held; no 15-cap, no sector cap
    assert all(c["key"] == "Eagle Trades" and c["source"] == "Eagle Trades" and c["rank"] >= 20 for c in out)
    assert "PLAIN" not in {c["sym"] for c in out}


def test_eagle_only_scans_in_the_opening_hour(monkeypatch):
    import market_api
    from datetime import datetime
    monkeypatch.setattr(market_api, "picks", lambda: {"picks": [_eagle_pick("E")]})
    st = {"cfg": {**auto_trader.DEFAULT_CFG, "buyOnly": False, "stockOnly": False, "classicOnly": False}, "trades": [], "log": []}
    for hh, mm, n in ((9, 15, 0), (9, 20, 1), (10, 30, 1), (10, 31, 0), (14, 0, 0)):
        monkeypatch.setattr(auto_trader, "_now", lambda hh=hh, mm=mm: datetime(2026, 10, 27, hh, mm, tzinfo=auto_trader.IST))
        assert len(auto_trader.eagle_cands(st, "2026-10-27")) == n, (hh, mm)


def test_a_cycle_enters_eagle_trades_first_and_drops_duplicates(monkeypatch):
    import market_api
    import nse_calendar
    import rzt
    from datetime import datetime
    now = datetime(2026, 10, 27, 9, 36, tzinfo=auto_trader.IST)
    monkeypatch.setattr(auto_trader, "_now", lambda: now)
    monkeypatch.setattr(market_api, "picks", lambda: {"picks": [_eagle_pick("EAG"), pick("OTH", signal="SELL", strength=80, ltp=100.0, stop=103.0)]})   # OTH: a single signal, allowed because its strength is 75+
    monkeypatch.setattr(nse_calendar, "session_open", lambda n: True)
    st = {"cfg": {**auto_trader.DEFAULT_CFG, "buyOnly": False, "stockOnly": False, "classicOnly": False, "eagleOn": True}, "trades": [], "log": []}    # Eagle is off by default now
    monkeypatch.setattr(auto_trader, "_load", lambda cached=False: st)
    monkeypatch.setattr(auto_trader, "_save", lambda s: None)
    monkeypatch.setattr(auto_trader, "scan_all", lambda s, t: ([], "scan"))
    monkeypatch.setattr(auto_trader, "_timecycle_cands", lambda n: [])
    monkeypatch.setattr(rzt, "intraday_cands", lambda: [])
    dup = {"key": "morning-pick", "sym": "EAG", "side": "BUY", "kind": "stock", "score": 0.5, "rank": 11.0}
    other = {"key": "morning-pick", "sym": "OTH", "side": "SELL", "kind": "stock", "score": 0.5, "rank": 5.0}
    monkeypatch.setattr(auto_trader, "fill_slots", lambda s, t, already: [dup, other])
    rep = auto_trader._run_cycle(now, False, True)
    got = [(e["sym"], e["strategy"]) for e in rep["entered"]]
    assert got == [("EAG", "Eagle Trades"), ("OTH", "morning-pick")]               # Eagle first; the duplicate morning-pick for EAG is gone
    assert "1 Eagle trade(s)" in rep["note"]


def test_eagle_is_skipped_when_switched_off(monkeypatch):
    import market_api, nse_calendar, rzt
    from datetime import datetime
    now = datetime(2026, 10, 27, 9, 36, tzinfo=auto_trader.IST)
    monkeypatch.setattr(auto_trader, "_now", lambda: now)
    monkeypatch.setattr(market_api, "picks", lambda: {"picks": [_eagle_pick("EAG")]})
    monkeypatch.setattr(nse_calendar, "session_open", lambda n: True)
    st = {"cfg": {**auto_trader.DEFAULT_CFG, "buyOnly": False, "stockOnly": False, "classicOnly": False, "eagleOn": False}, "trades": [], "log": []}
    monkeypatch.setattr(auto_trader, "_load", lambda cached=False: st)
    monkeypatch.setattr(auto_trader, "_save", lambda s: None)
    monkeypatch.setattr(auto_trader, "scan_all", lambda s, t: ([], "scan"))
    monkeypatch.setattr(auto_trader, "_timecycle_cands", lambda n: [])
    monkeypatch.setattr(rzt, "intraday_cands", lambda: [])
    monkeypatch.setattr(auto_trader, "fill_slots", lambda s, t, already: [])
    rep = auto_trader._run_cycle(now, False, True)
    assert not any(e["strategy"] == "Eagle Trades" for e in rep["entered"])


def test_buy_only_buys_puts_for_sell_side_stock_picks(monkeypatch):
    """buy-only = options are only BOUGHT (never written): a bearish pick opens a PUT buy instead of being dropped."""
    import market_api
    monkeypatch.setattr(market_api, "quick_index_calls", lambda n: [])
    picks = [pick("OLY", signal="NEUTRAL", strength=25, op=100.0, lo=100.0, hi=101.0, ltp=100.6),
             pick("TOP", strength=100), pick("SHORT", signal="SELL", strength=95)]
    monkeypatch.setattr(market_api, "picks", lambda: {"picks": picks})
    st = {"cfg": dict(auto_trader.DEFAULT_CFG), "trades": [], "log": []}            # default = buy-only
    out = auto_trader.fill_slots(st, "2026-10-28", [])
    assert out and all(c["kind"] == "stock" for c in out)
    assert any(c["side"] == "SELL" for c in out)                                    # bearish pick -> put buy
    assert not any(c.get("key") == "rzt-hedge" or c.get("pos") == "short" for c in out)


def _chain(spot_field, step=100, centre=54000, expiry="2026-11-23"):
    rows = []
    for k in range(centre - 30 * step, centre + 31 * step, step):
        ce, pe = max(centre - k, 0) + 700, max(k - centre, 0) + 700                 # forward ~ centre
        rows.append({"strike": float(k), "ce": {"key": f"C{k}", "ltp": ce, "bid": ce - 1, "ask": ce + 1},
                     "pe": {"key": f"P{k}", "ltp": pe, "bid": pe - 1, "ask": pe + 1}})
    return {"rows": rows, "spot": spot_field, "atm": 0, "expiry": expiry, "expiries": [expiry], "lot": 30}


def test_contract_uses_live_spot_not_stale_chain_spot(monkeypatch):
    """28 Oct: a stale chain spot after a gap-up bought a deep in-the-money call. The strike now follows the live price."""
    import market_api
    monkeypatch.setattr(market_api, "chain", lambda sym, exp="": _chain(spot_field=52800.0))        # stale: previous close
    monkeypatch.setattr(auto_trader, "_live_spot", lambda sym, fb=0: 54010.0)                          # live: gapped up
    ct = auto_trader._contract("BANKNIFTY", "BUY", "2026-10-28", 3)
    assert ct["strike"] == 54000.0 and ct["spot"] == 54010.0                                          # ATM, not 52800
    ct = auto_trader._contract("BANKNIFTY", "SELL", "2026-10-28", 3)                                  # SELL signal = PUT bought
    assert ct["strike"] == 54000.0 and ct["key"].startswith("P")


def test_contract_refuses_an_in_the_money_strike(monkeypatch):
    """Even if the price feed is wrong, the option prices (call - put parity) show a strike far in the money: refuse it."""
    import market_api
    monkeypatch.setattr(market_api, "chain", lambda sym, exp="": _chain(spot_field=52800.0))
    monkeypatch.setattr(auto_trader, "_live_spot", lambda sym, fb=0: 52800.0)                          # wrong live price too
    with pytest.raises(RuntimeError, match="in the money"):
        auto_trader._contract("BANKNIFTY", "BUY", "2026-10-28", 3)


def test_option_stop_is_capped_at_12_5_percent_of_the_premium(monkeypatch):
    """28 Oct: stops of 30% of the premium were too wide. The premium stop is now at most premSlPct (12.5%) below the entry."""
    import backtest
    import market_api
    bars = [{"date": f"2026-10-{d:02d}", "open": 100, "high": 102, "low": 98, "close": 100} for d in range(1, 28)]
    monkeypatch.setattr(auto_trader, "_atr_for", lambda sym: (5.0, 100.0, bars))
    monkeypatch.setattr(auto_trader, "_contract", lambda *a, **k: {"expiry": "2026-11-23", "strike": 100.0, "key": "K", "premium": 200.0, "lot": 100, "spot": 100.0, "bid": 199, "ltp": 200})
    monkeypatch.setattr(auto_trader, "_now", lambda: __import__("datetime").datetime.fromisoformat("2026-10-28T10:00:00+05:30"))
    monkeypatch.setattr(backtest, "plan_risk", lambda *a, **k: 120.0)              # a wide signal-candle stop (30% of the premium would allow exactly this)
    st = {"cfg": dict(auto_trader.DEFAULT_CFG), "trades": [], "log": []}
    t = auto_trader.open_trade(st, {"key": "x", "sym": "ABC", "side": "BUY", "kind": "stock", "variant": "fixed", "score": 1}, "2026-10-28")
    assert t["premSL"] == pytest.approx(175.0, abs=0.01)                           # 200 - 12.5%
    assert t["riskU"] == pytest.approx(50.0, abs=0.01)
    st2 = {"cfg": {**auto_trader.DEFAULT_CFG, "premSlPct": 0.1}, "trades": [], "log": []}
    t2 = auto_trader.open_trade(st2, {"key": "x", "sym": "ABC", "side": "BUY", "kind": "stock", "variant": "fixed", "score": 1}, "2026-10-28")
    assert t2["premSL"] == pytest.approx(180.0, abs=0.01)                          # the setting wins


def test_banknifty_premium_budget_moves_to_the_nearest_otm_strike_that_fits(monkeypatch):
    """User 28 Oct: Bank Nifty options 10-15k max per trade -> ATM (~1,000 x lot 30 = 30k) is replaced by the nearest OTM strike under 15k."""
    import market_api
    centre = 54000

    def mk(k):
        ce = max(centre - k, 0) + max(1000 - 0.45 * max(k - centre, 0), 20)          # OTM calls cheaper by 0.45 per point
        pe = max(k - centre, 0) + max(1000 - 0.45 * max(centre - k, 0), 20)
        return {"strike": float(k), "ce": {"key": f"C{k}", "ltp": ce, "bid": ce - 1, "ask": ce + 1}, "pe": {"key": f"P{k}", "ltp": pe, "bid": pe - 1, "ask": pe + 1}}
    ch = {"rows": [mk(k) for k in range(centre - 3000, centre + 3001, 100)], "spot": 54010.0, "atm": 54000, "expiry": "2026-11-23", "expiries": ["2026-11-23"], "lot": 30}
    monkeypatch.setattr(market_api, "chain", lambda sym, exp="": ch)
    monkeypatch.setattr(auto_trader, "_live_spot", lambda sym, fb=0: 54010.0)
    atm = auto_trader._contract("BANKNIFTY", "BUY", "2026-10-28", 3)                    # no budget: ATM
    assert atm["strike"] == 54000.0 and atm["premium"] * 30 > 15000
    ce = auto_trader._contract("BANKNIFTY", "BUY", "2026-10-28", 3, 15000.0)
    assert ce["strike"] > 54000.0 and ce["premium"] * 30 <= 15000 and ce["premium"] * 30 > 12000      # nearest OTM that fits, not a far lottery ticket
    pe = auto_trader._contract("BANKNIFTY", "SELL", "2026-10-28", 3, 15000.0)            # bearish signal: put, strikes go DOWN
    assert pe["strike"] < 54000.0 and pe["key"].startswith("P") and pe["premium"] * 30 <= 15000
    with pytest.raises(RuntimeError, match="premium budget"):
        auto_trader._contract("BANKNIFTY", "BUY", "2026-10-28", 3, 100.0)

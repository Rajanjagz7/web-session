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
    assert t["last"] == 130.0 and t["mark"] == 129.8                # the LTP is shown as the LTP; the P&L is figured at the bid (what a stop or exit gets)
    assert t["unrealised"] == pytest.approx(3874.0) and s["summary"]["openPnL"] == 3874
    assert load()["last"] == 130.0 and load()["mark"] == 129.8      # and it is saved


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


def _ladder_trade():
    lad = [round(22900 + r * 100, 2) for r in at.TARGET_LADDER]                 # entryU 22900, riskU 100
    return trade(tgts=lad, tHit=0, targetU=lad[-1])


def test_target_ladder_moves_the_stop_one_target_behind_and_closes_at_10r(env):
    clock, prices = env
    st = json.load(open(at.FILE)); st["trades"] = [_ladder_trade()]; json.dump(st, open(at.FILE, "w"))
    seen = []
    for und, expect_hit, expect_stop in ((23000.0, 0, 22800.0),                 # +1R: nothing yet
                                         (23060.0, 1, 22900.0),                 # T1 (1.5R = 23050): stop to breakeven
                                         (23110.0, 2, 23050.0),                 # T2 (2R = 23100): stop at T1
                                         (23260.0, 3, 23100.0),                 # T3 (3R = 23200): stop at T2
                                         (23600.0, 6, 23400.0)):                # 7R: T6 (6R = 23500) reached, stop at T5 (5R = 23400)
        prices["und"] = und; prices["opt"] = 120.0
        clock["now"] = clock["now"] + timedelta(minutes=5)
        at._MARK_AT = 0.0
        st = at.status()
        t = (st["open"] or st["closed"])[0]
        seen.append((t["tHit"], t["stopU"]))
    assert seen[0] == (0, 22800.0) and seen[1] == (1, 22900.0) and seen[2] == (2, 23050.0) and seen[3] == (3, 23100.0)
    assert seen[4][0] == 6 and seen[4][1] == 23400.0                           # T6 reached: stop sits at T5 (5R = 23400)
    prices["und"] = 24000.0                                                     # 10R = 23900
    clock["now"] = clock["now"] + timedelta(minutes=5); at._MARK_AT = 0.0
    s = at.status()
    assert s["closed"] and s["closed"][0]["exitReason"] == "TARGET" and s["closed"][0]["tHit"] == 7


def test_ladder_trade_exits_on_the_trailed_stop(env):
    clock, prices = env
    st = json.load(open(at.FILE)); st["trades"] = [_ladder_trade()]; json.dump(st, open(at.FILE, "w"))
    prices["und"] = 23110.0; prices["opt"] = 125.0
    clock["now"] += timedelta(minutes=5); at._MARK_AT = 0.0; at.status()        # T2 reached -> stop 23050
    prices["und"] = 23040.0; prices["opt"] = 118.0
    clock["now"] += timedelta(minutes=5); at._MARK_AT = 0.0
    s = at.status()
    assert s["closed"] and s["closed"][0]["exitReason"] == "TSL"


def test_trades_opened_before_the_ladder_keep_the_old_single_target(env):
    clock, prices = env
    prices["und"] = 23100.0; prices["opt"] = 140.0                              # old trade: target 23100
    s = at.status()
    assert s["closed"] and s["closed"][0]["exitReason"] == "TARGET"


def test_a_gaping_or_one_sided_book_is_marked_at_the_last_traded_price(env, monkeypatch):
    clock, prices = env
    for depth in ({"buy": [{"price": 80.0}], "sell": [{"price": 100.0}]},        # 20% spread: not a price anyone could trade at
                  {"buy": [], "sell": [{"price": 100.0}]},                       # no bid at all
                  {}):                                                           # no depth
        monkeypatch.setattr(at, "_quotes", lambda keys, d=depth: {"NSE_FO|111": {"last_price": 120.0, "depth": d}, "NSE_INDEX|NIFTY": {"last_price": 22900.0}})
        monkeypatch.setattr(at, "_MARK_AT", 0.0)
        t = at.status()["open"][0]
        assert t["mark"] == 120.0 and t["unrealised"] == (120.0 - 100.0) * 2 * 65


def test_a_sold_option_is_marked_at_the_ask(env, monkeypatch):
    clock, prices = env
    st = json.load(open(at.FILE)); st["trades"][0].update(pos="short", premSL=130.0); json.dump(st, open(at.FILE, "w"))
    monkeypatch.setattr(at, "_quotes", lambda keys: {"NSE_FO|111": {"last_price": 90.0, "depth": {"buy": [{"price": 89.0}], "sell": [{"price": 91.0}]}},
                                                     "NSE_INDEX|NIFTY": {"last_price": 22900.0}})
    monkeypatch.setattr(at, "_MARK_AT", 0.0)
    t = at.status()["open"][0]
    assert t["mark"] == 91.0 and t["unrealised"] == pytest.approx((100.0 - 91.0) * 2 * 65)


def test_the_mark_and_the_stop_are_one_price(env):
    """The running P&L and the stop test use the same price: a trade whose P&L shows -30% is the one the stop (-30%) closes."""
    clock, prices = env
    prices["opt"] = 70.2                                            # bid 70.0 -> at the stop (premSL 70)
    s = at.status()
    assert not s["open"] and s["closed"][0]["exitReason"] == "STOP"


def test_pre_open_cycle_scans_but_never_trades(monkeypatch):
    """08:30-09:15 the cycle only warms the once-a-day indicator scan (no entries); outside that window a closed market does nothing."""
    import auto_trader as A
    import nse_calendar
    from datetime import datetime
    calls = []
    monkeypatch.setattr(nse_calendar, "session_open", lambda now: False)
    monkeypatch.setattr(nse_calendar, "is_trading_day", lambda d: True)
    monkeypatch.setattr(A, "_prewarm_scan", lambda now: calls.append(now) or {"ran": False, "reason": "market closed", "preOpenScan": "x"})
    for hh, mm, expect in ((8, 40, 1), (9, 10, 1), (8, 10, 0), (9, 16, 0), (16, 0, 0)):
        calls.clear()
        monkeypatch.setattr(A, "_now", lambda hh=hh, mm=mm: datetime(2026, 10, 30, hh, mm, tzinfo=A.IST))
        r = A.run_cycle()
        assert len(calls) == expect, (hh, mm, calls)
        assert r["ran"] is False


def test_indicator_groups_split_all_sources_in_two_without_overlap():
    import auto_trader as A
    assert not set(A.GROUP_A) & set(A.GROUP_B), "a source is in both groups"
    import backtest
    assert set(backtest._runners()) <= set(A.GROUP_A) | set(A.GROUP_B), "an indicator is in neither group"
    for key in ("index-call-put", "stock-screen", "morning-pick", "Eagle Trades", "timecycle", "gann-angle", "premium-rider", "rzt-intraday", "rzt-hedge"):
        assert key in A.GROUP_A or key in A.GROUP_B, key
    # each group has index AND stock sources (a daily indicator trades both)
    assert all(g and len(g) >= 7 for g in (A.GROUP_A, A.GROUP_B))
    assert A.profile_ok({"key": "ut-bot"}, "B") and not A.profile_ok({"key": "ut-bot"}, "A")
    assert A.profile_ok({"key": "ut-bot"}, "") and A.profile_ok({"key": "anything"}, None) in (True, False)


def _fake_tc(monkeypatch, last, vib, res, trend, cyc_min):
    import sys
    import types
    import auto_trader as A
    import rzt as R
    from datetime import datetime
    now = datetime(2026, 10, 30, 10, 15, tzinfo=A.IST)
    fake = types.SimpleNamespace(timecycle=lambda **k: {"last": last, "vibration": {"level": vib}, "nextResistance": {"level": res},
                                                        "cycles": [{"m": 10 * 60 + 15 + cyc_min, "time": "10:15", "strength": "strong"}]})
    monkeypatch.setitem(sys.modules, "vedic_api", fake)
    monkeypatch.setattr(R, "intraday_cands", lambda syms, fresh_min=15: [{"sym": syms[0], "side": trend, "key": "rzt-intraday"}] if trend else [])
    return A, now


def test_z_timecycle_needs_zone_time_and_trend_to_agree(monkeypatch):
    A, now = _fake_tc(monkeypatch, 22000.0, 22005.0, 22400.0, "BUY", 0)          # at support, Z Trend BUY, on the cycle time
    out = A._ztc_cands(now)
    assert out and out[0]["key"] == "z-timecycle" and out[0]["side"] == "BUY" and out[0]["kind"] == "index" and out[0]["indStop"] < 22000
    A, now = _fake_tc(monkeypatch, 22000.0, 22005.0, 22400.0, "SELL", 0)         # trend disagrees -> nothing
    assert A._ztc_cands(now) == []
    A, now = _fake_tc(monkeypatch, 22000.0, 22005.0, 22400.0, "BUY", 20)         # not on a cycle time -> nothing
    assert A._ztc_cands(now) == []
    A, now = _fake_tc(monkeypatch, 22000.0, 21800.0, 22005.0, "SELL", 4)         # at resistance, Z Trend SELL, 4 min off the cycle (window 5) -> SELL
    out = A._ztc_cands(now)
    assert out and out[0]["side"] == "SELL" and out[0]["indStop"] > 22000
    A, now = _fake_tc(monkeypatch, 22000.0, 22005.0, 22400.0, None, 0)           # no Z Trend flip today -> nothing
    assert A._ztc_cands(now) == []
    assert A.profile_ok({"key": "z-timecycle"}, "B") and not A.profile_ok({"key": "z-timecycle"}, "A")


def test_group_c_is_the_22_oct_set_plus_backtested_extras():
    import auto_trader as A
    for k in ("stock-screen", "index-call-put", "ut-bot", "rajan-ha-momentum", "z-timecycle"):
        assert A.profile_ok({"key": k, "kind": "stock", "side": "BUY"}, "C"), k
    assert not A.profile_ok({"key": "gann-angle"}, "C") and not A.profile_ok({"key": "rzt-hedge"}, "C")
    assert A.profile_ok({"key": "Eagle Trades", "side": "SELL"}, "C") and not A.profile_ok({"key": "Eagle Trades", "side": "BUY"}, "C")
    assert A.profile_ok({"key": "morning-pick", "source": "Today's Picks · tier 1 · x"}, "C") and not A.profile_ok({"key": "morning-pick", "source": "Today's Picks · tier 2 · x"}, "C")
    assert A.C_CFG["pairSell"] is True and A.C_CFG["premSlPct"] == 0.30

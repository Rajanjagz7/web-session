"""Upstox shared request budget: leases are small and adaptive, so unused permits are not burned.

A fake in-memory Redis stands in for Upstash; no network.
"""
import time

import pytest

import upstox_service as us


class FakeRedis:
    def __init__(self):
        self.kv, self.h = {}, {}

    def pipe(self, cmds, timeout=2.5):
        out = []
        for c in cmds:
            op, args = c[0], c[1:]
            if op in ("INCRBY", "DECRBY"):
                self.kv[args[0]] = int(self.kv.get(args[0], 0)) + (int(args[1]) if op == "INCRBY" else -int(args[1]))
                out.append({"result": self.kv[args[0]]})
            elif op == "GET":
                out.append({"result": self.kv.get(args[0])})
            elif op in ("EXPIRE", "SETEX"):
                if op == "SETEX":
                    self.kv[args[0]] = args[2]
                out.append({"result": 1})
            elif op == "HINCRBY":
                d = self.h.setdefault(args[0], {})
                d[args[1]] = d.get(args[1], 0) + int(args[2])
                out.append({"result": d[args[1]]})
            elif op == "HGETALL":
                flat = []
                for k, v in self.h.get(args[0], {}).items():
                    flat += [k, str(v)]
                out.append({"result": flat})
            else:
                raise AssertionError("unexpected command " + op)
        return out

    def counted(self):
        return sum(int(v) for k, v in self.kv.items() if k.startswith("rl2:a:"))


@pytest.fixture
def redis(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(us, "_redis_creds", lambda: ("http://fake", "tok"))
    monkeypatch.setattr(us, "_redis_pipe", r.pipe)
    return r


def fresh_instance():
    us._LS.update(left=0, exp=0.0, deny=0.0, b20=None, b10=None, n=1)


def test_cold_instances_that_make_one_call_waste_nothing(redis):
    for _ in range(30):                       # 30 separate serverless instances, one call each
        fresh_instance()
        us._lease_permit()
    assert redis.counted() == 30              # was 30 x 10 = 300 with the old fixed lease of 10


def test_busy_instance_leases_grow_but_stay_small(redis):
    fresh_instance()
    for _ in range(20):
        us._lease_permit()
    assert 20 <= redis.counted() <= 20 + us.LEASE_N       # at most one lease of slack


def test_idle_lease_is_handed_back_on_renewal(redis):
    fresh_instance()
    us._LS.update(left=3, exp=time.time() - 1, b20=int(time.time() // 20), b10=int(time.time() // 600))
    key = f"rl2:a:{us._LS['b20']}"
    redis.kv[key] = 3
    us._lease_permit()
    assert redis.kv[key] == 1                  # 3 unused permits returned, 1 new permit taken


def test_global_cap_refuses_and_gives_the_permit_back(redis):
    fresh_instance()
    b20 = int(time.time() // 20)
    redis.kv[f"rl2:a:{b20}"] = us.GLOBAL_PER_MIN       # the minute is already full
    with pytest.raises(us.UpstoxRateLimited):
        us._lease_permit()
    assert redis.kv[f"rl2:a:{b20}"] == us.GLOBAL_PER_MIN      # the refused permit was returned
    with pytest.raises(us.UpstoxRateLimited):                 # and it does not hammer Redis for a few seconds
        us._lease_permit()


def test_blocked_flag_stops_everyone(redis):
    fresh_instance()
    redis.kv["rl2:block"] = "1"
    with pytest.raises(us.UpstoxRateLimited):
        us._lease_permit()


def test_shared_tally_shows_who_spends(redis):
    fresh_instance()
    us._CALLERS.clear()
    us._FLUSHED.clear()
    us._CALLERS.update({"market_api.py:quotes": 5, "research_data.py:expired_candles": 2})
    us._lease_permit()
    usage = us.budget_usage()
    assert usage["allInstancesByCaller"] == {"market_api.py:quotes": 5, "research_data.py:expired_candles": 2}
    assert usage["limit60s"] == us.GLOBAL_PER_MIN


def test_caps_are_below_the_real_upstox_limits():
    assert us.GLOBAL_PER_MIN < 500 and us.GLOBAL_PER_30M < 2000


@pytest.fixture
def isolated_cache(tmp_path, monkeypatch):
    import shared_cache
    monkeypatch.setattr(shared_cache, "_DISK", str(tmp_path))
    monkeypatch.setattr(shared_cache, "_creds", lambda: None)
    shared_cache._MEM.clear()                       # the in-memory layer belongs to the (simulated) instance
    import market_api
    market_api._cache.clear()
    return market_api


def test_instances_share_one_upstox_answer(isolated_cache):
    ma = isolated_cache
    calls = {"n": 0}

    def ask():
        calls["n"] += 1
        return {"quotes": [1, 2, 3]}

    for _ in range(5):                         # five "instances" (their own memory caches are empty each time)
        ma._cache.clear()
        assert ma._shared("qs|test", 4, ask) == {"quotes": [1, 2, 3]}
    assert calls["n"] == 1


def test_running_out_of_budget_is_not_a_red_banner(isolated_cache, monkeypatch):
    ma = isolated_cache
    monkeypatch.setenv("UPSTOX_ACCESS_TOKEN", "not-a-jwt")
    monkeypatch.setattr(ma, "_key", lambda s: "NSE_INDEX|Nifty 50")

    def limited(keys):
        raise us.UpstoxRateLimited("The shared Upstox request budget is used up for the moment")

    monkeypatch.setattr(ma.nse_service.upstox, "_full_quotes", limited)
    out = ma.health()
    assert out["state"] == "ok" and "Busy" in out["message"]


def test_real_upstox_errors_still_raise_the_banner(isolated_cache, monkeypatch):
    ma = isolated_cache
    monkeypatch.setenv("UPSTOX_ACCESS_TOKEN", "not-a-jwt")
    monkeypatch.setattr(ma, "_key", lambda s: "NSE_INDEX|Nifty 50")

    def broken(keys):
        raise RuntimeError("Upstox API HTTP 401: invalid token")

    monkeypatch.setattr(ma.nse_service.upstox, "_full_quotes", broken)
    assert ma.health()["state"] == "expired"


def test_background_jobs_stop_at_their_share_while_live_screens_keep_going(redis):
    fresh_instance()
    b20 = int(time.time() // 20)
    redis.kv[f"rl2:a:{b20}"] = int(us.GLOBAL_PER_MIN * us.BG_MIN_SHARE)          # background share is used up
    with us.background():
        with pytest.raises(us.UpstoxRateLimited):
            us._lease_permit()
    assert redis.kv[f"rl2:a:{b20}"] == int(us.GLOBAL_PER_MIN * us.BG_MIN_SHARE)  # refused permit returned
    us._lease_permit()                                                           # a live screen is still served
    assert redis.kv[f"rl2:a:{b20}"] > us.GLOBAL_PER_MIN * us.BG_MIN_SHARE


def test_background_flag_nests_and_clears():
    assert getattr(us._BG, "on", 0) == 0
    with us.background():
        with us.background():
            assert us._BG.on == 2
        assert us._BG.on == 1
    assert us._BG.on == 0


def test_research_proxy_marks_calls_as_background_and_returns_429_when_busy(monkeypatch):
    import research_data as rd
    seen = {}

    class Fake:
        BASE_V2 = "x"

        def _get(self, url, **kw):
            seen["bg"] = us._BG.on
            raise us.UpstoxRateLimited("busy")

    import nse_service
    monkeypatch.setattr(nse_service.nse_service, "upstox", Fake())
    import shared_cache
    monkeypatch.setattr(shared_cache, "get", lambda k: None)
    with pytest.raises(Exception) as ei:
        rd.expired_candles("NSE_FO|1", "5minute", "2026-10-01", "2026-10-02")
    assert seen["bg"] == 1
    assert getattr(ei.value, "status_code", None) == 429 and ei.value.headers["Retry-After"] == "30"


def test_fresh_instance_serves_shared_last_prices_when_upstox_is_busy(isolated_cache, monkeypatch):
    ma = isolated_cache
    monkeypatch.setattr(ma, "ensure_universe", lambda: None)
    monkeypatch.setattr(ma, "_key", lambda s: "K|" + s)
    monkeypatch.setattr(ma.nse_service.upstox, "is_listed_equity", lambda s: True)
    state = {"busy": False}

    def full(keys):
        if state["busy"]:
            raise us.UpstoxRateLimited("budget")
        return {k: {"last_price": 100.0, "prev_close_price": 99.0, "ohlc": {"open": 99.5, "high": 101, "low": 99}, "volume": 5, "year_high": 120, "year_low": 80} for k in keys}

    monkeypatch.setattr(ma.nse_service.upstox, "_full_quotes", full)
    first = ma.quotes(symbols="AAA,BBB")
    assert first["stale"] is False and len(first["quotes"]) == 2
    state["busy"] = True
    import hashlib
    import os
    import shared_cache
    os.remove(shared_cache._file("qs|" + hashlib.md5(b"AAA,BBB").hexdigest()))      # the 4-second shared answer has expired
    ma._cache.clear(); ma._QSYM.clear(); ma._QLAST.clear(); shared_cache._MEM.clear()   # a brand-new instance: nothing in memory
    second = ma.quotes(symbols="AAA,BBB")
    assert second["stale"] is True and len(second["quotes"]) == 2


def test_refresh_inside_the_cooldown_is_served_from_cache(isolated_cache):
    ma = isolated_cache
    ma._REFRESH_AT.clear()
    assert ma._allow_refresh("daily") is True          # first refresh runs
    assert ma._allow_refresh("daily") is False         # an immediate second one is answered from the cache
    assert ma._allow_refresh("picks", 20, 120) is True  # other scans have their own clock
    ma._REFRESH_AT["daily"] -= 1000
    assert ma._allow_refresh("daily") is True          # and it runs again once the gap has passed


def test_unknown_symbol_quotes_answer_empty_not_503(isolated_cache, monkeypatch):
    ma = isolated_cache
    monkeypatch.setattr(ma, "ensure_universe", lambda: None)
    monkeypatch.setattr(ma.nse_service.upstox, "is_listed_equity", lambda s: s == "REALCO")
    monkeypatch.setattr(ma.nse_service.upstox, "_full_quotes", lambda keys: (_ for _ in ()).throw(AssertionError("must not call Upstox")))
    out = ma.quotes(symbols="EMBASSY")
    assert out["quotes"] == [] and out["missing"] == ["EMBASSY"]


def test_strategies_accept_any_listed_equity_but_not_reits(monkeypatch):
    import bar_source
    import nse_service
    monkeypatch.setattr(bar_source, "_universe", lambda: {"TCS"})
    monkeypatch.setattr(nse_service.nse_service.upstox, "is_listed_equity", lambda s: s in ("AADHARHFC",))
    assert bar_source.supports("TCS") and bar_source.supports("aadharhfc")
    assert not bar_source.supports("EMBASSY")

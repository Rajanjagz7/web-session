"""The cash-picks seed: the last FINISHED session's picks, from the server's own cache; nothing older, never written back as "today's"."""
import json
import os
from datetime import date

import pytest

os.environ.setdefault("VERCEL", "1")
import market_api as m  # noqa: E402
import shared_cache  # noqa: E402

THU = date(2026, 10, 29)          # previous trading day: Wed 28 Oct


def row(sym, strength=70, **kw):
    r = dict(s=sym, strength=strength, signal="BUY", score=3, ltp=100.0, universe="cash")
    r.update(kw)
    return r


@pytest.fixture
def redis(monkeypatch):
    store = {}
    monkeypatch.setattr(shared_cache, "get", lambda k: store.get(k))
    monkeypatch.setattr(shared_cache, "set", lambda k, v, ttl=None: store.__setitem__(k, v))
    monkeypatch.setattr(m, "_static_path", lambda name: None)               # no committed file unless a test adds one
    m._SEED_MEM.update(sig=None, rows={}, asof=None)
    return store


# ───────── which day counts ─────────
@pytest.mark.parametrize("today,prev", [
    (date(2026, 10, 29), "2026-10-28"),       # Thursday -> Wednesday
    (date(2026, 10, 26), "2026-10-23"),       # Monday -> Friday
    (date(2026, 10, 25), "2026-10-23"),       # Sunday -> Friday
    (date(2026, 11, 11), "2026-11-09"),       # the day after a holiday (Tue 10 Nov) -> Monday
])
def test_seed_is_the_last_finished_session(redis, today, prev):
    redis[f"picks:cash|{prev}"] = {"TCS": row("TCS")}
    rows, asof, fresh = m.cash_seed(today)
    assert fresh and asof == prev and list(rows) == ["TCS"]


def test_older_than_the_last_finished_session_is_not_used(redis):
    redis["picks:cash|2026-10-27"] = {"TCS": row("TCS")}                    # two sessions back
    rows, asof, fresh = m.cash_seed(THU)
    assert rows == {} and fresh is False and asof is None


def test_todays_own_key_is_not_the_seed(redis):
    redis["picks:cash|2026-10-29"] = {"TCS": row("TCS")}
    assert m.cash_seed(THU)[0] == {}


def test_empty_cache_and_a_broken_cache_give_nothing_not_an_error(redis, monkeypatch):
    assert m.cash_seed(THU) == ({}, None, False)
    monkeypatch.setattr(shared_cache, "get", lambda k: (_ for _ in ()).throw(RuntimeError("redis down")))
    assert m.cash_seed(THU) == ({}, None, False)
    redis["picks:cash|2026-10-28"] = ["not", "a", "dict"]
    monkeypatch.setattr(shared_cache, "get", lambda k: redis.get(k))
    assert m.cash_seed(THU)[0] == {}


# ───────── the committed file is only a dated fallback ─────────
def files(tmp_path, monkeypatch, asof, rows=None, meta=None):
    fp, mp = tmp_path / "picks_cash_seed.json", tmp_path / "picks_cash_seed.meta.json"
    fp.write_text(json.dumps(rows or {"INFY": row("INFY")}))
    if meta is not False:
        mp.write_text(meta if meta is not None else json.dumps({"asOf": asof}))
    monkeypatch.setattr(m, "_static_path", lambda name: str(fp if name == m.SEED_NAME else mp) if (fp if name == m.SEED_NAME else mp).exists() else None)


def test_dated_file_from_the_last_session_is_used_when_the_cache_is_empty(redis, tmp_path, monkeypatch):
    files(tmp_path, monkeypatch, "2026-10-28")
    rows, asof, fresh = m.cash_seed(THU)
    assert fresh and asof == "2026-10-28" and "INFY" in rows


@pytest.mark.parametrize("asof", ["2026-10-27", "2026-10-25", "2025-01-01"])
def test_old_dated_file_is_ignored(redis, tmp_path, monkeypatch, asof):
    files(tmp_path, monkeypatch, asof)
    rows, _, fresh = m.cash_seed(THU)
    assert rows == {} and fresh is False


@pytest.mark.parametrize("meta", [False, "not json", json.dumps({}), json.dumps({"asOf": "yesterday"}), json.dumps({"asOf": None})])
def test_file_without_a_valid_date_is_ignored(redis, tmp_path, monkeypatch, meta):
    files(tmp_path, monkeypatch, None, meta=meta)
    assert m.cash_seed(THU) == ({}, None, False)


def test_the_file_in_the_repo_today_is_not_used():
    """public/static/picks_cash_seed.json is the undated 25 Oct snapshot: it must never reach a screen."""
    m._SEED_MEM.update(sig=None, rows={}, asof=None)
    assert m.cash_seed(THU)[0] == {}


def test_cache_wins_over_the_file(redis, tmp_path, monkeypatch):
    files(tmp_path, monkeypatch, "2026-10-28")
    redis["picks:cash|2026-10-28"] = {"TCS": row("TCS")}
    assert list(m.cash_seed(THU)[0]) == ["TCS"]


# ───────── mixing with today's scan ─────────
def test_todays_scan_overrides_the_seed_and_unscanned_names_keep_their_seed_row(redis, monkeypatch):
    monkeypatch.setattr(m, "cash_seed", lambda today=None: ({"A": row("A", ltp=1), "B": row("B", ltp=2), "C": row("C", ltp=3)}, "2026-10-28", True))
    shown = {r["s"]: r for r in m._with_seed({"A": row("A", ltp=11)})}
    assert shown["A"]["ltp"] == 11 and shown["B"]["ltp"] == 2 and shown["C"]["ltp"] == 3


def test_a_name_the_walk_already_scanned_today_loses_its_seed_row(redis, monkeypatch):
    monkeypatch.setattr(m, "cash_seed", lambda today=None: ({"A": row("A"), "B": row("B")}, "2026-10-28", True))
    shown = {r["s"] for r in m._with_seed({}, walked={"A"})}                 # A was scanned today and fell under the strength floor
    assert shown == {"B"}


def test_no_seed_no_scan_is_just_empty(redis):
    assert m._with_seed({}) == []


# ───────── the payload ─────────
def test_payload_without_cash_rows_gets_the_fresh_seed_and_says_so(redis, monkeypatch):
    redis["picks:cash|2026-10-28"] = {"TCS": row("TCS", strength=80), "WEAK": row("WEAK", strength=40)}
    monkeypatch.setattr(m, "cash_seed", lambda today=None, _f=m.cash_seed: _f(THU))
    d = {"picks": [{"s": "NIFTY", "universe": "fno", "signal": "BUY", "score": 5, "volx": 1}], "count": 1}
    m._inject_cash_seed_if_needed(d)
    assert d["cashSeed"] == {"asOf": "2026-10-28", "fresh": True}
    assert [r["s"] for r in d["picks"]] == ["NIFTY", "TCS"] and d["count"] == 2 and [r["s"] for r in d["buy"]] == ["NIFTY", "TCS"]
    assert all(r["s"] != "WEAK" for r in d["picks"])                         # below the strength floor


def test_payload_with_a_stale_seed_gets_nothing_and_says_so(redis, monkeypatch):
    monkeypatch.setattr(m, "cash_seed", lambda today=None, _f=m.cash_seed: _f(THU))
    d = {"picks": [{"s": "NIFTY", "universe": "fno"}], "count": 1}
    m._inject_cash_seed_if_needed(d)
    assert d["cashSeed"] == {"asOf": None, "fresh": False} and d["count"] == 1 and len(d["picks"]) == 1


def test_payload_that_already_has_cash_rows_is_left_alone(redis, monkeypatch):
    redis["picks:cash|2026-10-28"] = {"TCS": row("TCS")}
    monkeypatch.setattr(m, "cash_seed", lambda today=None, _f=m.cash_seed: _f(THU))
    d = {"picks": [row("INFY")], "count": 1}
    m._inject_cash_seed_if_needed(d)
    assert [r["s"] for r in d["picks"]] == ["INFY"]


def test_non_dict_and_error_payloads_do_not_crash():
    assert m._inject_cash_seed_if_needed(None) is None
    assert m._inject_cash_seed_if_needed({"error": "x"})["cashSeed"]["fresh"] in (True, False)


def test_day_cache_is_kept_four_days_so_tomorrow_has_a_seed():
    assert m.CASH_DAY_TTL == 96 * 3600


def test_cash_seed_status_endpoint_answers_at_the_top_level(monkeypatch):
    import market_api
    monkeypatch.setattr(market_api, "cash_seed", lambda today=None: ({"A": {}, "B": {}}, "2026-10-28", True))
    monkeypatch.setattr(market_api, "_prev_trading_day", lambda d: __import__("datetime").date(2026, 10, 28))
    monkeypatch.setattr(market_api.shared_cache, "get", lambda k: {"x": 1})
    r = market_api.cash_seed_status()
    assert (r["asOf"], r["fresh"], r["symbols"], r["wanted"], r["source"]) == ("2026-10-28", True, 2, "2026-10-28", "server day cache")
    monkeypatch.setattr(market_api, "cash_seed", lambda today=None: ({}, None, False))
    r = market_api.cash_seed_status()
    assert r["fresh"] is False and r["symbols"] == 0 and r["source"] == "none" and "next session" in r["note"]

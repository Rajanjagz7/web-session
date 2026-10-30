"""A build that loses its F&O rows must not replace a good list with a cash-only one."""
import time

import market_api
import shared_cache


def test_failed_fno_build_keeps_the_last_good_rows(monkeypatch):
    store = {}
    monkeypatch.setattr(shared_cache, "get", lambda k, *a, **kw: store.get(k))
    monkeypatch.setattr(shared_cache, "set", lambda k, v, *a, **kw: store.__setitem__(k, v))
    monkeypatch.setattr(shared_cache, "lock", lambda *a, **k: True)
    monkeypatch.setattr(shared_cache, "unlock", lambda *a, **k: None)
    monkeypatch.setattr(market_api, "ensure_universe", lambda: None)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setattr(market_api, "_inject_cash_seed_if_needed", lambda v: None)
    monkeypatch.setattr(market_api, "_drop_cash_dupes", lambda v: None)
    monkeypatch.setattr(market_api, "_add_shortlist", lambda v: None)
    monkeypatch.setattr(market_api, "_add_industry", lambda v: None)
    good = {"picks": [{"s": f"F{i}", "universe": "fno"} for i in range(30)] + [{"s": "C1", "universe": "cash"}], "count": 31, "complete": False}
    bad = {"picks": [{"s": "C1", "universe": "cash"}], "count": 1, "complete": False}
    builds = iter([good, bad])
    monkeypatch.setattr(market_api, "_picks_compute", lambda *a, **k: dict(next(builds)))
    market_api._cache.pop("picks", None)
    r1 = market_api.picks(refresh=True)
    assert sum(1 for r in r1["picks"] if r["universe"] != "cash") == 30
    store.pop("picks|" + market_api.date.today().isoformat(), None)           # the 5-minute copy expired
    market_api._cache.pop("picks", None)
    r2 = market_api.picks(refresh=True)
    assert sum(1 for r in r2["picks"] if r["universe"] != "cash") == 30 and r2.get("stale")

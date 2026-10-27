"""/api/m/picks on Vercel: a failed rebuild serves the last good list (no 502) and always releases the build lock."""
import os
import pytest

os.environ["VERCEL"] = "1"
import market_api  # noqa: E402
import shared_cache  # noqa: E402


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    market_api._cache.pop("picks", None)
    monkeypatch.setattr(market_api, "ensure_universe", lambda: None)
    monkeypatch.setattr(market_api, "_inject_cash_seed_if_needed", lambda v: None)
    monkeypatch.setattr(market_api, "_add_shortlist", lambda v: None)
    yield
    market_api._cache.pop("picks", None)


def _boom(*a, **k):
    raise RuntimeError("upstream rate limited")


def test_failed_rebuild_serves_last_good_list(monkeypatch):
    good = {"picks": [{"s": "TCS"}], "count": 1, "_t": 1.0}
    store = {}
    monkeypatch.setattr(shared_cache, "get", lambda k: good if k.startswith("picks|") else store.get(k))
    monkeypatch.setattr(shared_cache, "lock", lambda k, t: True)
    unlocked = []
    monkeypatch.setattr(shared_cache, "unlock", lambda k: unlocked.append(k))
    monkeypatch.setattr(market_api, "_picks_compute", _boom)
    out = market_api.picks(refresh=True, response=None)
    assert out["picks"] == [{"s": "TCS"}] and out["stale"] is True
    assert unlocked == ["picks-build"]


def test_failed_rebuild_without_any_list_still_errors_and_unlocks(monkeypatch):
    from fastapi import HTTPException
    monkeypatch.setattr(shared_cache, "get", lambda k: None)
    monkeypatch.setattr(shared_cache, "lock", lambda k, t: True)
    unlocked = []
    monkeypatch.setattr(shared_cache, "unlock", lambda k: unlocked.append(k))
    monkeypatch.setattr(market_api, "_picks_compute", _boom)
    with pytest.raises(HTTPException) as ei:
        market_api.picks(refresh=False, response=None)
    assert ei.value.status_code == 502 and "upstream rate limited" in str(ei.value.detail)
    assert unlocked == ["picks-build"]


def test_does_not_release_someone_elses_lock(monkeypatch):
    monkeypatch.setattr(shared_cache, "get", lambda k: None)
    monkeypatch.setattr(shared_cache, "lock", lambda k, t: False)       # another request holds it
    monkeypatch.setattr(market_api.time, "sleep", lambda s: None)
    unlocked = []
    monkeypatch.setattr(shared_cache, "unlock", lambda k: unlocked.append(k))
    monkeypatch.setattr(market_api, "_picks_compute", lambda d: {"picks": [], "count": 0, "complete": False})
    market_api.picks(refresh=False, response=None)
    assert unlocked == []

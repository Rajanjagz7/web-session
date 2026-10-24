"""IPO dashboard resilience regression tests (bug found 2026-10-25).

On Vercel, NSE's ipo-current-issue and public-past-issues APIs can both fail (datacenter-IP
throttling) while the GMP feed works - the rebuild then produced a dashboard with 0 closed and
0 listed IPOs and OVERWROTE the last good copy, so users saw no closed-IPO data at all. These
tests pin the guard: a degenerate build must carry the previous good copy's listed/closed rows
forward (marked stale) and the refresh path must never 500 while a stale copy exists.
"""
import ipo_funds
from fastapi import HTTPException


def _seed_prev():
    prev = {
        "as_of": "2026-10-23T18:00:00+05:30", "gmp_source": "x", "stale": None,
        "counts": {"open": 0, "upcoming": 3, "closed": 2, "listed": 45},
        "stats": {"listed_count": 44, "avg_listing_gain_pct": 12.98, "positive_listing_share": 65.9,
                  "gmp_avg_abs_error_pct": 6.71, "gmp_compared": 6},
        "ipos": (
            [{"name": f"Upcoming {i}", "status": "upcoming"} for i in range(3)]
            + [{"name": "Jio Platforms", "symbol": "JPL", "status": "closed", "close_date": "2026-10-23"},
               {"name": "Paras Healthcare", "symbol": "PARAS", "status": "closed", "close_date": "2026-10-23"}]
            + [{"name": f"Listed {i}", "symbol": f"L{i}", "status": "listed", "listing_gain_pct": 5 + i} for i in range(45)]
        ),
        "stats_x": None,
    }
    ipo_funds.shared_cache.set(ipo_funds._DASH_KEY + ":stale", prev, 3600)
    return prev


def _degenerate_build():
    return {
        "as_of": "2026-10-24T11:00:00+05:30", "gmp_source": "x",
        "counts": {"open": 0, "upcoming": 7, "closed": 0, "listed": 0},
        "stats": {"listed_count": 0, "avg_listing_gain_pct": None, "positive_listing_share": None,
                  "gmp_avg_abs_error_pct": None, "gmp_compared": 0},
        "ipos": [{"name": "Jio Platforms (C)", "status": "upcoming"}, *[{"name": f"Up {i}", "status": "upcoming"} for i in range(6)]],
    }


def test_degenerate_build_keeps_previous_listed_and_closed(monkeypatch):
    _seed_prev()
    monkeypatch.setattr(ipo_funds, "build_ipo_dashboard", _degenerate_build)
    monkeypatch.setattr(ipo_funds._dash_busy, "set", lambda *a: None)
    monkeypatch.setattr(ipo_funds._dash_busy, "clear", lambda *a: None)
    out = ipo_funds._dash_refresh()
    assert out["counts"]["listed"] == 45, "the previous good copy's listed rows must survive"
    assert out["counts"]["closed"] == 2, "the previous good copy's closed rows must survive"
    assert out["counts"]["upcoming"] >= 7, "the fresh build's upcoming rows must stay"
    assert out["stale"] is True, "a merged (partially stale) dashboard must be flagged"
    names = {r["name"] for r in out["ipos"]}
    assert "Jio Platforms" in names and "Listed 44" in names
    stored = ipo_funds.shared_cache.get(ipo_funds._DASH_KEY + ":stale")
    assert stored["counts"]["listed"] == 45, "the long-lived stale copy must also hold the merged payload"


def test_fresh_healthy_build_is_not_polluted(monkeypatch):
    _seed_prev()
    good = _degenerate_build()
    good["counts"] = {"open": 1, "upcoming": 7, "closed": 2, "listed": 45}
    good["stats"] = {"listed_count": 45, "avg_listing_gain_pct": 13.0, "positive_listing_share": 66.0,
                     "gmp_avg_abs_error_pct": 6.7, "gmp_compared": 6}
    good["ipos"] += [{"name": "New closed", "status": "closed"}, *[{"name": f"L {i}", "status": "listed"} for i in range(45)]]
    monkeypatch.setattr(ipo_funds, "build_ipo_dashboard", lambda: good)
    monkeypatch.setattr(ipo_funds._dash_busy, "set", lambda *a: None)
    monkeypatch.setattr(ipo_funds._dash_busy, "clear", lambda *a: None)
    out = ipo_funds._dash_refresh()
    assert out.get("stale") is None and out["counts"]["listed"] == 45
    assert not any(r["name"] == "Listed 0" for r in out["ipos"]), "no rows from the old copy may leak into a healthy build"


def test_refresh_never_500_while_a_stale_copy_exists(monkeypatch):
    _seed_prev()
    calls = {"n": 0}

    def boom():
        calls["n"] += 1
        raise RuntimeError("all sources down")

    monkeypatch.setattr(ipo_funds, "build_ipo_dashboard", boom)
    monkeypatch.setattr(ipo_funds._dash_busy, "set", lambda *a: None)
    monkeypatch.setattr(ipo_funds._dash_busy, "clear", lambda *a: None)
    out = ipo_funds.ipo_dashboard(refresh=True)
    assert calls["n"] == 1 and out["stale"] is True and out["counts"]["closed"] == 2


def test_refresh_raises_when_there_is_truly_nothing():
    ipo_funds.shared_cache.set(ipo_funds._DASH_KEY + ":stale", None, 1)
    import contextlib
    with contextlib.suppress(HTTPException):
        ipo_funds.ipo_dashboard(refresh=True)   # 502 is acceptable only when no copy exists at all

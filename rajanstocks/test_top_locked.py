import time
from datetime import datetime
import market_api as m


def _row(s, strength, ltp=100.0, sec=None):
    # Open = Low BUY idea with strong score, good room
    return {"s": s, "n": s, "sec": sec or s, "kind": "stock", "universe": "fno", "signal": "BUY", "strength": strength, "ltp": ltp, "chg": 1.0,
            "open": ltp * 0.99, "high": ltp * 1.03, "low": ltp * 0.99, "volx": 1.5, "rsi": 60, "score": 4,
            "stop": ltp * 0.97, "hi20": ltp * 1.2, "lo20": ltp * 0.8, "atr": 2.0}


def _setup(monkeypatch, now_hm, open_=True):
    store = {}
    monkeypatch.setattr(m.shared_cache, "get", lambda k: store.get(k))
    monkeypatch.setattr(m.shared_cache, "set", lambda k, v, ttl=None: store.__setitem__(k, v))
    monkeypatch.setattr(m, "market_open", lambda: open_)
    class D(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 27, now_hm[0], now_hm[1], 0, tzinfo=m.IST)
    monkeypatch.setattr(m, "datetime", D)
    m._TOPF.update(day=None, rows=None, checked=0.0)
    return store


def _picks(strengths):
    return [_row(f"S{i}", st, sec=f"sec{i}") for i, st in enumerate(strengths)]


def test_not_locked_before_0920_and_when_incomplete(monkeypatch):
    store = _setup(monkeypatch, (9, 18))
    v = {"picks": _picks([90] * 12), "complete": True}
    m._add_shortlist(v)
    assert v.get("topLocked") is False and not store
    _setup(monkeypatch, (10, 0))
    v = {"picks": _picks([90] * 12), "complete": False}
    m._add_shortlist(v)
    assert v.get("topLocked") is False


def test_locks_then_ignores_reshuffle_but_updates_price(monkeypatch):
    store = _setup(monkeypatch, (9, 30))
    v1 = {"picks": _picks([95 - i for i in range(14)]), "complete": True}
    m._add_shortlist(v1)
    assert v1["topLocked"] is True and len(v1["top"]) >= 10
    first = [r["s"] for r in v1["top"]]
    # later the scan is reshuffled: strengths reversed, new prices, one name drops out entirely
    later = _picks([60 + i for i in range(13)])
    for r in later:
        r["ltp"] = 123.0; r["chg"] = -2.0
    v2 = {"picks": later, "complete": True}
    m._add_shortlist(v2)
    assert [r["s"] for r in v2["top"]] == first                       # same stocks, same order
    assert all(r["ltp"] == 123.0 for r in v2["top"] if r["s"] in {x["s"] for x in later})
    assert v2["top"][0]["entry"] == v1["top"][0]["entry"]            # levels stay as at lock time
    # another server instance (empty memory) reads the same list from the shared store
    m._TOPF.update(rows=None, checked=0.0)
    v3 = {"picks": later, "complete": True}
    m._add_shortlist(v3)
    assert [r["s"] for r in v3["top"]] == first

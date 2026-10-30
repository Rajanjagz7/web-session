from datetime import datetime, timezone, timedelta
import stock_trader as stt

IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime(2026, 10, 30, 10, 30, tzinfo=IST)


def _st():
    return {"trades": [], "log": [], "seq": 0}


def _run(monkeypatch, rows, quotes, now=NOW, st=None):
    monkeypatch.setattr(stt, "ipo_listed_today", lambda today: rows)
    monkeypatch.setattr(stt, "_quotes", lambda syms: quotes)
    st = st or _st()
    return st, stt.enter_ipo(st, now)


IPO = [{"symbol": "NEWCO", "name": "New Co", "series": "EQ", "listing_date": "2026-10-30"}]


def test_open_low_buys_open_high_sells(monkeypatch):
    st, ent = _run(monkeypatch, IPO, {"NEWCO": {"last": 102, "open": 100, "low": 100, "high": 103}})
    t = st["trades"][0]
    assert ent and t["side"] == "BUY" and t["ipo"] and t["hz"] == "intraday" and t["stop"] < t["entry"] < t["t1"] < t["t2"]
    st, ent = _run(monkeypatch, IPO, {"NEWCO": {"last": 98, "open": 100, "low": 97, "high": 100}})
    assert st["trades"][0]["side"] == "SELL" and st["trades"][0]["stop"] > st["trades"][0]["entry"]


def test_no_trade_without_open_signal_before_start_or_twice(monkeypatch):
    st, ent = _run(monkeypatch, IPO, {"NEWCO": {"last": 101, "open": 100, "low": 95, "high": 104}})
    assert ent == []
    q = {"NEWCO": {"last": 102, "open": 100, "low": 100, "high": 103}}
    st, ent = _run(monkeypatch, IPO, q, now=NOW.replace(hour=9, minute=30))
    assert ent == []
    st, ent = _run(monkeypatch, IPO, q)
    st, ent = _run(monkeypatch, IPO, q, st=st)
    assert len(st["trades"]) == 1


def test_per_day_cap_and_switch(monkeypatch):
    rows = [{**IPO[0], "symbol": f"N{i}"} for i in range(5)]
    q = {r["symbol"]: {"last": 102, "open": 100, "low": 100, "high": 103} for r in rows}
    st, ent = _run(monkeypatch, rows, q)
    assert len(ent) == 3
    monkeypatch.setitem(stt.CFG, "ipoOn", False)
    st, ent = _run(monkeypatch, rows, q)
    assert ent == []


def test_listed_filter_mainboard_today_only(monkeypatch):
    import ipo_funds
    monkeypatch.setattr(ipo_funds, "_cached", lambda k, ttl, fn, shared=True: [
        {"symbol": "A", "series": "EQ", "listing_date": "2026-10-30"}, {"symbol": "B", "series": "SME", "listing_date": "2026-10-30"},
        {"symbol": "C", "series": "EQ", "listing_date": "2026-10-29"}])
    assert [r["symbol"] for r in stt.ipo_listed_today("2026-10-30")] == ["A"]

"""Exit screen: the price shown is the price booked. Live quotes, bid/ask side, no price, price moved (boundary 3%), share trader."""
import pytest
from fastapi import HTTPException

import auto_trader as at
import stock_trader as sb
from test_book_integrity import FakeStore, book, trade  # noqa: F401  (FakeStore used by the store fixture)
import shared_cache


def quote(last, bid=None, ask=None):
    q = {"last_price": last}
    if bid is not None or ask is not None:
        q["depth"] = {"buy": [{"price": bid or 0}], "sell": [{"price": ask or 0}]}
    return q


@pytest.fixture
def store(monkeypatch):
    fs = FakeStore()
    monkeypatch.setattr(shared_cache, "kv", fs.kv)
    monkeypatch.setattr(at, "_remote", lambda: ("https://x.upstash.io", "t"))
    monkeypatch.setattr(shared_cache, "lock", lambda *a, **k: True)
    at._RC.clear()
    at._LIVE.update(at=0.0, keys=(), q={})
    yield fs
    at._RC.clear()


def put(store, *trades):
    st = at._load()
    st["trades"] = list(trades)
    assert at._save(st) is True


def feed(monkeypatch, quotes):
    box = {"q": quotes, "calls": 0}

    def _q(keys):
        box["calls"] += 1
        if isinstance(box["q"], Exception):
            raise box["q"]
        return box["q"]
    monkeypatch.setattr(at, "_quotes", _q)
    return box


# ───────── exit price: one rule for the preview and the booking ─────────
def test_long_exits_at_the_bid_short_at_the_ask():
    q = quote(100, bid=98, ask=102)
    assert at._exit_px(trade(), q) == 98
    assert at._exit_px(trade(pos="short"), q) == 102


def test_empty_book_side_falls_back_to_last_and_nothing_at_all_is_zero():
    assert at._exit_px(trade(), quote(100, bid=0, ask=102)) == 100
    assert at._exit_px(trade(pos="short"), quote(100, bid=98, ask=0)) == 100
    assert at._exit_px(trade(), {}) == 0
    assert at._exit_px(trade(), None) == 0
    assert at._exit_px(trade(), {"depth": {"buy": [], "sell": []}}) == 0          # empty depth lists do not crash


# ───────── /live ─────────
def test_live_returns_ltp_bid_ask_exit_price_and_pnl(store, monkeypatch):
    put(store, trade(entry=100.0, lots=2, lot=75))
    feed(monkeypatch, {"OPT1": quote(110, bid=108, ask=112)})
    r = at.live_prices()
    assert r["ok"] is True and len(r["trades"]) == 1
    x = r["trades"][0]
    assert (x["ltp"], x["bid"], x["ask"], x["exitPx"]) == (110, 108, 112, 108)
    assert x["mark"] == 108 and x["unrealised"] == pytest.approx(8 * 150)    # the running P&L is figured at the bid (what a stop / an exit gets)
    assert x["exitGross"] == pytest.approx(8 * 150)               # = the price an exit books
    assert x["at"] and r["at"]


def test_live_short_trade_pnl_has_the_right_sign(store, monkeypatch):
    put(store, trade(pos="short", entry=100.0))
    feed(monkeypatch, {"OPT1": quote(90, bid=88, ask=92)})
    x = at.live_prices()["trades"][0]
    assert x["exitPx"] == 92 and x["unrealised"] == pytest.approx(8 * 150) and x["exitGross"] == pytest.approx(8 * 150)


def test_live_ignores_closed_trades_and_does_not_call_the_broker_without_open_ones(store, monkeypatch):
    put(store, trade(status="CLOSED"))
    box = feed(monkeypatch, {})
    assert at.live_prices()["trades"] == [] and box["calls"] == 0


def test_live_broker_failure_is_reported_not_raised(store, monkeypatch):
    put(store, trade())
    feed(monkeypatch, RuntimeError("upstox down"))
    r = at.live_prices()
    assert r["ok"] is False and "upstox down" in r["error"] and r["trades"] == []


def test_live_missing_quote_gives_zero_prices_and_no_pnl(store, monkeypatch):
    put(store, trade())
    feed(monkeypatch, {})
    x = at.live_prices()["trades"][0]
    assert x["ltp"] == 0 and x["exitPx"] == 0 and x["unrealised"] is None and x["exitGross"] is None


def test_live_quotes_are_shared_for_a_few_seconds(store, monkeypatch):
    put(store, trade())
    box = feed(monkeypatch, {"OPT1": quote(100, bid=99, ask=101)})
    at.live_prices(); at.live_prices(); at.live_prices()
    assert box["calls"] == 1                                       # ten tabs polling do not mean ten broker calls
    at._LIVE["at"] -= 10                                           # after the ttl a fresh quote is taken
    box["q"] = {"OPT1": quote(105, bid=104, ask=106)}
    assert at.live_prices()["trades"][0]["ltp"] == 105 and box["calls"] == 2


# ───────── exit with the price the user saw ─────────
def exit_with(store, monkeypatch, quotes, seen=None, tid="A-1"):
    feed(monkeypatch, quotes)
    return at.manual_exit(tid, at.ExitBody(seen=seen) if seen is not None else None)


def test_exit_books_the_bid_the_screen_showed(store, monkeypatch):
    put(store, trade(entry=100.0))
    r = exit_with(store, monkeypatch, {"OPT1": quote(110, bid=108, ask=112)}, seen=108)
    assert r["ok"] and r["exit"] == 108.0


def test_exit_without_a_seen_price_still_works(store, monkeypatch):
    put(store, trade())
    assert exit_with(store, monkeypatch, {"OPT1": quote(110, bid=108, ask=112)})["exit"] == 108.0


@pytest.mark.parametrize("seen,moved", [(100.0, False), (97.1, False), (103.0, False), (97.0, True), (96.9, True), (103.1, True), (50.0, True), (200.0, True)])
def test_exit_refused_only_when_the_price_moved_more_than_3_percent(store, monkeypatch, seen, moved):
    put(store, trade())
    q = {"OPT1": quote(100, bid=100, ask=101)}                      # the exit price is 100
    if moved:
        with pytest.raises(HTTPException) as e:
            exit_with(store, monkeypatch, q, seen=seen)
        assert e.value.status_code == 409 and "100.00" in e.value.detail
        assert at._load()["trades"][0]["status"] == "OPEN"          # nothing was booked
    else:
        assert exit_with(store, monkeypatch, q, seen=seen)["exit"] == 100.0


def test_exit_with_no_live_price_is_refused_and_leaves_the_trade_open(store, monkeypatch):
    put(store, trade())
    with pytest.raises(HTTPException) as e:
        exit_with(store, monkeypatch, {"OPT1": {}}, seen=100.0)
    assert e.value.status_code == 503 and at._load()["trades"][0]["status"] == "OPEN"


def test_exit_when_the_broker_is_down_is_a_503(store, monkeypatch):
    put(store, trade())
    with pytest.raises(HTTPException) as e:
        exit_with(store, monkeypatch, RuntimeError("boom"))
    assert e.value.status_code == 503


def test_exit_unknown_and_already_closed_trade(store, monkeypatch):
    put(store, trade(), trade(id="A-2", status="CLOSED"))
    for tid, code in (("nope", 404), ("A-2", 400)):
        with pytest.raises(HTTPException) as e:
            exit_with(store, monkeypatch, {"OPT1": quote(100, bid=100, ask=101)}, tid=tid)
        assert e.value.status_code == code


def test_exit_all_books_each_trade_at_its_own_side_and_leaves_unpriced_ones(store, monkeypatch):
    put(store, trade(id="A-1", key="K1"), trade(id="A-2", key="K2", pos="short", entry=100.0), trade(id="A-3", key="K3"))
    feed(monkeypatch, {"K1": quote(110, bid=108, ask=112), "K2": quote(90, bid=88, ask=92), "K3": {}})
    r = at.exit_all()
    assert r["closed"] == 2 and len(r["failed"]) == 1 and "A-3" in r["failed"][0]
    by = {t["id"]: t for t in at._load()["trades"]}
    assert by["A-1"]["exit"] == 108.0 and by["A-2"]["exit"] == 92.0 and by["A-3"]["status"] == "OPEN"


def test_exit_all_with_nothing_open(store, monkeypatch):
    put(store)
    assert at.exit_all() == {"ok": True, "closed": 0, "net": 0, "failed": []}


# ───────── share trader ─────────
def stock_book(monkeypatch, quotes):
    st = {"cfg": dict(sb.CFG), "trades": [dict(id="S-1", sym="TCS", side="BUY", hz="swing", status="OPEN", entry=100.0, qty=10, risk=50.0, last=105.0, stop=95.0)], "log": []}
    monkeypatch.setattr(sb, "_quotes", lambda syms: quotes)
    monkeypatch.setattr(sb, "_mutate", lambda apply, *a, **k: apply(st))
    return st


def test_share_exit_books_the_live_price(monkeypatch):
    st = stock_book(monkeypatch, {"TCS": {"last": 120.0}})
    r = sb.manual_exit("S-1", sb.ExitBody(seen=120.0))
    assert r["ok"] and r["exit"] == 120.0 and st["trades"][0]["status"] == "CLOSED"


def test_share_exit_without_a_live_price_is_refused_not_booked_at_entry(monkeypatch):
    st = stock_book(monkeypatch, {})
    with pytest.raises(HTTPException) as e:
        sb.manual_exit("S-1")
    assert e.value.status_code == 503 and st["trades"][0]["status"] == "OPEN"      # used to close at the ENTRY price (a fake break-even)


def test_share_exit_price_moved_is_a_409(monkeypatch):
    st = stock_book(monkeypatch, {"TCS": {"last": 120.0}})
    with pytest.raises(HTTPException) as e:
        sb.manual_exit("S-1", sb.ExitBody(seen=110.0))
    assert e.value.status_code == 409 and st["trades"][0]["status"] == "OPEN"


def test_share_exit_all_closes_every_open_share_in_one_call_and_skips_unpriced(monkeypatch):
    st = stock_book(monkeypatch, {"TCS": {"last": 120.0}})
    st["trades"].append(dict(id="S-2", sym="INFY", side="SELL", hz="swing", status="OPEN", entry=100.0, qty=10, risk=50.0, last=99.0, stop=105.0))
    r = sb.exit_all()
    assert r["closed"] == 1 and r["failed"] == ["INFY: no live price"]                # the unpriced one stays open, nothing is booked at a guess
    assert [t["status"] for t in st["trades"]] == ["CLOSED", "OPEN"] and st["trades"][0]["exit"] == 120.0


def test_share_exit_unknown_trade(monkeypatch):
    stock_book(monkeypatch, {"TCS": {"last": 120.0}})
    with pytest.raises(HTTPException) as e:
        sb.manual_exit("nope")
    assert e.value.status_code == 404


def test_live_gaping_book_marks_at_the_last_traded_price(store, monkeypatch):
    put(store, trade(entry=100.0, lots=2, lot=75))
    feed(monkeypatch, {"OPT1": quote(110, bid=90, ask=120)})        # 25% spread
    x = at.live_prices()["trades"][0]
    assert x["mark"] == 110 and x["unrealised"] == pytest.approx(10 * 150) and x["exitPx"] == 90


# ───────── "Reset" must not let the same ideas be bought back (29 Oct) ─────────
def test_after_a_reset_what_was_traded_today_is_not_entered_again_until_tomorrow(monkeypatch):
    import auto_trader as at
    today = at._now().date().isoformat()
    st = {"trades": [{"id": "A-1", "sym": "ATUL", "date": today, "status": "OPEN"}, {"id": "A-2", "sym": "CUPID", "date": today, "status": "CLOSED", "closedAt": today + "T10:00:00+05:30"},
                     {"id": "A-0", "sym": "OLD", "date": "2026-10-01", "status": "CLOSED", "closedAt": "2026-10-02T10:00:00+05:30"}], "cand": {}, "log": [], "cfg": {}}
    monkeypatch.setattr(at, "_mutate", lambda apply, *a, **k: apply(st))
    at.reset_portfolio()
    assert st["trades"] == [] and st["cleared"]["syms"] == ["ATUL", "CUPID"]
    assert at._taken_syms(st, today) >= {"ATUL", "CUPID"} and "OLD" not in at._taken_syms(st, today)
    assert not (at._taken_syms(st, "2026-12-01") & {"ATUL", "CUPID"})                # a new day starts clean


def test_share_trader_reset_blocks_the_same_shares_today(monkeypatch):
    today = sb._now().date().isoformat()
    st = {"trades": [dict(id="S-1", sym="TCS", side="BUY", hz="swing", date=today, status="OPEN")], "log": [], "seq": 1}
    monkeypatch.setattr(sb, "_mutate", lambda apply, *a, **k: apply(st))
    sb.reset()
    assert st["trades"] == [] and st["cleared"] == {"date": today, "syms": ["TCS"]}


def test_fresh_start_clears_everything_before_the_cut_and_keeps_newer_trades(monkeypatch):
    import common
    from datetime import datetime
    monkeypatch.setattr(common, "FRESH_START_FROM", "2026-10-29T12:05:00+05:30")
    assert common.fresh_start_active(datetime.fromisoformat("2026-10-29T12:30:00+05:30"))
    assert common.before_fresh_start({"openedAt": "2026-10-29T11:45:00+05:30"})
    assert not common.before_fresh_start({"openedAt": "2026-10-29T12:11:00+05:30"})

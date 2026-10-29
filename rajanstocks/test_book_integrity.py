"""Regression tests for the 29 Oct 2026 review: day P&L, stop fills, bid/ask stop, failed scans, lost updates."""
import json
from datetime import datetime

import pytest

import auto_trader as at
import shared_cache

TODAY = "2026-10-29"
NOW = datetime(2026, 10, 29, 11, 0, tzinfo=at.IST)


def trade(**kw):
    t = dict(id="A-1", date="2026-10-28", sym="NIFTY", kind="index", side="BUY", opt="CE", strike=25000, expiry="2026-11-10",
             key="OPT1", lot=75, lots=2, entry=100.0, entryU=25000.0, stopU=24900.0, targetU=None, riskU=100.0, variant="fixed",
             bestU=25000.0, strategy="x", sleeve="signals", status="OPEN", last=100.0, plan="v2", premSL=87.5, premRisk=50, initialRisk=7500,
             tgts=[25150, 25200, 25300, 25400, 25500, 25600, 26000], tHit=0, openedAt="2026-10-28T10:00:00+05:30")
    t.update(kw)
    return t


def book(*trades):
    return {"cfg": dict(at.DEFAULT_CFG), "trades": list(trades), "log": []}


# ───────────── 1. day P&L ─────────────
def test_day_pnl_counts_the_move_since_the_start_of_today_not_since_entry():
    carried = trade(last=400.0)                                    # +300/unit since entry, but nothing has happened today yet
    st = book(carried)
    assert at._day_pnl(st, TODAY) == 0                             # the first look today fixes its base at the last mark
    at._day_base(carried, TODAY)
    carried["last"] = 410.0                                        # +10/unit today
    assert at._day_pnl(st, TODAY) == pytest.approx(10 * 150)


def test_trade_opened_earlier_and_stopped_out_today_counts_today():
    t = trade(status="CLOSED", closedAt=TODAY + "T10:00:00+05:30", exit=60.0, net=-6000.0, cost=40.0, last=60.0)
    t.update(baseDate=TODAY, basePx=100.0)
    st = book(t)
    assert at._day_pnl(st, TODAY) == pytest.approx((60 - 100) * 150 - 40)
    assert at._day_pnl(st, "2026-10-30") == 0                      # and not on any other day


def test_trade_opened_and_closed_today_counts_its_net():
    t = trade(date=TODAY, status="CLOSED", closedAt=TODAY + "T12:00:00+05:30", net=1234.0)
    assert at._day_pnl(book(t), TODAY) == 1234.0


def test_guard_does_not_block_because_of_a_carried_winner():
    st = book(trade(last=400.0))                                    # +45,000 since entry
    at._day_base(st["trades"][0], TODAY)
    assert at._day_guard(st, TODAY)[0] == "off"


def test_paired_short_does_not_inherit_the_main_legs_baseline(monkeypatch):
    main = trade(date=TODAY, entry=100.0, baseDate=TODAY, basePx=100.0, riskU=40.0, entryU=25000.0)
    ct = {"expiry": "2026-11-10", "strike": 25000, "key": "OPT2", "premium": 90.0, "lot": 75, "spot": 25000.0, "bid": 88.0, "ltp": 89.0}
    monkeypatch.setattr(at, "_contract", lambda *a, **k: ct)
    monkeypatch.setattr(at, "_now", lambda: NOW)
    st = book(main)
    s = at._open_short(st, {"sym": "NIFTY", "side": "BUY"}, TODAY, main)
    assert "baseDate" not in s and "basePx" not in s


# ───────────── 2 + 3. stop fills and the bid/ask stop ─────────────
def run_manage(monkeypatch, t, opt_last, bid, ask, und=25000.0):
    import market_api
    q = {t["key"]: {"last_price": opt_last, "depth": {"buy": [{"price": bid}], "sell": [{"price": ask}]}}, "UND": {"last_price": und}}
    monkeypatch.setattr(at, "_quotes", lambda keys: q)
    monkeypatch.setattr(market_api, "_key", lambda s: "UND")
    st = book(t)
    at.manage(st, NOW)
    return st["trades"][0]


def test_stop_in_a_gap_fills_at_the_price_seen_not_at_the_stop(monkeypatch):
    t = run_manage(monkeypatch, trade(), opt_last=62, bid=60, ask=64)       # entry 100, stop 87.5, the bid is 60
    assert t["status"] == "CLOSED" and t["exitReason"] == "STOP"
    assert t["exit"] == 60.0
    assert t["gross"] == pytest.approx((60 - 100) * 150)


def test_stop_just_crossed_fills_at_the_stop(monkeypatch):
    t = run_manage(monkeypatch, trade(), opt_last=87, bid=86.8, ask=87.4)   # 0.8% beyond the stop: inside the tolerance
    assert t["status"] == "CLOSED" and t["exit"] == 87.5


def test_short_stop_gap_fills_at_the_ask_seen(monkeypatch):
    short = trade(pos="short", side="BUY", opt="PE", entry=100.0, last=100.0, premSL=112.5, tgts=None)
    t = run_manage(monkeypatch, short, opt_last=140, bid=138, ask=142)
    assert t["status"] == "CLOSED" and t["exit"] == 142.0


def test_gaping_book_does_not_stop_a_flat_trade_out(monkeypatch):
    t = run_manage(monkeypatch, trade(entry=97.0, last=97.0, premSL=84.88), opt_last=92, bid=84.0, ask=94.0)   # bid 10.6% under the ask, last traded 92
    assert t["status"] == "OPEN"


def test_real_adverse_move_still_stops_through_a_gaping_book(monkeypatch):
    t = run_manage(monkeypatch, trade(entry=97.0, last=97.0, premSL=84.88), opt_last=80, bid=70.0, ask=90.0)
    assert t["status"] == "CLOSED" and t["exit"] == 80.0


def _open_with(monkeypatch, bid, ask):
    import backtest
    ct = {"expiry": "2026-11-10", "strike": 25000, "key": "OPT1", "premium": ask, "lot": 75, "spot": 25000.0, "bid": bid, "ask": ask, "ltp": ask}
    monkeypatch.setattr(at, "_contract", lambda *a, **k: ct)
    monkeypatch.setattr(at, "_atr_for", lambda sym: (100.0, 25000.0, [{"date": "2026-10-28"}] * 30))
    monkeypatch.setattr(backtest, "plan_risk", lambda *a, **k: 100.0)
    monkeypatch.setattr(at, "_now", lambda: NOW)
    st = book()
    return at.open_trade(st, {"sym": "NIFTY", "side": "BUY", "kind": "index", "key": "x", "variant": "fixed"}, TODAY)


def test_entry_refused_when_the_spread_eats_the_stop(monkeypatch):
    with pytest.raises(RuntimeError, match="too wide for the 12.5% stop"):
        _open_with(monkeypatch, bid=88.0, ask=100.0)               # 12% spread


def test_entry_allowed_on_a_tight_book(monkeypatch):
    t = _open_with(monkeypatch, bid=99.0, ask=100.0)               # 1%
    assert t["status"] == "OPEN" and t["entry"] == 100.0


def test_entry_allowed_on_a_normal_opening_spread(monkeypatch):
    t = _open_with(monkeypatch, bid=92.0, ask=100.0)               # 8%: common in the first minutes, must still trade
    assert t["status"] == "OPEN"


# ───────────── 4. failed indicator runs ─────────────
def test_failed_runs_are_retried_then_closed_after_three_tries():
    cache = {}
    assert at._scan_settle(cache, "TCS", None, 0) is False         # out of time: not final
    assert at._scan_settle(cache, "TCS", [], 0) is True            # clean run, nothing found: final
    assert at._scan_settle(cache, "INFY", [], 1) is False          # one failed indicator: try again next cycle
    assert at._scan_settle(cache, "INFY", [], 1) is False
    assert at._scan_settle(cache, "INFY", [], 2) is True           # third try: give up for the day (keep what was found)


# ───────────── 5. lost updates ─────────────
class FakeStore:
    def __init__(self):
        self.d = {}
        self.sets = 0

    def kv(self, cmds, timeout=6.0):
        out = []
        for c in cmds:
            if c[0] == "GET":
                out.append({"result": self.d.get(c[1])})
            elif c[0] == "GETRANGE":
                out.append({"result": (self.d.get(c[1]) or "")[c[2]:c[3] + 1]})
            elif c[0] == "SET":
                self.d[c[1]] = c[2]
                self.sets += 1
                out.append({"result": "OK"})
            else:
                out.append({"result": None})
        return out


@pytest.fixture
def store(monkeypatch):
    fs = FakeStore()
    monkeypatch.setattr(shared_cache, "kv", fs.kv)
    monkeypatch.setattr(at, "_remote", lambda: ("https://x.upstash.io", "t"))
    monkeypatch.setattr(shared_cache, "lock", lambda *a, **k: True)
    at._RC.clear()
    yield fs
    at._RC.clear()


def test_version_token_is_the_first_key_and_readable_cheaply(store):
    st = at._load()
    st["trades"].append(trade())
    assert at._save(st) is True
    raw = store.d[at.KEY]
    assert raw.startswith('{"ver": "') and at._ver_of(raw) == st["_ver0"]
    assert at._read_ver() == (True, st["_ver0"])


def test_a_stale_copy_cannot_overwrite_a_newer_book(store):
    first = at._load()
    first["trades"].append(trade(id="A-1"))
    assert at._save(first) is True
    a, b = at._load(), at._load()                                   # two instances read the same book
    a["trades"].append(trade(id="A-2"))
    assert at._save(a) is True
    b["trades"].append(trade(id="A-3"))
    assert at._save(b) == "conflict"                                # b is refused, nothing is overwritten
    assert [t["id"] for t in json.loads(store.d[at.KEY])["trades"]] == ["A-1", "A-2"]


def test_user_action_is_redone_on_the_newest_book(store):
    st = at._load()
    st["trades"].append(trade(id="A-1"))
    at._save(st)

    def rival():                                                    # a cycle on another instance saves a new trade after our read
        r = at._load()
        r["trades"].append(trade(id="A-2"))
        assert at._save(r) is True
    calls = []

    def apply(book_):
        calls.append(len(book_["trades"]))
        if len(calls) == 1:
            rival()                                                 # the stored book is now newer than the copy this apply works on
        book_["log"].append({"at": "x", "msg": "user action"})
        return {"ok": True}
    assert at._mutate(apply) == {"ok": True}
    saved = json.loads(store.d[at.KEY])
    assert [t["id"] for t in saved["trades"]] == ["A-1", "A-2"]     # the cycle's trade survived
    assert any(l["msg"] == "user action" for l in saved["log"])     # and so did the user's action
    assert calls == [1, 2]                                          # applied twice: once on the stale copy, once on the fresh one


def test_mutate_gives_409_when_it_keeps_losing(store, monkeypatch):
    monkeypatch.setattr(at.time, "sleep", lambda s: None)
    monkeypatch.setattr(at, "_save", lambda st: "conflict")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as e:
        at._mutate(lambda st: {"ok": True})
    assert e.value.status_code == 409


def test_unreadable_store_never_blocks_a_save(store, monkeypatch):
    st = at._load()
    monkeypatch.setattr(shared_cache, "read_ver", lambda key: (False, None))     # GETRANGE unsupported / store hiccup: skip the check, save anyway
    st["trades"].append(trade())
    assert at._save(st) is True and store.sets == 1


def test_old_unversioned_book_is_readable_and_upgraded(store):
    store.d[at.KEY] = json.dumps({"cfg": {"riskPct": 1.0}, "trades": [trade()], "log": []})
    st = at._load()
    assert st["_ver0"] is None and len(st["trades"]) == 1
    st["log"].append({"at": "x", "msg": "m"})
    assert at._save(st) is True and at._ver_of(store.d[at.KEY])


# ───────────── 6. everything the cycle saves is read back ─────────────
def test_cycle_state_survives_a_save_and_load(monkeypatch):
    """_save wrote shadow / skipUntil / dayGuardMode / idxWhy / carry but _load dropped them: failed candidates were retried every cycle
    (burning the 18 s budget), the paper-only signal log restarted empty each cycle, and the day-guard note was logged again every time."""
    fs = FakeStore()
    monkeypatch.setattr(at.shared_cache, "kv", fs.kv)
    monkeypatch.setattr(at, "_remote", lambda: ("https://x.upstash.io", "t"))
    at._RC.clear()
    st = at._load()
    st.update(shadow=[{"id": "s1", "status": "OPEN"}], skipUntil={"k|NIFTY|BUY": 9e12}, dayGuardMode="soft", idxWhy={"NIFTY": {"text": "x", "t": 1}}, carry=[{"sym": "NIFTY", "_exp": 9e12}])
    assert at._save(st) is True
    at._RC.clear()
    back = at._load()
    for k in at.PERSIST_KEYS:
        assert back.get(k) == st[k], k


# ───────────── 7. two refreshes must not show two different books ─────────────
def test_status_read_notices_a_save_made_by_another_instance(monkeypatch):
    """Instance A holds a 60 s copy; instance B closes a trade. A's next status read must show B's book, not its older copy."""
    fs = FakeStore()
    monkeypatch.setattr(at.shared_cache, "kv", fs.kv)
    monkeypatch.setattr(at, "_remote", lambda: ("https://x.upstash.io", "t"))
    at._RC.clear()
    a = at._load()
    a["log"].append({"at": "x", "msg": "v1"})
    assert at._save(a) is True
    assert any(l["msg"] == "v1" for l in at._load(cached=True)["log"])                  # A's own copy
    other = json.loads(fs.d[at.KEY])                                                      # B saves behind A's back
    other["log"].append({"at": "y", "msg": "v2 from B"})
    fs.d[at.KEY] = json.dumps({"ver": "b" * 16, **{k: v for k, v in other.items() if k != "ver"}})
    assert not any(l["msg"] == "v2 from B" for l in at._load(cached=True)["log"])       # unchecked read: the old copy (the flip)
    assert any(l["msg"] == "v2 from B" for l in at._load(cached=True, verify=True)["log"])   # verified read: the newest


def test_verified_read_uses_the_copy_when_nothing_changed_and_when_the_store_is_silent(monkeypatch):
    fs = FakeStore()
    monkeypatch.setattr(at.shared_cache, "kv", fs.kv)
    monkeypatch.setattr(at, "_remote", lambda: ("https://x.upstash.io", "t"))
    at._RC.clear()
    st = at._load()
    assert at._save(st) is True
    gets = []
    real = fs.kv
    monkeypatch.setattr(at.shared_cache, "kv", lambda cmds, t=8.0: (gets.append(cmds[0][0]), real(cmds, t))[1])
    at._load(cached=True, verify=True)
    assert gets == ["GETRANGE"]                                                           # one tiny version check, no full read
    monkeypatch.setattr(at.shared_cache, "read_ver", lambda key: (False, None))           # store silent: keep serving the copy
    gets.clear()
    at._load(cached=True, verify=True)
    assert gets == []


def test_cash_seed_export_returns_the_days_cash_rows_in_seed_format(monkeypatch):
    import json
    import market_api, shared_cache
    from datetime import date
    rows = {"AAA": {"s": "AAA", "ltp": 10.0, "universe": "cash"}}
    monkeypatch.setattr(shared_cache, "get", lambda k, *a, **kw: rows if k == f"picks:cash|{date.today().isoformat()}" else None)
    r = market_api.cash_seed_export()
    assert json.loads(r.body) == rows and r.headers["x-rows"] == "1" and "picks_cash_seed.json" in r.headers["content-disposition"]

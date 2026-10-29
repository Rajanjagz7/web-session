"""Share trader and push subscriptions use the same lost-update guard as the options auto trader (29 Oct 2026 review)."""
import json

import pytest
from fastapi import HTTPException

import push_signals as ps
import shared_cache
import stock_trader as sb
from test_book_integrity import FakeStore


@pytest.fixture
def store(monkeypatch):
    fs = FakeStore()
    monkeypatch.setattr(shared_cache, "kv", fs.kv)
    monkeypatch.setattr(shared_cache, "lock", lambda *a, **k: True)
    for m in (ps, sb):
        monkeypatch.setattr(m, "_remote", lambda: ("https://x.upstash.io", "t"))
        m._RC.clear()
    yield fs
    ps._RC.clear()
    sb._RC.clear()


SUB1 = {"endpoint": "https://fcm.googleapis.com/fcm/send/aaa", "keys": {}}
SUB2 = {"endpoint": "https://fcm.googleapis.com/fcm/send/bbb", "keys": {}}


def test_push_two_devices_subscribing_at_once_both_survive(store):
    stale = ps._load()                                              # instance A reads the (still empty) book
    ps.subscribe(ps.SubBody(subscription=SUB2))                     # instance B subscribes and saves first
    stale["subs"][SUB1["endpoint"]] = {"sub": SUB1, "at": "x"}      # A's change was made on the stale copy ...
    assert ps._save(stale, merge=False) == "conflict"               # ... which is refused, not written over B's
    ps.subscribe(ps.SubBody(subscription=SUB1))                     # A's request is redone on the newest book
    assert set(json.loads(store.d[ps.STATE_KEY])["subs"]) == {SUB1["endpoint"], SUB2["endpoint"]}


def test_push_unsubscribe_is_not_undone_by_a_merge(store):
    ps.subscribe(ps.SubBody(subscription=SUB1))
    ps.subscribe(ps.SubBody(subscription=SUB2))
    ps.unsubscribe(ps.SubBody(subscription=SUB1))
    assert set(json.loads(store.d[ps.STATE_KEY])["subs"]) == {SUB2["endpoint"]}


def test_push_cycle_save_merges_instead_of_erasing(store):
    st = ps._load()                                                 # a cycle reads the book ...
    ps.subscribe(ps.SubBody(subscription=SUB2))                     # ... a new device subscribes meanwhile ...
    st["seen"]["2999-01-01"] = ["idea-1"]
    st["sent"]["2999-01-01"] = {SUB1["endpoint"]: 1}
    st["log"].append({"at": "t", "id": "idea-1", "title": "T"})
    assert ps._save(st) is True                                     # ... the cycle's save is merged, not refused and not destructive
    saved = json.loads(store.d[ps.STATE_KEY])
    assert SUB2["endpoint"] in saved["subs"]
    assert any(l.get("id") == "idea-1" for l in saved["log"])


def test_push_subscribe_reports_failure_instead_of_pretending(store, monkeypatch):
    monkeypatch.setattr(ps, "_load", lambda: {"subs": {}, "sent": {}, "seen": {}, "log": [], "_readonly": True})
    with pytest.raises(HTTPException) as e:
        ps.subscribe(ps.SubBody(subscription=SUB1))
    assert e.value.status_code == 503


def test_share_trader_stale_copy_is_refused_and_manual_exit_redone(store, monkeypatch):
    st = sb._load()
    st["trades"].append({"id": "S-1", "sym": "TCS", "status": "OPEN", "date": "2026-10-29", "hz": "swing", "entry": 100.0, "qty": 10, "side": "BUY", "last": 100.0})
    assert sb._save(st) is True
    a, b = sb._load(), sb._load()
    a["log"].append({"at": "x", "msg": "a"})
    assert sb._save(a) is True
    b["log"].append({"at": "y", "msg": "b"})
    assert sb._save(b) == "conflict"
    msgs = [l["msg"] for l in json.loads(store.d[sb.KEY])["log"]]
    assert msgs == ["a"]                                            # b did not overwrite a


def test_share_trader_reset_goes_through_the_guard(store):
    st = sb._load()
    st["trades"].append({"id": "S-1", "sym": "TCS", "status": "OPEN", "date": "2026-10-29", "hz": "swing", "entry": 1.0, "qty": 1, "side": "BUY"})
    sb._save(st)
    assert sb.reset() == {"ok": True}
    saved = json.loads(store.d[sb.KEY])
    assert saved["trades"] == [] and saved["seq"] == 0 and shared_cache.ver_of(store.d[sb.KEY])

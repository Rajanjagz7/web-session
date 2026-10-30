import push_signals as ps


def _world(monkeypatch, subs=1):
    st = {"subs": {f"ep{i}": {"sub": {"endpoint": f"https://x/{i}"}} for i in range(subs)}, "seen": {}, "sent": {}, "log": []}
    sent = []
    monkeypatch.setattr(ps, "_load", lambda: st)
    monkeypatch.setattr(ps, "_save", lambda s, merge=True: True)
    monkeypatch.setattr(ps, "_send", lambda sub, title, body, url="", tag=None: sent.append(title) or "ok")
    return st, sent


def test_lock_alerts_are_silent_by_default_and_everything_stops_at_five_a_day(monkeypatch):
    st, sent = _world(monkeypatch)
    for i in range(ps.MAX_TRADE_PER_DAY + 2):
        ps.notify_all(f"auto|{i}", f"PAPER ENTRY {i}", "b", kind="trade")
    assert len([t for t in sent if t.startswith("PAPER")]) == ps.MAX_TRADE_PER_DAY            # entries stop at 5 a day
    assert ps.notify_all("auto-lock|A-1|breakeven", "PROFIT LOCKED A-1", "b", kind="lock") == 0     # stop-moved alerts stay in the app (user 29 Oct)
    assert not any("LOCKED" in t for t in sent) and len(sent) == ps.MAX_TRADE_PER_DAY


def test_total_pushes_per_phone_never_pass_five_across_ideas_trades_and_locks(monkeypatch):
    st, sent = _world(monkeypatch)
    monkeypatch.setattr(ps, "MAX_LOCK_PER_DAY", 20)
    for i in range(ps.MAX_TOTAL_PER_DAY - 1):
        ps.notify_all(f"auto|{i}", f"ENTRY {i}", "b", kind="trade")
    for i in range(6):
        ps.notify_all(f"auto-lock|{i}", f"LOCK {i}", "b", kind="lock")
    ps.notify_all("idea|1", "IDEA", "b", kind="idea")
    assert len(sent) == ps.MAX_TOTAL_PER_DAY == 10


def test_the_reason_a_push_failed_is_recorded(monkeypatch):
    st, sent = _world(monkeypatch)
    monkeypatch.setattr(ps, "_send", lambda *a, **k: "no-key")
    ps.notify_all("auto|1", "t", "b")
    assert st["lastFail"]["result"] == "no-key"
    st2, _ = _world(monkeypatch, subs=0)
    ps.notify_all("auto|2", "t", "b")
    assert "no subscribed device" in st2["lastFail"]["result"]


def test_profit_lock_alert_is_on_and_uses_the_lock_budget(monkeypatch):
    import auto_trader as at
    assert at.PUSH_LOCKS is True
    got = []
    monkeypatch.setattr(ps, "notify_all", lambda idem, title, body, url="", kind="trade", bucket=None: got.append((idem, kind)))
    t = {"id": "A-1", "sym": "NIFTY", "strike": 25000, "opt": "CE", "entry": 100.0, "lots": 1, "lot": 100, "pos": "long"}
    at._profit_lock(t, 116.0, "old")
    assert got and got[0][1] == "lock" and got[0][0].startswith("auto-lock|A-1")


def test_signal_ideas_are_pushed_again_and_the_cron_can_run_only_the_pushes(monkeypatch):
    import auto_trader as at
    assert ps.PUSH_FROM_AUTO_ONLY is False
    calls = []
    monkeypatch.setattr(at, "run_cycle", lambda *a, **k: calls.append("auto"))
    monkeypatch.setattr(ps, "run_cycle", lambda *a, **k: calls.append("push") or {"ran": True})
    monkeypatch.delenv("CRON_SECRET", raising=False)
    ps.cron(only="push")
    assert calls == ["push"]
    calls.clear()
    ps.cron()
    assert calls == ["auto", "push"]


def test_two_signal_runs_at_once_send_once(monkeypatch):
    import shared_cache
    st, sent = _world(monkeypatch)
    monkeypatch.setattr(ps, "market_hours", lambda now=None: True)
    monkeypatch.setattr(ps, "PUSH_FROM_AUTO_ONLY", False)
    monkeypatch.setattr(ps, "collect", lambda today=None: [{"id": "x|1", "title": "T1", "body": "b", "rank": 1}])
    monkeypatch.setattr(shared_cache, "lock", lambda name, ttl: not sent)         # granted to the first caller only (nothing sent yet)
    a = ps.run_cycle()
    b = ps.run_cycle()
    assert a["ran"] and len(sent) == 1 and b == {"ran": False, "reason": "another run is in progress"}

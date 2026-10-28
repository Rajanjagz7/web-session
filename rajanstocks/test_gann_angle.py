import gann_angle as g


def _bars():
    b = []
    for i in range(21):
        b.append(dict(t=i, o=100 - i * .3 + .1, h=100 - i * .3 + .5, l=100 - i * .3 - .5, c=100 - i * .3))
    for i in range(21, 56):
        px = 94 + (i - 20) * 1.5
        b.append(dict(t=i, o=px - .2, h=px + .5, l=px - .5, c=px + .2))
    for i in range(56, 66):
        px = 146 - (i - 55) * 1.5
        b.append(dict(t=i, o=px + 1, h=px + 1.4, l=px - .3, c=px))
    return b


def _with_bounce(close_off):
    b, v = _bars(), 130.0
    for _ in range(20):
        v = g.line_value(b + [dict(t=99, o=v + .5, h=v + 6, l=v, c=v + 3)], "BUY")[0][-1]
    return b + [dict(t=99, o=v + .5, h=v + 6, l=v, c=v + close_off)], v


def test_support_bounce_is_a_buy():
    t, v = _with_bounce(3)
    r = g.bounce(t)
    assert r and r["side"] == "BUY" and r["stop"] < v and r["target"] > r["px"]


def test_close_under_the_line_is_no_trade():
    t, v = _with_bounce(-1)
    assert g.bounce(t) is None


def test_too_few_bars():
    assert g.bounce(_bars()[:10]) is None


def test_classic_mode_shadows_the_extras(monkeypatch):
    import datetime as dt
    import auto_trader as a
    monkeypatch.setattr(a, "_live_spot", lambda s, fallback=0.0: 100.0)
    st = {"shadow": []}
    now = dt.datetime(2026, 10, 29, 10, 0)
    a.shadow_record(st, [{"key": "gann-angle", "sym": "NIFTY", "side": "BUY", "indStop": 98.0},
                         {"key": a.EAGLE, "sym": "TCS", "side": "SELL", "indStop": 102.0},
                         {"key": "rzt-intraday", "sym": "SBIN", "side": "BUY", "indStop": 99.0}], now)
    assert {x["key"] for x in st["shadow"]} == {"gann-angle", a.EAGLE, "rzt"}
    assert all(x["target"] != x["entry"] for x in st["shadow"])
    assert {"morning-pick", a.EAGLE, "gann-angle", "timecycle"} <= a.SHADOW_KEYS
    assert a.shadow_summary(st)[0]["n"] == 1


def test_classic_stock_screen_candidates(monkeypatch):
    import market_api
    from datetime import datetime
    from zoneinfo import ZoneInfo
    import auto_trader as a
    monkeypatch.setattr(market_api, "quick_index_calls", lambda n: [])
    row = dict(s="AAA", kind="stock", universe="fno", signal="BUY", strength=70, ltp=100.0, op=100.0, lo=99.0, hi=101.0, volx=1.5, h20=110.0, l20=90.0, atr=2.0)
    monkeypatch.setattr(market_api, "picks", lambda: {"picks": [row]})
    monkeypatch.setattr(a, "_now", lambda: datetime(2026, 10, 29, 11, 0, tzinfo=ZoneInfo("Asia/Kolkata")))
    st = {"cfg": dict(a.DEFAULT_CFG), "trades": [], "log": []}
    out = a.fill_slots(st, "2026-10-29", [])
    assert all(c["key"] != "morning-pick" for c in out)


def test_classic_filter_extras_need_a_classic_agreement():
    import auto_trader as a
    ent = [dict(sym="NIFTY", side="BUY", key="index", label="index call/put screen"), dict(sym="NIFTY", side="BUY", key="gann-angle", source="Gann"),
           dict(sym="TCS", side="BUY", key=a.EAGLE), dict(sym="SBIN", side="SELL", key="stock-screen"), dict(sym="SBIN", side="BUY", key="gann-angle")]
    kept, paper = a.classic_filter(ent)
    assert sorted((c["sym"], c["key"]) for c in kept) == [("NIFTY", "index"), ("SBIN", "stock-screen")]
    kept, paper = a.classic_filter(ent, True)
    assert sorted((c["sym"], c["key"]) for c in kept) == [("NIFTY", "gann-angle"), ("SBIN", "stock-screen")]
    assert "agrees with" in kept[0]["source"] or "agrees with" in kept[1]["source"]
    assert sorted((c["sym"], c["side"]) for c in paper) == [("SBIN", "BUY"), ("TCS", "BUY")]


def test_share_trader_takes_only_the_stock_only_tab(monkeypatch):
    import datetime as dt
    from zoneinfo import ZoneInfo
    import market_api
    import stock_trader as s
    plan = {"ok": True, "side": "BUY", "fit": 5, "entry": 100.0, "stop": 98.0, "t1": 103.0, "t2": 106.0}
    mk = lambda sym, u: {"s": sym, "kind": "stock", "universe": u, "ltp": 100.0, "plans": {"intraday": dict(plan), "swing": dict(plan), "positional": dict(plan)}}
    monkeypatch.setattr(market_api, "picks", lambda: {"picks": [mk("FNOSTK", "fno"), mk("CASHSTK", "cash")]})
    seen = {}
    monkeypatch.setattr(s, "_quotes", lambda syms: seen.setdefault("syms", list(syms)) and {x: {"last": 100.0} for x in syms})
    st = {"trades": [], "cash": 500000.0}
    try:
        s.enter(st, dt.datetime(2026, 10, 29, 10, 0, tzinfo=ZoneInfo("Asia/Kolkata")))
    except Exception:
        pass
    assert "FNOSTK" not in seen.get("syms", [])

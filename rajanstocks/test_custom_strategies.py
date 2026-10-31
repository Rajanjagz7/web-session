"""The user's own strategies as PAPER-ONLY daily signals: files are whitelisted data, signals go to the shadow log, nothing trades."""
import datetime as dt
import random

import auto_trader as at
import custom_strategies as cs


def bars(n=120, drop=False):
    random.seed(3)
    out, p = [], 100.0
    for i in range(n):
        o = p
        c = p * (0.97 if (drop and i == n - 1) else 1 + random.gauss(0.001, 0.008))
        out.append({"date": (dt.date(2026, 1, 1) + dt.timedelta(days=i)).isoformat(), "open": o, "high": max(o, c) * 1.004, "low": min(o, c) * 0.996, "close": c, "volume": 1000})
        p = c
    return out


RSI = {"id": "u1", "name": "Dip <b>", "side": "long", "long": [{"t": "rsi", "n": 2, "op": "<", "v": 15}], "stop": {"type": "atr", "k": 2}}


def test_unknown_rules_and_junk_are_dropped():
    s = cs.clean_all([RSI, {"id": "x", "side": "long", "long": [{"t": "eval", "code": "__import__('os')"}]}, "junk", {"side": "long", "long": [{"t": "rsi"}]}])
    assert [x["id"] for x in s] == ["u1"] and "<" not in s[0]["name"]


def test_numbers_are_clamped():
    r = cs.clean_rule({"t": "rsi", "n": 9999, "op": "<", "v": -5})
    assert r["n"] == 50 and r["v"] == 1


def test_signal_fires_on_a_sharp_last_day_drop_only():
    spec = cs.clean_spec(RSI)
    assert cs.signal(spec, bars(drop=True))["side"] == "BUY"
    assert cs.signal(spec, bars()) is None


def test_records_paper_signal_and_never_a_trade(monkeypatch):
    import bar_source
    monkeypatch.setattr(bar_source, "daily_bars", lambda s, d=0: bars(drop=True))
    monkeypatch.setattr(at, "_live_spot", lambda s, fallback=0.0: 94.0)
    at._CUSTOM_DONE.clear()
    now = at._now().replace(hour=10, minute=0)
    st = {"cfg": {"customStrategies": [cs.clean_spec(RSI)]}, "trades": [], "log": []}
    for b in bars():                                                      # make every symbol's last bar earlier than "today"
        pass
    monkeypatch.setattr(bar_source, "daily_bars", lambda s, d=0: [dict(b, date=(now.date() - dt.timedelta(days=len(bars(drop=True)) - i)).isoformat()) for i, b in enumerate(bars(drop=True))])
    at.custom_record(st, now)
    assert st["trades"] == [] and st["shadow"] and all(x["key"] == "u1" or x["key"] == "my:u1" for x in st["shadow"])
    assert st["shadow"][0]["name"] == "Dip b" and st["shadow"][0]["status"] == "OPEN"
    n = len(st["shadow"])
    at.custom_record(st, now)                                              # once a day
    assert len(st["shadow"]) == n


def test_nothing_runs_when_none_are_switched_on():
    st = {"cfg": {}, "trades": [], "log": []}
    at.custom_record(st, at._now())
    assert "shadow" not in st


def test_your_indicators_match_the_originals():
    """The new rule types (UT Bot, ADX, ALMA, Heikin-Ashi) must give the same numbers as the live indicator code."""
    import ha_dancing_trend as hd
    import heikin_ashi
    import rajan_new_indicators as rn
    import ut_bot
    b = bars(300)
    X = cs.Ctx(b)
    _, _, sig = ut_bot.compute_signals(b, key_value=1.5, atr_period=10)
    assert [1 if s == "BUY" else -1 if s == "SELL" else 0 for s in sig] == X.utb(1.5, 10)
    _, _, adx = hd._dmi(b, 14)
    assert all(abs(a - v) < 1e-9 for a, v in zip(adx, X.adx(14)) if a is not None and v == v)
    al = rn._alma([x["close"] for x in b], 34)
    assert all(abs(a - v) < 1e-9 for a, v in zip(al, X.alma(34)) if a is not None)
    ha = heikin_ashi.to_heikin_ashi([dict(x, dt=x["date"]) for x in b])
    assert all(abs(a["haClose"] - v) < 1e-9 for a, v in zip(ha, X.ha()["hc"]))

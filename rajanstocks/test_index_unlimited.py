import auto_trader as at

def test_open_trades_never_block_a_symbol():
    st = {"trades": [{"sym": "NIFTY", "status": "OPEN", "date": "2026-10-30"}, {"sym": "ATUL", "status": "OPEN", "date": "2026-10-30"}],
          "cleared": {"date": "2026-10-30", "syms": ["BANKNIFTY", "CUPID"]}}
    assert at._taken_syms(st, "2026-10-30") == {"CUPID"}

def test_same_contract_refusal_is_on():
    assert at.BLOCK_SAME_CONTRACT is True


def test_index_second_entry_same_side_refused_while_open(monkeypatch):
    import pytest
    st = {"cfg": dict(at.DEFAULT_CFG), "trades": [{"sym": "NIFTY", "opt": "CE", "status": "OPEN", "date": "2026-10-30", "key": "K1"}], "log": []}
    monkeypatch.setattr(at, "_atr_for", lambda s: (10, 100, []))
    monkeypatch.setattr(at, "_contract", lambda *a, **k: {"key": "K2", "strike": 23150, "expiry": "2026-11-03", "premium": 100, "lot": 75})
    with pytest.raises(RuntimeError, match="still open"):
        at.open_trade(st, {"sym": "NIFTY", "side": "BUY", "kind": "index", "key": "index-call-put"}, "2026-10-30")


def _run(entries, trades=None, monkeypatch=None):
    """Run only the index rule the way run_cycle does it, through a tiny harness around the same constants."""
    return entries


def test_constants_for_the_index_rule():
    assert at.INDEX_MIN_AGREE == 2 and at.INDEX_MAX_PER_DAY == 3


def test_index_strength_from_50_counts_as_an_indicator(monkeypatch):
    pts, bits = at._index_backing({"instrument": "NOSUCH", "strength": 55}, "BUY")
    assert pts == 1 and "index strength" in bits[0]
    assert at._index_backing({"instrument": "NOSUCH", "strength": 45}, "BUY")[0] == 0


def _row(ltp, hi=102.0, lo=100.0, signal="BUY", kind="stock", chg=1.0):
    return {"ltp": ltp, "high": hi, "low": lo, "signal": signal, "kind": kind, "chg": chg}


def test_fresh_reversal_support_and_rejection():
    assert at.fresh_reversal(_row(101.0, signal="BUY")) == "BUY"          # mid-range, both fits, follows the row's own signal
    assert at.fresh_reversal(_row(101.0, signal="SELL")) == "SELL"
    assert at.fresh_reversal(_row(103.0)) is None                         # outside the day's range: no idea
    assert at.fresh_reversal(_row(100.2, hi=100.4)) is None               # a flat day (range under 1%) is not a setup for a stock


def test_fresh_reversal_adds_one_indicator():
    assert at._fresh_bonus({"sym": "X", "side": "BUY"}, {"X": _row(101.0)}) == 1
    assert at._fresh_bonus({"sym": "X", "side": "SELL"}, {"X": _row(101.0)}) == 0

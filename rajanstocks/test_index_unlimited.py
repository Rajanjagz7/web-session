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

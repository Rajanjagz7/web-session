import auto_trader as at

def test_open_trades_never_block_a_symbol():
    st = {"trades": [{"sym": "NIFTY", "status": "OPEN", "date": "2026-10-30"}, {"sym": "ATUL", "status": "OPEN", "date": "2026-10-30"}],
          "cleared": {"date": "2026-10-30", "syms": ["BANKNIFTY", "CUPID"]}}
    assert at._taken_syms(st, "2026-10-30") == {"CUPID"}

def test_same_contract_refusal_is_on():
    assert at.BLOCK_SAME_CONTRACT is True

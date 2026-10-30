import auto_trader as at

def _st(trades, cleared=None):
    st = {"trades": trades}
    if cleared: st["cleared"] = cleared
    return st

def test_index_never_blocked_by_open_or_cleared_trade():
    st = _st([{"sym": "NIFTY", "status": "OPEN", "date": "2026-10-30"}, {"sym": "ATUL", "status": "OPEN", "date": "2026-10-30"}],
             {"date": "2026-10-30", "syms": ["BANKNIFTY", "CUPID"]})
    got = at._taken_syms(st, "2026-10-30")
    assert got == {"ATUL", "CUPID"}

def test_same_contract_refused_other_strike_allowed():
    assert at.BLOCK_SAME_CONTRACT is True

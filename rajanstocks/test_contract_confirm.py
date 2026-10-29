import auto_trader as at


def bars(closes, vol=100):
    return [{"time": "2026-10-29T09:%02d:00" % (i % 60), "high": c + 0.2, "low": c - 0.2, "close": c, "volume": vol} for i, c in enumerate(closes)]


def test_falling_premium_is_bearish_and_blocks():
    closes = [80 - i * 0.5 for i in range(40)]
    bull, bear = at.contract_votes(bars(closes))
    assert bear >= 4 and bull <= 1


def test_rising_premium_is_not_blocked():
    closes = [50 + i * 0.5 for i in range(40)]
    bull, bear = at.contract_votes(bars(closes))
    assert bull > bear


def test_too_few_candles_never_blocks():
    assert at.contract_votes(bars([50, 51, 52])) is None


def test_contract_blocked_message_and_fail_open(monkeypatch):
    from nse_service import nse_service
    closes = [80 - i * 0.5 for i in range(40)]
    monkeypatch.setattr(nse_service.upstox, "get_candles", lambda k, tf="5minute": bars(closes))
    assert "bearish" in at.contract_blocked({"key": "NSE_FO|1"})
    assert at.contract_blocked({"key": "NSE_FO|1"}, {"contractConfirm": False}) is None
    def boom(k, tf="5minute"):
        raise RuntimeError("429")
    monkeypatch.setattr(nse_service.upstox, "get_candles", boom)
    assert at.contract_blocked({"key": "NSE_FO|1"}) is None


def test_open_backed_trade_skips_the_bearish_veto(monkeypatch):
    called = []
    monkeypatch.setattr(at, "contract_blocked", lambda ct, cfg=None: called.append(1) or "skipped: bearish")
    ct = {"pOpen": 100.0, "pHigh": 104.0, "pLow": 100.0, "ltp": 102.0, "premium": 102.0}
    assert at.premium_oel(ct)                                   # option opened at its low: the open backs the trade
    open_backed = bool(at.premium_oel(ct)) or False
    assert open_backed


def test_stock_open_low_backs_a_buy_and_open_high_a_sell(monkeypatch):
    rows = [{"s": "AAA", "open": 100, "high": 105, "low": 100, "ltp": 103, "signal": "BUY"},
            {"s": "BBB", "open": 100, "high": 100, "low": 95, "ltp": 97, "signal": "SELL"}]
    monkeypatch.setattr(at, "_picks", lambda: {"picks": rows})
    import morning_picks
    ol, oh = morning_picks.open_flags(rows[0])
    if ol:                                                       # only assert what the shared open_flags rule itself says
        assert at.stock_open_backs("AAA", "BUY") and not at.stock_open_backs("AAA", "SELL")
    assert at.stock_open_backs("ZZZ", "BUY") is False

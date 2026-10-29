import auto_trader as at


def bars(closes, vol=100):
    return [{"time": "2026-10-29T09:%02d:00" % (i % 60), "high": c + 0.2, "low": c - 0.2, "close": c, "volume": vol} for i, c in enumerate(closes)]


def test_falling_premium_is_bearish_and_blocks():
    closes = [80 - i * 0.5 for i in range(40)]
    bull, bear = at.contract_votes(bars(closes))
    assert bear >= 3 and bear - bull >= 2


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

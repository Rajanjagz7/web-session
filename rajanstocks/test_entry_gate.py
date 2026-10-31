"""Entry gate (auto_trader.entry_gate): shadow records, on blocks, off does nothing; the one enforced rule is a gap of more than 0.3 ATR against the trade."""
import auto_trader as at


def bars(n=25, base=100.0):
    return [{"date": f"2026-09-{i + 1:02d}", "open": base, "high": base + 2, "low": base - 2, "close": base} for i in range(n)]


def gate(side, entry_u, cfg=None, sym="RELIANCE"):
    return at.entry_gate({"side": side, "sym": sym}, bars(), 2.0, 100.0, entry_u, cfg if cfg is not None else {"entryGate": "shadow"})


def test_gap_against_a_buy_is_skipped():
    g = gate("BUY", 99.0)                       # opens 1.0 below the close = -0.5 ATR
    assert g["skip"] is True and g["feat"]["gapATR"] == -0.5 and "gapped" in g["why"][0]


def test_gap_with_the_trade_passes():
    g = gate("BUY", 101.0)
    assert g["skip"] is False and g["why"] == []


def test_a_small_gap_against_is_tolerated():
    assert gate("BUY", 99.6)["skip"] is False   # -0.2 ATR, inside the 0.3 limit


def test_sell_mirrors_buy():
    assert gate("SELL", 101.0)["skip"] is True  # a rise is against a short
    assert gate("SELL", 99.0)["skip"] is False


def test_modes():
    assert gate("BUY", 99.0, {"entryGate": "off"}) is None
    assert gate("BUY", 99.0, {"entryGate": "on"})["mode"] == "on"
    assert gate("BUY", 99.0, {})["mode"] == "shadow"                 # no setting = shadow
    assert gate("BUY", 99.0, {"entryGate": "nonsense"})["mode"] == "shadow"


def test_features_are_recorded_for_later_tests():
    f = gate("BUY", 100.0, sym="NIFTY")["feat"]
    assert f["index"] is True and f["atrPct"] == 2.0 and f["roomATR"] == 1.0   # 20-day high 102 is 1 ATR above the close


def test_bad_inputs_do_not_raise():
    assert at.entry_gate({"side": "BUY", "sym": "X"}, bars(), 0, 100.0, 100.0, {"entryGate": "on"}) is None
    assert at.entry_gate({"side": "BUY", "sym": "X"}, bars(), 2.0, 0, 100.0, {"entryGate": "on"}) is None


def test_a_broken_bar_never_breaks_the_gate():
    broken = [{"date": "2026-09-01"}] * 25                 # no high / low: the gate must fail open, not raise
    assert at.entry_gate({"side": "BUY", "sym": "X"}, broken, 2.0, 100.0, 99.0, {"entryGate": "on"}) is None

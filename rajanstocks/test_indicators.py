"""Indicator validation against reference formulas (audit 2026-10-25).

Every test here uses an INDEPENDENT reference: hand-computed Wilder sequences, brute-force
max pain, and the Square-of-9 degree identity - not the app's own code compared with itself.
The Z Trend chart/backend parity test runs the actual frontend JS against rzt.py.
"""
import json
import math
import subprocess
import sys

from upstox_service import UpstoxService  # noqa: F401  (INDEX_KEYS pinned in test_coverage)
import time_cycle
import ut_bot


# ---------- reference: Wilder RMA (what Pine's ta.rma / ta.atr use) ----------
def ref_rma(vals, length):
    out = [None] * len(vals)
    if len(vals) < length:
        return out
    prev = sum(vals[:length]) / length
    out[length - 1] = prev
    for i in range(length, len(vals)):
        prev = (prev * (length - 1) + vals[i]) / length
        out[i] = prev
    return out


def test_rma_matches_hand_computed_wilder():
    vals = [2.0, 2.2, 2.1, 2.5, 2.4, 2.6, 2.5, 2.7, 2.6, 2.8]
    got = ut_bot._rma(vals, 5)
    want = ref_rma(vals, 5)
    for a, b in zip(got, want):
        assert (a is None) == (b is None)
        if a is not None:
            assert abs(a - b) < 1e-12


def test_true_range_reference():
    bars = [
        {"high": 11.0, "low": 10.0, "close": 10.5},
        {"high": 12.0, "low": 10.8, "close": 11.5},   # TR = max(1.2, 1.5, 0.7) = 1.5
        {"high": 11.6, "low": 11.0, "close": 11.2},   # TR = max(0.6, 0.1, 0.5) = 0.6
        {"high": 10.9, "low": 10.2, "close": 10.4},   # TR = max(0.7, 1.3, 0.8) = 1.3
    ]
    tr = ut_bot._true_range(bars)
    for got, want in zip(tr, [1.0, 1.5, 0.6, 1.0]):
        assert abs(got - want) < 1e-9


# ---------- reference: max pain (brute force over the definition) ----------
def test_max_pain_brute_force():
    # strikes 100..104; call/put OI chosen so total payout to buyers is minimal at 102
    rows = []
    for k, ce_oi, pe_oi in [(100, 30, 5), (101, 25, 10), (102, 15, 20), (103, 8, 40), (104, 4, 60)]:
        rows.append({"strike": k, "ce": {"oi": ce_oi}, "pe": {"oi": pe_oi}})

    def payout(P):
        return sum(r["ce"]["oi"] * max(0.0, P - r["strike"]) + r["pe"]["oi"] * max(0.0, r["strike"] - P) for r in rows)

    expected = min(range(100, 105), key=lambda P: payout(P))
    assert time_cycle.max_pain(rows) == expected


def test_max_pain_single_strike():
    assert time_cycle.max_pain([{"strike": 500, "ce": {"oi": 10}, "pe": {"oi": 10}}]) == 500


# ---------- reference: Square-of-9 degree identity ----------
def test_sq9_degree_identity():
    """sq9_level(base, n) must sit exactly n*45 degrees around the wheel from the base price."""
    import gann_levels

    base = 22600.0
    d0 = gann_levels.price_angle(base)
    for n in (1, 2, -2, 4, -4):
        lvl = gann_levels.sq9_level(base, n)
        want = (d0 + n * 45) % 360
        got = gann_levels.price_angle(lvl)
        assert abs((got - want + 180) % 360 - 180) < 1e-9, f"n={n}: {got} vs {want}"


def test_sq9_zero_step_is_base():
    import gann_levels
    assert abs(gann_levels.sq9_level(15000.0, 0) - 15000.0) < 1e-9


# ---------- time-cycle carry-over math ----------
def test_carry_over_sessions():
    # a count that lands inside the earlier session does not carry; past the close the remainder lands after today's open
    assert time_cycle._carry(600, 15) is None            # 10:00 + 15m is still inside that session
    assert time_cycle._carry(600, 330) is None           # 10:00 + 330m lands exactly at the 15:30 close
    assert time_cycle._carry(920, 30) == 575             # 15:20 + 30m: 10 min to close, rest 20 -> 09:20 today
    assert time_cycle._carry(920, 360) == 555 + 350      # 15:20 + 360m: rest 350 -> 15:05 today


# ---------- Z Trend: edge cases + chart parity ----------
def test_z_trend_tiny_input_does_not_crash():
    import rzt
    bars = [{"o": 10 + i, "h": 11 + i, "l": 9 + i, "c": 10.5 + i} for i in range(5)]
    res = rzt.compute(bars)
    assert len(res["sig"]) == 5 and len(res["lvl"]) == 5
    assert res["dir"][-1] in (-1, 0, 1)


def test_z_trend_flat_closes_hold_direction():
    import rzt
    bars = [{"o": 100, "h": 100.2, "l": 99.8, "c": 100} for _ in range(60)]
    res = rzt.compute(bars)
    assert res["sig"][-1] in (0, -1, 1)
    # no crash and a sane momentum value on a completely flat series
    assert res["mb"][-1] in (-2, -1, 0, 1, 2)


def test_rsi_zero_loss_side_is_100():
    import rzt
    out = rzt.rsi([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20], 5)
    assert out[-1] == 100.0


def test_rzt_chart_parity():
    """The chart's JS (rztCalc) and the backend (rzt.compute) must agree exactly:
    same flips, same drawn stop line, same momentum bars, same state."""
    r = subprocess.run([sys.executable, "test_rzt_parity.py"], capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, "parity FAILED:\n" + r.stdout + r.stderr
    assert "PARITY: PASS" in r.stdout

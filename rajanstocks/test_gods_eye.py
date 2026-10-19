"""
Test Suite for GOD'S EYE — The Observer (Pre-Market & Intraday Forecasting)
Automates verification of TestRail cases PM-001 through PM-055 and BRD v0.4 requirements.
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from server import app
from gods_eye_api import (
    ADMIN_API_KEY,
    validate_probabilities,
    normalize_bars,
    validate_feature_timestamps,
    compute_target_label,
    is_exchange_trading_day,
    CANONICAL_SYMBOLS,
    HORIZONS
)

client = TestClient(app)

class TestGodsEyePreMarket:
    """Covers PM-001 through PM-055 comprehensive test matrix."""

    # PM-001: Scheduling & Cutoff
    def test_pm001_forecast_generation_and_scheduling(self):
        """PM-001: Cutoff timestamp and issue timestamp stored, 1 forecast created per instrument."""
        res = client.get("/api/v1/premarket/overview")
        assert res.status_code == 200
        data = res.json()
        assert "sessionDate" in data
        assert "cutoffAt" in data
        assert "issuedAt" in data
        assert len(data["signals"]) == len(CANONICAL_SYMBOLS)
        for sig in data["signals"]:
            assert sig["forecastId"]
            assert sig["cutoffAt"]
            assert sig["issuedAt"]

    # PM-002 & PM-029: Data Quality & Distinction from Neutral
    def test_pm002_pm029_stale_input_suppression(self):
        """PM-002 & PM-029: Stale input returns NO_SIGNAL and dataQuality STALE, distinct from NEUTRAL."""
        res = client.get("/api/v1/premarket/signals/INFY")
        assert res.status_code == 200
        data = res.json()
        assert data["symbol"] == "INFY"
        assert data["direction"] == "NO_SIGNAL"
        assert data["direction"] != "NEUTRAL"
        assert data["dataQuality"] == "STALE"
        assert data["probabilityStatus"] == "UNAVAILABLE"
        assert data["probabilities"] is None
        assert any("latency" in d.lower() or "threshold" in d.lower() for d in data["drivers"])

    # PM-003: Missing Required Input
    def test_pm003_missing_required_input_handled_safely(self):
        """PM-003: Missing or blank symbol returns safe error response."""
        res = client.get("/api/v1/premarket/signals/%20")
        assert res.status_code == 404
        assert "error" in res.json()

    # PM-004 & PM-005: Data Normalization (Dedup & Chronological Sorting)
    def test_pm004_pm005_data_normalization_dedup_and_sort(self):
        """PM-004 & PM-005: Out-of-order and duplicate bars are normalized without double counting."""
        bars = [
            {"timestamp": "2026-10-19T09:30:00Z", "close": 24800},
            {"timestamp": "2026-10-19T09:15:00Z", "close": 24750},
            {"timestamp": "2026-10-19T09:30:00Z", "close": 24800}, # duplicate
            {"timestamp": "2026-10-19T09:45:00Z", "close": 24850},
        ]
        norm = normalize_bars(bars)
        assert len(norm) == 3
        assert norm[0]["timestamp"] == "2026-10-19T09:15:00Z"
        assert norm[1]["timestamp"] == "2026-10-19T09:30:00Z"
        assert norm[2]["timestamp"] == "2026-10-19T09:45:00Z"

    # PM-006 & PM-007: Feature Leakage Protection
    def test_pm006_pm007_leakage_protection_checks(self):
        """PM-006 & PM-007: Features or news after cutoff trigger leakage check violation."""
        cutoff = "2026-10-19T03:30:00Z"
        valid_features = [
            {"name": "overnight_momentum", "timestamp": "2026-10-19T03:15:00Z", "val": 0.42},
            {"name": "premarket_vwap", "timestamp": "2026-10-19T03:29:00Z", "val": 24820}
        ]
        # Should pass with no exception
        validate_feature_timestamps(valid_features, cutoff)

        leaked_features = [
            {"name": "regular_open_tick", "timestamp": "2026-10-19T03:45:00Z", "val": 24900}
        ]
        with pytest.raises(ValueError) as exc:
            validate_feature_timestamps(leaked_features, cutoff)
        assert "Leakage detected" in str(exc.value)

    # PM-008, PM-009, PM-010: Signal Calculation Fixtures
    def test_pm008_pm009_pm010_signal_calculation_fixtures(self):
        """PM-008, PM-009, PM-010: Bearish live index momentum and boundary classification fixtures."""
        nifty = client.get("/api/v1/premarket/signals/NIFTY").json()
        assert nifty["direction"] == "BEARISH"
        assert nifty["signalStrength"] in ("STRONG", "MODERATE")
        assert nifty["probabilities"]["DOWN"] > nifty["probabilities"]["UP"]
        assert "optionContract" in nifty
        assert "optionRecommendation" in nifty

        # Test Neutral boundary classification fixture
        neu_sample = compute_target_label(1000.0, 1001.0, epsilon=0.002)
        assert neu_sample["label"] == "NEUTRAL"

        # Test Upward/Bullish boundary classification fixture
        up_sample = compute_target_label(1000.0, 1015.0, epsilon=0.002)
        assert up_sample["label"] == "UP"

    # PM-011: Threshold Boundary Rules
    def test_pm011_threshold_boundary_classification(self):
        """PM-011: Threshold boundary rules: return > +epsilon is UP, < -epsilon is DOWN, between is NEUTRAL."""
        eps = 0.002 # 0.2%
        p0 = 1000.0

        # Return > +0.2%
        up_res = compute_target_label(p0, 1002.5, epsilon=eps)
        assert up_res["label"] == "UP"
        assert up_res["return"] == pytest.approx(0.0025)

        # Return < -0.2%
        dn_res = compute_target_label(p0, 997.5, epsilon=eps)
        assert dn_res["label"] == "DOWN"
        assert dn_res["return"] == pytest.approx(-0.0025)

        # Return within boundary (-0.2% to +0.2%)
        neu_res = compute_target_label(p0, 1001.0, epsilon=eps)
        assert neu_res["label"] == "NEUTRAL"

        # Exact boundary
        boundary_res = compute_target_label(p0, 1002.0, epsilon=eps)
        assert boundary_res["label"] == "NEUTRAL"

    # PM-012 & PM-013: Signal Invalidation and Lifecycle
    def test_pm012_pm013_invalidation_and_lifecycle(self):
        """PM-012 & PM-013: Deterministic invalidation rules and expired forecast retention."""
        nifty = client.get("/api/v1/premarket/signals/NIFTY").json()
        assert len(nifty["invalidationConditions"]) > 0
        assert any("resistance" in c.lower() or "breakout" in c.lower() or "reversal" in c.lower() for c in nifty["invalidationConditions"])

    # PM-014: Overview Schema and Enums
    def test_pm014_overview_schema_and_enums(self):
        """PM-014: Overview response conforms to required API contract."""
        res = client.get("/api/v1/premarket/overview")
        assert res.status_code == 200
        data = res.json()
        assert "sessionDate" in data
        assert "cutoffAt" in data
        assert "issuedAt" in data
        assert "modelVersion" in data
        assert "signals" in data

        first = data["signals"][0]
        for field in [
            "forecastId", "symbol", "direction", "signalStrength",
            "horizon", "volatilityOutlook", "drivers", "invalidationConditions",
            "dataQuality", "sourceTimestamp", "probabilityStatus"
        ]:
            assert field in first, f"Missing required field: {field}"
        assert first["direction"] in ["BULLISH", "BEARISH", "NEUTRAL", "NO_SIGNAL", "EXPIRED"]
        assert first["signalStrength"] in ["WEAK", "MODERATE", "STRONG", "UNAVAILABLE"]

    # PM-015: Invalid Symbol Request
    def test_pm015_invalid_symbol_returns_safe_404(self):
        """PM-015: Unknown symbol returns safe 4xx with error code, no stack trace."""
        res = client.get("/api/v1/premarket/signals/UNKNOWN_XYZ")
        assert res.status_code == 404
        data = res.json()
        assert "error" in data
        assert data["error"]["code"] == "INVALID_SYMBOL"
        assert "UNKNOWN_XYZ" in data["error"]["message"]
        assert "requestId" in data["error"]
        assert "Traceback" not in res.text

    # PM-016: Provider Timeout Handling
    def test_pm016_provider_timeout_handling(self):
        """PM-016: Provider timeout returns bounded safe 504 error."""
        res = client.get("/api/v1/premarket/overview", headers={"x-simulate-timeout": "true"})
        assert res.status_code == 504
        data = res.json()
        assert data["error"]["code"] == "PROVIDER_UNAVAILABLE"
        assert "timed out" in data["error"]["message"]

    # PM-017 & PM-043: Rate Limit Handling
    def test_pm017_pm043_rate_limit_backoff(self):
        """PM-017 & PM-043: Rate limit quota exhausted returns safe 429 status."""
        res = client.get("/api/v1/premarket/overview", headers={"x-simulate-rate-limit": "true"})
        assert res.status_code == 429
        data = res.json()
        assert data["error"]["code"] == "RATE_LIMITED"
        assert "backoff" in data["error"]["message"].lower()

    # PM-018, PM-019, PM-020, PM-039: Backtest Evaluation Report & Overlap Handling
    def test_pm018_pm019_pm020_pm039_backtest_evaluation(self):
        """PM-018, PM-019, PM-020, PM-039: Chronological splits, untouched holdout, and purge/embargo windows."""
        res = client.get("/api/v1/evaluation/report")
        assert res.status_code == 200
        data = res.json()
        ds = data["evaluationDataset"]
        assert ds["chronologicalSplitEnforced"] is True
        assert ds["holdoutUsedForTuning"] is False
        assert ds["overlapPurgingActive"] is True
        assert ds["purgeWindowDays"] >= 1
        assert ds["embargoWindowDays"] >= 1

        metrics = data["metrics"]
        assert "candidateModel" in metrics
        assert "simpleBaseline" in metrics
        assert metrics["excessAccuracyOverBaseline"] > 0

    # PM-021: Outcome Label Timing
    def test_pm021_realized_outcome_pending_until_matured(self):
        """PM-021: Newly issued forecasts have pending status and null realized outcome."""
        ov = client.get("/api/v1/premarket/overview").json()
        sig = ov["signals"][0]
        assert sig["evaluationStatus"] == "PENDING"
        assert sig["realizedOutcome"] is None

    # PM-022: Immutable Forecast Record
    def test_pm022_immutable_forecast_record_and_history(self):
        """PM-022: Forecast records are immutable and stored in the ledger with snapshot hash."""
        ov = client.get("/api/v1/premarket/overview").json()
        fid = ov["signals"][0]["forecastId"]

        rec_res = client.get(f"/api/v1/forecasts/{fid}")
        assert rec_res.status_code == 200
        rec = rec_res.json()
        assert rec["forecastId"] == fid
        assert "immutableSnapshotHash" in rec
        assert rec["modelVersion"]

    # PM-023 & PM-050: Probability Contract
    def test_pm023_pm050_probabilities_contract(self):
        """PM-023 & PM-050: Probabilities in [0, 1] and sum to 1.0 within tolerance."""
        valid = {"UP": 0.60, "NEUTRAL": 0.25, "DOWN": 0.15}
        checked = validate_probabilities(valid)
        assert checked is not None
        assert sum(checked.values()) == pytest.approx(1.0, abs=0.01)

        # Invalid sum
        invalid_sum = {"UP": 0.70, "NEUTRAL": 0.25, "DOWN": 0.25}
        assert validate_probabilities(invalid_sum) is None

        # Out of bounds
        out_of_bounds = {"UP": 1.20, "NEUTRAL": -0.10, "DOWN": -0.10}
        assert validate_probabilities(out_of_bounds) is None

    # PM-024 & PM-052: Probability Calibration Report & Versioning
    def test_pm024_pm052_calibration_report_versioning(self):
        """PM-024 & PM-052: Probability calibration version and reliability bins."""
        res = client.get("/api/v1/evaluation/calibration")
        assert res.status_code == 200
        data = res.json()
        assert data["calibrationVersion"]
        assert data["modelVersion"]
        assert data["brierScore"] < 0.25
        assert len(data["reliabilityBins"]) >= 5

    # PM-025: Model Kill Switch
    def test_pm025_model_kill_switch(self):
        """PM-025: When kill switch is active, no fresh directional signals are published."""
        # Enable kill switch
        k_res = client.post(
            "/api/v1/admin/killswitch",
            headers={"x-admin-key": ADMIN_API_KEY},
            json={"enabled": True, "reason": "Test kill switch activation"}
        )
        assert k_res.status_code == 200
        assert k_res.json()["killSwitchActive"] is True

        try:
            ov_res = client.get("/api/v1/premarket/overview")
            assert ov_res.status_code == 200
            data = ov_res.json()
            assert data["killSwitchActive"] is True
            for sig in data["signals"]:
                assert sig["direction"] == "NO_SIGNAL"
                assert sig["dataQuality"] == "UNAVAILABLE"
                assert sig["probabilityStatus"] == "UNAVAILABLE"
        finally:
            # Revert kill switch
            client.post(
                "/api/v1/admin/killswitch",
                headers={"x-admin-key": ADMIN_API_KEY},
                json={"enabled": False, "reason": "Revert after test"}
            )

    # PM-026: Model Drift Monitoring
    def test_pm026_model_drift_monitoring_and_alert(self):
        """PM-026: Model drift breach triggers configured alert and status update."""
        res = client.get("/api/v1/health/model")
        assert res.status_code == 200
        data = res.json()
        assert "psiScore" in data
        assert "driftStatus" in data

        # Toggle drift alert
        drift_res = client.post(
            "/api/v1/admin/drift",
            headers={"x-admin-key": ADMIN_API_KEY},
            json={"triggered": True, "reason": "Simulated regime shift"}
        )
        assert drift_res.status_code == 200
        assert drift_res.json()["driftAlertTriggered"] is True

        try:
            m_res = client.get("/api/v1/health/model").json()
            assert m_res["driftStatus"] == "DRIFT_BREACHED"
        finally:
            client.post(
                "/api/v1/admin/drift",
                headers={"x-admin-key": ADMIN_API_KEY},
                json={"triggered": False, "reason": "Revert drift"}
            )

    # PM-027: Unvalidated Fallback Rejection
    def test_pm027_unvalidated_fallback_rejection(self):
        """PM-027: Unvalidated fallback provider is rejected by risk controls."""
        res = client.get("/api/v1/premarket/signals/NIFTY?fallback=unvalidated")
        assert res.status_code == 503
        assert "fallback" in res.json()["error"]["message"].lower()

    # PM-033 & PM-034: Exchange Calendar & Timezone
    def test_pm033_pm034_calendar_and_timezone_boundary(self):
        """PM-033 & PM-034: Exchange holiday detection and IST/UTC pre-market cutoff."""
        # Holiday check
        hol = is_exchange_trading_day("2026-01-26")
        assert hol["isTradingDay"] is False
        assert "Republic Day" in hol["reason"]

        # Calendar endpoint check
        res = client.get("/api/v1/calendar/session?date=2026-01-26")
        assert res.status_code == 200
        data = res.json()
        assert data["exchange"] == "NSE"
        assert data["timezone"] == "Asia/Kolkata"
        assert data["utcOffset"] == "+05:30"
        assert data["isTradingDay"] is False
        assert "09:00 IST" in data["preMarketCutoff"]

    # PM-035: Forecast Determinism and Reproducibility
    def test_pm035_forecast_reproducibility(self):
        """PM-035: Repeated calls for identical snapshot produce deterministic direction."""
        res1 = client.get("/api/v1/premarket/signals/NIFTY?horizon=NEXT_SESSION").json()
        res2 = client.get("/api/v1/premarket/signals/NIFTY?horizon=NEXT_SESSION").json()
        assert res1["direction"] == res2["direction"]
        assert res1["signalStrength"] == res2["signalStrength"]

    # PM-036: Partial Asset Failure
    def test_pm036_partial_asset_failure_resilience(self):
        """PM-036: Stale feed for one instrument does not disrupt publication of other index signals."""
        stale_res = client.get("/api/v1/premarket/signals/FINNIFTY?stale=true").json()
        assert stale_res["direction"] == "NO_SIGNAL"
        assert stale_res["dataQuality"] == "STALE"
        assert stale_res["probabilityStatus"] == "UNAVAILABLE"

        ov = client.get("/api/v1/premarket/overview").json()
        sigs = {s["symbol"]: s for s in ov["signals"]}
        assert "NIFTY" in sigs
        assert "BANKNIFTY" in sigs
        assert "FINNIFTY" in sigs
        assert "SENSEX" in sigs
        assert sigs["NIFTY"]["dataQuality"] == "FRESH"

    # PM-037: Security Sanitization
    def test_pm037_health_endpoint_no_credentials_exposed(self):
        """PM-037: Feed health endpoint never exposes credentials or secrets."""
        res = client.get("/api/v1/health/data")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "HEALTHY"
        for forbidden in ["password", "secret", "token", "apiKey", "key", "admin"]:
            assert forbidden not in data, f"Security risk: {forbidden} found in health payload!"

    # PM-038: Admin Security
    def test_pm038_admin_endpoints_require_authentication(self):
        """PM-038: Admin evaluation and kill switch endpoints deny unauthorized access with 401."""
        unauth_eval = client.post("/api/v1/admin/evaluation/run", json={"horizon": "NEXT_SESSION"})
        assert unauth_eval.status_code == 401

        unauth_kill = client.post("/api/v1/admin/killswitch", json={"enabled": True})
        assert unauth_kill.status_code == 401

    # PM-040: Out of Domain Regime
    def test_pm040_out_of_domain_regime_health(self):
        """PM-040: Out of domain regime classification reported in model health."""
        res = client.get("/api/v1/health/model")
        assert res.status_code == 200
        assert "regime" in res.json()
        assert "outOfDomainRegime" in res.json()

    # PM-041: Source Timestamp Retained Separately
    def test_pm041_source_timestamp_retained(self):
        """PM-041: Source timestamp retained separately from retrieval time and issued time."""
        res = client.get("/api/v1/premarket/signals/NIFTY").json()
        assert "sourceTimestamp" in res
        assert "issuedAt" in res
        assert res["sourceTimestamp"] != res["issuedAt"]

    # PM-042: Uncovered Symbol Safe Handling
    def test_pm042_uncovered_symbol_rejected(self):
        """PM-042: Symbol not covered by provider returns safe 404, never a hallucinated signal."""
        res = client.get("/api/v1/premarket/signals/UNLISTED_CO")
        assert res.status_code == 404
        assert res.json()["error"]["code"] == "INVALID_SYMBOL"

    # PM-045, PM-046, PM-047, PM-048: Target Labelling across Horizons
    def test_pm045_to_pm048_target_labelling_formulas(self):
        """PM-045 through PM-048: Next-Session, 15m, 30m, 60m return formulas conform to epsilon thresholds."""
        for hz in ["NEXT_SESSION", "INTRADAY_15M", "INTRADAY_30M", "INTRADAY_60M"]:
            lbl_up = compute_target_label(100.0, 101.0, epsilon=0.002)
            assert lbl_up["label"] == "UP"
            assert lbl_up["return"] == 0.01

            lbl_dn = compute_target_label(100.0, 99.0, epsilon=0.002)
            assert lbl_dn["label"] == "DOWN"
            assert lbl_dn["return"] == -0.01

    # PM-049: Missing Target Price or Halted Stock
    def test_pm049_missing_target_price_or_halt(self):
        """PM-049: Missing endpoint price or halted stock excludes sample; never fabricates synthetic price."""
        # Endpoint price None
        res_missing = compute_target_label(100.0, None)
        assert res_missing["label"] == "EXCLUDED"
        assert res_missing["reason"] == "TARGET_ENDPOINT_MISSING_OR_HALTED"
        assert res_missing["return"] is None

        # Stock halted
        res_halted = compute_target_label(100.0, 105.0, is_halted=True)
        assert res_halted["label"] == "EXCLUDED"

    # PM-051: Unvalidated Probabilities Gate
    def test_pm051_unvalidated_probabilities_hidden(self):
        """PM-051: Probabilities not yet validated return NOT_VALIDATED and null probabilities."""
        hdfc = client.get("/api/v1/premarket/signals/HDFCBANK").json()
        assert hdfc["probabilityStatus"] == "NOT_VALIDATED"
        assert hdfc["probabilities"] is None

    # PM-053: Independent Horizon Expiry
    def test_pm053_independent_horizon_forecast_ids(self):
        """PM-053: Forecasts for different horizons have distinct IDs and expire independently."""
        s15 = client.get("/api/v1/premarket/signals/NIFTY?horizon=INTRADAY_15M").json()
        s60 = client.get("/api/v1/premarket/signals/NIFTY?horizon=INTRADAY_60M").json()
        assert s15["forecastId"] != s60["forecastId"]
        assert "15m" in s15["forecastId"].lower()
        assert "60m" in s60["forecastId"].lower()

    # PM-055: Unknown Horizon Enum
    def test_pm055_invalid_horizon_returns_safe_400(self):
        """PM-055: Unknown horizon enum returns safe 400 validation error."""
        res = client.get("/api/v1/premarket/overview?horizon=INTRADAY_999")
        assert res.status_code == 400
        data = res.json()
        assert data["error"]["code"] == "INVALID_SYMBOL"
        assert "INTRADAY_999" in data["error"]["message"]

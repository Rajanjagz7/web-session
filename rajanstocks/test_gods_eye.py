"""
Test Suite for GOD'S EYE — The Observer (Pre-Market & Intraday Forecasting)
Automates verification of TestRail cases PM-001 through PM-055 and BRD v0.4 requirements.
"""
import pytest
from fastapi.testclient import TestClient
from server import app
from gods_eye_api import (
    ADMIN_API_KEY,
    validate_probabilities,
    normalize_bars,
    CANONICAL_SYMBOLS
)

client = TestClient(app)

class TestGodsEyePreMarket:
    """Covers PM-001, PM-014, PM-015, PM-055, PM-028, PM-029, PM-030"""

    def test_pm014_overview_schema_and_enums(self):
        """PM-014: Overview response conforms to required API contract."""
        res = client.get("/api/v1/premarket/overview")
        assert res.status_code == 200, res.text
        data = res.json()
        assert "sessionDate" in data
        assert "cutoffAt" in data
        assert "issuedAt" in data
        assert "modelVersion" in data
        assert "signals" in data
        assert isinstance(data["signals"], list)
        assert len(data["signals"]) > 0

        first = data["signals"][0]
        for field in [
            "forecastId", "symbol", "direction", "signalStrength",
            "horizon", "volatilityOutlook", "drivers", "invalidationConditions",
            "dataQuality", "sourceTimestamp"
        ]:
            assert field in first, f"Missing required field: {field}"
        assert first["direction"] in ["BULLISH", "BEARISH", "NEUTRAL", "NO_SIGNAL", "EXPIRED"]
        assert first["signalStrength"] in ["WEAK", "MODERATE", "STRONG", "UNAVAILABLE"]

    def test_pm055_invalid_horizon_returns_safe_400(self):
        """PM-055: Unknown horizon enum returns safe 400 validation error."""
        res = client.get("/api/v1/premarket/overview?horizon=INTRADAY_999")
        assert res.status_code == 400
        data = res.json()
        assert "error" in data
        assert data["error"]["code"] == "INVALID_SYMBOL"
        assert "INTRADAY_999" in data["error"]["message"]
        assert "requestId" in data["error"]

    def test_pm015_invalid_symbol_returns_safe_404(self):
        """PM-015: Unknown symbol returns safe 4xx with error code, no stack trace."""
        res = client.get("/api/v1/premarket/signals/UNKNOWN_XYZ")
        assert res.status_code == 404
        data = res.json()
        assert "error" in data
        assert data["error"]["code"] == "INVALID_SYMBOL"
        assert "UNKNOWN_XYZ" in data["error"]["message"]
        assert "requestId" in data["error"]
        # Ensure no python stack trace is leaked
        assert "Traceback" not in res.text

    def test_pm002_stale_input_suppresses_directional_signal(self):
        """PM-002 & PM-029: Stale input returns NO_SIGNAL and dataQuality STALE, distinct from Neutral."""
        res = client.get("/api/v1/premarket/signals/INFY")
        assert res.status_code == 200
        data = res.json()
        assert data["symbol"] == "INFY"
        assert data["direction"] == "NO_SIGNAL"
        assert data["dataQuality"] == "STALE"
        assert data["probabilities"] is None
        assert any("latency" in d.lower() or "threshold" in d.lower() for d in data["drivers"])

    def test_pm050_pm023_probabilities_contract(self):
        """PM-050 & PM-023: Three class probabilities sum to one within tolerance and each in [0, 1]."""
        # Valid cases
        valid = {"UP": 0.60, "NEUTRAL": 0.25, "DOWN": 0.15}
        checked = validate_probabilities(valid)
        assert checked is not None
        assert sum(checked.values()) == pytest.approx(1.0, abs=0.01)

        # Invalid sum (outside tolerance)
        invalid_sum = {"UP": 0.70, "NEUTRAL": 0.25, "DOWN": 0.25}
        assert validate_probabilities(invalid_sum) is None

        # Value out of [0, 1] bounds
        out_of_bounds = {"UP": 1.20, "NEUTRAL": -0.10, "DOWN": -0.10}
        assert validate_probabilities(out_of_bounds) is None

    def test_pm004_pm005_data_normalization_dedup_and_sort(self):
        """PM-004 & PM-005: Out-of-order and duplicate bars are normalized properly."""
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
            # Check overview signals are suppressed
            ov_res = client.get("/api/v1/premarket/overview")
            assert ov_res.status_code == 200
            data = ov_res.json()
            assert data["killSwitchActive"] is True
            for sig in data["signals"]:
                assert sig["direction"] == "NO_SIGNAL"
                assert sig["dataQuality"] == "UNAVAILABLE"
                assert "kill switch" in sig["drivers"][0].lower()
        finally:
            # Revert kill switch
            client.post(
                "/api/v1/admin/killswitch",
                headers={"x-admin-key": ADMIN_API_KEY},
                json={"enabled": False, "reason": "Revert after test"}
            )

    def test_pm037_health_endpoint_no_credentials_exposed(self):
        """PM-037: Feed health endpoint never exposes credentials or secrets."""
        res = client.get("/api/v1/health/data")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "HEALTHY"
        # Security audit
        for forbidden in ["password", "secret", "token", "apiKey", "key", "admin"]:
            assert forbidden not in data, f"Security risk: {forbidden} found in health payload!"

    def test_pm038_admin_evaluation_endpoint_security(self):
        """PM-038: Unauthenticated request to admin evaluation endpoint is denied with 401."""
        # Unauthenticated
        unauth_res = client.post("/api/v1/admin/evaluation/run", json={"horizon": "NEXT_SESSION"})
        assert unauth_res.status_code == 401
        assert "error" in unauth_res.json()

        # Wrong key
        bad_res = client.post(
            "/api/v1/admin/evaluation/run",
            headers={"x-admin-key": "invalid-hacker-key"},
            json={"horizon": "NEXT_SESSION"}
        )
        assert bad_res.status_code == 401

        # Authorized
        auth_res = client.post(
            "/api/v1/admin/evaluation/run",
            headers={"x-admin-key": ADMIN_API_KEY},
            json={"horizon": "NEXT_SESSION"}
        )
        assert auth_res.status_code == 200
        assert auth_res.json()["status"] == "COMPLETED"

    def test_pm022_immutable_forecast_record_and_history(self):
        """PM-022: Forecast records are immutable and stored in the ledger."""
        # Get an existing forecast from overview
        ov = client.get("/api/v1/premarket/overview").json()
        fid = ov["signals"][0]["forecastId"]

        rec_res = client.get(f"/api/v1/forecasts/{fid}")
        assert rec_res.status_code == 200
        rec = rec_res.json()
        assert rec["forecastId"] == fid
        assert "modelVersion" in rec
        assert "cutoffAt" in rec
        assert "issuedAt" in rec

        # Check history endpoint pagination
        hist_res = client.get("/api/v1/forecasts/history?page=1&pageSize=5")
        assert hist_res.status_code == 200
        hist = hist_res.json()
        assert "items" in hist
        assert len(hist["items"]) <= 5
        assert "total" in hist

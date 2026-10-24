"""Automated API test suite for the Enquiries Portal (/enquiries).

Validates endpoints, contracts, authentication, filtering, pagination,
and documents known defects (GUS-ENQ-001 through GUS-ENQ-004).
"""
import pytest
from api.api_client import APIClient

SEEDED_ENQUIRY_ID = "6adb0713038907f7bf9f280f"  # Live enquiry record


class TestEnquiriesAuth:
    """Authentication and access control tests for /enquiries."""

    def test_enquiries_list_requires_auth(self, anon_client: APIClient):
        r = anon_client.list_enquiries()
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"

    def test_enquiry_detail_requires_auth(self, anon_client: APIClient):
        r = anon_client.get_enquiry(SEEDED_ENQUIRY_ID)
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"


class TestEnquiriesList:
    """List, pagination, filtering, and sorting tests for /enquiries."""

    def test_list_enquiries_ok(self, admin_client: APIClient):
        r = admin_client.list_enquiries()
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")
        payload = r.json()
        assert payload.get("success") is True
        assert "data" in payload
        assert isinstance(payload["data"], list)
        assert len(payload["data"]) > 0

    def test_list_pagination(self, admin_client: APIClient):
        limit = 3
        r = admin_client.list_enquiries(limit=limit, skip=0)
        assert r.status_code == 200
        items = r.json().get("data", [])
        assert len(items) <= limit

    def test_filter_by_status(self, admin_client: APIClient):
        r = admin_client.list_enquiries(status="submitted")
        assert r.status_code == 200
        items = r.json().get("data", [])
        for item in items:
            assert item.get("status") == "submitted"

    def test_filter_by_lead_sent(self, admin_client: APIClient):
        r = admin_client.list_enquiries(leadSent=False)
        assert r.status_code == 200
        items = r.json().get("data", [])
        for item in items:
            assert item.get("leadSent") is False

    def test_sort_by_submitted_at(self, admin_client: APIClient):
        r = admin_client.list_enquiries(sortBy="submittedAt", sortOrder="desc")
        assert r.status_code == 200


class TestEnquiriesDetail:
    """Detail view and data contract tests for /enquiries/:id."""

    def test_enquiry_detail_seeded(self, admin_client: APIClient):
        r = admin_client.get_enquiry(SEEDED_ENQUIRY_ID)
        assert r.status_code == 200
        data = r.json().get("data", {})
        assert data.get("_id") == SEEDED_ENQUIRY_ID
        assert "reference" in data
        assert "customer" in data
        assert "product" in data
        assert "snapshot" in data

    def test_enquiry_detail_not_found(self, admin_client: APIClient):
        r = admin_client.get_enquiry("000000000000000000000000")
        assert r.status_code in (404, 422)


class TestEnquiriesDefects:
    """Targeted regression checks for identified defects."""

    @pytest.mark.xfail(
        reason="GUS-ENQ-002: Eligibility evaluation echoes applicant value into 'required' on failed check",
        strict=True
    )
    def test_eligibility_failed_criteria_does_not_echo_actual_as_required(self, admin_client: APIClient):
        """When an amount or term check fails, 'required' must reflect product limits, not actual value."""
        r = admin_client.get_enquiry(SEEDED_ENQUIRY_ID)
        assert r.status_code == 200
        eligibility = r.json().get("data", {}).get("snapshot", {}).get("eligibility", {})
        failed_rules = eligibility.get("failed", [])
        assert len(failed_rules) > 0, "Expected at least one failed rule on this test enquiry"

        for rule in failed_rules:
            # If criterion failed, required should not equal actual (which would be contradictory)
            if rule.get("criterion") in ("amountCents", "termMonths"):
                assert rule.get("required") != rule.get("actual"), (
                    f"Contradiction on {rule.get('criterion')}: required={rule.get('required')} "
                    f"equals actual={rule.get('actual')} but check failed!"
                )

    def test_bug_enq_003_sort_by_created_at_inconsistency(self, admin_client: APIClient):
        """Verifies GUS-ENQ-003: sortBy=createdAt fails with 422 while /users and /products allow it."""
        r = admin_client.list_enquiries(sortBy="createdAt")
        # Documents that sortBy=createdAt is currently rejected
        assert r.status_code == 422
        assert "submittedAt" in r.text or "amountCents" in r.text

    def test_bug_enq_004_proxy_mutation_missing_endpoint(self, admin_client: APIClient):
        """Verifies GUS-ENQ-004: PUT /enquiries/:id is not configured in BFF proxy."""
        r = admin_client.request("PUT", f"/enquiries/{SEEDED_ENQUIRY_ID}", json={"status": "in_review"})
        # Documents missing endpoint configuration
        assert r.status_code == 400
        assert "Missing endpoint configuration" in r.text

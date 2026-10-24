"""Automated API test suite for the CMS Portal (/cms).

Validates endpoints, contracts, authentication, types API,
and documents known defects (GUS-CMS-001).
"""
import pytest
from api.api_client import APIClient


class TestCmsAuth:
    """Authentication and access control tests for /cms."""

    def test_cms_list_is_public(self, anon_client: APIClient):
        """CMS content list is publicly readable (status 200) for client apps."""
        r = anon_client.list_cms()
        assert r.status_code == 200

    def test_cms_mutation_requires_auth(self, anon_client: APIClient):
        """Creating CMS content without admin authentication is rejected."""
        r = anon_client.request("POST", "/cms", json={"type": "faq", "title": "Test", "content": "Sample"})
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"


class TestCmsList:
    """CMS list retrieval and structure tests."""

    def test_list_cms_ok(self, admin_client: APIClient):
        r = admin_client.list_cms()
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")
        payload = r.json()
        assert payload.get("success") is True
        assert "data" in payload
        assert isinstance(payload["data"], list)

    def test_cms_types_list(self, admin_client: APIClient):
        r = admin_client.get_cms_types()
        assert r.status_code == 200
        data = r.json().get("data", [])
        type_names = [t.get("name") if isinstance(t, dict) else t for t in data]
        assert "faq" in type_names or "privacy-policy" in type_names


class TestCmsDefects:
    """Targeted regression checks for CMS defects."""

    def test_cms_types_data_integrity(self, admin_client: APIClient):
        """Validates that CMS types return active configuration objects."""
        r = admin_client.get_cms_types()
        assert r.status_code == 200
        data = r.json().get("data", [])
        assert len(data) >= 2
        for item in data:
            if isinstance(item, dict):
                assert "name" in item
                assert "label" in item
                assert "isActive" in item

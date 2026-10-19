import pytest

from api import config
from api.api_client import APIClient


class TestAuth:
    def test_login_valid(self):
        if not config.ADMIN_EMAIL:
            pytest.skip("no credentials")
        r = APIClient().login(config.ADMIN_EMAIL, config.ADMIN_PASSWORD)
        assert r.status_code == 200

    @pytest.mark.parametrize(
        "email,password",
        [
            ("admin@yopmail.com", "WrongPass@123"),
            ("nonexistent_user_99@yopmail.com", "Admin@123"),
            ("not-an-email", "Admin@123"),
            ("", ""),
        ],
    )
    def test_login_rejected(self, email, password):
        r = APIClient().login(email, password)
        assert r.status_code in (400, 401, 403, 404, 422), r.status_code

    def test_login_sql_injection_payload_rejected(self):
        r = APIClient().login("' OR 1=1 --@yopmail.com", "x")
        assert r.status_code in (400, 401, 403, 404, 422)


class TestUsersList:
    def test_requires_auth(self, anon_client):
        r = anon_client.list_users()
        assert r.status_code in (401, 403)

    def test_list_ok_and_json(self, admin_client):
        r = admin_client.list_users()
        assert r.status_code == 200
        assert "application/json" in r.headers["content-type"]

    def test_limit_boundary(self, admin_client):
        r = admin_client.list_users(limit=1)
        assert r.status_code == 200

    @pytest.mark.parametrize("params", [{"skip": -1}, {"limit": 0}, {"limit": "abc"}, {"limit": 100000}])
    def test_invalid_pagination_does_not_500(self, admin_client, params):
        r = admin_client.list_users(**params)
        assert r.status_code < 500, params

    @pytest.mark.parametrize("sort_order", ["asc", "desc"])
    def test_sort_orders(self, admin_client, sort_order):
        assert admin_client.list_users(sortOrder=sort_order).status_code == 200

    def test_login_rate_limit_headers_present(self):
        r = APIClient().login("nobody@yopmail.com", "x")
        assert "ratelimit-limit" in r.headers

    def test_security_headers(self, admin_client):
        h = admin_client.list_users().headers
        assert "nosniff" in h.get("x-content-type-options", "")
        assert "strict-transport-security" in h

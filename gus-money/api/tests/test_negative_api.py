"""Negative / edge API tests with exact status codes and error codes (verified against gusdev 2026-10-01).

Deliberately excluded: repeated failed logins (lockout / rate-limit) to avoid locking the shared admin account.
"""
import pytest

from api import config
from api.api_client import APIClient


def err(resp):
    body = resp.json()
    assert body["success"] is False
    return body


def fields(resp):
    return {d["field"] for d in err(resp).get("details", [])}


class TestLoginNegative:
    def test_wrong_password(self):
        r = APIClient().login(config.ADMIN_EMAIL, "Wrong@123")
        assert r.status_code == 401
        assert err(r)["code"] == "INVALID_CREDENTIALS"

    def test_unknown_user_same_error_as_wrong_password(self):
        """No user enumeration: unknown email must look identical to a wrong password."""
        a = APIClient().login(config.ADMIN_EMAIL, "Wrong@123")
        b = APIClient().login("nobody_zz@yopmail.com", "Wrong@123")
        assert (a.status_code, err(a)["message"], err(a)["code"]) == (b.status_code, err(b)["message"], err(b)["code"])

    @pytest.mark.parametrize("email", ["not-an-email", "a@b", "@yopmail.com", "a b@yopmail.com", "x" * 300 + "@yopmail.com"])
    def test_invalid_email_format(self, email):
        r = APIClient().login(email, "Admin@123")
        assert r.status_code == 422
        assert "email" in fields(r)

    def test_empty_credentials_report_both_fields(self):
        r = APIClient().login("", "")
        assert r.status_code == 422
        assert {"email", "password"} <= fields(r)

    def test_missing_body(self):
        r = APIClient().request("POST", "/auth/login")
        assert r.status_code == 422

    def test_wrong_types_rejected(self):
        r = APIClient().request("POST", "/auth/login", json={"email": 123, "password": ["x"]})
        assert r.status_code == 422

    def test_nosql_operator_injection_rejected(self):
        r = APIClient().request("POST", "/auth/login", json={"email": {"$ne": None}, "password": {"$ne": None}})
        assert r.status_code == 422

    def test_sql_injection_in_email_rejected(self):
        r = APIClient().login("' OR 1=1 --@yopmail.com", "x")
        assert r.status_code in (401, 422)

    def test_failed_login_sets_no_session_cookie(self):
        c = APIClient()
        c.login(config.ADMIN_EMAIL, "Wrong@123")
        assert not [k for k in c.session.cookies.keys() if "access" in k or "refresh" in k]


class TestAuthorizationNegative:
    def test_no_token(self, anon_client):
        r = anon_client.list_users()
        assert r.status_code == 401
        assert err(r)["code"] == "ACCESS_TOKEN_MISSING"

    def test_tampered_token(self, admin_client):
        bad = APIClient()
        bad.session.cookies.update({k: v + "x" for k, v in admin_client.session.cookies.items()})
        r = bad.list_users()
        assert r.status_code == 401
        assert err(r)["code"] == "ACCESS_TOKEN_INVALID"

    def test_garbage_bearer_header(self):
        r = APIClient().request("GET", "/users", headers={"Authorization": "Bearer abc.def.ghi"})
        assert r.status_code == 401


class TestUsersListNegative:
    @pytest.mark.parametrize(
        "params,field",
        [
            ({"skip": -1}, "skip"),
            ({"limit": 0}, "limit"),
            ({"limit": "abc"}, "limit"),
            ({"limit": 101}, "limit"),
            ({"limit": 100000}, "limit"),
            ({"sortBy": "nonexistent"}, "sortBy"),
            ({"sortOrder": "sideways"}, "sortOrder"),
            ({"scope": "bogus"}, "scope"),
        ],
    )
    def test_invalid_params_return_422_naming_the_field(self, admin_client, params, field):
        r = admin_client.list_users(**params)
        assert r.status_code == 422
        assert field in fields(r)

    @pytest.mark.parametrize("limit", [1, 100])
    def test_limit_boundaries_accepted(self, admin_client, limit):
        r = admin_client.list_users(limit=limit)
        assert r.status_code == 200
        assert len(r.json()["data"]) <= limit

    @pytest.mark.parametrize("term", ['{"$ne":1}', "' OR '1'='1", "<script>alert(1)</script>", "%", "\\", "😀", "a" * 1000])
    def test_search_hostile_input_is_safe(self, admin_client, term):
        r = admin_client.list_users(search=term)
        assert r.status_code < 500
        if r.status_code == 200:
            assert r.json()["data"] == [] or r.json()["totalCount"] >= 0

    def test_search_wildcard_does_not_dump_everything(self, admin_client):
        total = admin_client.list_users(limit=100).json()["totalCount"]
        r = admin_client.list_users(search="%", limit=100)
        assert r.status_code == 200
        assert r.json()["totalCount"] < total or total == 0

    @pytest.mark.parametrize("method", ["DELETE", "PUT", "PATCH"])
    def test_unsupported_methods_not_routable(self, admin_client, method):
        r = admin_client.request(method, "/users", json={})
        assert r.status_code == 404
        assert err(r)["code"] == "ROUTE_NOT_FOUND"

    def test_response_has_no_password_fields(self, admin_client):
        raw = admin_client.list_users(limit=5).text.lower()
        for secret in ("password", "passwordhash", "refreshtoken"):
            assert secret not in raw


class TestProxyNegative:
    def test_missing_target_endpoint(self):
        r = APIClient().session.get(config.BASE_URL + "/api/proxy")
        assert r.status_code == 400

    def test_unknown_endpoint(self, admin_client):
        r = admin_client.request("GET", "/does-not-exist")
        assert r.status_code == 404
        assert err(r)["code"] == "ROUTE_NOT_FOUND"

    @pytest.mark.parametrize("endpoint", ["/../auth/login", "/users/../../etc/passwd", "//evil.example.com/x", "http://evil.example.com/"])
    def test_target_endpoint_cannot_escape_api(self, admin_client, endpoint):
        r = admin_client.request("GET", endpoint)
        assert r.status_code in (400, 404)
        assert "evil.example.com" not in r.text


class TestCheckEmailEnumeration:
    @pytest.mark.xfail(strict=True, reason="GUS-FX-0014: public POST /auth/register/check-email still reveals which emails are registered")
    def test_check_email_does_not_reveal_registered_accounts(self):
        known = APIClient().request("POST", "/auth/register/check-email", json={"email": config.ADMIN_EMAIL})
        unknown = APIClient().request("POST", "/auth/register/check-email", json={"email": "nobody_zz@yopmail.com"})
        assert known.json()["data"] == unknown.json()["data"], "response differs for registered vs unregistered email"

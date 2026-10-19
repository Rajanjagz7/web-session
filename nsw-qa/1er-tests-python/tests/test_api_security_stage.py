"""NSW staging - API security checks (non-destructive).

Covers session lifecycle (logout / refresh / token type), CORS, security headers,
error leakage, brute-force throttling (against a NON-existent email, so the real
admin account can never be locked), injection and malformed input.
No cookie or token value is ever printed.
"""
import os
import re

import pytest
from playwright.sync_api import Playwright

from config import EMAIL, PASSWORD

STAGE_URL = os.environ.get("NSW_STAGE_URL", "https://nswstage.rebatem8.com.au")
LOGIN = "/api/v1/auth/admin/login"
ME = "/api/v1/auth/me"
FAKE_EMAIL = "no-such-admin-qa@rebatem8nsw.com.au"


def new_ctx(playwright, **kw):
    return playwright.request.new_context(base_url=STAGE_URL, timeout=20_000, **kw)


def logged_in(playwright):
    ctx = new_ctx(playwright)
    assert ctx.post(LOGIN, data={"email": EMAIL, "password": PASSWORD}).status == 200
    return ctx


def cookie(ctx, name):
    return next(c["value"] for c in ctx.storage_state()["cookies"] if c["name"] == name)


def with_cookies(playwright, **cookies):
    hdr = "; ".join(f"{k}={v}" for k, v in cookies.items())
    return new_ctx(playwright, extra_http_headers={"cookie": hdr})


# --------------------------------------------------------------------------- session lifecycle

class TestSession:
    def test_logout_revokes_access_token(self, playwright):
        ctx = logged_in(playwright)
        access = cookie(ctx, "access_token")
        assert ctx.post("/api/v1/auth/logout").status in (200, 204)
        replay = with_cookies(playwright, access_token=access)
        try:
            assert replay.get(ME).status == 401, "access token still accepted after logout"
        finally:
            replay.dispose(); ctx.dispose()

    def test_logout_revokes_refresh_token(self, playwright):
        ctx = logged_in(playwright)
        refresh = cookie(ctx, "refresh_token")
        ctx.post("/api/v1/auth/logout")
        replay = with_cookies(playwright, refresh_token=refresh)
        try:
            res = replay.post("/api/v1/auth/refresh", data={})
            assert res.status == 401, f"refresh token still usable after logout -> {res.status}"
        finally:
            replay.dispose(); ctx.dispose()

    def test_logout_clears_cookies(self, playwright):
        ctx = logged_in(playwright)
        res = ctx.post("/api/v1/auth/logout")
        set_cookies = [h["value"].lower() for h in res.headers_array if h["name"].lower() == "set-cookie"]
        for name in ("access_token", "refresh_token"):
            c = next((s for s in set_cookies if s.startswith(name + "=")), "")
            assert c and ("max-age=0" in c or "expires=thu, 01 jan 1970" in c), f"{name} not cleared on logout"
        ctx.dispose()

    def test_refresh_token_cannot_be_used_as_access_token(self, playwright):
        ctx = logged_in(playwright)
        wrong = with_cookies(playwright, access_token=cookie(ctx, "refresh_token"))
        try:
            assert wrong.get(ME).status == 401
        finally:
            wrong.dispose(); ctx.dispose()

    def test_refresh_rotates_refresh_token(self, playwright):
        ctx = logged_in(playwright)
        old = cookie(ctx, "refresh_token")
        res = ctx.post("/api/v1/auth/refresh", data={})
        assert res.status == 200, f"refresh -> {res.status}"
        reuse = with_cookies(playwright, refresh_token=old)
        try:
            assert reuse.post("/api/v1/auth/refresh", data={}).status == 401, "old refresh token reusable after rotation"
        finally:
            reuse.dispose(); ctx.dispose()

    def test_tampered_access_token_rejected(self, playwright):
        ctx = logged_in(playwright)
        tok = cookie(ctx, "access_token")
        head, body, sig = tok.split(".")
        forged = f"{head}.{body}.{sig[:-2]}{'AA' if not sig.endswith('AA') else 'BB'}"
        bad = with_cookies(playwright, access_token=forged)
        try:
            assert bad.get(ME).status == 401
        finally:
            bad.dispose(); ctx.dispose()

    def test_authorization_bearer_not_a_bypass(self, playwright):
        ctx = new_ctx(playwright, extra_http_headers={"authorization": "Bearer null"})
        try:
            assert ctx.get(ME).status == 401
        finally:
            ctx.dispose()


# --------------------------------------------------------------------------- brute force

class TestBruteForce:
    def test_repeated_failed_logins_are_throttled(self, playwright):
        ctx = new_ctx(playwright)
        statuses = [ctx.post(LOGIN, data={"email": FAKE_EMAIL, "password": f"wrong-{i}"}).status for i in range(12)]
        ctx.dispose()
        assert 429 in statuses, f"12 failed logins, no 429: {statuses}"

    def test_failed_login_message_does_not_enumerate(self, playwright):
        ctx = new_ctx(playwright)
        a = ctx.post(LOGIN, data={"email": EMAIL, "password": "wrong-pw-x"})
        b = ctx.post(LOGIN, data={"email": "nobody-else-qa@rebatem8nsw.com.au", "password": "wrong-pw-x"})
        ma, mb = a.json().get("message"), b.json().get("message")
        ctx.dispose()
        assert a.status == b.status and ma == mb, f"{a.status} {ma!r} vs {b.status} {mb!r}"


# --------------------------------------------------------------------------- CORS / headers

class TestCorsAndHeaders:
    def test_cors_does_not_trust_arbitrary_origin(self, playwright):
        ctx = logged_in(playwright)
        res = ctx.get(ME, headers={"origin": "https://evil.example"})
        acao = res.headers.get("access-control-allow-origin", "")
        ctx.dispose()
        assert acao not in ("https://evil.example", "*"), f"ACAO={acao!r} with credentials"

    def test_cors_preflight_arbitrary_origin(self, playwright):
        ctx = new_ctx(playwright)
        res = ctx.fetch(ME, method="OPTIONS", headers={
            "origin": "https://evil.example", "access-control-request-method": "POST"})
        ctx.dispose()
        assert res.headers.get("access-control-allow-origin", "") != "https://evil.example"

    def test_cors_null_origin_not_trusted(self, playwright):
        ctx = new_ctx(playwright)
        res = ctx.get(ME, headers={"origin": "null"})
        ctx.dispose()
        assert res.headers.get("access-control-allow-origin", "") != "null"

    @pytest.mark.parametrize("header", ["content-security-policy", "x-content-type-options",
                                        "strict-transport-security", "referrer-policy"])
    def test_web_app_security_headers(self, playwright, header):
        ctx = new_ctx(playwright)
        res = ctx.get("/log-in")
        ctx.dispose()
        assert header in res.headers, f"{header} missing on the web app"

    def test_no_framework_or_version_disclosure(self, playwright):
        ctx = new_ctx(playwright)
        res = ctx.get(ME)
        ctx.dispose()
        assert "x-powered-by" not in res.headers, f"X-Powered-By: {res.headers.get('x-powered-by')}"
        assert not re.search(r"\d+\.\d+", res.headers.get("server", "")), f"Server: {res.headers.get('server')}"

    def test_trace_method_disabled(self, playwright):
        ctx = new_ctx(playwright)
        res = ctx.fetch(ME, method="TRACE")
        ctx.dispose()
        assert res.status in (400, 403, 404, 405, 501)


# --------------------------------------------------------------------------- error handling / injection

@pytest.fixture(scope="module")
def admin(playwright: Playwright):
    ctx = logged_in(playwright)
    yield ctx
    ctx.dispose()


STACK = re.compile(r"(at \w+ \(|node_modules|\.js:\d+|CastError|MongoServerError|ValidationError:|stack)", re.I)


class TestErrorHandling:
    @pytest.mark.parametrize("path", [
        "/api/v1/installers/not-an-id/members",
        "/api/v1/installers/not-an-id/members/by-role?role=Plumber",
        "/api/v1/jobs/..%2F..%2Fetc%2Fpasswd",
        "/api/v1/jobs/%00",
        "/api/v1/notes?entityType=job&entityId=not-an-id&skip=0&limit=5",
        "/api/v1/contractor-groups?installerId=not-an-id&skip=0&limit=5",
        "/api/v1/installers/not-an-id/members/by-role?role[$ne]=x",
    ])
    def test_bad_ids_no_500_no_stack(self, admin, path):
        res = admin.get(path)
        assert not STACK.search(res.text()), f"{path}: internal details leaked"
        assert res.status < 500, f"{path} -> {res.status}"

    def test_oversized_login_body(self, playwright):
        ctx = new_ctx(playwright)
        res = ctx.post(LOGIN, data={"email": FAKE_EMAIL, "password": "x" * 2_000_000})
        ctx.dispose()
        assert res.status in (400, 401, 413, 429), f"-> {res.status}"

    def test_login_rejects_non_json_content_type(self, playwright):
        """Simple-form content types enable CSRF-style login posts."""
        ctx = new_ctx(playwright)
        res = ctx.post(LOGIN, form={"email": EMAIL, "password": PASSWORD})
        ctx.dispose()
        assert res.status in (400, 415), f"form-encoded login -> {res.status}"

    @pytest.mark.parametrize("term", ["{\"$gt\":\"\"}", "'||'1'=='1", "a' OR 1=1--", "$where"])
    def test_search_injection_does_not_widen_results(self, admin, term):
        from urllib.parse import quote
        total = admin.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["total"]
        res = admin.get(f"/api/v1/jobs?skip=0&limit=1&search={quote(term)}")
        assert res.status < 500
        if res.status == 200:
            assert res.json()["data"]["total"] < total

    @pytest.mark.parametrize("q", ["search[$ne]=zz", "search[$regex]=.*", "installerId[$ne]=x"])
    def test_operator_params_rejected(self, admin, q):
        total = admin.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["total"]
        res = admin.get(f"/api/v1/jobs?skip=0&limit=1&{q}")
        assert res.status == 400 or res.json()["data"]["total"] < total, f"{q} -> {res.status}"

import re

from playwright.sync_api import expect

from config import EMAIL, PASSWORD
from api_helpers import login_api, to_json


class TestAdminLoginAPI:
    def test_valid_credentials_succeed(self, api_context):
        res = login_api(api_context)
        assert res.status == 200

    def test_wrong_password_rejected_with_generic_message(self, api_context):
        res = api_context.post(
            "/api/v1/auth/admin/login",
            data={"email": EMAIL, "password": "definitely-wrong-password"},
        )
        assert res.status == 401
        body = to_json(res)
        assert body["message"] == "Invalid email or password"

    def test_nonexistent_email_returns_same_generic_message(self, api_context):
        """Anti-enumeration: nonexistent email must not reveal that it doesn't exist."""
        res = api_context.post(
            "/api/v1/auth/admin/login",
            data={"email": "does-not-exist-12345@rebatem8nsw.com.au", "password": "anything"},
        )
        assert res.status == 401
        body = to_json(res)
        assert body["message"] == "Invalid email or password"


class TestAdminLoginUI:
    def test_wrong_password_shows_generic_error_and_does_not_log_in(self, page):
        page.goto("/log-in")
        page.get_by_placeholder(re.compile("email", re.I)).fill(EMAIL)
        page.get_by_placeholder(re.compile("password", re.I)).fill("definitely-wrong-password")
        page.get_by_role("button", name=re.compile(r"log ?in|sign ?in", re.I)).click()
        expect(page.get_by_text("Invalid email or password", exact=False).first).to_be_visible()
        expect(page.get_by_role("button", name=re.compile("add job", re.I))).not_to_be_visible()

    def test_valid_credentials_reach_jobs_screen(self, page):
        page.goto("/log-in")
        page.get_by_placeholder(re.compile("email", re.I)).fill(EMAIL)
        page.get_by_placeholder(re.compile("password", re.I)).fill(PASSWORD)
        page.get_by_role("button", name=re.compile(r"log ?in|sign ?in", re.I)).click()
        expect(page.get_by_role("button", name=re.compile("add job", re.I))).to_be_visible(timeout=15_000)


class TestOtpRequestVerifyAPI:
    """
    Public endpoints, no login required. Deliberately uses a fake/nonexistent
    phone number, never a real registered one - hitting a real number
    repeatedly on every run would spam an actual person's phone with OTP SMS
    messages.
    """

    FAKE_PHONE = "0400000999"

    def test_request_for_nonexistent_phone_returns_generic_message(self, api_context):
        res = api_context.post(
            "/api/v1/auth/otp/request",
            data={"phoneNumber": self.FAKE_PHONE, "countryCode": "+61"},
        )
        assert res.status == 200
        body = to_json(res)
        assert body["message"] == "If an account exists, a verification code has been sent."

    def test_verify_with_obviously_wrong_code_is_rejected(self, api_context):
        res = api_context.post(
            "/api/v1/auth/otp/verify",
            data={"phoneNumber": self.FAKE_PHONE, "countryCode": "+61", "code": "000000"},
        )
        assert res.status == 401
        body = to_json(res)
        assert body["message"] == "Invalid code"

    # BUG-04 (Critical, see QA report): requesting an OTP for a REAL
    # registered phone number currently returns 500 Internal Server Error on
    # the first attempt (likely an unhandled Twilio/SMS-provider failure),
    # even though the follow-up 30s resend cooldown (429) correctly engages
    # afterward. Not automated here on purpose - re-running this against a
    # real number on every run would repeatedly SMS an actual person. Verify
    # manually against a known registered number when re-testing this fix,
    # e.g. an Installer User's phone from the Installer Users list.

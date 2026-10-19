"""NSW staging API tests - read-only (GET only, plus admin login).

Known defects already logged in NSW_BUGS.md are marked xfail with their ID, so
a plain FAILED in the run is a new finding. Nothing here creates, edits or
deletes data.
"""
import os
import re

import pytest
from playwright.sync_api import Playwright

from config import EMAIL, PASSWORD
from api_helpers import to_json

STAGE_URL = os.environ.get("NSW_STAGE_URL", "https://nswstage.rebatem8.com.au")
LOGIN = "/api/v1/auth/admin/login"

# endpoint -> key of the list inside data
LISTS = {
    "/api/v1/jobs": "jobs",
    "/api/v1/installers": "installers",
    "/api/v1/matrix": "items",
    "/api/v1/users?roleType=admin_user": "users",
    "/api/v1/activity-logs": "logs",
}


def url(path, **q):
    sep = "&" if "?" in path else "?"
    return path + (sep + "&".join(f"{k}={v}" for k, v in q.items()) if q else "")


@pytest.fixture
def anon(playwright: Playwright):
    ctx = playwright.request.new_context(base_url=STAGE_URL, timeout=20_000)
    yield ctx
    ctx.dispose()


@pytest.fixture(scope="module")
def admin(playwright: Playwright):
    ctx = playwright.request.new_context(base_url=STAGE_URL, timeout=20_000)
    res = ctx.post(LOGIN, data={"email": EMAIL, "password": PASSWORD})
    assert res.status == 200, f"admin login failed: {res.status}"
    yield ctx
    ctx.dispose()


@pytest.fixture(scope="module")
def sample_job(admin):
    return admin.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["jobs"][0]


@pytest.fixture(scope="module")
def job_statuses(admin):
    return [s["status"] for s in admin.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["statusList"]]


# --------------------------------------------------------------------------- auth

class TestLogin:
    def test_login_response_has_no_secrets(self, anon):
        res = anon.post(LOGIN, data={"email": EMAIL, "password": PASSWORD})
        assert res.status == 200
        body = res.text().lower()
        for leak in ("password", "hash", "salt", "otp"):
            assert f'"{leak}' not in body, f"login response contains a '{leak}' field"

    def test_auth_cookies_are_httponly_secure_samesite(self, anon):
        res = anon.post(LOGIN, data={"email": EMAIL, "password": PASSWORD})
        cookies = [h["value"] for h in res.headers_array if h["name"].lower() == "set-cookie"]
        names = {c.split("=", 1)[0] for c in cookies}
        assert {"access_token", "refresh_token"} <= names
        for c in cookies:
            flags = c.lower()
            name = c.split("=", 1)[0]
            assert "httponly" in flags, f"{name} not HttpOnly"
            assert "secure" in flags, f"{name} not Secure"
            assert "samesite" in flags, f"{name} has no SameSite"

    @pytest.mark.parametrize("payload", [
        {},
        {"email": EMAIL},
        {"password": "x"},
        {"email": "", "password": ""},
        {"email": "not-an-email", "password": "x"},
        {"email": ["a@b.com"], "password": "x"},
        {"email": {"$ne": None}, "password": {"$ne": None}},
    ], ids=["empty", "no-password", "no-email", "blank", "bad-email", "email-array", "operator-object"])
    def test_malformed_login_rejected_with_4xx(self, anon, payload):
        res = anon.post(LOGIN, data=payload)
        assert 400 <= res.status < 500, f"expected 4xx, got {res.status}"
        assert "access_token=" not in (res.headers.get("set-cookie") or "")

    def test_wrong_password_401(self, anon):
        res = anon.post(LOGIN, data={"email": EMAIL, "password": "wrong-password-123"})
        assert res.status == 401

    def test_email_is_case_insensitive(self, anon):
        res = anon.post(LOGIN, data={"email": EMAIL.upper(), "password": PASSWORD})
        assert res.status == 200, f"upper-case email rejected: {res.status}"

    def test_email_with_surrounding_spaces_is_trimmed(self, anon):
        res = anon.post(LOGIN, data={"email": f"  {EMAIL}  ", "password": PASSWORD})
        assert res.status == 200, f"email with spaces rejected: {res.status}"


class TestAuthRequired:
    @pytest.mark.parametrize("path", ["/api/v1/auth/me", *LISTS, "/api/v1/installers/000000000000000000000000/members"])
    def test_no_cookie_401(self, anon, path):
        res = anon.get(url(path, skip=0, limit=1) if path in LISTS else path)
        assert res.status == 401, f"{path} -> {res.status} without auth"

    @pytest.mark.parametrize("token", ["garbage", "eyJhbGciOiJub25lIn0.eyJzdWIiOiJ4In0.", ""])
    def test_forged_access_token_401(self, playwright, token):
        ctx = playwright.request.new_context(base_url=STAGE_URL, timeout=20_000,
                                             extra_http_headers={"cookie": f"access_token={token}"})
        try:
            assert ctx.get("/api/v1/auth/me").status == 401
        finally:
            ctx.dispose()

    def test_me_returns_logged_in_admin(self, admin):
        d = admin.get("/api/v1/auth/me").json()["data"]
        assert d["user"]["email"].lower() == EMAIL.lower()
        assert d["user"]["isActive"] is True
        assert d["impersonating"] is False


# --------------------------------------------------------------------------- list contract

@pytest.mark.parametrize("path,key", LISTS.items(), ids=list(LISTS))
class TestListContract:
    def test_envelope(self, admin, path, key):
        res = admin.get(url(path, skip=0, limit=5))
        assert res.status == 200
        b = res.json()
        assert b["success"] is True and b["statusCode"] == 200
        d = b["data"]
        assert isinstance(d[key], list) and isinstance(d["total"], int)
        assert d["skip"] == 0 and d["limit"] == 5
        assert len(d[key]) <= 5
        assert d["isNext"] == (d["total"] > 5)

    def test_skip_past_end_is_empty(self, admin, path, key):
        total = admin.get(url(path, skip=0, limit=1)).json()["data"]["total"]
        d = admin.get(url(path, skip=total + 10, limit=5)).json()["data"]
        assert d[key] == [] and d["isNext"] is False

    def test_pages_do_not_overlap(self, admin, path, key):
        p1 = admin.get(url(path, skip=0, limit=3)).json()["data"][key]
        p2 = admin.get(url(path, skip=3, limit=3)).json()["data"][key]
        ids1, ids2 = {x.get("id") or x.get("_id") for x in p1}, {x.get("id") or x.get("_id") for x in p2}
        assert not ids1 & ids2, f"same records on page 1 and 2: {ids1 & ids2}"

    @pytest.mark.parametrize("q", [
        {"skip": -1, "limit": 5}, {"skip": 0, "limit": -5}, {"skip": 0, "limit": 0},
        {"skip": "abc", "limit": 5}, {"skip": 0, "limit": "abc"},
    ], ids=["neg-skip", "neg-limit", "zero-limit", "text-skip", "text-limit"])
    def test_bad_paging_rejected(self, admin, path, key, q):
        res = admin.get(url(path, **q))
        assert res.status == 400, f"{q} -> {res.status}"

    def test_huge_limit_is_capped(self, admin, path, key):
        res = admin.get(url(path, skip=0, limit=1000000))
        assert res.status in (200, 400), f"-> {res.status}"
        if res.status == 200:
            assert len(res.json()["data"][key]) <= 100, "no server-side cap on limit"

    def test_invalid_sort_type_rejected(self, admin, path, key):
        res = admin.get(url(path, skip=0, limit=2, sort="createdAt", sortType="sideways"))
        assert res.status == 400, f"-> {res.status}"

    def test_unknown_sort_field_not_500(self, admin, path, key):
        res = admin.get(url(path, skip=0, limit=2, sort="doesNotExist", sortType="asc"))
        assert res.status < 500, f"-> {res.status}"


# --------------------------------------------------------------------------- jobs

UI_TAB_STATUSES = ["Install In Progress", "Action Required", "Being Assessed", "Complete", "Archived"]


class TestJobs:
    def test_sorted_by_created_desc(self, admin):
        jobs = admin.get("/api/v1/jobs?skip=0&limit=20&sort=createdAt&sortType=desc").json()["data"]["jobs"]
        dates = [j["createdAt"] for j in jobs]
        assert dates == sorted(dates, reverse=True)

    def test_sorted_by_created_asc(self, admin):
        jobs = admin.get("/api/v1/jobs?skip=0&limit=20&sort=createdAt&sortType=asc").json()["data"]["jobs"]
        dates = [j["createdAt"] for j in jobs]
        assert dates == sorted(dates)

    def test_job_numbers_well_formed_and_unique(self, admin):
        jobs, skip = [], 0
        while True:
            d = admin.get(f"/api/v1/jobs?skip={skip}&limit=100").json()["data"]
            jobs += d["jobs"]
            skip += 100
            if not d["isNext"]:
                break
        nums = [j["jobNumber"] for j in jobs]
        bad = [n for n in nums if not re.fullmatch(r"M8N\d{6}", n or "")]
        assert not bad, f"malformed job numbers: {bad}"
        assert len(nums) == len(set(nums)), "duplicate job numbers"

    def test_list_excludes_deleted(self, admin):
        jobs = admin.get("/api/v1/jobs?skip=0&limit=100").json()["data"]["jobs"]
        assert not [j["jobNumber"] for j in jobs if j.get("isDeleted")]

    def test_every_listed_status_is_in_status_list(self, admin, job_statuses):
        jobs = admin.get("/api/v1/jobs?skip=0&limit=100").json()["data"]["jobs"]
        unknown = {j["status"] for j in jobs} - set(job_statuses)
        assert not unknown, f"jobs with status not in statusList: {unknown}"

    def test_status_filter_by_key(self, admin, job_statuses):
        failures = []
        for s in job_statuses:
            res = admin.get(url("/api/v1/jobs", skip=0, limit=50, status=s))
            if res.status != 200:
                failures.append(f"{s}: HTTP {res.status}")
                continue
            wrong = {j["status"] for j in res.json()["data"]["jobs"]} - {s}
            if wrong:
                failures.append(f"{s}: returned {wrong}")
        assert not failures, failures

    @pytest.mark.xfail(reason="NSW-STG-24: UI tab labels rejected with 400 'Invalid status value'")
    @pytest.mark.parametrize("label", UI_TAB_STATUSES)
    def test_status_filter_ui_tab_labels(self, admin, label):
        assert admin.get(url("/api/v1/jobs", skip=0, limit=5, status=label)).status == 200

    def test_unknown_status_400(self, admin):
        assert admin.get("/api/v1/jobs?skip=0&limit=5&status=not_a_status").status == 400

    @pytest.mark.parametrize("q", ["status[$ne]=x", "status[$regex]=.*", "status[]=a&status[]=b"],
                             ids=["ne", "regex", "array"])
    def test_operator_in_query_rejected(self, admin, q):
        res = admin.get(f"/api/v1/jobs?skip=0&limit=5&{q}")
        assert res.status == 400, f"{q} -> {res.status}"

    def test_get_by_id(self, admin, sample_job):
        res = admin.get(f"/api/v1/jobs/{sample_job['id']}")
        assert res.status == 200
        assert res.json()["data"]  # non-empty
        assert sample_job["jobNumber"] in res.text()

    @pytest.mark.parametrize("sub", ["tasks", "documents", "all-photos"])
    def test_job_sub_resources(self, admin, sample_job, sub):
        assert admin.get(f"/api/v1/jobs/{sample_job['id']}/{sub}").status == 200

    def test_unknown_job_object_id_404(self, admin):
        assert admin.get("/api/v1/jobs/000000000000000000000000").status == 404

    @pytest.mark.xfail(reason="NSW-STG-34: well-formed but unknown job number returns 400 'Invalid job id'")
    def test_unknown_job_number_404(self, admin):
        assert admin.get("/api/v1/jobs/M8N999999").status == 404

    def test_malformed_job_id_4xx(self, admin):
        res = admin.get("/api/v1/jobs/not-an-id")
        assert 400 <= res.status < 500, f"-> {res.status}"

    def test_notes_for_job(self, admin, sample_job):
        res = admin.get(url("/api/v1/notes", skip=0, limit=10, entityType="job", entityId=sample_job["id"]))
        assert res.status == 200

    def test_notes_bad_entity_type_rejected(self, admin, sample_job):
        res = admin.get(url("/api/v1/notes", skip=0, limit=10, entityType="banana", entityId=sample_job["id"]))
        assert res.status == 400, f"-> {res.status}"


class TestJobSearch:
    def _search(self, admin, term):
        from urllib.parse import quote
        return admin.get(f"/api/v1/jobs?skip=0&limit=10&search={quote(term)}")

    def test_search_by_job_number(self, admin, sample_job):
        jobs = self._search(admin, sample_job["jobNumber"]).json()["data"]["jobs"]
        assert [j["jobNumber"] for j in jobs] == [sample_job["jobNumber"]]

    @pytest.mark.xfail(reason="NSW-STG-17: search not trimmed")
    def test_search_trims_spaces(self, admin, sample_job):
        jobs = self._search(admin, f"  {sample_job['jobNumber']}  ").json()["data"]["jobs"]
        assert [j["jobNumber"] for j in jobs] == [sample_job["jobNumber"]]

    @pytest.mark.xfail(reason="NSW-STG-19: single special character returns every job")
    @pytest.mark.parametrize("term", ["%", "*", "("])
    def test_special_char_does_not_match_all(self, admin, term):
        res = self._search(admin, term)
        assert res.status == 400 or res.json()["data"]["total"] == 0

    def test_regex_wildcard_does_not_match_all(self, admin):
        total = admin.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["total"]
        res = self._search(admin, ".*")
        assert res.status < 500
        if res.status == 200:
            assert res.json()["data"]["total"] < total, "'.*' is evaluated as a regex and matches every job"

    def test_long_search_not_500(self, admin):
        assert self._search(admin, "a" * 5000).status < 500


# --------------------------------------------------------------------------- other modules

class TestInstallers:
    def test_members_of_installer(self, admin):
        inst = admin.get("/api/v1/installers?skip=0&limit=1").json()["data"]["installers"][0]
        res = admin.get(f"/api/v1/installers/{inst['id']}/members")
        assert res.status == 200

    def test_members_by_unknown_role_rejected(self, admin):
        inst = admin.get("/api/v1/installers?skip=0&limit=1").json()["data"]["installers"][0]
        res = admin.get(f"/api/v1/installers/{inst['id']}/members/by-role?role=Astronaut")
        assert res.status == 400, f"-> {res.status}"

    def test_unknown_installer_404(self, admin):
        res = admin.get("/api/v1/installers/000000000000000000000000/members")
        assert res.status == 404, f"-> {res.status}"

    @pytest.mark.parametrize("sub", ["members", "members/by-role?role=Plumber"])
    def test_malformed_installer_id_not_500(self, admin, sub):
        res = admin.get(f"/api/v1/installers/not-an-id/{sub}")
        assert 400 <= res.status < 500, f"-> {res.status}"

    def test_abn_is_11_digits(self, admin):
        insts = admin.get("/api/v1/installers?skip=0&limit=100").json()["data"]["installers"]
        bad = [(i["companyName"], i["abn"]) for i in insts
               if i.get("abn") and not re.fullmatch(r"\d{11}", str(i["abn"]).replace(" ", ""))]
        assert not bad, f"installers with malformed ABN: {bad}"


class TestUsers:
    def test_user_list_has_no_secrets(self, admin):
        body = admin.get("/api/v1/users?roleType=admin_user&skip=0&limit=50").text().lower()
        for leak in ('"password', '"hash', '"salt', '"otp', '"resettoken'):
            assert leak not in body, f"user list exposes {leak}"

    def test_unknown_role_type_rejected(self, admin):
        res = admin.get("/api/v1/users?roleType=superhero&skip=0&limit=5")
        assert res.status == 400, f"-> {res.status}"


class TestKnownBrokenEndpoints:
    """Regression checks for 404s already logged - these flip to XPASS when fixed."""

    @pytest.mark.xfail(reason="NSW-STG-01")
    @pytest.mark.parametrize("ep", ["job-count", "job-breakdown", "job-rebate", "top-product", "avg-complete-time"])
    def test_dashboard(self, admin, ep):
        assert admin.get(f"/api/v1/dashboard/{ep}").status == 200

    @pytest.mark.xfail(reason="NSW-STG-02")
    def test_site_list(self, admin):
        assert admin.get("/api/v1/site/list?skip=0&limit=10&platform=web").status == 200

    @pytest.mark.xfail(reason="NSW-STG-03")
    def test_invoice_list(self, admin):
        assert admin.get("/api/v1/invoice/list?skip=0&limit=10&platform=web").status == 200

    @pytest.mark.xfail(reason="NSW-STG-04")
    def test_installer_filter_list(self, admin):
        assert admin.get("/api/v1/installer/filter/list?skip=0&limit=10").status == 200

import re
import time

from config import EMAIL, PASSWORD
from api_helpers import login_api, to_json


def get_any_job_id(api_context) -> str:
    """Fetches any one active job's id to attach notes to, rather than hardcoding a job that might get deleted later."""
    res = api_context.get("/api/v1/jobs?limit=1")
    body = to_json(res) or {}
    jobs = body.get("data", {}).get("jobs", [])
    if not jobs:
        raise Exception("No jobs found to attach a note to - create one first.")
    return jobs[0]["id"]


def test_fully_empty_note_is_rejected(api_context):
    login_api(api_context)
    job_id = get_any_job_id(api_context)

    res = api_context.post("/api/v1/notes", data={"entityType": "job", "entityId": job_id, "note": ""})
    assert res.status == 400
    body = to_json(res)
    assert body["error"]["details"][0]["message"] == "Provide note text or at least one attachment"


def test_valid_text_only_note_is_created_successfully(api_context):
    login_api(api_context)
    job_id = get_any_job_id(api_context)

    res = api_context.post(
        "/api/v1/notes",
        data={"entityType": "job", "entityId": job_id, "note": f"Automated QA note - {int(time.time() * 1000)}"},
    )
    assert res.status == 201
    body = to_json(res)
    assert "Automated QA note" in body["data"]["note"]["note"]


def test_known_bug_bug08_ui_note_with_internal_toggle_untouched_sends_internal(page):
    """
    BUG-08 (Medium, see QA report): calling POST /notes directly with no
    `visibility` field correctly defaults to 'external' (see the test above)
    - so the backend default matches the spec. The bug is in the FRONTEND: it
    explicitly sends visibility: "internal" in the request body even when the
    "Internal" toggle is left in its default/unchecked state, so this has to
    be driven through the real UI to reproduce - a direct API call bypasses
    the buggy code path entirely. This test currently asserts the ACTUAL
    (buggy) behaviour so the suite tracks the regression; flip the
    expectation to 'external' once fixed.
    """
    page.goto("/log-in")
    page.get_by_placeholder(re.compile("email", re.I)).fill(EMAIL)
    page.get_by_placeholder(re.compile("password", re.I)).fill(PASSWORD)
    page.get_by_role("button", name=re.compile(r"log ?in|sign ?in", re.I)).click()
    page.get_by_role("button", name=re.compile("add job", re.I)).wait_for(state="visible", timeout=20_000)

    # Open a known-signed job (the Notes tab only exists on the full
    # job-detail page, which only renders once a job is past "Engagement
    # Sent" - an arbitrary first row could still be unsigned).
    page.goto("/jobs")
    page.get_by_placeholder("Search Jobs...").fill("M8N000114")
    page.wait_for_timeout(1000)
    page.locator("table tbody tr").first.locator("svg, img, button").first.click()
    page.get_by_role("button", name="Notes", exact=True).click()
    page.locator(".ql-editor").first.wait_for(state="visible", timeout=15_000)

    page.locator(".ql-editor").first.click()
    page.keyboard.type(f"UI default-visibility check - {int(time.time() * 1000)}")

    with page.expect_response(lambda r: "/api/v1/notes" in r.url and r.request.method == "POST") as resp_info:
        page.get_by_role("button", name=re.compile(r"^add note$", re.I)).click()
    body = resp_info.value.json()
    assert body["data"]["note"]["visibility"] == "internal"  # documented default should be 'external'


def test_explicit_external_note_is_created_with_external_visibility(api_context):
    login_api(api_context)
    job_id = get_any_job_id(api_context)

    res = api_context.post(
        "/api/v1/notes",
        data={
            "entityType": "job",
            "entityId": job_id,
            "note": f"Explicit external - {int(time.time() * 1000)}",
            "visibility": "external",
        },
    )
    assert res.status == 201
    body = to_json(res)
    assert body["data"]["note"]["visibility"] == "external"


def test_explicit_internal_note_is_created_with_internal_visibility(api_context):
    login_api(api_context)
    job_id = get_any_job_id(api_context)

    res = api_context.post(
        "/api/v1/notes",
        data={
            "entityType": "job",
            "entityId": job_id,
            "note": f"Explicit internal - {int(time.time() * 1000)}",
            "visibility": "internal",
        },
    )
    assert res.status == 201
    body = to_json(res)
    assert body["data"]["note"]["visibility"] == "internal"

"""Read-only coverage of the modules not yet exercised in the earlier sessions:
Activity Logs, Notifications, Schedule, Job Report (submissions list) and every Settings tab.

Each test opens the module and fails on: a JavaScript error, a failed API call (HTTP >= 400), a blank
page, or an error message on screen. Content is awaited explicitly because the app renders the new page
after the URL has already changed (finding C9).
"""
import re

import pytest

from utils.config import BASE_URL

IGNORED_API = ("is-logged-in",)
ERROR_TEXT = re.compile(r"something went wrong|unexpected error|application error|cannot read prop", re.I)


def watch(page):
    """Collect JS errors and failing API calls for the rest of the test."""
    errors, bad_api = [], []
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    page.on("response", lambda r: bad_api.append(f"{r.status} {r.request.method} {r.url.split('/api/v1/')[-1][:70]}")
            if r.status >= 400 and "/api/" in r.url and not any(x in r.url for x in IGNORED_API) else None)
    return errors, bad_api


def open_and_wait(page, path: str, min_chars: int = 60, timeout_s: int = 40) -> str:
    """Go to a URL and wait until the app's main area has real content (not the loading spinner).

    Dismisses the "A new version is available" interstitial if it appears (related to finding F10:
    the app reloads itself on a version.json change; this full-page prompt is the same behaviour
    surfacing as a blocking screen instead of a silent reload) — a real user would hit this too, so
    a test suite has to click through it rather than treat it as a failure.
    """
    page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
    main = page.locator("main").first
    update_btn = page.get_by_role("button", name="Update now")
    for _ in range(timeout_s * 2):
        if update_btn.count():
            update_btn.click()
            page.wait_for_timeout(2000)
        text = main.inner_text() if main.count() else ""
        if len(text.strip()) >= min_chars:
            return text
        page.wait_for_timeout(500)
    return main.inner_text() if main.count() else ""


def assert_healthy(text, errors, bad_api, what):
    assert len(text.strip()) >= 60, f"{what}: page stayed blank/loading"
    assert not ERROR_TEXT.search(text[:600]), f"{what}: error text on screen: {text[:200]!r}"
    assert not errors, f"{what}: JavaScript errors: {errors}"
    assert not bad_api, f"{what}: failed API calls: {bad_api}"


MODULES = [
    ("Activity Logs", "/app/activity-log/list", "Activity Log"),
    ("Notifications", "/app/notifications", "Notifications"),
    ("Schedule", "/app/schedule", None),
    ("Job Report", "/app/report/list", "Job Report"),
]


@pytest.mark.parametrize("name,path,heading", MODULES, ids=[m[0] for m in MODULES])
def test_module_loads_cleanly(logged_in_page, name, path, heading):
    page = logged_in_page
    errors, bad_api = watch(page)
    text = open_and_wait(page, path)
    assert_healthy(text, errors, bad_api, name)
    if heading:
        assert heading.lower() in text.lower(), f"{name}: expected heading {heading!r} in {text[:120]!r}"


SETTINGS_TABS = [
    ("Company Settings", "/app/global-settings/workspace"),
    ("Roles & Permissions", "/app/role/list"),
    ("Shifts & Breaks", "/app/shift-and-break/list"),
    ("Integrations", "/app/global-settings/integrations"),
    ("Checklists", "/app/checklist/list"),
    ("Holidays", "/app/global-settings/holiday"),
    ("Report Builder", "/app/form-builder/list"),
    ("My Subscription", "/app/global-settings/subscription"),
    ("Payment Cards", "/app/global-settings/billing/cards"),
    ("Purchase History", "/app/global-settings/billing/history"),
]


@pytest.mark.parametrize("name,path", SETTINGS_TABS, ids=[t[0] for t in SETTINGS_TABS])
def test_settings_tab_loads_cleanly(logged_in_page, name, path):
    """A "Not included in your plan" upsell is a valid rendered state for a plan-gated tab, not a
    failure on its own. FINDING (2026-09-21): Roles & Permissions showed real content on one run and
    this upsell on another, for the same account and URL — that inconsistency is flagged below rather
    than asserted on, since either single render is individually correct."""
    page = logged_in_page
    errors, bad_api = watch(page)
    text = open_and_wait(page, path)
    assert_healthy(text, errors, bad_api, f"Settings > {name}")
    gated = "not included in your plan" in text.lower()
    if gated:
        print(f"NOTE: Settings > {name} rendered as plan-gated ('Not included in your plan') this run.")
    else:
        assert "Settings" in text, f"Settings > {name}: settings navigation not shown"


def test_job_report_list_shows_submissions(logged_in_page):
    """The page lists submissions (not the template-attached job reports); 61 were seeded on 2026-09-21."""
    page = logged_in_page
    errors, bad_api = watch(page)
    page.goto(f"{BASE_URL}/app/report/list", wait_until="domcontentloaded")
    page.get_by_text(re.compile(r"REPORT-\d+")).first.wait_for(timeout=45_000)
    rows = page.locator("tbody tr")
    assert rows.count() >= 5, f"expected several rows, saw {rows.count()}"
    statuses = {s.strip() for s in page.locator("tbody tr td:nth-last-child(2)").all_inner_texts()}
    assert statuses & {"Submitted", "Approved", "Rejected"}, f"unexpected statuses: {statuses}"
    assert not errors and not bad_api, f"errors={errors} bad_api={bad_api}"


def test_activity_log_search_filters_results(logged_in_page):
    page = logged_in_page
    open_and_wait(page, "/app/activity-log/list")
    search = page.get_by_placeholder(re.compile("search", re.I)).first
    if not search.count():
        pytest.skip("Activity Logs has no search box in this build")
    before = page.locator("tbody tr").count()
    search.fill("zzzz-no-such-activity-xyz")
    page.wait_for_timeout(2500)
    after = page.locator("tbody tr").count()
    body = page.locator("main").first.inner_text().lower()
    assert after < before or "no data" in body or "nothing to show" in body, (
        f"search for a nonsense term did not narrow results (before={before}, after={after})")

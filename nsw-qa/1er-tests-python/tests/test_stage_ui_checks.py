"""
UI-level versions of the API-testing checks, run against the redesigned staging
wizard. Read-only, or limited to job M8N000078 (Harrison Doyle), which QA created.
Nothing here submits a new job.
"""
import os
import re

import pytest
from playwright.sync_api import expect

from helpers import login, control_for_label

OWN_JOB = os.environ.get("NSW_OWN_JOB", "M8N000078")

REQUIRED_STEP1 = [
    "Activity Type", "Method of Lead Generation", "Building Type", "Installer (Company)",
    "Customer Name", "Customer Phone", "Customer Email", "Site Address", "Postcode",
]


def open_blank_add_job(page):
    page.goto("/jobs")
    page.get_by_role("button", name=re.compile("add job", re.I)).click()
    page.get_by_placeholder("Enter customer name").wait_for(state="visible")
    return page.get_by_role("dialog")


def open_own_job(page):
    page.goto("/jobs")
    page.get_by_placeholder(re.compile("search jobs", re.I)).fill(OWN_JOB)
    page.wait_for_timeout(1500)
    row = page.locator("table tbody tr").first
    row_text = row.inner_text()
    row.locator("svg, img, button").first.click()
    page.wait_for_timeout(2000)
    return row_text, page.get_by_role("dialog")


def test_blank_step1_submit_lists_every_required_field(page):
    """Validation check: every required field reports itself, and no job is created."""
    login(page)
    dialog = open_blank_add_job(page)
    dialog.get_by_role("button", name=re.compile("send engagement letter", re.I)).click()
    for field in REQUIRED_STEP1:
        expect(dialog.get_by_text(f"{field} is required", exact=True)).to_be_visible()
    # Optional fields must NOT be flagged.
    for optional in ("Own Reference", "Installation Date", "ABN/ACN"):
        expect(dialog.get_by_text(f"{optional} is required", exact=True)).to_have_count(0)


@pytest.mark.xfail(reason="BUG: Escape inside an open dropdown closes the whole Add Job drawer and discards input", strict=True)
def test_escape_in_dropdown_does_not_discard_the_form(page):
    login(page)
    dialog = open_blank_add_job(page)
    dialog.get_by_placeholder("Enter customer name").fill("Charlotte Nguyen")
    control = control_for_label(dialog, "Activity type")
    control.click()
    page.get_by_role("option").first.wait_for(state="visible")
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)
    expect(page.get_by_placeholder("Enter customer name")).to_have_value("Charlotte Nguyen", timeout=3000)


def test_own_job_list_row_matches_wizard_values(page):
    """List vs detail: what the All Jobs row shows must match the job's own record."""
    login(page)
    row_text, dialog = open_own_job(page)
    body = page.locator("body").inner_text()
    for expected in ("Harrison Doyle", "BAWA", "412987654", "1 George St", "20/10/2026"):
        assert expected in row_text, f"list row missing {expected!r}: {row_text!r}"
    assert "Site Assessment and Nomination Requested" in row_text
    assert "Site Assessment and Nomination Requested" in body, "status shown in the job view differs from the list"


def test_own_job_step2_team_persists_after_reload(page):
    """Read-back check: the Electrician / Refrigeration Mechanic saved on step 2 are still there after a reload."""
    login(page)
    open_own_job(page)
    page.reload()
    open_own_job(page)
    body = page.locator("body").inner_text()
    assert body.count("Belinda Baker") >= 2, "saved step-2 team members did not persist"
    expect(page.get_by_text("Awaiting signature", exact=False).first).to_be_visible()

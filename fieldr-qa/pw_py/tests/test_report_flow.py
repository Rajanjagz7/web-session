"""Add Report (Job Report submission) through the UI.

Uses an existing In Progress job that carries the "Site Safety Inspection Report" template.
"""
from pages.report_page import ReportPage
from utils.au_data import stamp, yopmail


def _open_with_job(page) -> ReportPage:
    report = ReportPage(page)
    report.open_new()
    job = report.pick_job("In Progress")
    assert "In Progress" in job, f"expected an In Progress job, got {job!r}"
    template = report.pick_type()
    assert template, "the job should offer at least one report template"
    return report


def test_empty_report_shows_required_errors_and_sends_nothing(logged_in_page):
    page = logged_in_page
    report = _open_with_job(page)
    sent = []
    page.on("request", lambda r: sent.append(r.url) if r.method == "POST" and "/submission/submit" in r.url else None)
    report.save().click()
    page.wait_for_timeout(1500)
    assert not sent, f"Save sent a request with required fields empty: {sent}"
    assert report.inline_errors() or report.save().get_attribute("aria-disabled") == "true", (
        "expected inline errors or a disabled Save when required fields are empty")


def test_submit_site_safety_report(logged_in_page):
    page = logged_in_page
    report = _open_with_job(page)
    report.fill_site_safety_report(
        site="145 Eagle Street, Brisbane QLD 4000",
        inspector=f"Olivia Nguyen ({stamp()})",
        hazards="Loose scaffold coupler on the north face; exclusion zone set up until it is replaced.",
        supervisor_email=yopmail("supervisor"),
    )
    with page.expect_response(lambda r: "/submission/submit" in r.url and r.request.method == "POST") as resp:
        report.save().click()
    assert resp.value.status == 200, f"submission/submit returned {resp.value.status}"

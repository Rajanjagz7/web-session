"""CMS: what the Add CMS form actually offers, and creating an entry through it.

Finding (2026-09-21): the Type dropdown offers ONLY "FAQ". Induction, Help, Privacy Policy and
Terms & Conditions entries exist in the tenant (seeded through the API on 2026-09-19) but cannot be
created through the UI. If the app later adds types, the first test fails so this file gets updated.
"""
import pytest

from pages.cms_page import CmsPage
from utils.au_data import stamp


def _open_type_options(page, cms: CmsPage) -> list[str]:
    combo = cms.type_combobox()
    try:
        combo.click(timeout=4000)
    except Exception:
        combo.focus()
        page.keyboard.press("ArrowDown")
    page.wait_for_timeout(800)
    return [t.strip() for t in page.locator("[role=option]").all_inner_texts() if t.strip()]


def test_type_dropdown_only_offers_faq(logged_in_page):
    page = logged_in_page
    cms = CmsPage(page)
    cms.open_new()
    options = _open_type_options(page, cms)
    assert options == ["FAQ"], (
        f"Type dropdown options changed: {options}. Update this test and the docs "
        "(previously only FAQ could be created through the UI)."
    )


TITLE_ERROR = "Title must be between 3 to 35 characters"


@pytest.mark.parametrize("length,expect_error", [(2, True), (3, False), (35, False), (36, True)],
                         ids=["2-below-min", "3-min", "35-max", "36-above-max"])
def test_title_length_boundaries(logged_in_page, length, expect_error):
    """Boundary values for the Title rule shown inline by the form (nothing is saved)."""
    page = logged_in_page
    cms = CmsPage(page)
    cms.open_new()
    cms.fill_title("T" * length)
    page.keyboard.press("Tab")
    page.wait_for_timeout(600)
    error = page.get_by_text(TITLE_ERROR)
    assert (error.count() > 0) == expect_error, (
        f"title length {length}: expected error={expect_error}, error shown={error.count() > 0}")


def test_create_faq_entry(logged_in_page):
    page = logged_in_page
    cms = CmsPage(page)
    cms.open_new()
    _open_type_options(page, cms)
    page.locator("[role=option]").filter(has_text="FAQ").first.click()
    cms.fill_title(f"Job status reset {stamp()}")  # the app enforces a 3 to 35 character title
    cms.fill_faq(
        question=f"How do I reset a job status after marking it Completed by mistake? ({stamp()})",
        answer="Open the job, choose Edit, and change the status back to In Progress. The change is recorded in Activity Logs.",
    )
    with page.expect_response(lambda r: r.url.endswith("/api/v1/cms/create") and r.request.method == "POST") as resp_info:
        cms.save().click()
    assert resp_info.value.status == 200, f"cms/create returned {resp_info.value.status}"
    page.wait_for_url("**/cms/list**", timeout=15_000)

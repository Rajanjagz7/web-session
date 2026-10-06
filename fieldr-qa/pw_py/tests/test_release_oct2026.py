"""Release notes (Oct 2026): Schedule, Customers & jobs, Users, Roles.

Everything here is read-only: dialogs and forms are opened and checked but never saved, so no
records are left behind. Not covered (needs data this tenant doesn't have, or a seat purchase):
company-name-first display (no customer has a company name), creating a user from Schedule
(seat limit), creating a role from the job Team step.
"""
import re

import pytest
from playwright.sync_api import expect

from utils.config import BASE_URL


def _side(page, name):
    page.locator("nav").get_by_role("link", name=name).first.click(timeout=8000)
    page.wait_for_timeout(3000)


def _open_new_job(page):
    page.get_by_role("button", name="Create").first.click()
    page.get_by_text("New Job", exact=True).first.click(timeout=5000)
    page.get_by_text("Core job information").wait_for(timeout=30_000)


# ---------- Schedule ----------

def test_add_shift_defaults_to_today_9am_to_5pm(logged_in_page):
    page = logged_in_page
    _side(page, "Schedule")
    page.get_by_role("button", name="Add Shift", exact=True).click()
    page.get_by_text("Shift Instruction").wait_for(timeout=10_000)
    values = [i.input_value() for i in page.locator("[role=dialog] input").all()]
    starts = [v for v in values if re.search(r"9:00 am", v)]
    ends = [v for v in values if re.search(r"5:00 pm", v)]
    assert starts and ends, f"expected 9:00 am start and 5:00 pm end, got {values}"
    today = __import__("datetime").date.today().strftime("%d/%m/%Y")
    assert starts[0].startswith(today) and ends[0].startswith(today), f"not today ({today}): {starts} {ends}"


def test_add_user_opens_on_schedule_without_leaving(logged_in_page):
    page = logged_in_page
    _side(page, "Schedule")
    page.get_by_role("button", name="Add User", exact=True).click()
    page.get_by_text("Photo and name for this team member.").wait_for(timeout=10_000)
    assert "/app/schedule" in page.url, f"left the Schedule: {page.url}"


def test_schedule_add_user_form_industry_is_optional(logged_in_page):
    page = logged_in_page
    _side(page, "Schedule")
    page.get_by_role("button", name="Add User", exact=True).click()
    page.get_by_text("Photo and name for this team member.").wait_for(timeout=10_000)
    page.get_by_role("button", name="Save").click()  # empty form: only mandatory fields may complain
    page.wait_for_timeout(1500)
    dialog = page.locator("[role=dialog]").last.inner_text()
    assert "Industry" in dialog  # field still exists
    # Industry must not be flagged as required once the form is submitted empty.
    industry_block = page.get_by_text("Industry", exact=True).locator("xpath=ancestor::div[1]").first
    assert not re.search(r"(?i)industry is required|select industry is required", dialog), dialog


# ---------- Customers and jobs ----------

def test_create_job_from_customer_preselects_customer(logged_in_page):
    page = logged_in_page
    _side(page, "Customer")
    page.get_by_text("Amelia Hartley").first.click()
    page.get_by_role("button", name="Create Job").first.click()
    page.get_by_text("Core job information").wait_for(timeout=30_000)
    assert "/app/job/new" in page.url
    expect(page.get_by_role("main")).to_contain_text("Amelia Hartley")
    expect(page.get_by_role("main")).not_to_contain_text("Select Customer")


def test_new_job_site_radius_defaults_to_1km(logged_in_page):
    page = logged_in_page
    _open_new_job(page)
    assert page.get_by_placeholder("Enter Site Radius").input_value() == "1000"


def test_new_job_description_is_optional(logged_in_page):
    page = logged_in_page
    _open_new_job(page)
    label = page.get_by_text("Job Description", exact=True).first
    # Required fields in this app render a separate "*" just before their label (e.g. "* Job Title").
    block = label.locator("xpath=ancestor::div[1]").inner_text()
    assert "*" not in block, f"Job Description still marked required: {block!r}"


@pytest.mark.parametrize("term,expected", [
    ("Amelia", "Amelia Hartley"),                       # name
    ("amelia.hartley.101@yopmail.com", "Amelia Hartley"),  # email
    ("CST-0102", "Amelia Hartley"),                     # customer ID
])
def test_new_job_customer_search(logged_in_page, term, expected):
    page = logged_in_page
    _open_new_job(page)
    picker = page.locator("input[id^='react-select'][id$='-input']").first
    picker.click(force=True)
    picker.press_sequentially(term, delay=40)
    option = page.locator("[role=option]").filter(has_text=expected).first
    option.wait_for(timeout=15_000)


# ---------- Roles ----------

def _role_names(page):
    rows = page.get_by_role("row")
    names = []
    for i in range(1, rows.count()):
        cell = rows.nth(i).get_by_role("cell").first.inner_text().strip()
        if cell:
            names.append(cell)
    return names


def test_roles_sorted_a_to_z_and_name_header_toggles(logged_in_page):
    page = logged_in_page
    page.goto(f"{BASE_URL}/app/role/list", wait_until="domcontentloaded")
    page.get_by_role("columnheader", name=re.compile("Name", re.I)).first.wait_for(timeout=30_000)
    page.wait_for_timeout(2000)
    asc = _role_names(page)
    assert len(asc) >= 2, f"need 2+ roles to check sorting, got {asc}"
    assert asc == sorted(asc, key=str.lower), f"not A to Z: {asc}"
    # Observed 2026-10-05: the first click on "Name" leaves the order unchanged (A to Z); only a
    # second click gives Z to A. Left failing on purpose: the release note says one click switches.
    page.get_by_role("columnheader").first.get_by_text("Name").click()
    page.wait_for_timeout(2000)
    desc = _role_names(page)
    assert desc == sorted(desc, key=str.lower, reverse=True), f"not Z to A after clicking Name: {desc}"


def test_create_menu_has_new_role(logged_in_page):
    """Release note: 'New Role is now in the sidebar's Create menu.' Observed on 2026-10-05: the
    menu only lists Job, Customer, User, Quote, Invoice, Item, CMS, Post, Report."""
    page = logged_in_page
    page.get_by_role("button", name="Create").first.click()
    page.get_by_text("New Job", exact=True).first.wait_for(timeout=8000)
    expect(page.get_by_text("New Role", exact=True)).to_be_visible(timeout=3000)


# ---------- Company name first ----------
# Needs the customer "Priya Venkatesan" / company "Harbourline Electrical Pty Ltd" (CST-0104) and its
# job JOB-0279, quote QTE-0108 and invoice INV-00184, created through the UI on 2026-10-05.
# The tests only read them and skip if they have been deleted.

COMPANY = "Harbourline Electrical Pty Ltd"
CONTACT = "Priya Venkatesan"


def _needs_company_records(page, path, marker):
    page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
    try:
        page.get_by_role("main").get_by_text(marker).first.wait_for(timeout=20_000)
    except Exception:
        pytest.skip(f"{marker} not found: company test records were removed")


def test_company_name_shown_before_contact_in_customer_list(logged_in_page):
    page = logged_in_page
    _needs_company_records(page, "/app/customer/list", COMPANY)
    text = page.get_by_role("main").inner_text()
    assert text.index(COMPANY) < text.index(CONTACT), "contact person shown before the company name"


def test_company_name_shown_before_contact_in_job_list(logged_in_page):
    page = logged_in_page
    _needs_company_records(page, "/app/job/list", COMPANY)
    expect(page.get_by_role("main")).to_contain_text(f"Customer: {COMPANY} · {CONTACT}")


def test_company_name_shown_before_contact_in_quote_list(logged_in_page):
    page = logged_in_page
    _needs_company_records(page, "/app/quote/list", "QTE-0108")
    row = page.get_by_role("row").filter(has_text="QTE-0108")
    assert row.inner_text().index(COMPANY) < row.inner_text().index(CONTACT)


def test_company_name_shown_before_contact_in_invoice_list(logged_in_page):
    page = logged_in_page
    _needs_company_records(page, "/app/invoices/list?tab=invoice", "INV-00184")
    row = page.get_by_role("row").filter(has_text="INV-00184")
    assert row.inner_text().index(COMPANY) < row.inner_text().index(CONTACT)


@pytest.mark.parametrize("term", ["Harbourline", "Priya", "venkatesan.2", "CST-0104"])
def test_new_job_customer_picker_finds_company_customer(logged_in_page, term):
    page = logged_in_page
    _open_new_job(page)
    picker = page.locator("input[id^='react-select'][id$='-input']").first
    picker.click(force=True)
    picker.press_sequentially(term, delay=40)
    option = page.locator("[role=option]").first
    option.wait_for(timeout=15_000)
    assert option.inner_text().split("\n") == [COMPANY, CONTACT], option.inner_text()

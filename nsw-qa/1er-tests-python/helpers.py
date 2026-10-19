import re
from typing import Optional

from playwright.sync_api import Page, Locator, expect

from config import EMAIL, PASSWORD

# Placeholders renamed on the redesigned (staging) Add Job wizard.
EMAIL_PLACEHOLDER = "Enter Customer Email"   # was "customer@email.com"
PHONE_PLACEHOLDER = "Enter Customer Phone"   # was "412345678"


def login(page: Page):
    page.goto("/log-in")
    page.get_by_placeholder(re.compile("email", re.I)).fill(EMAIL)
    page.get_by_placeholder(re.compile("password", re.I)).fill(PASSWORD)
    page.get_by_role("button", name=re.compile(r"log ?in|sign ?in", re.I)).click()
    page.get_by_role("button", name=re.compile("add job", re.I)).wait_for(state="visible", timeout=20_000)


def open_add_job_drawer(page: Page) -> Locator:
    page.goto("/jobs")
    page.get_by_role("button", name=re.compile("add job", re.I)).click()
    dialog = page.get_by_role("dialog")
    dialog.get_by_placeholder("Enter customer name").wait_for(state="visible")
    return dialog


def control_for_label(scope: Locator, label_text: str) -> Locator:
    """
    The form is dynamic - selecting Activity type / Building type / Installer
    inserts extra fields and shifts everything after them, so react-select
    controls can't be targeted by a fixed index. Instead, find the label text
    and walk up to the nearest ancestor that also contains a
    `.select__control`, then click that control.
    """
    # Match the label text exactly first: a substring match on "Brand" also hits
    # the selected value "Brand New Install" in the Original Equipment select.
    exact = scope.get_by_text(re.compile(rf"^\s*{re.escape(label_text)}\s*$", re.I))
    label = exact.first if exact.count() else scope.get_by_text(label_text, exact=False).first
    field_wrapper = label.locator('xpath=ancestor::*[.//*[contains(@class,"select__control")]][1]')
    return field_wrapper.locator(".select__control").first


def select_option(scope: Locator, label_text: str, option_name: str):
    control = control_for_label(scope, label_text)
    control.scroll_into_view_if_needed()
    control.click()
    scope.page.get_by_role("option", name=option_name, exact=True).click()


def field_exists(scope: Locator, label_text: str) -> bool:
    return scope.get_by_text(label_text, exact=False).count() > 0


def pick_address(dialog: Locator, search_term: str):
    """Site address is an async search - types the term and clicks the first suggestion."""
    control = control_for_label(dialog, "Site address")
    control.scroll_into_view_if_needed()
    control.click()
    dialog.page.keyboard.type(search_term)
    dialog.page.wait_for_timeout(1200)
    dialog.page.get_by_role("option").first.click()


def _product_container(dialog: Locator, index: int) -> Locator:
    return dialog.locator(".border-dashed.border-gray-300").nth(index)


def select_option_or_first(scope: Locator, label_text: str, preferred: Optional[str] = None) -> str:
    """Pick `preferred` if the dropdown offers it, else the first option. Never
    press Escape to close a dropdown: on this app Escape also closes the whole
    Add Job drawer."""
    control = control_for_label(scope, label_text)
    control.scroll_into_view_if_needed()
    control.click()
    page = scope.page
    page.get_by_role("option").first.wait_for(state="visible")
    options = page.get_by_role("option").all_text_contents()
    prefs = [preferred] if isinstance(preferred, str) else list(preferred or [])
    choice = next((o for o in prefs if o in options), options[0])
    page.get_by_role("option", name=choice, exact=True).click()
    return choice


def _fill_product_block(container: Locator):
    page = container.page
    # Staging renamed the old 'No existing system (new installation)' option;
    # Heating & Cooling now offers 'Installation of a New Air Conditioner'.
    select_option_or_first(container, "Original equipment",
                           ["Installation of a New Air Conditioner", "Brand New Install"])
    page.wait_for_timeout(500)
    # Brand is only rendered for some Activity type / Original equipment
    # combinations, so only fill it if it's actually there.
    if field_exists(container, "Brand"):
        brand_control = control_for_label(container, "Brand")
        brand_control.scroll_into_view_if_needed()
        brand_control.click()
        page.get_by_role("option").first.click()
        page.wait_for_timeout(500)
    model_control = control_for_label(container, "Model")
    model_control.scroll_into_view_if_needed()
    model_control.click()
    page.get_by_role("option").first.click()
    page.wait_for_timeout(300)


def fill_job_form(dialog: Locator, fields: dict):
    """
    Fills whichever keys are present in `fields`, leaving the rest blank -
    lets negative-path tests omit specific fields on purpose. Order matters:
    Activity type must be chosen before Building type/New system, and
    Installer must be chosen before the Equipment block exists at all.

    Recognised keys (all optional): customerName, email, phone, abnAcn,
    addressSearch, postcode, activityType, buildingType, newSystem,
    leadMethod, ownReference, installationDate, installer,
    fillEquipment (bool, shorthand for productCount=1), productCount (int).
    """
    page = dialog.page

    # Type selections first: on staging, Building type = Small Business swaps the
    # Customer Name/Phone/Email fields for Business Name + Authorised Signatory
    # fields, silently discarding anything typed into the customer fields before.
    if "activityType" in fields:
        select_option(dialog, "Activity type", fields["activityType"])
    if "buildingType" in fields:
        select_option(dialog, "Building type", fields["buildingType"])
    if "newSystem" in fields:
        # Only present when Activity type is 'Hot Water Heat Pump' AND
        # Building type is 'Residential Building'.
        if field_exists(dialog, "New system"):
            select_option(dialog, "New system", fields["newSystem"])

    for key, label in SMALL_BUSINESS_FIELDS.items():
        if key in fields:
            fill_by_label(dialog, label, fields[key], masked=(key == "signatoryPhone"))

    if "customerName" in fields:
        dialog.get_by_placeholder("Enter customer name").fill(fields["customerName"])
    if "email" in fields:
        dialog.get_by_placeholder(EMAIL_PLACEHOLDER).fill(fields["email"])
    if "phone" in fields:
        # Masked phone input (react-phone-input) - .fill() doesn't trigger
        # the mask, so click + type instead.
        phone_field = dialog.get_by_placeholder(PHONE_PLACEHOLDER)
        phone_field.click()
        page.keyboard.type(fields["phone"])
    if "abnAcn" in fields:
        dialog.get_by_placeholder("12345678901").fill(fields["abnAcn"])
    if "addressSearch" in fields:
        pick_address(dialog, fields["addressSearch"])
    if "postcode" in fields:
        dialog.get_by_placeholder("2000").fill(fields["postcode"])
    if "leadMethod" in fields:
        select_option(dialog, "Method of lead generation", fields["leadMethod"])
    if "ownReference" in fields:
        dialog.get_by_placeholder("REF-001").fill(fields["ownReference"])
    if "installationDate" in fields:
        # Masked date input - .fill() doesn't trigger the mask, click + type.
        date_field = dialog.get_by_placeholder("DD-MM-YYYY")
        date_field.click()
        page.keyboard.type(fields["installationDate"])
    if "installer" in fields:
        select_option(dialog, "Installer (company)", fields["installer"])
        # Selecting the installer inserts the "Equipment to be quoted" block,
        # and on staging also a required "Name of Installer Attended Site
        # Inspection" select.
        page.wait_for_timeout(500)
        if field_exists(dialog, "Name of Installer Attended Site Inspection"):
            select_option_or_first(dialog, "Name of Installer Attended Site Inspection")
            page.wait_for_timeout(300)

    product_count: Optional[int] = fields.get("productCount")
    if product_count is None and fields.get("fillEquipment"):
        product_count = 1
    if product_count:
        add_product_btn = dialog.get_by_role("button", name=re.compile("add another product", re.I))
        for _ in range(product_count - 1):
            add_product_btn.click()
            page.wait_for_timeout(400)
        for p in range(product_count):
            _fill_product_block(_product_container(dialog, p))


SMALL_BUSINESS_FIELDS = {
    "businessName": "Business Name",
    "signatoryFirstName": "Authorised Signatory First Name",
    "signatoryLastName": "Authorised Signatory Last Name",
    "signatoryPosition": "Authorised Signatory Position",
    "signatoryPhone": "Authorised Signatory Phone Number",
    "signatoryEmail": "Authorised Signatory Email Address",
}


def fill_by_label(scope: Locator, label_text: str, value: str, masked: bool = False):
    # Required labels render as "*Label", so allow an optional leading asterisk.
    label = scope.get_by_text(re.compile(rf"^\s*\*?\s*{re.escape(label_text)}\s*$", re.I)).first
    field = label.locator("xpath=ancestor::*[.//input][1]").locator("input").first
    field.scroll_into_view_if_needed()
    if masked:
        field.click()
        scope.page.keyboard.type(value)
    else:
        field.fill(value)


def send_button(dialog: Locator) -> Locator:
    return dialog.get_by_role("button", name=re.compile("send engagement letter", re.I))


def submit_job(dialog: Locator):
    send_button(dialog).click()


def field_error(dialog: Locator, message: str) -> Locator:
    """Staging reworded the messages ('Email is required' -> 'Customer Email is
    required', 'Site address' -> 'Site Address'), so match case-insensitively
    with an optional 'Customer ' prefix."""
    core = re.escape(message).replace(r"\ ", " ")
    return dialog.get_by_text(re.compile(rf"^(customer )?{core}$", re.I))


def expect_field_error(dialog: Locator, message: str):
    expect(field_error(dialog, message)).to_be_visible()


def submit_and_report(page: Page, dialog: Locator, label: str) -> dict:
    """
    For exploratory edge cases where the expected outcome isn't known ahead
    of time: submits, waits, then prints whether the job was created or the
    submission was blocked - and dumps the drawer's validation text when
    blocked. Never asserts a specific outcome, so the test documents real
    behaviour instead of guessing at it.
    """
    submit_job(dialog)
    page.wait_for_timeout(2500)
    try:
        # The Send button, not the customer-name field: Small Business forms have no customer-name field.
        still_open = send_button(dialog).is_visible()
    except Exception:
        still_open = False
    if still_open:
        print(f"[{label}] Result: submission BLOCKED. Dialog text:\n{dialog.inner_text()}")
    else:
        print(f"[{label}] Result: job CREATED.")
    return {"created": not still_open}


def expect_job_created(page: Page, dialog: Locator, customer_name, *also_try: str):
    """Asserts the drawer closed and the new job shows up in the All Jobs list,
    under any of the given names (small-business jobs may list under the
    business name or the signatory rather than a customer name)."""
    send_button(dialog).wait_for(state="hidden", timeout=15_000)
    names = [customer_name, *also_try]
    for name in names:
        page.goto("/jobs")
        page.get_by_placeholder(re.compile("search jobs", re.I)).fill(name)
        row = page.locator("table tbody tr").filter(has_text=name).first
        try:
            row.wait_for(state="visible", timeout=8_000)
            return name
        except Exception:
            continue
    raise AssertionError(f"new job not found in the All Jobs list under any of {names}")


def open_job_detail(page: Page, job_number: str):
    """
    Opens a signed job's full detail page (tabs: Job Information / Products /
    Post Install Details / ...) by searching for its job number in the All
    Jobs list and clicking the view icon. Only works for jobs already past
    "Engagement Sent" - unsigned jobs open the Add Job wizard drawer instead.
    """
    page.goto("/jobs")
    page.get_by_placeholder("Search Jobs...").fill(job_number)
    page.wait_for_timeout(1200)
    page.locator("table tbody tr").first.locator("svg, img, button").first.click()
    page.get_by_role("button", name="Job Information", exact=True).wait_for(state="visible", timeout=15_000)


def open_job_detail_tab(page: Page, tab_name: str):
    page.get_by_role("button", name=tab_name, exact=True).click()
    page.wait_for_timeout(1000)

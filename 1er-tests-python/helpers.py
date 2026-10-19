import re
from typing import Optional

from playwright.sync_api import Page, Locator, expect

from config import EMAIL, PASSWORD


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
    label = scope.get_by_text(label_text, exact=False).first
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


_varied_option_counter = 0


def _select_varied_open_option(page: Page):
    """
    Picks a varied option from whatever react-select dropdown is currently
    open, rather than always the first one - so Brand/Model differ across
    jobs/products instead of every test creating identical equipment.
    """
    global _varied_option_counter
    options = page.get_by_role("option")
    count = options.count()
    index = _varied_option_counter % count if count > 0 else 0
    _varied_option_counter += 1
    options.nth(index).click()


def _fill_product_block(container: Locator):
    page = container.page
    select_option(container, "Original equipment", "No existing system (new installation)")
    page.wait_for_timeout(500)
    # Brand is only rendered for some Activity type / Original equipment
    # combinations, so only fill it if it's actually there.
    if field_exists(container, "Brand"):
        brand_control = control_for_label(container, "Brand")
        brand_control.scroll_into_view_if_needed()
        brand_control.click()
        page.wait_for_timeout(300)
        _select_varied_open_option(page)
        page.wait_for_timeout(500)
    model_control = control_for_label(container, "Model")
    model_control.scroll_into_view_if_needed()
    model_control.click()
    page.wait_for_timeout(300)
    _select_varied_open_option(page)
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

    if "customerName" in fields:
        dialog.get_by_placeholder("Enter customer name").fill(fields["customerName"])
    if "email" in fields:
        dialog.get_by_placeholder("customer@email.com").fill(fields["email"])
    if "phone" in fields:
        # Masked phone input (react-phone-input) - .fill() doesn't trigger
        # the mask, so click + type instead.
        phone_field = dialog.get_by_placeholder("412345678")
        phone_field.click()
        page.keyboard.type(fields["phone"])
    if "abnAcn" in fields:
        dialog.get_by_placeholder("12345678901").fill(fields["abnAcn"])
    if "addressSearch" in fields:
        pick_address(dialog, fields["addressSearch"])
    if "postcode" in fields:
        dialog.get_by_placeholder("2000").fill(fields["postcode"])
    if "activityType" in fields:
        select_option(dialog, "Activity type", fields["activityType"])
    if "buildingType" in fields:
        select_option(dialog, "Building type", fields["buildingType"])
    if "newSystem" in fields:
        # Only present when Activity type is 'Hot Water Heat Pump' AND
        # Building type is 'Residential Building'.
        if field_exists(dialog, "New system"):
            select_option(dialog, "New system", fields["newSystem"])
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
        # Selecting the installer inserts the "Equipment to be quoted" block.
        page.wait_for_timeout(500)

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


def submit_job(dialog: Locator):
    dialog.get_by_role("button", name=re.compile("send engagement letter", re.I)).click()


def expect_field_error(dialog: Locator, message: str):
    expect(dialog.get_by_text(message, exact=True)).to_be_visible()


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
        still_open = dialog.get_by_placeholder("Enter customer name").is_visible()
    except Exception:
        still_open = False
    if still_open:
        print(f"[{label}] Result: submission BLOCKED. Dialog text:\n{dialog.inner_text()}")
    else:
        print(f"[{label}] Result: job CREATED.")
    return {"created": not still_open}


def expect_job_created(page: Page, dialog: Locator, customer_name: str):
    """Asserts the drawer closed and the new job shows up in the All Jobs list."""
    dialog.get_by_placeholder("Enter customer name").wait_for(state="hidden", timeout=15_000)
    expect(page.get_by_text(customer_name, exact=False).first).to_be_visible(timeout=15_000)


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

"""
Create one real, valid NSW job on staging with a full mandatory field set, then explore
the job-detail page to find what's needed to progress status toward "Photos Started".

Short per-field timeout so one run surfaces every mismatch instead of stalling on the
first one. Reuses helpers.py where placeholders still match; two placeholders changed
(email, phone) and are filled directly. Uses the yopmail.com convention already
established in tests/test_create_jobs.py - never a real address or contact.
"""
import re
import sys
import time

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
from config import INSTALLER_COMPANY  # noqa: E402
import helpers as h  # noqa: E402

BASE_URL = "https://nswstage.rebatem8.com.au"
RUN_ID = str(int(time.time()))[-6:]  # kept internal-only, never shown in a visible field
CUSTOMER_NAME = "Harrison Doyle"  # real AU name, not a labelled test record
FIELD_TIMEOUT = 8_000


def try_select(dialog, page, label, preferred):
    try:
        control = h.control_for_label(dialog, label)
        control.scroll_into_view_if_needed(timeout=FIELD_TIMEOUT)
        control.click(timeout=FIELD_TIMEOUT)
        page.wait_for_timeout(400)
        opts = page.get_by_role("option").all_text_contents()
        if not opts:
            print(f"  {label}: control opened but NO options rendered")
            page.keyboard.press("Escape")
            return None
        choice = preferred if preferred in opts else opts[0]
        page.get_by_role("option", name=choice, exact=True).click(timeout=FIELD_TIMEOUT)
        print(f"  {label}: options={opts} -> selected {choice!r}")
        return choice
    except Exception as e:
        print(f"  {label}: FAILED ({type(e).__name__}: {str(e)[:150]})")
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        return None


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(base_url=BASE_URL)
    page.set_default_timeout(20_000)  # cold page loads (login, first drawer open) are slower than field-level probes

    h.login(page)
    print("Logged in.")
    page.goto("/jobs")
    page.get_by_role("button", name=re.compile("add job", re.I)).click()
    dialog = page.get_by_role("dialog")
    page.wait_for_timeout(2000)  # staging's drawer needs longer to finish rendering than dev
    print("Add Job drawer open (fixed wait, not a visibility assertion).")

    # yopmail.com kept deliberately (the project's own established safe-email
    # convention, see tests/test_create_jobs.py) so no real inbox is contacted;
    # everything else here is plain, realistic AU data with no "test" labels.
    email_value = "harrison.doyle@yopmail.com"
    phone_value = "412987654"
    try:
        dialog.get_by_placeholder(re.compile("customer email", re.I)).fill(email_value, timeout=FIELD_TIMEOUT)
        print(f"  email: filled {email_value!r}")
    except Exception as e:
        print(f"  email: FAILED ({e})")
    try:
        phone_field = dialog.get_by_placeholder(re.compile("customer phone", re.I))
        phone_field.click(timeout=FIELD_TIMEOUT)
        page.keyboard.type(phone_value)
        print(f"  phone: typed {phone_value!r}")
    except Exception as e:
        print(f"  phone: FAILED ({e})")

    fields = dict(
        customerName=CUSTOMER_NAME,
        abnAcn="33102417032",  # valid AU ABN format/checksum, commonly used as a realistic example number
        addressSearch="1 George Street Sydney",
        postcode="2000",
        installationDate="20-10-2026",
        # ownReference intentionally omitted - it's optional (no red asterisk on
        # the form) and a manufactured reference code is exactly the kind of
        # "test data" look the user asked to avoid.
    )
    for key, val in fields.items():
        try:
            h.fill_job_form(dialog, {key: val})
            print(f"  {key}: filled {val!r}")
        except Exception as e:
            print(f"  {key}: FAILED ({type(e).__name__}: {str(e)[:150]})")

    print("\nSelecting dropdowns:")
    try_select(dialog, page, "Activity type", "Heating & Cooling")
    page.wait_for_timeout(600)
    try_select(dialog, page, "Building type", "Residential Building")
    page.wait_for_timeout(600)
    lead_result = try_select(dialog, page, "Method of lead generation", "Phone")
    page.wait_for_timeout(600)
    installer_result = try_select(dialog, page, "Installer (company)", INSTALLER_COMPANY)
    page.wait_for_timeout(800)

    # Selecting an installer inserts a new mandatory field on staging that
    # didn't exist in the old suite: which installer staff member attended
    # the site inspection. Pick whichever name is offered first.
    try_select(dialog, page, "Name of Installer Attended Site Inspection", None)
    page.wait_for_timeout(600)

    if installer_result:
        # "Original Equipment" options changed on staging - old suite's
        # 'No existing system (new installation)' no longer exists; the
        # closest equivalent for a fresh install is now
        # 'Installation of a New Air Conditioner'.
        try_select(dialog, page, "Original Equipment", "Installation of a New Air Conditioner")
        page.wait_for_timeout(500)
        try_select(dialog, page, "Brand", None)
        page.wait_for_timeout(500)
        try_select(dialog, page, "Model", None)
        page.wait_for_timeout(500)
    else:
        print("  equipment block: SKIPPED (no installer selected, block wouldn't exist)")

    page.wait_for_timeout(500)
    page.screenshot(path="stage-job-before-submit.png", full_page=True)
    print("\nScreenshot before submit saved: stage-job-before-submit.png")
    print("\n--- full dialog text (diagnostic) ---")
    print(dialog.inner_text()[:3000])

    submit_btn = page.get_by_role("button", name=re.compile("send engagement letter", re.I))
    if submit_btn.is_enabled():
        submit_btn.click()
        page.wait_for_timeout(3500)
        page.screenshot(path="stage-job-after-submit.png", full_page=True)
        print("\nClicked Send Engagement Letter & Fact Sheet. Screenshot after: stage-job-after-submit.png")
        print("\n--- page text after submit ---")
        print(page.locator("body").inner_text()[:2000])
    else:
        print("\nSubmit button is DISABLED - not clicking. Something above is still missing/invalid.")

    browser.close()

print("\nDone.")

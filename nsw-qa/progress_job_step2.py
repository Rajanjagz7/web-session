"""
Step 2 of job M8N000078 (Harrison Doyle): assign Electrician + Refrigeration
Mechanic on the "Site Assessment & Nomination" step, then Send - this requests
the Site Assessor Declaration signature from the installer, which (per the UI's
own text) automatically sends the Nomination Form to the customer once signed.
"""
import re
import sys

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

BASE_URL = "https://nswstage.rebatem8.com.au"
JOB_ID = "M8N000078"
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
    page.set_default_timeout(30_000)
    h.login(page)
    print("Logged in.")

    page.goto("/jobs")
    page.get_by_placeholder(re.compile("search jobs", re.I)).fill(JOB_ID)
    page.wait_for_timeout(1500)
    page.locator("table tbody tr").first.locator("svg, img, button").first.click()
    page.wait_for_timeout(2000)
    dialog = page.get_by_role("dialog")
    print("Opened job wizard (should already be on step 2).")

    try_select(dialog, page, "Electrician", None)
    page.wait_for_timeout(500)
    try_select(dialog, page, "Refrigeration Mechanic", None)
    page.wait_for_timeout(500)

    page.screenshot(path="job-step2-before-send.png", full_page=True)
    print("Screenshot before Send saved: job-step2-before-send.png")

    send_btn = dialog.get_by_role("button", name="Send", exact=True)
    if send_btn.is_enabled():
        send_btn.click()
        page.wait_for_timeout(3000)
        page.screenshot(path="job-step2-after-send.png", full_page=True)
        print("Clicked Send. Screenshot after: job-step2-after-send.png")
    else:
        print("Send button DISABLED - something above still missing.")
        print(dialog.inner_text()[:2000])

    page.goto("/jobs")
    page.get_by_placeholder(re.compile("search jobs", re.I)).fill(JOB_ID)
    page.wait_for_timeout(1500)
    print("\nRow after Send:", page.locator("table tbody tr").first.inner_text().replace("\n", " | ")[:250])

    browser.close()

print("\nDone.")

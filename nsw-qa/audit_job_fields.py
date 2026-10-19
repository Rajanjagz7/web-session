"""
Field-by-field audit of the NSW staging Add Job wizard: Step 1 (Engagement &
Products) opened fresh and never submitted (so no extra job is created - empty-
submit is used only to surface validation messages), plus Step 2 (Site Assessment
& Nomination) read from the already-existing job M8N000078.

For each field, records: label, placeholder, required (red asterisk) or not,
input type, and dropdown options where applicable.
"""
import re
import sys

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

BASE_URL = "https://nswstage.rebatem8.com.au"
JOB_ID = "M8N000078"


def dump_fields(scope):
    print("\n--- raw field-by-field text dump ---")
    print(scope.inner_text()[:4000])


def list_dropdown(dialog, page, label):
    try:
        control = h.control_for_label(dialog, label)
        control.scroll_into_view_if_needed(timeout=6000)
        control.click(timeout=6000)
        page.wait_for_timeout(500)
        opts = page.get_by_role("option").all_text_contents()
        page.keyboard.press("Escape")
        print(f"  {label}: {opts}")
        return opts
    except Exception as e:
        print(f"  {label}: could not open ({type(e).__name__}: {str(e)[:100]})")
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        return []


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(base_url=BASE_URL)
    page.set_default_timeout(25_000)
    h.login(page)
    print("Logged in.")

    # ============================== STEP 1: fresh Add Job, never submitted ==============================
    page.goto("/jobs")
    page.get_by_role("button", name=re.compile("add job", re.I)).click()
    dialog = page.get_by_role("dialog")
    page.wait_for_timeout(2000)
    print("\n===== STEP 1: Engagement & Products =====")
    dump_fields(dialog)

    print("\n--- dropdown options ---")
    list_dropdown(dialog, page, "Activity type")
    list_dropdown(dialog, page, "Building type")
    list_dropdown(dialog, page, "Method of lead generation")
    installers = list_dropdown(dialog, page, "Installer (company)")
    page.wait_for_timeout(800)

    submit_btn = dialog.get_by_role("button", name=re.compile("send engagement letter", re.I))
    print(f"\nSubmit button enabled with everything blank: {submit_btn.is_enabled()}")
    if submit_btn.is_enabled():
        submit_btn.click()
        page.wait_for_timeout(1500)
        print("--- validation text after clicking Send on a blank form ---")
        print(dialog.inner_text()[:3000])

    try:
        h.select_option(dialog, "Installer (company)", installers[0] if installers else "")
        page.wait_for_timeout(800)
        print("\n--- Equipment block (after selecting an installer) ---")
        dump_fields(dialog)
        list_dropdown(dialog, page, "Original Equipment")
    except Exception as e:
        print(f"Could not select installer to reveal equipment block: {e}")

    page.screenshot(path="audit-step1.png", full_page=True)
    print("\nScreenshot saved: audit-step1.png")

    try:
        page.get_by_role("button", name=re.compile("^discard$|^back$|close", re.I)).first.click(timeout=3000)
    except Exception:
        page.keyboard.press("Escape")
    page.wait_for_timeout(1000)

    # ============================== STEP 2: existing job M8N000078 ==============================
    page.goto("/jobs")
    page.get_by_placeholder(re.compile("search jobs", re.I)).fill(JOB_ID)
    page.wait_for_timeout(1500)
    page.locator("table tbody tr").first.locator("svg, img, button").first.click()
    page.wait_for_timeout(2000)
    dialog2 = page.get_by_role("dialog")
    print("\n===== STEP 2: Site Assessment & Nomination (job M8N000078) =====")
    dump_fields(dialog2)
    list_dropdown(dialog2, page, "Contractor Group Name")
    page.screenshot(path="audit-step2.png", full_page=True)
    print("\nScreenshot saved: audit-step2.png")

    browser.close()

print("\nDone.")

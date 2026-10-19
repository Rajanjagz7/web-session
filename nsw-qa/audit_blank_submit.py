"""Minimal, safe check: open a fresh Add Job drawer and click Send with everything
blank, to capture the validation messages for every required field. No dropdown
peek-and-Escape (that closes the whole drawer on this app, confirmed in the
previous run) - just the empty-submit check."""
import re
import sys

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

BASE_URL = "https://nswstage.rebatem8.com.au"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(base_url=BASE_URL)
    page.set_default_timeout(25_000)
    h.login(page)
    print("Logged in.")

    page.goto("/jobs")
    page.get_by_role("button", name=re.compile("add job", re.I)).click()
    dialog = page.get_by_role("dialog")
    page.wait_for_timeout(2000)

    submit_btn = dialog.get_by_role("button", name=re.compile("send engagement letter", re.I))
    print("Submit button enabled with everything blank:", submit_btn.is_enabled())
    submit_btn.click()
    page.wait_for_timeout(1500)
    page.screenshot(path="audit-blank-submit.png", full_page=True)
    print("Screenshot saved: audit-blank-submit.png")
    print("\n--- full dialog text after clicking Send on a blank form ---")
    print(dialog.inner_text()[:3000])

    browser.close()

print("\nDone.")

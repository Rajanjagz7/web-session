"""Reopen job M8N000078 now that it's at 'Site Assessment and Nomination Requested'
and report exactly what the wizard/detail page shows - is there an admin-side action
to complete the Site Assessor Declaration signature, or does it require a separate
installer-user login?"""
import re
import sys

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

BASE_URL = "https://nswstage.rebatem8.com.au"
JOB_ID = "M8N000078"

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
    page.screenshot(path="job-step3-state.png", full_page=True)
    print("Screenshot saved: job-step3-state.png")
    print("URL:", page.url)

    print("\n--- buttons on this page ---")
    for b in page.get_by_role("button").all():
        try:
            t = b.inner_text().strip()
            if t:
                print(" -", t)
        except Exception:
            pass

    print("\n--- full page text (first 3000 chars) ---")
    print(page.locator("body").inner_text()[:3000])

    browser.close()

print("\nDone.")

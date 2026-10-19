"""
Explore how to progress job M8N000078 (Harrison Doyle) past "Engagement Sent":
1. Open its detail page in the admin portal and list every tab/action available.
2. Check the yopmail.com inbox for harrison.doyle - the engagement letter should
   have gone there since that's a real, checkable (if disposable) inbox, not a
   dead-end domain. If it contains a nomination-signing link, that's the
   customer-side step needed to reach "Nomination Signed" -> "Photos Started".
Read-only exploration - clicks into tabs/links to see what's there, doesn't submit
anything further without reporting back first.
"""
import re
import sys

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

BASE_URL = "https://nswstage.rebatem8.com.au"
JOB_ID = "M8N000078"
CUSTOMER_NAME = "Harrison Doyle"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    # --- 1. admin portal: job detail page ---
    page = browser.new_page(base_url=BASE_URL)
    page.set_default_timeout(20_000)
    h.login(page)
    print("Logged in to admin portal.")

    page.goto("/jobs")
    page.get_by_placeholder(re.compile("search jobs", re.I)).fill(JOB_ID)
    page.wait_for_timeout(1500)
    row = page.locator("table tbody tr").first
    print("Row found:", row.inner_text().replace("\n", " | ")[:200])

    # click the first icon/button in the row (view/detail action)
    row.locator("svg, img, button").first.click()
    page.wait_for_timeout(2000)
    page.screenshot(path="job-detail.png", full_page=True)
    print("Screenshot saved: job-detail.png")
    print("URL after click:", page.url)

    print("\n--- buttons visible on this page ---")
    for b in page.get_by_role("button").all():
        try:
            t = b.inner_text().strip()
            if t:
                print(" -", t)
        except Exception:
            pass

    print("\n--- links visible on this page ---")
    for a in page.get_by_role("link").all():
        try:
            t = a.inner_text().strip()
            if t:
                print(" -", t)
        except Exception:
            pass

    print("\n--- page body text (first 2500 chars) ---")
    print(page.locator("body").inner_text()[:2500])

    page.close()

    # --- 2. yopmail inbox for the engagement letter ---
    ymp = browser.new_page()
    ymp.set_default_timeout(20_000)
    ymp.goto("https://yopmail.com/inbox?login=harrison.doyle")
    ymp.wait_for_timeout(2500)
    ymp.screenshot(path="yopmail-inbox.png", full_page=True)
    print("\nScreenshot saved: yopmail-inbox.png")
    print("Inbox page text (first 1500 chars):")
    print(ymp.locator("body").inner_text()[:1500])

    browser.close()

print("\nDone.")

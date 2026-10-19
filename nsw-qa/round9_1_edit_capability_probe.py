import sys, re
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
import helpers as h
from playwright.sync_api import sync_playwright

JOB_NUMBER = "M8N000208"
with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    page = b.new_page(base_url="https://nswstage.rebatem8.com.au")
    page.set_default_timeout(20000)
    calls = []
    page.on("request", lambda r: calls.append((r.method, r.url.split("/api/v1")[-1], r.post_data))
            if "/api/v1/" in r.url and r.method != "GET" else None)
    h.login(page)
    page.goto("/jobs")
    page.get_by_placeholder(re.compile("search jobs", re.I)).fill(JOB_NUMBER)
    page.wait_for_timeout(1800)
    page.locator("table tbody tr").first.locator("svg, img, button").first.click()
    page.wait_for_timeout(2000)
    page.get_by_role("button", name="Back", exact=True).click()
    page.wait_for_timeout(1500)
    dialog = page.get_by_role("dialog")

    # fix the customer name (remove the XSS payload) as our first real edit
    dialog.get_by_placeholder("Enter customer name").fill("Nathan Reeves")
    page.wait_for_timeout(300)
    calls.clear()
    dialog.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_timeout(2500)
    page.screenshot(path=r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\dbg-edit-after-save.png", full_page=True)
    print("URL after save:", page.url)
    print("dialog still open:", dialog.count() > 0 and dialog.is_visible() if dialog.count() else False)
    b.close()

print("\nwrite calls during Save:")
for m, u, d in calls:
    print(" ", m, u)
    print("   body:", (d or "")[:1200])

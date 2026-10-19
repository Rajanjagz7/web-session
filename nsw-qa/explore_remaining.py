"""Read-only look at the three remaining failure groups (nothing is submitted):
1. Hot Water Heat Pump: Building type options and the product-block labels.
2. Did the North Sydney small-business job (Mia Robertson) get created at all?
3. Signed job M8N000074: what the Products tab actually shows."""
import re
import sys

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(base_url="https://nswstage.rebatem8.com.au")
    page.set_default_timeout(30_000)
    h.login(page)

    # 1. Hot Water Heat Pump form shape
    dialog = h.open_add_job_drawer(page)
    print("Activity:", h.select_option_or_first(dialog, "Activity type", "Hot Water Heat Pump"))
    page.wait_for_timeout(700)
    ctl = h.control_for_label(dialog, "Building type")
    ctl.click()
    page.get_by_role("option").first.wait_for(state="visible")
    print("HWHP building options:", page.get_by_role("option").all_text_contents())
    page.get_by_role("option").first.click()
    page.wait_for_timeout(700)
    print("New system field present:", h.field_exists(dialog, "New system"))
    h.select_option(dialog, "Installer (company)", "BAWA")
    page.wait_for_timeout(1000)
    if h.field_exists(dialog, "Name of Installer Attended Site Inspection"):
        h.select_option_or_first(dialog, "Name of Installer Attended Site Inspection")
    page.wait_for_timeout(700)
    block = dialog.locator(".border-dashed.border-gray-300").first
    print("Product block count:", dialog.locator(".border-dashed.border-gray-300").count())
    print("HWHP product block text:\n", block.inner_text()[:1200] if block.count() else "(no dashed block found)")
    print("Equipment section text:\n", dialog.inner_text().split("Equipment to Be Quoted")[-1][:1200])

    # 2. North Sydney / other valid-case jobs in the list
    for name in ["Mia Robertson", "Olivia Bennett", "Jack Sullivan", "Noah Fitzgerald", "Ava Thompson", "Lucas Whitfield"]:
        page.goto("/jobs")
        page.get_by_placeholder(re.compile("search jobs", re.I)).fill(name)
        page.wait_for_timeout(1800)
        rows = page.locator("table tbody tr")
        texts = [rows.nth(i).inner_text().replace("\n", " ").replace("\t", " ")[:140] for i in range(min(rows.count(), 3))]
        print(f"\nSearch {name!r}: {rows.count()} row(s)")
        for t in texts:
            print("   ", t)

    # 3. Signed job Products tab
    h.open_job_detail(page, "M8N000074")
    h.open_job_detail_tab(page, "Products")
    print("\nM8N000074 Products tab text:\n", page.locator("main, body").first.inner_text()[:1800])
    print("Buttons:", [b.inner_text().strip() for b in page.get_by_role("button").all() if b.inner_text().strip()][:40])

    browser.close()

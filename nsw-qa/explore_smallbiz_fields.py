"""Read-only (the submit is expected to be rejected, as it was last run):
1. Heating & Cooling + Small Business: which mandatory field is the toast complaining about?
2. Hot Water Heat Pump: Original Equipment / Brand options and what the block looks like after each."""
import sys
import time

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402


def opts_then_pick(page, scope, label):
    ctl = h.control_for_label(scope, label)
    ctl.scroll_into_view_if_needed()
    ctl.click()
    page.get_by_role("option").first.wait_for(state="visible")
    o = page.get_by_role("option").all_text_contents()
    page.get_by_role("option").first.click()
    page.wait_for_timeout(600)
    return o


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(base_url="https://nswstage.rebatem8.com.au")
    page.set_default_timeout(30_000)
    h.login(page)

    # 1. Small business
    dialog = h.open_add_job_drawer(page)
    rid = str(int(time.time() * 1000))[-8:]
    h.fill_job_form(dialog, dict(
        customerName="Mia Robertson", email=f"mia.robertson.{rid}@yopmail.com", phone="4" + rid,
        abnAcn=("0" + rid + "01")[-11:], addressSearch="123 Walker Street North Sydney", postcode="2060",
        activityType="Heating & Cooling", buildingType="Small Business Site (less than 273 kWh/day)",
        leadMethod="Social media", installationDate="01-12-2026", installer="BAWA", fillEquipment=True))
    print("=== Small business form BEFORE submit ===\n", dialog.inner_text()[:3500])
    h.submit_job(dialog)
    page.wait_for_timeout(2500)
    page.screenshot(path="smallbiz-after-submit.png", full_page=True)
    after = page.locator("body").inner_text()
    msgs = sorted({ln.strip() for ln in after.splitlines() if any(k in ln.lower() for k in ("required", "invalid", "must", "error", "not able"))})
    print("\n=== Validation lines after submit ===", msgs)

    # 2. Hot water equipment
    page.goto("/jobs")
    dialog = h.open_add_job_drawer(page)
    h.select_option_or_first(dialog, "Activity type", "Hot Water Heat Pump")
    page.wait_for_timeout(600)
    h.select_option_or_first(dialog, "Building type", "Residential Building")
    h.select_option_or_first(dialog, "New system", "Heat pump")
    h.select_option(dialog, "Installer (company)", "BAWA")
    page.wait_for_timeout(900)
    h.select_option_or_first(dialog, "Name of Installer Attended Site Inspection")
    block = dialog.locator(".border-dashed.border-gray-300").first
    print("\nHWHP Original Equipment options:", opts_then_pick(page, block, "Original equipment"))
    print("HWHP block after Original Equipment:\n", block.inner_text()[:900])
    if h.field_exists(block, "Brand"):
        print("HWHP Brand options (first 10):", opts_then_pick(page, block, "Brand")[:10])
        print("HWHP block after Brand:\n", block.inner_text()[:900])
    browser.close()

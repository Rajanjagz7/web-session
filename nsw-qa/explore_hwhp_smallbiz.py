"""A: Hot Water Heat Pump equipment block (after New system is chosen) - read only.
B: Reproduce the North Sydney small-business valid case (Mia Robertson) and record
   the create-job response + any toast, since the drawer closed but no job appeared.
   B submits one job with the suite's own valid AU data."""
import re
import sys
import time

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(base_url="https://nswstage.rebatem8.com.au")
    page.set_default_timeout(30_000)
    h.login(page)

    # A
    dialog = h.open_add_job_drawer(page)
    h.select_option_or_first(dialog, "Activity type", "Hot Water Heat Pump")
    page.wait_for_timeout(600)
    h.select_option_or_first(dialog, "Building type", "Residential Building")
    page.wait_for_timeout(600)
    ctl = h.control_for_label(dialog, "New system")
    ctl.click()
    page.get_by_role("option").first.wait_for(state="visible")
    print("New system options:", page.get_by_role("option").all_text_contents())
    page.get_by_role("option").first.click()
    page.wait_for_timeout(600)
    h.select_option(dialog, "Installer (company)", "BAWA")
    page.wait_for_timeout(1000)
    if h.field_exists(dialog, "Name of Installer Attended Site Inspection"):
        h.select_option_or_first(dialog, "Name of Installer Attended Site Inspection")
    page.wait_for_timeout(800)
    print("Dashed product blocks:", dialog.locator(".border-dashed.border-gray-300").count())
    print("HWHP equipment section:\n", dialog.inner_text().split("Equipment to Be Quoted")[-1][:1500])

    # B
    page.goto("/jobs")
    events = []
    page.on("response", lambda r: events.append(f"{r.request.method} {r.url.split('/api/v1')[-1][:60]} -> {r.status}")
            if "/api/v1/" in r.url and r.request.method in ("POST", "PUT", "PATCH") else None)
    dialog = h.open_add_job_drawer(page)
    rid = str(int(time.time() * 1000))[-8:]
    h.fill_job_form(dialog, dict(
        customerName="Mia Robertson", email=f"mia.robertson.{rid}@yopmail.com", phone="4" + rid,
        abnAcn=("0" + rid + "01")[-11:], addressSearch="123 Walker Street North Sydney", postcode="2060",
        activityType="Heating & Cooling", buildingType="Small Business Site (less than 273 kWh/day)",
        leadMethod="Social media", installationDate="01-12-2026", installer="BAWA", fillEquipment=True))
    h.submit_job(dialog)
    toast = ""
    for _ in range(12):
        page.wait_for_timeout(500)
        t = page.locator("[role=alert], .Toastify__toast, .toast").all_inner_texts()
        if t:
            toast = " | ".join(t)
            break
    page.wait_for_timeout(2500)
    print("\nWrite calls after submit:", events)
    print("Toast:", toast or "(none)")
    try:
        still_open = dialog.get_by_placeholder("Enter customer name").is_visible()
    except Exception:
        still_open = False
    print("Drawer still open:", still_open)
    if still_open:
        print(dialog.inner_text()[-1500:])
    page.goto("/jobs")
    page.get_by_placeholder(re.compile("search jobs", re.I)).fill("Mia Robertson")
    page.wait_for_timeout(2000)
    print("Search 'Mia Robertson':", page.locator("table tbody tr").first.inner_text().replace("\n", " ")[:160])
    browser.close()

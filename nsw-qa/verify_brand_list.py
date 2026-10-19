"""Is the product Brand dropdown capped at 50? Checks scroll-to-load and type-to-search
for HWHP and H&C, and records the brand API calls. No submit."""
import sys

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

SEARCH = {"Hot Water Heat Pump": ["Stiebel", "Thermann", "Solahart", "Siddons", "Vulcan", "Reclaim"],
          "Heating & Cooling": ["Toshiba", "Samsung", "Mitsubishi", "Panasonic", "Fujitsu", "Daikin"]}

with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    page = b.new_page(base_url="https://nswstage.rebatem8.com.au", viewport={"width": 1440, "height": 900})
    page.set_default_timeout(15_000)
    api = []
    page.on("response", lambda r: api.append(f"{r.status} {r.url.split('/api/v1')[-1][:170]}")
            if "/api/v1/products" in r.url else None)
    h.login(page)
    for activity, terms in SEARCH.items():
        api.clear()
        d = h.open_add_job_drawer(page)
        f = {"activityType": activity, "buildingType": "Residential Building"}
        if activity.startswith("Hot"):
            f["newSystem"] = "Heat pump"
        h.fill_job_form(d, f)
        h.select_option_or_first(d, "Installer (company)", ["Belinda HVAC NSW"])
        page.wait_for_timeout(1500)
        box = d.locator(".border-dashed.border-gray-300").first
        h.select_option_or_first(box, "Original equipment", ["Brand New Install", "Installation of a New Air Conditioner"])
        page.wait_for_timeout(800)
        bc = box.locator(".select__control").filter(has_text="Select Brand").first
        bc.click()
        page.wait_for_timeout(1500)
        first = page.get_by_role("option").all_text_contents()
        menu = page.locator(".select__menu-list").first
        for _ in range(6):
            menu.evaluate("el => el.scrollTop = el.scrollHeight")
            page.wait_for_timeout(1200)
        after = page.get_by_role("option").all_text_contents()
        print(f"\n== {activity}: {len(first)} brands on open, {len(after)} after scrolling to bottom; last = {after[-3:]}")
        dupes = {}
        for o in after:
            dupes.setdefault(o.lower().replace(" ", ""), []).append(o)
        print("   case/space duplicates:", [v for v in dupes.values() if len(v) > 1])
        for t in terms:
            page.keyboard.press("Control+A")
            page.keyboard.type(t)
            page.wait_for_timeout(1500)
            opts = page.get_by_role("option").all_text_contents()
            print(f"   search {t!r}: {opts[:5]}")
        print("   product API calls:", sorted(set(api))[:8])
        page.keyboard.press("Control+A"); page.keyboard.press("Backspace")
        page.goto("/jobs")
    b.close()

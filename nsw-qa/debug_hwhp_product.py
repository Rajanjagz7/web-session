"""Debug: what does the HWHP product block render after each selection? No submit."""
import re
import sys

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    page = b.new_page(base_url="https://nswstage.rebatem8.com.au", viewport={"width": 1440, "height": 900})
    page.set_default_timeout(15_000)
    api = []
    page.on("response", lambda r: api.append(f"{r.status} {r.request.method} {r.url.split('/api/v1')[-1][:140]}")
            if "/api/v1/" in r.url else None)
    h.login(page)
    d = h.open_add_job_drawer(page)
    h.fill_job_form(d, {"activityType": "Hot Water Heat Pump", "buildingType": "Residential Building", "newSystem": "Heat pump"})
    h.select_option_or_first(d, "Installer (company)", ["Belinda HVAC NSW"])
    page.wait_for_timeout(1500)
    box = d.locator(".border-dashed.border-gray-300").first
    print("BLOCK before:", box.inner_text())
    for oe_idx in range(4):
        c = h.control_for_label(box, "Original equipment")
        c.click()
        opts = page.get_by_role("option").all_text_contents()
        print("\nOriginal equipment options:", opts)
        if oe_idx >= len(opts):
            page.keyboard.press("Tab")
            break
        api.clear()
        page.get_by_role("option", name=opts[oe_idx], exact=True).click()
        page.wait_for_timeout(2500)
        print(f"--- after OE={opts[oe_idx]!r}\nBLOCK:", box.inner_text().replace("\n", " | "))
        print("API:", api)
        if h.field_exists(box, "Brand"):
            bc = box.locator(".select__control").filter(has_text="Select Brand").first
            bc.click()
            page.wait_for_timeout(2000)
            bo = page.get_by_role("option").all_text_contents()
            print("Brand options:", len(bo), bo[:8], "| menu text:", page.locator(".select__menu").all_inner_texts()[:1])
            print("API:", api)
            if bo:
                page.get_by_role("option", name=bo[0], exact=True).click()
                page.wait_for_timeout(2000)
                print("after brand BLOCK:", box.inner_text().replace("\n", " | "))
                if h.field_exists(box, "Model"):
                    mc = box.locator(".select__control").filter(has_text="Select Model").first
                    print("model control disabled?", mc.get_attribute("class"))
                    mc.click()
                    page.wait_for_timeout(2000)
                    print("Model options:", page.get_by_role("option").all_text_contents()[:8],
                          "| menu:", page.locator(".select__menu").all_inner_texts()[:1])
                    print("API:", api)
                    mo = page.get_by_role("option").all_text_contents()
                    if mo:
                        page.get_by_role("option", name=mo[0], exact=True).click()
                    else:
                        d.get_by_text("Equipment to Be Quoted").click()
            else:
                d.get_by_text("Equipment to Be Quoted").click()
        page.screenshot(path=f"dbg-hwhp-{oe_idx}.png")
    b.close()

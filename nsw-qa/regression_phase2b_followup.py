"""Follow-up to regression_phase2_ui.py: fixes for NSW-STG-63 (Critical) and NSW-STG-09
which errored on the first run, plus a clean re-run of NSW-STG-43 in an isolated drawer
using ONLY the Testing Company installer (the first run's dialog had picked up Owl HVAC
Services from the NSW-STG-21 check, which is against the test-installer-only rule).
NSW-STG-21 itself is intentionally skipped here - it can only be reproduced by switching
between two different real installer companies, which conflicts with that rule; needs a
manual check or an explicit one-off exception from the user instead of automation.
"""
import json, re, sys, time
sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright
import helpers as h

RID = str(int(time.time()))[-6:]
results = []
TEST_INSTALLER = "Testing Company"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(base_url="https://nswstage.rebatem8.com.au")
    h.login(page)

    # ---------------- NSW-STG-63 (CRITICAL), debug-friendly ----------------
    try:
        page.goto("/jobs")
        page.wait_for_timeout(1000)
        search = page.get_by_placeholder("Search Jobs...")
        search.fill("M8N000285")
        page.wait_for_timeout(1800)
        rows = page.locator("table tbody tr")
        print("rows found for M8N000285:", rows.count())
        rows.first.screenshot(path="regr63-debug-row.png")
        rows.first.locator("svg, img, button").first.click()
        page.wait_for_timeout(2000)
        page.screenshot(path="regr63-debug-after-click.png", full_page=True)
        print("url after click:", page.url)
        page.get_by_role("button", name="Job Information", exact=True).wait_for(state="visible", timeout=15_000)

        requests_seen = []
        def on_request(req):
            if req.method in ("POST", "PUT", "PATCH"):
                requests_seen.append(f"{req.method} {req.url}")
        page.on("request", on_request)

        label = page.get_by_text(re.compile(r"own reference", re.I)).first
        own_ref_field = label.locator("xpath=ancestor::*[.//input][1]").locator("input").first
        new_value = f"REGR-EDIT-{RID}"
        own_ref_field.click()
        own_ref_field.fill(new_value)
        save_btn = page.get_by_role("button", name=re.compile(r"^save$", re.I)).first
        save_btn.click()
        page.wait_for_timeout(3000)

        page.reload()
        page.get_by_role("button", name="Job Information", exact=True).wait_for(state="visible", timeout=15_000)
        page.wait_for_timeout(1000)
        current_text = page.locator("body").inner_text()
        persisted = new_value in current_text
        page.screenshot(path="regr-63-after-save-reload.png", full_page=True)
        verdict = "STILL_OPEN" if not requests_seen and not persisted else "FIXED"
        print(f"NSW-STG-63 {verdict} network requests on Save: {requests_seen}; persisted after reload: {persisted}")
        results.append({"id": "NSW-STG-63", "verdict": verdict,
                         "detail": f"network requests on Save: {requests_seen}; persisted after reload: {persisted}"})
        page.remove_listener("request", on_request)
    except Exception as e:
        print("NSW-STG-63 ERROR", e)
        results.append({"id": "NSW-STG-63", "verdict": "ERROR", "detail": str(e)[:300]})

    # ---------------- NSW-STG-09, retry ----------------
    try:
        page.goto("/jobs")
        dialog = h.open_add_job_drawer(page)
        h.select_option(dialog, "Activity type", "Heating & Cooling")
        h.select_option(dialog, "Building type", "Residential Building")
        dialog.get_by_placeholder("Enter customer name").fill("Regr WipeTest")
        dialog.get_by_placeholder(h.PHONE_PLACEHOLDER).click()
        page.keyboard.type("412000111")
        dialog.get_by_placeholder(h.EMAIL_PLACEHOLDER).fill("regr.wipe@yopmail.com")
        page.wait_for_timeout(500)
        ctl = h.control_for_label(dialog, "Building type")
        ctl.scroll_into_view_if_needed()
        ctl.click()
        page.wait_for_timeout(400)
        opts = page.get_by_role("option").all_text_contents()
        print("Building type options:", opts)
        target = next((o for o in opts if "small business" in o.lower()), opts[-1] if opts else None)
        if target:
            page.get_by_role("option", name=target, exact=True).click()
            page.wait_for_timeout(700)
            name_gone = dialog.get_by_placeholder("Enter customer name").count() == 0
            page.screenshot(path="regr-09-buildingtype-wipe.png", full_page=True)
            verdict = "STILL_OPEN" if name_gone else "FIXED"
            print(f"NSW-STG-09 {verdict} Customer Name field replaced/removed: {name_gone}")
            results.append({"id": "NSW-STG-09", "verdict": verdict,
                             "detail": f"Customer Name field replaced/removed after switching to '{target}': {name_gone}"})
        else:
            print("NSW-STG-09 no Small Business option found:", opts)
            results.append({"id": "NSW-STG-09", "verdict": "ERROR", "detail": f"no matching option found: {opts}"})
    except Exception as e:
        print("NSW-STG-09 ERROR", e)
        results.append({"id": "NSW-STG-09", "verdict": "ERROR", "detail": str(e)[:300]})

    # ---------------- NSW-STG-43, clean re-run (Testing Company only) ----------------
    try:
        page.goto("/jobs")
        dialog2 = h.open_add_job_drawer(page)
        fields = {
            "activityType": "Heating & Cooling", "buildingType": "Residential Building",
            "customerName": f"Regr AddressTest {RID}", "email": f"regr.address.{RID}@yopmail.com",
            "phone": f"4{RID}"[:9], "addressSearch": "10 The Corso Manly",
            "leadMethod": "Customer initiated contact", "ownReference": f"REGR-ADDR-{RID}",
            "installationDate": "01-12-2027", "installer": TEST_INSTALLER, "fillEquipment": True,
        }
        h.fill_job_form(dialog2, fields)
        page.wait_for_timeout(500)
        h.submit_job(dialog2)
        page.wait_for_timeout(3000)
        page.screenshot(path="regr-43-address-submit.png", full_page=True)
        still_open = h.send_button(dialog2).is_visible()
        print("NSW-STG-43 submit result: created" if not still_open else "NSW-STG-43 blocked", still_open)
        results.append({"id": "NSW-STG-43", "verdict": "CREATED" if not still_open else "BLOCKED",
                         "detail": "job submitted with Testing Company + '10 The Corso Manly' address; verify streetName via API next" if not still_open
                         else "submission blocked - dialog text: " + dialog2.inner_text()[:400]})
    except Exception as e:
        print("NSW-STG-43 ERROR", e)
        results.append({"id": "NSW-STG-43", "verdict": "ERROR", "detail": str(e)[:300]})

    browser.close()

with open("regression_phase2b_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=1, ensure_ascii=False)
print("done")

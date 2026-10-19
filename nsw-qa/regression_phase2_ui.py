"""Regression pass (Phase 2: UI-only checks) against the 60 bugs in NSW_BUGS.md/csv,
re-tested on staging 30 Sep 2026. Covers every bug whose original repro needed real
browser interaction (client-side masking/validation, dropdown/drawer behaviour, the
Save button, address autocomplete). Runs headed (visible Chrome), per project convention.

Uses ONLY the "Testing Company" installer (TEST_INSTALLER label below) except for
NSW-STG-21 which specifically needs to switch between two installer companies to
reproduce the stale-dropdown bug - matches the original bug's own repro steps.
"""
import json, re, sys, time
sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright
import helpers as h

RID = str(int(time.time()))[-6:]
results = []
TEST_INSTALLER = "Testing Company"
SIGNED_JOB_NUMBER = "M8N000285"  # confirmed status=site_assessment_requested (past engagement_sent)


def record(bug_id, verdict, detail, screenshot=None):
    row = {"id": bug_id, "verdict": verdict, "detail": detail}
    if screenshot:
        row["screenshot"] = screenshot
    results.append(row)
    print(f"{bug_id:12} {verdict:12} {detail[:160]}")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(base_url="https://nswstage.rebatem8.com.au")
    h.login(page)

    # ================================================================
    # NSW-STG-63 (CRITICAL) - Save fires no request, on a signed job
    # ================================================================
    try:
        h.open_job_detail(page, SIGNED_JOB_NUMBER)

        requests_seen = []
        def on_request(req):
            if req.method in ("POST", "PUT", "PATCH"):
                requests_seen.append(f"{req.method} {req.url}")
        page.on("request", on_request)

        own_ref_field = page.get_by_placeholder(re.compile("REF-001|own reference", re.I)).first
        if own_ref_field.count() == 0:
            # fall back: any text input near "Own Reference" label
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
        record("NSW-STG-63", "STILL_OPEN" if not requests_seen and not persisted else "FIXED",
               f"network requests fired on Save: {requests_seen}; value persisted after reload: {persisted}",
               "regr-63-after-save-reload.png")
        page.remove_listener("request", on_request)
    except Exception as e:
        record("NSW-STG-63", "ERROR", f"script error: {e}")

    # ================================================================
    # Fresh Add Job drawer: sequential non-destructive field checks
    # ================================================================
    page.goto("/jobs")
    dialog = h.open_add_job_drawer(page)
    h.select_option(dialog, "Activity type", "Heating & Cooling")
    h.select_option(dialog, "Building type", "Residential Building")

    # NSW-STG-15: valid ABN typed with spaces
    abn_field = dialog.get_by_placeholder("12345678901")
    abn_field.fill("33 102 417 032")
    page.wait_for_timeout(300)
    abn_val = abn_field.input_value()
    record("NSW-STG-15", "STILL_OPEN" if abn_val != "33102417032" else "FIXED",
           f"ABN typed with spaces '33 102 417 032' -> field now shows {abn_val!r}")

    # NSW-STG-26: valid 9-digit ACN
    abn_field.fill("")
    abn_field.fill("004085616")
    page.wait_for_timeout(300)
    acn_val = abn_field.input_value()
    # trigger blur to surface validation message if any
    dialog.get_by_placeholder("Enter customer name").click()
    page.wait_for_timeout(300)
    acn_error = h.field_error(dialog, "ABN/ACN must be exactly 11 digits").count() > 0
    record("NSW-STG-26", "STILL_OPEN" if acn_error else "FIXED",
           f"9-digit ACN '004085616' -> field value {acn_val!r}, '11 digits' error shown: {acn_error}")
    abn_field.fill("")

    # NSW-STG-29: phone 000000000
    phone_field = dialog.get_by_placeholder(h.PHONE_PLACEHOLDER)
    phone_field.click()
    page.keyboard.type("000000000")
    page.wait_for_timeout(300)
    phone_val = phone_field.input_value()
    record("NSW-STG-29", "STILL_OPEN" if "0" in phone_val and phone_val.strip() else "INCONCLUSIVE",
           f"phone '000000000' -> field shows {phone_val!r}")

    # NSW-STG-20: phone with leading 0, 10 digits
    phone_field.fill("")
    phone_field.click()
    page.keyboard.type("0412247248")
    page.wait_for_timeout(300)
    phone_val20 = phone_field.input_value()
    record("NSW-STG-20", "STILL_OPEN" if phone_val20.lstrip("+61").strip().startswith("0") or len(re.sub(r"\D", "", phone_val20)) == 10 else "FIXED",
           f"phone '0412247248' (leading 0, 10 digits) -> field shows {phone_val20!r}")

    # NSW-STG-22: phone pasted with +61 prefix
    phone_field.fill("")
    phone_field.click()
    page.keyboard.type("+61413247248")
    page.wait_for_timeout(300)
    phone_val22 = phone_field.input_value()
    dialog.get_by_placeholder("Enter customer name").click()
    page.wait_for_timeout(300)
    phone22_error = h.field_error(dialog, "Phone number must be 9 digits for Australia").count() > 0
    record("NSW-STG-22", "STILL_OPEN" if phone22_error else "FIXED",
           f"phone '+61413247248' -> field shows {phone_val22!r}, 9-digit error shown: {phone22_error}")
    phone_field.fill("")

    # NSW-STG-16: invalid email, no TLD
    email_field = dialog.get_by_placeholder(h.EMAIL_PLACEHOLDER)
    email_field.fill(f"regr.notld.{RID}@yopmail")
    dialog.get_by_placeholder("Enter customer name").click()
    page.wait_for_timeout(300)
    email_inline_error = h.field_error(dialog, "Enter a valid email").count() > 0 or \
                          dialog.get_by_text(re.compile(r"enter.*valid.*email", re.I)).count() > 0
    record("NSW-STG-16", "STILL_OPEN" if not email_inline_error else "FIXED",
           f"email 'regr.notld.{RID}@yopmail' (no TLD) -> inline validation shown: {email_inline_error}")
    email_field.fill("")

    # NSW-STG-27: postcode not NSW-validated
    postcode_field = dialog.get_by_placeholder("2000")
    for pc in ["3000"]:
        postcode_field.fill(pc)
        dialog.get_by_placeholder("Enter customer name").click()
        page.wait_for_timeout(300)
        pc_error = dialog.get_by_text(re.compile(r"nsw postcode|invalid postcode", re.I)).count() > 0
        record("NSW-STG-27", "STILL_OPEN" if not pc_error else "FIXED",
               f"postcode '{pc}' (VIC) -> NSW-range error shown: {pc_error}")
    postcode_field.fill("2000")

    # NSW-STG-28: installation date, impossible calendar date
    date_field = dialog.get_by_placeholder("DD-MM-YYYY")
    date_field.click()
    page.keyboard.type("31-04-2027")
    dialog.get_by_placeholder("Enter customer name").click()
    page.wait_for_timeout(300)
    date_val = date_field.input_value()
    date_error = dialog.get_by_text(re.compile(r"invalid date|not a valid date", re.I)).count() > 0
    record("NSW-STG-28", "STILL_OPEN" if not date_error else "FIXED",
           f"date '31-04-2027' (no such day) -> field shows {date_val!r}, error shown: {date_error}")
    date_field.fill("")

    # NSW-STG-30 / 31: free-text length limits
    own_ref = dialog.get_by_placeholder("REF-001")
    long_text = "A" * 258
    own_ref.fill(long_text)
    page.wait_for_timeout(200)
    own_ref_val = own_ref.input_value()
    record("NSW-STG-30 / NSW-STG-31", "STILL_OPEN" if len(own_ref_val) >= 258 else "FIXED_OR_TRUNCATED_SILENTLY" if 0 < len(own_ref_val) < 258 else "CHANGED",
           f"Own Reference 258 'A's -> field now holds {len(own_ref_val)} chars")
    own_ref.fill("")

    page.screenshot(path="regr-drawer-field-checks.png", full_page=True)

    # NSW-STG-47: 'Model is required' shown prematurely
    try:
        h.select_option(dialog, "Installer (company)", TEST_INSTALLER)
        page.wait_for_timeout(700)
        if h.field_exists(dialog, "Name of Installer Attended Site Inspection"):
            h.select_option_or_first(dialog, "Name of Installer Attended Site Inspection")
            page.wait_for_timeout(300)
        h.select_option_or_first(dialog, "Original equipment", ["Installation of a New Air Conditioner", "Brand New Install"])
        page.wait_for_timeout(500)
        if h.field_exists(dialog, "Brand"):
            brand_ctl = h.control_for_label(dialog, "Brand")
            brand_ctl.scroll_into_view_if_needed()
            brand_ctl.click()
            page.get_by_role("option").first.click()
            page.wait_for_timeout(600)
            model_required_shown = dialog.get_by_text(re.compile(r"model is required", re.I)).count() > 0
            record("NSW-STG-47", "STILL_OPEN" if model_required_shown else "FIXED",
                   f"'Model is required' visible right after picking Brand (before touching Model): {model_required_shown}")
        else:
            record("NSW-STG-47", "INCONCLUSIVE", "Brand field not present for this equipment combination")
    except Exception as e:
        record("NSW-STG-47", "ERROR", f"script error: {e}")

    # NSW-STG-35: capacity field strips ',' and 'e'
    # NSW-STG-36: heating capacity no upper limit
    # NSW-STG-37: warranty period no validation
    try:
        model_ctl = h.control_for_label(dialog, "Model")
        model_ctl.scroll_into_view_if_needed()
        model_ctl.click()
        page.get_by_role("option").first.click()
        page.wait_for_timeout(500)

        cooling_field = dialog.get_by_text(re.compile(r"cooling capacity", re.I)).first \
            .locator("xpath=ancestor::*[.//input][1]").locator("input").first
        cooling_field.fill("")
        cooling_field.fill("5,5")
        page.wait_for_timeout(300)
        cooling_val = cooling_field.input_value()
        record("NSW-STG-35", "STILL_OPEN" if cooling_val in ("55", "5.5") and cooling_val != "" else "INCONCLUSIVE",
               f"Cooling Capacity typed '5,5' -> field now shows {cooling_val!r} (bug: silently becomes 55)")

        heating_field = dialog.get_by_text(re.compile(r"heating capacity", re.I)).first \
            .locator("xpath=ancestor::*[.//input][1]").locator("input").first
        heating_field.fill("")
        heating_field.fill("65.01")
        dialog.get_by_placeholder("Enter customer name").click()
        page.wait_for_timeout(300)
        heating_error = dialog.get_by_text(re.compile(r"must be under 65", re.I)).count() > 0
        record("NSW-STG-36", "STILL_OPEN" if not heating_error else "FIXED",
               f"Heating Capacity '65.01' kW -> 'must be under 65kW' error shown: {heating_error}")

        if h.field_exists(dialog, "Warranty"):
            warranty_field = dialog.get_by_text(re.compile(r"warranty period", re.I)).first \
                .locator("xpath=ancestor::*[.//input][1]").locator("input").first
            warranty_field.fill("")
            warranty_field.fill("9999")
            dialog.get_by_placeholder("Enter customer name").click()
            page.wait_for_timeout(300)
            warranty_val = warranty_field.input_value()
            record("NSW-STG-37", "STILL_OPEN" if warranty_val == "9999" else "FIXED",
                   f"Warranty Period '9999' -> field shows {warranty_val!r}")
        else:
            record("NSW-STG-37", "INCONCLUSIVE", "Warranty Period field not present for this product")
    except Exception as e:
        record("NSW-STG-35 / 36 / 37", "ERROR", f"script error in product-field checks: {e}")

    page.screenshot(path="regr-drawer-product-checks.png", full_page=True)

    # ================================================================
    # NSW-STG-21: stale site-inspection installer list after changing Installer
    # (needs a FRESH drawer since the current one already has an installer/product set)
    # ================================================================
    try:
        page.goto("/jobs")
        dialog2 = h.open_add_job_drawer(page)
        h.select_option(dialog2, "Activity type", "Heating & Cooling")
        h.select_option(dialog2, "Building type", "Residential Building")
        h.select_option(dialog2, "Installer (company)", "BAWA")
        page.wait_for_timeout(700)
        first_choice = None
        if h.field_exists(dialog2, "Name of Installer Attended Site Inspection"):
            first_choice = h.select_option_or_first(dialog2, "Name of Installer Attended Site Inspection")
            page.wait_for_timeout(300)
        h.select_option(dialog2, "Installer (company)", "Owl HVAC Services")
        page.wait_for_timeout(700)
        insp_control = h.control_for_label(dialog2, "Name of Installer Attended Site Inspection")
        insp_control.scroll_into_view_if_needed()
        insp_control.click()
        page.wait_for_timeout(400)
        options_after = page.get_by_role("option").all_text_contents()
        page.keyboard.press("Escape") if False else None  # never press Escape (NSW-STG-08); click elsewhere instead
        stale = first_choice is not None and options_after == [first_choice]
        page.screenshot(path="regr-21-installer-switch.png", full_page=True)
        record("NSW-STG-21", "STILL_OPEN" if stale else "FIXED_OR_NO_REPRO",
               f"after switching BAWA -> Owl HVAC, inspection-installer options: {options_after} (was: {first_choice!r})",
               "regr-21-installer-switch.png")
        dialog2.get_by_placeholder("Enter customer name").click()
    except Exception as e:
        record("NSW-STG-21", "ERROR", f"script error: {e}")

    # ================================================================
    # NSW-STG-43: address autocomplete parsing for "The Corso"
    # ================================================================
    try:
        h.fill_job_form(dialog2, {
            "customerName": f"Regr AddressTest {RID}", "email": f"regr.address.{RID}@yopmail.com",
            "phone": f"4{RID}"[:9], "addressSearch": "10 The Corso Manly",
            "leadMethod": "Customer initiated contact", "ownReference": f"REGR-ADDR-{RID}",
            "installationDate": "01-12-2027",
        })
        page.wait_for_timeout(500)
        h.submit_job(dialog2)
        page.wait_for_timeout(3000)
        page.screenshot(path="regr-43-address-submit.png", full_page=True)
        still_open = h.send_button(dialog2).is_visible()
        record("NSW-STG-43", "NEEDS_API_VERIFY" if not still_open else "BLOCKED_COULD_NOT_TEST",
               f"'10 The Corso Manly' job submission -> {'created' if not still_open else 'blocked'} (verify streetName via API next)",
               "regr-43-address-submit.png")
    except Exception as e:
        record("NSW-STG-43", "ERROR", f"script error: {e}")

    # ================================================================
    # NSW-STG-09: Building Type -> Small Business wipes customer fields (fresh, destructive)
    # ================================================================
    try:
        page.goto("/jobs")
        dialog3 = h.open_add_job_drawer(page)
        h.select_option(dialog3, "Activity type", "Heating & Cooling")
        h.select_option(dialog3, "Building type", "Residential Building")
        dialog3.get_by_placeholder("Enter customer name").fill("Regr WipeTest")
        dialog3.get_by_placeholder(h.PHONE_PLACEHOLDER).click()
        page.keyboard.type("412000111")
        dialog3.get_by_placeholder(h.EMAIL_PLACEHOLDER).fill("regr.wipe@yopmail.com")
        page.wait_for_timeout(300)
        h.select_option(dialog3, "Building type", "Small Business Site")
        page.wait_for_timeout(500)
        name_gone = dialog3.get_by_placeholder("Enter customer name").count() == 0
        page.screenshot(path="regr-09-buildingtype-wipe.png", full_page=True)
        record("NSW-STG-09", "STILL_OPEN" if name_gone else "FIXED",
               f"Customer Name field replaced/removed after switching to Small Business: {name_gone}",
               "regr-09-buildingtype-wipe.png")
    except Exception as e:
        record("NSW-STG-09", "ERROR", f"script error: {e}")

    # ================================================================
    # NSW-STG-08: Esc in a dropdown closes the whole drawer (fresh, destructive)
    # ================================================================
    try:
        page.goto("/jobs")
        dialog4 = h.open_add_job_drawer(page)
        dialog4.get_by_placeholder("Enter customer name").fill("Regr EscTest")
        ctl = h.control_for_label(dialog4, "Activity type")
        ctl.scroll_into_view_if_needed()
        ctl.click()
        page.get_by_role("option").first.wait_for(state="visible")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        drawer_gone = dialog4.count() == 0 or not dialog4.is_visible()
        page.screenshot(path="regr-08-esc-drawer.png", full_page=True)
        record("NSW-STG-08", "STILL_OPEN" if drawer_gone else "FIXED",
               f"Esc pressed while Activity type dropdown open -> whole drawer closed: {drawer_gone}",
               "regr-08-esc-drawer.png")
    except Exception as e:
        record("NSW-STG-08", "ERROR", f"script error: {e}")

    # ================================================================
    # NSW-STG-23: no unsaved-changes warning on reload (fresh, uses native dialog listener)
    # ================================================================
    try:
        native_dialog_seen = []
        page.on("dialog", lambda d: (native_dialog_seen.append(d.message), d.dismiss()))
        page.goto("/jobs")
        dialog5 = h.open_add_job_drawer(page)
        dialog5.get_by_placeholder("Enter customer name").fill("Regr ReloadTest")
        page.wait_for_timeout(300)
        page.reload()
        page.wait_for_timeout(1500)
        record("NSW-STG-23", "STILL_OPEN" if not native_dialog_seen else "FIXED",
               f"reload after typing a name -> native confirm dialog shown: {bool(native_dialog_seen)} ({native_dialog_seen})")
    except Exception as e:
        record("NSW-STG-23", "ERROR", f"script error: {e}")

    browser.close()

with open("regression_phase2_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=1, ensure_ascii=False)

print("\n\n=== SUMMARY ===")
from collections import Counter
counts = Counter(r["verdict"] for r in results)
for k, v in counts.items():
    print(f"{k}: {v}")

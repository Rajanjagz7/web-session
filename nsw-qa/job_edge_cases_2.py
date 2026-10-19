"""
Round 2 of job-module edge cases (UI, report-only). Covers field formats not tried yet
plus STATE/INTERACTION scenarios: changing a parent field after dependent fields are
filled, and leaving the form with unsaved data. Jobs are only created where the app
accepts the input; names are realistic AU names, emails @yopmail.com.
Output: job_edge_2.txt (UTF-8) + edge2-*.png screenshots.
"""
import json
import re
import sys
import time

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

RID = str(int(time.time()))[-6:]
out = open("job_edge_2.txt", "w", encoding="utf-8")


def log(obj):
    print(json.dumps(obj, ensure_ascii=False) if isinstance(obj, dict) else obj, file=out, flush=True)


def base(name, i, **over):
    first = re.sub(r"[^a-z]", "", name.split(" ")[0].lower())
    d = dict(activityType="Heating & Cooling", buildingType="Residential Building",
             customerName=name, email=f"{first}.{RID}{i}@yopmail.com", phone=f"4{RID}{i:02d}"[:9],
             addressSearch="1 George Street Sydney", postcode="2000", leadMethod="Customer initiated contact",
             installationDate="15-12-2026", installer="BAWA", fillEquipment=True)
    d.update(over)
    return d


def input_value(scope, label):
    lab = scope.get_by_text(re.compile(rf"^\s*{re.escape(label)}\s*$", re.I)).first
    return lab.locator("xpath=ancestor::*[.//input][1]").locator("input").first.input_value()


def control_text(scope, label):
    return h.control_for_label(scope, label).inner_text().strip()


def submit_and_record(page, dialog, cid, what, name, extra=None):
    h.submit_job(dialog)
    page.wait_for_timeout(3000)
    try:
        still_open = h.send_button(dialog).is_visible()
    except Exception:
        still_open = False
    rec = dict(id=cid, case=what, name=name, **(extra or {}))
    if still_open:
        text = page.locator("body").inner_text()
        rec["result"] = "BLOCKED"
        rec["errors"] = sorted({l.strip() for l in text.splitlines() if len(l) < 120 and re.search(
            r"required|invalid|valid|must|digit|not able|error|failed|greater|less|number", l, re.I)})
        page.screenshot(path=f"edge2-{cid}.png", full_page=True)
    else:
        page.goto("/jobs")
        page.get_by_placeholder(re.compile("search jobs", re.I)).fill(name)
        page.wait_for_timeout(4500)
        rows = page.locator("table tbody tr")
        rec["result"] = "CREATED"
        rec["list_row"] = re.sub(r"\s+", " ", rows.first.inner_text())[:230] if rows.count() else ""
    log(rec)


def new_form(page, fields):
    page.goto("/jobs")
    dialog = h.open_add_job_drawer(page)
    h.fill_job_form(dialog, fields)
    return dialog


def product_block(dialog):
    return dialog.locator(".border-dashed.border-gray-300").first


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(base_url="https://nswstage.rebatem8.com.au")
    page.set_default_timeout(30_000)
    h.login(page)

    # ---------- field-format submissions ----------
    fmt_cases = [
        ("F01", "Phone typed with leading 0 (0412...)", "Ruby Sinclair", {"phone": "0412" + RID[:6]}),
        ("F02", "Phone typed with +61 prefix", "Jasper Moore", {"phone": "+61413" + RID}),
        ("F03", "Installation date 31-04-2027 (April has 30 days)", "Evie Lawson", {"installationDate": "31-04-2027"}),
        ("F04", "Installation date 01-01-2099 (far future)", "Archie Knox", {"installationDate": "01-01-2099"}),
    ]
    for i, (cid, what, name, over) in enumerate(fmt_cases, start=1):
        try:
            dialog = new_form(page, base(name, i, **over))
            submit_and_record(page, dialog, cid, what, name, {"typed": list(over.values())[0]})
        except Exception as e:
            log(dict(id=cid, case=what, result="SCRIPT-ERROR", detail=f"{type(e).__name__}: {str(e)[:200]}"))

    # ---------- product numeric fields ----------
    num_cases = [
        ("F05", "Heating Capacity negative (-5)", "Hugo Barrett", {"Heating Capacity (kW)": "-5"}),
        ("F06", "Cooling Capacity non-numeric (abc)", "Ivy Holloway", {"Cooling Capacity (kW)": "abc"}),
        ("F07", "Heating Capacity 0 and Cooling 99999", "Oscar Delaney", {"Heating Capacity (kW)": "0", "Cooling Capacity (kW)": "99999"}),
        ("F08", "Warranty Period negative (-1)", "Poppy Marsh", {"Warranty Period": "-1"}),
    ]
    for i, (cid, what, name, vals) in enumerate(num_cases, start=10):
        try:
            dialog = new_form(page, base(name, i))
            blk = product_block(dialog)
            stored = {}
            for label, val in vals.items():
                try:
                    h.fill_by_label(blk, label, val)
                except Exception as fe:
                    stored[label + " (fill error)"] = f"{type(fe).__name__}"
                stored[label] = input_value(blk, label)
            submit_and_record(page, dialog, cid, what, name, {"field_value_after_typing": stored})
        except Exception as e:
            log(dict(id=cid, case=what, result="SCRIPT-ERROR", detail=f"{type(e).__name__}: {str(e)[:200]}"))

    # ---------- state / interaction (no submit) ----------
    try:
        dialog = new_form(page, base("Stella Hughes", 20, fillEquipment=False))
        insp_before = control_text(dialog, "Name of Installer Attended Site Inspection")
        h.select_option(dialog, "Installer (company)", "Owl HVAC Services")
        page.wait_for_timeout(1200)
        insp_after = control_text(dialog, "Name of Installer Attended Site Inspection") if h.field_exists(
            dialog, "Name of Installer Attended Site Inspection") else "(field gone)"
        ctl = h.control_for_label(dialog, "Name of Installer Attended Site Inspection")
        ctl.click()
        page.wait_for_timeout(800)
        opts = page.get_by_role("option").all_text_contents()
        log(dict(id="F09", case="Change Installer (BAWA -> Owl HVAC Services) after choosing site-inspection installer",
                 inspector_before=insp_before, inspector_after=insp_after, inspector_options_now=opts,
                 bug_if="inspector_after still shows a BAWA person"))
        page.screenshot(path="edge2-F09.png", full_page=True)
    except Exception as e:
        log(dict(id="F09", result="SCRIPT-ERROR", detail=f"{type(e).__name__}: {str(e)[:200]}"))

    try:
        dialog = new_form(page, base("Leo Harrington", 21))
        blk = product_block(dialog)
        before = dict(model=control_text(blk, "Model"), heat=input_value(blk, "Heating Capacity (kW)"),
                      cool=input_value(blk, "Cooling Capacity (kW)"))
        ctl = h.control_for_label(blk, "Model")
        ctl.click()
        page.get_by_role("option").nth(1).wait_for(state="visible")
        page.get_by_role("option").nth(1).click()
        page.wait_for_timeout(1000)
        after = dict(model=control_text(blk, "Model"), heat=input_value(blk, "Heating Capacity (kW)"),
                     cool=input_value(blk, "Cooling Capacity (kW)"))
        log(dict(id="F10", case="Change Model after capacities auto-filled", before=before, after=after,
                 bug_if="capacities unchanged while the model changed"))
    except Exception as e:
        log(dict(id="F10", result="SCRIPT-ERROR", detail=f"{type(e).__name__}: {str(e)[:200]}"))

    try:
        dialog = new_form(page, base("Zara Fletcher", 22))
        blk_before = product_block(dialog).inner_text()[:300]
        h.select_option(dialog, "Activity type", "Hot Water Heat Pump")
        page.wait_for_timeout(1200)
        blk_after = product_block(dialog).inner_text()[:300] if product_block(dialog).count() else "(no product block)"
        log(dict(id="F11", case="Switch Activity Type (H&C -> Hot Water) after products filled",
                 product_block_before=blk_before, product_block_after=blk_after,
                 bug_if="air-conditioner brand/model still selected under Hot Water Heat Pump"))
        page.screenshot(path="edge2-F11.png", full_page=True)
    except Exception as e:
        log(dict(id="F11", result="SCRIPT-ERROR", detail=f"{type(e).__name__}: {str(e)[:200]}"))

    try:
        dialogs = []
        page.on("dialog", lambda d: (dialogs.append(f"{d.type}: {d.message}"), d.dismiss()))
        page.goto("/jobs")
        dialog = h.open_add_job_drawer(page)
        dialog.get_by_placeholder("Enter customer name").fill("Mason Kerr")
        page.reload()
        page.wait_for_timeout(1500)
        log(dict(id="F12", case="Reload page with unsaved Add Job data", browser_dialogs=dialogs,
                 bug_if="no warning and the data is gone"))
    except Exception as e:
        log(dict(id="F12", result="SCRIPT-ERROR", detail=f"{type(e).__name__}: {str(e)[:200]}"))

    try:
        page.goto("/jobs")
        dialog = h.open_add_job_drawer(page)
        dialog.get_by_placeholder("Enter customer name").fill("Mason Kerr")
        page.get_by_text("Add Job", exact=True).first.locator(
            "xpath=ancestor::*[.//button][1]").locator("button").last.click()
        page.wait_for_timeout(1200)
        body = page.locator("body").inner_text()
        confirm = [l for l in body.splitlines() if re.search(r"discard|unsaved|are you sure|lose", l, re.I)]
        page.screenshot(path="edge2-F13.png", full_page=True)
        log(dict(id="F13", case="Close Add Job drawer (X) with data entered", confirmation_text=confirm,
                 drawer_still_open=h.send_button(page.get_by_role("dialog")).is_visible()))
    except Exception as e:
        log(dict(id="F13", result="SCRIPT-ERROR", detail=f"{type(e).__name__}: {str(e)[:200]}"))

    browser.close()
out.close()
print("done")

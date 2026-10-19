"""
Round 6 - happy-path jobs with proper, realistic data, then data-integrity check.

For each case: fill Add Job with valid data (checksum-valid ABN, 9-digit mobile,
real NSW address, future date, varied installer and product Brand/Model), send,
then read the job back from the API and check each entered value was stored
unchanged. Logs every write request + response and every 4xx/5xx/console error.

Headed Chrome (visible). Emails are @yopmail.com, never a real inbox.
Output: proper_data_round6.json + pd6-<n>-*.png
"""
import json
import random
import re
import sys
import time

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

BASE_URL = "https://nswstage.rebatem8.com.au"
rnd = random.Random()


def valid_abn() -> str:
    w = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    while True:
        d = [rnd.randint(1, 9)] + [rnd.randint(0, 9) for _ in range(10)]
        if sum((x - (1 if i == 0 else 0)) * w[i] for i, x in enumerate(d)) % 89 == 0:
            return "".join(map(str, d))


def mobile() -> str:
    return "4" + "".join(str(rnd.randint(0, 9)) for _ in range(8))


CASES = [
    dict(label="H&C / Residential / Wentworthville", customerName="Priya Raman",
         addressSearch="14 Station Street Wentworthville", postcode="2145",
         activityType="Heating & Cooling", buildingType="Residential Building",
         leadMethod="Customer initiated contact", ownReference="Q-26-0412", installationDate="14-10-2026",
         installerIdx=0, products=1),
    dict(label="HWHP / Residential / Parramatta", customerName="Thomas Nguyen",
         addressSearch="21 Macquarie Street Parramatta", postcode="2150",
         activityType="Hot Water Heat Pump", buildingType="Residential Building", newSystem="Heat pump",
         leadMethod="Online advertisement", ownReference="Q-26-0413", installationDate="21-10-2026",
         installerIdx=1, products=1),
    dict(label="H&C / Small Business / Manly", businessName="Harbourside Cafe Pty Ltd",
         signatoryFirstName="Daniel", signatoryLastName="Kowalski", signatoryPosition="Owner",
         addressSearch="10 The Corso Manly", postcode="2095",
         activityType="Heating & Cooling", buildingType="Small Business Site (less than 273 kWh/day)",
         leadMethod="Social media", ownReference="Q-26-0414", installationDate="28-10-2026",
         installerIdx=2, products=1),
    dict(label="HWHP / Small Business / Hornsby", businessName="Blue Gum Veterinary Clinic Pty Ltd",
         signatoryFirstName="Sarah", signatoryLastName="O'Connor", signatoryPosition="Practice Manager",
         addressSearch="5 Hunter Street Hornsby", postcode="2077",
         activityType="Hot Water Heat Pump", buildingType="Small Business Site",
         leadMethod="Email campaign", ownReference="Q-26-0415", installationDate="04-11-2026",
         installerIdx=3, products=1),
    dict(label="H&C / Residential / 2 products / Newcastle", customerName="Liam O'Brien",
         addressSearch="45 Hunter Street Newcastle", postcode="2300",
         activityType="Heating & Cooling", buildingType="Residential Building",
         leadMethod="Customer initiated contact", ownReference="Q-26-0416", installationDate="11-11-2026",
         installerIdx=4, products=2),
    dict(label="HWHP / Residential / Wollongong", customerName="Aisha Khan",
         addressSearch="100 Crown Street Wollongong", postcode="2500",
         activityType="Hot Water Heat Pump", buildingType="Residential Building", newSystem="Heat pump",
         leadMethod="Social media", ownReference="Q-26-0417", installationDate="18-11-2026",
         installerIdx=5, products=1),
]


def options_for(dialog, label):
    c = h.control_for_label(dialog, label)
    c.scroll_into_view_if_needed()
    c.click()
    page = dialog.page
    page.get_by_role("option").first.wait_for(state="visible", timeout=10_000)
    return c, page.get_by_role("option").all_text_contents()


def pick_idx(dialog, label, idx):
    _, opts = options_for(dialog, label)
    choice = opts[idx % len(opts)]
    dialog.page.get_by_role("option", name=choice, exact=True).click()
    return choice, opts


def fill_products(dialog, n):
    page = dialog.page
    btn = dialog.get_by_role("button", name=re.compile("add another product", re.I))
    for _ in range(n - 1):
        btn.click()
        page.wait_for_timeout(400)
    out = []
    for i in range(n):
        box = dialog.locator(".border-dashed.border-gray-300").nth(i)
        rec = {}
        rec["originalEquipment"] = h.select_option_or_first(
            box, "Original equipment", ["Installation of a New Air Conditioner", "Brand New Install"])
        # HWHP renders Brand a moment after Original Equipment is chosen.
        try:
            box.get_by_text(re.compile(r"^\s*\*?\s*Brand\s*$")).first.wait_for(state="visible", timeout=4000)
        except Exception:
            pass
        # Label-based lookup hits the Original Equipment control on HWHP; use placeholders.
        brand_ctl = box.locator(".select__control").filter(has_text="Select Brand")
        if brand_ctl.count():
            brand_ctl.first.click()
            page.get_by_role("option").first.wait_for(state="visible", timeout=10_000)
            rec["brand"] = rnd.choice(page.get_by_role("option").all_text_contents())
            page.get_by_role("option", name=rec["brand"], exact=True).click()
            page.wait_for_timeout(1500)
        box.locator(".select__control").filter(has_text="Select Model").first.click()
        page.get_by_role("option").first.wait_for(state="visible", timeout=10_000)
        opts = page.get_by_role("option").all_text_contents()
        rec["model"] = rnd.choice(opts)
        page.get_by_role("option", name=rec["model"], exact=True).click()
        page.wait_for_timeout(600)
        rec["block_text"] = box.inner_text()[:600]
        rec["inputs"] = {el.get_attribute("placeholder") or el.get_attribute("name") or "?": el.input_value()
                         for el in box.locator("input:visible").all()}
        out.append(rec)
    return out


def flat(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from flat(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from flat(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj


def norm(v):
    return re.sub(r"[\s\-()+]", "", str(v)).lower()


def locate(job, value):
    """Where in the stored job does `value` appear (normalised, exact then contains)."""
    n = norm(value)
    items = list(flat(job))
    exact = [k for k, v in items if v is not None and norm(v) == n]
    if exact:
        return "exact", exact
    part = [(k, v) for k, v in items if v is not None and n and n in norm(v)]
    return ("contained", [f"{k}={v!r}"[:120] for k, v in part]) if part else ("MISSING", [])


import os  # noqa: E402

ONLY = {int(x) for x in os.environ.get("CASES_ONLY", "").split(",") if x}
OUT = os.environ.get("OUT", "proper_data_round6.json")
CASES = [c for i, c in enumerate(CASES, 1) if not ONLY or i in ONLY]
CASE_NUMS = [i for i in range(1, 7) if not ONLY or i in ONLY]

results = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=60)
    page = browser.new_page(base_url=BASE_URL, viewport={"width": 1440, "height": 900})
    page.set_default_timeout(20_000)
    net, console = [], []

    def on_resp(r):
        if "/api/v1/" not in r.url:
            return
        m = r.request.method
        path = r.url.split("/api/v1")[-1][:160]
        if m != "GET" or r.status >= 400:
            try:
                body = r.text()[:1500]
            except Exception:
                body = ""
            net.append({"method": m, "path": path, "status": r.status,
                        "req": (r.request.post_data or "")[:3000], "resp": body})

    page.on("response", on_resp)
    page.on("console", lambda m: console.append(m.text[:200]) if m.type == "error" else None)
    h.login(page)

    for n, case in zip(CASE_NUMS, CASES):
        net.clear(); console.clear()
        rec = {"n": n, "label": case["label"]}
        entered = {}
        try:
            dialog = h.open_add_job_drawer(page)
            page.wait_for_timeout(1000)
            f = {k: case[k] for k in ("activityType", "buildingType", "newSystem") if k in case}
            h.fill_job_form(dialog, f)
            page.wait_for_timeout(600)

            entered.update(f)
            stamp = str(int(time.time()))[-5:]
            if "businessName" in case:
                sb = {k: case[k] for k in ("businessName", "signatoryFirstName", "signatoryLastName", "signatoryPosition")}
                sb["signatoryPhone"] = mobile()
                sb["signatoryEmail"] = f"{case['signatoryFirstName'].lower()}.{stamp}@yopmail.com"
                h.fill_job_form(dialog, sb)
                entered.update(sb)
            else:
                cust = dict(customerName=case["customerName"],
                            email=f"{re.sub(r'[^a-z]', '.', case['customerName'].lower())}.{stamp}@yopmail.com",
                            phone=mobile())
                h.fill_job_form(dialog, cust)
                entered.update(cust)

            rest = dict(abnAcn=valid_abn(), addressSearch=case["addressSearch"], postcode=case["postcode"],
                        leadMethod=case["leadMethod"], ownReference=case["ownReference"],
                        installationDate=case["installationDate"])
            h.fill_job_form(dialog, rest)
            entered.update(rest)
            try:
                entered["addressSelected"] = h.control_for_label(dialog, "Site address").inner_text().strip()
            except Exception:
                pass

            entered["installer"], inst_opts = pick_idx(dialog, "Installer (company)", case["installerIdx"])
            rec["installer_options"] = inst_opts
            page.wait_for_timeout(800)
            if h.field_exists(dialog, "Name of Installer Attended Site Inspection"):
                _, opts = options_for(dialog, "Name of Installer Attended Site Inspection")
                entered["siteInspectionInstaller"] = rnd.choice(opts)
                page.get_by_role("option", name=entered["siteInspectionInstaller"], exact=True).click()
                page.wait_for_timeout(400)

            rec["products_entered"] = fill_products(dialog, case["products"])
            page.screenshot(path=f"pd6-{n}-before.png", full_page=True)

            h.submit_job(dialog)
            try:
                h.send_button(dialog).wait_for(state="hidden", timeout=20_000)
                rec["created"] = True
            except Exception:
                rec["created"] = False
                rec["dialog_text"] = dialog.inner_text()[:2500]
            page.wait_for_timeout(2500)
            page.screenshot(path=f"pd6-{n}-after.png", full_page=True)
        except Exception as e:
            rec["script_error"] = f"{type(e).__name__}: {str(e)[:300]}"
            try:
                page.screenshot(path=f"pd6-{n}-error.png", full_page=True)
            except Exception:
                pass

        rec["entered"] = entered
        rec["writes"] = [x for x in net if x["method"] != "GET"]
        rec["errors_4xx_5xx"] = [f'{x["status"]} {x["method"]} {x["path"]}' for x in net if x["status"] >= 400]
        rec["console_errors"] = list(console)

        # --- read back and compare
        if rec.get("created"):
            lst = page.request.get("/api/v1/jobs?skip=0&limit=5&sort=createdAt&sortType=desc").json()["data"]["jobs"]
            mine = [j for j in lst if entered.get("email", entered.get("signatoryEmail", "~")).lower() in json.dumps(j).lower()]
            job_summary = mine[0] if mine else lst[0]
            rec["jobNumber"] = job_summary.get("jobNumber")
            detail = page.request.get(f"/api/v1/jobs/{job_summary['id']}")
            job = detail.json().get("data", {})
            job = job.get("job", job)
            rec["stored"] = job
            checks = {}
            for k, v in entered.items():
                checks[k] = {"entered": v, **dict(zip(("match", "where"), locate(job, v)))}
            for i, pr in enumerate(rec["products_entered"]):
                for k in ("brand", "model"):
                    if k in pr:
                        checks[f"product{i+1}.{k}"] = {"entered": pr[k], **dict(zip(("match", "where"), locate(job, pr[k])))}
            rec["checks"] = checks
            bad = {k: c for k, c in checks.items() if c["match"] != "exact"}
            print(f"[{n}] {case['label']}: CREATED {rec['jobNumber']} - {len(checks) - len(bad)}/{len(checks)} exact; "
                  f"not exact: {list(bad)}; errors: {rec['errors_4xx_5xx']}")
        else:
            print(f"[{n}] {case['label']}: NOT CREATED. {rec.get('script_error', '')} errors: {rec['errors_4xx_5xx']}")
        results.append(rec)
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=1, ensure_ascii=False, default=str)

    browser.close()
print("done -> proper_data_round6.json")

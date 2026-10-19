"""
Round 4 - more Job module scenarios (UI, report-only). Output: job_edge_4.txt (UTF-8).
Mostly client-side: only the fields under test are filled, so the other required
fields block the submit and NO job is created. The exceptions create at most three
jobs (H07 duplicate customer, H08 brand without model, H09 two identical products),
all with realistic AU names and @yopmail.com emails.
"""
import json
import re
import sys
import time

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

RID = str(int(time.time()))[-6:]
out = open("job_edge_4b.txt" if len(sys.argv) > 1 else "job_edge_4.txt", "w", encoding="utf-8")


def log(obj):
    print(json.dumps(obj, ensure_ascii=False), file=out, flush=True)


def lines(page):
    return {l.strip() for l in page.locator("body").inner_text().splitlines() if l.strip() and len(l.strip()) < 140}


def open_blank(page):
    page.goto("/jobs")
    page.get_by_role("button", name=re.compile("add job", re.I)).click()
    page.get_by_placeholder("Enter customer name").wait_for(state="visible")
    page.wait_for_timeout(600)
    return page.get_by_role("dialog")


def new_msgs(page, baseline, pattern):
    return sorted(l for l in lines(page) - baseline if re.search(pattern, l, re.I))


def base(name, i, **over):
    first = re.sub(r"[^a-z]", "", name.split(" ")[0].lower())
    d = dict(activityType="Heating & Cooling", buildingType="Residential Building",
             customerName=name, email=f"{first}.{RID}{i}@yopmail.com", phone=f"4{RID}{i:02d}"[:9],
             addressSearch="1 George Street Sydney", postcode="2000", leadMethod="Customer initiated contact",
             installationDate="15-12-2026", installer="BAWA", fillEquipment=True)
    d.update(over)
    return d


def submit_and_record(page, dialog, rec, search_for):
    h.submit_job(dialog)
    page.wait_for_timeout(3500)
    try:
        blocked = h.send_button(dialog).is_visible()
    except Exception:
        blocked = False
    if blocked:
        rec["result"] = "BLOCKED"
        rec["messages"] = sorted(l for l in lines(page) if re.search(
            r"required|valid|must|digit|error|failed|already|exist|duplicate", l, re.I))[:15]
        page.screenshot(path=f"edge4-{rec['id']}.png", full_page=True)
    else:
        page.goto("/jobs")
        page.get_by_placeholder(re.compile("search jobs", re.I)).fill(search_for)
        page.wait_for_timeout(4500)
        rows = page.locator("table tbody tr")
        rec["result"] = "CREATED"
        rec["rows_for_search"] = [re.sub(r"\s+", " ", rows.nth(k).inner_text())[:160] for k in range(min(rows.count(), 5))]
    log(rec)


ONLY = set(sys.argv[1:])


def run(cid, fn):
    if ONLY and cid not in ONLY:
        return
    try:
        fn()
    except Exception as e:
        log(dict(id=cid, result="SCRIPT-ERROR", detail=f"{type(e).__name__}: {str(e)[:220]}"))


def input_for(scope, label):
    return scope.get_by_text(re.compile(rf"^\s*\*?\s*{re.escape(label)}\s*$", re.I)).first.locator(
        "xpath=ancestor::*[.//input][1]").locator("input").first


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(base_url="https://nswstage.rebatem8.com.au")
    page.set_default_timeout(30_000)
    errs = []
    page.on("response", lambda r: errs.append(f"{r.status} {r.request.method} {r.url.split('/api/v1')[-1][:90]}")
            if "/api/v1/" in r.url and r.status >= 400 else None)
    for _ in range(3):
        try:
            h.login(page)
            break
        except Exception:
            pass

    d = open_blank(page)
    h.submit_job(d)
    page.wait_for_timeout(1500)
    baseline = lines(page)

    # H01 - Small Business: business-name / signatory field scenarios (client-side)
    sb_cases = [
        ("valid", dict(businessName="Harbourside Physiotherapy Pty Ltd", signatoryFirstName="Grace",
                       signatoryLastName="O'Connell", signatoryPosition="Practice Manager",
                       signatoryPhone="412398765", signatoryEmail="grace.oconnell@yopmail.com")),
        ("spaces only", dict(businessName="   ", signatoryFirstName="   ", signatoryLastName="   ", signatoryPosition="   ")),
        ("email no TLD", dict(signatoryEmail="grace@yopmail")),
        ("email no @", dict(signatoryEmail="grace.yopmail.com")),
        ("phone 8 digits", dict(signatoryPhone="41239876")),
        ("phone leading 0", dict(signatoryPhone="0412398765")),
        ("digits as names", dict(signatoryFirstName="12345", signatoryLastName="67890", signatoryPosition="99")),
        ("258-char business name", dict(businessName="Harbourside" * 23 + "Pty Ltd")),
    ]
    for scen, vals in sb_cases:
        def h01(scen=scen, vals=vals):
            dlg = open_blank(page)
            h.select_option(dlg, "Activity type", "Heating & Cooling")
            h.control_for_label(dlg, "Building type").click()
            page.get_by_role("option", name=re.compile(r"^Small Business Site", re.I)).first.click()
            page.wait_for_timeout(800)
            kept = {}
            for key, val in vals.items():
                label = h.SMALL_BUSINESS_FIELDS[key]
                h.fill_by_label(dlg, label, val, masked=(key == "signatoryPhone"))
                v = input_for(dlg, label).input_value()
                kept[label] = v if len(v) < 45 else f"{v[:15]}...({len(v)} chars)"
            h.submit_job(dlg)
            page.wait_for_timeout(1500)
            now = lines(page)
            log(dict(id="H01", scenario=scen, kept=kept,
                     messages=sorted(l for l in now if re.search(r"signatory|business|valid|digit|must", l, re.I)
                                     and "Small Business Site" not in l)[:14]))
        run("H01", h01)

    # H02-H04 - product numeric boundaries (client-side, no customer fields)
    num_cases = [
        ("H02", "Cooling Capacity (kW)", ["64.99", "65", "65.01", "0.01", "5.123456", "1e3", "5,5"]),
        ("H03", "Heating Capacity (kW)", ["64.99", "65", "65.01", "0", "5.123456", "1e3"]),
        ("H04", "Warranty Period", ["0", "1.5", "5", "100", "9999"]),
    ]
    for cid, label, values in num_cases:
        for val in values:
            def hnum(cid=cid, label=label, val=val):
                dlg = open_blank(page)
                h.select_option(dlg, "Activity type", "Heating & Cooling")
                h.select_option(dlg, "Building type", "Residential Building")
                h.select_option(dlg, "Installer (company)", "BAWA")
                page.wait_for_timeout(800)
                blk = dlg.locator(".border-dashed.border-gray-300").first
                h.fill_by_label(blk, label, val)
                kept = input_for(blk, label).input_value()
                h.submit_job(dlg)
                page.wait_for_timeout(1300)
                log(dict(id=cid, field=label, typed=val, kept=kept,
                         messages=new_msgs(page, baseline, r"capacity|warranty|kw|must|valid|number|year")))
            run(cid, hnum)

    # H05 - add / remove product blocks
    def h05():
        dlg = open_blank(page)
        h.select_option(dlg, "Activity type", "Heating & Cooling")
        h.select_option(dlg, "Building type", "Residential Building")
        h.select_option(dlg, "Installer (company)", "BAWA")
        page.wait_for_timeout(800)
        blocks = dlg.locator(".border-dashed.border-gray-300")
        add = dlg.get_by_role("button", name=re.compile("add another product", re.I))
        counts = [blocks.count()]
        for _ in range(6):
            if not add.is_visible() or not add.is_enabled():
                break
            add.click()
            page.wait_for_timeout(400)
            counts.append(blocks.count())
        btns = [b.strip() for b in dlg.get_by_role("button").all_inner_texts() if b.strip()]
        removed = None
        rm = dlg.get_by_role("button", name=re.compile(r"remove|delete", re.I))
        if rm.count():
            rm.last.click()
            page.wait_for_timeout(500)
            removed = blocks.count()
        h.submit_job(dlg)
        page.wait_for_timeout(1500)
        log(dict(id="H05", case="Add Another Product x6 then remove one", block_counts_after_each_add=counts,
                 add_button_still_enabled=add.is_visible() and add.is_enabled(), buttons_in_drawer=btns[:25],
                 blocks_after_remove=removed,
                 product_messages=new_msgs(page, baseline, r"product|brand|model|equipment")[:15]))
        page.screenshot(path="edge4-H05.png", full_page=True)
    run("H05", h05)

    # H06 - click outside the drawer with data entered (the drawer has no X button)
    def h06():
        dlg = open_blank(page)
        dlg.get_by_placeholder("Enter customer name").fill("Mason Kerr")
        page.mouse.click(40, 400)
        page.wait_for_timeout(1500)
        log(dict(id="H06", case="Click outside the Add Job drawer after typing a name",
                 drawer_still_open=page.get_by_placeholder("Enter customer name").is_visible(),
                 confirmation_text=[l for l in lines(page) if re.search(r"discard|unsaved|are you sure|lose|leave", l, re.I)]))
    run("H06", h06)

    # H07 - same customer (name, email, phone, address) as existing job M8N000078
    def h07():
        dlg = h.open_add_job_drawer(page)
        h.fill_job_form(dlg, base("Harrison Doyle", 1, email="harrison.doyle@yopmail.com", phone="412987654"))
        submit_and_record(page, dlg, dict(id="H07", case="Duplicate customer: same name/email/phone/address as M8N000078"),
                          "Harrison Doyle")
    run("H07", h07)

    # H08 - Brand chosen but Model left blank
    def h08():
        dlg = h.open_add_job_drawer(page)
        h.fill_job_form(dlg, base("Imogen Carter", 2, fillEquipment=False))
        blk = dlg.locator(".border-dashed.border-gray-300").first
        h.select_option_or_first(blk, "Original equipment", ["Installation of a New Air Conditioner", "Brand New Install"])
        page.wait_for_timeout(500)
        h.select_option_or_first(blk, "Brand")
        page.wait_for_timeout(500)
        submit_and_record(page, dlg, dict(id="H08", case="Product with Brand but no Model"), "Imogen Carter")
    run("H08", h08)

    # H09 - two identical products on one job
    def h09():
        dlg = h.open_add_job_drawer(page)
        h.fill_job_form(dlg, base("Lachlan Pierce", 3, fillEquipment=False, productCount=2))
        models = [h.control_for_label(dlg.locator(".border-dashed.border-gray-300").nth(k), "Model").inner_text().strip()
                  for k in range(2)]
        submit_and_record(page, dlg, dict(id="H09", case="Two identical products (same brand + model) on one job",
                                          models=models), "Lachlan Pierce")
    run("H09", h09)

    # H10 - job search by other attributes
    for term, why in [("harrison.doyle@yopmail.com", "customer email"), ("412987654", "phone digits"),
                      ("+61 412987654", "phone as displayed"), ("Doyle", "surname only"), ("m8n000078", "lower-case job id"),
                      ("M8N00007", "partial job id"), ("George St", "address"), ("BAWA", "installer"),
                      ("Heating & Cooling", "activity type"), ("REF-", "own reference")]:
        def h10(term=term, why=why):
            before = len(errs)
            page.goto("/jobs")
            page.get_by_placeholder(re.compile("search jobs", re.I)).fill(term)
            page.wait_for_timeout(4000)
            rows = page.locator("table tbody tr")
            first = re.sub(r"\s+", " ", rows.first.inner_text())[:120] if rows.count() else ""
            log(dict(id="H10", search=term, by=why, rows=rows.count(), first_row=first, api_errors=errs[before:]))
        run("H10", h10)

    # H11 - pagination and sorting on All Jobs
    def h11():
        page.goto("/jobs")
        page.wait_for_timeout(4000)

        def ids():
            return re.findall(r"M8N\d+", page.locator("table tbody").inner_text())
        p1 = ids()
        footer = [l for l in lines(page) if re.search(r"page|of \d+|showing|rows|per page", l, re.I)][:8]
        p2 = None
        nxt = page.get_by_role("button", name=re.compile(r"next|›|»", re.I))
        two = page.get_by_role("button", name="2", exact=True)
        target = nxt if nxt.count() else two
        if target.count():
            target.first.click()
            page.wait_for_timeout(3500)
            p2 = ids()
        sort = {}
        page.goto("/jobs")
        page.wait_for_timeout(3500)
        for col in ["Job ID", "Customer Name", "Installation Date", "Status"]:
            hdr = page.locator("table thead th").filter(has_text=col).first
            if hdr.count():
                before = len(errs)
                hdr.click()
                page.wait_for_timeout(3000)
                sort[col] = dict(first_ids=ids()[:4], api_errors=errs[before:])
        log(dict(id="H11", page1=p1, page2=p2, overlap=sorted(set(p1) & set(p2 or [])), footer=footer, sort=sort))
    run("H11", h11)

    # H12 - URL tampering on job pages
    for url in ["/jobs/M8N999999", "/jobs/not-a-job", "/job-details/M8N999999", "/jobs?status=Paid", "/jobs?page=9999"]:
        def h12(url=url):
            before = len(errs)
            page.goto(url)
            page.wait_for_timeout(3500)
            body = re.sub(r"\s+", " ", page.locator("body").inner_text())
            log(dict(id="H12", url=url, landed=page.url, api_errors=errs[before:],
                     shows=re.findall(r"(not found|404|no data found|something went wrong|access denied)", body, re.I)[:3],
                     rows=page.locator("table tbody tr").count()))
        run("H12", h12)

    # H13 - after logout: Back button and direct /jobs
    def h13():
        page.goto("/jobs")
        page.wait_for_timeout(2000)
        if not page.get_by_text(re.compile(r"log ?out|sign ?out", re.I)).first.is_visible():
            page.locator("header img, header button, [class*=avatar]").last.click()
            page.wait_for_timeout(800)
        page.get_by_text(re.compile(r"log ?out|sign ?out", re.I)).first.click()
        page.wait_for_timeout(1500)
        for t in page.get_by_role("button", name=re.compile(r"^(yes|log ?out|confirm)", re.I)).all():
            if t.is_visible():
                t.click()
                break
        page.wait_for_timeout(2500)
        after_logout = page.url
        page.go_back()
        page.wait_for_timeout(2500)
        back_url, back_rows = page.url, page.locator("table tbody tr").count()
        page.goto("/jobs")
        page.wait_for_timeout(2500)
        log(dict(id="H13", case="Log out, then Back button and direct /jobs", url_after_logout=after_logout,
                 back_url=back_url, back_shows_rows=back_rows, direct_jobs_url=page.url,
                 direct_jobs_rows=page.locator("table tbody tr").count(),
                 auth_keys_left_in_storage=page.evaluate("() => Object.keys(localStorage).filter(k => /token|auth|user/i.test(k))")))
    run("H13", h13)

    browser.close()
out.close()
print("done")

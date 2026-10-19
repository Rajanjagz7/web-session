"""
Round 3 - wider Job module scenarios (UI, report-only). Output: job_edge_3.txt (UTF-8).
Writes: G01 creates a job only if the app accepts a VIC address; G07 edits our own job
M8N000078 (clears Electrician, tries Save, then restores Belinda Baker). Everything
else is read-only.
"""
import json
import re
import sys
import time

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

RID = str(int(time.time()))[-6:]
out = open("job_edge_3.txt", "w", encoding="utf-8")
STATUSES = ["Engagement Sent", "Site Assessment and Nomination Requested", "Site Assessment Complete",
            "Nomination Signed", "Photos Started", "Photos Complete", "Being Assessed", "Action Required",
            "Completed", "Archived", "Cancelled", "Draft"]


def log(obj):
    print(json.dumps(obj, ensure_ascii=False), file=out, flush=True)


def row_statuses(page):
    rows = page.locator("table tbody tr")
    found = []
    for k in range(rows.count()):
        t = re.sub(r"\s+", " ", rows.nth(k).inner_text())
        st = next((s for s in sorted(STATUSES, key=len, reverse=True) if s in t), "?")
        jid = re.search(r"M8N\d+", t)
        found.append(f"{jid.group(0) if jid else '-'}:{st}")
    return found


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(base_url="https://nswstage.rebatem8.com.au")
    page.set_default_timeout(45_000)
    errs = []
    page.on("response", lambda r: errs.append(f"{r.status} {r.request.method} {r.url.split('/api/v1')[-1][:90]}")
            if "/api/v1/" in r.url and r.status >= 400 else None)
    h.login(page)

    # G01 - Victorian address on an NSW-scheme job
    try:
        name = "Charlotte Nguyen"
        dialog = h.open_add_job_drawer(page)
        h.fill_job_form(dialog, dict(
            activityType="Heating & Cooling", buildingType="Residential Building", customerName=name,
            email=f"charlotte.nguyen.{RID}@yopmail.com", phone=f"4{RID}31"[:9], addressSearch="88 Bourke Street Melbourne",
            postcode="3000", leadMethod="Customer initiated contact", installationDate="15-12-2026",
            installer="BAWA", fillEquipment=True))
        addr = h.control_for_label(dialog, "Site address").inner_text().strip()
        h.submit_job(dialog)
        page.wait_for_timeout(3500)
        blocked = h.send_button(dialog).is_visible()
        rec = dict(id="G01", case="Victorian address (Melbourne VIC 3000) on an NSW-scheme job", address_picked=addr)
        if blocked:
            rec["result"] = "BLOCKED"
            rec["messages"] = sorted({l.strip() for l in page.locator("body").inner_text().splitlines()
                                      if len(l) < 140 and re.search(r"nsw|state|address|postcode|error|required|valid", l, re.I)})[:12]
        else:
            page.goto("/jobs")
            page.get_by_placeholder(re.compile("search jobs", re.I)).fill(name)
            page.wait_for_timeout(4500)
            rec["result"] = "CREATED"
            rec["list_row"] = re.sub(r"\s+", " ", page.locator("table tbody tr").first.inner_text())[:220]
        log(rec)
    except Exception as e:
        log(dict(id="G01", result="SCRIPT-ERROR", detail=f"{type(e).__name__}: {str(e)[:200]}"))

    # G02 - Manual address option
    try:
        dialog = h.open_add_job_drawer(page)
        page.get_by_text("Add Manual Address", exact=True).first.click()
        page.wait_for_timeout(1200)
        txt = dialog.inner_text()
        seg = txt.split("Site Address")[-1][:700] if "Site Address" in txt else txt[-700:]
        h.submit_job(dialog)
        page.wait_for_timeout(2000)
        msgs = sorted({l.strip() for l in page.locator("body").inner_text().splitlines()
                       if len(l) < 120 and re.search(r"required|valid", l, re.I)})
        page.screenshot(path="edge3-G02.png", full_page=True)
        log(dict(id="G02", case="Add Manual Address - fields shown and blank-submit messages", fields_section=seg, messages=msgs))
    except Exception as e:
        log(dict(id="G02", result="SCRIPT-ERROR", detail=f"{type(e).__name__}: {str(e)[:200]}"))

    # G03 - Job list tabs: which statuses appear where
    for tab, url in [("All", "/jobs"), ("In Progress", "/in-progress-jobs"), ("Action Required", "/action-Required-jobs"),
                     ("Being Assessed", "/being-assessed-jobs"), ("Completed", "/completed-jobs"), ("Archived", "/archived-jobs")]:
        try:
            before = len(errs)
            page.goto(url)
            page.wait_for_timeout(4000)
            log(dict(id="G03", tab=tab, url=url, rows=row_statuses(page), api_errors=errs[before:]))
        except Exception as e:
            log(dict(id="G03", tab=tab, result="SCRIPT-ERROR", detail=str(e)[:200]))

    # G04 - Status filter on All Jobs
    try:
        page.goto("/jobs")
        page.wait_for_timeout(3000)
        page.get_by_text("Select Status", exact=True).first.click()
        page.wait_for_timeout(1000)
        opts = page.get_by_role("option").all_text_contents()
        pick = "Nomination Signed" if "Nomination Signed" in opts else opts[0]
        page.get_by_role("option", name=pick, exact=True).click()
        page.wait_for_timeout(4000)
        rows = row_statuses(page)
        log(dict(id="G04", case=f"Status filter = {pick}", filter_options=opts, rows=rows,
                 wrong_rows=[r for r in rows if not r.endswith(pick)]))
    except Exception as e:
        log(dict(id="G04", result="SCRIPT-ERROR", detail=f"{type(e).__name__}: {str(e)[:200]}"))

    # G05 - Job detail tabs on a Photos Started job: any API errors?
    try:
        h.open_job_detail(page, "M8N000071")
        tab_errs = {}
        for tab in ["Job Information", "Products", "Post Install Details", "Tasks", "Photos", "Notes",
                    "Documents", "Audit Checklist", "Activity Logs"]:
            before = len(errs)
            try:
                page.get_by_role("button", name=tab, exact=True).first.click(timeout=8000)
                page.wait_for_timeout(2500)
                body = page.locator("body").inner_text()
                empty = bool(re.search(r"no data|not found|something went wrong", body, re.I))
                tab_errs[tab] = dict(api_errors=errs[before:], shows_empty_or_error_text=empty)
            except Exception as te:
                tab_errs[tab] = f"could not open: {type(te).__name__}"
        header = re.sub(r"\s+", " ", page.locator("body").inner_text())
        m = re.search(r"Job ID:\s*(\S*)", header)
        log(dict(id="G05", case="Job detail tabs on M8N000071 (Photos Started)", tabs=tab_errs,
                 header_job_id=m.group(1) if m else "?"))
    except Exception as e:
        log(dict(id="G05", result="SCRIPT-ERROR", detail=f"{type(e).__name__}: {str(e)[:200]}"))

    # G06 - Document icon on a job row
    try:
        page.goto("/jobs")
        page.get_by_placeholder(re.compile("search jobs", re.I)).fill("M8N000078")
        page.wait_for_timeout(4000)
        icons = page.locator("table tbody tr").first.locator("svg, img, button")
        before = len(errs)
        popup = None
        try:
            with page.context.expect_page(timeout=6000) as pinfo:
                icons.nth(1).click()
            popup = pinfo.value
        except Exception:
            pass
        page.wait_for_timeout(2500)
        tgt = popup or page
        log(dict(id="G06", case="Second (document) icon on job row M8N000078", opened_url=tgt.url,
                 api_errors=errs[before:], visible_text=re.sub(r"\s+", " ", tgt.locator("body").inner_text())[:200]))
        if popup:
            popup.close()
    except Exception as e:
        log(dict(id="G06", result="SCRIPT-ERROR", detail=f"{type(e).__name__}: {str(e)[:200]}"))

    # G07 - Step 2 on our own job: clear Electrician, Save, then restore
    try:
        page.goto("/jobs")
        page.get_by_placeholder(re.compile("search jobs", re.I)).fill("M8N000078")
        page.wait_for_timeout(4000)
        page.locator("table tbody tr").first.locator("svg, img, button").first.click()
        page.wait_for_timeout(3000)
        dialog = page.get_by_role("dialog")
        ctl = h.control_for_label(dialog, "Electrician")
        ctl.locator(".select__clear-indicator").first.click(timeout=8000)
        page.wait_for_timeout(600)
        dialog.get_by_role("button", name="Save", exact=True).click()
        page.wait_for_timeout(3000)
        msgs = sorted({l.strip() for l in page.locator("body").inner_text().splitlines()
                       if len(l) < 120 and re.search(r"required|error|success|updated|saved", l, re.I)})
        page.screenshot(path="edge3-G07.png", full_page=True)
        rec = dict(id="G07", case="Own job M8N000078 step 2: clear Electrician then Save", messages=msgs)
        page.goto("/jobs")
        page.get_by_placeholder(re.compile("search jobs", re.I)).fill("M8N000078")
        page.wait_for_timeout(4000)
        page.locator("table tbody tr").first.locator("svg, img, button").first.click()
        page.wait_for_timeout(3000)
        dialog = page.get_by_role("dialog")
        now = h.control_for_label(dialog, "Electrician").inner_text().strip()
        rec["electrician_after_save_and_reopen"] = now
        if "Belinda Baker" not in now:
            h.select_option_or_first(dialog, "Electrician", "Belinda Baker")
            dialog.get_by_role("button", name="Save", exact=True).click()
            page.wait_for_timeout(2500)
            rec["restored"] = True
        log(rec)
    except Exception as e:
        log(dict(id="G07", result="SCRIPT-ERROR", detail=f"{type(e).__name__}: {str(e)[:200]}"))

    browser.close()
out.close()
print("done")

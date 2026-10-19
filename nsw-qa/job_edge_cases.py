"""
Job-module edge cases NOT already in the automated suite. Each case fills a valid
Residential Heating & Cooling job (BAWA) with ONE field changed, submits, and reports
whether the app BLOCKED it (with the error text) or CREATED a job. Report-only, no
asserts - "created" on an invalid input is the potential bug.

Jobs are only created where the app accepts the input. Names are realistic AU names,
emails are @yopmail.com. Job-list search checks at the end are read-only.
"""
import json
import re
import sys
import time

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

RID = str(int(time.time()))[-6:]
results = []


def base(name, i):
    first = re.sub(r"[^a-z]", "", name.split(" ")[0].lower()) or "customer"
    return dict(
        activityType="Heating & Cooling", buildingType="Residential Building",
        customerName=name, email=f"{first}.{RID}{i}@yopmail.com", phone=f"4{RID}{i:02d}"[:9],
        addressSearch="1 George Street Sydney", postcode="2000", leadMethod="Customer initiated contact",
        installationDate="15-12-2026", installer="BAWA", fillEquipment=True,
    )


CASES = [
    ("E01", "ABN with invalid checksum (11 digits)", "Oliver Bennett", {"abnAcn": "12345678901"}, "blocked"),
    ("E02", "ABN valid checksum typed with spaces", "Grace Whitaker", {"abnAcn": "33 102 417 032"}, "created"),
    ("E03", "Email without a TLD", "Harper Collins", {"email": f"harper.collins{RID}@yopmail"}, "blocked"),
    ("E04", "Email with consecutive dots", "Thomas Reid", {"email": f"thomas..reid{RID}@yopmail.com"}, "blocked"),
    ("E05", "Email with trailing space", "Chloe Watson", {"email": f"chloe.watson{RID}@yopmail.com "}, "created (trimmed)"),
    ("E06", "Customer phone is an NSW landline (02)", "Henry Clarke", {"phone": "298765432"}, "PO decision"),
    ("E07", "Customer name is a single character", "J", {}, "PO decision"),
    ("E08", "Name with apostrophe, hyphen and diacritic", "Siobhán O'Brien-Nguyễn", {}, "created, shown correctly"),
    ("E09", "Installation date 29-02-2027 (not a leap year)", "Isabella Hart", {"installationDate": "29-02-2027"}, "blocked"),
    ("E10", "Installation date 29-02-2028 (leap year)", "Matilda Grant", {"installationDate": "29-02-2028"}, "created"),
    ("E11", "Second product added but left blank", "William Foster", {"_add_blank_product": True}, "blocked"),
]


def run_case(page, i, cid, what, name, overrides, expect):
    fields = base(name, i)
    add_blank = overrides.pop("_add_blank_product", False)
    fields.update(overrides)
    page.goto("/jobs")
    dialog = h.open_add_job_drawer(page)
    h.fill_job_form(dialog, fields)
    if add_blank:
        dialog.get_by_role("button", name=re.compile("add another product", re.I)).click()
        page.wait_for_timeout(500)
    h.submit_job(dialog)
    page.wait_for_timeout(3000)
    try:
        still_open = h.send_button(dialog).is_visible()
    except Exception:
        still_open = False
    rec = dict(id=cid, case=what, name=name, expected=expect)
    if still_open:
        text = page.locator("body").inner_text()
        errs = sorted({l.strip() for l in text.splitlines()
                       if re.search(r"required|invalid|valid|must|digit|not able|error|incorrect", l, re.I) and len(l) < 120})
        rec.update(result="BLOCKED", errors=errs)
        page.screenshot(path=f"edge-{cid}.png", full_page=True)
    else:
        page.goto("/jobs")
        term = name if len(name) > 1 else fields["email"].split("@")[0]
        page.get_by_placeholder(re.compile("search jobs", re.I)).fill(term)
        page.wait_for_timeout(2000)
        rows = page.locator("table tbody tr")
        rec.update(result="CREATED", searched_for=term,
                   list_rows=[rows.nth(k).inner_text().replace("\n", " ").replace("\t", " ")[:170] for k in range(min(rows.count(), 3))])
    results.append(rec)
    print(json.dumps(rec, ensure_ascii=False))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(base_url="https://nswstage.rebatem8.com.au")
    page.set_default_timeout(30_000)
    server_errors = []
    page.on("response", lambda r: server_errors.append(f"{r.status} {r.request.method} {r.url.split('/api/v1')[-1][:80]}")
            if "/api/v1/" in r.url and r.status >= 500 else None)
    h.login(page)

    for i, (cid, what, name, ov, exp) in enumerate(CASES, start=1):
        try:
            run_case(page, i, cid, what, name, dict(ov), exp)
        except Exception as e:
            rec = dict(id=cid, case=what, result="SCRIPT-ERROR", detail=f"{type(e).__name__}: {str(e)[:200]}")
            results.append(rec)
            print(json.dumps(rec))

    # E12: double-click Send - does it create two jobs?
    try:
        name = "Lachlan Pearce"
        page.goto("/jobs")
        dialog = h.open_add_job_drawer(page)
        h.fill_job_form(dialog, base(name, 12))
        h.send_button(dialog).dblclick()
        page.wait_for_timeout(4000)
        page.goto("/jobs")
        page.get_by_placeholder(re.compile("search jobs", re.I)).fill(name)
        page.wait_for_timeout(2000)
        rows = page.locator("table tbody tr").filter(has_text=name)
        rec = dict(id="E12", case="Double-click Send Engagement Letter", expected="1 job", result=f"{rows.count()} job(s) created",
                   list_rows=[rows.nth(k).inner_text().replace("\n", " ").replace("\t", " ")[:120] for k in range(rows.count())])
    except Exception as e:
        rec = dict(id="E12", case="Double-click Send", result="SCRIPT-ERROR", detail=str(e)[:200])
    results.append(rec)
    print(json.dumps(rec))

    # S01-S06: job-list search edge cases (read-only)
    for sid, term, note in [
        ("S01", "m8n000078", "job ID in lowercase"),
        ("S02", "  M8N000078  ", "job ID with surrounding spaces"),
        ("S03", "Harrison", "partial customer name"),
        ("S04", "412987654", "phone number"),
        ("S05", "%", "SQL wildcard"),
        ("S06", "'", "single quote"),
    ]:
        page.goto("/jobs")
        before = len(server_errors)
        page.get_by_placeholder(re.compile("search jobs", re.I)).fill(term)
        page.wait_for_timeout(2200)
        rows = page.locator("table tbody tr")
        first = rows.first.inner_text().replace("\n", " ").replace("\t", " ")[:110] if rows.count() else ""
        rec = dict(id=sid, case=f"Search: {note} ({term!r})", rows=rows.count(), first_row=first,
                   server_errors=server_errors[before:])
        results.append(rec)
        print(json.dumps(rec, ensure_ascii=False))

    print("\nAll 5xx seen during run:", server_errors)
    browser.close()

with open("job_edge_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=1, ensure_ascii=False)
print("Saved job_edge_results.json")

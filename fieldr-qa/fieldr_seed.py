"""
Fieldr QA data seeder (Python port of the browser-side seeding used in this session).

What it does (all data is fictional, AU-flavoured, deterministic):
  customers  - unique AU names, @yopmail.com emails, unique realistic AU mobiles, AU addresses, optional profile photo
  items      - trade items in price tiers, each with a DIFFERENT margin (cost price vs sell price)
  invoices   - 1-3 line items, 10% GST is calculated by the server
  jobs       - varied statuses, dated this week so dashboard tiles fill

Auth: the OTP endpoints were not captured during the session, so this script uses your logged-in
browser session. Log in once (OTP), copy the `connect.sid` cookie value from DevTools > Application > Cookies,
and export it. Never commit it.

    set FLDR_COOKIE=s%3A....            (Windows cmd)     export FLDR_COOKIE='s%3A....'   (bash)
    set FLDR_BASE_URL=https://<tenant>.dev.fieldr.app
    python fieldr_seed.py --customers 100 --items 100 --invoices 100 --jobs 60 --avatars seed-images
    python fieldr_seed.py --fix-items --quotes 100 --cms --holidays --settings-data
    python fieldr_seed.py --enrich-jobs --fill-reports --invoice-statuses      (run last: needs templates, jobs and invoices first)

Not covered (blocked or undiscovered): users and groups (seat-limited, API-created users are invisible), timesheets/crew (POST /timelog/create stores nothing).

Known platform limits seen on the dev tenant (plan/seat gated - not bugs in this script):
  * Solo plan: max 5 active jobs (403 planLimitReached).  Basic plan lifts it.
  * Basic plan: 1 user seat. Users created over the API succeed but never appear in the UI.
  * Mobile numbers must be unique across ALL tenants (400/409 "already registered").
"""
import argparse
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests

BASE = os.environ.get("FLDR_BASE_URL", "https://rajanjagz7.dev.fieldr.app").rstrip("/")
COOKIE = os.environ.get("FLDR_COOKIE", "")
HEADERS = {"x-device-type": "web", "content-type": "application/json"}

FIRST = ["Olivia", "Noah", "Mia", "Jack", "Aria", "Liam", "Charlotte", "William", "Zoe", "Ethan", "Amelia", "Oliver", "Isla", "Lucas", "Grace",
         "Henry", "Ruby", "Leo", "Chloe", "Thomas", "Sophie", "Mason", "Emily", "Archer", "Matilda", "Harrison", "Ella", "Riley", "Hannah", "Cooper",
         "Lily", "Hunter", "Evie", "Max", "Sienna", "Jacob", "Georgia", "Xavier", "Willow", "Sebastian", "Piper", "Angus", "Frankie", "Hamish",
         "Tahlia", "Kai", "Imogen", "Callum", "Maddison", "Dylan"]
LAST = ["Nguyen", "Smith", "Collins", "Wilson", "Patel", "Brown", "Anderson", "Lee", "Khan", "White", "Taylor", "Martin", "Thompson", "Walker",
        "Harris", "Clarke", "Robinson", "Young", "Kelly", "Ryan", "Murphy", "Campbell", "Stewart", "Morgan", "Reid", "Bennett", "Fraser", "Mitchell",
        "Hughes", "Cameron", "Singh", "Chen", "Wang", "Tran", "Kaur", "Sharma", "Papadopoulos", "Rossi", "Kovacs", "Hassan", "OConnor", "McDonald",
        "Sutherland", "Ferguson", "Grant", "Hayes", "Barker", "Doyle", "Watts", "Lawson"]
ADDR = [("12 Macquarie Street", "Sydney", "NSW", "2000"), ("88 Bourke Street", "Melbourne", "VIC", "3000"), ("145 Eagle Street", "Brisbane", "QLD", "4000"),
        ("27 Adelaide Terrace", "Perth", "WA", "6000"), ("101 Rundle Mall", "Adelaide", "SA", "5000"), ("9 Brisbane Street", "Hobart", "TAS", "7000"),
        ("21 London Circuit", "Canberra", "ACT", "2601"), ("76 Mitchell Street", "Darwin", "NT", "0800")]
PREFIX = ["412", "423", "434", "458", "401", "417", "438", "449", "466", "477", "421", "431", "404", "415", "429"]
ITEMS = [("Labour - Electrician", "hour", 110), ("Labour - Plumber", "hour", 105), ("Labour - Apprentice", "hour", 65), ("Labour - Site Supervisor", "hour", 135),
         ("Call-out Fee", "each", 89), ("LED Downlight 10W", "each", 24.5), ("Power Point Double GPO", "each", 18.9), ("Circuit Breaker 20A", "each", 32),
         ("Safety Switch RCD", "each", 78), ("Copper Pipe 15mm", "metre", 12.4), ("PVC Pipe 50mm", "metre", 8.75), ("Mixer Tap Chrome", "each", 145),
         ("Hot Water Unit 250L", "each", 1290), ("Split System Install", "each", 850), ("Air Con Service", "each", 180), ("Smoke Alarm 240V", "each", 49),
         ("Cable TPS 2.5mm", "metre", 3.2), ("Conduit 20mm", "metre", 2.1), ("Concrete Slab 100mm", "sqm", 95), ("Paint Interior 10L", "each", 132),
         ("Gutter Cleaning", "each", 220), ("Lawn Mow & Edge", "each", 75), ("Pressure Wash", "sqm", 6.5), ("Skip Bin 6m3", "each", 420), ("Traffic Control", "hour", 98)]
TIERS = [("Standard", 1.0), ("Premium", 1.25), ("Bulk", 0.9), ("Weekend", 1.5)]
JOBS = ["Switchboard Upgrade", "Hot Water Replacement", "Split System Install", "Downlight Retrofit", "Blocked Drain Clearing", "Bathroom Re-plumb",
        "Smoke Alarm Compliance", "EV Charger Install", "Roof Gutter Repair", "Kitchen Tap Replacement", "Solar Inverter Service",
        "Backflow Prevention Test", "Pool Pump Repair", "Ceiling Fan Install", "Safety Inspection"]


class Fieldr:
    def __init__(self):
        if not COOKIE:
            sys.exit("Set FLDR_COOKIE (connect.sid value from a logged-in browser session).")
        self.s = requests.Session()
        self.s.cookies.set("connect.sid", COOKIE)
        self.s.headers.update(HEADERS)

    def call(self, method, path, **kw):
        r = self.s.request(method, f"{BASE}/api/v1{path}", timeout=30, **kw)
        try:
            body = r.json()
        except ValueError:
            body = {"raw": r.text[:200]}
        return r.status_code, body

    def logged_in(self):
        code, _ = self.call("GET", "/auth/is-logged-in")
        return code == 200

    def list(self, resource, limit=200):
        code, body = self.call("GET", f"/{resource}/list", params={"query": "", "skip": 0, "limit": limit})
        return body.get("data", []) if code == 200 else []

    def upload_image(self, path: Path):
        """multipart POST /aws/upload-file (field 'files') -> public fileUrl"""
        headers = {k: v for k, v in HEADERS.items() if k != "content-type"}  # let requests set the multipart boundary
        with path.open("rb") as fh:
            r = self.s.post(f"{BASE}/api/v1/aws/upload-file", headers=headers, files={"files": (path.name, fh, "image/png")}, timeout=60)
        r.raise_for_status()
        return r.json()["data"][0]["fileUrl"]


def national_mobile(seed_index, used):
    """Deterministic realistic 04xx xxx xxx. NOTE: may belong to a real person - keep SMS notifications OFF on the tenant."""
    x = 20260919 + seed_index * 7919
    while True:
        x = (x * 1103515245 + 12345) % 2147483648
        n = "0" + PREFIX[x % len(PREFIX)] + str(100000 + (x >> 8) % 899999)
        if n not in used:
            used.add(n)
            return n


def seed_customers(api, count, avatars_dir):
    existing = api.list("customer")
    used = {"0" + c["phone"] for c in existing}
    have = len(existing)
    ok = fail = 0
    for i in range(have, count):
        first, last = FIRST[i % 50], LAST[(i * 7 + i // 50 * 3 + i) % 50]
        street, city, st, pc = ADDR[i % 8]
        body = {"firstName": first, "lastName": last, "name": f"{first} {last}", "phone": national_mobile(i, used),
                "email": f"{first}.{last}.{i + 1:03d}@yopmail.com".lower(), "address": f"{(i * 7) % 190 + 1} {street.split(' ', 1)[1]}, {city} {st} {pc}",
                "description": f"QA seed customer {i + 1:03d} - {city} {st}. Fictional test data.", "profilePicture": "", "countryCode": "+61", "countryFlag": "au"}
        if avatars_dir:
            img = Path(avatars_dir) / f"avatar-{i % 100 + 1:03d}.png"
            if img.exists():
                body["profilePicture"] = api.upload_image(img)
        code, resp = api.call("POST", "/customer/create", json=body)
        ok, fail = (ok + 1, fail) if code == 200 else (ok, fail + 1)
        if code != 200:
            print("customer", i + 1, code, resp.get("message"))
    print(f"customers: +{ok} ok, {fail} failed (had {have})")


def seed_items(api, count):
    have = len(api.list("item"))
    ok = 0
    margins = set()
    n = 0
    for tier, mult in TIERS:
        for name, unit, price in ITEMS:
            n += 1
            if n <= have:
                continue
            if n > count:
                break
            rate = round(price * mult, 2)
            m = round(12 + ((n * 37) % 431) / 10, 1)  # 12.0% - 55.0%, different per item
            while m in margins:
                m = round(m + 0.1, 1)
            margins.add(m)
            body = {"name": f"{name} ({tier})", "unit": unit, "rate": rate, "costPrice": round(rate * (1 - m / 100), 2),
                    "description": f"{name} - {tier} tier. AUD ex-GST. Fictional test item."}
            code, resp = api.call("POST", "/item/create", json=body)
            ok += code == 200
            if code != 200:
                print("item", n, code, resp.get("message"))
    print(f"items: +{ok} ok (had {have})")


def seed_invoices(api, count):
    customers, items = api.list("customer", 500), api.list("item", 500)
    if not customers or not items:
        sys.exit("Seed customers and items first.")
    have = len(api.list("invoice"))
    ok = 0
    for i in range(have, count):
        lines = []
        for k in range(1 + i % 3):
            it = items[(i * 7 + k * 13) % len(items)]
            lines.append({"itemId": it["_id"], "item": it["_id"], "name": it["name"], "description": it["description"], "unit": it["unit"],
                          "quantity": 1 + (i + k) % 5, "rate": it["rate"], "discount": 10 if (i % 10 == 0 and k == 0) else 0, "tax": 10, "taxRate": 10})
        inv = date(2026, 7, 1) + timedelta(days=i % 80)
        body = {"customer": customers[(i * 3) % len(customers)]["_id"], "invoiceDate": inv.isoformat(), "dueDate": (inv + timedelta(days=30)).isoformat(), "lineItems": lines}
        code, resp = api.call("POST", "/invoice/create", json=body)
        ok += code == 200
        if code != 200:
            print("invoice", i + 1, code, resp.get("message"))
    print(f"invoices: +{ok} ok (had {have})")


def seed_jobs(api, per_status, week_start):
    customers = api.list("customer", 500)
    if not customers:
        sys.exit("Seed customers first.")
    ok = n = 0
    for status in ("In Progress", "On Hold", "Completed", "Schedule", "Cancelled"):
        for _ in range(per_status):
            n += 1
            c = customers[(n * 7) % len(customers)]
            day = (week_start + timedelta(days=n % 7)).isoformat()
            body = {"title": f"{JOBS[n % len(JOBS)]} - {c['firstName']} {c['lastName']} [{status}] #{n:03d}", "clientId": c["_id"], "date": day, "endDate": day,
                    "address": c["address"], "siteRadius": 100, "description": f"{JOBS[n % len(JOBS)]} at {c['address']}. Fictional QA seed job.", "status": status}
            code, resp = api.call("POST", "/job/create", json=body)
            ok += code == 200
            if code == 403:
                print("Job limit reached:", resp.get("data"))
                print(f"jobs: +{ok} ok")
                return
    print(f"jobs: +{ok} ok")


# ---------------------------------------------------------------------------------------------
# Added after the full walkthrough. Every payload below was observed working on the dev tenant.
# ---------------------------------------------------------------------------------------------
CITY_GEO = {"Sydney": (-33.8688, 151.2093), "Melbourne": (-37.8136, 144.9631), "Brisbane": (-27.4698, 153.0251), "Perth": (-31.9505, 115.8605),
            "Adelaide": (-34.9285, 138.6007), "Hobart": (-42.8821, 147.3272), "Canberra": (-35.2809, 149.13), "Darwin": (-12.4634, 130.8456)}
LABOUR = ("Labour", "Call-out", "Traffic Control", "Split System Install", "Air Con Service", "Gutter Cleaning", "Lawn Mow", "Pressure Wash")


def fix_items(api):
    """Labour/service items -> lineType 'labour' (the default was 'material' for everything). Margins already differ per item (seed_items)."""
    n = 0
    for it in api.list("item", 500):
        lt = "labour" if it.get("unit") == "hour" or it["name"].startswith(LABOUR) else "material"
        n += api.call("PUT", f"/item/update/{it['_id']}", json={**it, "lineType": lt})[0] == 200
    print(f"items retyped: {n}")


def _tokens(*parts):
    return [{"type": "op" if p in "+-*/" else "field" if p.isalpha() else "num", "value": p} for p in parts]


def seed_formulas(api):
    """Quote formulas. Tokens: field (quantity|rate|discount|tax|finalAmount), op (+ - * /), num. NOT a raw expression string."""
    defs = [("Line Total with 20% Markup", ["quantity", "*", "rate", "*", "1.2"], False), ("Cost plus 35% margin", ["quantity", "*", "rate", "*", "1.35"], False),
            ("GST amount (10%)", ["quantity", "*", "rate", "*", "tax", "/", "100"], True), ("Labour with 15% overhead", ["quantity", "*", "rate", "*", "1.15"], False),
            ("Trade discount amount", ["quantity", "*", "rate", "*", "discount", "/", "100"], True)]
    have = {f["name"]: f["_id"] for f in api.list("quote-formula", 100)}
    ids = {}
    for name, toks, show in defs:
        if name in have:
            ids[name] = have[name]
            continue
        _, r = api.call("POST", "/quote-formula/create", json={"name": name, "description": name, "expression": " ".join(toks), "tokens": _tokens(*toks),
                                                                "inputs": [], "decimals": 2, "showToCustomer": show, "isActive": True})
        ids[name] = r.get("data", {}).get("_id")
    return ids


def seed_quotes(api, count):
    """Quotes need sections[].items[]; formulas attach as section.formulaColumns=[{formulaId}]. formulaValues holds LINE-INPUT values, never results."""
    customers, items, fids = api.list("customer", 500), api.list("item", 500), seed_formulas(api)
    lab = [fids["Labour with 15% overhead"], fids["Line Total with 20% Markup"]]
    mat = [fids["Cost plus 35% margin"], fids["GST amount (10%)"], fids["Trade discount amount"]]
    desc = ["Bathroom renovation", "Kitchen rewire and downlights", "Split system supply and install", "Hot water system replacement", "Switchboard upgrade",
            "Storm-damage gutter repair", "Deck and pergola electrics", "Blocked drain relining", "Smoke alarm compliance upgrade", "EV charger installation"]

    def line(it, q):
        return {"itemId": it["_id"], "item": it["_id"], "name": it["name"], "description": it["description"], "unit": it["unit"], "quantity": q,
                "rate": it["rate"], "discount": 0, "tax": 10, "taxRate": 10, "lineType": it.get("lineType", "material"), "formulaValues": []}
    have = len(api.list("quote", 500))
    ok = 0
    for i in range(have, count):
        c = customers[(i * 3 + 1) % len(customers)]
        labour, m1, m2 = items[(i * 5) % len(items)], items[(i * 11 + 3) % len(items)], items[(i * 13 + 7) % len(items)]
        sections = [{"name": "Labour", "items": [line(labour, 2 + i % 6)], "formulaColumns": [{"formulaId": f} for f in lab[: 1 + i % 2]]},
                    {"name": "Materials", "items": [line(m1, 1 + i % 4)] + ([line(m2, 1 + i % 3)] if i % 2 else []),
                     "formulaColumns": [{"formulaId": f} for f in mat[: 1 + i % 3]]}]
        code, _ = api.call("POST", "/quote/create", json={"customer": c["_id"], "description": f"{desc[i % 10]} - {c['name']}, {c['address']}. Fictional QA quote.", "sections": sections})
        ok += code == 200
    print(f"quotes: +{ok}")


def seed_cms(api):
    """type is the DISPLAY name: Induction | Help | Privacy Policy | Terms & Conditions | FAQ (the API returns 500 on a bad value)."""
    pages = {"Induction": ["Site induction - NSW construction sites", "Working at heights", "Electrical safety and lock-out tag-out", "Manual handling", "Asbestos awareness", "PPE", "Incident reporting", "Working in heat"],
             "Help": ["How to clock on to a job", "Creating an invoice from a job report", "Adding a customer", "Sending a quote", "Scheduling a crew", "Recording timesheets", "Exporting reports", "Contacting support"],
             "Privacy Policy": ["Australian Privacy Principles", "Information we collect", "How we use information", "Disclosure to third parties", "Overseas disclosure", "Access and correction", "Data breach notification", "Cookies"],
             "Terms & Conditions": ["Terms of service", "Fees, GST and payment", "Acceptable use", "Subscription and cancellation", "Limitation of liability", "Intellectual property", "Governing law (NSW)", "Changes to terms"],
             "FAQ": ["How do I book a callout in NSW?", "Do prices include GST?", "Payment methods", "Are electricians licensed?", "Do you service regional VIC and QLD?", "Warranty", "Rescheduling", "Invoice copies"]}
    ok = sum(api.call("POST", "/cms/create", json={"type": t, "title": ti, "content": f"<p>{ti}. Fictional QA content for Australian field services.</p>"})[0] == 200
             for t, ts in pages.items() for ti in ts)
    print(f"cms: +{ok}")


def seed_holidays(api):
    """One per date (409 on duplicates)."""
    nat = "National public holiday."
    hol = [("New Year's Day", "2026-01-01", nat), ("Australia Day", "2026-01-26", nat), ("Labour Day (WA)", "2026-03-02", "WA"), ("Labour Day (VIC)", "2026-03-09", "VIC"),
           ("Good Friday", "2026-04-03", nat), ("Easter Saturday", "2026-04-04", "Most states"), ("Easter Sunday", "2026-04-05", "NSW VIC QLD ACT SA NT"), ("Easter Monday", "2026-04-06", nat),
           ("Anzac Day", "2026-04-25", nat), ("Labour Day (QLD)", "2026-05-04", "QLD"), ("Adelaide Cup Day", "2026-05-18", "SA"), ("Reconciliation Day", "2026-06-01", "ACT"),
           ("King's Birthday", "2026-06-08", "All except WA and QLD"), ("Picnic Day", "2026-08-03", "NT"), ("Royal Queensland Show", "2026-08-12", "Brisbane"),
           ("Labour Day (NSW)", "2026-10-05", "NSW"), ("Melbourne Cup Day", "2026-11-03", "Melbourne"), ("Christmas Day", "2026-12-25", nat), ("Boxing Day", "2026-12-26", nat)]
    print("holidays:", sum(api.call("POST", "/holiday/create", json={"name": n, "date": d, "description": ds})[0] == 200 for n, d, ds in hol))


def seed_checklists_and_templates(api):
    """Basic plan caps checklists and report templates at 3 each. Checklist items use 'label'. Template fields are free-form; type+label render in the builder."""
    cl = {"Pre-start safety check - electrical": ["PPE worn", "Test and tag current", "Circuit isolated and locked", "Voltage tested dead", "RCD tested"],
          "Plumbing job completion checklist": ["Pressure test passed", "No leaks", "Tempering valve tested", "Compliance certificate lodged"],
          "Smoke alarm compliance inspection": ["Alarms interconnected", "Alarm within 3 years of manufacture", "Test button operates", "Compliance form signed"]}
    have = {c["name"]: c["_id"] for c in api.list("checklist", 50)}
    for name, labels in cl.items():
        cid = have.get(name) or api.call("POST", "/checklist/create", json={"name": name, "description": name})[1].get("data", {}).get("_id")
        if cid:
            api.call("PUT", f"/checklist/update/{cid}", json={"name": name, "description": name, "items": [{"label": x} for x in labels]})

    def f(t, label, req=False, opts=None):
        d = {"type": t, "label": label, "name": label.lower().replace(" ", "_"), "required": req}
        if opts:
            d["options"] = [{"label": o, "value": o} for o in opts]
        return d
    tpl = {"Electrical Job Completion Report": [f("textbox", "Site address", True), f("date", "Date of work", True), f("radio", "Circuit tested and RCD operational", True, ["Yes", "No", "N/A"]),
                                                f("textarea", "Work summary", True), f("upload", "Photos of completed work")],
           "Plumbing Compliance Report": [f("textbox", "Site address", True), f("date", "Inspection date", True), f("radio", "Pressure test passed", True, ["Yes", "No"]), f("textarea", "Defects found")],
           "Site Safety Inspection Report": [f("textbox", "Site address", True), f("radio", "PPE worn by all crew", True, ["Yes", "No"]),
                                             f("dropdown", "Risk rating", False, ["Low", "Medium", "High", "Critical"]), f("textarea", "Hazards identified")]}
    have = {t["title"]: t["_id"] for t in api.list("template", 50)}
    for title, fields in tpl.items():
        tid = have.get(title) or api.call("POST", "/template/add", json={"title": title})[1].get("data", {}).get("_id")  # create is /template/add
        if tid:
            api.call("PUT", f"/template/edit/{tid}", json={"title": title, "fields": fields})  # edit is /template/edit/:id


def _epoch_ms(d, hour_utc):
    return ((d - date(1970, 1, 1)).days * 24 + hour_utc) * 3600 * 1000


def enrich_jobs(api):
    """Give every job dates (epoch ms, AEST = UTC+10), coordinates, report templates, checklists and planned items.
    Attaching templates to a job auto-creates one Job Report (status 'Created') per template. Partial PUT is supported."""
    jobs, items = api.list("job", 300), api.list("item", 300)
    tpls, cls = [t["_id"] for t in api.list("template", 20)], [c["_id"] for c in api.list("checklist", 20)]
    for i, j in enumerate(jobs):
        city = next((c for c in CITY_GEO if c in (j.get("address") or "")), "Sydney")
        la, lo = CITY_GEO[city]
        jit = ((i * 37) % 100 - 50) / 5000
        off = 7 + i % 26 if j["status"] == "Schedule" else (i % 14) - 3 if j["status"] == "Cancelled" else i % 7
        start = _epoch_ms(date(2026, 9, 13) + timedelta(days=off), -10 + 7 + i % 3)
        body = {"_id": j["_id"], "startDateAndTime": start, "endDateAndTime": start + (6 + i % 4) * 3600 * 1000, "latitude": la + jit, "longitude": lo + jit,
                "reports": [{"reportId": t, "isMandatory": (i + k) % 2 == 0} for k, t in enumerate(tpls[: 1 + i % 3])],
                "checklists": [{"checklistId": c, "isMandatory": (i + k) % 3 == 0} for k, c in enumerate(cls[: 1 + i % 3])],
                "plannedItems": [{"itemId": it["_id"], "item": it["_id"], "name": it["name"], "unit": it["unit"], "quantity": 1 + (i + k) % 6, "rate": it["rate"], "costPrice": it["costPrice"]}
                                 for k, it in [(k, items[(i * 7 + k * 11) % len(items)]) for k in range(2 + i % 2)]]}
        api.call("PUT", f"/job/update/{j['_id']}", json=body)
    print(f"jobs enriched: {len(jobs)}")


def fill_job_reports(api):
    """Set a status and a value on every report field (key 'value'). Statuses other than Created are free text on the API."""
    reports = api.list("job/report", 500)
    statuses = ["Created", "Submitted", "Approved", "Rejected"]
    addr = [f"{a[0]}, {a[1]} {a[2]} {a[3]}" for a in ADDR]
    for i, r in enumerate(reports):
        fields = []
        for f in r.get("fields", []):
            t, lab, opts = f.get("type"), f.get("label", "").lower(), f.get("options") or []
            if t == "date":
                v = f"2026-09-{10 + i % 9:02d}"
            elif "address" in lab:
                v = addr[i % 8]
            elif t in ("radio", "dropdown") and opts:
                v = opts[i % len(opts)]["value"]
            elif t == "number":
                v = 2 + i % 8
            elif t == "textarea":
                v = "Work completed and tested. Fictional QA report."
            elif t == "upload":
                v = ""
            else:
                v = f"Entry {i + 1}"
            fields.append({**f, "value": v})
        api.call("PUT", f"/job/report/update/{r['_id']}", json={"_id": r["_id"], "status": statuses[i % 4], "fields": fields})
    print(f"job reports filled: {len(reports)}")


def set_invoice_statuses(api):
    """Real UI statuses: Draft | Awaiting Approval | Awaiting Payment | Paid. Other strings are accepted by the API but vanish from the dashboard.
    NOTE: the API also accepts amountPaid/amountDue/payments from the client (finding F1) - use only on a throwaway tenant."""
    methods = ["Bank Transfer", "Credit Card", "Cheque", "Cash"]
    for i, d in enumerate(api.list("invoice", 500)):
        if not d.get("totalAmount"):
            continue
        k = i % 20
        if k < 11:
            day = f"2026-09-{13 + i % 7:02d}"
            body = {"status": "Paid", "amountPaid": d["totalAmount"], "amountDue": 0,
                    "payments": [{"amount": d["totalAmount"], "method": methods[i % 4], "reference": f"{d.get('serialNumber', i)} BSB 062-000", "date": day, "paidAt": day + "T00:00:00.000Z"}]}
        else:
            body = {"status": "Awaiting Payment" if k < 16 else "Awaiting Approval" if k < 18 else "Draft"}
        api.call("PUT", f"/invoice/update/{d['_id']}", json={"_id": d["_id"], **body})


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--quotes", type=int, default=0)
    p.add_argument("--cms", action="store_true")
    p.add_argument("--holidays", action="store_true")
    p.add_argument("--settings-data", action="store_true", help="checklists + report templates (Basic plan max 3 each)")
    p.add_argument("--fix-items", action="store_true")
    p.add_argument("--enrich-jobs", action="store_true", help="dates, coordinates, templates, checklists, planned items")
    p.add_argument("--fill-reports", action="store_true")
    p.add_argument("--invoice-statuses", action="store_true")
    p.add_argument("--customers", type=int, default=0)
    p.add_argument("--items", type=int, default=0)
    p.add_argument("--invoices", type=int, default=0)
    p.add_argument("--jobs", type=int, default=0, help="jobs PER STATUS (5 statuses)")
    p.add_argument("--avatars", default="", help="folder of avatar-001.png ... (see gen_avatars.py)")
    p.add_argument("--week-start", default="2026-09-13", help="Sunday of the dashboard week, YYYY-MM-DD")
    a = p.parse_args()
    api = Fieldr()
    if not api.logged_in():
        sys.exit("Cookie rejected: log in again and refresh FLDR_COOKIE.")
    if a.customers:
        seed_customers(api, a.customers, a.avatars)
    if a.items:
        seed_items(api, a.items)
    if a.invoices:
        seed_invoices(api, a.invoices)
    if a.jobs:
        seed_jobs(api, a.jobs, date.fromisoformat(a.week_start))
    # Order matters: items -> (fix types) -> quotes; settings data -> jobs enriched -> reports filled.
    if a.fix_items:
        fix_items(api)
    if a.quotes:
        seed_quotes(api, a.quotes)
    if a.cms:
        seed_cms(api)
    if a.holidays:
        seed_holidays(api)
    if a.settings_data:
        seed_checklists_and_templates(api)
    if a.enrich_jobs:
        enrich_jobs(api)
    if a.fill_reports:
        fill_job_reports(api)
    if a.invoice_statuses:
        set_invoice_statuses(api)


if __name__ == "__main__":
    t = time.time()
    main()
    print(f"done in {time.time() - t:.1f}s")

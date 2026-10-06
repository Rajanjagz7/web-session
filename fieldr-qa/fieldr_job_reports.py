"""Job Report data: convert templates and job reports to the app's native field schema, then create submissions.

The Job Report page lists /job/report/submission/list (submissions), not the /job/report records seeded earlier.
Native field: {id, name (element name), type, value, label, position, placeholder, options (strings), validation:{mandatory}}.
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fieldr_seed as f  # noqa: E402

NATIVE = {"textbox": ("Textbox", "text"), "text": ("Textbox", "text"), "dropdown": ("Dropdown", "dropdown"), "radio": ("Radio Button", "radio"),
          "checkbox": ("Checkbox", "checkbox"), "textarea": ("Textarea", "textarea"), "number": ("Number", "number"), "date": ("Date", "date"),
          "email": ("Email", "email"), "file": ("Upload", "file"), "sign": ("Signature", "sign")}
BASE_ID = 1789948800000
api = f.Fieldr()
log = {}


def convert(fields, keep_values=True):
    out = []
    for i, fl in enumerate(fields):
        nm, tp = NATIVE.get(fl.get("type"), ("Textbox", "text"))
        opts = [o["label"] if isinstance(o, dict) else o for o in fl.get("options", [])]
        d = {"id": fl.get("id") or f"{i + 1}-{BASE_ID + i}", "name": nm, "type": tp, "value": fl.get("value", "") if keep_values else "", "label": fl["label"],
             "position": i, "placeholder": f"Enter {fl['label']}", "validation": fl.get("validation") or {"mandatory": bool(fl.get("required"))}}
        if opts and tp in ("dropdown", "radio", "checkbox"):
            d["options"] = opts
        out.append(d)
    return out


def is_native(fields):
    return bool(fields) and all("id" in x and "validation" in x for x in fields)


# 1. templates
ok = 0
for t in api.list("template", 50):
    if is_native(t.get("fields", [])):
        continue
    code, _ = api.call("PUT", f"/template/edit/{t['_id']}", json={"title": t["title"], "fields": convert(t.get("fields", []), keep_values=False)})
    ok += code == 200
log["templates_converted"] = ok
print("templates converted:", ok)

# 2. job reports
recs = api.list("job/report", 700)
todo = [r for r in recs if not is_native(r.get("fields", []))]
ok = 0
for i, r in enumerate(todo):
    code, _ = api.call("PUT", f"/job/report/update/{r['_id']}", json={"fields": convert(r["fields"])})
    ok += code == 200
    if (i + 1) % 100 == 0:
        print(f"  converted {i + 1}/{len(todo)}", flush=True)
log["job_reports_converted"] = f"{ok}/{len(todo)}"
print("job reports converted:", log["job_reports_converted"])

# 3. submissions: filled reports on distinct jobs, spread over dates and templates
recs = api.list("job/report", 700)
filled = [r for r in recs if is_native(r["fields"]) and all(str(x.get("value", "")).strip() for x in r["fields"] if x["validation"]["mandatory"])]
seen_jobs, by_title, picks = set(), Counter(), []
for r in filled:
    if r["jobId"] in seen_jobs or by_title[r["title"]] >= 22:
        continue
    seen_jobs.add(r["jobId"]); by_title[r["title"]] += 1; picks.append(r)
    if len(picks) == 60:
        break
existing = {s["jobReportId"] for s in api.list("job/report/submission", 500)}
subs = []
for i, r in enumerate(picks):
    if r["_id"] in existing:
        continue
    day = datetime(2026, 9, 1, tzinfo=timezone.utc) + timedelta(days=i % 20)
    code, body = api.call("POST", "/job/report/submission/submit", json={"jobId": r["jobId"], "jobReportId": r["_id"], "fields": r["fields"], "reportDate": day.strftime("%Y-%m-%d")})
    if code == 200:
        subs.append(body["data"]["_id"])
log["submissions_created"] = len(subs)
print("submissions created:", len(subs), "| by template:", dict(by_title))

# 4. statuses: roughly 50% Submitted, 33% Approved, 17% Rejected
allsubs = api.list("job/report/submission", 500)
res = Counter()
for i, s in enumerate(allsubs):
    want = "Approved" if i % 3 == 1 else "Rejected" if i % 6 == 2 else None
    if want and s["status"] != want:
        body = {"status": want}
        if want == "Rejected":
            body["reason"] = "Missing photo of completed work; please resubmit."
        code, _ = api.call("PUT", f"/job/report/submission/status/{s['_id']}", json=body)
        res[f"{want}:{code}"] += 1
log["status_updates"] = dict(res)
print("status updates:", dict(res))

code, lst = api.call("GET", "/job/report/submission/list", params={"skip": 0, "limit": 1})
final = Counter(s["status"] for s in api.list("job/report/submission", 500))
log["submission_total"] = lst.get("totalCount")
log["submission_by_status"] = dict(final)
print("SUBMISSIONS NOW:", lst.get("totalCount"), dict(final))
json.dump(log, open("report_data-log.json", "w"), indent=1)

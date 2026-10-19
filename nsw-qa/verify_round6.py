"""Round 6 verification (read-only): stored details, engagement delivery status,
rebate values vs later-stage jobs, and the Jobs list row for each created job."""
import json
import re
import sys

sys.path.insert(0, "1er-tests-python")
from playwright.sync_api import sync_playwright  # noqa: E402
import helpers as h  # noqa: E402

runs = [r for f in ("proper_data_round6.json", "proper_data_round6_hwhp.json")
        for r in json.load(open(f, encoding="utf-8")) if r.get("jobNumber")]

with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    page = b.new_page(base_url="https://nswstage.rebatem8.com.au", viewport={"width": 1440, "height": 900})
    page.set_default_timeout(20_000)
    h.login(page)
    api = page.request

    print("== stored details / engagement delivery")
    for r in runs:
        jid = r["stored"].get("job", r["stored"])["id"]
        job = api.get(f"/api/v1/jobs/{jid}").json()["data"]["job"]
        a = job["address"]
        print(f"{r['jobNumber']} {r['label']}\n   status={job['status']} engagement={json.dumps(job.get('engagement'))}"
              f"\n   address: street#={a.get('streetNumber')!r} name={a.get('streetName')!r} type={a.get('streetType')!r} "
              f"suburb={a.get('suburb')!r} pc={a.get('postcode')!r} | entered pc={r['entered'].get('postcode')}"
              f"\n   installDate={job.get('installationDate')} entered={r['entered'].get('installationDate')}"
              f" | newSystem entered={r['entered'].get('newSystem')} stored={job.get('newSystem') or job.get('systemType')}"
              f"\n   rebate: esc={job.get('escCertificates')} escValue={job.get('escValue')} total={job.get('totalRebate')}"
              f"\n   customer={json.dumps(job.get('customer'), ensure_ascii=False)[:260]}"
              f"\n   equipment={json.dumps(job.get('equipmentQuoted'), ensure_ascii=False)[:300]}")

    print("\n== rebate values on later-stage jobs (for comparison)")
    for st in ["nomination_signed", "photos_started", "photos_complete", "customer_signature_requested"]:
        js = api.get(f"/api/v1/jobs?skip=0&limit=5&status={st}").json()["data"]["jobs"]
        for j in js[:2]:
            d = api.get(f"/api/v1/jobs/{j['id']}").json()["data"]["job"]
            print(f"   {st:30} {d['jobNumber']} esc={d.get('escCertificates')} escValue={d.get('escValue')} "
                  f"prc={d.get('prcValue')} total={d.get('totalRebate')} eng={json.dumps(d.get('engagement'))[:160]}")

    print("\n== Jobs list rows")
    for r in runs:
        page.goto("/jobs")
        page.get_by_placeholder(re.compile("search jobs", re.I)).fill(r["jobNumber"])
        page.wait_for_timeout(1800)
        rows = page.locator("table tbody tr")
        txt = re.sub(r"\s+", " ", rows.first.inner_text()) if rows.count() else "(no row)"
        e = r["entered"]
        want = {"name": e.get("customerName") or e.get("businessName"), "installer": e.get("installer")}
        missing = [k for k, v in want.items() if v and v.lower() not in txt.lower()]
        print(f"   {r['jobNumber']}: rows={rows.count()} missing={missing} | {txt[:230]}")
    page.screenshot(path="pd6-list.png", full_page=True)
    b.close()

"""Continuation: equipmentQuoted + ownReference fields, plus a clean single-shot
reproduction of the whitespace-name 500, plus an XSS-in-customer-name render check."""
import sys, json, time
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
from config import EMAIL, PASSWORD
from playwright.sync_api import sync_playwright

BASE_URL = "https://nswstage.rebatem8.com.au"
TEST_INSTALLER_ID = "6aace061972e326f8fef7aae"
RUN = str(int(time.time()))[-6:]


def baseline(n):
    return {
        "installerId": TEST_INSTALLER_ID, "activityType": "heating_cooling", "customerType": "residential",
        "methodOfLeadGeneration": "Customer initiated contact", "ownReference": f"BVM2-{RUN}-{n}",
        "installationDate": "2026-12-10",
        "customer": {"name": f"Boundary Test2 {n}", "email": f"boundary2.test.{RUN}.{n}@yopmail.com",
                     "phoneNumber": f"4{RUN[-8:]}"[:9], "countryCode": "+61", "flagCode": "AU", "abnAcn": "33102417032"},
        "address": {"fullAddress": "1 George St, Sydney NSW 2000, Australia", "isManual": False,
                    "streetNumber": "1", "streetName": "George", "streetType": "Street",
                    "suburb": "Sydney", "state": "NSW", "postcode": "2000"},
        "equipmentQuoted": [{"originalEquipment": "Installation of a New Air Conditioner",
                             "brand": "KELVINATOR", "model": "KWH60CRF", "coolingCapacityKw": 6, "heatingCapacityKw": 0}],
        "createdFrom": "add_job",
    }


def set_path(d, path, value):
    d = json.loads(json.dumps(d))
    obj = d
    parts = [int(p) if p.isdigit() else p for p in path.split(".")]
    for p in parts[:-1]:
        obj = obj[p]
    obj[parts[-1]] = value
    return d


results = []
with sync_playwright() as p:
    c = p.request.new_context(base_url=BASE_URL, timeout=20_000)
    c.post("/api/v1/auth/admin/login", data={"email": EMAIL, "password": PASSWORD})
    count_before = c.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["total"]

    CASES = []
    CASES += [("equipmentQuoted.0.coolingCapacityKw", lbl, v) for lbl, v in [
        ("valid", 6), ("zero", 0), ("negative", -5), ("very large", 999999),
        ("string number", "6"), ("null", None), ("float", 6.5),
        ("scientific notation", "1e3"), ("NaN string", "NaN"), ("Infinity string", "Infinity"),
        ("omitted", "__OMIT__"),
    ]]
    CASES += [("ownReference", lbl, v) for lbl, v in [
        ("valid", f"REF-{RUN}"), ("empty string", ""), ("null", None), ("omitted", "__OMIT__"),
        ("very long (600 chars)", "X" * 600), ("null byte", "REF\u0000X"),
    ]]

    n = 0
    for field, label, value in CASES:
        n += 1
        body = baseline(n)
        if value == "__OMIT__":
            parts = field.split(".")
            d = body
            for pp in parts[:-1]:
                d = d[int(pp) if pp.isdigit() else pp]
            del d[parts[-1]]
        else:
            body = set_path(body, field, value)
        r = c.post("/api/v1/jobs", data=body)
        try:
            j = r.json()
        except Exception:
            j = {"raw": r.text()[:200]}
        rec = {"n": n, "field": field, "label": label, "value": repr(value)[:60], "status": r.status,
               "response": json.dumps(j)[:350]}
        if r.status < 300:
            job = j["data"]["job"]
            rec["jobNumber"] = job["jobNumber"]
            detail = c.get(f"/api/v1/jobs/{job['id']}").json()["data"]["job"]
            rec["stored_equipment_or_ref"] = json.dumps(detail.get("equipmentQuoted") or detail.get("ownReference"))[:300]
        results.append(rec)
        print(f"[{n:3}] {'OK ' if r.status<300 else 'ERR'} {field:35} {label:38} -> {r.status}  {rec.get('jobNumber','')}  {rec['response'][:180]}")

    count_after = c.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["total"]
    print(f"\ncount before={count_before} after={count_after} delta={count_after-count_before}")

    print("\n-- clean repro: whitespace-only customer.name -> 500? --")
    body = baseline(999)
    body["customer"]["name"] = "   "
    r = c.post("/api/v1/jobs", data=body)
    print(r.status, r.text()[:1000])

    print("\n-- XSS check: does <script> in customer.name get created, and does it render raw anywhere? --")
    body2 = baseline(998)
    body2["customer"]["name"] = f"<img src=x onerror=alert('name-xss-{RUN}')> XSSCheck{RUN}"
    r2 = c.post("/api/v1/jobs", data=body2)
    print(r2.status, json.dumps(r2.json())[:400] if r2.status < 300 else r2.text()[:300])
    if r2.status < 300:
        jid = r2.json()["data"]["job"]["id"]
        jnum = r2.json()["data"]["job"]["jobNumber"]
        print("created job for XSS render check:", jnum, jid)

    with open(r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\round8_boundary_matrix2_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)
    c.dispose()

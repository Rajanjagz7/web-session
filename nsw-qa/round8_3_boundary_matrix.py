"""STEPS 2-6 of the protocol applied to POST /v1/jobs, one field at a time
against a known-good baseline. Every 2xx is read back via GET and the jobs
count is checked before/after. installerId is fixed to the designated
"Testing Company" test installer for every case (per user instruction)."""
import sys, json, time
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
from config import EMAIL, PASSWORD
from playwright.sync_api import sync_playwright

BASE_URL = "https://nswstage.rebatem8.com.au"
TEST_INSTALLER_ID = "6aace061972e326f8fef7aae"  # Testing Company, I01-00014
RUN = str(int(time.time()))[-6:]


def baseline(n):
    return {
        "installerId": TEST_INSTALLER_ID, "activityType": "heating_cooling", "customerType": "residential",
        "methodOfLeadGeneration": "Customer initiated contact", "ownReference": f"BVM-{RUN}-{n}",
        "installationDate": "2026-12-10",
        "customer": {"name": f"Boundary Test {n}", "email": f"boundary.test.{RUN}.{n}@yopmail.com",
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
    count_before_all = c.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["total"]

    n = 0
    CASES = []  # (field, label, value)

    CASES += [("address.postcode", lbl, v) for lbl, v in [
        ("valid NSW min 2000", "2000"), ("1999 (below NSW range)", "1999"),
        ("valid NSW max 2999", "2999"), ("3000 (VIC, above NSW range)", "3000"),
        ("0000", "0000"), ("length 3 (200)", "200"), ("length 5 (20000)", "20000"),
        ("empty string", ""), ("whitespace", "   "), ("null", None), ("omitted", "__OMIT__"),
        ("leading zero valid-looking", "02000"), ("non-numeric", "abcd"),
        ("float-looking", "2000.5"), ("negative", "-2000"), ("as integer type", 2000),
        ("emoji", "🙂🙂🙂🙂"), ("sql-ish", "2000' OR '1'='1"),
    ]]

    CASES += [("customer.abnAcn", lbl, v) for lbl, v in [
        ("valid ABN (checksum-correct)", "33102417032"), ("valid ACN, 9 digits", "004085616"),
        ("10 digits (min-1 for ABN)", "3310241703"), ("12 digits (max+1)", "331024170321"),
        ("all zeros", "00000000000"), ("checksum-invalid 11 digits", "12345678901"),
        ("with spaces", "33 102 417 032"), ("with dashes", "33-102-417-032"),
        ("empty string", ""), ("null", None), ("omitted", "__OMIT__"),
        ("letters", "ABCDEFGHIJK"), ("unicode digits", "３３１０２４１７０３２"),
    ]]

    CASES += [("customer.phoneNumber", lbl, v) for lbl, v in [
        ("valid 9-digit mobile", "412345678"), ("8 digits (min-1)", "41234567"),
        ("10 digits (max+1)", "4123456789"), ("leading zero + 9 digits", "0412345678"),
        ("with +61 prefix inline", "+61412345678"), ("all zeros", "000000000"),
        ("landline-looking 02", "0298765432"), ("empty string", ""), ("whitespace", "   "),
        ("null", None), ("omitted", "__OMIT__"), ("letters", "abcdefghi"),
        ("with spaces", "412 345 678"), ("scientific notation", "4.12e8"),
        ("as integer type", 412345678),
    ]]

    CASES += [("customer.email", lbl, v) for lbl, v in [
        ("valid", f"boundary.valid.{RUN}@yopmail.com"), ("no TLD", f"boundary.{RUN}@yopmail"),
        ("no @", f"boundary.{RUN}.yopmail.com"), ("double dot local", f"a..b.{RUN}@yopmail.com"),
        ("leading dot local", f".a.{RUN}@yopmail.com"), ("empty string", ""), ("whitespace only", "   "),
        ("null", None), ("omitted", "__OMIT__"), ("very long local part (80 chars)", "a" * 80 + f"{RUN}@yopmail.com"),
        ("unicode domain", f"boundary.{RUN}@yöpmail.com"), ("plus-addressing", f"boundary+tag.{RUN}@yopmail.com"),
        ("trailing space", f"boundary.{RUN}@yopmail.com "), ("uppercase", f"BOUNDARY.{RUN}@YOPMAIL.COM"),
    ]]

    CASES += [("installationDate", lbl, v) for lbl, v in [
        ("valid future date", "2026-12-15"), ("leap day valid", "2028-02-29"),
        ("leap day invalid (non-leap year)", "2027-02-29"), ("April 31 (no such day)", "2026-04-31"),
        ("month 13", "2026-13-01"), ("month 00", "2026-00-01"), ("day 00", "2026-01-00"),
        ("far past", "1900-01-01"), ("epoch", "1970-01-01"), ("far future", "9999-12-31"),
        ("empty string", ""), ("null", None), ("omitted", "__OMIT__"),
        ("wrong format DD-MM-YYYY", "15-12-2026"), ("datetime with time", "2026-12-15T00:00:00.000Z"),
        ("non-date string", "not-a-date"), ("as integer (epoch ms)", 1798934400000),
    ]]

    CASES += [("customer.name", lbl, v) for lbl, v in [
        ("valid", "Boundary Valid Name"), ("empty string", ""), ("whitespace only", "   "),
        ("null", None), ("omitted", "__OMIT__"), ("1 char", "A"),
        ("very long (500 chars)", "Long Name " * 50), ("emoji", "🙂 Test"),
        ("null byte", "Test\u0000Name"), ("html/script", "<script>alert(1)</script>"),
        ("digits only", "123456"), ("leading/trailing spaces", "  Padded Name  "),
    ]]

    CASES += [("equipmentQuoted.0.coolingCapacityKw", lbl, v) for lbl, v in [
        ("valid", 6), ("zero", 0), ("negative", -5), ("very large", 999999),
        ("string number", "6"), ("null", None), ("float", 6.5),
        ("scientific notation", "1e3"), ("NaN string", "NaN"), ("Infinity string", "Infinity"),
    ]]
    CASES += [("ownReference", lbl, v) for lbl, v in [
        ("valid", f"REF-{RUN}"), ("empty string", ""), ("null", None), ("omitted", "__OMIT__"),
        ("very long (600 chars)", "X" * 600), ("null byte", "REF\u0000X"),
    ]]

    for field, label, value in CASES:
        n += 1
        body = baseline(n)
        if value == "__OMIT__":
            parts = field.split(".")
            d = body
            for p in parts[:-1]:
                d = d[p]
            del d[parts[-1]]
        else:
            body = set_path(body, field, value)
        r = c.post("/api/v1/jobs", data=body)
        rec = {"n": n, "field": field, "label": label, "value": repr(value)[:60], "status": r.status}
        try:
            j = r.json()
        except Exception:
            j = {"raw": r.text()[:200]}
        rec["response"] = json.dumps(j)[:350]
        if r.status < 300:
            job = j["data"]["job"]
            rec["jobNumber"] = job["jobNumber"]
            detail = c.get(f"/api/v1/jobs/{job['id']}").json()["data"]["job"]
            rec["stored"] = json.dumps(detail)[:600]
        results.append(rec)
        status_tag = "OK " if r.status < 300 else "ERR"
        print(f"[{n:3}] {status_tag} {field:35} {label:38} -> {r.status}  {rec.get('jobNumber','')}")

    count_after_all = c.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["total"]
    created = sum(1 for x in results if x["status"] < 300)
    print(f"\ncount before={count_before_all} after={count_after_all} delta={count_after_all - count_before_all} created(2xx)={created}")

    with open(r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\round8_boundary_matrix_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)
    c.dispose()

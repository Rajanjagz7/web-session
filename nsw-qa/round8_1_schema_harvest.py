"""STEP 1: harvest the full POST /v1/jobs field schema from Zod validation errors
(empty body -> every required-field error in one response), then get the test
installer's site-inspection member id."""
import sys, json
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
from config import EMAIL, PASSWORD
from playwright.sync_api import sync_playwright

BASE_URL = "https://nswstage.rebatem8.com.au"
TEST_INSTALLER_ID = "6aace061972e326f8fef7aae"  # "Testing Company", I01-00014

with sync_playwright() as p:
    c = p.request.new_context(base_url=BASE_URL, timeout=20_000)
    c.post("/api/v1/auth/admin/login", data={"email": EMAIL, "password": PASSWORD})

    r = c.post("/api/v1/jobs", data={})
    print("POST /jobs {} ->", r.status)
    print(json.dumps(r.json(), indent=1))

    print("\n-- installer members (for siteInspectionInstallerId) --")
    m = c.get(f"/api/v1/installers/{TEST_INSTALLER_ID}/members").json()
    print(json.dumps(m, indent=1)[:800])

    print("\n-- baseline valid job (minimal, from round 6 shape) --")
    r2 = c.post("/api/v1/jobs", data={
        "installerId": TEST_INSTALLER_ID,
        "activityType": "heating_cooling",
        "customerType": "residential",
        "methodOfLeadGeneration": "Customer initiated contact",
        "installationDate": "2026-12-01",
        "customer": {"name": "Schema Probe", "email": "schema.probe@yopmail.com",
                     "phoneNumber": "400000001", "countryCode": "+61", "flagCode": "AU"},
        "address": {"fullAddress": "1 George St, Sydney NSW 2000, Australia", "isManual": False,
                    "streetNumber": "1", "streetName": "George", "streetType": "Street",
                    "suburb": "Sydney", "state": "NSW", "postcode": "2000"},
        "createdFrom": "add_job",
    })
    print(r2.status, json.dumps(r2.json())[:600])
    c.dispose()

import sys, json
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
from config import EMAIL, PASSWORD
from playwright.sync_api import sync_playwright

BASE_URL = "https://nswstage.rebatem8.com.au"
TEST_INSTALLER_ID = "6aace061972e326f8fef7aae"

with sync_playwright() as p:
    c = p.request.new_context(base_url=BASE_URL, timeout=20_000)
    c.post("/api/v1/auth/admin/login", data={"email": EMAIL, "password": PASSWORD})

    base = {
        "installerId": TEST_INSTALLER_ID, "activityType": "heating_cooling", "customerType": "residential",
        "customer": {}, "address": {}, "equipmentQuoted": [{}],
    }
    r = c.post("/api/v1/jobs", data=base)
    print("nested empty objects ->", r.status)
    print(json.dumps(r.json(), indent=1))

    print("\n-- small_business customerType (different customer shape) --")
    base2 = dict(base); base2["customerType"] = "small_business"; base2["customer"] = {}
    r2 = c.post("/api/v1/jobs", data=base2)
    print(r2.status, json.dumps(r2.json(), indent=1)[:1500])

    print("\n-- hot_water_heat_pump activityType (systemType / different equip shape) --")
    base3 = dict(base); base3["activityType"] = "hot_water_heat_pump"
    r3 = c.post("/api/v1/jobs", data=base3)
    print(r3.status, json.dumps(r3.json(), indent=1)[:1500])

    print("\n-- extra unknown top-level field --")
    ok = {
        "installerId": TEST_INSTALLER_ID, "activityType": "heating_cooling", "customerType": "residential",
        "methodOfLeadGeneration": "Customer initiated contact", "installationDate": "2026-12-02",
        "customer": {"name": "Schema Probe 2", "email": "schema.probe2@yopmail.com",
                     "phoneNumber": "400000002", "countryCode": "+61", "flagCode": "AU"},
        "address": {"fullAddress": "1 George St, Sydney NSW 2000, Australia", "streetNumber": "1",
                    "streetName": "George", "streetType": "Street", "suburb": "Sydney", "state": "NSW", "postcode": "2000"},
        "createdFrom": "add_job", "totallyMadeUpField": "x", "escValue": 999999, "status": "photos_complete",
    }
    r4 = c.post("/api/v1/jobs", data=ok)
    print(r4.status, json.dumps(r4.json())[:700])
    c.dispose()

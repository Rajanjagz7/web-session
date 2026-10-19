import sys, json
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
from config import EMAIL, PASSWORD
from playwright.sync_api import sync_playwright

BASE_URL = "https://nswstage.rebatem8.com.au"

with sync_playwright() as p:
    c = p.request.new_context(base_url=BASE_URL, timeout=20_000)
    c.post("/api/v1/auth/admin/login", data={"email": EMAIL, "password": PASSWORD})
    before = c.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["total"]

    print("-- array body on object endpoint --")
    r = c.post("/api/v1/jobs", data="[]", headers={"content-type": "application/json"})
    print(r.status, r.text()[:250])

    print("\n-- malformed JSON: trailing comma --")
    r = c.post("/api/v1/jobs", data='{"installerId":"x",}', headers={"content-type": "application/json"})
    print(r.status, r.text()[:250])

    print("\n-- malformed JSON: unquoted key --")
    r = c.post("/api/v1/jobs", data='{installerId:"x"}', headers={"content-type": "application/json"})
    print(r.status, r.text()[:250])

    print("\n-- malformed JSON: line break inside string --")
    r = c.post("/api/v1/jobs", data='{"installerId":"x\ny"}', headers={"content-type": "application/json"})
    print(r.status, r.text()[:250])

    print("\n-- wrong Content-Type (text/plain) with valid JSON body --")
    r = c.post("/api/v1/jobs", data='{"installerId":"x"}', headers={"content-type": "text/plain"})
    print(r.status, r.text()[:250])

    print("\n-- 0-byte body, Content-Length 0 --")
    r = c.post("/api/v1/jobs", data="", headers={"content-type": "application/json"})
    print(r.status, r.text()[:250])

    print("\n-- duplicate keys (last-wins is standard JSON parser behaviour, just confirming) --")
    r = c.post("/api/v1/jobs", data='{"installerId":"aaaaaaaaaaaaaaaaaaaaaaaa","installerId":"bbbbbbbbbbbbbbbbbbbbbbbb"}',
                headers={"content-type": "application/json"})
    print(r.status, r.text()[:300])

    after = c.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["total"]
    print(f"\ncount before={before} after={after} delta={after-before} (every case above should be 4xx, count must be unchanged)")
    c.dispose()

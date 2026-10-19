"""STEP 2 protocol on POST /v1/notes, API-only (headless, fast, no flaky UI editor).
Uses the field shape already confirmed from the UI-created note:
{entityType, entityId, note (HTML string), visibility, attachments:[]}."""
import sys, json
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
from config import EMAIL, PASSWORD
from playwright.sync_api import sync_playwright

BASE_URL = "https://nswstage.rebatem8.com.au"
JOB_ID = "6ab24e097541fdf3f7a498fc"  # M8N000071

with sync_playwright() as p:
    c = p.request.new_context(base_url=BASE_URL, timeout=20_000)
    c.post("/api/v1/auth/admin/login", data={"email": EMAIL, "password": PASSWORD})

    def notes_total():
        return c.get(f"/api/v1/notes?entityType=job&entityId={JOB_ID}&skip=0&limit=50").json()["data"]["total"]

    before = notes_total()
    print("count before:", before)

    print("\n-- invalid-value checks (expect 400, no note created) --")
    cases = [
        ("missing note text", {"entityType": "job", "entityId": JOB_ID, "visibility": "internal"}),
        ("missing entityId", {"entityType": "job", "note": "<p>x</p>", "visibility": "internal"}),
        ("invalid entityType enum", {"entityType": "banana", "entityId": JOB_ID, "note": "<p>x</p>", "visibility": "internal"}),
        ("invalid visibility enum", {"entityType": "job", "entityId": JOB_ID, "note": "<p>x</p>", "visibility": "banana"}),
        ("entityId wrong length", {"entityType": "job", "entityId": "not-an-id", "note": "<p>x</p>", "visibility": "internal"}),
        ("entityId well-formed but unknown job", {"entityType": "job", "entityId": "000000000000000000000000", "note": "<p>x</p>", "visibility": "internal"}),
        ("empty note html", {"entityType": "job", "entityId": JOB_ID, "note": "<p></p>", "visibility": "internal"}),
        ("note as number not string", {"entityType": "job", "entityId": JOB_ID, "note": 12345, "visibility": "internal"}),
    ]
    for label, body in cases:
        r = c.post("/api/v1/notes", data=body)
        print(f"  {label:38} -> {r.status} {json.dumps(r.json())[:220]}")

    after_negative = notes_total()
    print(f"\ncount after negative cases: {after_negative} (expected same as before={before})")

    print("\n-- valid create + read-back + count check --")
    import time
    text = f"API regression check {int(time.time())} - safe to delete"
    r = c.post("/api/v1/notes", data={"entityType": "job", "entityId": JOB_ID,
                                       "note": f"<p>{text}</p>", "visibility": "internal", "attachments": []})
    print("create ->", r.status, json.dumps(r.json())[:400])
    after_create = notes_total()
    print(f"count after create: {after_create} (expected {before + 1})")

    listing = c.get(f"/api/v1/notes?entityType=job&entityId={JOB_ID}&skip=0&limit=50").json()["data"]["notes"]
    match = [n for n in listing if text in n.get("note", "")]
    print("read-back match:", json.dumps(match, indent=1)[:900] if match else "NOT FOUND")

    print("\n-- XSS in note body: is it stored raw or sanitised? --")
    xss = "<img src=x onerror=alert(1)>"
    r = c.post("/api/v1/notes", data={"entityType": "job", "entityId": JOB_ID,
                                       "note": f"<p>{xss} marker-{int(time.time())}</p>", "visibility": "internal"})
    if r.status < 300:
        nid = r.json().get("data", {}).get("id") or r.json().get("data", {}).get("note", {}).get("id")
        listing2 = c.get(f"/api/v1/notes?entityType=job&entityId={JOB_ID}&skip=0&limit=50").json()["data"]["notes"]
        stored = next((n for n in listing2 if "marker-" in n.get("note", "")), None)
        print("stored raw:", json.dumps(stored.get("note")) if stored else "NOT FOUND")
    else:
        print("rejected:", r.status, r.text()[:200])

    c.dispose()

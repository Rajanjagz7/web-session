"""Delete exactly one known boundary-test job (M8N000208, the XSS-name check job)
via the UI, capturing the real DELETE request body/response, then confirm via
API whether it's a soft delete (isDeleted flag, still fetchable) or hard delete
(404/gone, and does it disappear from jobs count)."""
import sys, re, json
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
import helpers as h
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    page = b.new_page(base_url="https://nswstage.rebatem8.com.au")
    page.set_default_timeout(20000)
    calls = []
    page.on("request", lambda r: calls.append((r.method, r.url.split("/api/v1")[-1], r.post_data))
            if "/api/v1/jobs" in r.url and r.method == "DELETE" else None)
    responses = []
    page.on("response", lambda r: responses.append((r.status, r.text()[:400]))
            if "/api/v1/jobs" in r.url and r.request.method == "DELETE" else None)

    h.login(page)
    before_total = page.request.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["total"]
    job_before = page.request.get("/api/v1/jobs?skip=0&limit=1&search=M8N000208").json()["data"]["jobs"][0]
    job_id = job_before["id"]

    page.goto("/jobs")
    page.wait_for_timeout(1500)
    page.locator("table tbody tr").first.locator('input[type="checkbox"]').check()
    page.wait_for_timeout(500)
    page.get_by_role("button", name="Delete", exact=True).click()
    page.wait_for_timeout(1000)
    page.screenshot(path=r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\dbg-delete-confirm.png", full_page=True)
    print("confirm dialog text:", page.locator("body").inner_text()[-800:])

    # look for a Confirm/Yes/Delete button in a confirmation modal
    confirm_btn = page.get_by_role("button", name=re.compile(r"^(confirm|yes|delete)$", re.I)).last
    confirm_btn.click()
    page.wait_for_timeout(2500)
    page.screenshot(path=r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\dbg-delete-after.png", full_page=True)
    b.close()

print("\nDELETE calls:")
for m, u, d in calls:
    print(" ", m, u, "body:", (d or "")[:300])
print("\nDELETE responses:")
for s, t in responses:
    print(" ", s, t)

# verify via API
import sys as _s
_s.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
from config import EMAIL, PASSWORD
with sync_playwright() as p:
    c = p.request.new_context(base_url="https://nswstage.rebatem8.com.au", timeout=20000)
    c.post("/api/v1/auth/admin/login", data={"email": EMAIL, "password": PASSWORD})
    after_total = c.get("/api/v1/jobs?skip=0&limit=1").json()["data"]["total"]
    detail = c.get(f"/api/v1/jobs/{job_id}")
    still_in_list = c.get("/api/v1/jobs?skip=0&limit=1&search=M8N000208").json()["data"]["total"]
    print(f"\ntotal before={before_total} after={after_total} delta={after_total-before_total}")
    print("GET by id after delete ->", detail.status, detail.text()[:300])
    print("still findable via search ->", still_in_list, "results")
    c.dispose()

"""Read-only probe of the impersonation endpoint's INPUT VALIDATION only - never
supplies a real installer/user id, so no impersonation session is actually created."""
import sys, json
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
from config import BASE_URL, EMAIL, PASSWORD
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    ctx = p.request.new_context(base_url=BASE_URL, timeout=20_000)
    ctx.post("/api/v1/auth/admin/login", data={"email": EMAIL, "password": PASSWORD})

    for body in [{}, {"userId": "000000000000000000000000"}, {"userId": "not-an-id"},
                 {"companyId": "000000000000000000000000"}]:
        r = ctx.post("/api/v1/auth/bypass-login", data=body)
        try:
            j = r.json()
        except Exception:
            j = r.text()[:200]
        print(f"POST bypass-login body={body} -> {r.status} {json.dumps(j)[:300]}")

    r = ctx.post("/api/v1/auth/exit-impersonation")
    print("exit-impersonation (not impersonating) ->", r.status, r.text()[:200])
    ctx.dispose()

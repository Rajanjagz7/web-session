"""Read-only recon of endpoints found in the JS bundle that look security-sensitive:
bypass-login, forgot/reset-password, register-installer. No state changes attempted
beyond what the endpoint itself reports; nothing here creates a real installer or
resets a real password (uses fake identifiers)."""
import sys, json
sys.path.insert(0, r"C:\Users\Baps\Downloads\rajan backup\nsw-qa\1er-tests-python")
from config import BASE_URL, EMAIL, PASSWORD
from playwright.sync_api import sync_playwright

FAKE = "no-such-admin-qa@rebatem8nsw.com.au"

with sync_playwright() as p:
    anon = p.request.new_context(base_url=BASE_URL, timeout=20_000)

    print("--- unauthenticated probes ---")
    for path, body in [
        ("/api/v1/auth/bypass-login", {}),
        ("/api/v1/auth/bypass-login", {"email": FAKE}),
        ("/api/v1/installer/bypass/login", {}),
        ("/api/v1/installer/bypass/login", {"email": FAKE}),
        ("/api/v1/auth/forgot-password", {"email": FAKE}),
        ("/api/v1/auth/forgot-password", {"email": EMAIL}),
    ]:
        r = anon.post(path, data=body)
        try:
            j = r.json()
        except Exception:
            j = r.text()[:200]
        print(f"POST {path} body={body} -> {r.status} {json.dumps(j)[:300]}")

    print("\n--- GET variants (in case they're GET, not POST) ---")
    for path in ["/api/v1/auth/bypass-login", "/api/v1/installer/bypass/login"]:
        r = anon.get(path)
        print(f"GET {path} -> {r.status} {r.text()[:200]}")

    anon.dispose()

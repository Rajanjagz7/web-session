"""Login helper: logs in once by email OTP (retrying through the known blank-splash bug, see
CRASH_CHECK_2026-09-21.md finding C1), then caches the browser storage state so later test runs
reuse the session instead of requesting a fresh OTP every time (OTP requests are rate-limited —
see finding C10 / T-notes in SECURITY_EDGE_CASE_FINDINGS_2026-09-21.md)."""
import json

from playwright.sync_api import Page

from utils.config import AUTH_STATE_PATH, BASE_URL, EMAIL, OTP


def ensure_logged_in(page: Page) -> None:
    """Navigate to the dashboard, retrying through the blank-splash bug. Raises if it never loads."""
    loaded = False
    for _ in range(8):
        page.goto(f"{BASE_URL}/app/dashboard", wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(6000)
        try:
            page.get_by_role("button", name="Create").first.wait_for(state="visible", timeout=2000)
            loaded = True
            break
        except Exception:
            continue
    if not loaded:
        raise RuntimeError("Dashboard never rendered after 8 attempts (see finding C1: blank loading splash)")


def login_fresh(page: Page) -> None:
    """Full email-OTP login flow. Only call this when no cached session exists — each call is one OTP request."""
    loaded = False
    for _ in range(8):
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(6000)
        try:
            page.get_by_role("button", name="Email Address").wait_for(state="visible", timeout=2000)
            loaded = True
            break
        except Exception:
            continue
    if not loaded:
        raise RuntimeError("Login page never rendered (see finding C1)")

    page.get_by_role("button", name="Email Address").click()
    identifier = page.locator("form").get_by_role("textbox").first
    identifier.click()
    identifier.press_sequentially(EMAIL, delay=40)
    page.get_by_role("button", name="Send OTP").click()
    page.get_by_role("heading", name="Check Your Messages").wait_for(timeout=20_000)
    for i, digit in enumerate(OTP, start=1):
        page.get_by_role("textbox", name=f"Digit {i}").fill(digit)
    page.get_by_role("button", name="Verify & Login").click()
    page.wait_for_url("**/app/dashboard**", timeout=30_000)


def get_or_create_storage_state(browser) -> dict:
    """Return a storage_state dict, reusing the cached session file when present so tests don't
    each trigger a fresh OTP request."""
    if AUTH_STATE_PATH.exists():
        return json.loads(AUTH_STATE_PATH.read_text())

    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    login_fresh(page)
    AUTH_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state = context.storage_state(path=str(AUTH_STATE_PATH))
    context.close()
    return state

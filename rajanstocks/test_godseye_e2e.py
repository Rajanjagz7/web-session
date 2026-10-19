"""
E2E Playwright Tests for GOD'S EYE — The Observer (v1.0)
Tests UI interactions, accessibility compliance (WCAG 2.2 AA, touch targets >= 44px),
multi-horizon switching, signal inspection modal, forecast history, and model health.
"""
import os
import subprocess
import time
import pytest
from playwright.sync_api import sync_playwright

SERVER_PORT = 8877
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"

@pytest.fixture(scope="module")
def live_server():
    """Starts the Rajan Algo FastAPI server in a background process."""
    cmd = [
        "python", "-m", "uvicorn", "server:app",
        "--host", "127.0.0.1",
        "--port", str(SERVER_PORT),
        "--log-level", "warning"
    ]
    cwd = os.path.join(os.getcwd(), "rajanstocks")
    proc = subprocess.Popen(cmd, cwd=cwd)
    # Wait for server to warm up
    time.sleep(3.5)
    yield SERVER_URL
    proc.terminate()
    proc.wait()

def test_godseye_ui_full_e2e(live_server):
    os.makedirs("test-results/godseye", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        # 1. Navigate to main page and wait for boot
        page.goto(live_server)
        page.wait_for_selector("#boot", state="detached", timeout=25000)

        # Navigate to God's Eye via nav button or go('godseye')
        page.evaluate("go('godseye')")
        page.wait_for_selector("#v-godseye.on", timeout=10000)
        page.wait_for_selector(".ge-card", timeout=10000)

        # Capture initial Overview screenshot
        page.screenshot(path="test-results/godseye/01-godseye-overview.png")

        # 2. Verify Brand, Demo Label and Disclaimer (PM-032)
        assert page.locator("h2:has-text(\"GOD'S EYE\")").is_visible()
        assert page.locator("text=DEMO — MOCK DATA").is_visible()
        assert page.locator(".ge-disclaimer").is_visible()
        disclaimer_text = page.locator(".ge-disclaimer").inner_text()
        assert "guarantee" in disclaimer_text.lower() or "certainty" in disclaimer_text.lower()

        # 3. Verify Accessibility: minimum touch target CSS px >= 44px (PM-031 / WCAG 2.2 AA)
        pills = page.locator(".ge-pill")
        count = pills.count()
        assert count == 4, f"Expected 4 horizon pills, got {count}"
        for i in range(count):
            box = pills.nth(i).bounding_box()
            assert box["height"] >= 43.5, f"Touch target height {box['height']}px < 44px minimum!"

        # 4. Verify Horizon Switching
        pills.nth(1).click() # Click INTRADAY_15M
        page.wait_for_timeout(800)
        page.screenshot(path="test-results/godseye/02-horizon-15m.png")
        assert pills.nth(1).get_attribute("aria-checked") == "true"

        # 5. Verify Signal Details Modal (PM-02)
        details_btn = page.locator(".ge-btn-details").first
        details_btn.click()
        page.wait_for_selector(".ge-modal-card", timeout=5000)
        page.screenshot(path="test-results/godseye/03-signal-audit-modal.png")
        assert page.locator("text=Signal Audit:").is_visible()
        assert page.locator("text=Deterministic Invalidation Conditions").is_visible()
        # Close modal
        page.locator(".ge-close-btn").click()
        page.wait_for_timeout(400)

        # 6. Verify Forecast Ledger & History Tab (PM-03)
        page.locator("button:has-text(\"Forecast Ledger\")").click()
        page.wait_for_selector(".ge-table tbody tr", timeout=8000)
        page.screenshot(path="test-results/godseye/04-forecast-ledger.png")
        rows = page.locator(".ge-table tbody tr")
        assert rows.count() > 0

        # 7. Verify System & Model Health Tab (PM-04 & PM-037 security)
        page.locator("button:has-text(\"System & Model Health\")").click()
        page.wait_for_selector(".ge-health-grid", timeout=5000)
        page.screenshot(path="test-results/godseye/05-system-health.png")
        assert page.locator("text=ZERO CREDENTIALS EXPOSED").is_visible()
        assert page.locator("text=Operational Status").is_visible()

        browser.close()

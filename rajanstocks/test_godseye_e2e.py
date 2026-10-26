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
    cwd = os.path.dirname(os.path.abspath(__file__))
    proc = subprocess.Popen(cmd, cwd=cwd)
    # Wait for server to warm up
    time.sleep(3.5)
    yield SERVER_URL
    proc.terminate()
    proc.wait()

@pytest.mark.skip(reason="asserts the removed 'DEMO - MOCK DATA' mode and fixed BEARISH NIFTY; God's Eye is now live data (covered by test_gods_eye.py)")
def test_godseye_ui_full_e2e(live_server):
    os.makedirs("test-results/godseye", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
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

        # 2. Verify Brand, Demo Label, Disclaimer, and Index-only Universe
        assert page.locator("h2:has-text(\"GOD'S EYE\")").is_visible()
        assert page.locator("text=DEMO — MOCK DATA").is_visible()
        assert page.locator(".ge-disclaimer").is_visible()
        disclaimer_text = page.locator(".ge-disclaimer").inner_text()
        assert "guarantee" in disclaimer_text.lower() or "certainty" in disclaimer_text.lower()

        # Verify ONLY Indices are present in God's Eye
        card_titles = page.locator(".ge-sym").all_inner_texts()
        assert "NIFTY" in card_titles
        assert "BANKNIFTY" in card_titles
        assert "FINNIFTY" in card_titles
        assert "SENSEX" in card_titles
        assert "RELIANCE" not in card_titles
        assert "TCS" not in card_titles

        # Verify NIFTY is BEARISH with real downward momentum & OI stats
        nifty_card = page.locator(".ge-card:has(.ge-sym:has-text(\"NIFTY\"))").first
        n_text = nifty_card.inner_text().upper()
        assert "BEARISH" in n_text
        assert "PCR" in n_text
        assert "RESISTANCE" in n_text
        assert "SUPPORT" in n_text

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
        # Close modal and verify touch target >= 44px (PM-031 / WCAG 2.2 AA)
        close_btn = page.locator(".ge-close-btn")
        c_box = close_btn.bounding_box()
        assert c_box["height"] >= 43.5 and c_box["width"] >= 43.5, f"Close btn touch target {c_box['width']}x{c_box['height']} < 44px!"
        close_btn.click()
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
        assert page.locator("text=Chronological Out-of-Sample Evaluation").is_visible()
        assert page.locator("text=Exchange Calendar & Session Boundary").is_visible()

        # 8. Verify Mobile Responsive Screen (PM-031 <= 767px mobileMax)
        mobile_page = browser.new_page(viewport={"width": 390, "height": 844})
        mobile_page.goto(live_server)
        mobile_page.wait_for_selector("#boot", state="detached", timeout=25000)
        mobile_page.evaluate("go('godseye')")
        mobile_page.wait_for_selector("#v-godseye.on", timeout=10000)
        mobile_page.wait_for_selector(".ge-card", timeout=10000)
        mobile_page.screenshot(path="test-results/godseye/06-mobile-view.png")
        assert mobile_page.locator(".ge-card").count() > 0
        mobile_page.close()

        # 9. Verify Today's Picks: Indices placed strictly first with Option Premium levels
        page.evaluate("go('picks')")
        page.wait_for_selector("#v-picks.on", timeout=10000)
        page.wait_for_selector(".pk-grid .pk", timeout=10000)

        # Verify index card is visible with Option Premium levels
        idx_pick = page.locator(".pk:has-text(\"Major Benchmark Index\")").first
        assert idx_pick.is_visible()
        idx_pick.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.screenshot(path="test-results/godseye/07-picks-all-indices-first.png")

        pk_sym = idx_pick.locator(".pk-t b").inner_text()
        assert pk_sym in ("NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "MIDCPNIFTY")
        pk_text = idx_pick.inner_text().upper()
        assert "OPTION PREMIUM LEVELS" in pk_text
        assert "PREMIUM ENTRY" in pk_text
        assert "PREMIUM SL" in pk_text
        assert "PREMIUM T1" in pk_text
        assert "UNDERLYING SPOT" in pk_text

        # 10. Verify Swing horizon selection retains indices first with Swing Option Premium
        page.locator("[data-pkf=\"hz:SWING\"]").click()
        page.wait_for_timeout(800)
        swing_idx_pick = page.locator(".pk:has-text(\"Major Benchmark Index\")").first
        assert swing_idx_pick.is_visible()
        swing_idx_pick.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.screenshot(path="test-results/godseye/08-picks-swing-option-premium.png")

        swing_text = swing_idx_pick.inner_text().upper()
        assert "SWING" in swing_text
        assert "PREMIUM ENTRY" in swing_text

        # 11. Verify Positional horizon selection retains indices first with Positional Option Premium
        page.locator("[data-pkf=\"hz:POS\"]").click()
        page.wait_for_timeout(800)
        pos_idx_pick = page.locator(".pk:has-text(\"Major Benchmark Index\")").first
        assert pos_idx_pick.is_visible()
        pos_idx_pick.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.screenshot(path="test-results/godseye/09-picks-positional-option-premium.png")

        pos_text = pos_idx_pick.inner_text().upper()
        assert "POSITIONAL" in pos_text
        assert "PREMIUM ENTRY" in pos_text

        browser.close()

"""
Selenium script — OzMed Sign-in Page
Clicks the "Create an account" button on a React SPA.

The page source is a bare <div id="root"> shell; all UI is injected by
JavaScript.  The script therefore waits for React to finish rendering
before it tries to locate the button.

Install dependencies:
    pip install selenium webdriver-manager

Run:
    python selenium_click_create_account.py
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://practice2.dev.ozmed.health/"

# ── XPath strategies tried in order ──────────────────────────────────────────
# React components often wrap text in <span> children, so we check both the
# element itself and any descendant that carries the text.
XPATHS = [
    # Exact text on the element
    "//*[normalize-space(text())='Create an account']",
    # Exact text anywhere inside (covers <button><span>Create an account</span></button>)
    "//*[normalize-space(.)='Create an account']",
    # Partial match — last resort
    "//*[contains(text(),'Create an account')]",
    "//*[contains(.,'Create an account') and (self::button or self::a)]",
]


def wait_for_react(driver: webdriver.Chrome, timeout: int = 15) -> None:
    """Block until React has mounted at least one child inside #root."""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script(
            "const root = document.getElementById('root');"
            "return root && root.children.length > 0;"
        )
    )


def click_create_account() -> None:
    # ── Browser setup ─────────────────────────────────────────────────────────
    options = Options()
    # options.add_argument("--headless=new")   # ← uncomment for headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    wait = WebDriverWait(driver, 15)

    try:
        # ── 1. Open the page ──────────────────────────────────────────────────
        print(f"[1/4] Navigating to {URL}")
        driver.get(URL)

        # ── 2. Wait for React to hydrate ──────────────────────────────────────
        print("[2/4] Waiting for React to mount …")
        wait_for_react(driver)
        print("      React root has children — page is ready.")

        # ── 3. Locate the button ──────────────────────────────────────────────
        print("[3/4] Searching for 'Create an account' element …")
        element = None
        for xpath in XPATHS:
            try:
                element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                print(f"      Found via XPath: {xpath}")
                print(f"      Tag={element.tag_name!r}  Text={element.text!r}")
                break
            except Exception:
                continue

        if element is None:
            raise RuntimeError(
                "Could not locate 'Create an account' after trying all XPath strategies.\n"
                "Tip: open DevTools on the page, find the element, and add its specific "
                "selector to the XPATHS list at the top of this script."
            )

        # ── 4. Click ──────────────────────────────────────────────────────────
        print("[4/4] Clicking …")
        # Scroll into view first (helps on smaller viewports)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.3)   # brief pause after scroll
        element.click()
        print("✅  Clicked 'Create an account'")

        # ── Post-click verification ───────────────────────────────────────────
        time.sleep(2)
        print(f"\n--- Result ---")
        print(f"Current URL : {driver.current_url}")
        print(f"Page title  : {driver.title}")

    except Exception as exc:
        screenshot = "error_screenshot.png"
        driver.save_screenshot(screenshot)
        print(f"\n❌ Error: {exc}")
        print(f"   Screenshot saved → {screenshot}")
        raise

    finally:
        driver.quit()
        print("\nBrowser closed.")


if __name__ == "__main__":
    click_create_account()

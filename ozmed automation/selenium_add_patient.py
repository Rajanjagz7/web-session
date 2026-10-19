"""
Selenium script — OzMed: Login → Patients → Click Add Patient

Steps:
  1. Navigate to OzMed
  2. Log in with email + password
  3. Enter bypass/PIN code if prompted
  4. Navigate to the Patients section
  5. Click the Add Patient button

Install:
    pip install selenium webdriver-manager

Run:
    python selenium_add_patient.py
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

URL           = "https://practice2.dev.ozmed.health/"
EMAIL         = "fep5@yopmail.com"
PASSWORD      = "Test@1234"
BYPASS_CODE   = "489567"


# ── Helpers ───────────────────────────────────────────────────────────────────

def wait_for_react(driver, timeout=15):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script(
            "const r = document.getElementById('root'); return r && r.children.length > 0;"
        )
    )


def find_and_fill(driver, xpaths, value, timeout=8):
    for xpath in xpaths:
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.clear()
            el.send_keys(value)
            return el
        except Exception:
            continue
    return None


def find_and_click(driver, xpaths, timeout=8):
    for xpath in xpaths:
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(0.2)
            el.click()
            return el
        except Exception:
            continue
    return None


def click_by_text(driver, *texts, timeout=8):
    for text in texts:
        result = find_and_click(driver, [
            f"//button[contains(normalize-space(.),'{text}')]",
            f"//a[contains(normalize-space(.),'{text}')]",
            f"//*[@role='button' and contains(normalize-space(.),'{text}')]",
            f"//*[contains(@class,'btn') and contains(normalize-space(.),'{text}')]",
        ], timeout=timeout)
        if result:
            print(f"      Clicked: '{text}'")
            return text
    return None


# ── Main flow ─────────────────────────────────────────────────────────────────

def run():
    options = Options()
    # options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )

    try:
        # ── 1. Navigate ───────────────────────────────────────────────────────
        print(f"[1] Navigating to {URL}")
        driver.get(URL)
        wait_for_react(driver)
        print(f"    Page ready — {driver.title}")

        # ── 2. Fill email ─────────────────────────────────────────────────────
        print(f"[2] Entering email: {EMAIL}")
        find_and_fill(driver, [
            "//input[@type='email']",
            "//input[contains(@name,'email')]",
            "//input[contains(@id,'email')]",
            "//input[contains(@placeholder,'email') or contains(@placeholder,'Email')]",
        ], EMAIL)

        # ── 3. Fill password ──────────────────────────────────────────────────
        print(f"[3] Entering password")
        find_and_fill(driver, [
            "//input[@type='password']",
            "//input[contains(@name,'password')]",
            "//input[contains(@id,'password')]",
            "//input[contains(@placeholder,'assword')]",
        ], PASSWORD)

        # ── 4. Click Sign in / Login ──────────────────────────────────────────
        print(f"[4] Clicking Sign in")
        click_by_text(driver,
            "Sign in", "Sign In", "Log in", "Log In",
            "Login", "Continue", "Submit",
        )
        time.sleep(2)

        # ── 5. Bypass / PIN / 2FA code ────────────────────────────────────────
        print(f"[5] Checking for bypass / PIN prompt ...")
        bypass_filled = find_and_fill(driver, [
            "//input[contains(@name,'bypass') or contains(@id,'bypass')]",
            "//input[contains(@name,'pin') or contains(@id,'pin')]",
            "//input[contains(@name,'code') or contains(@id,'code')]",
            "//input[contains(@name,'otp')  or contains(@id,'otp')]",
            "//input[contains(@placeholder,'code') or contains(@placeholder,'Code')]",
            "//input[contains(@placeholder,'bypass') or contains(@placeholder,'Bypass')]",
            "//input[contains(@placeholder,'PIN') or contains(@placeholder,'pin')]",
            # 6-digit input boxes (OTP style)
            "(//input[@maxlength='1'])[1]",
        ], BYPASS_CODE, timeout=4)

        if bypass_filled:
            print(f"    Bypass code entered: {BYPASS_CODE}")
            click_by_text(driver,
                "Verify", "Confirm", "Submit", "Continue", "Next",
                timeout=4,
            )
            time.sleep(2)
        else:
            print("    No bypass prompt found — continuing")

        # ── 6. Wait for dashboard / home page ────────────────────────────────
        print(f"[6] Waiting for dashboard ...")
        time.sleep(3)
        print(f"    Current URL: {driver.current_url}")
        driver.save_screenshot("after_login.png")

        # ── 7. Navigate to Patients ───────────────────────────────────────────
        print(f"[7] Navigating to Patients section ...")
        nav_clicked = click_by_text(driver,
            "Patients", "Patient", "Patient list",
            "All patients", "Manage patients",
            timeout=8,
        )
        if not nav_clicked:
            # Try sidebar/nav links
            find_and_click(driver, [
                "//nav//a[contains(normalize-space(.),  'Patient')]",
                "//aside//a[contains(normalize-space(.),'Patient')]",
                "//*[@role='navigation']//a[contains(normalize-space(.),'Patient')]",
                "//a[contains(@href,'patient')]",
                "//a[contains(@href,'Patient')]",
            ], timeout=8)
            print("    Clicked Patients nav link")

        time.sleep(2)
        print(f"    URL: {driver.current_url}")
        driver.save_screenshot("patients_page.png")

        # ── 8. Click Add Patient ──────────────────────────────────────────────
        print(f"[8] Clicking Add Patient button ...")
        add_clicked = click_by_text(driver,
            "Add patient", "Add Patient", "New patient", "New Patient",
            "Create patient", "Create Patient", "Add new patient",
            "+ Add patient", "+ Patient", "Add",
            timeout=8,
        )

        if not add_clicked:
            # Try icon buttons with aria-label
            find_and_click(driver, [
                "//*[contains(@aria-label,'Add patient') or contains(@aria-label,'add patient')]",
                "//*[contains(@aria-label,'New patient') or contains(@aria-label,'new patient')]",
                "//*[contains(@title,'Add patient')]",
                "//button[contains(@class,'add') or contains(@class,'create')]",
                "//button[@data-testid='add-patient']",
            ], timeout=5)
            print("    Clicked Add Patient via aria-label/attribute")

        time.sleep(2)
        print(f"    URL after click: {driver.current_url}")
        driver.save_screenshot("add_patient_clicked.png")

        print("\n✅  Done — Add Patient button clicked.")
        print("    Screenshots saved:")
        print("      after_login.png")
        print("      patients_page.png")
        print("      add_patient_clicked.png")

        time.sleep(3)   # keep browser open briefly so you can see the result

    except Exception as exc:
        driver.save_screenshot("error.png")
        print(f"\n❌ Error: {exc}")
        print("   Screenshot saved → error.png")
        raise

    finally:
        driver.quit()
        print("\nBrowser closed.")


if __name__ == "__main__":
    run()

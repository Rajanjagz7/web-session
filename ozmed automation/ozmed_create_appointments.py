"""
OzMed — Auto-login and create 3 appointments for today.
Run: python ozmed_create_appointments.py
"""

import sys, time, traceback, subprocess
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL  = "https://practice2.dev.ozmed.health"
LOGIN_URL = BASE_URL + "/auth/sign-in"

EMAIL    = "fep5@yopmail.com"
PASSWORD = "Test@1234"
BYPASS   = "489567"
CONCERN  = "General consultation"

TODAY     = datetime.now().strftime("%d/%m/%Y")
TODAY_DAY = str(datetime.now().day)

SLOTS = [
    {"time": f"{14+i:02d}:00", "label": f"{14+i:02d}:00"}
    for i in range(3)
]


def log(msg):
    print(msg, flush=True)


def kill_stale_chrome():
    for proc in ["chrome.exe", "chromedriver.exe"]:
        try:
            subprocess.run(["taskkill", "/F", "/IM", proc],
                           capture_output=True, timeout=5)
        except Exception:
            pass
    time.sleep(5)


def driver_setup():
    opt = Options()
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")
    opt.add_argument("--window-size=1440,900")
    opt.add_argument("--disable-extensions")
    opt.add_argument("--disable-gpu")
    opt.add_argument("--disable-renderer-backgrounding")
    opt.add_argument("--disable-background-timer-throttling")
    drv = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opt)
    drv.set_page_load_timeout(60)
    return drv


def els(driver, by, sel):
    """One-shot find_elements — no polling, safe from renderer crashes."""
    try:
        return driver.find_elements(by, sel)
    except Exception:
        return []


def visible_els(driver, by, sel):
    return [e for e in els(driver, by, sel) if e.is_displayed()]


# ── LOGIN ─────────────────────────────────────────────────────────────────────

def login(driver):
    log("[1] Sign-in page ...")
    try:
        driver.get(LOGIN_URL)
    except Exception as e:
        log(f"    Page load note: {type(e).__name__} — continuing")

    log("[2] Email & password ...")
    email_el = None
    for attempt in range(4):
        time.sleep(6)
        found = visible_els(driver, By.CSS_SELECTOR, "input[name='email'], input[type='email']")
        if found:
            email_el = found[0]
            log(f"    Email field found on attempt {attempt+1}")
            break
        log(f"    Email field not found (attempt {attempt+1}), re-navigating ...")
        try:
            driver.get(LOGIN_URL)
        except Exception:
            try:
                driver.execute_script("window.stop();")
            except Exception:
                pass

    if email_el is None:
        raise Exception("Could not find email input after 4 attempts")

    email_el.click()
    email_el.send_keys(Keys.CONTROL + "a")
    email_el.send_keys(EMAIL)

    pw_els = visible_els(driver, By.CSS_SELECTOR, "input[type='password']")
    if not pw_els:
        raise Exception("Password input not found")
    pw_els[0].click()
    pw_els[0].send_keys(Keys.CONTROL + "a")
    pw_els[0].send_keys(PASSWORD)
    pw_els[0].send_keys(Keys.RETURN)
    log("    Submitted login")

    # Wait for redirect away from sign-in (no WebDriverWait polling)
    for _ in range(15):
        time.sleep(2)
        if "/sign-in" not in driver.current_url:
            break
    log(f"    URL after login: {driver.current_url}")

    # OTP verify
    if "/verify" in driver.current_url:
        log("[3] Verify page — entering OTP ...")
        driver.save_screenshot("verify_page.png")

        # Wait for 6 input boxes
        for _ in range(8):
            time.sleep(2)
            inputs = els(driver, By.CSS_SELECTOR, "input")
            if len(inputs) >= 6:
                break

        inputs = els(driver, By.CSS_SELECTOR, "input")
        log(f"    {len(inputs)} input(s) found")

        if len(inputs) >= 6:
            for i, ch in enumerate(BYPASS):
                try:
                    box = inputs[i]
                    driver.execute_script("arguments[0].focus();", box)
                    box.click()
                    box.send_keys(ch)
                    time.sleep(0.2)
                except Exception:
                    pass
            log("    Entered bypass digit-by-digit")
        elif inputs:
            inputs[0].click()
            inputs[0].send_keys(BYPASS)
            log("    Entered bypass as single value")

        time.sleep(0.5)

        # Click Submit
        submit_btns = els(driver, By.XPATH,
            "//button[normalize-space(.)='Submit'] | "
            "//button[@type='submit']")
        if submit_btns:
            submit_btns[0].click()
            log("    Clicked Submit")
        elif inputs:
            inputs[-1].send_keys(Keys.RETURN)
            log("    Pressed Enter on last input")

        # Wait for verify to complete
        for _ in range(15):
            time.sleep(2)
            if "/verify" not in driver.current_url and "/otp" not in driver.current_url:
                break
        log(f"    Verify done — URL: {driver.current_url}")

    time.sleep(2)
    log(f"[OK] Logged in — {driver.current_url}")


# ── APPOINTMENTS PAGE ─────────────────────────────────────────────────────────

def open_appointments_page(driver):
    log("    > Opening /appointments ...")
    try:
        driver.get(BASE_URL + "/appointments")
    except Exception:
        pass
    time.sleep(5)


def click_book_appointment(driver):
    log("    > Clicking Book Appointment ...")
    # No WebDriverWait — find once after sleep
    time.sleep(3)
    for attempt in range(6):
        btns = els(driver, By.TAG_NAME, "button")
        for b in btns:
            try:
                txt = b.text.strip()
                if any(k in txt for k in ("Book Appointment", "New Appointment", "Add Appointment", "Book")):
                    log(f"    > Button: '{txt}'")
                    driver.execute_script("arguments[0].click();", b)
                    time.sleep(2)
                    return
            except Exception:
                pass
        time.sleep(2)
    raise Exception("Book Appointment button not found")


# ── DATE PICKER ───────────────────────────────────────────────────────────────

def pick_date(driver):
    log("    > Picking date ...")

    container = None
    for by, sel in [
        (By.CSS_SELECTOR, "div.MuiPickersInputBase-root"),
        (By.CSS_SELECTOR, "[class*='MuiPickersInputBase-root']"),
        (By.CSS_SELECTOR, "div[role='group'][class*='MuiPickers']"),
        (By.CSS_SELECTOR, "[role='group'][aria-labelledby]"),
    ]:
        found = els(driver, by, sel)
        if found:
            container = found[0]
            log(f"    > Date container: {sel}")
            break

    if container:
        driver.execute_script("arguments[0].click();", container)
        log("    > Clicked date container via JS")
    else:
        icon_btns = els(driver, By.CSS_SELECTOR,
            "button[aria-label*='date' i], button[aria-label*='calendar' i]")
        if icon_btns:
            driver.execute_script("arguments[0].click();", icon_btns[0])
            log("    > Clicked calendar icon button")
        else:
            hidden = els(driver, By.CSS_SELECTOR, "input[name='appointmentDate']")
            if hidden:
                driver.execute_script("arguments[0].click();", hidden[0])
                log("    > Clicked hidden input via JS")

    time.sleep(1.5)
    driver.save_screenshot("date_picker_open.png")

    log(f"    > Selecting day {TODAY_DAY} ...")
    for day_xpath in [
        f"//button[normalize-space(.)='{TODAY_DAY}' and not(@disabled)]",
        f"//*[@role='gridcell'][normalize-space(.)='{TODAY_DAY}']",
        f"//button[contains(@aria-label,'{TODAY_DAY}')]",
        f"//*[contains(@class,'day')][normalize-space(.)='{TODAY_DAY}']",
        f"//td[normalize-space(.)='{TODAY_DAY}']",
    ]:
        found = els(driver, By.XPATH, day_xpath)
        if found:
            try:
                driver.execute_script("arguments[0].click();", found[0])
                log(f"    > Clicked day {TODAY_DAY}")
                time.sleep(1)
                driver.save_screenshot("date_picked.png")
                # Close calendar
                try:
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    time.sleep(0.8)
                except Exception:
                    pass
                return
            except Exception:
                pass

    log("    > Could not select day from calendar")
    driver.save_screenshot("date_calendar_debug.png")
    try:
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        time.sleep(0.8)
    except Exception:
        pass


# ── FILL MODAL STEP 1 ─────────────────────────────────────────────────────────

def find_autocomplete_input(dialog, label_text):
    return dialog.find_element(By.XPATH,
        f".//label[normalize-space(.)='{label_text}']/..//input[@role='combobox']")


def select_practitioner_with_fallback(driver):
    """
    Select Practitioner via keyboard nav.
    If the selected practitioner has no Appointment Type field, skip to the next one.
    Tries up to 5 practitioners.
    """
    log("    > Selecting Practitioner ...")
    dialog = driver.find_element(By.CSS_SELECTOR, "[class*='MuiDialog-paper']")
    inp = find_autocomplete_input(dialog, "Practitioner")

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
    time.sleep(0.3)
    inp.click()
    time.sleep(0.5)
    inp.send_keys(Keys.ARROW_DOWN)
    time.sleep(3)

    for attempt in range(5):
        inp.send_keys(Keys.RETURN)
        time.sleep(1.5)
        prac_val = inp.get_attribute('value') or ''
        log(f"    > Practitioner attempt {attempt+1}: '{prac_val}'")

        if not prac_val:
            log("    > Practitioner input still empty — stopping")
            break

        # Check if Appointment Type field appeared
        has_appt_type = len(els(driver, By.XPATH,
            "//div[contains(@class,'MuiDialog-paper')]"
            "//label[normalize-space(.)='Appointment Type']")) > 0

        if has_appt_type:
            log(f"    > Appointment Type available for '{prac_val}'")
            return True

        log(f"    > No Appointment Type for '{prac_val}' — trying next")
        inp.send_keys(Keys.CONTROL, 'a')
        inp.send_keys(Keys.DELETE)
        time.sleep(0.3)
        inp.send_keys(Keys.ARROW_DOWN)
        time.sleep(3)

    log("    > Could not find a practitioner with Appointment Types")
    return False


def select_appointment_type(driver):
    """
    Select the first available Appointment Type option.
    Strategy: click input → ArrowDown (opens dropdown + triggers API call) →
    sleep 7s → one-shot find_elements for options → click first via ActionChains.
    Falls back to keyboard Enter if no options found in DOM.
    """
    log("    > Selecting Appointment Type ...")
    dialog = driver.find_element(By.CSS_SELECTOR, "[class*='MuiDialog-paper']")
    inp = find_autocomplete_input(dialog, "Appointment Type")

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
    time.sleep(0.3)

    # Click input to focus it, then ArrowDown to open dropdown and trigger API
    ActionChains(driver).move_to_element(inp).pause(0.2).click().perform()
    time.sleep(0.4)
    ActionChains(driver).send_keys_to_element(inp, Keys.ARROW_DOWN).perform()
    log("    > ArrowDown sent — waiting 7s for API ...")
    time.sleep(7)

    # One-shot check for options (no polling — avoids renderer crash)
    option_selectors = [
        "[class*='MuiAutocomplete-option']",
        "ul[class*='MuiAutocomplete-listbox'] li",
        "ul[role='listbox'] li",
        "[role='option']",
    ]
    first_opt = None
    for sel in option_selectors:
        found = [e for e in els(driver, By.CSS_SELECTOR, sel) if e.is_displayed()]
        if found:
            first_opt = found[0]
            log(f"    > Found option via '{sel}': '{first_opt.text}'")
            break

    if first_opt:
        ActionChains(driver).move_to_element(first_opt).pause(0.1).click().perform()
        time.sleep(0.8)
    else:
        log("    > No options in DOM — using keyboard fallback")
        # Re-focus inp and try Enter on already-highlighted item
        ActionChains(driver).move_to_element(inp).pause(0.1).click().perform()
        time.sleep(0.2)
        inp.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.5)
        inp.send_keys(Keys.RETURN)
        time.sleep(0.8)

    val = inp.get_attribute('value') or ''
    log(f"    > Appointment Type value: '{val}'")
    if not val:
        log("    > Appointment Type still empty — form may reject submission")
    return val


def fill_step1(driver, slot):
    log(f"    > Step 1 — Date + Practitioner + Appointment Type + Concern ...")

    pick_date(driver)
    time.sleep(1)

    select_practitioner_with_fallback(driver)

    # Appointment Type field appears dynamically after Practitioner chosen
    # Wait briefly for it without WebDriverWait polling
    for _ in range(5):
        time.sleep(1)
        if els(driver, By.XPATH,
               "//div[contains(@class,'MuiDialog-paper')]"
               "//label[normalize-space(.)='Appointment Type']"):
            break

    try:
        select_appointment_type(driver)
    except Exception as e:
        log(f"    > Appointment Type error: {e}")

    # Concern textarea
    time.sleep(0.5)
    concern_els = visible_els(driver, By.XPATH,
        "//div[contains(@class,'MuiDialog-paper')]//textarea[not(@aria-hidden='true')]")
    if concern_els:
        driver.execute_script("arguments[0].click();", concern_els[0])
        concern_els[0].send_keys(CONCERN)
        log("    > Concern filled")
    else:
        log("    > Concern field not found")

    driver.save_screenshot("step1_filled.png")

    # Click Next
    log("    > Clicking Next ...")
    time.sleep(1)
    next_btns = els(driver, By.XPATH,
        "//div[contains(@class,'MuiDialog-paper')]//button[normalize-space(.)='Next']")
    if next_btns:
        ActionChains(driver).move_to_element(next_btns[0]).pause(0.2).click().perform()
        time.sleep(2.5)
        driver.save_screenshot("step2.png")
        log("    > Next clicked")
    else:
        log("    > Next button not found")


# ── FILL MODAL STEP 2 ─────────────────────────────────────────────────────────

def fill_step2(driver, idx):
    log("    > Step 2 — Patient info ...")
    driver.save_screenshot(f"appt_{idx}_step2.png")

    # Log dialog HTML to confirm we're on Step 2 (not stuck on Step 1 validation)
    try:
        dlg = driver.find_element(By.CSS_SELECTOR, "[class*='MuiDialog-paper']")
        html = dlg.get_attribute('innerHTML')
        with open(r"C:\Users\Baps\Downloads\dialog_step2_dump.html", "w", encoding="utf-8") as f:
            f.write(html)
        log(f"    > Step 2 HTML saved ({len(html)} bytes)")
        btns = dlg.find_elements(By.TAG_NAME, "button")
        for b in btns[:10]:
            log(f"      Button: '{b.text.strip()}' disabled={b.get_attribute('disabled')}")
        # Check we actually advanced (no "Appointment Type is required!" still shown)
        if "Appointment Type is required" in html:
            log("    > [WARN] Still on Step 1 (Appointment Type validation error)")
    except Exception:
        pass

    # Patient search input — no WebDriverWait, just find after sleep
    search_el = None
    for _ in range(5):
        time.sleep(2)
        found = visible_els(driver, By.XPATH,
            "//div[contains(@class,'MuiDialog-paper')]"
            "//input[not(@aria-hidden='true') and not(@type='hidden')]")
        if found:
            search_el = found[0]
            break

    if search_el is None:
        log("    > Patient search input not found")
        driver.save_screenshot(f"appt_{idx}_patient_error.png")
        return False

    ph = search_el.get_attribute('placeholder') or ''
    log(f"    > Patient search input placeholder='{ph}'")
    ActionChains(driver).move_to_element(search_el).pause(0.2).click().perform()
    time.sleep(0.5)
    search_el.clear()
    search_el.send_keys("R")
    log("    > Typed 'R' — waiting 4s for results ...")
    time.sleep(4)
    driver.save_screenshot(f"appt_{idx}_patient_search.png")

    # One-shot find for autocomplete options (no polling)
    result_el = None
    for sel in [
        "[class*='MuiAutocomplete-option']",
        "ul[class*='MuiAutocomplete-listbox'] li",
        "ul[role='listbox'] li",
        "[role='option']",
    ]:
        found = [e for e in els(driver, By.CSS_SELECTOR, sel) if e.is_displayed()]
        if found:
            result_el = found[0]
            log(f"    > Patient result: '{result_el.text}'")
            break

    if result_el:
        ActionChains(driver).move_to_element(result_el).pause(0.1).click().perform()
        log("    > Patient selected")
        time.sleep(1)
    else:
        log("    > No patient results found — trying keyboard fallback")
        search_el.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.5)
        search_el.send_keys(Keys.RETURN)
        time.sleep(1)

    driver.save_screenshot(f"appt_{idx}_step2_filled.png")

    # Submit
    log("    > Submitting ...")
    submitted = False
    time.sleep(1)
    for label in ("Submit", "Confirm", "Book", "Book Appointment", "Save", "Create", "Done", "Finish", "Next"):
        btns = els(driver, By.XPATH,
            f"//div[contains(@class,'MuiDialog-paper')]//button[normalize-space(.)='{label}']")
        if btns:
            log(f"    > Submit button: '{label}'")
            driver.execute_script("arguments[0].click();", btns[0])
            submitted = True
            break

    if not submitted:
        btns = els(driver, By.XPATH, "//div[@role='dialog']//button[@type='submit']")
        if btns:
            driver.execute_script("arguments[0].click();", btns[0])
            submitted = True

    time.sleep(4)
    driver.save_screenshot(f"appt_{idx}_after_submit.png")
    log(f"    > Submit {'OK' if submitted else 'NOT FOUND'}. URL: {driver.current_url}")
    return submitted


# ── CREATE ONE APPOINTMENT ────────────────────────────────────────────────────

def create_appointment(driver, slot, idx):
    log(f"\n=== Appointment {idx}/3 | {TODAY} {slot['label']} ===")
    open_appointments_page(driver)
    click_book_appointment(driver)
    fill_step1(driver, slot)
    result = fill_step2(driver, idx)
    return result


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log(f"  OzMed -- 3 appointments for {TODAY}")
    log("=" * 60)

    log("Cleaning up stale Chrome processes ...")
    kill_stale_chrome()

    driver = driver_setup()
    success = 0

    try:
        login(driver)
        time.sleep(2)

        for idx, slot in enumerate(SLOTS, 1):
            try:
                ok = create_appointment(driver, slot, idx)
                if ok:
                    success += 1
            except Exception as e:
                log(f"    [ERROR on appt {idx}] {e}")
                driver.save_screenshot(f"error_appt_{idx}.png")
                traceback.print_exc(file=sys.stdout)
                sys.stdout.flush()

        log("\n" + "=" * 60)
        log(f"  DONE -- {success}/3 appointments created for {TODAY}")
        log("=" * 60)

    except Exception as exc:
        driver.save_screenshot("error_screenshot.png")
        log(f"\n[FATAL ERROR] {exc}")
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()

    finally:
        log("Keeping browser open for 20 seconds ...")
        time.sleep(20)
        driver.quit()
        log("Done.")


if __name__ == "__main__":
    main()

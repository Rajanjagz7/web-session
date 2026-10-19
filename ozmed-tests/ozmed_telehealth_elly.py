"""
OzMed -- 12 Telehealth appointments
Practitioner : ELLY HAUSER
Patient       : Arline FOSTER
Visit type    : Telehealth (> 20 min preferred)
Run: python ozmed_telehealth_elly.py
"""

import re, time, sys, traceback
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL  = "https://practice2.dev.ozmed.health"
LOGIN_URL = BASE_URL + "/auth/sign-in"

EMAIL    = "fep5@yopmail.com"
PASSWORD = "Test@1234"
BYPASS   = "489567"

PRACTITIONER_NAME = "ELLY HAUSER"
PATIENT_NAME      = "Arline FOSTER"
CONCERN           = "Telehealth consultation"
NUM_APPTS         = 12

TODAY = datetime.now()
DLG   = "[class*='MuiDialog-paper']"

def log(msg): print(msg, flush=True)
def sleep(ms): time.sleep(ms / 1000)

def duration_minutes(text):
    m = re.search(r'(\d+)\s*(?:min|minute)', text, re.IGNORECASE)
    return int(m.group(1)) if m else 0


# ── LOGIN ─────────────────────────────────────────────────────────────────────

def _enter_otp(page):
    sleep(3000)
    inputs = page.locator("input").all()
    log(f"  OTP inputs: {len(inputs)}")
    if len(inputs) >= 6:
        for i, ch in enumerate(BYPASS):
            try: inputs[i].click(); inputs[i].type(ch); sleep(200)
            except: pass
    elif inputs:
        inputs[0].click(); inputs[0].fill(BYPASS)
    sleep(500)
    sub = page.locator("button:has-text('Submit'), button[type='submit']").first
    if sub.count() > 0: sub.click()
    else: page.keyboard.press("Enter")
    for _ in range(15):
        sleep(2000)
        if not any(x in page.url for x in ["/verify", "/otp", "/authenticate"]): break
    log(f"  After OTP: {page.url}")

def login(page):
    log("[LOGIN] ...")
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
    sleep(5000)
    page.wait_for_selector("input[type='email'], input[name='email']", timeout=30000)
    page.fill("input[type='email'], input[name='email']", EMAIL)
    sleep(300)
    page.fill("input[type='password']", PASSWORD)
    sleep(300)
    sub = page.locator("button[type='submit']").first
    if sub.count() > 0: sub.click(); log("  Clicked submit")
    else: page.keyboard.press("Enter"); log("  Pressed Enter")
    for i in range(20):
        sleep(2000)
        if "sign-in" not in page.url: break
        if i == 9: page.keyboard.press("Enter"); log("  Enter fallback")
    log(f"  URL: {page.url}")
    if any(x in page.url for x in ["/verify", "/otp", "/2fa", "/authenticate"]):
        _enter_otp(page)
    sleep(2000)
    log(f"[LOGIN] Done -- {page.url}")


# ── DATE PICKER ───────────────────────────────────────────────────────────────

def pick_date(page, target_date):
    day = str(target_date.day)
    log(f"    Date: {target_date.strftime('%d/%m/%Y')}")
    for sel in [f"{DLG} div.MuiPickersInputBase-root",
                f"{DLG} [class*='MuiPickersInputBase-root']",
                f"{DLG} [role='group'][aria-labelledby]",
                f"{DLG} button[aria-label*='date' i]"]:
        loc = page.locator(sel).first
        if loc.count() > 0:
            try: loc.click(force=True, timeout=3000); log(f"    Picker opened"); break
            except: pass
    sleep(1500)

    # Navigate months safely
    for _ in range(3):
        hdrs = page.locator("[class*='PickersCalendarHeader'], [class*='MuiPickersCalendarHeader']").all()
        hdr_text = " ".join((h.text_content() or "") for h in hdrs)
        log(f"    Calendar: '{hdr_text.strip()[:35]}'")
        if target_date.strftime("%B %Y").lower() in hdr_text.lower(): break
        nxt_btns = [b for b in page.locator("button[aria-label*='next' i]").all()
                    if b.is_visible() and b.get_attribute("disabled") is None]
        if nxt_btns:
            try: nxt_btns[-1].click(force=True, timeout=3000); sleep(700)
            except: break
        else: break

    # Click day -- no Escape (let calendar close naturally)
    for loc in [
        page.locator("button").filter(has_text=re.compile(rf"^\s*{day}\s*$")),
        page.get_by_role("gridcell", name=re.compile(rf"^\s*{day}\s*$")),
        page.locator(f"xpath=//button[normalize-space(.)='{day}']"),
        page.locator(f"xpath=//*[@role='gridcell'][normalize-space(.)='{day}']"),
    ]:
        visible = [el for el in loc.all() if el.is_visible()]
        if visible:
            try:
                visible[0].click(force=True); log(f"    Day {day} clicked")
                sleep(1500); return
            except: pass
    log(f"    Could not click day {day}")
    sleep(500)


# ── OPTION PICKER (batch evaluate_all -- avoids lazy-locator timeout) ──────────

OPTION_SELS = [
    "[class*='MuiAutocomplete-option']",
    "ul[role='listbox'] li",
    "[role='option']",
]

def pick_option(page, exact_name=None):
    """Read all dropdown option texts at once via JS, then click best match by index."""
    for sel in OPTION_SELS:
        try:
            texts = page.locator(sel).evaluate_all(
                "els => els.map(e => (e.textContent || '').trim())"
            )
            texts = [t for t in texts if t]
            if not texts: continue
            log(f"    Options ({sel[:30]}): {texts[:5]}")

            if exact_name:
                idx = next((i for i, t in enumerate(texts)
                            if exact_name.upper() in t.upper()), None)
                if idx is not None:
                    page.locator(sel).nth(idx).click(force=True)
                    log(f"    Clicked [{idx}]: '{texts[idx][:50]}'")
                    sleep(600); return texts[idx]

            # Fallback: first
            page.locator(sel).first.click(force=True)
            log(f"    Clicked first: '{texts[0][:50]}'")
            sleep(600); return texts[0]
        except Exception as e:
            log(f"    pick_option err ({sel[:25]}): {e}")
            continue
    log("    No dropdown options found")
    return None


def type_search(page, inp_loc, text, wait_ms=4500):
    inp_loc.scroll_into_view_if_needed()
    sleep(200)
    inp_loc.click(force=True)
    sleep(300)
    inp_loc.select_text(); sleep(100)
    inp_loc.type(text, delay=50)
    log(f"    Typed '{text}' -- waiting {wait_ms}ms ...")
    sleep(wait_ms)


def arrow_open(page, inp_loc, wait_ms=6000):
    inp_loc.scroll_into_view_if_needed()
    sleep(300)
    inp_loc.click(force=True); sleep(300)
    page.keyboard.press("ArrowDown")
    log(f"    ArrowDown -- waiting {wait_ms}ms ...")
    sleep(wait_ms)


def pick_telehealth_or_over20(page):
    """Pick best appointment type: Telehealth >20min > >20min > Telehealth > first."""
    for sel in OPTION_SELS:
        try:
            texts = page.locator(sel).evaluate_all(
                "els => els.map(e => (e.textContent || '').trim())"
            )
            texts = [t for t in texts if t]
            if not texts: continue
            log(f"    Visit types: {texts[:8]}")

            tele_over  = [(i,t) for i,t in enumerate(texts)
                          if 'telehealth' in t.lower() and duration_minutes(t) > 20]
            over       = [(i,t) for i,t in enumerate(texts) if duration_minutes(t) > 20]
            tele_any   = [(i,t) for i,t in enumerate(texts) if 'telehealth' in t.lower()]

            if tele_over:   idx, lbl = tele_over[0][0],  "Telehealth >20min"
            elif over:      idx, lbl = over[0][0],        ">20min"
            elif tele_any:  idx, lbl = tele_any[0][0],   "Telehealth any"
            else:           idx, lbl = 0,                 "first"

            page.locator(sel).nth(idx).click(force=True)
            log(f"    [{lbl}] Picked: '{texts[idx][:50]}'")
            sleep(700)
            return texts[idx]
        except Exception as e:
            log(f"    pick_telehealth err: {e}")
    return None


# ── STEP 1 ─────────────────────────────────────────────────────────────────────

def fill_step1(page, target_date, idx):
    log(f"  [Step 1] {target_date.strftime('%d/%m/%Y')}")

    pick_date(page, target_date)
    sleep(800)

    # Grab all comboboxes in dialog
    combos = [c for c in page.locator(f"{DLG} input[role='combobox']").all() if c.is_visible()]
    log(f"  Combos found: {len(combos)}")

    if not combos:
        log("  No combos -- dialog may have closed early")
        return

    # ── Practitioner (combo[0]) ─────────────────────────────────────────────
    log("  Selecting Practitioner ...")
    prac = combos[0]
    type_search(page, prac, "Elly", wait_ms=4000)
    result = pick_option(page, exact_name=PRACTITIONER_NAME)
    log(f"  Practitioner set: {result}")
    sleep(1500)

    # ── Visit Type / Appointment Medium (Telehealth) ──────────────────────
    # Check for any new comboboxes after practitioner (Visit Type may appear)
    combos2 = [c for c in page.locator(f"{DLG} input[role='combobox']").all() if c.is_visible()]
    log(f"  Combos after practitioner: {len(combos2)}")

    # Also look for radio/toggle button labelled Telehealth
    tele_btn = page.locator(f"{DLG} label:has-text('Telehealth'), {DLG} button:has-text('Telehealth')").first
    if tele_btn.count() > 0 and tele_btn.is_visible():
        tele_btn.click(force=True)
        log("  Clicked Telehealth toggle")
        sleep(500)

    # ── Appointment Type (second combobox or later) ───────────────────────
    # Wait a bit for Appointment Type to appear
    for _ in range(6):
        sleep(1000)
        combos3 = [c for c in page.locator(f"{DLG} input[role='combobox']").all() if c.is_visible()]
        if len(combos3) >= 2: break

    combos3 = [c for c in page.locator(f"{DLG} input[role='combobox']").all() if c.is_visible()]
    log(f"  Combos before appt type: {len(combos3)}")

    if len(combos3) >= 2:
        appt_inp = combos3[1]
        log("  Opening Appointment Type (combo[1]) ...")
        arrow_open(page, appt_inp, wait_ms=6000)
        pick_telehealth_or_over20(page)
    else:
        log("  Appointment Type combo not found")

    # ── Concern ────────────────────────────────────────────────────────────
    sleep(500)
    concern = page.locator(f"{DLG} textarea:not([aria-hidden='true'])").first
    if concern.count() > 0 and concern.is_visible():
        concern.click(force=True)
        concern.select_text()
        concern.type(CONCERN, delay=20)
        log("  Concern filled")

    page.screenshot(path=f"elly_step1_{idx}.png")

    # ── Next ───────────────────────────────────────────────────────────────
    sleep(1000)
    nxt = page.locator(f"{DLG} button:has-text('Next')").last
    if nxt.count() > 0 and nxt.is_visible():
        nxt.click(force=True); sleep(3000)
        log("  Next clicked")
    else:
        all_btns = [b.inner_text().strip() for b in page.locator(f"{DLG} button").all() if b.is_visible()]
        log(f"  Next not found. Buttons: {all_btns}")


# ── STEP 2 ─────────────────────────────────────────────────────────────────────

def fill_step2(page, idx):
    log("  [Step 2] Patient: Arline FOSTER")
    page.screenshot(path=f"elly_step2_{idx}.png")

    try:
        if "Appointment Type is required" in page.locator(DLG).inner_text(timeout=3000):
            log("  [WARN] Still Step 1 -- validation error"); return False
    except: pass

    patient_inp = None
    for _ in range(5):
        sleep(2000)
        visible = [i for i in page.locator(
            f"{DLG} input:not([aria-hidden='true']):not([type='hidden'])").all()
            if i.is_visible()]
        if visible: patient_inp = visible[0]; break

    if patient_inp is None:
        log("  Patient input not found"); return False

    # Try multiple search strings for Arline FOSTER
    result = None
    for search in ["Arline", "Foster", "A"]:
        type_search(page, patient_inp, search, wait_ms=4000)
        result = pick_option(page, exact_name=PATIENT_NAME)
        if result: break
        log(f"  No result for '{search}', trying next ...")
        patient_inp.select_text(); sleep(200)

    log(f"  Patient set: {result}")
    page.screenshot(path=f"elly_step2_filled_{idx}.png")
    sleep(2000)   # wait for Submit button to become active after patient selection

    # Log all visible buttons in dialog to debug
    dlg_btns = [b.inner_text().strip() for b in page.locator(f"{DLG} button").all() if b.is_visible()]
    log(f"  Dialog buttons: {dlg_btns}")

    submitted = False
    for lbl in ("Submit", "Confirm", "Book Appointment", "Book", "Schedule",
                "Save", "Create", "Finish", "Done", "Next", "Complete"):
        btn = page.locator(f"{DLG} button:has-text('{lbl}')").last
        if btn.count() > 0 and btn.is_visible():
            btn.click(force=True); log(f"  Submitted via '{lbl}'")
            submitted = True; break

    if not submitted:
        # Try submit-type button
        btn = page.locator(f"{DLG} button[type='submit']").last
        if btn.count() > 0 and btn.is_visible():
            btn.click(force=True); submitted = True; log("  Submitted via type=submit")

    if not submitted and dlg_btns:
        # Last resort: click the last visible button that isn't Back/Cancel
        all_btns = [b for b in page.locator(f"{DLG} button").all()
                    if b.is_visible() and b.inner_text().strip().lower() not in ("back","cancel","close")]
        if all_btns:
            t = all_btns[-1].inner_text().strip()
            all_btns[-1].click(force=True); log(f"  Submitted via last button: '{t}'")
            submitted = True

    sleep(4000)
    page.screenshot(path=f"elly_done_{idx}.png")
    log(f"  Submit {'OK' if submitted else 'NOT FOUND'} | {page.url}")
    return submitted


# ── CREATE ONE APPOINTMENT ────────────────────────────────────────────────────

def create_one(page, target_date, idx):
    log(f"\n{'='*60}")
    log(f"  Appt {idx}/{NUM_APPTS} -- {target_date.strftime('%d/%m/%Y')}")
    log(f"{'='*60}")

    page.goto(BASE_URL + "/appointments", wait_until="domcontentloaded", timeout=60000)
    sleep(5000)

    dialog_opened = False
    for attempt in range(8):
        for kw in ["Book Appointment", "New Appointment", "Book"]:
            for btn in page.locator("button").all():
                try:
                    t = btn.inner_text().strip()
                    if kw.lower() in t.lower() and btn.is_visible():
                        btn.click(force=True); log(f"  Clicked '{t}'"); sleep(3000)
                        if page.locator(DLG).count() > 0:
                            dialog_opened = True; break
                except: pass
            if dialog_opened: break
        if dialog_opened: break
        sleep(2000)

    if not dialog_opened:
        page.screenshot(path=f"elly_no_dialog_{idx}.png")
        raise Exception("Dialog did not open")

    fill_step1(page, target_date, idx)

    if page.locator(DLG).count() == 0:
        log("  Dialog gone after Step 1 -- form may not have filled")
        return False

    return fill_step2(page, idx)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log(f"  OzMed -- ELLY HAUSER / Arline FOSTER -- Telehealth x{NUM_APPTS}")
    log("=" * 60)

    success, results = 0, []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=60,
                                     args=["--start-maximized"])
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        page.set_default_timeout(60000)

        try:
            login(page)
            page.keyboard.press("F11"); sleep(1500)

            for i in range(NUM_APPTS):
                target_date = TODAY + timedelta(days=i)
                try:
                    ok = create_one(page, target_date, i + 1)
                    status = "OK" if ok else "FAIL"
                    results.append(f"  [{status}] Appt {i+1} -- {target_date.strftime('%d/%m/%Y')}")
                    if ok: success += 1
                except Exception as e:
                    log(f"  [ERROR] Appt {i+1}: {e}")
                    try: page.screenshot(path=f"elly_error_{i+1}.png")
                    except: pass
                    results.append(f"  [FAIL] Appt {i+1} -- {target_date.strftime('%d/%m/%Y')} -- {str(e)[:60]}")

            log("\n" + "=" * 60)
            log(f"  RESULT: {success}/{NUM_APPTS} created")
            log("=" * 60)
            for r in results: log(r)

        except Exception as exc:
            try: page.screenshot(path="elly_fatal.png")
            except: pass
            log(f"\n[FATAL] {exc}")
        finally:
            log("\nKeeping browser open 20s ...")
            sleep(20000)
            browser.close()
            log("Done.")


if __name__ == "__main__":
    main()

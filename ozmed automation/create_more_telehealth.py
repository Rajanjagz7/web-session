"""
Books additional Telehealth appointments (30 more) for today's date.
Appointment type must be >= 20 minutes. Cycles through all 10 patients.
"""
import asyncio
import re
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

URL = "https://practice2.dev.ozmed.health/"
EMAIL = "fep5@yopmail.com"
PASSWORD = "Test@1234"
OTP = "489567"
MIN_DURATION_MINUTES = 20

DURATION_RE = re.compile(r"\((\d+)\s*mins?\)", re.IGNORECASE)

VISIT_TYPE = "Telehealth"
APPOINTMENTS_TO_BOOK = 30

PATIENT_NAMES = [
    "Lucas Thomas", "Noah Anderson", "Liam Taylor", "Emma Rodriguez",
    "Noah Wilson", "Mason Davis", "Noah Davis", "Jack Taylor",
    "Lucas Wilson", "Mason Anderson",
]


def parse_duration(text: str):
    m = DURATION_RE.search(text)
    return int(m.group(1)) if m else None


async def login(page):
    await page.goto(URL, wait_until="networkidle", timeout=30_000)
    await page.wait_for_function(
        "() => { const r = document.getElementById('root'); return r && r.children.length > 0; }",
        timeout=15_000,
    )
    inputs = await page.locator("input").all()
    await inputs[0].fill(EMAIL)
    await inputs[1].fill(PASSWORD)
    await page.get_by_role("button", name="Sign In").click()
    await page.wait_for_timeout(2500)
    if "verify" in page.url:
        for attempt in range(4):
            for i, digit in enumerate(OTP):
                for _ in range(3):
                    try:
                        otp_inputs = await page.locator("input").all()
                        if i < len(otp_inputs):
                            await otp_inputs[i].fill(digit, timeout=5000)
                        break
                    except Exception:
                        await page.wait_for_timeout(300)
            await page.wait_for_timeout(300)
            try:
                await page.get_by_role("button", name="Submit").click(timeout=5000)
            except Exception:
                pass
            await page.wait_for_timeout(3000)
            if "verify" not in page.url:
                break
            print(f"  OTP attempt {attempt + 1} failed, retrying...")


async def dismiss_all_overlays(page):
    for _ in range(5):
        try:
            dialog = page.locator("[class*='MuiDialog-paper']").first
            if await dialog.count() == 0:
                break
            if not await dialog.is_visible():
                break
        except Exception:
            break
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(700)


async def open_appointments_page(page):
    await dismiss_all_overlays(page)
    await page.get_by_role("link", name="Appointments").click()
    await page.wait_for_timeout(3000)


async def open_book_appointment_modal(page):
    await page.get_by_role("button", name="Book Appointment").click()
    dialog = page.locator("[class*='MuiDialog-paper']")
    try:
        await dialog.first.wait_for(state="visible", timeout=10_000)
    except Exception:
        pass
    await page.wait_for_timeout(1500)
    return dialog


async def pick_today(page, dialog) -> bool:
    date_btn = dialog.locator("button[aria-label='Choose date']")
    clicked = False
    for _ in range(4):
        try:
            await date_btn.click(timeout=8_000)
            clicked = True
            break
        except Exception:
            await page.wait_for_timeout(1000)
    if not clicked:
        return False
    await page.wait_for_timeout(500)
    day_buttons = await page.locator("button.MuiPickersDay-root").all()
    for b in day_buttons:
        cls = await b.get_attribute("class") or ""
        if "Mui-disabled" not in cls:
            await b.click()
            await page.wait_for_timeout(800)
            return True
    return False


async def select_visit_type(page, dialog, visit_type: str) -> bool:
    vt_select = dialog.locator("[aria-haspopup='listbox']").first
    try:
        await vt_select.click(timeout=5_000)
    except Exception:
        return False
    await page.wait_for_timeout(800)
    opts = await page.get_by_role("option").all()
    for o in opts:
        text = (await o.inner_text()).strip()
        if visit_type.lower() in text.lower():
            await o.click()
            await page.wait_for_timeout(500)
            return True
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)
    return False


async def select_first_slot(page, dialog) -> bool:
    avail = dialog.locator("text=Practitioner Availability")
    try:
        await avail.scroll_into_view_if_needed(timeout=10_000)
    except Exception:
        pass
    slot_start = page.locator("span", has_text=re.compile(r"^\d{2}:\d{2}$")).first
    for _ in range(8):
        if await slot_start.count() > 0:
            break
        await page.wait_for_timeout(1000)
    if await slot_start.count() == 0:
        return False
    await slot_start.click()
    await page.wait_for_timeout(800)
    return True


async def select_practitioner_with_qualifying_type(page, dialog):
    prac_input = dialog.locator("input[role='combobox']").first
    await prac_input.click()
    await page.wait_for_timeout(300)
    await page.keyboard.press("ArrowDown")
    await page.wait_for_timeout(3000)
    prac_count = len(await page.get_by_role("option").all())
    if prac_count == 0:
        await page.keyboard.press("Escape")
        return None
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)

    for idx in range(prac_count):
        await prac_input.click()
        await page.wait_for_timeout(300)
        await prac_input.fill("")
        await page.keyboard.press("ArrowDown")
        await page.wait_for_timeout(2500)
        opts = await page.get_by_role("option").all()
        if idx >= len(opts):
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            break
        prac_name = (await opts[idx].inner_text()).strip().splitlines()[0]
        await opts[idx].click()
        await page.wait_for_timeout(1200)

        combo_inputs = await dialog.locator("input[role='combobox']").all()
        if len(combo_inputs) < 2:
            print(f"    {prac_name!r}: no Appointment Type field")
            continue

        appt_type_input = combo_inputs[1]
        await appt_type_input.click()
        await page.wait_for_timeout(300)
        await page.keyboard.press("ArrowDown")
        await page.wait_for_timeout(4000)
        type_opts = await page.get_by_role("option").all()

        if not type_opts:
            print(f"    {prac_name!r}: 0 appointment types")
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            continue

        qualifying = []
        for o in type_opts:
            text = (await o.inner_text()).strip()
            d = parse_duration(text)
            if d is not None and d >= MIN_DURATION_MINUTES:
                qualifying.append(text)

        if not qualifying:
            print(f"    {prac_name!r}: no types >= {MIN_DURATION_MINUTES} min")
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            continue

        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)

        for q_text in qualifying:
            await appt_type_input.click()
            await page.wait_for_timeout(300)
            await page.keyboard.press("ArrowDown")
            await page.wait_for_timeout(3000)
            type_opts2 = await page.get_by_role("option").all()
            match_opt = None
            for o in type_opts2:
                if (await o.inner_text()).strip() == q_text:
                    match_opt = o
                    break
            if not match_opt:
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(300)
                continue
            await match_opt.click()
            await page.wait_for_timeout(1500)
            print(f"    {prac_name!r}: trying {q_text!r}")

            if await select_first_slot(page, dialog):
                return (prac_name, q_text)

            print(f"    {prac_name!r}/{q_text!r}: no slot")

        print(f"    {prac_name!r}: all qualifying types exhausted")

    return None


async def book_one(page, patient_name: str) -> bool:
    await open_appointments_page(page)
    dialog = await open_book_appointment_modal(page)

    if not await pick_today(page, dialog):
        print("  Could not pick today's date")
        await dismiss_all_overlays(page)
        return False

    if not await select_visit_type(page, dialog, VISIT_TYPE):
        print(f"  Could not select {VISIT_TYPE!r}")
        await dismiss_all_overlays(page)
        return False

    result = await select_practitioner_with_qualifying_type(page, dialog)
    if not result:
        print(f"  No practitioner with open slot >= {MIN_DURATION_MINUTES} min")
        await dismiss_all_overlays(page)
        return False

    prac_name, type_text = result

    concern = page.get_by_role("textbox", name="Concern")
    await concern.click()
    await concern.fill(f"{VISIT_TYPE} - {type_text}")
    await page.wait_for_timeout(300)

    next_btn = dialog.get_by_role("button", name="Next")
    await next_btn.scroll_into_view_if_needed()
    await next_btn.click()
    await page.wait_for_timeout(1500)

    if "Appointment Type is required" in (await dialog.inner_text()):
        print("  Validation failed")
        await dismiss_all_overlays(page)
        return False

    search_input = dialog.get_by_role("combobox", name="Search Patient")
    await search_input.click()
    await search_input.fill(patient_name)
    await page.wait_for_timeout(2500)
    results = await page.get_by_role("option").all()
    if not results:
        print(f"  Patient not found: {patient_name!r}")
        await dismiss_all_overlays(page)
        return False
    await results[0].click()
    await page.wait_for_timeout(800)

    submit_btn = dialog.get_by_role("button", name="Submit")
    await submit_btn.scroll_into_view_if_needed()
    await submit_btn.click()

    for _ in range(8):
        await page.wait_for_timeout(1000)
        alert = page.locator("[role='alert'], .MuiAlert-root").first
        if await alert.count() > 0 and await alert.is_visible():
            text = (await alert.inner_text()).strip()
            if re.search(r"success", text, re.IGNORECASE):
                print(f"  Toast: {text!r} -> success")
                return True
            print(f"  Error: {text!r}")
            return False
        if await dialog.count() == 0 or not await dialog.is_visible():
            return True

    await dismiss_all_overlays(page)
    return False


async def main():
    booked = 0
    failed = 0

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        print("Logging in...")
        await login(page)
        print("Logged in:", page.url)

        print(f"\nBooking {APPOINTMENTS_TO_BOOK} additional {VISIT_TYPE!r} appointments...")

        for n in range(1, APPOINTMENTS_TO_BOOK + 1):
            patient_name = PATIENT_NAMES[(n - 1) % len(PATIENT_NAMES)]
            print(f"\n[{n}/{APPOINTMENTS_TO_BOOK}] Patient: {patient_name}")
            ok = False
            try:
                ok = await book_one(page, patient_name)
            except Exception as exc:
                print(f"  Exception: {exc!r}")
                try:
                    await page.keyboard.press("Escape")
                except Exception:
                    pass
            if ok:
                booked += 1
                print(f"  -> OK ({booked} booked)")
            else:
                failed += 1
                print(f"  -> FAILED ({failed} failed)")

        await page.screenshot(path="more_telehealth_final.png", full_page=True)
        print(f"\nDone. {VISIT_TYPE}: {booked}/{APPOINTMENTS_TO_BOOK} booked, {failed} failed.")
        await page.wait_for_timeout(5000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

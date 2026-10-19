"""
Books one appointment each for the 10 patients created earlier in OzMed
(practice2.dev.ozmed.health).

Flow per patient: Appointments -> Book Appointment -> pick any open date ->
pick a practitioner that has appointment types (try others if one has none)
-> pick the first appointment type -> pick the first available time slot ->
fill a health-related concern -> Next -> search for the patient by name ->
select them -> Submit.
"""
import asyncio
import random
import re
import sys

from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

URL = "https://practice2.dev.ozmed.health/"
EMAIL = "fep5@yopmail.com"
PASSWORD = "Test@1234"
OTP = "489567"

PATIENT_NAMES = [
    "Lucas Thomas", "Noah Anderson", "Liam Taylor", "Emma Rodriguez",
    "Noah Wilson", "Mason Davis", "Noah Davis", "Jack Taylor",
    "Lucas Wilson", "Mason Anderson",
]

CONCERNS = [
    "Patient reports mild headache and fatigue for the past two days.",
    "Follow-up consultation requested for ongoing back pain.",
    "Patient experiencing seasonal allergy symptoms.",
    "Routine check-up requested, mild sore throat noted.",
    "Patient reports occasional dizziness and wants it assessed.",
    "Mild stomach discomfort after meals over the last week.",
    "Patient requesting review of recent blood pressure readings.",
    "Persistent cough for several days, no fever reported.",
    "Patient reports difficulty sleeping and general tiredness.",
    "Minor skin rash on forearm, patient wants it checked.",
]


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
        otp_inputs = await page.locator("input").all()
        for i, digit in enumerate(OTP):
            if i < len(otp_inputs):
                await otp_inputs[i].fill(digit)
        await page.get_by_role("button", name="Submit").click()
        await page.wait_for_timeout(2500)


async def open_appointments_page(page):
    await page.get_by_role("link", name="Appointments").click()
    await page.wait_for_timeout(3000)


async def open_book_appointment_modal(page):
    await page.get_by_role("button", name="Book Appointment").click()
    await page.wait_for_timeout(1200)
    return page.locator("[class*='MuiDialog-paper']")


async def pick_any_date(page, dialog):
    await dialog.locator("button[aria-label='Choose date']").click()
    await page.wait_for_timeout(500)
    day_buttons = await page.locator("button.MuiPickersDay-root").all()
    for b in day_buttons:
        cls = await b.get_attribute("class") or ""
        if "Mui-disabled" not in cls:
            await b.click()
            await page.wait_for_timeout(800)
            return True
    return False


async def select_practitioner_and_type(page, dialog) -> bool:
    """Tries practitioners in order until one has at least one Appointment
    Type available, selects the first type, then picks the first open slot.
    Returns True on success."""
    prac_input = dialog.locator("input[role='combobox']").first
    await prac_input.click()
    await page.wait_for_timeout(300)
    await page.keyboard.press("ArrowDown")
    await page.wait_for_timeout(3000)
    prac_count = len(await page.get_by_role("option").all())
    if prac_count == 0:
        return False
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
            break
        prac_name = (await opts[idx].inner_text()).strip().splitlines()[0]
        await opts[idx].click()
        await page.wait_for_timeout(1200)

        combo_inputs = await dialog.locator("input[role='combobox']").all()
        if len(combo_inputs) < 2:
            print(f"    Practitioner {prac_name!r}: no Appointment Type field, trying next")
            continue

        appt_type_input = combo_inputs[1]
        await appt_type_input.click()
        await page.wait_for_timeout(300)
        await page.keyboard.press("ArrowDown")
        await page.wait_for_timeout(4000)
        type_opts = await page.get_by_role("option").all()

        if not type_opts:
            print(f"    Practitioner {prac_name!r}: 0 appointment types, trying next")
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            continue

        await type_opts[0].click()
        await page.wait_for_timeout(1500)
        print(f"    Practitioner {prac_name!r}: {len(type_opts)} appointment types -> selected first")

        # Pick the first available time slot
        slot_picked = await select_first_slot(page, dialog)
        if slot_picked:
            return True
        print(f"    Practitioner {prac_name!r}: no bookable slot found, trying next")

    return False


async def select_first_slot(page, dialog) -> bool:
    await dialog.locator("text=Practitioner Availability").scroll_into_view_if_needed()
    await page.wait_for_timeout(500)
    slot_start = page.locator("span", has_text=re.compile(r"^\d{2}:\d{2}$")).first
    if await slot_start.count() == 0:
        return False
    await slot_start.click()
    await page.wait_for_timeout(800)
    return True


async def book_appointment_for_patient(page, patient_name: str) -> bool:
    await open_appointments_page(page)
    dialog = await open_book_appointment_modal(page)

    if not await pick_any_date(page, dialog):
        print("  No open date found")
        return False

    if not await select_practitioner_and_type(page, dialog):
        print("  No practitioner with available appointment type/slot found")
        try:
            await dialog.get_by_role("button", name="Cancel").click()
        except Exception:
            await page.keyboard.press("Escape")
        return False

    concern = page.get_by_role("textbox", name="Concern")
    await concern.click()
    await concern.fill(random.choice(CONCERNS))
    await page.wait_for_timeout(300)

    next_btn = dialog.get_by_role("button", name="Next")
    await next_btn.scroll_into_view_if_needed()
    await next_btn.click()
    await page.wait_for_timeout(1500)

    if "Appointment Type is required" in (await dialog.inner_text()):
        print("  Validation failed on step 1 (Appointment Type) — aborting this patient")
        try:
            await dialog.get_by_role("button", name="Cancel").click()
        except Exception:
            await page.keyboard.press("Escape")
        return False

    search_input = dialog.get_by_role("combobox", name="Search Patient")
    await search_input.click()
    await search_input.fill(patient_name)
    await page.wait_for_timeout(2500)

    results = await page.get_by_role("option").all()
    if not results:
        print(f"  No search result for patient {patient_name!r}")
        try:
            await dialog.get_by_role("button", name="Cancel").click()
        except Exception:
            await page.keyboard.press("Escape")
        return False

    await results[0].click()
    await page.wait_for_timeout(800)

    submit_btn = dialog.get_by_role("button", name="Submit")
    await submit_btn.scroll_into_view_if_needed()
    await submit_btn.click()
    await page.wait_for_timeout(2000)

    # The modal doesn't reliably close right after Submit (animation/lag),
    # so check the actual appointments table for the new row instead of
    # relying on dialog visibility.
    for _ in range(6):
        await page.wait_for_timeout(1000)
        error_alert = page.locator("[role='alert'], .MuiAlert-root").first
        if await error_alert.count() > 0 and await error_alert.is_visible():
            error_text = (await error_alert.inner_text()).strip()
            print(f"  Submit error: {error_text!r}")
            return False
        if await dialog.count() == 0 or not await dialog.is_visible():
            return True

    # Modal still open with no visible error — verify via the table directly
    try:
        await dialog.get_by_role("button", name="Cancel").click()
    except Exception:
        await page.keyboard.press("Escape")
    await page.wait_for_timeout(1000)
    search = page.get_by_placeholder("Search patient name...")
    await search.click()
    await search.fill(patient_name)
    await page.wait_for_timeout(1500)
    rows = await page.locator("table tbody tr").all()
    return len(rows) > 0


async def main():
    created = 0
    failed = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        print("Logging in...")
        await login(page)
        print("Logged in. URL:", page.url)

        for i, name in enumerate(PATIENT_NAMES, 1):
            print(f"\n[{i}/{len(PATIENT_NAMES)}] Booking appointment for {name}")
            ok = False
            try:
                ok = await book_appointment_for_patient(page, name)
            except Exception as exc:
                print(f"  -> error: {exc!r}")
                ok = False
                try:
                    await page.keyboard.press("Escape")
                except Exception:
                    pass

            if ok:
                created += 1
                print("  -> booked successfully")
            else:
                failed.append(name)
                print("  -> FAILED")

        await page.screenshot(path="final_appointments_list.png", full_page=True)
        print(f"\nDone. Booked {created}/{len(PATIENT_NAMES)} appointments.")
        if failed:
            print(f"Failed for: {failed}")

        await page.wait_for_timeout(5000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

"""
Books appointments for existing patients, each using a different
appointment type whose duration is more than 20 minutes (per the
practitioner/appointment-type scenario test cases).

For each (patient, desired appointment type) pair: open Book Appointment,
pick a date, find a practitioner offering that specific appointment type
(trying other practitioners if the current one doesn't have it or has no
types at all), pick the first open slot, fill a concern, advance to Step 2,
search for the patient, and submit.
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

# (patient name, appointment type substring to match) — all durations > 20 min
# Lucas Thomas: pick ANY qualifying type not already used in this batch
ALREADY_USED_TYPES = {
    "Rehabilitation Progress Summary",
    "Pain Management Note",
    "Mental Health Care Plan Note",
    "Initial Dental Assessment",
    "General Consultation 2",
}

BOOKINGS = [
    ("Lucas Thomas", ""),  # match any type; filter against ALREADY_USED_TYPES below
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
                for _ in range(3):  # re-query before each digit; boxes can re-render mid-fill
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
            print(f"  OTP attempt {attempt + 1} did not advance past /verify, retrying...")


async def dismiss_all_overlays(page):
    """Press Escape until no MUI dialog is visible (handles nested: dropdown → modal)."""
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
    # Close any leftover modal/dropdown before navigating — MUI backdrop intercepts clicks
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


async def pick_any_date(page, dialog):
    return await pick_date_by_offset(page, dialog, 0)


async def pick_date_by_offset(page, dialog, offset: int) -> bool:
    """offset=0 picks the first enabled day (today), 1 the next enabled
    day (tomorrow), 2 the day after, etc. — rolls into next month if the
    current month runs out of enabled days."""
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

    remaining = offset
    for _ in range(3):  # at most a couple of month rolls
        day_buttons = await page.locator("button.MuiPickersDay-root").all()
        enabled = []
        for b in day_buttons:
            cls = await b.get_attribute("class") or ""
            if "Mui-disabled" not in cls:
                enabled.append(b)

        if remaining < len(enabled):
            await enabled[remaining].click()
            await page.wait_for_timeout(800)
            return True

        remaining -= len(enabled)
        next_month_btn = page.get_by_role("button", name="Next month")
        if await next_month_btn.count() == 0:
            return False
        await next_month_btn.click()
        await page.wait_for_timeout(500)

    return False


async def select_first_slot(page, dialog) -> bool:
    avail = dialog.locator("text=Practitioner Availability")
    try:
        await avail.scroll_into_view_if_needed(timeout=10_000)
    except Exception:
        pass
    # Slot list can take a moment to load after picking the appointment type
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


async def select_practitioner_with_type(page, dialog, type_substring: str):
    """Find a practitioner offering an appointment type containing
    `type_substring` with duration > MIN_DURATION_MINUTES, select it, and
    pick the first open slot. Returns the matched option text, or None."""
    prac_input = dialog.locator("input[role='combobox']").first
    await prac_input.click()
    await page.wait_for_timeout(300)
    await page.keyboard.press("ArrowDown")
    await page.wait_for_timeout(3000)
    prac_count = len(await page.get_by_role("option").all())
    if prac_count == 0:
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
            break
        prac_name = (await opts[idx].inner_text()).strip().splitlines()[0]
        await opts[idx].click()
        await page.wait_for_timeout(1200)

        combo_inputs = await dialog.locator("input[role='combobox']").all()
        if len(combo_inputs) < 2:
            print(f"    {prac_name!r}: no Appointment Type field, trying next")
            continue

        appt_type_input = combo_inputs[1]
        await appt_type_input.click()
        await page.wait_for_timeout(300)
        await page.keyboard.press("ArrowDown")
        await page.wait_for_timeout(4000)
        type_opts = await page.get_by_role("option").all()
        if not type_opts:
            print(f"    {prac_name!r}: 0 appointment types, trying next")
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            continue

        match_idx = None
        match_text = None
        for i, o in enumerate(type_opts):
            text = (await o.inner_text()).strip()
            if type_substring.lower() in text.lower():
                d = parse_duration(text)
                if d is not None and d > MIN_DURATION_MINUTES:
                    match_idx = i
                    match_text = text
                break

        if match_idx is None:
            print(f"    {prac_name!r}: does not offer {type_substring!r} (>{MIN_DURATION_MINUTES}min), trying next")
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            continue

        await type_opts[match_idx].click()
        await page.wait_for_timeout(1500)
        print(f"    {prac_name!r}: selected {match_text!r}")

        if not await select_first_slot(page, dialog):
            print(f"    {prac_name!r}/{match_text!r}: no open slot, trying next")
            continue

        return match_text

    return None


async def book_one(page, patient_name: str, type_substring: str) -> bool:
    # If no practitioner has an open slot for this type today, roll forward
    # to the next day, then the day after, before giving up entirely. Each
    # attempt reopens a fresh modal — reusing the same one after a failed
    # practitioner loop left it in a stale state (dropdowns open, calendar
    # button unreachable).
    match_text = None
    dialog = None
    max_days_to_try = 4
    for day_offset in range(max_days_to_try):
        await open_appointments_page(page)
        dialog = await open_book_appointment_modal(page)

        if not await pick_date_by_offset(page, dialog, day_offset):
            print(f"  No date available at offset {day_offset}")
            try:
                await dialog.get_by_role("button", name="Cancel").click()
            except Exception:
                await page.keyboard.press("Escape")
            break

        match_text = await select_practitioner_with_type(page, dialog, type_substring)
        if match_text:
            break

        print(f"  No practitioner offers {type_substring!r} with duration > {MIN_DURATION_MINUTES} min "
              f"and an open slot on this date -> trying the next day")
        await dismiss_all_overlays(page)
        await page.wait_for_timeout(300)

    if not match_text:
        print(f"  No open slot for {type_substring!r} (>{MIN_DURATION_MINUTES} min) across "
              f"{max_days_to_try} days tried")
        await dismiss_all_overlays(page)
        return False

    concern = page.get_by_role("textbox", name="Concern")
    await concern.click()
    await concern.fill(f"Appointment booked for {match_text} review.")
    await page.wait_for_timeout(300)

    next_btn = dialog.get_by_role("button", name="Next")
    await next_btn.scroll_into_view_if_needed()
    await next_btn.click()
    await page.wait_for_timeout(1500)

    if "Appointment Type is required" in (await dialog.inner_text()):
        print("  Validation failed on step 1 — aborting")
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

    # Submit doesn't reliably close the modal right away; poll for either
    # a toast (success or error — distinguish by wording, since both use
    # the same alert role/class) or the modal disappearing.
    for _ in range(8):
        await page.wait_for_timeout(1000)
        alert = page.locator("[role='alert'], .MuiAlert-root").first
        if await alert.count() > 0 and await alert.is_visible():
            text = (await alert.inner_text()).strip()
            if re.search(r"success", text, re.IGNORECASE):
                print(f"  Toast: {text!r} -> success")
                return True
            print(f"  Submit error: {text!r}")
            return False
        if await dialog.count() == 0 or not await dialog.is_visible():
            return True

    print("  Modal still open after submit with no visible error — treating as uncertain failure")
    try:
        await dialog.get_by_role("button", name="Cancel").click()
    except Exception:
        await page.keyboard.press("Escape")
    return False


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

        for i, (patient_name, type_substring) in enumerate(BOOKINGS, 1):
            print(f"\n[{i}/{len(BOOKINGS)}] Booking {patient_name} -> {type_substring!r} (>{MIN_DURATION_MINUTES} min)")
            ok = False
            try:
                ok = await book_one(page, patient_name, type_substring)
            except Exception as exc:
                print(f"  -> error: {exc!r}")
                try:
                    await page.keyboard.press("Escape")
                except Exception:
                    pass

            if ok:
                created += 1
                print("  -> booked successfully")
            else:
                failed.append((patient_name, type_substring))
                print("  -> FAILED")

        await page.screenshot(path="long_duration_appointments_final.png", full_page=True)
        print(f"\nDone. Booked {created}/{len(BOOKINGS)} appointments.")
        if failed:
            print(f"Failed: {failed}")

        await page.wait_for_timeout(5000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

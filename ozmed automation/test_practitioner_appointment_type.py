"""
Automated test for the scenario:

  On the Appointments screen, select a practitioner. If that practitioner has
  no appointment types available, select another practitioner. The chosen
  appointment type's duration must be more than 20 minutes.

Implements TC_APT_01 .. TC_APT_14 from
TestCases_Practitioner_AppointmentType_Selection.md as a single end-to-end
run, with assertions at each decision point.
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
MIN_DURATION_MINUTES = 20  # strictly greater than this

DURATION_RE = re.compile(r"\((\d+)\s*mins?\)", re.IGNORECASE)


def parse_duration(option_text: str) -> int | None:
    m = DURATION_RE.search(option_text)
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
        otp_inputs = await page.locator("input").all()
        for i, digit in enumerate(OTP):
            if i < len(otp_inputs):
                await otp_inputs[i].fill(digit)
        await page.get_by_role("button", name="Submit").click()
        await page.wait_for_timeout(2500)


async def select_first_slot(page, dialog) -> bool:
    await dialog.locator("text=Practitioner Availability").scroll_into_view_if_needed()
    await page.wait_for_timeout(500)
    slot_start = page.locator("span", has_text=re.compile(r"^\d{2}:\d{2}$")).first
    if await slot_start.count() == 0:
        return False
    await slot_start.click()
    await page.wait_for_timeout(800)
    return True


async def find_qualifying_practitioner_and_type(page, dialog):
    """TC_APT_01..03, TC_APT_05..10: walk practitioners until one has an
    appointment type with duration > MIN_DURATION_MINUTES; pick the first
    such type for that practitioner. Returns (practitioner_name, type_text)
    or (None, None) if nothing qualifies (TC_APT_10)."""
    prac_input = dialog.locator("input[role='combobox']").first
    await prac_input.click()
    await page.wait_for_timeout(300)
    await page.keyboard.press("ArrowDown")
    await page.wait_for_timeout(3000)
    prac_count = len(await page.get_by_role("option").all())
    assert prac_count > 0, "TC_APT_01 precondition failed: no practitioners listed at all"
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
            print(f"  [TC_APT_02] {prac_name!r}: no Appointment Type field -> trying next practitioner")
            continue

        appt_type_input = combo_inputs[1]
        await appt_type_input.click()
        await page.wait_for_timeout(300)
        await page.keyboard.press("ArrowDown")
        await page.wait_for_timeout(4000)
        type_opts = await page.get_by_role("option").all()

        if not type_opts:
            print(f"  [TC_APT_02] {prac_name!r}: 0 appointment types -> trying next practitioner")
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            continue

        # TC_APT_04: every option should expose a parsable duration
        durations = []
        for o in type_opts:
            text = (await o.inner_text()).strip()
            d = parse_duration(text)
            assert d is not None, f"TC_APT_04 failed: could not parse duration from option {text!r}"
            durations.append((text, d))

        qualifying = [(text, d) for text, d in durations if d > MIN_DURATION_MINUTES]
        if not qualifying:
            print(f"  [TC_APT_09] {prac_name!r}: has {len(durations)} type(s) but none > "
                  f"{MIN_DURATION_MINUTES} min -> trying next practitioner")
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            continue

        # Try every qualifying (>20 min) type for THIS practitioner before
        # giving up on them — only move to the next practitioner once all
        # of this one's qualifying types have been tried and none had an
        # open slot.
        slot_found = False
        for chosen_text, chosen_duration in qualifying:
            chosen_idx = [t for t, _ in durations].index(chosen_text)
            await type_opts[chosen_idx].click()
            await page.wait_for_timeout(1500)
            print(f"  [TC_APT_05/08] {prac_name!r}: trying {chosen_text!r} "
                  f"({chosen_duration} min > {MIN_DURATION_MINUTES})")

            if await select_first_slot(page, dialog):
                slot_found = True
                break

            print(f"  {prac_name!r}/{chosen_text!r}: no bookable slot -> "
                  f"trying another qualifying appointment type for {prac_name!r}")
            # Reopen the Appointment Type dropdown to pick the next candidate
            await appt_type_input.click()
            await page.wait_for_timeout(300)
            await page.keyboard.press("ArrowDown")
            await page.wait_for_timeout(3000)
            type_opts = await page.get_by_role("option").all()

        if not slot_found:
            print(f"  {prac_name!r}: no qualifying type had an open slot -> trying next practitioner")
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            continue

        return prac_name, chosen_text

    return None, None


async def main():
    results = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        print("Logging in...")
        await login(page)
        print("Logged in. URL:", page.url)

        # --- Navigate to Appointments and open the modal ---
        await page.get_by_role("link", name="Appointments").click()
        await page.wait_for_timeout(3000)
        await page.get_by_role("button", name="Book Appointment").click()
        await page.wait_for_timeout(1200)
        dialog = page.locator("[class*='MuiDialog-paper']")

        # --- TC_APT_12: Practitioner field must not exist before a date is picked ---
        labels_before = [
            (await l.inner_text()).strip()
            for l in await dialog.locator("label").all()
        ]
        assert "Practitioner" not in labels_before, (
            "TC_APT_12 failed: Practitioner field present before a date was selected"
        )
        print("[TC_APT_12] PASS: Practitioner field absent before date selection")

        await dialog.locator("button[aria-label='Choose date']").click()
        await page.wait_for_timeout(500)
        day_buttons = await page.locator("button.MuiPickersDay-root").all()
        picked = False
        for b in day_buttons:
            cls = await b.get_attribute("class") or ""
            if "Mui-disabled" not in cls:
                await b.click()
                picked = True
                break
        assert picked, "Could not pick any enabled date"
        await page.wait_for_timeout(800)

        labels_after = [
            (await l.inner_text()).strip()
            for l in await dialog.locator("label").all()
        ]
        assert "Practitioner" in labels_after, (
            "TC_APT_12 failed: Practitioner field did not appear after date selection"
        )
        print("[TC_APT_12] PASS: Practitioner field appears after date selection")

        # --- Core scenario: TC_APT_01..10 ---
        prac_name, type_text = await find_qualifying_practitioner_and_type(page, dialog)
        assert prac_name is not None, (
            "TC_APT_10 failed: no practitioner with a qualifying (>20 min) appointment "
            "type and an open slot was found"
        )
        duration = parse_duration(type_text)
        assert duration is not None and duration > MIN_DURATION_MINUTES, (
            f"Scenario rule violated: chosen type {type_text!r} duration {duration} "
            f"is not > {MIN_DURATION_MINUTES} minutes"
        )
        print(f"[TC_APT_05] PASS: {prac_name!r} / {type_text!r} satisfies duration > {MIN_DURATION_MINUTES} min")

        # --- TC_APT_14: advancing past Step 1 works after a discarded earlier pick ---
        concern = page.get_by_role("textbox", name="Concern")
        await concern.click()
        await concern.fill("Automated test: verifying appointment type duration > 20 minutes.")
        await page.wait_for_timeout(300)

        next_btn = dialog.get_by_role("button", name="Next")
        await next_btn.scroll_into_view_if_needed()
        await next_btn.click()
        await page.wait_for_timeout(1500)

        dlg_text = await dialog.inner_text()
        assert "Appointment Type is required" not in dlg_text, (
            "TC_APT_11/14 failed: validation error shown even though a type was selected"
        )
        assert "Patient info" in dlg_text, "Did not advance to Step 2 (Patient info)"
        print("[TC_APT_14] PASS: advanced cleanly to Step 2 (Patient info)")

        await page.screenshot(path="test_practitioner_appttype_step2.png")

        print("\nALL ASSERTIONS PASSED")
        print(f"Summary: practitioner={prac_name!r}, appointment_type={type_text!r}, "
              f"duration={duration} min (> {MIN_DURATION_MINUTES})")

        # Leave the appointment unsubmitted (Step 2) — this script validates the
        # selection rule, not full booking. Close without submitting.
        try:
            await dialog.get_by_role("button", name="Back").click()
            await page.wait_for_timeout(500)
            await dialog.get_by_role("button", name="Cancel").click()
        except Exception:
            await page.keyboard.press("Escape")

        await page.wait_for_timeout(3000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

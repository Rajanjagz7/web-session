"""
Creates PATIENT_COUNT fake test patients in OzMed (practice2.dev.ozmed.health).

Login -> Patients -> Add Patient -> fill Step 1 (Personal info, all required
fields) -> Next -> Step 2 (Health & Insurance, all optional) -> Add Patient.
Repeats for each generated patient. On a duplicate-phone/email error, the
patient is retried once with freshly generated contact details.
"""
import asyncio
import random
import sys
import time
from datetime import date

from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

URL = "https://practice2.dev.ozmed.health/"
EMAIL = "fep5@yopmail.com"
PASSWORD = "Test@1234"
OTP = "489567"
PATIENT_COUNT = 10  # number of new patients to create each time this script runs

FIRST_NAMES = [
    "Liam", "Olivia", "Noah", "Emma", "Mason", "Ava", "Ethan", "Sophia",
    "Lucas", "Isabella", "Jack", "Mia", "Henry", "Charlotte", "Leo",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Wilson", "Anderson", "Taylor",
    "Thomas", "Moore",
]
GENDERS = ["Male", "Female", "Other"]


def random_dob():
    today = date.today()
    age_years = random.randint(18, 85)
    year = today.year - age_years
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return day, month, year


def gen_patient(used_phones: set, used_emails: set):
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)

    # Guarantee uniqueness within this run, not just low collision odds —
    # AU mobile format: 9 digits starting with 4 (no leading 0), matching
    # the country-code selector already set to Australia on the form.
    while True:
        phone = f"4{random.randint(10_000_000, 99_999_999)}"
        if phone not in used_phones:
            used_phones.add(phone)
            break

    while True:
        unique = f"{int(time.time() * 1000) % 1_000_000}{random.randint(0, 999)}"
        email = f"{first.lower()}.{last.lower()}.{unique}@example.com"
        if email not in used_emails:
            used_emails.add(email)
            break

    day, month, year = random_dob()
    gender = random.choice(GENDERS)
    return {
        "first": first, "last": last, "email": email, "phone": phone,
        "day": day, "month": month, "year": year, "gender": gender,
    }


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


async def set_dob(page, target_day: int, target_month: int, target_year: int):
    await page.locator("button[aria-label='Choose date']").click()
    await page.wait_for_timeout(300)
    await page.locator(
        "button[aria-label='calendar view is open, switch to year view']"
    ).click()
    await page.wait_for_timeout(300)

    year_radio = page.get_by_role("radio", name=str(target_year))
    for _ in range(40):
        if await year_radio.count() > 0 and await year_radio.is_visible():
            break
        await page.mouse.wheel(0, -300)
        await page.wait_for_timeout(80)
    await year_radio.click()
    await page.wait_for_timeout(300)

    current_month = date.today().month
    delta = target_month - current_month
    if delta < 0:
        btn = page.get_by_role("button", name="Previous month")
        for _ in range(-delta):
            await btn.click()
            await page.wait_for_timeout(120)
    elif delta > 0:
        btn = page.get_by_role("button", name="Next month")
        for _ in range(delta):
            await btn.click()
            await page.wait_for_timeout(120)

    day_buttons = await page.locator("button.MuiPickersDay-root").all()
    for b in day_buttons:
        txt = (await b.inner_text()).strip()
        cls = await b.get_attribute("class") or ""
        if txt == str(target_day) and "Mui-disabled" not in cls:
            await b.click()
            break
    await page.wait_for_timeout(300)


async def fill_step1(page, patient):
    inputs = await page.locator("input").all()
    await inputs[1].fill(patient["first"])
    await inputs[2].fill(patient["last"])
    await inputs[3].fill(patient["email"])
    await inputs[4].fill(patient["phone"])

    await set_dob(page, patient["day"], patient["month"], patient["year"])

    await page.get_by_role("combobox", name="Gender").click()
    await page.wait_for_timeout(300)
    await page.get_by_role("option", name=patient["gender"], exact=True).click()
    await page.wait_for_timeout(300)


async def add_one_patient(page, patient) -> bool:
    """Returns True on success, False if any field was rejected (duplicate
    phone/email, invalid format, etc.) — caller should retry with new data."""
    await page.get_by_role("link", name="Patients").click()
    await page.wait_for_timeout(800)
    await page.get_by_role("button", name="Add Patient").click()
    await page.wait_for_timeout(800)

    await fill_step1(page, patient)

    next_btn = page.get_by_role("button", name="Next")
    await next_btn.scroll_into_view_if_needed()
    await next_btn.click()
    await page.wait_for_timeout(800)

    submit_btn = page.get_by_role("button", name="Add Patient")
    await submit_btn.scroll_into_view_if_needed()
    await submit_btn.click(timeout=10_000)
    await page.wait_for_timeout(1500)

    # Catch any field-level rejection generically (duplicate phone/email,
    # invalid format, etc.) via the toast/alert the form raises, not just
    # the one "already exists" message we happened to see during testing.
    error_alert = page.locator("[role='alert'], .MuiAlert-root").first
    if await error_alert.count() > 0 and await error_alert.is_visible():
        error_text = (await error_alert.inner_text()).strip()
        print(f"  Field error for {patient['first']} {patient['last']}: "
              f"{error_text!r} — will replace data and retry")
        await recover_to_patients_list(page)
        return False

    if "/add" in page.url:
        # Submit didn't error but also didn't navigate away — treat as
        # failure rather than silently assuming success.
        print(f"  Submit for {patient['first']} {patient['last']} did not "
              f"complete (still on /add) — will replace data and retry")
        await recover_to_patients_list(page)
        return False

    return True


async def recover_to_patients_list(page):
    """Best-effort reset to a clean state before retrying a patient."""
    try:
        cancel_btn = page.get_by_role("button", name="Cancel")
        if await cancel_btn.count() > 0 and await cancel_btn.is_visible():
            await cancel_btn.click()
            await page.wait_for_timeout(500)
    except Exception:
        pass
    try:
        await page.keyboard.press("Escape")
    except Exception:
        pass
    try:
        await page.get_by_role("link", name="Patients").click()
        await page.wait_for_timeout(500)
    except Exception:
        pass


async def main():
    created = 0
    failed = []
    used_phones = set()
    used_emails = set()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        print("Logging in...")
        await login(page)
        print("Logged in. URL:", page.url)

        for i in range(1, PATIENT_COUNT + 1):
            patient = gen_patient(used_phones, used_emails)
            print(f"[{i}/{PATIENT_COUNT}] Creating {patient['first']} {patient['last']} "
                  f"(DOB {patient['day']:02d}/{patient['month']:02d}/{patient['year']}, "
                  f"{patient['gender']}, phone {patient['phone']})")

            ok = False
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    ok = await add_one_patient(page, patient)
                except Exception as exc:
                    print(f"  -> error during attempt {attempt}: {exc!r}")
                    ok = False
                    await recover_to_patients_list(page)

                if ok:
                    break

                if attempt < max_attempts:
                    # Replace the rejected/erroring fields with fresh data
                    # and retry the same patient slot.
                    patient = gen_patient(used_phones, used_emails)
                    print(f"  Retrying [{i}/{PATIENT_COUNT}] with new data: "
                          f"{patient['first']} {patient['last']} "
                          f"(DOB {patient['day']:02d}/{patient['month']:02d}/{patient['year']}, "
                          f"{patient['gender']}, phone {patient['phone']})")

            if ok:
                created += 1
                print(f"  -> created successfully")
            else:
                failed.append(patient)
                print(f"  -> FAILED after {max_attempts} attempts")

        await page.screenshot(path="final_patients_list.png", full_page=True)
        print(f"\nDone. Created {created}/{PATIENT_COUNT} patients.")
        if failed:
            print(f"Failed: {len(failed)} -> {failed}")

        await page.wait_for_timeout(5000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

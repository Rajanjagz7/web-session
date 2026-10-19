import asyncio
import sys
import random
from datetime import date
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

URL = "https://practice2.dev.ozmed.health/"
EMAIL = "fep5@yopmail.com"
PASSWORD = "Test@1234"
OTP = "489567"


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


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        await page.goto(URL, wait_until="networkidle", timeout=30_000)
        await page.wait_for_function(
            "() => { const r = document.getElementById('root'); return r && r.children.length > 0; }",
            timeout=15_000,
        )

        inputs = await page.locator("input").all()
        await inputs[0].fill(EMAIL)
        await inputs[1].fill(PASSWORD)
        await page.get_by_role("button", name="Sign In").click()
        await page.wait_for_timeout(3000)

        if "verify" in page.url:
            otp_inputs = await page.locator("input").all()
            for i, digit in enumerate(OTP):
                if i < len(otp_inputs):
                    await otp_inputs[i].fill(digit)
            await page.get_by_role("button", name="Submit").click()
            await page.wait_for_timeout(3000)

        await page.get_by_text("Patients", exact=True).click()
        await page.wait_for_timeout(1500)
        await page.get_by_role("button", name="Add Patient").click()
        await page.wait_for_timeout(1500)

        inputs = await page.locator("input").all()
        await inputs[1].fill("Jane")
        await inputs[2].fill("Doe")
        await inputs[3].fill("jane.doe.test@example.com")
        await inputs[4].fill("412345678")

        await set_dob(page, 14, 3, 1985)

        await page.get_by_role("combobox", name="Gender").click()
        await page.wait_for_timeout(400)
        options = await page.get_by_role("option").all()
        opt_texts = [await o.inner_text() for o in options]
        print("Gender options:", opt_texts)
        if options:
            await random.choice(options).click()
        await page.wait_for_timeout(400)

        await page.screenshot(path="ex2_step1_filled.png", full_page=True)
        await page.get_by_role("button", name="Next").click()
        await page.wait_for_timeout(1500)
        print("URL after Next:", page.url)
        await page.screenshot(path="ex2_step2.png", full_page=True)

        # Dump fields on step 2
        for tag in ["input", "select", "textarea"]:
            els = await page.locator(tag).all()
            print(f"\n--- step2 {tag} elements: {len(els)} ---")
            for i, el in enumerate(els):
                name = await el.get_attribute("name")
                ph = await el.get_attribute("placeholder")
                idattr = await el.get_attribute("id")
                print(f"  [{i}] name={name!r} placeholder={ph!r} id={idattr!r}")

        all_buttons = await page.locator("button").all()
        print(f"\n--- step2 buttons: {len(all_buttons)} ---")
        for i, b in enumerate(all_buttons):
            txt = (await b.inner_text()).strip()
            if txt:
                print(f"  [{i}] {txt!r}")

        # Try clicking a final submit-like button without filling step2 to see validation
        for label in ["Save", "Create", "Create Patient", "Submit", "Finish", "Add Patient"]:
            btn = page.get_by_role("button", name=label)
            if await btn.count() > 0:
                print(f"Found submit-like button: {label!r}; clicking it")
                await btn.first.click()
                break

        await page.wait_for_timeout(1500)
        await page.screenshot(path="ex2_step2_validation.png", full_page=True)
        print("URL after submit attempt:", page.url)

        await page.wait_for_timeout(20_000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

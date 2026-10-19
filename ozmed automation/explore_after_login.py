"""
Exploration script: log in to OzMed and screenshot the dashboard so we can
find where to create patients.
"""
import asyncio
import sys
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

sys.stdout.reconfigure(encoding="utf-8")

URL = "https://practice2.dev.ozmed.health/"
EMAIL = "fep5@yopmail.com"
PASSWORD = "Test@1234"
OTP = "489567"


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
        print(f"Found {len(inputs)} input elements")
        for i, inp in enumerate(inputs):
            ph = await inp.get_attribute("placeholder")
            typ = await inp.get_attribute("type")
            name = await inp.get_attribute("name")
            print(f"  [{i}] placeholder={ph!r} type={typ!r} name={name!r}")

        await inputs[0].fill(EMAIL)
        await inputs[1].fill(PASSWORD)
        await page.get_by_role("button", name="Sign In").click()

        # Wait a bit and screenshot to see what happens (OTP screen? dashboard?)
        await page.wait_for_timeout(3000)
        await page.screenshot(path="step1_after_signin.png")
        print("URL after sign in:", page.url)
        print("Title:", await page.title())

        if "verify" in page.url:
            print("OTP screen detected, filling code:", OTP)
            otp_inputs = await page.locator("input").all()
            print(f"Found {len(otp_inputs)} OTP boxes")
            for i, digit in enumerate(OTP):
                if i < len(otp_inputs):
                    await otp_inputs[i].fill(digit)
            await page.get_by_role("button", name="Submit").click()
            await page.wait_for_timeout(3000)

        await page.screenshot(path="step2_after_otp.png")
        print("URL after OTP:", page.url)
        print("Title:", await page.title())

        await page.get_by_text("Patients", exact=True).click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="step3_patients_page.png")
        print("URL on patients page:", page.url)

        # Look for an "Add" button
        for label in ["Add Patient", "Add patient", "New Patient", "+ Add Patient", "Add"]:
            btn = page.get_by_role("button", name=label)
            if await btn.count() > 0:
                print(f"Found add button with label: {label!r}")
                await btn.first.click()
                break

        await page.wait_for_timeout(2000)
        await page.screenshot(path="step4_add_patient_form.png")
        print("URL on add patient form:", page.url)

        await page.screenshot(path="step4b_full_page.png", full_page=True)

        # Dump all input/select/textarea elements with identifying attrs
        for tag in ["input", "select", "textarea"]:
            els = await page.locator(tag).all()
            print(f"\n--- {tag} elements: {len(els)} ---")
            for i, el in enumerate(els):
                name = await el.get_attribute("name")
                ph = await el.get_attribute("placeholder")
                typ = await el.get_attribute("type")
                idattr = await el.get_attribute("id")
                print(f"  [{i}] name={name!r} placeholder={ph!r} type={typ!r} id={idattr!r}")

        await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)

        # Fill required fields
        inputs = await page.locator("input").all()
        await inputs[1].fill("Jane")        # firstname
        await inputs[2].fill("Doe")         # lastname
        await inputs[3].fill("jane.doe.test@example.com")  # email
        await inputs[4].fill("412345678")   # phone

        # DOB — segmented keyboard typing was unreliable (clamped to 31/12).
        # Open the calendar picker UI instead and click through it.
        await page.locator("button[aria-label='Choose date']").click()
        await page.wait_for_timeout(500)

        # Dump all buttons in the open calendar popup to find a stable
        # selector for the month/year header (avoid hardcoding "June 2026")
        all_buttons = await page.locator("button").all()
        print(f"\n--- all buttons on page while calendar open: {len(all_buttons)} ---")
        for i, b in enumerate(all_buttons):
            txt = (await b.inner_text()).strip()
            aria = await b.get_attribute("aria-label")
            cls = await b.get_attribute("class")
            print(f"  [{i}] text={txt!r} aria-label={aria!r} class={cls!r}")

        await page.wait_for_timeout(15_000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

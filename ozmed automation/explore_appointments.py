import asyncio
import sys
from playwright.async_api import async_playwright

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

        await page.get_by_role("link", name="Appointments").click()
        await page.wait_for_timeout(4000)
        await page.screenshot(path="appt1_list_page.png")
        print("URL:", page.url)

        await page.get_by_role("button", name="Book Appointment").click()
        await page.wait_for_timeout(1500)

        dialog = page.locator("[class*='MuiDialog-paper']")

        # Open the date picker and pick any enabled day
        await dialog.locator("button[aria-label='Choose date']").click()
        await page.wait_for_timeout(500)
        await page.screenshot(path="appt3_calendar.png")

        day_buttons = await page.locator("button.MuiPickersDay-root").all()
        for b in day_buttons:
            cls = await b.get_attribute("class") or ""
            if "Mui-disabled" not in cls:
                txt = (await b.inner_text()).strip()
                print("Picking day:", txt)
                await b.click()
                break
        await page.wait_for_timeout(1000)
        await page.screenshot(path="appt4_after_date.png")

        labels = await dialog.locator("label").all()
        print(f"\n--- modal labels after date pick: {len(labels)} ---")
        for l in labels:
            txt = (await l.inner_text()).strip()
            if txt:
                print(f"  {txt!r}")

        all_inputs = await dialog.locator("input").all()
        print(f"\n--- modal inputs after date pick: {len(all_inputs)} ---")
        for i, inp in enumerate(all_inputs):
            name = await inp.get_attribute("name")
            ph = await inp.get_attribute("placeholder")
            role = await inp.get_attribute("role")
            print(f"  [{i}] name={name!r} placeholder={ph!r} role={role!r}")

        # Click Practitioner combobox and open its dropdown
        prac_input = dialog.locator("input[role='combobox']").first
        await prac_input.click()
        await page.wait_for_timeout(500)
        await page.keyboard.press("ArrowDown")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="appt5_practitioner_open.png")

        options = await page.get_by_role("option").all()
        print(f"\n--- practitioner options: {len(options)} ---")
        for o in options:
            print(" ", (await o.inner_text()).strip())

        if options:
            await options[0].click()
        await page.wait_for_timeout(1500)
        await page.screenshot(path="appt6_after_practitioner.png")

        labels = await dialog.locator("label").all()
        print(f"\n--- modal labels after practitioner pick: {len(labels)} ---")
        for l in labels:
            txt = (await l.inner_text()).strip()
            if txt:
                print(f"  {txt!r}")

        # Appointment Type combobox is the 2nd combobox input now
        combo_inputs = await dialog.locator("input[role='combobox']").all()
        print(f"\ncombobox inputs now: {len(combo_inputs)}")
        appt_type_input = combo_inputs[1]
        await appt_type_input.click()
        await page.wait_for_timeout(500)
        await page.keyboard.press("ArrowDown")
        await page.wait_for_timeout(5000)
        await page.screenshot(path="appt7_apptype_open.png")

        type_options = await page.get_by_role("option").all()
        print(f"\n--- appointment type options: {len(type_options)} ---")
        for o in type_options:
            print(" ", (await o.inner_text()).strip())

        if type_options:
            await type_options[0].click()
        else:
            print("No appointment types for this practitioner — would need to try another")
        await page.wait_for_timeout(1000)

        concern = page.get_by_role("textbox", name="Concern")
        await concern.click()
        await concern.fill("Patient reports mild headache and fatigue for the past two days.")

        await page.screenshot(path="appt8_step1_filled.png")

        next_btn = dialog.get_by_role("button", name="Next")
        await next_btn.click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="appt9_step2.png")
        print("\nDialog text after Next:")
        print((await dialog.inner_text())[:500])

        step2_inputs = await dialog.locator("input").all()
        print(f"\n--- step2 inputs: {len(step2_inputs)} ---")
        for i, inp in enumerate(step2_inputs):
            ph = await inp.get_attribute("placeholder")
            role = await inp.get_attribute("role")
            name = await inp.get_attribute("name")
            print(f"  [{i}] name={name!r} placeholder={ph!r} role={role!r}")

        await page.wait_for_timeout(20_000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

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
PATIENT_NAME = "Lucas Thomas"


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
        await page.wait_for_timeout(3000)
        await page.get_by_role("button", name="Book Appointment").click()
        await page.wait_for_timeout(1200)
        dialog = page.locator("[class*='MuiDialog-paper']")

        await dialog.locator("button[aria-label='Choose date']").click()
        await page.wait_for_timeout(500)
        day_buttons = await page.locator("button.MuiPickersDay-root").all()
        for b in day_buttons:
            cls = await b.get_attribute("class") or ""
            if "Mui-disabled" not in cls:
                await b.click()
                break
        await page.wait_for_timeout(800)

        prac_input = dialog.locator("input[role='combobox']").first
        await prac_input.click()
        await page.wait_for_timeout(300)
        await page.keyboard.press("ArrowDown")
        await page.wait_for_timeout(3000)
        opts = await page.get_by_role("option").all()
        # pick index 1 = Olivia Brown directly (known to work)
        await opts[1].click()
        await page.wait_for_timeout(1200)

        combo_inputs = await dialog.locator("input[role='combobox']").all()
        appt_type_input = combo_inputs[1]
        await appt_type_input.click()
        await page.wait_for_timeout(300)
        await page.keyboard.press("ArrowDown")
        await page.wait_for_timeout(4000)
        type_opts = await page.get_by_role("option").all()
        await type_opts[0].click()
        await page.wait_for_timeout(1500)

        await dialog.locator("text=Practitioner Availability").scroll_into_view_if_needed()
        await page.wait_for_timeout(500)
        slot_start = page.locator("span", has_text=re.compile(r"^\d{2}:\d{2}$")).first
        await slot_start.click()
        await page.wait_for_timeout(800)

        concern = page.get_by_role("textbox", name="Concern")
        await concern.click()
        await concern.fill("Patient reports mild headache and fatigue for the past two days.")
        await page.wait_for_timeout(300)

        next_btn = dialog.get_by_role("button", name="Next")
        await next_btn.scroll_into_view_if_needed()
        await next_btn.click()
        await page.wait_for_timeout(1500)
        await page.screenshot(path="dbg1_step2.png")

        search_input = dialog.get_by_role("combobox", name="Search Patient")
        await search_input.click()
        await search_input.fill(PATIENT_NAME)
        await page.wait_for_timeout(2500)
        results = await page.get_by_role("option").all()
        print("results:", len(results))
        await results[0].click()
        await page.wait_for_timeout(800)
        await page.screenshot(path="dbg2_patient_filled.png")

        submit_btn = dialog.get_by_role("button", name="Submit")
        await submit_btn.scroll_into_view_if_needed()
        print("submit disabled attr:", await submit_btn.get_attribute("disabled"))
        print("submit aria-disabled:", await submit_btn.get_attribute("aria-disabled"))
        await page.screenshot(path="dbg3_before_submit.png")
        await submit_btn.click()
        await page.wait_for_timeout(3000)
        await page.screenshot(path="dbg4_after_submit.png")

        dlg_text = await dialog.inner_text() if await dialog.count() > 0 else "(no dialog)"
        print("Dialog text after submit:")
        print(dlg_text[:1500])

        print("\nURL:", page.url)

        await page.wait_for_timeout(15_000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

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
        await page.wait_for_timeout(3000)
        await page.screenshot(path="check_appointments_list.png", full_page=True)

        rows = await page.locator("table tbody tr, [role='row']").all()
        print(f"Row-like elements found: {len(rows)}")

        body_text = await page.locator("body").inner_text()
        count_lucas = body_text.count("Lucas Thomas")
        print("Occurrences of 'Lucas Thomas':", count_lucas)

        await page.wait_for_timeout(10_000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

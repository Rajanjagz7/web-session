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
        await page.screenshot(path="final_appointments_check.png", full_page=True)

        rows = await page.locator("table tbody tr").all()
        print(f"Total rows shown: {len(rows)}")
        for r in rows:
            print(" -", (await r.inner_text()).replace("\n", " | "))

        await page.wait_for_timeout(8_000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

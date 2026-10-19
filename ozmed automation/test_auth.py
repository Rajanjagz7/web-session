import asyncio
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

async def test_domain(url, email, password):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        print(f"Testing {url} with {email}...")
        await page.goto(url, wait_until="networkidle", timeout=30_000)
        await page.wait_for_timeout(1000)
        inputs = await page.locator("input").all()
        if len(inputs) >= 2:
            await inputs[0].fill(email)
            await inputs[1].fill(password)
            await page.get_by_role("button", name="Sign In").click()
            await page.wait_for_timeout(3000)
            print(f"  URL after login: {page.url}")
            alerts = await page.locator("[role='alert'], .MuiAlert-root").all()
            for a in alerts:
                print(f"  Alert: {repr(await a.inner_text())}")
        await browser.close()

async def main():
    await test_domain("https://vibrantlifeholisticclinic.dev.ozmed.health/", "henry77053@yopmail.com", "Test@123")
    await test_domain("https://practice2.dev.ozmed.health/", "henry77053@yopmail.com", "Test@123")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

URL = "https://vibrantlifeholisticclinic.dev.ozmed.health/"
EMAIL = "henry77053@yopmail.com"
PASSWORD = "Test@123"

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        print(f"Navigating to {URL}...")
        await page.goto(URL, wait_until="networkidle", timeout=30_000)
        await page.wait_for_timeout(2000)

        buttons = await page.locator("button").all()
        print(f"Buttons on login page: {len(buttons)}")
        for b in buttons:
            txt = (await b.inner_text()).strip()
            print("  Button:", repr(txt))

        inputs = await page.locator("input").all()
        if len(inputs) >= 2:
            await inputs[0].fill(EMAIL)
            await inputs[1].fill(PASSWORD)
            
            # Click sign in button
            login_btn = page.get_by_role("button", name="Sign In")
            if await login_btn.count() > 0:
                await login_btn.click()
            else:
                await buttons[0].click()
                
            await page.wait_for_timeout(4000)

        print("URL after login click:", page.url)
        
        # Check alerts/errors
        alerts = await page.locator("[role='alert'], .MuiAlert-root").all()
        print(f"Alerts found: {len(alerts)}")
        for a in alerts:
            print("  Alert text:", repr(await a.inner_text()))

        # Check if OTP page or input count changed
        inputs_after = await page.locator("input").all()
        print(f"Inputs after login attempt: {len(inputs_after)}")
        for i, inp in enumerate(inputs_after):
            ph = await inp.get_attribute("placeholder")
            typ = await inp.get_attribute("type")
            name = await inp.get_attribute("name")
            print(f"  [{i}] name={name!r} placeholder={ph!r} type={typ!r}")

        await page.screenshot(path="vibrant_login_result.png", full_page=True)
        
        # Keep open for 5 seconds to observe
        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

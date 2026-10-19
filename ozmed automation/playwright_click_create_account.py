"""
Playwright script — OzMed Sign-in Page
Clicks the "Create an account" button on a React SPA.

The page source is a bare <div id="root"> shell; all UI is injected by
JavaScript.  Playwright's auto-waiting handles React hydration natively.

Install dependencies:
    pip install playwright
    playwright install chromium       # downloads the browser binary

Run:
    python playwright_click_create_account.py
"""

import asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

URL = "https://practice2.dev.ozmed.health/"

# ── Locator strategies tried in order ────────────────────────────────────────
# Playwright's get_by_role / get_by_text handle React-rendered DOM natively.
# We cascade from most-specific to most-lenient.
LOCATOR_STRATEGIES = [
    # 1. Semantic role — best practice (button OR link)
    ("role_button",  lambda page: page.get_by_role("button", name="Create an account")),
    ("role_link",    lambda page: page.get_by_role("link",   name="Create an account")),
    # 2. Exact visible text
    ("text_exact",   lambda page: page.get_by_text("Create an account", exact=True)),
    # 3. Partial visible text — last resort
    ("text_partial", lambda page: page.get_by_text("Create an account")),
]


async def click_create_account() -> None:
    async with async_playwright() as pw:
        # ── Browser setup ─────────────────────────────────────────────────────
        browser = await pw.chromium.launch(
            headless=False,          # set True for headless / CI environments
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page    = await context.new_page()

        try:
            # ── 1. Navigate ───────────────────────────────────────────────────
            print(f"[1/4] Navigating to {URL}")
            await page.goto(URL, wait_until="networkidle", timeout=30_000)

            # ── 2. Wait for React to hydrate ──────────────────────────────────
            print("[2/4] Waiting for React root to populate …")
            await page.wait_for_function(
                "() => { const r = document.getElementById('root'); "
                "        return r && r.children.length > 0; }",
                timeout=15_000,
            )
            print("      React root has children — page is ready.")

            # ── 3. Locate the button ──────────────────────────────────────────
            print("[3/4] Searching for 'Create an account' element …")
            element = None
            used_strategy = None

            for name, strategy_fn in LOCATOR_STRATEGIES:
                locator = strategy_fn(page)
                try:
                    # wait_for is Playwright's built-in auto-retry
                    await locator.wait_for(state="visible", timeout=8_000)
                    element          = locator
                    used_strategy    = name
                    print(f"      Found via strategy: {name!r}")
                    break
                except PWTimeout:
                    print(f"      Strategy {name!r} timed out, trying next …")
                    continue

            if element is None:
                raise RuntimeError(
                    "Could not locate 'Create an account' after all strategies.\n"
                    "Open DevTools → Elements, find the button, and add a CSS/XPath "
                    "selector to LOCATOR_STRATEGIES at the top of this script."
                )

            # ── 4. Click ──────────────────────────────────────────────────────
            print(f"[4/4] Clicking (strategy={used_strategy!r}) …")
            await element.scroll_into_view_if_needed()
            await element.click()
            print("✅  Clicked 'Create an account'")

            # ── Post-click verification ───────────────────────────────────────
            # Wait for navigation or a DOM change that confirms the click worked
            try:
                await page.wait_for_url(lambda url: url != URL, timeout=5_000)
            except PWTimeout:
                pass   # page might update in-place (SPA route change via history API)

            print(f"\n--- Result ---")
            print(f"Current URL : {page.url}")
            print(f"Page title  : {await page.title()}")

        except Exception as exc:
            screenshot = "error_screenshot.png"
            await page.screenshot(path=screenshot)
            print(f"\n❌ Error: {exc}")
            print(f"   Screenshot saved → {screenshot}")
            raise

        finally:
            await browser.close()
            print("\nBrowser closed.")


if __name__ == "__main__":
    asyncio.run(click_create_account())

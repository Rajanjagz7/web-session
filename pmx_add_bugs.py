import asyncio
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

URL_LOGIN = "https://dev.pmx.softwareco.com/login"
URL_BOARD = "https://dev.pmx.softwareco.com/dashboard/projects/6a704558959d74f201d55ce5/board"
EMAIL = "rajanj@softwareco.com"
PASSWORD = "*#Hanuman56$"

BUGS_TO_ADD = [
    "Login form does not validate invalid email format",
    "App crashes when clicking 'Save' without network connection",
    "Profile picture upload fails for images larger than 5MB",
    "Mobile menu overlaps with main content on small screens",
    "Password reset email link expires immediately",
    "Dashboard charts fail to load on Safari browser",
    "Checkout button is unresponsive after applying coupon",
    "Dark mode text is illegible on the settings page"
]

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        print(f"Navigating to {URL_LOGIN}...")
        await page.goto(URL_LOGIN, wait_until="networkidle", timeout=30_000)
        
        # Login
        print("Logging in...")
        await page.locator("#loginForm_email").fill(EMAIL)
        await page.locator("#loginForm_password").fill(PASSWORD)
        await page.get_by_role("button", name="Login").click()
        
        print("Waiting for navigation to dashboard...")
        await page.wait_for_timeout(3000)
        
        print(f"Navigating to {URL_BOARD}...")
        await page.goto(URL_BOARD, wait_until="networkidle", timeout=30_000)
        await page.wait_for_timeout(3000)
        
        # Click on Development tab
        print("Switching to Development tab...")
        await page.locator('#rc-tabs-0-tab-development').click()
        await page.wait_for_timeout(2000)
        
        # Add Bugs
        for i, bug_title in enumerate(BUGS_TO_ADD, 1):
            print(f"Adding bug {i}/{len(BUGS_TO_ADD)}: {bug_title}")
            
            # Click the top-right 'Add Task' button to open inline creator
            # Or the column 'Add Task' button
            add_task_btns = await page.locator("button.projectDetail_createTaskButton__QnQW0").all()
            if not add_task_btns:
                add_task_btns = await page.locator("button:has-text('Add Task')").all()
            
            if add_task_btns:
                await add_task_btns[0].click()
                await page.wait_for_timeout(1000)
                
                # Fill the title
                task_input = page.locator("textarea.projectDetail_createTaskInput__szVaI")
                await task_input.fill(bug_title)
                await page.wait_for_timeout(500)
                
                # Change type to 'Bug'
                type_btn = page.locator('button[aria-label="Task"]')
                if await type_btn.count() > 0:
                    await type_btn.click()
                    await page.wait_for_timeout(500)
                    
                    # Click Bug from dropdown
                    bug_option = page.locator('div[role="option"]').filter(has_text="Bug").first
                    await bug_option.click()
                    await page.wait_for_timeout(500)
                
                # Press enter to save
                await task_input.press("Enter")
                await page.wait_for_timeout(2000)
            else:
                print("Could not find the '+ Add Task' button.")
                break

        print("Finished adding bugs!")
        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

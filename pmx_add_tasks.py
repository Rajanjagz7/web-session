import asyncio
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

URL_LOGIN = "https://dev.pmx.softwareco.com/login"
URL_BOARD = "https://dev.pmx.softwareco.com/dashboard/projects/6a704558959d74f201d55ce5/board"
EMAIL = "rajanj@softwareco.com"
PASSWORD = "*#Hanuman56$"

TASKS_TO_ADD = [
    "Setup Authentication & JWT tokens",
    "Fix navigation menu bug on mobile",
    "Refactor database schema for projects",
    "Add user profile management page",
    "Implement search and filter components",
    "Write comprehensive unit tests for API",
    "Optimize image loading and caching",
    "Configure CI/CD deployment pipeline",
    "Design modern onboarding flow",
    "Fix responsive layout breakpoints",
    "Add dark mode theme toggle",
    "Integrate Stripe payment gateway",
    "Export dashboard reports to PDF",
    "Update third-party npm dependencies",
    "Benchmark query performance",
    "Setup Sentry error tracking",
    "Add email notification preferences",
    "Audit accessibility and WCAG compliance"
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
        
        # Add Tasks
        for i, task_title in enumerate(TASKS_TO_ADD, 1):
            print(f"Adding task {i}/{len(TASKS_TO_ADD)}: {task_title}")
            
            # Click the Add Task button in the 'To Do' column
            # (Assuming the first one on the page is for To Do)
            add_task_btns = await page.locator(".projectDetail_createTaskButton__QnQW0").all()
            if add_task_btns:
                await add_task_btns[0].click()
                await page.wait_for_timeout(500)
                
                # Type the task title and press Enter
                task_input = page.locator(".projectDetail_createTaskInput__szVaI")
                await task_input.fill(task_title)
                await task_input.press("Enter")
                
                # Wait for the task to be saved
                await page.wait_for_timeout(1000)
            else:
                print("Could not find the '+ Add Task' button.")
                break

        print("Finished adding tasks!")
        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

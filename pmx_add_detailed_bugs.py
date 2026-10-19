import asyncio
import sys
import os
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

URL_LOGIN = "https://dev.pmx.softwareco.com/login"
URL_BOARD = "https://dev.pmx.softwareco.com/dashboard/projects/6a704558959d74f201d55ce5/board"
EMAIL = "rajanj@softwareco.com"
PASSWORD = "*#Hanuman56$"

# We use an existing image in your backup folder as the screenshot attachment
IMAGE_PATH = "c:/Users/Baps/Downloads/backup/final_patients_list.png"

# Generate 20 bug titles
BUGS = [f"Critical UI Bug #{i}: Form validation fails on edge cases" for i in range(1, 21)]

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
        
        await page.wait_for_timeout(3000)
        await page.goto(URL_BOARD, wait_until="networkidle", timeout=30_000)
        await page.wait_for_timeout(3000)
        
        print("Switching to Development tab...")
        await page.locator('#rc-tabs-0-tab-development').click()
        await page.wait_for_timeout(2000)
        
        for i, bug_title in enumerate(BUGS, 1):
            print(f"Adding detailed bug {i}/20: {bug_title}")
            
            # Click the top-right 'Add Task' button
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
                    bug_option = page.locator('div[role="option"]').filter(has_text="Bug").first
                    await bug_option.click()
                    await page.wait_for_timeout(500)
                
                # Press enter to save the task
                await task_input.press("Enter")
                await page.wait_for_timeout(2000)
                
                # Now click on the newly created task to open the details drawer
                print(f"  -> Opening details drawer for: {bug_title}")
                await page.locator('.projectDetail_kanbanBoardContainer__6Gs2H span', has_text=bug_title).first.click()
                await page.wait_for_timeout(2000)
                
                # Add structured description
                description = (
                    "Description:\n"
                    f"A detailed bug report for {bug_title}. The application enters an unrecoverable state.\n\n"
                    "Actual Result:\n"
                    "When the user attempts to submit the data, the page freezes and an unknown error is thrown in the console.\n\n"
                    "Expected Result:\n"
                    "The system should successfully validate the input, submit the data, and redirect the user to the success page."
                )
                
                editor = page.locator(".DescriptionEditor_wrapper__MTywL .ql-editor")
                if await editor.count() > 0:
                    await editor.click()
                    # Use 'fill' to quickly replace text in Quill editor
                    await editor.fill(description)
                    print("  -> Description added.")
                
                # Upload Screenshot
                file_input = page.locator('input[name="files"][type="file"]')
                if await file_input.count() > 0:
                    if os.path.exists(IMAGE_PATH):
                        await file_input.set_input_files(IMAGE_PATH)
                        print("  -> Uploading screenshot...")
                        # Wait for upload to complete (3 seconds)
                        await page.wait_for_timeout(3000)
                    else:
                        print(f"  -> Image not found at {IMAGE_PATH}, skipping upload.")
                
                # Close the drawer (Escape key will blur editor, second Escape will close the drawer)
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(500)
                
                # Find and click close button for drawer
                close_icon = page.locator(".iconify--ph.iconify.iconify--mdi").first
                if await close_icon.count() > 0:
                    await close_icon.click()
                else:
                    await page.keyboard.press("Escape")
                
                await page.wait_for_timeout(1500)
            else:
                print("Could not find the '+ Add Task' button.")
                break

        print("Finished adding all 20 detailed bugs!")
        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

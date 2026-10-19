"""
Lesson 1: Introduction to Playwright in Python (Sync API)
--------------------------------------------------------
In this script, we will:
1. Initialize the Playwright driver using `sync_playwright()`
2. Launch a Chromium browser with visible UI (headless=False)
3. Open a new isolated page/tab
4. Navigate to a test website
5. Perform an action (search / read title)
6. Capture a screenshot
7. Safely close the browser
"""

import time
from playwright.sync_api import sync_playwright

def run_first_test():
    print("\n[Step 1] Starting Playwright engine...")
    
    # Using 'with' is a context manager in Python.
    # It guarantees that Playwright's background processes clean up properly when done.
    with sync_playwright() as p:
        
        print("[Step 2] Launching Chromium browser (headed mode)...")
        # headless=False: Shows the browser window so you can watch what's happening
        # slow_mo=500: Adds a 500ms delay between actions so human eyes can follow
        browser = p.chromium.launch(headless=False, slow_mo=500)
        
        print("[Step 3] Creating a new browser page (tab)...")
        page = browser.new_page()
        
        print("[Step 4] Navigating to example website...")
        page.goto("https://playwright.dev/python")
        
        # Extract and print the page title
        title = page.title()
        print(f"[Step 5] Page Loaded! Title is: '{title}'")
        
        # Find an element using Playwright's recommended modern locator
        # 'get_by_role' finds standard HTML elements like links, buttons, headings
        get_started_btn = page.get_by_role("link", name="Get started")
        
        print("[Step 6] Clicking the 'Get started' link...")
        get_started_btn.click()
        
        # Verify the current URL after clicking
        print(f"[Step 7] Current URL is now: {page.url}")
        
        # Take a screenshot to prove the test ran successfully
        screenshot_path = "learn_playwright/first_test_result.png"
        page.screenshot(path=screenshot_path)
        print(f"[Step 8] Screenshot saved to: {screenshot_path}")
        
        print("[Step 9] Closing browser...")
        browser.close()
        
    print("SUCCESS: Test completed successfully!\n")

if __name__ == "__main__":
    run_first_test()

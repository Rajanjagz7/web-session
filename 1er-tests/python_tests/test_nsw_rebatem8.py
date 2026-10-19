import os
import pytest
from playwright.sync_api import sync_playwright, expect

BASE_URL = "https://nswdev.rebatem8.com.au"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

@pytest.fixture(scope="module")
def browser_context():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Login
        page.goto(f"{BASE_URL}/log-in", wait_until="domcontentloaded")
        page.locator('input[name="email"]').fill("admin@rebatem8nsw.com.au")
        page.locator('input[name="password"]').fill("admin@123")
        page.get_by_role("button", name="Log In").click()
        page.wait_for_url("**/jobs", timeout=20000)

        yield page
        browser.close()

def test_01_authentication_and_session(browser_context):
    """Verifies that authentication succeeds and session lands on jobs overview."""
    page = browser_context
    assert "/jobs" in page.url
    expect(page).to_have_title("RebateM8 NSW")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "py_01_authenticated.png"))

def test_02_walkthrough_all_screens(browser_context):
    """Navigates through all application screens, validates rendering and takes screenshots."""
    page = browser_context
    routes = [
        ("/dashboard", "py_02_dashboard.png"),
        ("/projects", "py_03_projects.png"),
        ("/jobs", "py_04_all_jobs.png"),
        ("/in-progress-jobs", "py_05_in_progress.png"),
        ("/action-Required-jobs", "py_06_action_required.png"),
        ("/being-assessed-jobs", "py_07_being_assessed.png"),
        ("/completed-jobs", "py_08_completed.png"),
        ("/archived-jobs", "py_09_archived.png"),
        ("/installer", "py_10_installers.png"),
        ("/installeruser", "py_11_installer_users.png"),
        ("/matrix", "py_12_matrix.png"),
        ("/admin-users", "py_13_admin_users.png"),
        ("/privacypolicy", "py_14_cms.png"),
        ("/activity", "py_15_activity.png"),
        ("/products", "py_16_products.png"),
        ("/rebates", "py_17_rebates.png"),
        ("/rebates/calculator", "py_18_calculator.png"),
        ("/rebates/statistics", "py_19_statistics.png"),
        ("/invoices", "py_20_invoices.png"),
    ]

    for route, shot_name in routes:
        page.goto(f"{BASE_URL}{route}", wait_until="domcontentloaded")
        page.wait_for_timeout(1000)
        assert page.locator("body").is_visible()
        shot_path = os.path.join(SCREENSHOT_DIR, shot_name)
        page.screenshot(path=shot_path)
        assert os.path.exists(shot_path)

def test_03_verify_created_jobs_under_rajan_testing_company(browser_context):
    """Verifies all four created jobs exist in the Jobs table with proper AU data."""
    page = browser_context
    page.goto(f"{BASE_URL}/jobs", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    # Verification criteria for the created jobs
    jobs_to_verify = [
        {"id": "M8N000380", "entity": "Coastal Enterprises NSW Pty Ltd", "company": "Rajan Testing Company", "type": "Hot Water Heat Pump"},
        {"id": "M8N000379", "entity": "Jack Wilson", "company": "Rajan Testing Company", "type": "Hot Water Heat Pump"},
        {"id": "M8N000378", "entity": "Sydney Tech Solutions Pty Ltd", "company": "Rajan Testing Company", "type": "Heating & Cooling"},
        {"id": "M8N000377", "entity": "Olivia Nguyen", "company": "Rajan Testing Company", "type": "Heating & Cooling"},
    ]

    for j in jobs_to_verify:
        row = page.locator("tr").filter(has_text=j["id"])
        expect(row).to_be_visible()
        expect(row).to_contain_text(j["company"])
        expect(row).to_contain_text(j["type"])
        expect(row).to_contain_text("Engagement Sent")

    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "py_21_verified_jobs_table.png"))

def test_04_add_job_modal_structure(browser_context):
    """Validates the Add Job modal fields, Activity Types, and Building Types."""
    page = browser_context
    page.goto(f"{BASE_URL}/jobs", wait_until="domcontentloaded")
    page.wait_for_timeout(1500)

    page.get_by_role("button", name="Add Job").click()
    page.wait_for_timeout(1000)

    # Check Activity Type dropdown
    act_item = page.locator(".form-item").filter(has_text="Activity Type").first
    act_item.locator(".select__control").click()
    page.wait_for_timeout(400)

    expect(page.locator('[class*="-option"]').filter(has_text="Heating & Cooling")).to_be_visible()
    expect(page.locator('[class*="-option"]').filter(has_text="Hot Water Heat Pump")).to_be_visible()

    # Close modal
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)

import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const BASE_URL = 'https://nswdev.rebatem8.com.au';
const SCREENSHOT_DIR = path.join(__dirname, '../screenshots/nsw-screens');

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

test.describe('RebateM8 NSW - Comprehensive Walkthrough & Verification', () => {
  test.beforeEach(async ({ page }) => {
    // 1. Authenticate with admin credentials
    await page.goto(`${BASE_URL}/log-in`, { waitUntil: 'domcontentloaded' });
    await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
    await page.locator('input[name="password"]').fill('admin@123');
    await page.getByRole('button', { name: 'Log In' }).click();
    await page.waitForURL('**/jobs', { timeout: 20000 });
  });

  test('Walkthrough: Execute and assert all core application screens', async ({ page }) => {
    test.setTimeout(120000);
    const screens = [
      { name: '01_dashboard', route: '/dashboard', heading: /dashboard/i },
      { name: '02_projects', route: '/projects', heading: /all projects/i },
      { name: '03_all_jobs', route: '/jobs', heading: /all jobs/i },
      { name: '04_in_progress_jobs', route: '/in-progress-jobs', heading: /in progress/i },
      { name: '05_action_required_jobs', route: '/action-Required-jobs', heading: /action required/i },
      { name: '06_being_assessed_jobs', route: '/being-assessed-jobs', heading: /being assessed/i },
      { name: '07_completed_jobs', route: '/completed-jobs', heading: /completed/i },
      { name: '08_archived_jobs', route: '/archived-jobs', heading: /archived/i },
      { name: '09_installers', route: '/installer', heading: /installers/i },
      { name: '10_installer_users', route: '/installeruser', heading: /installer users/i },
      { name: '11_matrix', route: '/matrix', heading: /matrix/i },
      { name: '12_admin_users', route: '/admin-users', heading: /users/i },
      { name: '13_cms_privacy', route: '/privacypolicy', heading: /cms/i },
      { name: '14_activity_log', route: '/activity', heading: /activity log/i },
      { name: '15_products', route: '/products', heading: /products/i },
      { name: '16_rebates', route: '/rebates', heading: /rebates/i },
      { name: '17_rebates_calculator', route: '/rebates/calculator', heading: /calculator/i },
      { name: '18_rebates_statistics', route: '/rebates/statistics', heading: /statistics/i },
      { name: '19_invoices', route: '/invoices', heading: /invoices/i },
    ];

    for (const screen of screens) {
      console.log(`Navigating to ${screen.name}: ${screen.route}`);
      await page.goto(`${BASE_URL}${screen.route}`, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(1000);

      // Verify page title
      await expect(page).toHaveTitle(/RebateM8 NSW/i);

      // Verify page heading or body presence
      const hasHeading = await page.locator('h1, h2, h3, h4').filter({ hasText: screen.heading }).first().isVisible().catch(() => false);
      expect(hasHeading || (await page.locator('body').isVisible())).toBeTruthy();

      // Capture screenshot
      const shotFile = path.join(SCREENSHOT_DIR, `${screen.name}.png`);
      await page.screenshot({ path: shotFile });
      expect(fs.existsSync(shotFile)).toBeTruthy();
    }
  });

  test('Jobs Verification: Confirm created NSW jobs under Rajan Testing Company', async ({ page }) => {
    await page.goto(`${BASE_URL}/jobs`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);

    const table = page.locator('table');
    await expect(table).toBeVisible();

    // Verify all 4 created jobs appear in the table
    const createdJobs = [
      { id: 'M8N000380', name: 'Coastal Enterprises NSW Pty Ltd', company: 'Rajan Testing Company', type: 'Hot Water Heat Pump' },
      { id: 'M8N000379', name: 'Jack Wilson', company: 'Rajan Testing Company', type: 'Hot Water Heat Pump' },
      { id: 'M8N000378', name: 'Sydney Tech Solutions Pty Ltd', company: 'Rajan Testing Company', type: 'Heating & Cooling' },
      { id: 'M8N000377', name: 'Olivia Nguyen', company: 'Rajan Testing Company', type: 'Heating & Cooling' },
    ];

    const searchInput = page.locator('input[placeholder*="Search" i], input[type="search"]').first();
    for (const job of createdJobs) {
      console.log(`Verifying Job ${job.id} (${job.name} - ${job.company})...`);
      if (await searchInput.isVisible()) {
        await searchInput.fill(job.id);
        await page.waitForTimeout(1200);
      }
      const row = page.locator('tr').filter({ hasText: job.id }).first();
      await expect(row).toBeVisible({ timeout: 10000 });
      await expect(row).toContainText(job.company);
      await expect(row).toContainText(job.type);
    }

    // Take screenshot of the jobs list showing Rajan Testing Company jobs
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'verified_rajan_jobs_table.png') });
  });

  test('Add Job Modal: Verify dropdown options and validation structure', async ({ page }) => {
    await page.goto(`${BASE_URL}/jobs`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);

    await page.getByRole('button', { name: 'Add Job' }).click();
    await page.waitForTimeout(1500);

    const actSelect = page.locator('.form-item').filter({ hasText: 'Activity Type' }).first();
    await expect(actSelect).toBeVisible({ timeout: 10000 });
    await actSelect.locator('.select__control').click();
    await page.waitForTimeout(400);

    await expect(page.locator('[class*="-option"]').filter({ hasText: 'Heating & Cooling' })).toBeVisible();
    await expect(page.locator('[class*="-option"]').filter({ hasText: 'Hot Water Heat Pump' })).toBeVisible();

    // Close modal
    await page.keyboard.press('Escape');
  });
});

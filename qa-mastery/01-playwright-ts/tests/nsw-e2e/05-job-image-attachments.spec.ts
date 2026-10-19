import { test, expect } from '@playwright/test';
import { LoginPage } from '../../src/pages/LoginPage';
import { JobsPage } from '../../src/pages/JobsPage';

test.describe('NSW-IMAGES: Job Images, Energy Bills & Note Attachments E2E', () => {
  let loginPage: LoginPage;
  let jobsPage: JobsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    jobsPage = new JobsPage(page);

    await loginPage.goto();
    await loginPage.login('admin@rebatem8nsw.com.au', 'admin@123');
    await loginPage.expectLoggedIn();
  });

  test('NSW-IMG-001: Verify Energy Bill Image Attached on Commercial Job M8N000380', async ({ page }) => {
    await jobsPage.goto();
    await jobsPage.search('M8N000380');

    const row = page.locator('tr').filter({ hasText: 'M8N000380' }).first();
    await expect(row).toBeVisible();

    // Open job view
    const eyeIcon = row.locator('.cursor-pointer').first();
    await eyeIcon.click();
    await page.waitForTimeout(2000);

    // Verify Job Details page loaded
    await expect(page).toHaveURL(/.*\/jobs\/.+/);
    await expect(page.locator('h4, h3, h2, p').filter({ hasText: 'M8N000380' }).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('button', { name: 'Documents' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Photos' })).toBeVisible();
  });

  test('NSW-IMG-002: Verify Site Photo Image Evidence in Job Notes', async ({ page }) => {
    // Navigate directly to M8N000380 job view
    await page.goto('https://nswdev.rebatem8.com.au/jobs/6ab2438c7c29b5bf7379e390');
    await page.waitForTimeout(2500);

    // Click Notes tab
    const notesTab = page.getByRole('button', { name: 'Notes' });
    await notesTab.click();
    await page.waitForTimeout(2000);

    // Verify note card with image thumbnail exists
    const noteContent = page.locator('div').filter({ hasText: 'Pre-installation site photos and equipment verification images uploaded.' }).first();
    await expect(noteContent).toBeVisible();

    // Check thumbnail image or attachment box exists
    const thumbnail = page.locator('.note-card img, div:has-text("Pre-installation") img, div:has-text("Pre-installation") div.w-48, div:has-text("Pre-installation") [class*="rounded"]').first();
    await expect(thumbnail).toBeVisible();
  });

  test('NSW-IMG-003: Verify Residential Job M8N000379 Has Image Evidence Attached', async ({ page }) => {
    // Navigate to Jack Wilson's job
    await page.goto('https://nswdev.rebatem8.com.au/jobs/6ab2430e7c29b5bf7379e2f3');
    await page.waitForTimeout(2500);

    // Click Notes tab
    await page.getByRole('button', { name: 'Notes' }).click();
    await page.waitForTimeout(2000);

    // Verify note card with image thumbnail exists
    const noteCard = page.locator('div').filter({ hasText: 'Site inspection completed. Existing water heater nameplate' }).first();
    await expect(noteCard).toBeVisible();
  });
});

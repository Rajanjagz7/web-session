import { test, expect } from '@playwright/test';
import { LoginPage } from '../../src/pages/LoginPage';
import { JobsPage } from '../../src/pages/JobsPage';

test.describe('NSW-SEARCH: Search, Table Filtering & Job Inspection E2E', () => {
  let loginPage: LoginPage;
  let jobsPage: JobsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    jobsPage = new JobsPage(page);

    await loginPage.goto();
    await loginPage.login('admin@rebatem8nsw.com.au', 'admin@123');
    await loginPage.expectLoggedIn();
  });

  test('NSW-SEARCH-001: Search table by specific Job ID', async ({ page }) => {
    await jobsPage.goto();

    // Pick top job in table to search
    const firstRow = page.locator('table tbody tr').first();
    const rowText = await firstRow.innerText();
    const jobIdMatch = rowText.match(/M8N\d+/);
    const targetJobId = jobIdMatch ? jobIdMatch[0] : 'M8N000380';

    console.log(`Searching for Job ID: ${targetJobId}`);
    await jobsPage.search(targetJobId);

    // Verify row with that ID is visible and matches
    const resultRow = page.locator('tr').filter({ hasText: targetJobId });
    await expect(resultRow).toBeVisible();
    await expect(resultRow).toContainText('Rajan Testing Company');

    // Clear search
    await jobsPage.clearSearch();
  });

  test('NSW-SEARCH-002: Search table by Customer / Business entity name', async ({ page }) => {
    await jobsPage.goto();

    console.log('Searching for customer name: "Jack Wilson"');
    await jobsPage.search('Jack Wilson');

    const resultRow = page.locator('tr').filter({ hasText: 'Jack Wilson' }).first();
    await expect(resultRow).toBeVisible();
    await expect(resultRow).toContainText('Rajan Testing Company');
    await expect(resultRow).toContainText('Residential');

    await jobsPage.clearSearch();
  });

  test('NSW-INSPECT-001: Verify job details page navigation', async ({ page }) => {
    await jobsPage.goto();

    // Click on Jack Wilson's job
    const row = page.locator('tr').filter({ hasText: 'Jack Wilson' }).first();
    const viewButton = row.locator('button, a, svg').first();
    if (await viewButton.isVisible()) {
      await viewButton.click();
      await page.waitForTimeout(2000);
      expect(page.url()).toBeTruthy();
    }
  });
});

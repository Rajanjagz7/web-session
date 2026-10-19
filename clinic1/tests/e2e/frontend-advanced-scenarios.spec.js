// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');

const authFile = path.join(__dirname, '../../playwright/.auth/user.json');
test.use({ storageState: authFile });

test.describe('Clinic1 - Advanced Frontend Workflows & Live Verification', () => {
  const origin = 'https://abc-health-world.dev.clinic1.ai';

  test('Frontend Workflow 1: Invoices filtering, search, and invoice table inspection', async ({ page }) => {
    await page.goto(origin + '/invoices', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    const table = page.locator('table, [role="grid"], .MuiTable-root');
    await expect(table).toBeVisible();

    const searchInput = page.locator('input[placeholder*="Search"], input[type="search"], input[placeholder*="search"]').first();
    if (await searchInput.count() > 0) {
      await searchInput.fill('Albert');
      await page.waitForTimeout(1500);
      await searchInput.clear();
      await page.waitForTimeout(1000);
    }

    const firstRow = page.locator('tbody tr, .MuiTableRow-root').first();
    if (await firstRow.count() > 0) {
      const rowText = await firstRow.innerText();
      console.log('Sample Invoice Row:', rowText.replace(/\n/g, ' | '));
      await firstRow.click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'test-results/invoice-detail-drawer.png' });
    }
  });

  test('Frontend Workflow 2: Patient directory, profile inspection, Memberships tab and Billing tab', async ({ page }) => {
    await page.goto(origin + '/patients', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    const patientRow = page.locator('tbody tr, .MuiTableRow-root').first();
    await expect(patientRow).toBeVisible();
    const patientText = await patientRow.innerText();
    console.log('First Patient:', patientText.replace(/\n/g, ' | '));

    await patientRow.click();
    await page.waitForTimeout(3000);
    console.log('Patient Profile URL:', page.url());
    await page.screenshot({ path: 'test-results/patient-profile.png' });

    const membershipTab = page.locator('button:has-text("Membership"), a:has-text("Membership"), [role="tab"]:has-text("Membership")').first();
    if (await membershipTab.count() > 0) {
      await membershipTab.click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'test-results/patient-memberships-tab.png' });
    }
  });

  test('Frontend Workflow 3: Classes module schedule and sessions', async ({ page }) => {
    await page.goto(origin + '/classes', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(4000);

    const bodyText = await page.locator('body').innerText();
    expect(bodyText.length).toBeGreaterThan(50);
    await page.screenshot({ path: 'test-results/classes-schedule-full.png' });
    console.log('Classes schedule loaded successfully.');
  });

  test('Frontend Workflow 4: Payments registry inspection', async ({ page }) => {
    await page.goto(origin + '/payments', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    await page.screenshot({ path: 'test-results/payments-registry.png' });
    const contentText = await page.locator('body').innerText();
    expect(contentText).toContain('Payment');
    console.log('Payments registry verified.');
  });

  test('Frontend Workflow 5: Settings / Membership Plans configuration inspection', async ({ page }) => {
    await page.goto(origin + '/settings', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    await page.screenshot({ path: 'test-results/settings-page.png' });
    console.log('Settings page loaded:', page.url());
  });

});
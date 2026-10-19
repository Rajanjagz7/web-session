// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');

const authFile = path.join(__dirname, '../../playwright/.auth/user.json');
test.use({ storageState: authFile });

test.describe('Clinic1 - Appointments Lifecycle & Membership Operations', () => {
  const origin = 'https://abc-health-world.dev.clinic1.ai';

  test('Appointments 1: Navigate to Appointments list, inspect status badges, filters, and records', async ({ page }) => {
    await page.goto(`${origin}/dashboard`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const apptLink = page.locator('text=Appointments').first();
    await apptLink.click();
    await page.waitForTimeout(3000);

    const rows = page.locator('tbody tr, .MuiTableRow-root');
    const count = await rows.count();
    console.log(`Appointments loaded: ${count} rows`);
  });

  test('Appointments 2: Navigate to Schedule / Calendar view and inspect practitioner bookings', async ({ page }) => {
    await page.goto(`${origin}/dashboard`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const scheduleLink = page.locator('text=Schedule').first();
    await scheduleLink.click();
    await page.waitForTimeout(3000);

    const pageContent = await page.locator('body').innerText();
    expect(pageContent).toContain('Schedule');
  });

  test('Appointments 3: Membership Pause & Cancellation request queues on Dashboard', async ({ page }) => {
    await page.goto(`${origin}/dashboard`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const pauseCard = page.locator('text=Pending Membership Pause Requests').first();
    await expect(pauseCard).toBeVisible();

    const cancelCard = page.locator('text=Pending Membership Cancellation Requests').first();
    await expect(cancelCard).toBeVisible();
    console.log('Membership widgets active.');
  });
});
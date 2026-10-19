import { test, expect } from '@playwright/test';

test.describe('OzMed Settings - Billing & Vouchers Module', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate directly to the Vouchers page
    await page.goto('/settings/billing/vouchers');
    // Ensure table or main wrapper finishes rendering
    await expect(page.getByRole('tab', { name: /Vouchers/i })).toBeVisible({ timeout: 15000 });
  });

  test('should verify Billing sub-navigation tabs and active Vouchers view', async ({ page }) => {
    // 1. Verify all three Billing sub-tabs exist
    await expect(page.getByRole('tab', { name: /Invoice \/ Receipts/i })).toBeVisible();
    const vouchersTab = page.getByRole('tab', { name: /Vouchers/i });
    await expect(vouchersTab).toBeVisible();
    await expect(page.getByRole('tab', { name: /Payment Receipts/i })).toBeVisible();

    // 2. Verify Vouchers tab is currently selected
    await expect(vouchersTab).toHaveAttribute('aria-selected', 'true');
  });

  test('should display the vouchers table with all required data columns', async ({ page }) => {
    // Verify expected column headers
    const expectedHeaders = [
      'Voucher #',
      'Invoice #',
      'Patient',
      'Practitioner',
      'Funder',
      'Requested',
      'Claimed',
      'Gap',
      'Status'
    ];

    for (const header of expectedHeaders) {
      await expect(
        page.getByRole('columnheader', { name: new RegExp(header, 'i') })
          .or(page.locator(`th:has-text("${header}")`))
          .first()
      ).toBeVisible();
    }
  });

  test('should allow searching vouchers by voucher number with debounce', async ({ page }) => {
    // 1. Locate search input field
    const searchInput = page.getByPlaceholder(/Search voucher number/i);
    await expect(searchInput).toBeVisible();

    // 2. Type a query into search
    await searchInput.fill('VOUCH-TEST-999');
    await page.waitForTimeout(600); // Allow debounced search to trigger

    // 3. Clear search to restore default state
    await searchInput.fill('');
    await page.waitForTimeout(600);
  });

  test('should toggle advanced filters panel for fine-grained voucher filtering', async ({ page }) => {
    // 1. Locate the "Filters" toggle button
    const filtersBtn = page.getByRole('button', { name: /Filters/i });
    await expect(filtersBtn).toBeVisible();

    // 2. Click to open filters drawer
    await filtersBtn.click();

    // 3. Verify filter options are displayed inside drawer
    await expect(page.getByRole('combobox', { name: /Patient/i })).toBeVisible();
    await expect(page.getByRole('combobox', { name: /Practitioner/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Date Range/i })).toBeVisible();

    // 4. Close drawer using Escape
    await page.keyboard.press('Escape');
    await expect(page.getByRole('combobox', { name: /Patient/i })).not.toBeVisible();
  });

});

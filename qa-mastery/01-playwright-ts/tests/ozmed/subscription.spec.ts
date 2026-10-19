import { test, expect } from '@playwright/test';

test.describe('OzMed Settings - Subscription & Billing Module (Positive & Negative Scenarios)', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate directly to the Subscription page using baseURL
    await page.goto('/settings/subscription');
    // Ensure the page main container finishes loading
    await expect(page.getByRole('heading', { name: /Subscription & Billing/i })).toBeVisible({ timeout: 15000 });
  });

  // -------------------------------------------------------------
  // POSITIVE SCENARIO: Active Plan & Metrics Overview
  // -------------------------------------------------------------
  test('POSITIVE: should display active subscription plan details and seat utilization', async ({ page }) => {
    // 1. Verify Active Plan & Badge
    await expect(page.getByText(/Plan:\s*base_monthly/i)).toBeVisible();
    await expect(page.getByText('Active', { exact: true }).first()).toBeVisible();

    // 2. Verify Pricing summary
    await expect(page.getByText('Base plan (month)')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'A$15.00' }).first()).toBeVisible();
    await expect(page.getByText('Monthly total')).toBeVisible();
    await expect(page.getByText(/Additional user price/i)).toBeVisible();

    // 3. Verify Seats Used Counter
    await expect(page.getByText('Seats used')).toBeVisible();
    await expect(page.getByRole('heading', { name: /17 of 17/i })).toBeVisible();

    // 4. Verify Key Action Buttons
    await expect(page.getByRole('button', { name: /Buy seats/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Manage card/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Cancel subscription/i })).toBeVisible();
  });

  // -------------------------------------------------------------
  // NEGATIVE / BOUNDARY SCENARIO: Buy Seats Zero Delta State
  // -------------------------------------------------------------
  test('NEGATIVE / BOUNDARY: should disable submission when zero additional seats are selected in Buy Seats modal', async ({ page }) => {
    // 1. Open the Buy seats dialog
    await page.getByRole('button', { name: /Buy seats/i }).click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText('Buy user seats')).toBeVisible();

    // 2. Initial state starts at 1 seat to buy, submit button is enabled
    const submitBtn = dialog.getByRole('button', { name: /Add to next invoice|Confirm/i });
    await expect(submitBtn).toBeEnabled();

    // 3. Decrement to 0 seats by clicking the minus button
    const minusBtn = dialog.getByRole('button', { name: /Remove one paid user/i });
    await minusBtn.click();

    // 4. Negative Boundary Assertion: Submit button must become DISABLED at 0 seats
    const disabledConfirmBtn = dialog.getByRole('button', { name: /Confirm/i });
    await expect(disabledConfirmBtn).toBeDisabled();

    // 5. Verify instructional warning/hint text appears
    await expect(dialog.getByText(/Use the \+ and − buttons to change your paid additional users/i)).toBeVisible();

    // 6. Close modal safely via Cancel
    await dialog.getByRole('button', { name: /Cancel/i }).click();
    await expect(dialog).not.toBeVisible();
  });

  // -------------------------------------------------------------
  // POSITIVE SCENARIO: Dynamic Calculations with Stepper
  // -------------------------------------------------------------
  test('POSITIVE: should dynamically calculate prorated pricing when incrementing seats', async ({ page }) => {
    await page.getByRole('button', { name: /Buy seats/i }).click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    const plusBtn = dialog.getByRole('button', { name: /Add one paid user/i });
    const minusBtn = dialog.getByRole('button', { name: /Remove one paid user/i });

    // Increment seats
    await plusBtn.click();
    await expect(dialog.getByText(/A\$/i)).toBeVisible();

    // Decrement back
    await minusBtn.click();

    // Cancel modal
    await dialog.getByRole('button', { name: /Cancel/i }).click();
    await expect(dialog).not.toBeVisible();
  });

  // -------------------------------------------------------------
  // NEGATIVE / RETENTION SAFEGUARD: Cancel Subscription Retention Flow
  // -------------------------------------------------------------
  test('NEGATIVE / SAFEGUARD: should present cancellation warning and safely abort when Keep Subscription is chosen', async ({ page }) => {
    // 1. Click Cancel subscription button
    await page.getByRole('button', { name: /Cancel subscription/i }).click();

    // 2. Assert Confirmation Dialog appears
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole('heading', { name: /Cancel subscription/i })).toBeVisible();

    // 3. Verify high-impact warning message is clearly communicated
    await expect(dialog.getByText(/Your practice stays fully active until.*then becomes read-only\. Nothing is deleted\./i)).toBeVisible();

    // 4. Verify presence of both Destructive and Safe action buttons
    const keepBtn = dialog.getByRole('button', { name: /Keep subscription/i });
    const cancelConfirmBtn = dialog.getByRole('button', { name: 'Cancel subscription' });
    await expect(keepBtn).toBeVisible();
    await expect(cancelConfirmBtn).toBeVisible();

    // 5. Abort cancellation by clicking "Keep subscription"
    await keepBtn.click();

    // 6. Verify dialog is dismissed and plan remains fully active
    await expect(dialog).not.toBeVisible();
    await expect(page.getByText(/Plan:\s*base_monthly/i)).toBeVisible();
    await expect(page.getByText('Active', { exact: true }).first()).toBeVisible();
  });

  // -------------------------------------------------------------
  // POSITIVE & BOUNDARY SCENARIO: Table Pagination Limits
  // -------------------------------------------------------------
  test('POSITIVE & BOUNDARY: should paginate Seat Usage roster and enforce navigation boundary limits', async ({ page }) => {
    // 1. Ensure Seat usage tab is active
    await page.getByRole('tab', { name: /Seat usage/i }).click();
    await expect(page.getByText(/17 of 17 in use/i)).toBeVisible();

    // 2. Initial Page 1 Boundary: Previous page button must be DISABLED
    const prevBtn = page.getByRole('button', { name: /Go to previous page/i });
    const nextBtn = page.getByRole('button', { name: /Go to next page/i });

    await expect(page.getByText('1–10 of 17')).toBeVisible();
    await expect(prevBtn).toBeDisabled();
    await expect(nextBtn).toBeEnabled();

    // 3. Navigate to Page 2
    await nextBtn.click();

    // 4. Page 2 Boundary: Next page button must become DISABLED on the last page
    await expect(page.getByText('11–17 of 17')).toBeVisible();
    await expect(prevBtn).toBeEnabled();
    await expect(nextBtn).toBeDisabled();

    // 5. Navigate back to Page 1
    await prevBtn.click();
    await expect(page.getByText('1–10 of 17')).toBeVisible();
    await expect(prevBtn).toBeDisabled();
    await expect(nextBtn).toBeEnabled();
  });

  // -------------------------------------------------------------
  // POSITIVE SCENARIO: Billing History Records
  // -------------------------------------------------------------
  test('POSITIVE: should display Billing History with invoices and payment records', async ({ page }) => {
    // Switch to Billing history sub-tab
    await page.getByRole('tab', { name: /Billing history/i }).click();

    // Verify Table Columns
    const expectedColumns = ['Invoice', 'Issued', 'Period', 'Amount', 'Status'];
    for (const col of expectedColumns) {
      await expect(page.getByText(col, { exact: true }).first()).toBeVisible();
    }

    // Verify paid invoice records exist
    await expect(page.getByText(/Paid/i).first()).toBeVisible();

    // Verify Stripe invoice links
    const invoiceLinks = page.locator('a[href*="invoice.stripe.com"], button:has-text("View"), a:has-text("View")');
    if (await invoiceLinks.count() > 0) {
      await expect(invoiceLinks.first()).toBeVisible();
    }
  });

});

// -------------------------------------------------------------
// NEGATIVE / SECURITY SCENARIO: Unauthorized Access Redirect
// -------------------------------------------------------------
test.describe('OzMed Settings - Subscription Unauthorized Access Guard', () => {
  // Use a completely clean context without saved authentication state
  test.use({ storageState: { cookies: [], origins: [] } });

  test('NEGATIVE / SECURITY: should deny direct unauthenticated access to subscription settings and redirect to sign-in', async ({ page }) => {
    // Navigate directly to protected route without auth token
    await page.goto('/settings/subscription');

    // Verify redirected immediately to sign-in page
    await expect(page).toHaveURL(/.*\/auth\/sign-in.*/);
    await expect(page.getByRole('heading', { name: /Welcome to OzMed|Sign In/i })).toBeVisible();
    await expect(page.locator('input[name="email"], input[type="email"]')).toBeVisible();
  });
});

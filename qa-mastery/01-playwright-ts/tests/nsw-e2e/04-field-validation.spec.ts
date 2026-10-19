import { test, expect } from '@playwright/test';
import { LoginPage } from '../../src/pages/LoginPage';
import { AddJobModal } from '../../src/pages/AddJobModal';

test.describe('NSW-VAL: Field Validations and Edge Cases E2E', () => {
  let loginPage: LoginPage;
  let addJobModal: AddJobModal;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    addJobModal = new AddJobModal(page);

    await loginPage.goto();
    await loginPage.login('admin@rebatem8nsw.com.au', 'admin@123');
    await loginPage.expectLoggedIn();
  });

  test('NSW-VAL-001: Submitting empty Add Job form highlights mandatory asterisks', async ({ page }) => {
    await addJobModal.open();

    // Click submit without filling required fields
    const submitBtn = page.locator('#submitButton');
    await submitBtn.click();
    await page.waitForTimeout(1000);

    // Assert mandatory field markers are present
    const redMarkers = page.locator('.text-red-500');
    expect(await redMarkers.count()).toBeGreaterThanOrEqual(8);

    // Verify modal remains open and didn't submit
    await expect(page.locator('#submitButton')).toBeVisible();
    await expect(page).toHaveURL(/.*\/jobs/);
  });

  test('NSW-VAL-002: Address manual toggle dynamically replaces autocomplete with text input', async ({ page }) => {
    await addJobModal.open();

    // Verify default state has Google Places autocomplete
    await expect(page.locator('#react-select-9-input')).toBeVisible();

    // Click toggle switcher
    await page.locator('.switcher-toggle').click();
    await page.waitForTimeout(400);

    // Verify text inputs appear for customerAddress and postcode
    const addressInput = page.locator('input[name="customerAddress"]');
    const postcodeInput = page.locator('input[name="postcode"]');

    await expect(addressInput).toBeVisible();
    await expect(postcodeInput).toBeVisible();

    // Test typing Australian NSW address
    await addressInput.fill('100 George St, Sydney NSW');
    await postcodeInput.fill('2000');

    await expect(addressInput).toHaveValue('100 George St, Sydney NSW');
    await expect(postcodeInput).toHaveValue('2000');
  });
});

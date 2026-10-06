import { test, expect } from '@playwright/test';
import { LoginPage } from '../src/pages/LoginPage';
import { QuotePage } from '../src/pages/QuotePage';

test.describe('Quote Section Module Tests', () => {
  let loginPage: LoginPage;
  let quotePage: QuotePage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    quotePage = new QuotePage(page);

    const email = process.env.TEST_EMAIL || 'anayra@yopmail.com';
    const otp = process.env.TEST_OTP || '';

    // Authenticate into Fieldr
    await loginPage.login(email, otp);
  });

  test.describe('Negative Scenarios', () => {
    test('should prevent advancing without selecting a customer on overview tab', async ({ page }) => {
      await quotePage.gotoNew();

      // Attempt to advance to Sections step without selecting a customer
      await quotePage.clickNext();

      // Verify that we remain on the overview page (or Customer required validation is displayed)
      await expect(page.locator("input[placeholder='Section Name']")).toHaveCount(0);
    });

    test('should validate required section name on sections tab', async ({ page }) => {
      await quotePage.gotoNew();
      await quotePage.selectCustomer();
      await quotePage.clickNext();

      // Wait for Sections tab
      await expect(page.locator("input[placeholder='Section Name']")).toBeVisible();

      // Click save with empty section name
      await quotePage.clickSave();

      // Verify error for section name
      await quotePage.expectValidationError(/Please enter a section name/i);
    });

    test('should validate required item fields when section has empty line items', async ({ page }) => {
      await quotePage.gotoNew();
      await quotePage.selectCustomer();
      await quotePage.clickNext();

      // Fill section name only
      await quotePage.fillSectionDetails({
        sectionName: 'Testing Empty Items Section',
      });

      // Click save with empty item inputs
      await quotePage.clickSave();

      // Check for item-level validations
      const errorTexts = await quotePage.getValidationErrors();
      expect(
        errorTexts.some(txt =>
          /Please enter an item name|Please enter a description|Please enter a unit|Please enter a valid quantity|Please enter a valid rate/i.test(txt)
        )
      ).toBeTruthy();
    });
  });

  test.describe('Positive Scenarios', () => {
    test('should successfully create and save a new quote with valid line items and calculation', async ({ page }) => {
      await quotePage.gotoNew();

      // 1. Overview Step: Select Customer
      await quotePage.selectCustomer();
      await quotePage.clickNext();

      // 2. Sections Step: Fill complete line item
      await expect(page.locator("input[placeholder='Section Name']")).toBeVisible();
      await quotePage.fillSectionDetails({
        sectionName: 'Plumbing & Waterworks',
        itemName: 'Transperent Water Pipes',
        description: 'Heavy duty commercial water piping',
        unit: 'Meters',
        quantity: '10',
        rate: '250',
      });

      // Verify Sub Total calculation displays $2,500.00
      await expect(page.locator('text=$2,500.00, text=2,500.00').first()).toBeVisible({ timeout: 10000 });

      // 3. Save Quote
      await quotePage.clickSave();

      // 4. Verify Quote created
      await quotePage.verifyQuoteCreated();
    });
  });
});

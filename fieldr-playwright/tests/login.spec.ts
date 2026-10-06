import { test, expect } from '@playwright/test';
import { LoginPage } from '../src/pages/LoginPage';

test.describe('Fieldr Authentication Tests', () => {
  test('should login with email and OTP', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const email = process.env.TEST_EMAIL || 'anayra@yopmail.com';
    const otp = process.env.TEST_OTP || '';

    await loginPage.goto();
    await loginPage.selectEmailLogin();
    await loginPage.enterEmail(email);
    await loginPage.clickSendOtp();

    // Verify OTP fields appear
    await expect(page.locator("input[aria-label^='Digit']").first()).toBeVisible();

    await loginPage.enterOtp(otp);
    await loginPage.submitOtp();

    // Verify successful login
    await expect(page).toHaveURL(/.*\/app.*/, { timeout: 25000 });
  });
});

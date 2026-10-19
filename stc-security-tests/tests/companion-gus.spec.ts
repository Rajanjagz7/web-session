import { test, expect } from '@playwright/test';

test.describe('Gus Money Companion Service - Sanity Suite', () => {

  test('GUS-01: Admin Login Sanity Check on Gus Money Dev', async ({ page }) => {
    const gusUrl = process.env.GUS_DEV_URL || 'https://gusdev.softwareco.com/';
    const email = process.env.GUS_EMAIL || 'admin@yopmail.com';
    const password = process.env.GUS_PASSWORD || 'Admin@123';

    await page.goto(gusUrl);

    const emailInput = page.locator('input[type="email"], input[name="email"], input[name="username"]').first();
    await expect(emailInput).toBeVisible({ timeout: 15000 });
    await emailInput.fill(email);

    const passwordInput = page.locator('input[type="password"]').first();
    await passwordInput.fill(password);

    const submitBtn = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")').first();
    await submitBtn.click();

    await page.waitForLoadState('networkidle');
    await expect(page).not.toHaveURL(/\/login/i);
  });

});

import { test as setup, expect } from '@playwright/test';

const authFile = 'auth.json';

setup('authenticate into OzMed', async ({ page }) => {
  // 1. Go to Sign In
  await page.goto('/auth/sign-in');

  // Fill credentials
  const emailInput = page.locator('input[name="email"], input[type="email"]');
  await emailInput.fill('john.doe@yopmail.com');

  const passwordInput = page.locator('input[type="password"]');
  await passwordInput.fill('Test@1234');

  await page.getByRole('button', { name: /Sign In/i }).click();

  // 2. Handle OTP Verification page
  await expect(page.getByRole('heading', { name: /Verification Required/i })).toBeVisible({ timeout: 15000 });
  
  // Focus first textbox and type code sequentially
  const otpInputs = page.getByRole('textbox', { name: '-' });
  const count = await otpInputs.count();
  const bypass = '489567';

  if (count >= 6) {
    for (let i = 0; i < 6; i++) {
      await otpInputs.nth(i).click();
      await page.keyboard.type(bypass[i]);
      await page.waitForTimeout(100);
    }
  } else {
    await page.keyboard.type(bypass);
  }

  // Click Submit
  const submitBtn = page.getByRole('button', { name: /Submit/i });
  await expect(submitBtn).toBeEnabled({ timeout: 5000 });
  await submitBtn.click();

  // 3. Wait until redirected inside the app (e.g. /appointments or /dashboard or /settings)
  await page.waitForURL(url => !url.pathname.includes('/auth/'), { timeout: 25000 });
  await page.waitForLoadState('networkidle');

  // 4. Save the full storage state (both cookies & localStorage)
  await page.context().storageState({ path: authFile });
});

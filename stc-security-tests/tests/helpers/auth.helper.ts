import { Page, expect } from '@playwright/test';

export interface LoginOptions {
  email?: string;
  password?: string;
  otp?: string;
  targetPath?: string;
}

export async function loginSTC(page: Page, options: LoginOptions = {}) {
  const isStage = process.env.TEST_ENV === 'stage';
  const email = options.email || (isStage ? process.env.STC_STAGE_EMAIL : process.env.STC_DEV_EMAIL) || 'stc.admin@yopmail.com';
  const password = options.password || (isStage ? process.env.STC_STAGE_PASSWORD : process.env.STC_DEV_PASSWORD) || 'defaultPassword';
  const otpCode = options.otp || process.env.STC_BYPASS_OTP || '486219';

  // Navigate to login / start page
  await page.goto(options.targetPath || '/login');

  // Fill Email & Password
  const emailInput = page.locator('input[type="email"], input[name="email"], input[name="username"]').first();
  await expect(emailInput).toBeVisible({ timeout: 15000 });
  await emailInput.fill(email);

  const passwordInput = page.locator('input[type="password"]').first();
  await passwordInput.fill(password);

  // Click Submit / Sign In
  const submitButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")').first();
  await submitButton.click();

  // Handle OTP Challenge if prompted
  const otpSection = page.locator('text=/OTP|Verification|Enter code/i').first();
  const isOtpVisible = await otpSection.isVisible({ timeout: 5000 }).catch(() => false);

  if (isOtpVisible) {
    const singleOtpInput = page.locator('input[name="otp"], input[name="code"], input[placeholder*="OTP"]');
    const multiOtpInputs = page.locator('input[type="text"][maxlength="1"], input[type="tel"][maxlength="1"]');

    if (await multiOtpInputs.count() >= 6) {
      for (let i = 0; i < 6; i++) {
        await multiOtpInputs.nth(i).fill(otpCode[i]);
      }
    } else if (await singleOtpInput.isVisible().catch(() => false)) {
      await singleOtpInput.fill(otpCode);
    } else {
      // Type sequentially via keyboard
      await page.keyboard.type(otpCode);
    }

    const verifyBtn = page.locator('button:has-text("Verify"), button:has-text("Submit"), button[type="submit"]').first();
    if (await verifyBtn.isVisible().catch(() => false)) {
      await verifyBtn.click();
    }
  }

  // Expect dashboard or target landing page
  await page.waitForLoadState('networkidle');
}

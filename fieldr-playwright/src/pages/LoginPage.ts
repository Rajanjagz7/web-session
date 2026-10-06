import { Page, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto('/login');
    await this.page.waitForLoadState('domcontentloaded');
  }

  async selectEmailLogin() {
    const emailTab = this.page.locator('button, div[role="tab"]').filter({ hasText: /email address/i }).first();
    await emailTab.waitFor({ state: 'visible', timeout: 15000 });
    await emailTab.click();
  }

  async enterEmail(email: string) {
    const emailInput = this.page.locator('input[type="email"], input[placeholder*="email" i], input').first();
    await emailInput.fill(email);
  }

  async clickSendOtp() {
    const sendOtpButton = this.page.locator('button').filter({ hasText: /send otp/i });
    await sendOtpButton.click();
  }

  async enterOtp(otp: string) {
    // Wait for OTP input boxes to be visible
    await this.page.waitForSelector("input[aria-label^='Digit']", { state: 'visible', timeout: 15000 });
    const otpInputs = this.page.locator("input[aria-label^='Digit']");
    const count = await otpInputs.count();

    for (let i = 0; i < Math.min(otp.length, count); i++) {
      await otpInputs.nth(i).fill(otp[i]);
    }
  }

  async submitOtp() {
    const verifyButton = this.page.locator('button').filter({ hasText: /verify/i });
    await verifyButton.click();
  }

  async login(email: string, otp: string) {
    await this.goto();
    await this.selectEmailLogin();
    await this.enterEmail(email);
    await this.clickSendOtp();
    await this.enterOtp(otp);
    await this.submitOtp();
    // Wait for redirect to /app
    await this.page.waitForURL(/.*\/app.*/, { timeout: 30000 });
  }
}

import { Page, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
    await this.page.waitForTimeout(500);
  }

  async login(email: string, pass: string) {
    const emailInput = this.page.locator('input[name="email"]');
    await emailInput.waitFor({ state: 'visible', timeout: 10000 });
    await emailInput.fill(email);

    const passInput = this.page.locator('input[name="password"]');
    await passInput.fill(pass);

    const submitBtn = this.page.getByRole('button', { name: /log in/i });
    await submitBtn.click();
  }

  async expectLoggedIn() {
    await this.page.waitForURL('**/jobs', { timeout: 15000 });
    await expect(this.page).toHaveURL(/.*\/jobs/);
  }

  async expectErrorMessage(message: string | RegExp) {
    const errorNotice = this.page.locator('.toast, [role="alert"], .text-red-500, .notification').filter({ hasText: message });
    await expect(errorNotice.first()).toBeVisible({ timeout: 10000 });
  }

  async logout() {
    // Check if user avatar/menu exists
    const userMenu = this.page.locator('.user-profile, .avatar, [class*="profile"]').first();
    if (await userMenu.isVisible()) {
      await userMenu.click();
      await this.page.waitForTimeout(300);
      const signoutBtn = this.page.getByRole('menuitem', { name: /sign out|log out/i }).or(this.page.locator('text=/sign out|log out/i'));
      if (await signoutBtn.isVisible()) {
        await signoutBtn.click();
        await this.page.waitForURL(/.*\/log-in.*/, { timeout: 10000 });
      }
    }
  }
}

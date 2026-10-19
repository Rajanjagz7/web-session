import { Page, Locator, expect } from "@playwright/test";

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly signInButton: Locator;
  readonly alertMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('input[name="email"]');
    this.passwordInput = page.locator('input[name="password"]');
    this.signInButton = page.locator('button[type="submit"]');
    this.alertMessage = page.locator('[role="alert"], .MuiAlert-message');
  }

  async goto() {
    await this.page.goto("/sign-in", { waitUntil: "domcontentloaded" });
  }

  async login(email: string, pass: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(pass);
    await this.signInButton.click();
  }

  async expectErrorMessage(messageSnippet?: string) {
    if (messageSnippet) {
      await expect(this.page.locator(`text=${messageSnippet}`).first()).toBeVisible({ timeout: 5000 });
    } else {
      await expect(this.alertMessage.first()).toBeVisible({ timeout: 5000 });
    }
  }
}
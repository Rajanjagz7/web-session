// FLD-AUTH-002 | P0 | Functional
// Preconditions: Logged out
// Expected: All observed elements are visible; legal links point to /terms-and-conditions and /privacy-policy
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-002", () => {
  test("FLD-AUTH-002 Login page shows heading, helper text, both tabs, Send OTP and legal links", { tag: ["@P0", "@regression", "@auth", "@smoke"] }, async ({ loginPage }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Verify the Welcome to Fieldr heading", async () => {
      await expect(loginPage.heading()).toBeVisible({ timeout: config.timeouts.ui });
    });
    await test.step("Verify the SECURE LOGIN label", async () => {
      await expect(loginPage.eyebrow()).toBeVisible({ timeout: config.timeouts.ui });
    });
    await test.step("Verify the helper text", async () => {
      await expect(loginPage.helper()).toBeVisible({ timeout: config.timeouts.ui });
    });
    await test.step("Verify the Mobile Number tab", async () => {
      await expect(loginPage.mobileTab()).toBeVisible({ timeout: config.timeouts.ui });
    });
    await test.step("Verify the Email Address tab", async () => {
      await expect(loginPage.emailTab()).toBeVisible({ timeout: config.timeouts.ui });
    });
    await test.step("Verify the Send OTP button", async () => {
      await expect(loginPage.sendOtpBtn()).toBeVisible({ timeout: config.timeouts.ui });
    });
    await test.step("Verify the Terms link target", async () => {
      await expect(loginPage.termsLink()).toHaveAttribute('href', /terms-and-conditions/);
    });
    await test.step("Verify the Privacy link target", async () => {
      await expect(loginPage.privacyLink()).toHaveAttribute('href', /privacy-policy/);
    });
  });
});

// FLD-AUTH-004 | P0 | Functional
// Preconditions: Logged out
// Expected: Heading, 'We sent a 6-digit OTP to' text and Digit 1 to Digit 6 boxes shown; Verify & Login disabled
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-004", () => {
  test("FLD-AUTH-004 Send OTP moves to the Check Your Messages step with six digit boxes", { tag: ["@P0", "@regression", "@auth"] }, async ({ loginPage }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Click the Mobile Number tab", async () => {
      await loginPage.clickMobileTab();
    });
    await test.step("Enter the QA mobile number in the mobile field", async () => {
      await loginPage.fillIdentifier(config.mobile);
    });
    await test.step("Click Send OTP", async () => {
      await loginPage.clickSendOtp();
    });
    await test.step("Wait for the Check Your Messages heading", async () => {
      await expect(loginPage.otpHeading()).toBeVisible({ timeout: config.timeouts.network });
    });
    await test.step("Verify the sent-to text", async () => {
      await expect(loginPage.otpSentTo()).toBeVisible({ timeout: config.timeouts.ui });
    });
    await test.step("Verify Digit 1 is visible", async () => {
      await expect(loginPage.otpDigit(1)).toBeVisible({ timeout: config.timeouts.ui });
    });
    await test.step("Verify Digit 2 is visible", async () => {
      await expect(loginPage.otpDigit(2)).toBeVisible({ timeout: config.timeouts.ui });
    });
    await test.step("Verify Digit 3 is visible", async () => {
      await expect(loginPage.otpDigit(3)).toBeVisible({ timeout: config.timeouts.ui });
    });
    await test.step("Verify Digit 4 is visible", async () => {
      await expect(loginPage.otpDigit(4)).toBeVisible({ timeout: config.timeouts.ui });
    });
    await test.step("Verify Digit 5 is visible", async () => {
      await expect(loginPage.otpDigit(5)).toBeVisible({ timeout: config.timeouts.ui });
    });
    await test.step("Verify Digit 6 is visible", async () => {
      await expect(loginPage.otpDigit(6)).toBeVisible({ timeout: config.timeouts.ui });
    });
    await test.step("Verify Verify & Login is disabled", async () => {
      await expect(loginPage.verifyBtn()).toBeDisabled({ timeout: config.timeouts.ui });
    });
  });
});

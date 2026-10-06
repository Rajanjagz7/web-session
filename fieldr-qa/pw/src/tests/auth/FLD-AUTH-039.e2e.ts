// FLD-AUTH-039 | P0 | Flaky
// Preconditions: OTP step shown
// Expected: After Resend OTP the countdown text returns at 30s or less
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-039", () => {
  test("FLD-AUTH-039 Resend restarts the countdown (throttle)", { tag: ["@P0", "@regression", "@auth", "@flaky"] }, async ({ loginPage }) => {
    test.slow();
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
    await test.step("Wait for the Resend OTP button", async () => {
      await expect(loginPage.resendBtn()).toBeEnabled({ timeout: config.timeouts.resend });
    });
    await test.step("Click Resend OTP", async () => {
      await loginPage.clickResend();
    });
    await test.step("Verify the countdown returns", async () => {
      await expect(loginPage.resendTimer()).toBeVisible({ timeout: config.timeouts.network });
    });
  });
});

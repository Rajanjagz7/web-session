// FLD-AUTH-014 | P1 | Flaky
// Preconditions: OTP step shown
// Expected: Resend OTP button enabled within 45s (time-sensitive)
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-014", () => {
  test("FLD-AUTH-014 Resend OTP button appears when the countdown ends", { tag: ["@P1", "@regression", "@auth", "@flaky"] }, async ({ loginPage }) => {
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
  });
});

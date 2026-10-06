// FLD-AUTH-015 | P1 | Functional
// Preconditions: OTP step shown
// Expected: No Resend OTP button while the countdown text shows
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-015", () => {
  test("FLD-AUTH-015 Resend OTP button is not offered during the countdown", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage }) => {
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
    await test.step("Verify the countdown text", async () => {
      await expect(loginPage.resendTimer()).toBeVisible({ timeout: config.timeouts.ui });
    });
    await test.step("Verify no Resend OTP button", async () => {
      await expect(loginPage.resendBtn()).toHaveCount(0, { timeout: config.timeouts.ui });
    });
  });
});

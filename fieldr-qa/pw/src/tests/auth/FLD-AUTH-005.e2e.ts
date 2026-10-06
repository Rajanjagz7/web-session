// FLD-AUTH-005 | P1 | Validation
// Preconditions: OTP step shown
// Expected: Verify & Login disabled
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-005", () => {
  test("FLD-AUTH-005 Verify & Login is disabled with an empty OTP", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage }) => {
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
    await test.step("Verify Verify & Login is disabled", async () => {
      await expect(loginPage.verifyBtn()).toBeDisabled({ timeout: config.timeouts.ui });
    });
  });
});

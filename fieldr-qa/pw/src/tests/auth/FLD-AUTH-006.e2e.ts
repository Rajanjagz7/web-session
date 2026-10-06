// FLD-AUTH-006 | P1 | Boundary
// Preconditions: OTP step shown
// Expected: Verify & Login disabled
import { test, expect } from '@fixtures';
import { config } from '@config/index';
import { AU } from '@testdata/au';

test.describe("FLD-AUTH-006", () => {
  test("FLD-AUTH-006 Verify & Login stays disabled with a 5-digit OTP (boundary min-1)", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage, loginModule }) => {
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
    await test.step("Enter five digits", async () => {
      await loginModule.enterOtp(AU.otp.fiveDigits);
    });
    await test.step("Verify Verify & Login is disabled", async () => {
      await expect(loginPage.verifyBtn()).toBeDisabled({ timeout: config.timeouts.ui });
    });
  });
});

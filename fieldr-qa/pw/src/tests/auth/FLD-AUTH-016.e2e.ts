// FLD-AUTH-016 | P1 | Functional
// Preconditions: OTP step shown
// Expected: Identifier step shown; OTP step hidden
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-016", () => {
  test("FLD-AUTH-016 Use a different number or email returns to the identifier step", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage }) => {
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
    await test.step("Click Use a different number or email", async () => {
      await loginPage.clickChangeIdentifier();
    });
    await test.step("Verify Send OTP is shown", async () => {
      await expect(loginPage.sendOtpBtn()).toBeVisible({ timeout: config.timeouts.ui });
    });
    await test.step("Verify the OTP step is hidden", async () => {
      await expect(loginPage.otpHeading()).toBeHidden({ timeout: config.timeouts.ui });
    });
  });
});

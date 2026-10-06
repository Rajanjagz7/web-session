// FLD-AUTH-003 | P0 | Functional
// Preconditions: QA number registered; bypass OTP configured
// Expected: Redirect to /app/dashboard; Dashboard heading visible
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-003", () => {
  test("FLD-AUTH-003 Mobile AU valid + correct OTP logs in to the dashboard", { tag: ["@P0", "@regression", "@auth", "@smoke"] }, async ({ loginPage, loginModule }) => {
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
    await test.step("Enter the 6-digit OTP into Digit 1 to Digit 6", async () => {
      await loginModule.enterOtp(config.otp);
    });
    await test.step("Click Verify & Login", async () => {
      await loginPage.clickVerify();
    });
    await test.step("Verify the dashboard is shown", async () => {
      await loginModule.expectOnDashboard();
    });
  });
});

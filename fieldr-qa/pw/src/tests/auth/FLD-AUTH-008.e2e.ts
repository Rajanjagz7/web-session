// FLD-AUTH-008 | P1 | Security
// Preconditions: OTP step shown
// Expected: Response body contains none of: not registered, no account, does not exist
import { test, expect } from '@fixtures';
import { config } from '@config/index';
import { AU } from '@testdata/au';

test.describe("FLD-AUTH-008", () => {
  test("FLD-AUTH-008 Wrong-OTP message does not reveal account existence", { tag: ["@P1", "@regression", "@auth", "@security"] }, async ({ loginPage, loginModule }) => {
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
    await test.step("Enter the wrong OTP", async () => {
      await loginModule.enterOtp(AU.otp.wrong);
    });
    await test.step("Click Verify & Login and capture the response", async () => {
      const response = await loginModule.verifyCapturing();
    });
    await test.step("Verify the body is generic", async () => {
      expect(await response.text()).not.toMatch(/not registered|no account|does not exist|doesn't exist/i);
    });
  });
});

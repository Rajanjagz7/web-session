// FLD-AUTH-007 | P0 | Negative
// Preconditions: OTP step shown
// Expected: HTTP 4xx (not 5xx); user stays on /login; dashboard not reachable
import { test, expect } from '@fixtures';
import { config } from '@config/index';
import { AU } from '@testdata/au';

test.describe("FLD-AUTH-007", () => {
  test("FLD-AUTH-007 Wrong OTP is rejected with a 4xx and no session", { tag: ["@P0", "@regression", "@auth"] }, async ({ loginPage, loginModule, page }) => {
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
    await test.step("Record the observed response body", async () => {
      test.info().annotations.push({ type: 'observed-response', description: `${response.status()} ${(await response.text()).slice(0, 300)}` });
    });
    await test.step("Verify the status is 4xx", async () => {
      expect(response.status()).toBeGreaterThanOrEqual(400);
      expect(response.status()).toBeLessThan(500);
    });
    await test.step("Verify the user is still on /login", async () => {
      await expect(page).toHaveURL(/\/login/);
    });
  });
});

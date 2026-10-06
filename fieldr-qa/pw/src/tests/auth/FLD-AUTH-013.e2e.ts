// FLD-AUTH-013 | P1 | Functional
// Preconditions: OTP step shown
// Expected: 'Resend OTP in Ns' with N <= 30
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-013", () => {
  test("FLD-AUTH-013 Resend countdown is shown and starts at 30s or less", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage }) => {
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
    await test.step("Verify the countdown is 30s or less", async () => {
      const text = (await loginPage.resendTimer().textContent()) ?? '';
      expect(Number(/(\d+)s/.exec(text)?.[1])).toBeLessThanOrEqual(30);
    });
  });
});

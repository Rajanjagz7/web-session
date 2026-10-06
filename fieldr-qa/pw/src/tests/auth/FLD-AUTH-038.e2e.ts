// FLD-AUTH-038 | P0 | Security
// Preconditions: FLDR_ALLOW_LOCKOUT=1 (may lock the shared QA account)
// Expected: 429 or a lock message before the 20th attempt
import { test, expect } from '@fixtures';
import { config } from '@config/index';
import { AU } from '@testdata/au';

test.describe("FLD-AUTH-038", () => {
  test("FLD-AUTH-038 Twenty wrong OTPs in 60s trigger a lock or rate limit", { tag: ["@P0", "@regression", "@auth", "@destructive", "@security"] }, async ({ loginPage, loginModule }) => {
    test.skip(!config.allowLockout, "Precondition not met: FLDR_ALLOW_LOCKOUT=1 (may lock the shared QA account)");
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
    await test.step("Submit wrong OTPs and stop at the first 429 or lock message", async () => {
      let limited = false;
      for (let attempt = 0; attempt < 20 && !limited; attempt += 1) {
        await loginModule.enterOtp(AU.otp.wrong);
        const response = await loginModule.verifyCapturing();
        limited = response.status() === 429 || /lock|too many|try again/i.test(await response.text());
      }
    });
    await test.step("Verify rate limiting kicked in", async () => {
      expect(limited).toBe(true);
    });
  });
});

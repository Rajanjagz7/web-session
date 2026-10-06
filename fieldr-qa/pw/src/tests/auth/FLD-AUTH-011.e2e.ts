// FLD-AUTH-011 | P1 | Functional
// Preconditions: OTP step shown
// Expected: Digits 1-6 hold the pasted digits (ASSUMPTION: paste is supported)
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-011", () => {
  test("FLD-AUTH-011 Pasting a 6-digit code fills all six boxes", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage, page }) => {
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
    await test.step("Focus Digit 1", async () => {
      await loginPage.otpDigit(1).focus();
    });
    await test.step("Dispatch a paste event with the OTP", async () => {
      await page.evaluate((code) => {
        const dt = new DataTransfer();
        dt.setData('text', code);
        document.activeElement?.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true }));
      }, config.otp);
    });
    await test.step("Verify Digit 1", async () => {
      await expect(loginPage.otpDigit(1)).toHaveValue(config.otp[0], { timeout: config.timeouts.ui });
    });
    await test.step("Verify Digit 2", async () => {
      await expect(loginPage.otpDigit(2)).toHaveValue(config.otp[1], { timeout: config.timeouts.ui });
    });
    await test.step("Verify Digit 3", async () => {
      await expect(loginPage.otpDigit(3)).toHaveValue(config.otp[2], { timeout: config.timeouts.ui });
    });
    await test.step("Verify Digit 4", async () => {
      await expect(loginPage.otpDigit(4)).toHaveValue(config.otp[3], { timeout: config.timeouts.ui });
    });
    await test.step("Verify Digit 5", async () => {
      await expect(loginPage.otpDigit(5)).toHaveValue(config.otp[4], { timeout: config.timeouts.ui });
    });
    await test.step("Verify Digit 6", async () => {
      await expect(loginPage.otpDigit(6)).toHaveValue(config.otp[5], { timeout: config.timeouts.ui });
    });
  });
});

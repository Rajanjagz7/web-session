// FLD-AUTH-009 | P1 | Validation
// Preconditions: OTP step shown
// Expected: Digit 1 stays empty
import { test, expect } from '@fixtures';
import { config } from '@config/index';
import { AU } from '@testdata/au';

test.describe("FLD-AUTH-009", () => {
  test("FLD-AUTH-009 OTP digit box rejects a letter", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage }) => {
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
    await test.step("Type a letter into Digit 1", async () => {
      await loginPage.typeIntoOtpDigit(1, AU.otp.letters);
    });
    await test.step("Verify Digit 1 is empty", async () => {
      await expect(loginPage.otpDigit(1)).toHaveValue('', { timeout: config.timeouts.ui });
    });
  });
});

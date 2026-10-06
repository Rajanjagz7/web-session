// FLD-AUTH-010 | P1 | Boundary
// Preconditions: OTP step shown
// Expected: Digit 1 value length <= 1
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-010", () => {
  test("FLD-AUTH-010 OTP digit box holds at most one character", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage }) => {
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
    await test.step("Type two digits into Digit 1", async () => {
      await loginPage.typeIntoOtpDigit(1, '12');
    });
    await test.step("Verify Digit 1 holds at most one character", async () => {
      expect((await loginPage.otpDigit(1).inputValue()).length).toBeLessThanOrEqual(1);
    });
  });
});

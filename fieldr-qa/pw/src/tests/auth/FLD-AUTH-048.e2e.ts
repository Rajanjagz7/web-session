// FLD-AUTH-048 | P1 | Security
// Preconditions: Logged out
// Expected: Response body contains neither the OTP nor an otp/code/passcode field with 6 digits
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-048", () => {
  test("FLD-AUTH-048 Send OTP response does not expose the OTP", { tag: ["@P1", "@regression", "@auth", "@security"] }, async ({ loginPage, loginModule }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Click the Mobile Number tab", async () => {
      await loginPage.clickMobileTab();
    });
    await test.step("Enter the QA mobile number", async () => {
      await loginPage.fillIdentifier(config.mobile);
    });
    await test.step("Click Send OTP and capture the response body", async () => {
      const body = await (await loginModule.sendOtpCapturing()).text();
    });
    await test.step("Verify the OTP is not in the body", async () => {
      expect(body).not.toContain(config.otp);
      expect(body).not.toMatch(/"(otp|code|passcode)"\s*:\s*"?\d{6}/i);
    });
  });
});

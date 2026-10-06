// FLD-AUTH-012 | P1 | Accessibility
// Preconditions: OTP step shown
// Expected: Six named textboxes; Verify & Login gets focus within 10 Tab presses once enabled
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-012", () => {
  test("FLD-AUTH-012 OTP boxes are named Digit 1 to Digit 6 and Verify is reachable by keyboard", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage, loginModule, page }) => {
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
    await test.step("Enter the OTP", async () => {
      await loginModule.enterOtp(config.otp);
    });
    await test.step("Verify the accessible name Digit 1", async () => {
      await expect(page.getByRole('textbox', { name: 'Digit 1' })).toHaveCount(1);
    });
    await test.step("Verify the accessible name Digit 2", async () => {
      await expect(page.getByRole('textbox', { name: 'Digit 2' })).toHaveCount(1);
    });
    await test.step("Verify the accessible name Digit 3", async () => {
      await expect(page.getByRole('textbox', { name: 'Digit 3' })).toHaveCount(1);
    });
    await test.step("Verify the accessible name Digit 4", async () => {
      await expect(page.getByRole('textbox', { name: 'Digit 4' })).toHaveCount(1);
    });
    await test.step("Verify the accessible name Digit 5", async () => {
      await expect(page.getByRole('textbox', { name: 'Digit 5' })).toHaveCount(1);
    });
    await test.step("Verify the accessible name Digit 6", async () => {
      await expect(page.getByRole('textbox', { name: 'Digit 6' })).toHaveCount(1);
    });
    await test.step("Press Tab until Verify & Login is focused", async () => {
      for (let i = 0; i < 10; i += 1) {
        if (await loginPage.verifyBtn().evaluate((el) => el === document.activeElement)) break;
        await loginPage.pressTab();
      }
    });
    await test.step("Verify Verify & Login is focused", async () => {
      await expect(loginPage.verifyBtn()).toBeFocused();
    });
  });
});

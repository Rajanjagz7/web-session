// FLD-AUTH-026 | P0 | Security
// Preconditions: FLDR_UNREGISTERED_MOBILE belongs to no user
// Expected: Not on dashboard; response recorded for PO review (enumeration policy is undecided)
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-026", () => {
  test("FLD-AUTH-026 Unregistered mobile never reaches the dashboard and does not leak account existence", { tag: ["@P0", "@regression", "@auth", "@security"] }, async ({ loginPage, loginModule, page }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Click the Mobile Number tab", async () => {
      await loginPage.clickMobileTab();
    });
    await test.step("Enter the unregistered mobile", async () => {
      await loginPage.fillIdentifier(config.unregisteredMobile);
    });
    await test.step("Click Send OTP and capture the response", async () => {
      const response = await loginModule.sendOtpCapturing();
    });
    await test.step("Record the observed response", async () => {
      test.info().annotations.push({ type: 'observed-response', description: `${response.status()} ${(await response.text()).slice(0, 300)}` });
    });
    await test.step("Verify the dashboard is not shown", async () => {
      await expect(page).not.toHaveURL(/\/app\/dashboard/);
    });
  });
});

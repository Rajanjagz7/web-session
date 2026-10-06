// FLD-AUTH-035 | P0 | Security
// Preconditions: Logged out
// Expected: Not on dashboard; response recorded
import { test, expect } from '@fixtures';
import { DataGenerator } from '@utils/DataGenerator';

test.describe("FLD-AUTH-035", () => {
  test("FLD-AUTH-035 Unregistered email never reaches the dashboard", { tag: ["@P0", "@regression", "@auth", "@security"] }, async ({ loginPage, loginModule, page }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Click the Email Address tab", async () => {
      await loginPage.clickEmailTab();
    });
    await test.step("Enter an unregistered email", async () => {
      await loginPage.fillIdentifier(DataGenerator.unregisteredEmail());
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

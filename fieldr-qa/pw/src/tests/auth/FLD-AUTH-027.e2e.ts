// FLD-AUTH-027 | P0 | Functional
// Preconditions: Logged out
// Expected: Identifier field shown without the Australia selector; Send OTP visible
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-027", () => {
  test("FLD-AUTH-027 Email Address tab replaces the mobile field and hides the country selector", { tag: ["@P0", "@regression", "@auth"] }, async ({ loginPage }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Click the Email Address tab", async () => {
      await loginPage.clickEmailTab();
    });
    await test.step("Verify the country selector is hidden", async () => {
      await expect(loginPage.countryButton()).toBeHidden({ timeout: config.timeouts.ui });
    });
    await test.step("Verify Send OTP is shown", async () => {
      await expect(loginPage.sendOtpBtn()).toBeVisible({ timeout: config.timeouts.ui });
    });
  });
});

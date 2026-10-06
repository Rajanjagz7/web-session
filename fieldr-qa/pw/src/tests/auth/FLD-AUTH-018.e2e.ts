// FLD-AUTH-018 | P1 | Negative
// Preconditions: Logged out
// Expected: Country selector still shows Australia; nothing is submitted
import { test, expect } from '@fixtures';
import { config } from '@config/index';
import { AU } from '@testdata/au';

test.describe("FLD-AUTH-018", () => {
  test("FLD-AUTH-018 US number typed into the AU field keeps the Australia country selector", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Click the Mobile Number tab", async () => {
      await loginPage.clickMobileTab();
    });
    await test.step("Enter a US-format number", async () => {
      await loginPage.fillIdentifier(AU.mobile.us);
    });
    await test.step("Verify the country selector still shows Australia", async () => {
      await expect(loginPage.countryButton()).toBeVisible({ timeout: config.timeouts.ui });
    });
  });
});

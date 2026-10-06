// FLD-AUTH-025 | P1 | Validation
// Preconditions: Logged out
// Expected: Value +61 (04) 4412 4222 (not submitted)
import { test, expect } from '@fixtures';
import { config } from '@config/index';
import { AU } from '@testdata/au';

test.describe("FLD-AUTH-025", () => {
  test("FLD-AUTH-025 Surrounding whitespace is ignored by the mobile mask", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Click the Mobile Number tab", async () => {
      await loginPage.clickMobileTab();
    });
    await test.step("Type the number with surrounding spaces", async () => {
      await loginPage.fillIdentifier('  0444124222 ');
    });
    await test.step("Verify the mask", async () => {
      await expect(loginPage.identifierInput()).toHaveValue(AU.mask('0444124222'), { timeout: config.timeouts.ui });
    });
  });
});

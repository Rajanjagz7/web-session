// FLD-AUTH-024 | P1 | Functional
// Preconditions: Logged out
// Expected: Observed mask +61 (04) 1234 5678 (not submitted)
import { test, expect } from '@fixtures';
import { config } from '@config/index';
import { AU } from '@testdata/au';

test.describe("FLD-AUTH-024", () => {
  test("FLD-AUTH-024 National format 0412 345 678 is masked as +61 (04) 1234 5678", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Click the Mobile Number tab", async () => {
      await loginPage.clickMobileTab();
    });
    await test.step("Type the national number", async () => {
      await loginPage.fillIdentifier('0412345678');
    });
    await test.step("Verify the mask", async () => {
      await expect(loginPage.identifierInput()).toHaveValue(AU.mask('0412345678'), { timeout: config.timeouts.ui });
    });
  });
});

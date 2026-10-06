// FLD-AUTH-023 | P1 | Boundary
// Preconditions: Logged out
// Expected: At most 10 digits after +61 (not submitted)
import { test, expect } from '@fixtures';
import { AU } from '@testdata/au';

test.describe("FLD-AUTH-023", () => {
  test("FLD-AUTH-023 Eleven-digit mobile is truncated to 10 national digits (boundary max+1)", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Click the Mobile Number tab", async () => {
      await loginPage.clickMobileTab();
    });
    await test.step("Type 11 digits", async () => {
      await loginPage.fillIdentifier(AU.mobile.elevenDigits);
    });
    await test.step("Verify at most 10 national digits", async () => {
      const digits = (await loginPage.identifierInput().inputValue()).replace(/^\+61/, '').replace(/\D/g, '');
      expect(digits.length).toBeLessThanOrEqual(10);
    });
  });
});

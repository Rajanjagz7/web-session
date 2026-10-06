// FLD-AUTH-019 | P1 | Validation
// Preconditions: Logged out
// Expected: Field value contains no letters (not submitted)
import { test, expect } from '@fixtures';
import { AU } from '@testdata/au';

test.describe("FLD-AUTH-019", () => {
  test("FLD-AUTH-019 Letters mixed into the mobile field are stripped", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Click the Mobile Number tab", async () => {
      await loginPage.clickMobileTab();
    });
    await test.step("Type digits mixed with letters", async () => {
      await loginPage.fillIdentifier(AU.mobile.lettersMixed);
    });
    await test.step("Verify no letters remain", async () => {
      expect(await loginPage.identifierInput().inputValue()).not.toMatch(/[A-Za-z]/);
    });
  });
});

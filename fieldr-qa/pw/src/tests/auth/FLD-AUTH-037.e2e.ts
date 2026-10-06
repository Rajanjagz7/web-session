// FLD-AUTH-037 | P0 | Security
// Preconditions: Needs a single-use live OTP
// Expected: Second use rejected
import { test, expect } from '@fixtures';

test.describe("FLD-AUTH-037", () => {
  test("FLD-AUTH-037 A used OTP cannot be replayed", { tag: ["@P0", "@regression", "@auth", "@security"] }, async ({  }) => {
    test.fixme(true, "Static bypass OTP is reusable by design; test manually with a live OTP");
    await test.step("Log in once with a live OTP, log out, then reuse the same OTP", async () => {
      // The QA bypass OTP is static, so replay cannot be tested with it.
    });
  });
});

// FLD-AUTH-036 | P0 | Negative
// Preconditions: Needs a real OTP that has expired
// Expected: Expired message and a Resend OTP option
import { test, expect } from '@fixtures';

test.describe("FLD-AUTH-036", () => {
  test("FLD-AUTH-036 Expired OTP prompts the user to resend", { tag: ["@P0", "@regression", "@auth"] }, async ({  }) => {
    test.fixme(true, "QA bypass OTP never expires; run manually with a live SMS OTP (window length unknown - ask PO)");
    await test.step("Request an OTP and wait past its validity window", async () => {
      // The QA bypass OTP never expires, so this case needs a live SMS OTP.
    });
  });
});

import { test, expect, Page } from "@playwright/test";

// Lender contact phone validation (front end). Writes are intercepted: nothing is created.
// Rules used (national significant number): India 10 digits starting 6-9; Australia 9 digits starting 2, 3, 4, 7 or 8.

type Sent = { target: string; body: any };

async function openForm(page: Page, country: string) {
  const sent: Sent[] = [];
  await page.route("**/api/proxy", (route) => {
    const q = route.request();
    if (q.method() === "GET") return route.continue();
    sent.push({ target: q.headers()["x-target-endpoint"], body: JSON.parse(q.postData() || "null") });
    return route.abort();
  });
  await page.goto("/lenders?create=1");
  await page.locator("#lender-contact-phone").waitFor({ state: "visible" });
  if (country !== "Australia") {
    await page.getByRole("button", { name: /Australia|\+ ?61|country/i }).first().click();
    await page.getByText(country, { exact: true }).first().click();
  }
  await page.locator('[name="name"]').fill("Harbour Credit Partners");
  await page.locator('[name="legalName"]').fill("Harbour Credit Partners Pty Ltd");
  await page.locator('[name="abn"]').fill("48 123 123 124");
  await page.locator('[name="contactName"]').fill("Aarav Mehta");
  await page.locator('[name="contactEmail"]').fill("aarav.mehta@yopmail.com");
  return sent;
}

async function submitPhone(page: Page, sent: Sent[], value: string) {
  sent.length = 0;
  await page.locator("#lender-contact-phone").fill(value);
  await page.getByRole("button", { name: "Create lender" }).click();
  await page.waitForTimeout(600);
  return sent.find((s) => s.target === "/lenders");
}

test.describe("Lender contact phone - India (PHONE-IN)", () => {
  for (const ok of ["9876543210", "6000000001", "7012345678", "8123456789"]) {
    test(`PHONE-IN-001: valid Indian mobile ${ok} is accepted and sent as +91${ok}`, async ({ page }) => {
      const sent = await openForm(page, "India");
      const post = await submitPhone(page, sent, ok);
      expect(post?.body.contactPhone).toBe(`+91${ok}`);
    });
  }

  for (const bad of ["123456789", "1234567890", "98765432101", "5876543210"]) {
    test(`PHONE-IN-002: invalid Indian number ${bad} is blocked with an error`, async ({ page }) => {
      test.fail(true, "GUS-FX-0023: the form only strips non-digits and sends any digits (needs 10 digits starting 6-9)");
      const sent = await openForm(page, "India");
      const post = await submitPhone(page, sent, bad);
      expect(post, `sent ${post?.body.contactPhone}`).toBeUndefined();
    });
  }

  test("PHONE-IN-003: letters are not accepted in the phone field", async ({ page }) => {
    const sent = await openForm(page, "India");
    const post = await submitPhone(page, sent, "abcdefghij");
    expect(post).toBeUndefined();
    await expect(page.getByText(/phone number is required/i).first()).toBeVisible();
  });

  test("PHONE-IN-004: spaces, dashes and a leading zero are normalised", async ({ page }) => {
    const sent = await openForm(page, "India");
    for (const v of ["98765 43210", "98765-43210", "09876543210"]) {
      const post = await submitPhone(page, sent, v);
      expect(post?.body.contactPhone).toBe("+919876543210");
    }
  });
});

test.describe("Lender contact phone - Australia and other countries (PHONE-AU)", () => {
  for (const ok of ["412345678", "255501234", "755501234"]) {
    test(`PHONE-AU-001: valid Australian number ${ok} is accepted`, async ({ page }) => {
      const sent = await openForm(page, "Australia");
      const post = await submitPhone(page, sent, ok);
      expect(post?.body.contactPhone).toBe(`+61${ok}`);
    });
  }

  for (const bad of ["123456789", "1234567890", "41234567", "912345678"]) {
    test(`PHONE-AU-002: invalid Australian number ${bad} is blocked`, async ({ page }) => {
      test.fail(true, "GUS-FX-0023: no country rules; any digits are sent (needs 9 digits starting 2, 3, 4, 7 or 8)");
      const sent = await openForm(page, "Australia");
      const post = await submitPhone(page, sent, bad);
      expect(post, `sent ${post?.body.contactPhone}`).toBeUndefined();
    });
  }

  for (const [country, bad] of [["United States", "123456"], ["United Kingdom", "12345"]] as const) {
    test(`PHONE-XX-001: ${country} number ${bad} (too short) is blocked`, async ({ page }) => {
      test.fail(true, "GUS-FX-0023: a 5-6 digit number is sent for any country");
      const sent = await openForm(page, country);
      const post = await submitPhone(page, sent, bad);
      expect(post).toBeUndefined();
    });
  }

  for (const country of ["Australia", "India", "United States"]) {
    test(`PHONE-XX-002: the placeholder example matches the selected country (${country})`, async ({ page }) => {
      test.fail(country !== "Australia" ? true : false, "GUS-FX-0024: placeholder stays '412 555 012' (an Australian mobile) for every country");
      await openForm(page, country);
      const ph = await page.locator("#lender-contact-phone").getAttribute("placeholder");
      if (country === "Australia") expect(ph).toBe("412 555 012");
      else expect(ph).not.toBe("412 555 012");
    });
  }
});

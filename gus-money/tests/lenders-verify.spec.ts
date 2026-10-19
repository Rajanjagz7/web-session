import { test, expect, type Page } from "@playwright/test";

// Regression tests for bugs fixed on dev (verified 2026-10-07): GUS-FX-0015 logo upload, GUS-FX-0016 ABN checksum,
// GUS-FX-0017 lender counts, GUS-FX-0019 avatar link names. The final lender save is always aborted: nothing is created.
const LOGO = "tests/fixtures/logo.png";

async function openLenderForm(page: Page) {
  const sent: { target: string; body: string | null }[] = [];
  await page.route("**/api/proxy", (route) => {
    const q = route.request();
    if (q.method() === "GET") return route.continue();
    const target = q.headers()["x-target-endpoint"] ?? "";
    if (target !== "/lenders") return route.continue(); // presign and the logo upload must go through
    sent.push({ target, body: q.postData() });
    return route.abort();
  });
  await page.goto("/lenders?create=1");
  await page.locator("#lender-logo-file").waitFor({ state: "attached" });
  return sent;
}

async function fillLender(page: Page, abn: string) {
  await page.locator('[name="name"]').fill("Harbour Credit Partners");
  await page.locator('[name="legalName"]').fill("Harbour Credit Partners Pty Ltd");
  await page.locator('[name="abn"]').fill(abn);
  await page.locator('[name="contactName"]').fill("Aarav Mehta");
  await page.locator('[name="contactEmail"]').fill("aarav.mehta@yopmail.com");
  await page.locator("#lender-contact-phone").fill("2 5550 1234");
}

test.describe("Lenders - verified fixes (LV)", () => {
  test("LV-001: GUS-FX-0015 a chosen logo is uploaded without a CORS error and reaches the lender payload", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
    const sent = await openLenderForm(page);
    await page.locator("#lender-logo-file").setInputFiles(LOGO);
    await expect.poll(async () => page.locator('[role="dialog"] img, main img').count()).toBeGreaterThan(0);
    await fillLender(page, "51 824 753 556");
    await page.getByRole("button", { name: "Create lender" }).click();
    await expect.poll(() => sent.length).toBeGreaterThan(0);
    expect(Object.keys(JSON.parse(sent[0]?.body ?? "{}"))).toContain("logo");
    expect(errors.filter((e) => /CORS|blocked by CORS|Failed to fetch/i.test(e))).toEqual([]);
  });

  test("LV-002: GUS-FX-0016 an ABN that fails the checksum is blocked in the form", async ({ page }) => {
    const sent = await openLenderForm(page);
    await fillLender(page, "48 123 123 125"); // checksum fails
    await page.getByRole("button", { name: "Create lender" }).click();
    await expect(page.getByText(/valid ABN/i).first()).toBeVisible();
    expect(sent).toHaveLength(0);
  });

  test("LV-003: GUS-FX-0019 no user link has its name repeated in its accessible name", async ({ page }) => {
    await page.goto("/users");
    await expect(page.locator('tbody a[href^="/users/"]').first()).toBeVisible();
    const names = await page.locator('tbody a[href^="/users/"]').evaluateAll((as) => as.map((a) => (a.textContent ?? "").replace(/\s+/g, " ").trim()));
    expect(names.filter((n) => /^(.+) \1$/.test(n))).toEqual([]);
    await expect(page.getByRole("link", { name: /^(.+) \1$/ })).toHaveCount(0);
  });

  test("LV-004: GUS-FX-0017 lender counts read 'N active of M' whenever some products are inactive", async ({ page }) => {
    await page.goto("/lenders");
    await expect(page.locator("tbody tr").first()).toBeVisible();
    const call = (target: string) => page.request.get(`https://gusdev.softwareco.com/api/proxy?skip=0&limit=100`, { headers: { "x-target-endpoint": target } }).then((r) => r.json());
    const products = (await call("/products")).data as { isActive: boolean; lender: { name: string } }[];
    const headers = await page.locator("thead th").allInnerTexts();
    const col = headers.findIndex((h) => /products/i.test(h));
    const cells = await page.locator("tbody tr").evaluateAll((rows, c) => rows.map((r) => {
      const td = r.querySelectorAll("td");
      return [(td[0]?.textContent ?? "").replace(/\s+/g, " ").trim(), (td[c]?.textContent ?? "").replace(/\s+/g, " ").trim()] as [string, string];
    }), col);
    for (const [lender, text] of cells) {
      const mine = products.filter((p) => lender.endsWith(p.lender.name));
      const active = mine.filter((p) => p.isActive).length;
      const expected = active === mine.length ? String(mine.length) : `${active} active of ${mine.length}`;
      if (mine.length > 0) expect(text, `${lender}`).toBe(expected);
    }
  });
});

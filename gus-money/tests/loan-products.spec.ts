import { test, expect } from "@playwright/test";
import { LoanProductsPage, SEEDED_ID } from "../pages/LoanProductsPage";

// Loan Products - negative, edge and boundary UI tests.
// Safe by construction: all writes are intercepted (LoanProductsPage.interceptWrites) so nothing is ever
// created/changed/deleted on gusdev and no server write quota is used. Rendering edge cases use mocked list data.

const BAD_TEXT = /undefined|NaN|\[object|null\b/;

test.describe("Loan products list (LP-LIST)", () => {
  let lp: LoanProductsPage;
  test.beforeEach(async ({ page }) => {
    lp = new LoanProductsPage(page);
    await lp.interceptWrites();
  });

  test("LP-001: list renders heading, filters, columns and Add product", async ({ page }) => {
    await lp.gotoList();
    await expect(lp.addButton).toBeVisible();
    for (const name of ["Lender", "Product type", "Status"]) {
      await expect(page.getByRole("combobox", { name, exact: true })).toBeVisible();
    }
    for (const col of ["Product", "Lender", "Type", "Interest rate", "Comparison rate", "Amount", "Terms", "Status", "Created", "Actions"]) {
      await expect(page.locator("thead th").filter({ hasText: col }).first()).toBeVisible();
    }
  });

  test("LP-002: status=Inactive shows only inactive products, or an empty state", async ({ page }) => {
    await lp.gotoList();
    await lp.pick("Status", "Inactive");
    await expect(page.locator("tbody")).not.toBeEmpty();
    await expect.poll(async () => (await page.getByText(/^Showing /).count()) + (await page.getByText(/no matching products/i).count())).toBeGreaterThan(0);
    const statuses = await page.locator('tbody tr:has(a[href^="/loan-products/"]) td:nth-child(8)').allInnerTexts();
    if (statuses.length === 0) await expect(page.getByText(/no matching products/i).first()).toBeVisible();
    for (const s of statuses) expect(s.trim()).toBe("Inactive");
  });

  test("LP-003: type filter only returns that type", async ({ page }) => {
    await lp.gotoList();
    await lp.pick("Product type", "Pet Loan");
    await expect(lp.rows.first()).toBeVisible();
    for (const t of await page.locator("tbody tr td:nth-child(3)").allInnerTexts()) expect(t).toBe("Pet Loan");
  });

  test("LP-004: type + status + search with no match is handled gracefully", async ({ page }) => {
    await lp.gotoList();
    await lp.pick("Product type", "Car Loan");
    await lp.pick("Status", "Active");
    await lp.search.fill("zzzz_no_such_product");
    await expect(page.locator('tbody a[href^="/loan-products/"]')).toHaveCount(0);
    await expect(page.getByText(/no matching products/i).first()).toBeVisible();
  });

  test("LP-005: Clear resets search and filters", async ({ page }) => {
    await lp.gotoList();
    const before = await page.locator('tbody a[href^="/loan-products/"]').count();
    await lp.pick("Product type", "Car Loan");
    await lp.search.fill("zzzz");
    await page.getByRole("button", { name: "Clear", exact: true }).click();
    await expect(lp.search).toHaveValue("");
    await expect(page.locator('tbody a[href^="/loan-products/"]')).toHaveCount(before);
  });

  for (const term of ["<img src=x onerror=alert(1)>", "' OR '1'='1", '{"$ne":1}', "%", "(", "😀", "a".repeat(101)]) {
    test(`LP-006: hostile/edge search input is inert: ${term.slice(0, 20)}`, async ({ page }) => {
      let dialog = false;
      page.on("dialog", async (d) => { dialog = true; await d.dismiss(); });
      await lp.gotoList();
      await lp.search.fill(term);
      await page.waitForTimeout(1200);
      expect(dialog).toBe(false);
      await expect(lp.heading).toBeVisible();
      await expect(page.getByText(/internal|unhandled|something went wrong|stack/i)).toHaveCount(0);
    });
  }

  test("LP-007: unauthenticated visits are redirected to sign-in", async ({ browser }) => {
    const ctx = await browser.newContext({ storageState: { cookies: [], origins: [] } });
    const page = await ctx.newPage();
    for (const path of ["/loan-products", "/loan-products/new", `/loan-products/${SEEDED_ID}`, `/loan-products/${SEEDED_ID}/edit`]) {
      await page.goto(path);
      await expect(page).toHaveURL(/sign-in/);
    }
    await ctx.close();
  });
});

test.describe("Loan products list - rendering edge cases with mocked data (LP-RENDER)", () => {
  let lp: LoanProductsPage;
  const P = LoanProductsPage.product;
  test.beforeEach(async ({ page }) => {
    lp = new LoanProductsPage(page);
    await lp.interceptWrites();
  });

  test("LP-010: HTML in a product name is rendered as text (no injection)", async ({ page }) => {
    let dialog = false;
    page.on("dialog", async (d) => { dialog = true; await d.dismiss(); });
    await lp.mockList([P({ name: "<img src=x onerror=alert(1)>Home <b>Saver</b>" })]);
    await lp.gotoList();
    await expect(page.locator("tbody a", { hasText: "Home" }).first()).toContainText("<b>Saver</b>");
    expect(dialog).toBe(false);
    await expect(page.locator("tbody img[src='x']")).toHaveCount(0);
  });

  test("LP-011: 120-character name does not overflow the page", async ({ page }) => {
    await lp.mockList([P({ name: "N".repeat(120) })]);
    await lp.gotoList();
    await expect(lp.rows.first()).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
    expect(overflow, "page scrolls horizontally with a 120-char name").toBe(false);
  });

  test("LP-012: rate and amount boundaries format correctly", async () => {
    await lp.mockList([
      P({ name: "Zero Rate Loan", interestRateBps: 0, comparisonRateBps: 0, minAmountCents: 0, maxAmountCents: 100 }),
      P({ name: "Full Rate Loan", interestRateBps: 10000, comparisonRateBps: 10000, minAmountCents: 1, maxAmountCents: 99999999999 })
    ]);
    await lp.gotoList();
    const zero = lp.rows.filter({ hasText: "Zero Rate Loan" });
    await expect(zero).toContainText("0.00%");
    await expect(zero).toContainText("$0.00 – $1.00");
    const full = lp.rows.filter({ hasText: "Full Rate Loan" });
    await expect(full).toContainText("100.00%");
    await expect(full).toContainText("$0.01 – $999,999,999.99");
  });

  test("LP-013: missing/empty terms and lender never render undefined/NaN/null", async ({ page }) => {
    await lp.mockList([
      P({ name: "No Term Loan", termMonths: [] }),
      P({ name: "No Lender Loan", lender: null, lenderId: null }),
      P({ name: "Many Terms Loan", termMonths: [12, 24, 36, 48, 60, 72, 84, 96] })
    ]);
    await lp.gotoList();
    await expect(lp.rows.first()).toBeVisible();
    expect(await page.locator("tbody").innerText()).not.toMatch(BAD_TEXT);
  });

  test("LP-014: list API failure shows a message, not a blank or crashed page", async ({ page }) => {
    await lp.mockList([], 500, { success: false, message: "Something went wrong", code: "INTERNAL" });
    await page.goto("/loan-products");
    await expect(lp.heading).toBeVisible();
    await expect(page.getByText(/something went wrong|try again|unable|failed|error/i).first()).toBeVisible();
  });

  test("LP-015: rate-limited list (429) is explained to the user", async ({ page }) => {
    await lp.mockList([], 429, { success: false, message: "Too many requests", code: "RATE_LIMITED" });
    await page.goto("/loan-products");
    await expect(lp.heading).toBeVisible();
    await expect(page.getByText(/too many|rate|try again|wait/i).first()).toBeVisible();
  });
});

test.describe("Add loan product - validation (LP-ADD)", () => {
  let lp: LoanProductsPage;
  test.beforeEach(async ({ page }) => {
    lp = new LoanProductsPage(page);
    await lp.interceptWrites();
    await lp.gotoNew();
  });

  test("LP-020: empty submit shows required errors and sends nothing", async ({ page }) => {
    await lp.submit();
    for (const msg of ["Select a lender", "Select a type", "Enter a valid name", "Enter a valid interest rate", "Enter a valid minimum amount", "Enter a valid maximum amount"]) {
      await expect(page.getByText(msg).first()).toBeVisible();
    }
    expect(lp.writes).toHaveLength(0);
  });

  for (const bad of ["abc", "-1", "7.495", "7,49", "1e2", " ", "--5", "7.4.9"]) {
    test(`LP-021: interest rate "${bad}" is blocked client-side`, async () => {
      await lp.fillValid({ "Interest rate (%)": bad });
      await lp.submit();
      expect(lp.writes, `request sent for rate "${bad}"`).toHaveLength(0);
    });
  }

  test("LP-022: interest rate above 100% is blocked client-side", async () => {
    // fixed on dev 2026-10-06 (previously expected to fail)
    await lp.fillValid({ "Interest rate (%)": "101" });
    await lp.submit();
    expect(lp.writes).toHaveLength(0);
  });

  test("LP-023: comparison rate above 100% is blocked client-side", async () => {
    // fixed on dev 2026-10-06 (previously expected to fail)
    await lp.fillValid({ "Comparison rate (%)": "150" });
    await lp.submit();
    expect(lp.writes).toHaveLength(0);
  });

  test("LP-024: minimum greater than maximum is blocked", async ({ page }) => {
    await lp.fillValid({ "Minimum amount (AUD)": "60000", "Maximum amount (AUD)": "50000" });
    await lp.submit();
    expect(lp.writes).toHaveLength(0);
    await expect(page.getByText("Maximum must be at least the minimum")).toBeVisible();
  });

  test("LP-025: a negative minimum amount gets its own clear message", async ({ page }) => {
    await lp.fillValid({ "Minimum amount (AUD)": "-5" });
    await lp.submit();
    expect(lp.writes).toHaveLength(0);
    await expect(page.getByText("Maximum must be at least the minimum")).toHaveCount(0);
    await expect(page.getByText(/valid minimum amount|cannot be negative/i).first()).toBeVisible();
  });

  for (const bad of ["abc", "5000.123", "1e3"]) {
    test(`LP-026: amount "${bad}" is blocked`, async () => {
      await lp.fillValid({ "Minimum amount (AUD)": bad });
      await lp.submit();
      expect(lp.writes).toHaveLength(0);
    });
  }

  test("LP-026b: a thousands separator in an amount is parsed, not mangled", async () => {
    await lp.interceptWrites(() => ({ status: 201, body: { success: true, message: "Product created", data: {} } }));
    await lp.fillValid({ "Minimum amount (AUD)": "1,000" });
    await lp.submit();
    expect(lp.writes[lp.writes.length - 1].body.minAmountCents).toBe(100000);
  });

  test("LP-027: whitespace-only name is blocked", async () => {
    await lp.fillValid({ Name: "   " });
    await lp.submit();
    expect(lp.writes).toHaveLength(0);
  });

  test("LP-028: 121-character name is blocked or truncated to 120", async () => {
    // fixed on dev 2026-10-06 (previously expected to fail)
    await lp.fillValid({ Name: "N".repeat(121) });
    await lp.submit();
    if (lp.writes.length) expect(lp.writes[0].body.name.length).toBeLessThanOrEqual(120);
  });

  test("LP-029: submitting with no term selected is allowed", async ({ page }) => {
    // Decision 2026-10-05: a product with no term is allowed.
    await lp.pick("Lender", "Preventive Health Review");
    await lp.pick("Type", "Home Loan");
    await page.locator("#product-name").fill("Home Saver Variable");
    for (const [l, v] of Object.entries({ "Interest rate (%)": "6.19", "Minimum amount (AUD)": "20000", "Maximum amount (AUD)": "900000" })) await lp.field(l).fill(v);
    await lp.submit();
    expect(lp.writes).toHaveLength(1);
    expect(lp.writes[0].body.termMonths ?? []).toEqual([]);
  });

  test("LP-050: lender dropdown offers only active lenders", async ({ page }) => {
    const res = await page.request.get("/api/proxy?skip=0&limit=100", { headers: { "x-target-endpoint": "/lenders" } });
    const lenders: { name: string; isActive: boolean }[] = (await res.json()).data;
    const active = lenders.filter((l) => l.isActive).map((l) => l.name).sort();
    const inactive = lenders.filter((l) => !l.isActive).map((l) => l.name);
    await page.getByRole("combobox", { name: "Lender", exact: true }).click();
    await expect(page.getByRole("option").first()).toBeVisible();
    await expect.poll(async () => (await page.getByRole("option").allInnerTexts()).sort()).toEqual(active);
    for (const name of inactive) expect(await page.getByRole("option", { name, exact: true }).count()).toBe(0);
  });

  test("LP-051: a $0.00 - $0.00 amount range is blocked client-side", async ({ page }) => {
    await lp.fillValid({ "Minimum amount (AUD)": "0", "Maximum amount (AUD)": "0" });
    await lp.submit();
    expect(lp.writes).toHaveLength(0);
    await expect(page.getByText("Enter an amount range greater than $0.00").first()).toBeVisible();
  });

  test("LP-052: comparison rate below the interest rate is not blocked", async () => {
    // Decision 2026-10-05: no comparison-rate validation for now.
    await lp.fillValid({ "Interest rate (%)": "7.49", "Comparison rate (%)": "7.00" });
    await lp.submit();
    expect(lp.writes).toHaveLength(1);
    expect(lp.writes[0].body.comparisonRateBps).toBe(700);
  });

  for (const bad of ["0", "-5", "abc", "12.5", ""]) {
    test(`LP-030: custom term "${bad}" is not added`, async ({ page }) => {
      await lp.field("Custom months").fill(bad);
      await page.getByRole("button", { name: "Add", exact: true }).click();
      await expect(page.getByRole("button", { name: /^(0|-5|601|abc|12\.5) mo$/ })).toHaveCount(0);
    });
  }

  test("LP-030b: custom term above the 600-month maximum is not added", async ({ page }) => {
    // fixed on dev 2026-10-06 (previously expected to fail)
    await lp.field("Custom months").fill("601");
    await page.getByRole("button", { name: "Add", exact: true }).click();
    await expect(page.getByRole("button", { name: "601 mo" })).toHaveCount(0);
  });

  test("LP-031: valid custom term 18 is added once even if added twice", async ({ page }) => {
    for (let i = 0; i < 2; i++) {
      await lp.field("Custom months").fill("18");
      await page.getByRole("button", { name: "Add", exact: true }).click();
    }
    await expect(page.getByRole("button", { name: "18 mo" })).toHaveCount(1);
  });

  for (const [label, val] of [["Minimum age (years)", "-1"], ["Maximum age (years)", "200"], ["Minimum age (years)", "18.5"], ["Maximum debt-to-income", "abc"], ["Minimum income (AUD / year)", "-1"], ["Minimum monthly surplus (AUD)", "-1"]] as const) {
    test(`LP-032: criteria "${label}" = ${val} is blocked with an error`, async ({ page }) => {
      // Maximum age 200 is blocked today; the other four values are silently dropped and the product is still submitted.
      if (!(label === "Maximum age (years)")) test.fail(true, "GUS-FX-0012: invalid criteria value is silently dropped, no error, form still submits");
      await lp.fillValid();
      await lp.field(label).fill(val);
      await lp.submit();
      expect(lp.writes, `${label}=${val} was sent`).toHaveLength(0);
    });
  }

  test("LP-033: minimum age above maximum age is blocked", async () => {
    await lp.fillValid();
    await lp.field("Minimum age (years)").fill("70");
    await lp.field("Maximum age (years)").fill("30");
    await lp.submit();
    expect(lp.writes).toHaveLength(0);
  });

  test("LP-034: a fee with a negative amount or no name is blocked", async ({ page }) => {
    await lp.fillValid();
    await page.getByRole("button", { name: "Add fee" }).click();
    await lp.submit();
    expect(lp.writes, "empty fee row was submitted").toHaveLength(0);
    await page.locator('[name="fees.0.name"]').fill("Establishment fee");
    await page.locator('[name="fees.0.amount"]').fill("-10");
    await lp.submit();
    expect(lp.writes, "negative fee was submitted").toHaveLength(0);
  });

  test("LP-035: valid form sends exact integer basis points and cents (no float drift)", async () => {
    await lp.interceptWrites(() => ({ status: 201, body: { success: true, message: "Product created", data: {} } }));
    await lp.fillValid({ "Interest rate (%)": "1.15", "Comparison rate (%)": "4.35", "Minimum amount (AUD)": "5000.10", "Maximum amount (AUD)": "19999.99" });
    await lp.submit();
    const b = lp.writes[lp.writes.length - 1].body;
    expect(b.interestRateBps).toBe(115);
    expect(b.comparisonRateBps).toBe(435);
    expect(b.minAmountCents).toBe(500010);
    expect(b.maxAmountCents).toBe(1999999);
    expect(Number.isInteger(b.interestRateBps) && Number.isInteger(b.minAmountCents)).toBe(true);
  });

  test("LP-036: double-click on Create product sends one request", async ({ page }) => {
    const hits: number[] = [];
    await page.unroute("**/api/proxy");
    const lp2 = new LoanProductsPage(page);
    await lp2.interceptWrites((w) => { hits.push(1); return { status: 201, body: { success: true, message: "Product created", data: { _id: "6abde76fe6b189801e58bbbb" } }, delayMs: 800 }; });
    await lp2.fillValid();
    await lp2.createButton.dblclick();
    await page.waitForTimeout(1500);
    expect(hits.length, "duplicate create requests").toBe(1);
  });

  test("LP-037: server validation error (422) is shown inline and the form keeps its data", async ({ page }) => {
    // The form now blocks rates above 100% itself (GUS-FX-0010 fixed), so a server 422 is simulated on a field the form does not check.
    await page.unroute("**/api/proxy");
    const lp2 = new LoanProductsPage(page);
    await lp2.interceptWrites(() => ({ status: 422, body: { success: false, message: "Validation failed", code: "VALIDATION_ERROR", details: [{ field: "name", message: "That name is not allowed" }] } }));
    await lp2.gotoNew();
    await lp2.fillValid();
    await lp2.submit();
    await expect(page.getByText(/that name is not allowed/i).first()).toBeVisible();
    await expect(page.locator("#product-name")).toHaveValue("Everyday Personal Loan");
    await expect(page).toHaveURL(/loan-products\/new/);
  });

  test("LP-038: server 500 and 429 on create show a message and keep the form", async ({ page }) => {
    for (const [status, body] of [[500, { success: false, message: "Something went wrong", code: "INTERNAL" }], [429, { success: false, message: "Too many requests", code: "RATE_LIMITED" }]] as const) {
      await page.unroute("**/api/proxy");
      const lp2 = new LoanProductsPage(page);
      await lp2.interceptWrites(() => ({ status, body }));
      await lp2.gotoNew();
      await lp2.fillValid();
      await lp2.submit();
      await expect(page.getByText(/something went wrong|too many|try again/i).first()).toBeVisible();
      await expect(lp2.field("Interest rate (%)")).toHaveValue("7.49");
    }
  });

  test("LP-039: Cancel returns to the list without sending anything", async ({ page }) => {
    await lp.fillValid();
    await page.getByRole("button", { name: "Cancel" }).click();
    await expect(page).toHaveURL(/\/loan-products$/);
    expect(lp.writes).toHaveLength(0);
  });
});

test.describe("Loan product detail, edit and stop-offering (LP-DETAIL)", () => {
  let lp: LoanProductsPage;
  test.beforeEach(async ({ page }) => {
    lp = new LoanProductsPage(page);
    await lp.interceptWrites();
  });

  test("LP-040: malformed product id shows a friendly not-found, not a raw validation error", async ({ page }) => {
    // fixed on dev 2026-10-06 (previously expected to fail)
    await page.goto("/loan-products/zzz");
    await expect(page.getByText("Product not found")).toBeVisible();
    await expect(page.getByText("Validation failed")).toHaveCount(0);
  });

  test("LP-041: unknown product id shows not-found and Back works", async ({ page }) => {
    await page.goto("/loan-products/000000000000000000000000");
    await expect(page.getByText("Product not found")).toBeVisible();
    await page.getByRole("link", { name: "Back to products" }).click();
    await expect(page).toHaveURL(/\/loan-products$/);
  });

  test("LP-042: edit of an unknown product shows not-found, not an empty form", async ({ page }) => {
    await page.goto("/loan-products/000000000000000000000000/edit");
    await expect(page.getByText(/not found/i).first()).toBeVisible();
    await expect(page.locator("#product-name")).toHaveCount(0);
  });

  test("LP-043: edit form is pre-filled with the stored values", async ({ page }) => {
    await page.goto(`/loan-products/${SEEDED_ID}/edit`);
    await expect(page.locator("#product-name")).toHaveValue("Angelique Morse");
    await expect(lp.field("Interest rate (%)")).toHaveValue("10.00");
    await expect(lp.field("Minimum amount (AUD)")).toHaveValue("100000.00");
  });

  for (const [label, bad] of [["Interest rate (%)", "-1"], ["Interest rate (%)", "abc"], ["Maximum amount (AUD)", "-5"]] as const) {
    test(`LP-044: edit with ${label} = ${bad} is blocked`, async ({ page }) => {
      await page.goto(`/loan-products/${SEEDED_ID}/edit`);
      await expect(page.locator("#product-name")).toHaveValue("Angelique Morse");
      await lp.field(label).fill(bad);
      await page.getByRole("button", { name: "Save changes" }).click();
      await page.waitForTimeout(600);
      expect(lp.writes).toHaveLength(0);
    });
  }

  test("LP-045: clearing the name on edit is blocked", async ({ page }) => {
    await page.goto(`/loan-products/${SEEDED_ID}/edit`);
    await page.locator("#product-name").fill("");
    await page.getByRole("button", { name: "Save changes" }).click();
    await page.waitForTimeout(600);
    expect(lp.writes).toHaveLength(0);
  });

  test("LP-046: edit sends only the changed field", async ({ page }) => {
    await page.unroute("**/api/proxy");
    const lp2 = new LoanProductsPage(page);
    await lp2.interceptWrites(() => ({ status: 200, body: { success: true, message: "Product updated", data: {} } }));
    await page.goto(`/loan-products/${SEEDED_ID}/edit`);
    await expect(page.locator("#product-name")).toHaveValue("Angelique Morse");
    await page.getByRole("textbox", { name: "Description" }).fill("Pet loan for veterinary expenses.");
    await page.getByRole("button", { name: "Save changes" }).click();
    await page.waitForTimeout(800);
    expect(lp2.writes).toHaveLength(1);
    expect(lp2.writes[0].method).toBe("PUT");
    expect(Object.keys(lp2.writes[0].body)).toEqual(["description"]);
  });

  test("LP-047: Stop offering asks for confirmation; Cancel sends nothing", async ({ page }) => {
    await page.goto(`/loan-products/${SEEDED_ID}`);
    await page.getByRole("button", { name: "Stop offering" }).click();
    const dlg = page.getByRole("alertdialog");
    await expect(dlg).toContainText("Confirm Stop Offering");
    await expect(dlg.getByRole("button", { name: "Deactivate" })).toBeVisible();
    await expect(dlg.getByRole("button", { name: "Delete permanently" })).toBeVisible();
    await dlg.getByRole("button", { name: "Cancel" }).click();
    await expect(dlg).toHaveCount(0);
    expect(lp.writes).toHaveLength(0);
  });

  test("LP-048: Escape closes the confirmation without acting", async ({ page }) => {
    await page.goto(`/loan-products/${SEEDED_ID}`);
    await page.getByRole("button", { name: "Stop offering" }).click();
    await expect(page.getByRole("alertdialog")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("alertdialog")).toHaveCount(0);
    expect(lp.writes).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------------------------
// Integration findings (2026-10-06): found by creating real products through the UI and following
// them across list, detail, edit, lender page and dashboard. Writes stay intercepted.
// ---------------------------------------------------------------------------------------------
test.describe("Loan products - integration findings (LP-INT)", () => {
  let lp: LoanProductsPage;
  test.beforeEach(async ({ page }) => {
    lp = new LoanProductsPage(page);
    await lp.interceptWrites();
  });

  const productByName = async (page: import("@playwright/test").Page, name: string) => {
    const res = await page.request.get(`/api/proxy?skip=0&limit=100&search=${encodeURIComponent(name)}`, { headers: { "x-target-endpoint": "/products" } });
    return (await res.json()).data.find((p: any) => p.name === name);
  };

  test("LP-060: term chips allow selecting more than one term on the Add form", async ({ page }) => {
    test.fail(true, "GUS-FX-0020: chips behave as single-select; selecting 12, 24, 36 leaves only 36 and adding a custom term replaces it");
    await lp.gotoNew();
    await lp.pick("Lender", "Westpac");
    await lp.pick("Type", "Personal Loan");
    await page.locator("#product-name").fill("Graduate Starter Loan");
    await lp.field("Interest rate (%)").fill("7.49");
    await lp.field("Minimum amount (AUD)").fill("2500");
    await lp.field("Maximum amount (AUD)").fill("45000");
    for (const t of ["12 mo", "24 mo", "36 mo"]) await page.getByRole("button", { name: t, exact: true }).click();
    await lp.submit();
    expect(lp.writes[0].body.termMonths).toEqual([12, 24, 36]);
  });

  test("LP-061: editing one term chip must not drop the other terms of a multi-term product", async ({ page }) => {
    test.fail(true, "GUS-FX-0020: one click on '24 mo' sends termMonths [24] for a product that has six terms (data loss)");
    const p = await productByName(page, "Fixed Rate Personal Loan");
    await page.goto(`/loan-products/${p._id}/edit`);
    await expect(page.locator("#product-name")).toHaveValue("Fixed Rate Personal Loan");
    await page.getByRole("button", { name: "24 mo", exact: true }).click();
    await page.getByRole("button", { name: "Save changes" }).click();
    await page.waitForTimeout(700);
    const sent = lp.writes[0]?.body?.termMonths as number[] | undefined;
    expect(sent === undefined || sent.length >= 5, `terms sent: ${JSON.stringify(sent)}`).toBe(true);
  });

  test("LP-062: the detail page shows the eligibility criteria that were saved", async ({ page }) => {
    test.fail(true, "GUS-FX-0021: age, income, debt-to-income and surplus are stored but never displayed (detail shows only the notes)");
    const p = await productByName(page, "Flexi First Home Loan");
    expect(p.criteria.minAgeYears).toBeGreaterThan(0);
    await page.goto(`/loan-products/${p._id}`);
    await expect(page.getByRole("heading", { name: "Flexi First Home Loan" })).toBeVisible();
    await expect(page.locator("main")).toContainText(/min(imum)? age|age/i);
    await expect(page.locator("main")).toContainText(/income/i);
  });

  test("LP-063: a duplicate product name for the same lender shows the server message inline", async ({ page }) => {
    await page.unroute("**/api/proxy");
    const lp2 = new LoanProductsPage(page);
    await lp2.interceptWrites(() => ({ status: 409, body: { success: false, message: "That lender already has a product with this name", code: "PRODUCT_NAME_EXISTS", details: [{ field: "name", message: "That lender already has a product with this name" }] } }));
    await lp2.gotoNew();
    await lp2.fillValid({ Name: "Graduate Starter Loan" });
    await lp2.submit();
    await expect(page.getByText("That lender already has a product with this name").first()).toBeVisible();
    await expect(page).toHaveURL(/loan-products\/new/);
  });
});


// ---------------------------------------------------------------------------------------------
// Terms and months (2026-10-06): chips, custom months input, display and edit prefill. Writes intercepted.
// ---------------------------------------------------------------------------------------------
test.describe("Loan products - terms and months (LP-TERM)", () => {
  let lp: LoanProductsPage;
  const chip = (page: import("@playwright/test").Page, name: string) => page.getByRole("button", { name, exact: true });
  const chipsOn = (page: import("@playwright/test").Page) =>
    page.locator("button").evaluateAll((bs) => bs.filter((b) => /^\d+ mo$/.test(b.textContent!.trim()) && /bg-primary/.test(b.className)).map((b) => b.textContent!.trim()));
  const findProduct = async (page: import("@playwright/test").Page, search: string, pred: (p: any) => boolean) => {
    const res = await page.request.get(`https://gusdev.softwareco.com/api/proxy?skip=0&limit=100&search=${encodeURIComponent(search)}`, { headers: { "x-target-endpoint": "/products" } });
    return (await res.json()).data.find(pred);
  };

  test.beforeEach(async ({ page }) => {
    lp = new LoanProductsPage(page);
    await lp.interceptWrites();
  });

  test("LP-070: preset chips offer 12, 24, 36, 48 and 60 months and none starts selected", async ({ page }) => {
    await lp.gotoNew();
    for (const t of ["12 mo", "24 mo", "36 mo", "48 mo", "60 mo"]) await expect(chip(page, t)).toBeVisible();
    expect(await chipsOn(page)).toEqual([]);
  });

  test("LP-071: clicking a selected chip again deselects it", async ({ page }) => {
    await lp.gotoNew();
    await chip(page, "12 mo").click();
    expect(await chipsOn(page)).toEqual(["12 mo"]);
    await chip(page, "12 mo").click();
    expect(await chipsOn(page)).toEqual([]);
  });

  for (const [v, shown] of [["1", "1 mo"], ["600", "600 mo"], ["7", "7 mo"], ["018", "18 mo"]] as const) {
    test(`LP-072: custom term "${v}" is accepted and shown as "${shown}"`, async ({ page }) => {
      await lp.gotoNew();
      await lp.field("Custom months").fill(v);
      await page.getByRole("button", { name: "Add", exact: true }).click();
      await expect(chip(page, shown)).toBeVisible();
      expect(await chipsOn(page)).toEqual([shown]);
    });
  }

  for (const [v, msg] of [
    ["0", /valid whole number/i], ["-5", /valid whole number/i], ["abc", /valid whole number/i], ["12.5", /valid whole number/i],
    ["1e2", /valid whole number/i], ["+24", /valid whole number/i], ["", /valid whole number/i],
    ["601", /600 months or less/i], ["5000", /600 months or less/i], ["99999999999", /600 months or less/i]
  ] as const) {
    test(`LP-073: custom term "${v}" is rejected with a clear message and no chip is added`, async ({ page }) => {
      await lp.gotoNew();
      await lp.field("Custom months").fill(v);
      await page.getByRole("button", { name: "Add", exact: true }).click();
      await expect(page.getByText(msg).first()).toBeVisible();
      expect(await chipsOn(page)).toEqual([]);
    });
  }

  test("LP-074: a custom term equal to a preset selects that preset instead of adding a duplicate", async ({ page }) => {
    await lp.gotoNew();
    await lp.field("Custom months").fill("12");
    await page.getByRole("button", { name: "Add", exact: true }).click();
    await expect(chip(page, "12 mo")).toHaveCount(1);
    expect(await chipsOn(page)).toEqual(["12 mo"]);
  });

  test("LP-075: the chosen term is sent as whole months in termMonths", async () => {
    await lp.interceptWrites(() => ({ status: 201, body: { success: true, message: "Product created", data: {} } }));
    await lp.gotoNew();
    await lp.fillValid();
    await lp.submit();
    expect(lp.writes[lp.writes.length - 1].body.termMonths).toEqual([36]);
  });

  test("LP-076: a multi-term product shows its terms ascending as 'N mo' on the detail page and the list", async ({ page }) => {
    const p = await findProduct(page, "Equipment Finance", (x) => x.termMonths.length >= 5);
    const expected = p.termMonths.slice().sort((a: number, b: number) => a - b).map((m: number) => `${m} mo`).join(", ");
    await page.goto(`/loan-products/${p._id}`);
    await expect(page.locator("main")).toContainText(expected);
    await lp.gotoList();
    await lp.search.fill(p.name);
    await expect(lp.rows.first().locator("td").nth(6)).toHaveText(expected);
  });

  test("LP-077: the Edit page shows non-preset terms as selected and a description-only edit does not send terms", async ({ page }) => {
    const p = await findProduct(page, "Basic Home Loan", (x) => x.termMonths.some((m: number) => ![12, 24, 36, 48, 60].includes(m)));
    await page.goto(`/loan-products/${p._id}/edit`);
    await expect(page.locator("#product-name")).toHaveValue(p.name);
    expect((await chipsOn(page)).sort()).toEqual(p.termMonths.map((m: number) => `${m} mo`).sort());
    await page.getByRole("textbox", { name: "Description", exact: true }).fill("Updated description text.");
    await page.getByRole("button", { name: "Save changes" }).click();
    await page.waitForTimeout(700);
    expect(Object.keys(lp.writes[0].body)).toEqual(["description"]);
  });

  test("LP-078: a long term list shows no layout overflow at phone width", async ({ page }) => {
    const p = await findProduct(page, "Equipment Finance", (x) => x.termMonths.length >= 5);
    await page.setViewportSize({ width: 375, height: 800 });
    await page.goto(`/loan-products/${p._id}`);
    await expect(page.locator("main")).toContainText("mo");
    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(0);
  });
});

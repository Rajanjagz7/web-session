import { Page, Locator, Route, expect } from "@playwright/test";

export type SentWrite = { method: string; target: string; body: any };

export const SEEDED_ID = "6abde76fe6b189801e58343a"; // existing product, only ever opened read-only

export class LoanProductsPage {
  readonly page: Page;
  readonly writes: SentWrite[] = [];
  readonly heading: Locator;
  readonly addButton: Locator;
  readonly rows: Locator;
  readonly search: Locator;
  readonly createButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { name: "Loan products", level: 1 });
    this.addButton = page.getByRole("button", { name: "Add product" });
    this.rows = page.locator("tbody tr");
    this.search = page.getByRole("textbox", { name: "Search loan products" });
    this.createButton = page.getByRole("button", { name: "Create product" });
  }

  /**
   * Every non-GET call is recorded and answered locally, so UI tests can never create, change or delete
   * data and never consume the 100-writes-per-hour server limit. Pass `respond` to simulate a server reply.
   */
  async interceptWrites(respond?: (w: SentWrite) => { status: number; body: any; delayMs?: number }) {
    await this.page.route("**/api/proxy", async (route: Route) => {
      const req = route.request();
      if (req.method() === "GET") return route.continue();
      const w: SentWrite = {
        method: req.method(),
        target: req.headers()["x-target-endpoint"],
        body: req.postData() ? JSON.parse(req.postData()!) : null
      };
      this.writes.push(w);
      if (!respond) return route.abort();
      const r = respond(w);
      if (r.delayMs) await new Promise((res) => setTimeout(res, r.delayMs));
      return route.fulfill({ status: r.status, contentType: "application/json", body: JSON.stringify(r.body) });
    });
  }

  /** Replaces the products list response (GET /products) with fabricated rows. */
  async mockList(products: any[], status = 200, body?: any) {
    await this.page.route("**/api/proxy*", async (route) => {
      const req = route.request();
      if (req.method() === "GET" && req.headers()["x-target-endpoint"] === "/products") {
        return route.fulfill({
          status,
          contentType: "application/json",
          body: JSON.stringify(
            body ?? { success: true, message: "Products", isNext: false, data: products, totalCount: products.length }
          )
        });
      }
      return route.fallback();
    });
  }

  async gotoList() {
    await this.page.goto("/loan-products");
    await expect(this.heading).toBeVisible();
  }

  async gotoNew() {
    await this.page.goto("/loan-products/new");
    await expect(this.page.getByRole("heading", { name: "Add loan product" })).toBeVisible();
  }

  async pick(combo: string, option: string) {
    await this.page.getByRole("combobox", { name: combo, exact: true }).click();
    await this.page.getByRole("option", { name: option, exact: true }).click();
  }

  field(label: string) {
    return this.page.getByRole("textbox", { name: label, exact: true });
  }

  /** Fills every required field with valid, realistic data. Override any field by label. */
  async fillValid(over: Record<string, string> = {}) {
    await this.pick("Lender", "Preventive Health Review");
    await this.pick("Type", "Personal Loan");
    const v: Record<string, string> = {
      Name: "Everyday Personal Loan",
      "Interest rate (%)": "7.49",
      "Comparison rate (%)": "8.12",
      "Minimum amount (AUD)": "5000.00",
      "Maximum amount (AUD)": "50000.00",
      ...over
    };
    await this.page.locator("#product-name").fill(v["Name"]);
    for (const [label, value] of Object.entries(v)) {
      if (label !== "Name") await this.field(label).fill(value);
    }
    await this.page.getByRole("button", { name: "36 mo" }).click();
  }

  async submit() {
    await this.createButton.click();
    await this.page.waitForTimeout(600);
  }

  fieldErrors() {
    return this.page.locator('[data-slot="field-error"], p.text-destructive, [id$="-error"]');
  }

  static product(over: Record<string, any> = {}) {
    return {
      _id: "6abde76fe6b189801e58aaaa",
      lenderId: "6ab119e3983eb386149dce1b",
      lender: { _id: "6ab119e3983eb386149dce1b", name: "Preventive Health Review", isActive: true },
      name: "Everyday Personal Loan",
      type: "personal_loan",
      description: "Fixed-rate unsecured personal loan.",
      interestRateBps: 749,
      comparisonRateBps: 812,
      termMonths: [36],
      minAmountCents: 500000,
      maxAmountCents: 5000000,
      criteria: { requiresBankConnection: true },
      isActive: true,
      createdAt: "2026-10-05T09:06:46.473Z",
      updatedAt: "2026-10-05T09:06:46.473Z",
      ...over
    };
  }
}

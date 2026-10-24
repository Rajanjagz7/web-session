import { Page, Locator, Route, expect } from "@playwright/test";

export interface EnquiryItem {
  id: string;
  reference: string;
  customer: {
    name: string;
    email: string;
  };
  lender: {
    id: string;
    name: string;
  };
  product: {
    id: string;
    name: string;
    type: string;
  };
  requested: {
    amountCents: number;
    termMonths: number;
  };
  status: string;
  leadSent: boolean;
  submittedAt: string;
}

export class EnquiriesPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly table: Locator;
  readonly rows: Locator;
  readonly columnHeaders: Locator;
  readonly searchInput: Locator;
  readonly lenderFilter: Locator;
  readonly typeFilter: Locator;
  readonly statusFilter: Locator;
  readonly leadSentFilter: Locator;
  readonly clearButton: Locator;
  readonly emptyState: Locator;
  readonly errorBanner: Locator;
  readonly paginationSummary: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole("heading", { name: "Enquiries", level: 1 });
    this.table = page.locator("table");
    this.rows = page.locator("tbody tr");
    this.columnHeaders = page.locator("thead th");
    this.searchInput = page.getByPlaceholder(/search enquiries/i)
      .or(page.getByRole("textbox", { name: /search enquiries/i }));
    this.lenderFilter = page.getByRole("combobox", { name: "Lender" });
    this.typeFilter = page.getByRole("combobox", { name: "Product type" });
    this.statusFilter = page.getByRole("combobox", { name: "Status" });
    this.leadSentFilter = page.getByRole("combobox", { name: "Lead sent" });
    this.clearButton = page.getByRole("button", { name: "Clear", exact: true });
    this.emptyState = page.getByText(/no matching enquiries|no enquiries found/i);
    this.errorBanner = page.getByText(/unable to load enquiries/i);
    this.paginationSummary = page.getByText(/^Showing \d+/);
  }

  async gotoList() {
    await this.page.goto("/enquiries");
    await expect(this.heading).toBeVisible();
    await expect(this.rows.first()).toBeVisible();
  }

  async gotoDetail(id: string) {
    await this.page.goto(`/enquiries/${id}`);
    await expect(this.page.locator("h1")).toBeVisible();
  }

  /** Intercepts enquiries list GET requests to provide mock data */
  async mockList(enquiries: any[], status = 200, extra?: any) {
    await this.page.route("**/api/proxy*", async (route) => {
      const req = route.request();
      if (req.method() === "GET" && req.headers()["x-target-endpoint"]?.startsWith("/enquiries")) {
        return route.fulfill({
          status,
          contentType: "application/json",
          body: JSON.stringify(
            extra ?? {
              success: true,
              message: "Enquiries retrieved",
              isNext: false,
              data: enquiries,
              totalCount: enquiries.length
            }
          )
        });
      }
      return route.fallback();
    });
  }

  async search(query: string) {
    await this.searchInput.fill(query);
    await this.page.keyboard.press("Enter");
  }

  async getReferences(): Promise<string[]> {
    return this.rows.locator("td:nth-child(1)").allInnerTexts();
  }

  async getStatuses(): Promise<string[]> {
    return this.rows.locator("td:nth-child(7)").allInnerTexts();
  }
}

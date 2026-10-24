import { test, expect } from "@playwright/test";
import { EnquiriesPage } from "../pages/EnquiriesPage";

const SEEDED_ENQUIRY_ID = "6adb0713038907f7bf9f280f"; // ENQ-2026-WTBM8W

test.describe("Enquiries Portal UI Tests", () => {
  let ep: EnquiriesPage;

  test.beforeEach(async ({ page }) => {
    ep = new EnquiriesPage(page);
  });

  test("ENQ-UI-001: Enquiries list renders heading, table headers, and seeded enquiries", async ({ page }) => {
    await ep.gotoList();
    await expect(ep.heading).toBeVisible();

    // Verify exact columns matching live schema
    const expectedHeaders = [
      "Reference",
      "Customer",
      "Product",
      "Type",
      "Requested",
      "Eligibility",
      "Status",
      "Lead",
      "Submitted",
      "Actions"
    ];
    for (const header of expectedHeaders) {
      await expect(ep.columnHeaders.filter({ hasText: header }).first()).toBeVisible();
    }

    // Verify seeded rows are present
    await expect(ep.rows.first()).toBeVisible();
  });

  test("ENQ-UI-002: Search filters enquiries table by customer or reference number", async ({ page }) => {
    await ep.gotoList();
    await ep.search("Rajan");
    await expect(ep.rows.first()).toBeVisible();
    const rowsText = await ep.rows.allInnerTexts();
    for (const r of rowsText) {
      expect(r.toLowerCase()).toContain("rajan");
    }
  });

  test("ENQ-UI-003: Non-matching search displays empty state gracefully without crash", async ({ page }) => {
    await ep.gotoList();
    await ep.search("nonexistent_enquiry_query_xyz999");
    await expect(ep.rows).toHaveCount(0);
    await expect(page.getByText(/no matching enquiries|no enquiries found/i).first()).toBeVisible();
  });

  test("ENQ-UI-004: Clear button resets search and restores enquiries list", async ({ page }) => {
    await ep.gotoList();
    await ep.search("nonexistent_enquiry_query_xyz999");
    await expect(ep.rows).toHaveCount(0);

    // Click Clear
    const clearBtn = page.getByRole("button", { name: "Clear", exact: true });
    await expect(clearBtn).toBeEnabled();
    await clearBtn.click();
    await expect(ep.rows.first()).toBeVisible();
  });

  test("ENQ-UI-005: Enquiry detail page loads core cards (Request, Eligibility, Customer, Financial, Estimate)", async ({ page }) => {
    await page.goto(`/enquiries/${SEEDED_ENQUIRY_ID}`);
    await expect(page.getByRole("heading", { name: "ENQ-2026-WTBM8W" })).toBeVisible();

    // Verify core section cards
    await expect(page.getByRole("heading", { name: "Request", level: 2 })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Eligibility", level: 2 })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Customer", level: 2 })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Financial position", level: 2 })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Estimate", level: 2 })).toBeVisible();
  });

  test("ENQ-UI-006: [Defect GUS-ENQ-001 Verification] API 404 displays error banner gracefully", async ({ page }) => {
    // Simulates Staging environment failure where GET /api/v1/enquiries returns 404
    await ep.mockList([], 404, { success: false, message: "Route not found: GET /api/v1/enquiries" });
    await page.goto("/enquiries");
    await expect(page.getByText(/unable to load enquiries|error/i).first()).toBeVisible();
  });
});

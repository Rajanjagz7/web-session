import { test, expect } from "@playwright/test";
import { CmsPage } from "../pages/CmsPage";

test.describe("CMS Portal UI Tests", () => {
  let cp: CmsPage;

  test.beforeEach(async ({ page }) => {
    cp = new CmsPage(page);
  });

  test("CMS-UI-001: CMS list renders heading, table headers, and seeded content", async ({ page }) => {
    await cp.gotoList();
    await expect(cp.heading).toBeVisible();

    const expectedHeaders = ["Title / Question", "Type", "Status", "Created At", "Updated At", "Actions"];
    for (const h of expectedHeaders) {
      await expect(page.locator("thead th").filter({ hasText: h }).first()).toBeVisible();
    }

    await expect(cp.rows.first()).toBeVisible();
  });

  test("CMS-UI-002: Add CMS button opens modal dialog with form controls", async ({ page }) => {
    await cp.gotoList();
    await expect(cp.addButton).toBeVisible();
    await cp.addButton.click();

    // Verify modal dialog appears
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole("heading", { name: "Add CMS" })).toBeVisible();
    await expect(dialog.getByText(/CMS type/i).first()).toBeVisible();

    // Verify Cancel closes the dialog
    await dialog.getByRole("button", { name: "Cancel" }).click();
    await expect(dialog).not.toBeVisible();
  });

  test("CMS-UI-003: CMS direct /cms/new route renders form and controls", async ({ page }) => {
    await page.goto("/cms/new");
    await expect(page.getByText(/CMS type/i).first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Cancel" })).toBeVisible();
    await expect(page.getByRole("button", { name: /add cms/i })).toBeVisible();
  });

  test("CMS-UI-004: Cancel button on /cms/new returns user to /cms list", async ({ page }) => {
    await page.goto("/cms/new");
    await page.getByRole("button", { name: "Cancel" }).click();
    await page.waitForURL("**/cms");
    expect(page.url()).toContain("/cms");
  });

  test("CMS-UI-005: [Defect GUS-CMS-001] Type dropdown offers Terms & Conditions option", async ({ page }) => {
    await page.goto("/cms/new");
    // Verify that the Terms & Conditions option is present in the select dropdown
    const termsOption = page.locator('option[value="terms-and-conditions"]')
      .or(page.getByRole("option", { name: /terms & conditions/i }));
    await expect(termsOption.first()).toBeAttached();
  });
});

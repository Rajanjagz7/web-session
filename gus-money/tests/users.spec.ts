import { test, expect } from "@playwright/test";
import { UsersPage } from "../pages/UsersPage";

// Read-only suite: never creates/edits/deletes users on the shared dev environment.
test.describe("Users list (USR)", () => {
  let users: UsersPage;

  test.beforeEach(async ({ page }) => {
    users = new UsersPage(page);
    await users.goto();
  });

  test("USR-001: page renders heading, filters and table columns @smoke", async () => {
    await expect(users.heading).toBeVisible();
    await expect(users.statusFilter).toBeVisible();
    await expect(users.searchInput).toBeVisible();
    for (const col of ["Name", "Email", "Phone", "Status", "Last active", "Created", "Actions"]) {
      await expect(users.columnHeaders.filter({ hasText: col }).first()).toBeVisible();
    }
  });

  test("USR-002: list is populated and summary matches row count", async () => {
    const count = await users.rows.count();
    expect(count).toBeGreaterThan(0);
    await expect(users.summary).toContainText(`of ${count}`);
  });

  test("USR-003: every row has name link, email and actions button", async () => {
    const n = await users.rows.count();
    for (let i = 0; i < n; i++) {
      const row = users.rows.nth(i);
      await expect(row.locator('a[href^="/users/"]')).toHaveCount(1);
      await expect(row.locator("td:nth-child(2)")).toContainText("@");
      await expect(row.getByRole("button", { name: "Open actions" })).toBeVisible();
    }
  });

  test("USR-004: search by email prefix filters the list", async () => {
    const first = (await users.emails())[0];
    const prefix = first.slice(0, 5).toLowerCase();
    await users.search(prefix);
    await expect
      .poll(async () => (await users.emails()).every((e) => e.toLowerCase().startsWith(prefix)))
      .toBe(true);
    await expect(users.clearButton).toBeEnabled();
  });

  test("USR-005: search with no match shows no user rows (negative)", async ({ page }) => {
    await users.search("zzzz_no_such_user_" + Date.now());
    await expect(page.locator('tbody a[href^="/users/"]')).toHaveCount(0);
  });

  test("USR-006: search is not vulnerable to markup injection (security)", async ({ page }) => {
    let dialogSeen = false;
    page.on("dialog", async (d) => {
      dialogSeen = true;
      await d.dismiss();
    });
    await users.search("<img src=x onerror=alert(1)>");
    await page.waitForTimeout(1000);
    expect(dialogSeen).toBe(false);
    await expect(page).toHaveURL(/\/users/);
  });

  test("USR-007: Clear resets the search", async ({ page }) => {
    const before = await users.rows.count();
    await users.search("zzzz_no_such_user");
    await users.clearButton.click();
    await expect(users.searchInput).toHaveValue("");
    await expect(page.locator('tbody a[href^="/users/"]')).toHaveCount(before);
  });

  test("USR-008: search boundary - whitespace only and 300 chars do not crash", async ({ page }) => {
    await users.search("   ");
    await expect(users.heading).toBeVisible();
    await users.searchInput.fill("a".repeat(300));
    await page.keyboard.press("Enter");
    await expect(users.heading).toBeVisible();
  });

  test("USR-009: status filter offers options", async ({ page }) => {
    await users.statusFilter.click();
    expect(await page.getByRole("option").count()).toBeGreaterThan(1);
  });

  test("USR-010: sorting by Created calls the list API with sortBy=createdAt", async () => {
    const resp = await users.waitForList(() =>
      users.columnHeaders.getByRole("button", { name: "Created" }).click()
    );
    expect(resp.status()).toBe(200);
    expect(resp.url()).toContain("sortBy=createdAt");
  });

  test("USR-011: clicking a user name opens the detail page", async ({ page }) => {
    await users.rows.first().locator('a[href^="/users/"]').click();
    await expect(page).toHaveURL(/\/users\/[0-9a-f]{24}/);
  });

  test("USR-012: row actions menu opens (no action executed)", async ({ page }) => {
    await users.rows.first().getByRole("button", { name: "Open actions" }).click();
    await expect(page.getByRole("menu")).toBeVisible();
  });

  test("USR-013: pagination controls reflect a single page", async ({ page }) => {
    await expect(page.getByText(/Page 1 \/ /)).toBeVisible();
    await expect(page.getByRole("button", { name: "Previous page" })).toBeDisabled();
    await expect(page.getByRole("button", { name: "First page" })).toBeDisabled();
  });

  test("USR-014: sidebar navigation links are present", async ({ page }) => {
    for (const name of ["Dashboard", "Users", "Lenders", "Loan Products", "CMS"]) {
      await expect(page.getByRole("link", { name, exact: true })).toBeVisible();
    }
  });
});

test.describe("Users - access control (USR-SEC)", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("USR-015: unauthenticated visit redirects to sign-in with callbackUrl", async ({ page }) => {
    await page.goto("/users");
    await expect(page).toHaveURL(/sign-in\?callbackUrl=%2Fusers/);
  });
});

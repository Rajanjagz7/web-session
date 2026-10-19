import { test, expect } from "@playwright/test";
import { LoginPage } from "../pages/LoginPage";
import { UsersPage } from "../pages/UsersPage";

// Negative / edge UI tests for sign-in and the Users page.
// Failed-login tests are intentionally few (3) to avoid locking the shared admin account.

test.describe("Sign-in negative (AUTH-NEG)", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  let login: LoginPage;
  test.beforeEach(async ({ page }) => {
    login = new LoginPage(page);
    await login.goto();
  });

  test("NEG-001: empty submit stays on sign-in and shows required errors", async ({ page }) => {
    await page.getByRole("button", { name: "Sign In" }).click();
    await expect(page).toHaveURL(/sign-in/);
    await expect(page.getByText(/required|enter a valid|invalid/i).first()).toBeVisible();
  });

  test("NEG-002: invalid email format is rejected", async ({ page }) => {
    await page.getByRole("textbox", { name: "Email address" }).fill("not-an-email");
    await page.getByRole("textbox", { name: "Password" }).fill("Admin@123");
    await page.getByRole("button", { name: "Sign In" }).click();
    await expect(page).toHaveURL(/sign-in/);
    await expect(page.getByText(/valid email/i).first()).toBeVisible();
  });

  const failedLoginToast = async (page, email: string) => {
    await page.getByRole("textbox", { name: "Email address" }).fill(email);
    await page.getByRole("textbox", { name: "Password" }).fill("Wrong@123");
    await page.getByRole("button", { name: "Sign In" }).click();
    const toast = page.locator("[data-sonner-toast]").first();
    await expect(toast).toBeVisible();
    return (await toast.innerText()).trim();
  };

  test("NEG-003: wrong password shows an error and creates no session", async ({ page }) => {
    await failedLoginToast(page, process.env.ADMIN_EMAIL!);
    await expect(page).toHaveURL(/sign-in/);
    await page.goto("/users");
    await expect(page).toHaveURL(/sign-in/);
  });

  test("NEG-004: unknown user gets the same message as a wrong password (no enumeration)", async ({ page }) => {
    // GUS-FX-0014 (UI part) fixed 2026-10-06: both cases show the same generic message.
    const real = await failedLoginToast(page, process.env.ADMIN_EMAIL!);
    await login.goto();
    const unknown = await failedLoginToast(page, `nobody_${Date.now()}@yopmail.com`);
    expect(unknown).toBe(real);
  });

  test("NEG-005: password is masked and toggle works", async ({ page }) => {
    const pw = page.getByRole("textbox", { name: "Password" });
    await pw.fill("Secret@123");
    await expect(pw).toHaveAttribute("type", "password");
    await page.getByRole("button", { name: "Show password" }).click();
    await expect(pw).toHaveAttribute("type", "text");
  });

  test("NEG-006: callbackUrl to an external site is not followed", async ({ page }) => {
    await page.goto("/sign-in?callbackUrl=https%3A%2F%2Fevil.example.com");
    await page.getByRole("textbox", { name: "Email address" }).fill(process.env.ADMIN_EMAIL!);
    await page.getByRole("textbox", { name: "Password" }).fill(process.env.ADMIN_PASSWORD!);
    await page.getByRole("button", { name: "Sign In" }).click();
    await page.waitForURL((u) => !u.pathname.includes("sign-in"), { timeout: 15000 });
    expect(new URL(page.url()).hostname).not.toContain("evil.example.com");
  });
});

test.describe("Users negative (USR-NEG)", () => {
  let users: UsersPage;
  test.beforeEach(async ({ page }) => {
    users = new UsersPage(page);
    await users.goto();
  });

  test("NEG-010: search with special characters does not break the page", async ({ page }) => {
    for (const term of ["%", "\\", "' OR '1'='1", '{"$ne":1}', "😀", "  leading", "trailing  "]) {
      await users.search(term);
      await expect(users.heading).toBeVisible();
      await expect(page.getByText(/something went wrong|internal server error|unhandled/i)).toHaveCount(0);
    }
  });

  test("NEG-011: search is case-insensitive", async () => {
    const email = (await users.emails())[0];
    const prefix = email.slice(0, 5);
    await users.search(prefix.toUpperCase());
    await expect.poll(async () => (await users.emails()).includes(email)).toBe(true);
  });

  test("NEG-012: search term is not reflected as HTML", async ({ page }) => {
    await users.search("<b id=injected>x</b>");
    await page.waitForTimeout(800);
    await expect(page.locator("#injected")).toHaveCount(0);
  });

  test("NEG-013: no-result search then Clear restores the full list", async ({ page }) => {
    const before = await page.locator('tbody a[href^="/users/"]').count();
    await users.search("zzzz_no_match");
    await expect(page.locator('tbody a[href^="/users/"]')).toHaveCount(0);
    await users.clearButton.click();
    await expect(page.locator('tbody a[href^="/users/"]')).toHaveCount(before);
  });

  test("NEG-014: user detail with malformed id does not crash", async ({ page }) => {
    const resp = await page.goto("/users/zzz");
    expect(resp?.status() ?? 200).toBeLessThan(500);
    await expect(page.getByText(/internal server error|unhandled|stack/i)).toHaveCount(0);
  });

  test("NEG-015: user detail with well-formed but non-existent id does not crash", async ({ page }) => {
    const resp = await page.goto("/users/000000000000000000000000");
    expect(resp?.status() ?? 200).toBeLessThan(500);
    await expect(page.getByText(/internal server error|unhandled|stack/i)).toHaveCount(0);
  });

  test("NEG-016: unknown route under /users shows not-found, not a crash", async ({ page }) => {
    const resp = await page.goto("/users/zzz/does/not/exist");
    expect(resp?.status() ?? 404).toBeLessThan(500);
  });

  test("NEG-017: rapid repeated sort clicks leave the page stable", async ({ page }) => {
    const created = users.columnHeaders.getByRole("button", { name: "Created" });
    for (let i = 0; i < 5; i++) await created.click();
    await expect(users.heading).toBeVisible();
    await expect(users.rows.first()).toBeVisible();
  });

  test("NEG-018: actions menu closes with Escape and changes nothing", async ({ page }) => {
    const before = await users.emails();
    await users.rows.first().getByRole("button", { name: "Open actions" }).click();
    await expect(page.getByRole("menu")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("menu")).toHaveCount(0);
    expect(await users.emails()).toEqual(before);
  });

  test("NEG-019: logging out clears access to /users", async ({ page, context }) => {
    await context.clearCookies();
    await page.goto("/users");
    await expect(page).toHaveURL(/sign-in/);
  });
});

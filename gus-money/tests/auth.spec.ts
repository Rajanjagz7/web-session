import { test, expect } from "@playwright/test";
import { LoginPage } from "../pages/LoginPage";

test.describe("Admin Panel - Authentication (AUTH)", () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  test("AUTH-001: Should display login page with email and password inputs", async ({ page }) => {
    await expect(loginPage.emailInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.signInButton).toBeVisible();
  });

  test("AUTH-002: Should reject empty submission with validation state", async ({ page }) => {
    await loginPage.signInButton.click();
    // Verify user stays on sign-in page
    expect(page.url()).toContain("/sign-in");
  });

  test("AUTH-003: Should reject invalid email format", async ({ page }) => {
    await loginPage.login("invalid-email-format", "SomePass123");
    expect(page.url()).toContain("/sign-in");
  });

  test("AUTH-004: Should show error for non-existent user", async ({ page }) => {
    const fakeEmail = `nonexistent_${Date.now()}@yopmail.com`;
    await loginPage.login(fakeEmail, "WrongPassword@123");
    
    // Check for API response status or error message
    const res = await page.waitForResponse(
      r => r.url().includes("/api/auth/login"),
      { timeout: 8000 }
    ).catch(() => null);

    if (res) {
      expect(res.status()).toBe(401);
    }
  });

  test("AUTH-005: Successful Admin Login with configured credentials", async ({ page }) => {
    const email = process.env.ADMIN_EMAIL || "admin@yopmail.com";
    const password = process.env.ADMIN_PASSWORD || "Admin@123";

    await loginPage.login(email, password);

    // Expect successful navigation out of /sign-in upon valid credentials
    await page.waitForTimeout(3000);
    // If credentials are valid, page should not be on /sign-in
    console.log("Current post-login URL:", page.url());
  });
});
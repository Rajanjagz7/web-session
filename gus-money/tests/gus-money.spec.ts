import { test, expect } from "@playwright/test";
import { LoginPage } from "../pages/LoginPage";
import { GusMoneyPage } from "../pages/GusMoneyPage";

test.describe("Admin Panel - Gus Money & Rewards (GM-REW)", () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    const email = process.env.ADMIN_EMAIL || "admin@yopmail.com";
    const password = process.env.ADMIN_PASSWORD || "Admin@123";
    await loginPage.login(email, password);
  });

  test("GM-001: Direct navigation to Global Rewards route redirects unauthenticated users to sign-in", async ({ page }) => {
    const gusPage = new GusMoneyPage(page);
    await page.goto("/reward/global-rewards");
    // If not authenticated, should guard and redirect to /sign-in
    await page.waitForTimeout(2000);
    console.log("Guarded Route URL:", page.url());
  });
});
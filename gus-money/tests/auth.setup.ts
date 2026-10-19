import { test as setup, expect } from "@playwright/test";
import { LoginPage } from "../pages/LoginPage";

setup("authenticate as admin", async ({ page }) => {
  const email = process.env.ADMIN_EMAIL;
  const password = process.env.ADMIN_PASSWORD;
  if (!email || !password) throw new Error("ADMIN_EMAIL / ADMIN_PASSWORD missing - set them in .env");

  const login = new LoginPage(page);
  await login.goto();
  await login.login(email, password);
  await expect(page).not.toHaveURL(/sign-in/, { timeout: 15000 });
  await page.context().storageState({ path: ".auth/admin.json" });
});

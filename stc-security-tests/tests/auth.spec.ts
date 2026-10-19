import { test, expect } from '@playwright/test';
import { loginSTC } from './helpers/auth.helper';

test.describe('STC Security - Authentication Test Suite', () => {

  test('AUTH-01: Successful Login with Super Admin credentials & OTP bypass', async ({ page }) => {
    await loginSTC(page);

    // Verify redirected away from login and onto authenticated area
    await expect(page).not.toHaveURL(/\/login/i);
    
    // Validate dashboard UI elements
    const dashboardHeader = page.locator('text=/Dashboard|Postcode Coverage|Overview/i').first();
    await expect(dashboardHeader).toBeVisible({ timeout: 15000 });

    // Verify authenticated user badge/profile
    const userProfile = page.locator('text=/Admin|stc\.admin/i').first();
    await expect(userProfile).toBeVisible();
  });

  test('AUTH-02: Negative Test - Login rejection on invalid password', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.locator('input[type="email"], input[name="email"], input[name="username"]').first();
    await emailInput.fill('stc.admin@yopmail.com');

    const passwordInput = page.locator('input[type="password"]').first();
    await passwordInput.fill('WrongPassword!999');

    const submitBtn = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")').first();
    await submitBtn.click();

    // Verify error toast/message appears
    const errorAlert = page.locator('.error, [role="alert"], text=/Invalid credentials|Incorrect password|Authentication failed/i').first();
    await expect(errorAlert).toBeVisible({ timeout: 8000 });
  });

  test('AUTH-03: Session Management - Logout and Route Guard check', async ({ page }) => {
    await loginSTC(page);

    // Click logout
    const logoutBtn = page.locator('button:has-text("Logout"), button:has-text("Sign Out"), [aria-label="Logout"]').first();
    if (await logoutBtn.isVisible().catch(() => false)) {
      await logoutBtn.click();
    } else {
      // Check user dropdown first
      const profileDropdown = page.locator('[aria-haspopup="menu"], .avatar, .profile-menu').first();
      if (await profileDropdown.isVisible().catch(() => false)) {
        await profileDropdown.click();
        await page.locator('text=/Logout|Sign Out/i').first().click();
      }
    }

    // Assert redirected back to login
    await expect(page).toHaveURL(/\/login/i, { timeout: 10000 });

    // Direct access to protected page should redirect back to login
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/i, { timeout: 10000 });
  });

});

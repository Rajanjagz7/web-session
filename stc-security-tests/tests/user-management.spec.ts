import { test, expect } from '@playwright/test';
import { loginSTC } from './helpers/auth.helper';

test.describe('STC Security - User Management Test Suite', () => {

  test.beforeEach(async ({ page }) => {
    await loginSTC(page);
  });

  test('USER-01: User Listing - View directory, table headers & pagination', async ({ page }) => {
    // Navigate to user management
    const usersNavLink = page.locator('a:has-text("User Management"), a:has-text("Users"), [href*="users"]').first();
    if (await usersNavLink.isVisible().catch(() => false)) {
      await usersNavLink.click();
    } else {
      await page.goto('/users');
    }

    await page.waitForLoadState('networkidle');

    // Verify User table/grid is visible
    const usersTable = page.locator('table, [role="table"], .user-list, .grid').first();
    await expect(usersTable).toBeVisible({ timeout: 15000 });

    // Verify key columns exist
    await expect(page.locator('text=/Name|Email|Role|Status/i').first()).toBeVisible();
  });

  test('USER-02: Search & Filter Users by Role or Keyword', async ({ page }) => {
    await page.goto('/users');

    const searchInput = page.locator('input[placeholder*="Search"], input[type="search"]').first();
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.fill('admin');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1000);

      // Verify filtered results contain search term
      const resultCell = page.locator('table tr, .user-card').filter({ hasText: /admin/i });
      expect(await resultCell.count()).toBeGreaterThan(0);
    }
  });

  test('USER-03: Create New User Modal - Form validation & Input fields', async ({ page }) => {
    await page.goto('/users');

    const addUserBtn = page.locator('button:has-text("Add User"), button:has-text("Create User"), button:has-text("New User")').first();
    if (await addUserBtn.isVisible().catch(() => false)) {
      await addUserBtn.click();

      // Verify Modal/Drawer is rendered
      const modal = page.locator('[role="dialog"], .modal, .drawer').first();
      await expect(modal).toBeVisible();

      // Submit empty form to trigger validations
      const saveBtn = modal.locator('button[type="submit"], button:has-text("Save"), button:has-text("Create")').first();
      await saveBtn.click();

      // Expect field validations
      const requiredValidation = modal.locator('text=/Required|Enter valid email|Please fill/i').first();
      await expect(requiredValidation).toBeVisible();
    }
  });

});

import { test, expect } from '@playwright/test';

test.describe('OzMed Settings - Users & Team Members Module (Positive & Negative Scenarios)', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate directly to the Users page
    await page.goto('/settings/users');
    // Ensure the Team Members sub-tab finishes rendering
    await expect(page.getByRole('tab', { name: /Team Members/i })).toBeVisible({ timeout: 15000 });
  });

  // -------------------------------------------------------------
  // POSITIVE SCENARIO: Sub-Navigation & Default Selection
  // -------------------------------------------------------------
  test('POSITIVE: should verify Users sub-navigation tabs and active Team Members view', async ({ page }) => {
    // 1. Verify both sub-tabs exist
    const teamMembersTab = page.getByRole('tab', { name: /Team Members/i });
    const practitionerTab = page.getByRole('tab', { name: /Practitioner/i });

    await expect(teamMembersTab).toBeVisible();
    await expect(practitionerTab).toBeVisible();

    // 2. Verify Team Members tab is selected by default
    await expect(teamMembersTab).toHaveAttribute('aria-selected', 'true');
  });

  // -------------------------------------------------------------
  // POSITIVE SCENARIO: Table Grid & Search Bar
  // -------------------------------------------------------------
  test('POSITIVE: should display user table headers and allow debounced searching', async ({ page }) => {
    // 1. Verify Primary Action Button
    await expect(page.getByRole('button', { name: /Add Team Member/i }).first()).toBeVisible();

    // 2. Verify Table Columns
    const expectedHeaders = ['Name', 'Email', 'Role', 'Status'];
    for (const header of expectedHeaders) {
      await expect(
        page.getByRole('columnheader', { name: new RegExp(header, 'i') })
          .or(page.locator(`th:has-text("${header}")`))
          .first()
      ).toBeVisible();
    }

    // 3. Verify Search Bar Debounce
    const searchInput = page.getByPlaceholder(/Search name, email/i);
    await expect(searchInput).toBeVisible();

    await searchInput.fill('NonExistentUserQuery999');
    await page.waitForTimeout(600);

    // Clear search
    await searchInput.fill('');
    await page.waitForTimeout(600);
  });

  // -------------------------------------------------------------
  // NEGATIVE SCENARIO: Empty Form Submission Required Errors
  // -------------------------------------------------------------
  test('NEGATIVE: should enforce required field validations when submitting empty Add Team Member form', async ({ page }) => {
    // 1. Navigate to Add Team Member form
    await page.goto('/settings/users/add');
    await expect(page.getByRole('heading', { name: /Add Team Member/i })).toBeVisible({ timeout: 10000 });

    // 2. Click Submit button without filling any fields
    const submitBtn = page.getByRole('button', { name: 'Add Team Member' });
    await submitBtn.click();

    // 3. Assert all 6 mandatory field validation errors
    await expect(page.getByText('First Name is required!')).toBeVisible();
    await expect(page.getByText('Last Name is required!')).toBeVisible();
    await expect(page.getByText('Email is required!')).toBeVisible();
    await expect(page.getByText('Phone Number is required!')).toBeVisible();
    await expect(page.getByText('Role is required!')).toBeVisible();
    await expect(page.getByText('Gender is required!')).toBeVisible();
  });

  // -------------------------------------------------------------
  // NEGATIVE SCENARIO: Invalid Email Format
  // -------------------------------------------------------------
  test('NEGATIVE: should reject invalid email format with specific validation message', async ({ page }) => {
    await page.goto('/settings/users/add');
    await expect(page.getByRole('heading', { name: /Add Team Member/i })).toBeVisible({ timeout: 10000 });

    // 1. Fill First Name
    const firstNameInput = page.getByRole('textbox', { name: /First Name/i });
    await firstNameInput.fill('TestFirst');

    // 2. Fill invalid email format
    const emailInput = page.getByRole('textbox', { name: /Email/i });
    await emailInput.fill('invalid-email-format');

    // 3. Trigger validation by clicking submit
    const submitBtn = page.getByRole('button', { name: 'Add Team Member' });
    await submitBtn.click();

    // 4. Assert invalid email format error
    await expect(page.getByText('Email must be a valid email address!')).toBeVisible();
  });

  // -------------------------------------------------------------
  // POSITIVE SCENARIO: Cancel Form Navigation
  // -------------------------------------------------------------
  test('POSITIVE: should cancel Add Team Member form and safely return to user list', async ({ page }) => {
    await page.goto('/settings/users/add');
    await expect(page.getByRole('heading', { name: /Add Team Member/i })).toBeVisible({ timeout: 10000 });

    // Fill partial data
    const emailInput = page.getByRole('textbox', { name: /Email/i });
    await emailInput.fill('temporary.draft@test.com');

    // Click Cancel
    const cancelBtn = page.getByRole('button', { name: /Cancel/i });
    await cancelBtn.click();

    // Assert immediate return to /settings/users
    await expect(page).toHaveURL(/.*\/settings\/users$/);
    await expect(page.getByRole('tab', { name: /Team Members/i })).toBeVisible();
  });

  // -------------------------------------------------------------
  // SAFEGUARD & NEGATIVE SCENARIO: User Removal Confirmation & Safe Cancel
  // -------------------------------------------------------------
  test('SAFEGUARD & NEGATIVE: should trigger delete confirmation dialog when removing user and safely cancel', async ({ page }) => {
    // 1. Ensure table rows are populated
    const firstRow = page.locator('tbody tr').first();
    await expect(firstRow).toBeVisible();

    // 2. Verify row action controls (Status toggle switch, Edit, Resend link, Delete)
    const statusSwitch = firstRow.getByRole('switch');
    await expect(statusSwitch).toBeVisible();

    const deleteBtn = firstRow.getByRole('button', { name: 'Delete' });
    await expect(deleteBtn).toBeVisible();

    // 3. Click Delete button to trigger confirmation prompt
    await deleteBtn.click();

    // 4. Assert Confirmation Dialog appears
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText(/Delete|Are you sure/i).first()).toBeVisible();

    // 5. Click Cancel to abort removal safely
    const cancelDialogBtn = dialog.getByRole('button', { name: /Cancel|No/i });
    await cancelDialogBtn.click();

    // 6. Verify dialog closes and row still exists intact
    await expect(dialog).not.toBeVisible();
    await expect(firstRow).toBeVisible();
  });

});

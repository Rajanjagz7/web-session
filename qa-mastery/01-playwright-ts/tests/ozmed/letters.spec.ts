import { test, expect } from '@playwright/test';

test.describe('OzMed Settings - Templates & Referral Letters Module', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate directly to the Letters Templates page
    await page.goto('/settings/templates/letters');
    // Ensure the Letters sub-tab finishes rendering
    await expect(page.getByRole('tab', { name: /Letters/i })).toBeVisible({ timeout: 15000 });
  });

  test('should verify Templates sub-navigation tabs and active Letters view', async ({ page }) => {
    // 1. Verify all 4 Templates sub-tabs exist
    const lettersTab = page.getByRole('tab', { name: /Letters/i });
    await expect(lettersTab).toBeVisible();
    await expect(page.getByRole('tab', { name: /Medical Certificate/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Assessment/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Progress Notes/i })).toBeVisible();

    // 2. Verify Letters tab is currently selected
    await expect(lettersTab).toHaveAttribute('aria-selected', 'true');
  });

  test('should display template table headers and key action controls', async ({ page }) => {
    // 1. Verify Create action button exists
    const createBtn = page.getByRole('button', { name: /Create/i });
    await expect(createBtn).toBeVisible();

    // 2. Verify Search input is present
    const searchInput = page.getByPlaceholder(/Search/i);
    await expect(searchInput).toBeVisible();

    // 3. Verify Table column headers
    const expectedHeaders = ['Template Name', 'Last Modified Date', 'Created By', 'Status'];
    for (const header of expectedHeaders) {
      await expect(
        page.getByRole('columnheader', { name: new RegExp(header, 'i') })
          .or(page.locator(`th:has-text("${header}")`))
          .or(page.getByRole('button', { name: header }))
          .first()
      ).toBeVisible();
    }
  });

  test('should interact with search input and filter dropdowns', async ({ page }) => {
    // 1. Test live search debounce
    const searchInput = page.getByPlaceholder(/Search/i);
    await searchInput.fill('Cardiology');
    await page.waitForTimeout(500);
    await searchInput.fill('');
    await page.waitForTimeout(500);

    // 2. Open Created By autocomplete dropdown
    const popupIndicator = page.locator('.MuiAutocomplete-popupIndicator');
    if (await popupIndicator.isVisible()) {
      await popupIndicator.click();
      await page.waitForTimeout(300);
      await page.keyboard.press('Escape');
    }
  });

  test('should open Create Referral Letter modal, verify all 8 smart placeholders, and discard changes safely', async ({ page }) => {
    // 1. Click Create button to launch modal
    const createBtn = page.getByRole('button', { name: /Create/i });
    await createBtn.click();

    // 2. Verify Modal Dialog renders
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole('heading', { name: /Create Referral Letter/i }).first()).toBeVisible();

    // 3. Verify Template Name and Body fields
    const nameInput = dialog.getByRole('textbox', { name: /Template Name/i });
    await expect(nameInput).toBeVisible();
    const bodyTextarea = dialog.getByRole('textbox', { name: /Template Body/i });
    await expect(bodyTextarea).toBeVisible();

    // 4. Verify all 8 Smart Placeholders buttons
    const smartPlaceholders = [
      'Patient Name',
      'Referral Doctor',
      'Diagnosis',
      'Treatment Plans',
      'Medications',
      'Additional Notes',
      'Provider Name',
      'Provider Number'
    ];

    for (const tag of smartPlaceholders) {
      await expect(dialog.getByRole('button', { name: tag })).toBeVisible();
    }

    // 5. Fill sample template name and click a smart placeholder
    await nameInput.fill('Cardiology Consultation Referral');
    const patientNameBtn = dialog.getByRole('button', { name: 'Patient Name' });
    await patientNameBtn.click();

    // 6. Click Cancel to trigger Unsaved Changes guard
    const cancelBtn = dialog.getByRole('button', { name: /Cancel/i });
    await cancelBtn.click();

    // 7. Verify Unsaved Changes confirmation dialog
    await expect(page.getByRole('heading', { name: 'Unsaved Changes' })).toBeVisible();
    await expect(page.getByText(/Are you sure you want to close without saving/i)).toBeVisible();

    // 8. Click Discard Changes to cleanly dismiss without mutating clinic data
    const discardBtn = page.getByRole('button', { name: /Discard Changes/i });
    await discardBtn.click();

    // 9. Verify both dialogs are closed
    await expect(dialog).not.toBeVisible();
  });

});

import { test, expect } from '@playwright/test';
import { login, pickSearchableOption, openAddProjectDrawer, dismissRegisteredUserDialogIfPresent } from './helpers';

// Plumber/Electrician options are scoped to the selected Company - they were
// empty under "1st Class Heating & Cooling" but populated once "1st Energy"
// is selected, so this suite uses its own company rather than the shared
// COMPANY_SEARCH default used by the other specs.
const COMPANY_SEARCH = process.env.SKILLS_COMPANY_SEARCH || '1st Energy';
const EQUIPMENT_SEARCH = process.env.EQUIPMENT_SEARCH || 'REVERSE CYCLE Non Ducted Air Con';

const PLUMBER_SEARCH = process.env.PLUMBER_SEARCH || 'Gopika Jani';
const ELECTRICIAN_SEARCH = process.env.ELECTRICIAN_SEARCH || 'Test Electrician2';

async function fillBaseProjectFields(page: import('@playwright/test').Page, dialog: import('@playwright/test').Locator, projectName: string) {
  await page.getByPlaceholder('Enter Project Name').fill(projectName);
  await pickSearchableOption(page, dialog.getByRole('combobox').nth(0), COMPANY_SEARCH);
  await pickSearchableOption(page, dialog.getByRole('combobox').nth(3), EQUIPMENT_SEARCH);

  const benefitCombo = dialog.getByRole('combobox').nth(4);
  await benefitCombo.scrollIntoViewIfNeeded();
  await benefitCombo.click();
  await page.getByRole('option', { name: 'Discount' }).click();

  const consumerEmail = `skills.test.${Date.now()}@yopmail.com`;
  const consumerPhone = `04${String(Date.now()).slice(-8)}`;

  await dialog.getByPlaceholder('Enter Consumer Name').fill('Skills Test Consumer');
  await dialog.getByPlaceholder('Enter Email ID').fill(consumerEmail);
  const phoneField = dialog.getByPlaceholder('Enter Phone Number');
  await phoneField.click();
  await page.keyboard.type(consumerPhone);
  await dismissRegisteredUserDialogIfPresent(page);

  await pickSearchableOption(page, dialog.getByRole('combobox').nth(9), '45 Church Street Parramatta');
  await dialog.getByPlaceholder('Enter Postcode').fill('2150');
}

test('creates a project with a single skill assigned (Electrician only)', async ({ page }) => {
  test.setTimeout(90_000);
  test.skip(!ELECTRICIAN_SEARCH, 'ELECTRICIAN_SEARCH is empty - no Electrician records exist yet on this tenant.');

  await login(page);
  const dialog = await openAddProjectDrawer(page);
  const projectName = `skills-single-${Date.now()}`;
  await fillBaseProjectFields(page, dialog, projectName);

  // Electrician only (combobox #6) - Plumber and Refrigeration Mechanic left unset.
  await pickSearchableOption(page, dialog.getByRole('combobox').nth(6), ELECTRICIAN_SEARCH);

  await dialog.getByRole('button', { name: /add project/i }).click();
  await page.getByPlaceholder('Enter Project Name').waitFor({ state: 'hidden', timeout: 15_000 });

  await expect(page.getByText(projectName, { exact: false })).toBeVisible();
});

test('creates a project with multiple skills assigned (Plumber + Electrician)', async ({ page }) => {
  test.setTimeout(90_000);
  test.skip(!PLUMBER_SEARCH || !ELECTRICIAN_SEARCH,
    'PLUMBER_SEARCH / ELECTRICIAN_SEARCH are empty - no Plumber/Electrician records exist yet on this tenant.');

  await login(page);
  const dialog = await openAddProjectDrawer(page);
  const projectName = `skills-multi-${Date.now()}`;
  await fillBaseProjectFields(page, dialog, projectName);

  // Plumber (combobox #5) and Electrician (combobox #6) both assigned.
  await pickSearchableOption(page, dialog.getByRole('combobox').nth(5), PLUMBER_SEARCH);
  await pickSearchableOption(page, dialog.getByRole('combobox').nth(6), ELECTRICIAN_SEARCH);

  await dialog.getByRole('button', { name: /add project/i }).click();
  await page.getByPlaceholder('Enter Project Name').waitFor({ state: 'hidden', timeout: 15_000 });

  await expect(page.getByText(projectName, { exact: false })).toBeVisible();
});

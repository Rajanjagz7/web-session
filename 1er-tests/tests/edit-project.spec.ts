import { test, expect } from '@playwright/test';
import { login, pickSearchableOption, openAddProjectDrawer, findInputByValue, dismissRegisteredUserDialogIfPresent } from './helpers';

const COMPANY_SEARCH = process.env.COMPANY_SEARCH || '1st Class Heating & Cooling';
const EQUIPMENT_SEARCH = process.env.EQUIPMENT_SEARCH || 'REVERSE CYCLE Non Ducted Air Con';

/**
 * This test never touches pre-existing projects: it creates its own
 * disposable project (unique name/consumer per run) and edits that one.
 */
test('creates a project then edits its consumer details', async ({ page }) => {
  test.setTimeout(90_000);
  await login(page);

  const uniqueName = `edit-test-${Date.now()}`;
  const updatedPostcode = '2153';
  // Unique per run so the "Registered User May Already Exist" dialog
  // (matched by phone number) never triggers on a previous run's consumer.
  const initialPhone = `04${String(Date.now()).slice(-8)}`;
  const updatedPhone = `04${String(Date.now() + 1).slice(-8)}`;

  const dialog = await openAddProjectDrawer(page);
  await page.getByPlaceholder('Enter Project Name').fill(uniqueName);
  await pickSearchableOption(page, dialog.getByRole('combobox').nth(0), COMPANY_SEARCH);
  await pickSearchableOption(page, dialog.getByRole('combobox').nth(3), EQUIPMENT_SEARCH);

  const benefitCombo = dialog.getByRole('combobox').nth(4);
  await benefitCombo.scrollIntoViewIfNeeded();
  await benefitCombo.click();
  await page.getByRole('option', { name: 'Discount' }).click();

  await dialog.getByPlaceholder('Enter Consumer Name').fill('Priya Singh');
  await dialog.getByPlaceholder('Enter Email ID').fill(`priya.singh.${Date.now()}@yopmail.com`);
  const phoneField = dialog.getByPlaceholder('Enter Phone Number');
  await phoneField.click();
  await page.keyboard.type(initialPhone);
  await dismissRegisteredUserDialogIfPresent(page);

  await pickSearchableOption(page, dialog.getByRole('combobox').nth(9), '45 Church Street Parramatta');
  await dialog.getByPlaceholder('Enter Postcode').fill('2150');

  await dialog.getByRole('button', { name: /add project/i }).click();
  await page.getByPlaceholder('Enter Project Name').waitFor({ state: 'hidden', timeout: 15_000 });

  // Open the freshly created project's detail page.
  await page.getByPlaceholder('Search Projects...').fill(uniqueName);
  await page.waitForTimeout(1500);
  const row = page.locator('tr', { hasText: uniqueName }).first();
  await row.locator('td').first().locator('span.cursor-pointer').first().click();
  await page.waitForURL(/\/projects\/view\//);
  await page.getByText('Postcode').first().waitFor({ state: 'visible' });
  await page.waitForTimeout(1000); // let the form finish populating from the fetch

  // Edit the open (non-locked) fields and save.
  const postcodeField = await findInputByValue(page, '2150');
  await postcodeField.fill(updatedPostcode);

  // Phone is a masked input - .fill() alone doesn't reliably replace masked
  // values, so select-all then type.
  const phoneOnDetail = await findInputByValue(page, initialPhone);
  await phoneOnDetail.click({ clickCount: 3 });
  await page.keyboard.press('Control+A');
  await page.keyboard.type(updatedPhone);

  await page.getByRole('button', { name: 'Edit Project' }).click();
  await page.waitForTimeout(1500);

  // Verify the change persisted by reloading the detail page.
  await page.reload();
  await page.getByText('Postcode').first().waitFor({ state: 'visible' });
  await page.waitForTimeout(1000);
  await expect(await findInputByValue(page, updatedPostcode)).toBeVisible();
  await expect(await findInputByValue(page, updatedPhone)).toBeVisible();
});

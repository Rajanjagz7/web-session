import { test, expect } from '@playwright/test';
import { login, pickSearchableOption, openAddProjectDrawer, dismissRegisteredUserDialogIfPresent } from './helpers';

const PROJECT_NAME = process.env.PROJECT_NAME || 'nsw rajan';

const COMPANY_SEARCH = process.env.COMPANY_SEARCH || '';
const EQUIPMENT_SEARCH = process.env.EQUIPMENT_SEARCH || '';
const BENEFIT_TYPE = process.env.BENEFIT_TYPE || 'Discount';

const CONSUMER_NAME = process.env.CONSUMER_NAME || 'Rajan Kumar';
const CONSUMER_EMAIL = process.env.CONSUMER_EMAIL || 'rajan.kumar@yopmail.com';
const CONSUMER_PHONE = process.env.CONSUMER_PHONE || '0412 345 678';
const CONSUMER_ADDRESS_SEARCH = process.env.CONSUMER_ADDRESS_SEARCH || '12 George Street Parramatta';
const CONSUMER_POSTCODE = process.env.CONSUMER_POSTCODE || '2150';

test('logs in and creates a new project', async ({ page }) => {
  await login(page);

  const dialog = await openAddProjectDrawer(page);
  await page.getByPlaceholder('Enter Project Name').fill(PROJECT_NAME);

  // Company Name (required, async search)
  await pickSearchableOption(page, dialog.getByRole('combobox').nth(0), COMPANY_SEARCH);

  // Activity Type and Method of Lead Generation are left on their defaults
  // ("Heating & Cooling" / "Customer initiated contact"), which already fit
  // an AC-fitting job.

  // Original Equipment (required, async search)
  await pickSearchableOption(page, dialog.getByRole('combobox').nth(3), EQUIPMENT_SEARCH);

  // Benefit Type (required, fixed list: Discount / Delayed Cash)
  const benefitCombo = dialog.getByRole('combobox').nth(4);
  await benefitCombo.scrollIntoViewIfNeeded();
  await benefitCombo.click();
  await page.getByRole('option', { name: BENEFIT_TYPE }).click();

  // Consumer Information
  await dialog.getByPlaceholder('Enter Consumer Name').fill(CONSUMER_NAME);
  await dialog.getByPlaceholder('Enter Email ID').fill(CONSUMER_EMAIL);

  // This field is a masked phone input - .fill() doesn't trigger its mask
  // logic, so it ends up empty. Click + type instead.
  const phoneField = dialog.getByPlaceholder('Enter Phone Number');
  await phoneField.click();
  await page.keyboard.type(CONSUMER_PHONE);
  await dismissRegisteredUserDialogIfPresent(page);

  // The suggestion list has multiple "12 George Street, ..." entries (different
  // suburbs), so match by name is ambiguous - the first suggestion is the
  // correct exact match ("12 George Street, Parramatta NSW, Australia").
  await pickSearchableOption(page, dialog.getByRole('combobox').nth(9), CONSUMER_ADDRESS_SEARCH);

  await dialog.getByPlaceholder('Enter Postcode').fill(CONSUMER_POSTCODE);
  // Consumer Type is left on its default ("Residential").

  await dialog.getByRole('button', { name: /add project/i }).click();

  // Submission is an API call - wait for the drawer to close rather than
  // asserting immediately.
  await page.getByPlaceholder('Enter Project Name').waitFor({ state: 'hidden', timeout: 15_000 });

  await expect(page.getByText(PROJECT_NAME, { exact: false })).toBeVisible();
});

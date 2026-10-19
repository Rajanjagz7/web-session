import { test, expect, Page, Locator } from '@playwright/test';

const EMAIL = process.env.LOGIN_EMAIL!;
const PASSWORD = process.env.LOGIN_PASSWORD!;
const PROJECT_NAME = process.env.PROJECT_NAME || 'nsw rajan';

const COMPANY_SEARCH = process.env.COMPANY_SEARCH || '';
const EQUIPMENT_SEARCH = process.env.EQUIPMENT_SEARCH || '';
const BENEFIT_TYPE = process.env.BENEFIT_TYPE || 'Discount';

const CONSUMER_NAME = process.env.CONSUMER_NAME || 'Rajan Kumar';
const CONSUMER_EMAIL = process.env.CONSUMER_EMAIL || 'rajan.kumar@yopmail.com';
const CONSUMER_PHONE = process.env.CONSUMER_PHONE || '0412 345 678';
const CONSUMER_ADDRESS_SEARCH = process.env.CONSUMER_ADDRESS_SEARCH || '12 George Street Parramatta';
const CONSUMER_ADDRESS_OPTION = process.env.CONSUMER_ADDRESS_OPTION || '12 George Street, Parramatta NSW';
const CONSUMER_POSTCODE = process.env.CONSUMER_POSTCODE || '2150';

/**
 * This app keeps some connection open (websocket/polling) that never lets
 * the network go idle, so waitForLoadState('networkidle') hangs/times out
 * unreliably. Wait for a concrete post-login element instead.
 */
async function login(page: Page) {
  await page.goto('/log-in');
  await page.getByPlaceholder(/email/i).fill(EMAIL);
  await page.getByPlaceholder(/password/i).fill(PASSWORD);
  await page.getByRole('button', { name: /log ?in|sign ?in/i }).click();
  await page.getByRole('link', { name: 'Projects' }).waitFor({ state: 'visible', timeout: 20_000 });
}

/**
 * Picks an option from one of the drawer's async react-select comboboxes
 * (Company Name / Original Equipment / Address) by typing a search term
 * and clicking the first matching suggestion.
 * Note: pressing Escape here closes the whole "Add Project" drawer, not
 * just the open select - so this always resolves by picking an option.
 */
async function pickSearchableOption(page: Page, combo: Locator, searchTerm: string, optionName?: string | RegExp) {
  await combo.scrollIntoViewIfNeeded();
  await combo.click();
  await page.keyboard.type(searchTerm);
  await page.waitForTimeout(1000);
  const option = optionName
    ? page.getByRole('option', { name: optionName })
    : page.getByRole('option').first();
  await option.click();
}

test('logs in and creates a new project', async ({ page }) => {
  await login(page);

  await page.goto('/projects');
  await expect(page).toHaveURL(/\/projects/);

  await page.getByRole('button', { name: /add project/i }).click();
  const dialog = page.locator('.drawer-portal');
  await page.getByPlaceholder('Enter Project Name').waitFor({ state: 'visible' });

  await page.getByPlaceholder('Enter Project Name').fill(PROJECT_NAME);

  test.skip(!COMPANY_SEARCH || !EQUIPMENT_SEARCH,
    'COMPANY_SEARCH / EQUIPMENT_SEARCH are empty - seed a Company + Equipment record on nswdev, ' +
    'then set those env vars before running this test.');

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

  // If this consumer (matched by phone) already exists from a previous run,
  // a "Registered User May Already Exist" modal blocks the rest of the
  // form - dismiss it via Cancel to create a new user instead.
  const registeredUserDialog = page.getByText('Registered User May Already Exist', { exact: false });
  const registeredUserAppeared = await registeredUserDialog
    .waitFor({ state: 'visible', timeout: 6000 })
    .then(() => true)
    .catch(() => false);
  if (registeredUserAppeared) {
    await page.getByRole('button', { name: 'Cancel' }).click();
  }

  // The suggestion list can have multiple "12 George Street, ..." entries
  // (different suburbs), so matching by name is ambiguous - the first
  // suggestion is the correct exact match for the typed search term.
  await pickSearchableOption(page, dialog.getByRole('combobox').nth(9), CONSUMER_ADDRESS_SEARCH);

  await dialog.getByPlaceholder('Enter Postcode').fill(CONSUMER_POSTCODE);
  // Consumer Type is left on its default ("Residential").

  await dialog.getByRole('button', { name: /add project/i }).click();

  // Submission is an API call - wait for the drawer to close rather than
  // asserting immediately.
  await page.getByPlaceholder('Enter Project Name').waitFor({ state: 'hidden', timeout: 15_000 });

  await expect(page.getByText(PROJECT_NAME, { exact: false })).toBeVisible();
});

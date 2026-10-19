import { Page, Locator } from '@playwright/test';

const EMAIL = process.env.LOGIN_EMAIL!;
const PASSWORD = process.env.LOGIN_PASSWORD!;

/**
 * This app keeps some connection open (websocket/polling) that never lets
 * the network go idle, so waitForLoadState('networkidle') hangs/times out
 * unreliably. Wait for a concrete post-login element instead.
 */
export async function login(page: Page) {
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
export async function pickSearchableOption(page: Page, combo: Locator, searchTerm: string, optionName?: string | RegExp) {
  await combo.scrollIntoViewIfNeeded();
  await combo.click();
  await page.keyboard.type(searchTerm);
  await page.waitForTimeout(1000);
  const option = optionName
    ? page.getByRole('option', { name: optionName })
    : page.getByRole('option').first();
  await option.click();
}

/**
 * The Add Project form pops up a "Registered User May Already Exist" modal
 * if the phone number matches an existing consumer. Test data uses unique
 * phone numbers per run to avoid this, but as a safety net, always choose
 * "Cancel" (create a new user) so tests never silently reuse/mutate a real
 * consumer record.
 */
export async function dismissRegisteredUserDialogIfPresent(page: Page) {
  const dialog = page.getByText('Registered User May Already Exist', { exact: false });
  // The lookup runs async after the phone field is filled/blurred, so give
  // it real time to appear rather than assuming it's already there.
  const appeared = await dialog
    .waitFor({ state: 'visible', timeout: 6000 })
    .then(() => true)
    .catch(() => false);
  if (appeared) {
    await page.getByRole('button', { name: 'Cancel' }).click();
  }
}

export async function openAddProjectDrawer(page: Page) {
  await page.goto('/projects');
  await page.getByRole('button', { name: /add project/i }).click();
  const dialog = page.locator('.drawer-portal');
  await page.getByPlaceholder('Enter Project Name').waitFor({ state: 'visible' });
  return dialog;
}

/**
 * On the project detail/edit page, fields show their current value rather
 * than a placeholder, so they can't be targeted by placeholder text like
 * the Add Project drawer. Match by the live controlled value instead
 * (input.inputValue(), not the static DOM attribute).
 */
export async function findInputByValue(page: Page, currentValue: string): Promise<Locator> {
  const inputs = page.locator('input');
  const count = await inputs.count();
  for (let i = 0; i < count; i++) {
    const input = inputs.nth(i);
    const value = await input.inputValue().catch(() => null);
    if (value === currentValue) return input;
  }
  throw new Error(`No input found with value "${currentValue}"`);
}

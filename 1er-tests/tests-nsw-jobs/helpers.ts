import { Page, Locator, expect } from '@playwright/test';

const EMAIL = process.env.NSW_LOGIN_EMAIL!;
const PASSWORD = process.env.NSW_LOGIN_PASSWORD!;

export async function login(page: Page) {
  await page.goto('/log-in');
  await page.getByPlaceholder(/email/i).fill(EMAIL);
  await page.getByPlaceholder(/password/i).fill(PASSWORD);
  await page.getByRole('button', { name: /log ?in|sign ?in/i }).click();
  await page.getByRole('button', { name: /add job/i }).waitFor({ state: 'visible', timeout: 20_000 });
}

/**
 * Opens the "Add Job" drawer from the All Jobs screen and returns it scoped
 * by role=dialog (it renders as a `.drawer-portal`, same pattern as the
 * 1er.softwareco Add Project drawer).
 */
export async function openAddJobDrawer(page: Page): Promise<Locator> {
  await page.goto('/jobs');
  await page.getByRole('button', { name: /add job/i }).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByPlaceholder('Enter customer name').waitFor({ state: 'visible' });
  return dialog;
}

/**
 * The form is dynamic - selecting Activity type / Building type / Installer
 * inserts extra fields (New system, Equipment to be quoted: Original
 * equipment / Brand / Model) and shifts everything after them, so the
 * react-select controls can't be targeted by a fixed index. Instead, find
 * the "*Label" text and walk up to the nearest ancestor that also contains
 * a `.select__control`, then click that control.
 */
export async function controlForLabel(scope: Locator, labelText: string): Promise<Locator> {
  const label = scope.getByText(labelText, { exact: false }).first();
  const fieldWrapper = label.locator('xpath=ancestor::*[.//*[contains(@class,"select__control")]][1]');
  return fieldWrapper.locator('.select__control').first();
}

export async function selectOption(scope: Locator, labelText: string, optionName: string) {
  const control = await controlForLabel(scope, labelText);
  await control.scrollIntoViewIfNeeded();
  await control.click();
  await scope.page().getByRole('option', { name: optionName, exact: true }).click();
}

export async function fieldExists(scope: Locator, labelText: string): Promise<boolean> {
  return (await scope.getByText(labelText, { exact: false }).count()) > 0;
}

/**
 * Opens a signed job's full detail page (tabs: Job Information / Products /
 * Post Install Details / ...) by searching for its job number in the All
 * Jobs list and clicking the view icon. Only works for jobs already past
 * "Engagement Sent" - unsigned jobs open the Add Job wizard drawer instead.
 */
export async function openJobDetail(page: Page, jobNumber: string) {
  await page.goto('/jobs');
  await page.getByPlaceholder('Search Jobs...').fill(jobNumber);
  await page.waitForTimeout(1200);
  await page.locator('table tbody tr').first().locator('svg, img, button').first().click();
  await page.getByRole('button', { name: 'Job Information', exact: true }).waitFor({ state: 'visible', timeout: 15_000 });
}

export async function openJobDetailTab(page: Page, tabName: string) {
  await page.getByRole('button', { name: tabName, exact: true }).click();
  await page.waitForTimeout(1000);
}

/**
 * Each "+ Add another product" click appends its own Original
 * equipment/Brand/Model block, each wrapped in a
 * `.border-dashed.border-gray-300` container - scoping lookups to that
 * container (rather than the whole dialog) is what lets Product 2, 3, ...
 * be targeted instead of always hitting Product 1's fields.
 */
function productContainer(dialog: Locator, index: number): Locator {
  return dialog.locator('.border-dashed.border-gray-300').nth(index);
}

/**
 * Picks a varied option from whatever react-select dropdown is currently
 * open, rather than always the first one - so Brand/Model (and similar
 * fields) differ across jobs/products instead of every test creating
 * identical equipment. Cycles through the available options using a
 * module-level counter shared across the whole test run.
 */
let _variedOptionCounter = 0;
async function selectVariedOpenOption(page: Page) {
  const options = page.getByRole('option');
  const count = await options.count();
  const index = count > 0 ? _variedOptionCounter % count : 0;
  _variedOptionCounter++;
  await options.nth(index).click();
}

/** Fills one product block's Original equipment / Brand / Model, scoped to that product's own container. */
async function fillProductBlock(container: Locator) {
  const page = container.page();
  // Option was 'No existing system (new installation)'; the live NSW dev
  // site now offers 'Installation of a New <product noun>' / 'Replacement
  // of an Existing <product noun>' instead (confirmed via a failed-run page
  // snapshot on 2026-09-16). The noun is category-specific (e.g. 'Air
  // Conditioner' for Heating & Cooling vs. something else for Hot Water Heat
  // Pump), so match the common prefix instead of one category's exact text.
  const originalEquipmentControl = await controlForLabel(container, 'Original Equipment');
  await originalEquipmentControl.scrollIntoViewIfNeeded();
  await originalEquipmentControl.click();
  await page.getByRole('option', { name: /^Installation of a New/i }).click();
  await page.waitForTimeout(500);
  // Brand is only rendered for some Activity type / Original equipment
  // combinations (e.g. it disappears for Hot Water Heat Pump + "No
  // existing system"), so only fill it if it's actually there.
  if (await fieldExists(container, 'Brand')) {
    const brandControl = await controlForLabel(container, 'Brand');
    await brandControl.scrollIntoViewIfNeeded();
    await brandControl.click();
    await page.waitForTimeout(300);
    await selectVariedOpenOption(page);
    await page.waitForTimeout(500);
  }
  const modelControl = await controlForLabel(container, 'Model');
  await modelControl.scrollIntoViewIfNeeded();
  await modelControl.click();
  await page.waitForTimeout(300);
  await selectVariedOpenOption(page);
  await page.waitForTimeout(300);
}

/**
 * Site address is an async Google-Places-style search. Types the search
 * term and clicks the first suggestion.
 */
export async function pickAddress(dialog: Locator, searchTerm: string) {
  const control = await controlForLabel(dialog, 'Site address');
  await control.scrollIntoViewIfNeeded();
  await control.click();
  await dialog.page().keyboard.type(searchTerm);
  await dialog.page().waitForTimeout(1200);
  await dialog.page().getByRole('option').first().click();
}

export interface JobFields {
  customerName?: string;
  email?: string;
  phone?: string; // digits only, no country code (field already shows +61)
  abnAcn?: string;
  addressSearch?: string;
  postcode?: string;
  activityType?: string; // 'Heating & Cooling' | 'Hot Water Heat Pump'
  buildingType?: string; // 'Residential Building' | 'Small Business Site'
  // Only rendered/required when activityType is 'Hot Water Heat Pump':
  // 'Heat pump' | 'Solar (electric boosted)'
  newSystem?: string;
  // 'Customer initiated contact' | 'Social media' | 'Email campaign' |
  // 'Print advertisement' | 'Online advertisement' | 'Pamphlet' |
  // 'Promotional booth' | 'Other' | 'Radio advertisement' |
  // 'Telemarketing with express prior consent' |
  // 'Door-to-door sales with express prior consent' | 'TV advertisement' |
  // 'Telemarketing (pre-1 May 2024)' | 'Doorknocking (pre-1 August 2024)'
  leadMethod?: string;
  ownReference?: string;
  installationDate?: string; // DD-MM-YYYY
  installer?: string;
  /**
   * Fills the "Equipment to be quoted" product block (Original equipment /
   * Brand / Model) that appears once Installer is selected. Only needed
   * when the job is expected to actually submit successfully - negative
   * tests that expect a required-field error don't need this. Shorthand for
   * `productCount: 1`.
   */
  fillEquipment?: boolean;
  /**
   * Fills this many product blocks, clicking "+ Add another product"
   * (productCount - 1) times first. Takes precedence over `fillEquipment`.
   */
  productCount?: number;
}

/**
 * Fills whichever fields are present in `fields`, leaving the rest blank -
 * lets negative-path tests omit specific fields on purpose. Order matters:
 * Activity type must be chosen before Building type/New system, and
 * Installer must be chosen before the Equipment block exists at all.
 */
export async function fillJobForm(dialog: Locator, fields: JobFields) {
  const page = dialog.page();

  if (fields.customerName !== undefined) {
    await dialog.getByPlaceholder('Enter customer name').fill(fields.customerName);
  }
  if (fields.email !== undefined) {
    // Placeholder was 'customer@email.com'; the live NSW dev site now shows
    // 'Enter email' (confirmed via a failed-run page snapshot on 2026-09-16).
    await dialog.getByPlaceholder('Enter email').fill(fields.email);
  }
  if (fields.phone !== undefined) {
    // Masked phone input (react-phone-input) - .fill() doesn't trigger the
    // mask, so click + type instead. Each test gets a fresh dialog with the
    // field already empty (just the +61 prefix), so no need to clear first.
    // Placeholder was '412345678'; the live NSW dev site now shows
    // 'Enter phone number' (confirmed via a failed-run page snapshot on 2026-09-16).
    const phoneField = dialog.getByPlaceholder('Enter phone number');
    await phoneField.click();
    await page.keyboard.type(fields.phone);
  }
  if (fields.abnAcn !== undefined) {
    await dialog.getByPlaceholder('12345678901').fill(fields.abnAcn);
  }
  if (fields.addressSearch !== undefined) {
    await pickAddress(dialog, fields.addressSearch);
  }
  if (fields.postcode !== undefined) {
    await dialog.getByPlaceholder('2000').fill(fields.postcode);
  }
  if (fields.activityType !== undefined) {
    await selectOption(dialog, 'Activity type', fields.activityType);
  }
  if (fields.buildingType !== undefined) {
    await selectOption(dialog, 'Building type', fields.buildingType);
  }
  if (fields.newSystem !== undefined) {
    // Only present when Activity type is 'Hot Water Heat Pump' AND
    // Building type is 'Residential Building' - absent for Small Business
    // Site, so check before trying to select it.
    if (await fieldExists(dialog, 'New system')) {
      await selectOption(dialog, 'New system', fields.newSystem);
    }
  }
  if (fields.leadMethod !== undefined) {
    await selectOption(dialog, 'Method of lead generation', fields.leadMethod);
  }
  if (fields.ownReference !== undefined) {
    await dialog.getByPlaceholder('REF-001').fill(fields.ownReference);
  }
  if (fields.installationDate !== undefined) {
    // Masked date input - .fill() doesn't trigger the mask, click + type.
    const dateField = dialog.getByPlaceholder('DD-MM-YYYY');
    await dateField.click();
    await page.keyboard.type(fields.installationDate);
  }
  if (fields.installer !== undefined) {
    await selectOption(dialog, 'Installer (company)', fields.installer);
    // Selecting the installer inserts the "Equipment to be quoted" block.
    await page.waitForTimeout(500);
    // The live site now also inserts a required "Name of Installer Attended
    // Site Inspection" dropdown once Installer (company) is chosen
    // (confirmed via a failed-run page snapshot on 2026-09-16 - this field
    // did not exist when this suite was originally written). Its options
    // are specific to whichever installer company was selected, so there's
    // no fixed name to hardcode - pick whichever option is available,
    // varying across jobs the same way Brand/Model do.
    if (await fieldExists(dialog, 'Name of Installer Attended Site Inspection')) {
      const attendeeControl = await controlForLabel(dialog, 'Name of Installer Attended Site Inspection');
      await attendeeControl.scrollIntoViewIfNeeded();
      await attendeeControl.click();
      await page.waitForTimeout(300);
      await selectVariedOpenOption(page);
      await page.waitForTimeout(300);
    }
  }
  const productCount = fields.productCount ?? (fields.fillEquipment ? 1 : undefined);
  if (productCount !== undefined && productCount > 0) {
    const addProductBtn = dialog.getByRole('button', { name: /add another product/i });
    for (let p = 1; p < productCount; p++) {
      await addProductBtn.click();
      await page.waitForTimeout(400);
    }
    for (let p = 0; p < productCount; p++) {
      await fillProductBlock(productContainer(dialog, p));
    }
  }
}

export async function submitJob(dialog: Locator) {
  await dialog.getByRole('button', { name: /send engagement letter/i }).click();
}

export async function expectFieldError(dialog: Locator, message: string) {
  await expect(dialog.getByText(message, { exact: true })).toBeVisible();
}

/**
 * For exploratory edge cases where the expected outcome isn't known ahead
 * of time: submits, waits, then reports (via console.log, visible in the
 * test run output) whether the job was created or the submission was
 * blocked - and dumps the drawer's validation text when blocked. Always
 * resolves rather than asserting a specific outcome, so the test documents
 * real behaviour instead of guessing at it.
 */
export async function submitAndReport(page: Page, dialog: Locator, label: string): Promise<{ created: boolean }> {
  await submitJob(dialog);
  await page.waitForTimeout(2500);
  const stillOpen = await dialog.getByPlaceholder('Enter customer name').isVisible().catch(() => false);
  if (stillOpen) {
    console.log(`[${label}] Result: submission BLOCKED. Dialog text:\n` + (await dialog.innerText()));
  } else {
    console.log(`[${label}] Result: job CREATED.`);
  }
  return { created: !stillOpen };
}

/** Asserts the drawer closed and the new job shows up in the All Jobs list. */
export async function expectJobCreated(page: Page, dialog: Locator, customerName: string) {
  await dialog.getByPlaceholder('Enter customer name').waitFor({ state: 'hidden', timeout: 15_000 });
  await expect(page.getByText(customerName, { exact: false }).first()).toBeVisible({ timeout: 15_000 });
}

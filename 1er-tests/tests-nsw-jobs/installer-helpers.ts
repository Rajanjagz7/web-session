import { Page, expect } from '@playwright/test';

/**
 * Helpers for the "Add Installer" flow (/installer/add). Unlike Add Job,
 * this is a dedicated page (not a drawer), and both phone inputs
 * (Company Phone Number / Primary Admin Phone Number) share the exact same
 * placeholder text "Company Phone Number", so they're targeted by order
 * (first = company, last = primary admin) rather than by unique placeholder.
 */

export interface InstallerFields {
  accountStatus?: 'Active' | 'Inactive';
  companyName?: string;
  abn?: string;
  address?: string;
  companyPhone?: string; // digits typed after the fixed "+61" prefix
  website?: string;
  companyEmail?: string;
  suburb?: string;
  firstName?: string;
  lastName?: string;
  adminPhone?: string; // digits typed after the fixed "+61" prefix
  adminEmail?: string;
}

export async function openAddInstallerPage(page: Page) {
  await page.goto('/installer/add');
  await page.getByPlaceholder('Registered Company Name').waitFor({ state: 'visible' });
}

/** Fills whichever fields are present, leaving the rest untouched. */
export async function fillInstallerForm(page: Page, fields: InstallerFields) {
  if (fields.accountStatus !== undefined) {
    await page.getByRole('radio', { name: fields.accountStatus }).check();
  }
  if (fields.companyName !== undefined) {
    await page.getByPlaceholder('Registered Company Name').fill(fields.companyName);
  }
  if (fields.abn !== undefined) {
    await page.getByPlaceholder('ABN').fill(fields.abn);
  }
  if (fields.address !== undefined) {
    await page.getByPlaceholder('Registered Company Address').fill(fields.address);
  }
  if (fields.companyPhone !== undefined) {
    const phoneField = page.getByPlaceholder('Company Phone Number').first();
    await phoneField.click();
    await page.keyboard.type(fields.companyPhone);
  }
  if (fields.website !== undefined) {
    await page.getByPlaceholder('https://example.com').fill(fields.website);
  }
  if (fields.companyEmail !== undefined) {
    await page.getByPlaceholder('Company Email Address').fill(fields.companyEmail);
  }
  if (fields.suburb !== undefined) {
    await page.getByPlaceholder('Enter Suburb').fill(fields.suburb);
  }
  if (fields.firstName !== undefined) {
    await page.getByPlaceholder('Primary Admin First Name').fill(fields.firstName);
  }
  if (fields.lastName !== undefined) {
    await page.getByPlaceholder('Primary Admin Last Name').fill(fields.lastName);
  }
  if (fields.adminPhone !== undefined) {
    const phoneField = page.getByPlaceholder('Company Phone Number').last();
    await phoneField.click();
    await page.keyboard.type(fields.adminPhone);
  }
  if (fields.adminEmail !== undefined) {
    await page.getByPlaceholder('Primary Admin Email Address').fill(fields.adminEmail);
  }
}

export async function submitInstaller(page: Page) {
  await page.getByRole('button', { name: 'Submit', exact: true }).click();
}

export async function expectInstallerFieldError(page: Page, message: string) {
  await expect(page.getByText(message, { exact: true })).toBeVisible();
}

/**
 * Submits and reports (via console.log) whether the installer was created
 * (page navigated away from /installer/add) or the submission was blocked
 * (still on the add page) - dumping validation text when blocked. Mirrors
 * the tests-nsw-jobs/helpers.ts submitAndReport pattern used for Add Job,
 * so exploratory cases document real behaviour instead of assuming it.
 */
export async function submitInstallerAndReport(page: Page, label: string): Promise<{ created: boolean; url: string }> {
  await submitInstaller(page);
  await page.waitForTimeout(2500);
  const stillOnAddPage = page.url().includes('/installer/add');
  if (stillOnAddPage) {
    const bodyText = await page.locator('main').innerText().catch(() => '(could not read main)');
    console.log(`[${label}] Result: submission BLOCKED (still on /installer/add). Visible text:\n${bodyText}`);
  } else {
    console.log(`[${label}] Result: navigated away to ${page.url()} - likely CREATED.`);
  }
  return { created: !stillOnAddPage, url: page.url() };
}

export async function findInstallerFieldByValue(page: Page, currentValue: string) {
  const inputs = page.locator('input');
  const count = await inputs.count();
  for (let i = 0; i < count; i++) {
    const input = inputs.nth(i);
    const value = await input.inputValue().catch(() => null);
    if (value === currentValue) return input;
  }
  throw new Error(`No installer form input found with value "${currentValue}"`);
}

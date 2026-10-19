import { test, expect } from '@playwright/test';
import { login } from './helpers';
import {
  openAddInstallerPage,
  fillInstallerForm,
  submitInstaller,
  submitInstallerAndReport,
  expectInstallerFieldError,
} from './installer-helpers';

const RUN_ID = Date.now().toString().slice(-8);
const uniq = (n: number) => `${RUN_ID}${n}`;

const validBase = (i: number) => ({
  companyName: `QA Installer ${uniq(i)}`,
  abn: uniq(i).padStart(11, '5').slice(-11),
  address: '1 George Street, Sydney NSW 2000',
  companyEmail: `qa.installer.${uniq(i)}@yopmail.com`,
  suburb: 'Sydney',
  firstName: 'QA',
  lastName: `Tester${i}`,
  adminPhone: `4${uniq(i).padStart(8, '0').slice(-8)}`,
  adminEmail: `qa.admin.${uniq(i)}@yopmail.com`,
});

test.describe('Add Installer - mandatory field validation', () => {
  test('submitting a completely empty form shows a required message for every mandatory field', async ({ page }) => {
    await login(page);
    await openAddInstallerPage(page);
    await submitInstaller(page);

    for (const message of [
      'Company name is required',
      'Company ABN / ACN is required',
      'Address is required',
      'First name is required',
      'Last name is required',
      'Primary admin phone number is required',
      'Primary admin email is required',
    ]) {
      await expectInstallerFieldError(page, message);
    }

    // Optional fields must NOT show a required error.
    for (const message of ['Company phone number is required', 'Website is required', 'Company email is required', 'Suburb is required']) {
      await expect(page.getByText(message, { exact: true })).toHaveCount(0);
    }

    // The form must not have actually submitted / navigated away.
    await expect(page).toHaveURL(/\/installer\/add/);
  });

  test('shows format validation for an invalid Company Email and Primary Admin Email', async ({ page }) => {
    await login(page);
    await openAddInstallerPage(page);
    await fillInstallerForm(page, { ...validBase(1), companyEmail: 'not-an-email', adminEmail: 'also-not-an-email' });
    await submitInstaller(page);
    await page.waitForTimeout(1000);
    console.log('[Email format] visible text:\n' + (await page.locator('main').innerText()));
    await expect(page).toHaveURL(/\/installer\/add/);
  });

  test('shows format validation for an invalid Website Address', async ({ page }) => {
    await login(page);
    await openAddInstallerPage(page);
    await fillInstallerForm(page, { ...validBase(2), website: 'not-a-url' });
    await submitInstaller(page);
    await page.waitForTimeout(1000);
    console.log('[Website format] visible text:\n' + (await page.locator('main').innerText()));
    await expect(page).toHaveURL(/\/installer\/add/);
  });

  test('ABN: fewer than 11 digits is handled', async ({ page }) => {
    await login(page);
    await openAddInstallerPage(page);
    await fillInstallerForm(page, { ...validBase(3), abn: '123456789' });
    await submitInstallerAndReport(page, 'ABN 9-digit');
  });

  test('ABN: letters mixed with digits are handled', async ({ page }) => {
    await login(page);
    await openAddInstallerPage(page);
    await fillInstallerForm(page, { ...validBase(4), abn: '1234ABCD901' });
    const held = await page.getByPlaceholder('ABN').inputValue();
    console.log(`[ABN letters] field holds "${held}"`);
    await submitInstallerAndReport(page, 'ABN letters');
  });

  test('ABN: all zeros (11 digits, syntactically valid but not a real ABN)', async ({ page }) => {
    await login(page);
    await openAddInstallerPage(page);
    await fillInstallerForm(page, { ...validBase(5), abn: '00000000000' });
    await submitInstallerAndReport(page, 'ABN all-zeros');
  });

  test('Primary admin phone: fewer digits than required is handled', async ({ page }) => {
    await login(page);
    await openAddInstallerPage(page);
    await fillInstallerForm(page, { ...validBase(6), adminPhone: '412345' });
    await submitInstallerAndReport(page, 'Admin phone short');
  });

  test('creates a brand-new installer end-to-end with straightforward valid data', async ({ page }) => {
    test.setTimeout(60_000);
    await login(page);
    await openAddInstallerPage(page);
    const fields = validBase(99);
    await fillInstallerForm(page, fields);
    const { created, url } = await submitInstallerAndReport(page, 'Happy path create');
    console.log(`[Happy path create] created=${created}, landed on ${url}`);
  });
});

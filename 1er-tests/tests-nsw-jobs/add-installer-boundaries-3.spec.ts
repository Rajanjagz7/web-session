import { test, expect } from '@playwright/test';
import { login } from './helpers';
import { openAddInstallerPage, fillInstallerForm, submitInstaller, submitInstallerAndReport } from './installer-helpers';

const RUN_ID = Date.now().toString().slice(-8);
const uniq = (n: number) => `${RUN_ID}${n}`;

const validBase = (i: number) => ({
  companyName: `QA Bnd ${uniq(i)}`,
  abn: uniq(i).padStart(11, '9').slice(-11),
  address: '1 George Street, Sydney NSW 2000',
  companyEmail: `qa.bnd.${uniq(i)}@yopmail.com`,
  suburb: 'Sydney',
  firstName: 'QA',
  lastName: `BndTester${i}`,
  adminPhone: `4${uniq(i).padStart(8, '2').slice(-8)}`,
  adminEmail: `qa.bnd.admin.${uniq(i)}@yopmail.com`,
});

test('Duplicate ABN: capture the FULL page (not just <main>) to see whether a toast/snackbar explains the block', async ({ page }) => {
  test.setTimeout(90_000);
  const sharedAbn = uniq(1).padStart(11, '4').slice(-11);

  await login(page);
  await openAddInstallerPage(page);
  await fillInstallerForm(page, { ...validBase(1), abn: sharedAbn });
  await submitInstaller(page);
  await page.waitForTimeout(2500);

  await openAddInstallerPage(page);
  await fillInstallerForm(page, { ...validBase(2), abn: sharedAbn });
  await submitInstaller(page);
  // Capture immediately (500ms) in case it's a fast-fading toast, then again at 3s.
  await page.waitForTimeout(500);
  console.log('[Duplicate ABN full-page @500ms]\n' + await page.locator('body').innerText());
  await page.waitForTimeout(2500);
  console.log('[Duplicate ABN full-page @3s]\n' + await page.locator('body').innerText());
  console.log(`[Duplicate ABN] final URL: ${page.url()}`);
});

test('Mandatory text fields: whitespace-only input is handled the same as blank', async ({ page }) => {
  test.setTimeout(60_000);
  await login(page);
  await openAddInstallerPage(page);
  await fillInstallerForm(page, {
    ...validBase(3),
    companyName: '   ',
    address: '   ',
    firstName: '   ',
    lastName: '   ',
  });
  await submitInstaller(page);
  await page.waitForTimeout(1500);
  console.log('[Whitespace-only mandatory fields] visible text:\n' + await page.locator('main').innerText());
  await expect(page).toHaveURL(/\/installer\/add/);
});

test('Company Name: extremely long input (500 chars) is handled', async ({ page }) => {
  test.setTimeout(60_000);
  await login(page);
  await openAddInstallerPage(page);
  const longName = 'Q'.repeat(500);
  await fillInstallerForm(page, { ...validBase(4), companyName: longName });
  const held = await page.getByPlaceholder('Registered Company Name').inputValue();
  console.log(`[Company name 500-char] field holds length: ${held.length}`);
  await submitInstallerAndReport(page, 'Company name 500-char');
});

test('Registered Company Address: extremely long input (500 chars) is handled', async ({ page }) => {
  test.setTimeout(60_000);
  await login(page);
  await openAddInstallerPage(page);
  const longAddress = 'A'.repeat(500);
  await fillInstallerForm(page, { ...validBase(5), address: longAddress });
  const held = await page.getByPlaceholder('Registered Company Address').inputValue();
  console.log(`[Address 500-char] field holds length: ${held.length}`);
  await submitInstallerAndReport(page, 'Address 500-char');
});

test('Primary Admin First/Last Name: unicode and emoji are handled', async ({ page }) => {
  test.setTimeout(60_000);
  await login(page);
  await openAddInstallerPage(page);
  await fillInstallerForm(page, { ...validBase(6), firstName: 'José 🎉', lastName: "O'Connor-Nguyen" });
  const { created } = await submitInstallerAndReport(page, 'Name unicode/emoji');
  if (created) {
    await page.goto('/installer');
    await page.getByPlaceholder('Search Installer...').fill(validBase(6).companyName);
    await page.waitForTimeout(1500);
    console.log('[Name unicode/emoji] list row text:\n' + await page.locator('main').innerText());
  }
});

test('Suburb: numbers-only and special characters are handled (optional field)', async ({ page }) => {
  test.setTimeout(60_000);
  await login(page);
  await openAddInstallerPage(page);
  await fillInstallerForm(page, { ...validBase(7), suburb: '12345 !@#$%' });
  await submitInstallerAndReport(page, 'Suburb numbers/special-chars');
});

test('Account Status: the form defaults to "Inactive" - verify what actually gets saved', async ({ page }) => {
  test.setTimeout(60_000);
  await login(page);
  await openAddInstallerPage(page);
  const defaultChecked = await page.getByRole('radio', { name: 'Inactive' }).isChecked();
  console.log(`[Account status default] "Inactive" radio checked by default: ${defaultChecked}`);

  const fields = validBase(8);
  await fillInstallerForm(page, fields); // status left on its default
  const { created } = await submitInstallerAndReport(page, 'Account status default create');
  if (created) {
    await page.goto('/installer');
    await page.getByPlaceholder('Search Installer...').fill(fields.companyName);
    await page.waitForTimeout(1500);
    console.log('[Account status default] resulting list row:\n' + await page.locator('main').innerText());
  }
});

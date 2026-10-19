import { test, expect } from '@playwright/test';
import { login, openAddJobDrawer, fillJobForm, submitJob, submitAndReport, controlForLabel } from './helpers';

const INSTALLER_COMPANY = process.env.NSW_INSTALLER_COMPANY || 'Rajan Testing Company';
const RUN_ID = Date.now().toString().slice(-8);
const uniq = (n: number) => `${RUN_ID}${n}`;
const abn = (n: number) => uniq(n).padStart(11, '0').slice(-11);
const phone = (n: number) => `4${uniq(n).padStart(8, '0').slice(-8)}`;

const baseValid = (i: number) => ({
  customerName: `Field Boundary ${i}`,
  email: `field.boundary.${uniq(i)}@yopmail.com`,
  phone: phone(i),
  abnAcn: abn(i),
  addressSearch: '1 George Street Sydney',
  postcode: '2000',
  activityType: 'Heating & Cooling',
  buildingType: 'Residential Building',
  leadMethod: 'Customer initiated contact',
  ownReference: `REF-${RUN_ID}-BND${i}`,
  installationDate: '15-10-2026',
  installer: INSTALLER_COMPANY,
  fillEquipment: true,
});

test.describe('Add Job - per-field boundary, invalid & negative values', () => {
  test('ABN/ACN: negative-sign prefix is handled (accepted/stripped/rejected - documents actual behaviour)', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(1), abnAcn: undefined });
    const abnField = dialog.getByPlaceholder('12345678901');
    await abnField.fill('-1234567890');
    const held = await abnField.inputValue();
    console.log(`[ABN negative-sign] typed "-1234567890" -> field holds "${held}"`);
    await submitAndReport(page, dialog, 'ABN negative-sign');
  });

  test('ABN/ACN: letters mixed with digits are handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(2), abnAcn: undefined });
    const abnField = dialog.getByPlaceholder('12345678901');
    await abnField.fill('1234ABCD901');
    const held = await abnField.inputValue();
    console.log(`[ABN letters] typed "1234ABCD901" -> field holds "${held}"`);
    await submitAndReport(page, dialog, 'ABN letters');
  });

  test('ABN/ACN: all-zeros (11 digits) is a syntactically valid but meaningless ABN', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(3), abnAcn: '00000000000' });
    const { created } = await submitAndReport(page, dialog, 'ABN all-zeros');
    console.log(`[ABN all-zeros] job created: ${created}`);
  });

  test('Postcode: negative-sign prefix is handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(4), postcode: undefined });
    const postcodeField = dialog.getByPlaceholder('2000');
    await postcodeField.fill('-200');
    const held = await postcodeField.inputValue();
    console.log(`[Postcode negative-sign] typed "-200" -> field holds "${held}"`);
    await submitAndReport(page, dialog, 'Postcode negative-sign');
  });

  test('Postcode: letters are handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(5), postcode: undefined });
    const postcodeField = dialog.getByPlaceholder('2000');
    await postcodeField.fill('ABCD');
    const held = await postcodeField.inputValue();
    console.log(`[Postcode letters] typed "ABCD" -> field holds "${held}"`);
    await submitAndReport(page, dialog, 'Postcode letters');
  });

  test('Postcode: all-zeros (0000) is a syntactically valid but nonexistent postcode', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(6), postcode: '0000' });
    const { created } = await submitAndReport(page, dialog, 'Postcode all-zeros');
    console.log(`[Postcode all-zeros] job created: ${created}`);
  });

  test('Phone: negative-sign and decimal characters are handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(7), phone: undefined });
    const phoneField = dialog.getByPlaceholder('412345678');
    await phoneField.click();
    await page.keyboard.type('-41.234.567');
    const held = await phoneField.inputValue();
    console.log(`[Phone negative/decimal] typed "-41.234.567" -> field holds "${held}"`);
    await submitAndReport(page, dialog, 'Phone negative/decimal');
  });

  test('Installation date (wizard field): non-numeric characters are handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(8), installationDate: undefined });
    const dateField = dialog.getByPlaceholder('DD-MM-YYYY');
    await dateField.click();
    await page.keyboard.type('AB-CD-EFGH');
    const held = await dateField.inputValue();
    console.log(`[Date non-numeric] typed "AB-CD-EFGH" -> field holds "${held}"`);
    await submitAndReport(page, dialog, 'Date non-numeric');
  });

  test('Installation date (wizard field): extreme boundary years 0001 and 9999', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(9), installationDate: undefined });
    const dateField = dialog.getByPlaceholder('DD-MM-YYYY');

    await dateField.click();
    await page.keyboard.type('01-01-0001');
    console.log(`[Date year 0001] field holds "${await dateField.inputValue()}"`);

    await dateField.fill('');
    await dateField.click();
    await page.keyboard.type('31-12-9999');
    console.log(`[Date year 9999] field holds "${await dateField.inputValue()}"`);

    await submitAndReport(page, dialog, 'Date extreme years');
  });

  test('Installation date (wizard field): incomplete date is handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(10), installationDate: undefined });
    const dateField = dialog.getByPlaceholder('DD-MM-YYYY');
    await dateField.click();
    await page.keyboard.type('15-13');
    console.log(`[Date incomplete] typed "15-13" -> field holds "${await dateField.inputValue()}"`);
    await submitAndReport(page, dialog, 'Date incomplete');
  });

  test('Site address: a nonsense search string returns no suggestions and the field stays required', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(11), addressSearch: undefined });

    const addressControl = await controlForLabel(dialog, 'Site address');
    await addressControl.click();
    await page.keyboard.type('zzzzxxxxqqqq99999nonexistentplace');
    await page.waitForTimeout(1500);
    const optionCount = await page.getByRole('option').count();
    console.log(`[Address gibberish] suggestion count: ${optionCount}`);
    expect(optionCount).toBe(0);

    // Close the dropdown without selecting anything by clicking a neutral
    // area - pressing Escape here closes the whole drawer, not just the
    // open select (a known gotcha in this app, see helpers.ts history).
    await dialog.getByText('Add Job', { exact: true }).first().click();
    await page.waitForTimeout(300);
    await submitJob(dialog);
    await page.waitForTimeout(1500);
    await expect(dialog.getByText('Site address is required', { exact: true })).toBeVisible();
  });

  test('Own reference: a negative number and a decimal are accepted as free text', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(12), ownReference: '-999.50' });
    const refField = dialog.getByPlaceholder('REF-001');
    console.log(`[Own reference negative/decimal] field holds "${await refField.inputValue()}"`);
    await submitAndReport(page, dialog, 'Own reference negative/decimal');
  });
});

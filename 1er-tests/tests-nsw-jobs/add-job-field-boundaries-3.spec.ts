import { test, expect } from '@playwright/test';
import { login, openAddJobDrawer, fillJobForm, submitJob, submitAndReport, expectJobCreated } from './helpers';

const INSTALLER_COMPANY = process.env.NSW_INSTALLER_COMPANY || 'Rajan Testing Company';
const RUN_ID = Date.now().toString().slice(-8);
const uniq = (n: number) => `${RUN_ID}${n}`;
const abn = (n: number) => uniq(n).padStart(11, '0').slice(-11);
const phone = (n: number) => `4${uniq(n).padStart(8, '0').slice(-8)}`;

const baseValid = (i: number) => ({
  customerName: `Field Boundary Three ${i}`,
  email: `field.boundary.three.${uniq(i)}@yopmail.com`,
  phone: phone(i),
  abnAcn: abn(i),
  addressSearch: '1 George Street Sydney',
  postcode: '2000',
  activityType: 'Heating & Cooling',
  buildingType: 'Residential Building',
  leadMethod: 'Customer initiated contact',
  ownReference: `REF-${RUN_ID}-BND3-${i}`,
  installationDate: '15-10-2026',
  installer: INSTALLER_COMPANY,
  fillEquipment: true,
});

test.describe('Add Job - create a new install (happy path)', () => {
  test('creates a brand-new job end-to-end with straightforward valid data', async ({ page }) => {
    test.setTimeout(90_000);
    await login(page);
    const dialog = await openAddJobDrawer(page);
    const customerName = `New Install ${RUN_ID}`;
    await fillJobForm(dialog, { ...baseValid(0), customerName });
    await submitJob(dialog);
    await expectJobCreated(page, dialog, customerName);
  });
});

test.describe('Add Job - new negative & boundary values (round 3)', () => {
  test('Customer name: whitespace-only is treated as blank / required', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(1), customerName: '   ' });
    await submitJob(dialog);
    await page.waitForTimeout(1500);
    const stillOpen = await dialog.getByPlaceholder('Enter customer name').isVisible().catch(() => false);
    console.log(`[Name whitespace-only] submission blocked: ${stillOpen}`);
    expect(stillOpen).toBe(true);
  });

  test('Customer name: markup/script-like input is stored as inert text, not executed', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    const injected = '<script>window.__xss=1</script>';
    await fillJobForm(dialog, { ...baseValid(2), customerName: injected });
    const { created } = await submitAndReport(page, dialog, 'Name script-tag');
    if (created) {
      const executed = await page.evaluate(() => (window as any).__xss === 1);
      console.log(`[Name script-tag] script executed on page: ${executed}`);
      expect(executed).toBe(false);
    }
  });

  test('Phone: one digit short of the required 9 is rejected', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(3), phone: undefined });
    const phoneField = dialog.getByPlaceholder('412345678');
    await phoneField.click();
    await page.keyboard.type('4123456');
    const held = await phoneField.inputValue();
    console.log(`[Phone 7-digit] field holds "${held}"`);
    await submitAndReport(page, dialog, 'Phone 7-digit');
  });

  test('ABN/ACN: 12 digits (one over the required 11) is handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(4), abnAcn: undefined });
    const abnField = dialog.getByPlaceholder('12345678901');
    await abnField.fill('123456789012');
    const held = await abnField.inputValue();
    console.log(`[ABN 12-digit] typed "123456789012" -> field holds "${held}"`);
    await submitAndReport(page, dialog, 'ABN 12-digit');
  });

  test('Postcode: a real low-numbered postcode with a leading zero (0200, ACT) is a boundary distinct from 2000', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(5), postcode: '0200' });
    const held = await dialog.getByPlaceholder('2000').inputValue();
    console.log(`[Postcode leading-zero] field holds "${held}"`);
    await submitAndReport(page, dialog, 'Postcode leading-zero');
  });

  test('Installation date: an invalid calendar date (31-02, Feb 31st) that still fits the mask is handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(6), installationDate: undefined });
    const dateField = dialog.getByPlaceholder('DD-MM-YYYY');
    await dateField.click();
    await page.keyboard.type('31-02-2026');
    const held = await dateField.inputValue();
    console.log(`[Date Feb-31] typed "31-02-2026" -> field holds "${held}"`);
    await submitAndReport(page, dialog, 'Date Feb-31');
  });

  test('Installation date: a date already in the past is handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(7), installationDate: undefined });
    const dateField = dialog.getByPlaceholder('DD-MM-YYYY');
    await dateField.click();
    await page.keyboard.type('01-01-2020');
    console.log(`[Date past] field holds "${await dateField.inputValue()}"`);
    await submitAndReport(page, dialog, 'Date past');
  });

  test('Own reference: markup/script-like input is stored as inert text, not executed', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    const injected = '"><img src=x onerror=window.__xss2=1>';
    await fillJobForm(dialog, { ...baseValid(8), ownReference: injected });
    const { created } = await submitAndReport(page, dialog, 'Own reference script-like');
    if (created) {
      const executed = await page.evaluate(() => (window as any).__xss2 === 1);
      console.log(`[Own reference script-like] script executed on page: ${executed}`);
      expect(executed).toBe(false);
    }
  });

  test('Customer name: extremely long (300 chars) is handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    const longName = 'Z'.repeat(300);
    await fillJobForm(dialog, { ...baseValid(9), customerName: longName });
    const held = await dialog.getByPlaceholder('Enter customer name').inputValue();
    console.log(`[Name 300-char] field holds length: ${held.length}`);
    await submitAndReport(page, dialog, 'Name 300-char');
  });

  test('Email: leading/trailing whitespace around an otherwise-valid address is handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(10), email: `  field.boundary.three.${uniq(10)}.pad@yopmail.com  ` });
    const held = await dialog.getByPlaceholder('customer@email.com').inputValue();
    console.log(`[Email padded] field holds "${held}"`);
    await submitAndReport(page, dialog, 'Email padded whitespace');
  });
});

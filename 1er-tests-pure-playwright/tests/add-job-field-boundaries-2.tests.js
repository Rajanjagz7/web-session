const { describe, test, expect, expectVisible } = require('../runner');
const { INSTALLER_COMPANY } = require('../config');
const { login, openAddJobDrawer, fillJobForm, submitJob, submitAndReport, controlForLabel } = require('../helpers');

const RUN_ID = Date.now().toString().slice(-8);
const uniq = (n) => `${RUN_ID}${n}`;
const abn = (n) => uniq(n).padStart(11, '0').slice(-11);
const phone = (n) => `4${uniq(n).padStart(8, '0').slice(-8)}`;

const baseValid = (i) => ({
  customerName: `Field Boundary Two ${i}`,
  email: `field.boundary.two.${uniq(i)}@yopmail.com`,
  phone: phone(i),
  abnAcn: abn(i),
  addressSearch: '1 George Street Sydney',
  postcode: '2000',
  activityType: 'Heating & Cooling',
  buildingType: 'Residential Building',
  leadMethod: 'Phone',
  ownReference: `REF-${RUN_ID}-BND2-${i}`,
  installationDate: '20-10-2026',
  installer: INSTALLER_COMPANY,
  fillEquipment: true,
});

describe('Add Job - new boundary & negative values (round 2)', () => {
  test('Customer name: a single character is a valid-looking minimum boundary', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(1), customerName: 'A' });
    console.log(`  [Name 1-char] field holds: "${await dialog.getByPlaceholder('Enter customer name').inputValue()}"`);
    await submitAndReport(page, dialog, 'Name 1-char');
  });

  test('Customer name: purely numeric digits accepted as a "name"', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(2), customerName: '1234567890' });
    await submitAndReport(page, dialog, 'Name numeric-only');
  });

  test('Email: extremely long local-part (250+ chars)', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    const longLocal = 'x'.repeat(250);
    await fillJobForm(dialog, { ...baseValid(3), email: `${longLocal}@yopmail.com` });
    const held = await dialog.getByPlaceholder('customer@email.com').inputValue();
    console.log(`  [Email long] field holds length: ${held.length}`);
    await submitAndReport(page, dialog, 'Email long local-part');
  });

  test('Email: multiple @ symbols is rejected', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(4), email: 'a@b@c.com' });
    await submitJob(dialog);
    await page.waitForTimeout(1500);
    const stillOpen = await dialog.getByPlaceholder('Enter customer name').isVisible().catch(() => false);
    console.log(`  [Email multi-@] submission blocked: ${stillOpen}`);
    expect(stillOpen).toBe(true);
  });

  test('Email: missing top-level domain (no ".xxx") is handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(5), email: 'test@localhost' });
    await submitAndReport(page, dialog, 'Email no TLD');
  });

  test('Postcode: too long (5 digits) is handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(6), postcode: '20000' });
    console.log(`  [Postcode 5-digit] field holds: "${await dialog.getByPlaceholder('2000').inputValue()}"`);
    await submitAndReport(page, dialog, 'Postcode too-long');
  });

  test('Postcode: decimal value is handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(7), postcode: '2000.5' });
    console.log(`  [Postcode decimal] field holds: "${await dialog.getByPlaceholder('2000').inputValue()}"`);
    await submitAndReport(page, dialog, 'Postcode decimal');
  });

  test('ABN/ACN: embedded spaces are handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(8), abnAcn: undefined });
    const abnField = dialog.getByPlaceholder('12345678901');
    await abnField.fill('123 456 789 01');
    console.log(`  [ABN spaces] field holds: "${await abnField.inputValue()}"`);
    await submitAndReport(page, dialog, 'ABN embedded spaces');
  });

  test('ABN/ACN: exactly 10 digits (one short of the required 11) is rejected', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(9), abnAcn: '1234567890' });
    await submitJob(dialog);
    await page.waitForTimeout(1500);
    await expectVisible(dialog.getByText('ABN/ACN must be exactly 11 digits', { exact: true }));
  });

  test('Own reference: isolated extreme length (500 chars, no other confounding long fields)', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    const longRef = 'REF-' + 'Y'.repeat(500);
    await fillJobForm(dialog, { ...baseValid(10), ownReference: longRef });
    const held = await dialog.getByPlaceholder('REF-001').inputValue();
    console.log(`  [Own ref 500-char] field holds length: ${held.length}`);
    await submitAndReport(page, dialog, 'Own reference 500-char');
  });

  test('Phone: typing a "+61" country-code prefix into the national-number field is handled', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(11), phone: undefined });
    const phoneField = dialog.getByPlaceholder('412345678');
    await phoneField.click();
    await page.keyboard.type('+61412345678');
    console.log(`  [Phone with +61 prefix] field holds: "${await phoneField.inputValue()}"`);
    await submitAndReport(page, dialog, 'Phone with +61 prefix');
  });

  test('Site address: valid search term typed but no suggestion selected before submit', async ({ page }) => {
    await login(page);
    const dialog = await openAddJobDrawer(page);
    await fillJobForm(dialog, { ...baseValid(12), addressSearch: undefined });
    const addressControl = await controlForLabel(dialog, 'Site address');
    await addressControl.click();
    await page.keyboard.type('1 George Street Sydney');
    await page.waitForTimeout(1200);
    // Deliberately do NOT click a suggestion - close the dropdown via a
    // neutral click (Escape closes the whole drawer, a known gotcha).
    await dialog.getByText('Add Job', { exact: true }).first().click();
    await page.waitForTimeout(300);
    await submitJob(dialog);
    await page.waitForTimeout(1500);
    const stillOpen = await dialog.getByPlaceholder('Enter customer name').isVisible().catch(() => false);
    console.log(`  [Address typed-not-selected] submission blocked: ${stillOpen}`);
    expect(stillOpen).toBe(true);
  });
});

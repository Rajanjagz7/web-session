import { test, expect } from '@playwright/test';
import { login } from './helpers';
import { openAddInstallerPage, fillInstallerForm, submitInstaller, submitInstallerAndReport } from './installer-helpers';

const RUN_ID = Date.now().toString().slice(-8);
const uniq = (n: number) => `${RUN_ID}${n}`;

const validBase = (i: number) => ({
  companyName: `QA Sec ${uniq(i)}`,
  abn: uniq(i).padStart(11, '7').slice(-11),
  address: '1 George Street, Sydney NSW 2000',
  companyEmail: `qa.sec.${uniq(i)}@yopmail.com`,
  suburb: 'Sydney',
  firstName: 'QA',
  lastName: `SecTester${i}`,
  adminPhone: `4${uniq(i).padStart(8, '1').slice(-8)}`,
  adminEmail: `qa.sec.admin.${uniq(i)}@yopmail.com`,
});

test.describe('Add Installer - duplicate handling', () => {
  test('creating a second installer with the same ABN as an existing one is handled', async ({ page }) => {
    test.setTimeout(90_000);
    const sharedAbn = uniq(1).padStart(11, '3').slice(-11);

    await login(page);
    await openAddInstallerPage(page);
    await fillInstallerForm(page, { ...validBase(1), abn: sharedAbn });
    const first = await submitInstallerAndReport(page, 'Duplicate ABN - first create');
    console.log(`[Duplicate ABN] first installer created: ${first.created}`);

    await openAddInstallerPage(page);
    await fillInstallerForm(page, { ...validBase(2), abn: sharedAbn });
    const second = await submitInstallerAndReport(page, 'Duplicate ABN - second create (same ABN)');
    console.log(`[Duplicate ABN] second installer (same ABN, different company name) created: ${second.created}`);
  });

  test('creating a second installer with the exact same Company Name is handled', async ({ page }) => {
    test.setTimeout(90_000);
    const sharedName = `QA Duplicate Name ${RUN_ID}`;

    await login(page);
    await openAddInstallerPage(page);
    await fillInstallerForm(page, { ...validBase(3), companyName: sharedName });
    const first = await submitInstallerAndReport(page, 'Duplicate name - first create');
    console.log(`[Duplicate name] first installer created: ${first.created}`);

    await openAddInstallerPage(page);
    await fillInstallerForm(page, { ...validBase(4), companyName: sharedName });
    const second = await submitInstallerAndReport(page, 'Duplicate name - second create (same name, different ABN)');
    console.log(`[Duplicate name] second installer (same name, different ABN) created: ${second.created}`);
  });
});

test.describe('Add Installer - injection / security inputs', () => {
  test('Company Name with a <script> tag is stored as inert text, not executed', async ({ page }) => {
    test.setTimeout(60_000);
    await login(page);
    await openAddInstallerPage(page);
    const injected = `QA XSS ${uniq(5)} <script>window.__installerXss=1</script>`;
    await fillInstallerForm(page, { ...validBase(5), companyName: injected });
    const { created } = await submitInstallerAndReport(page, 'Company name script-tag');
    if (created) {
      await page.goto('/installer');
      await page.getByPlaceholder('Search Installer...').fill(`QA XSS ${uniq(5)}`);
      await page.waitForTimeout(1500);
      const executed = await page.evaluate(() => (window as any).__installerXss === 1);
      console.log(`[Company name script-tag] script executed on page: ${executed}`);
      expect(executed).toBe(false);
      console.log('[Company name script-tag] rendered list text:\n' + (await page.locator('main').innerText()));
    }
  });

  test('Registered Company Address with SQL-like input is handled safely', async ({ page }) => {
    test.setTimeout(60_000);
    await login(page);
    await openAddInstallerPage(page);
    await fillInstallerForm(page, { ...validBase(6), address: `' OR '1'='1` });
    await submitInstallerAndReport(page, 'Address SQL-like');
  });

  test('Primary Admin First/Last Name with HTML injection is handled safely', async ({ page }) => {
    test.setTimeout(60_000);
    await login(page);
    await openAddInstallerPage(page);
    await fillInstallerForm(page, {
      ...validBase(7),
      firstName: '<img src=x onerror=window.__installerXss2=1>',
      lastName: '"><b>bold</b>',
    });
    const { created } = await submitInstallerAndReport(page, 'Name HTML injection');
    if (created) {
      const executed = await page.evaluate(() => (window as any).__installerXss2 === 1);
      console.log(`[Name HTML injection] script executed on page: ${executed}`);
      expect(executed).toBe(false);
    }
  });
});

test.describe('Add Installer - phone / website edge cases', () => {
  test('Primary admin phone: typing a redundant "+61" prefix into the national-number field is handled', async ({ page }) => {
    await login(page);
    await openAddInstallerPage(page);
    await fillInstallerForm(page, { ...validBase(8), adminPhone: undefined });
    const phoneField = page.getByPlaceholder('Company Phone Number').last();
    await phoneField.click();
    await page.keyboard.type('+61412345678');
    const held = await phoneField.inputValue();
    console.log(`[Admin phone +61 prefix] field holds "${held}"`);
    await submitInstallerAndReport(page, 'Admin phone +61 prefix');
  });

  test('Primary admin phone: all zeros (9 digits) is handled', async ({ page }) => {
    await login(page);
    await openAddInstallerPage(page);
    await fillInstallerForm(page, { ...validBase(9), adminPhone: '000000000' });
    await submitInstallerAndReport(page, 'Admin phone all-zeros');
  });

  test('Website: a bare domain without protocol (example.com) is handled', async ({ page }) => {
    await login(page);
    await openAddInstallerPage(page);
    await fillInstallerForm(page, { ...validBase(10), website: 'example.com' });
    await submitInstallerAndReport(page, 'Website no-protocol');
  });

  test('Website: a javascript: URL is rejected or neutralised', async ({ page }) => {
    await login(page);
    await openAddInstallerPage(page);
    await fillInstallerForm(page, { ...validBase(11), website: 'javascript:alert(1)' });
    await submitInstallerAndReport(page, 'Website javascript-url');
  });
});

test.describe('Add Installer - save behaviour & persistence', () => {
  test('rapid double-click on Submit does not create two installer records', async ({ page }) => {
    test.setTimeout(60_000);
    await login(page);
    await openAddInstallerPage(page);
    const fields = validBase(12);
    await fillInstallerForm(page, fields);
    const submitBtn = page.getByRole('button', { name: 'Submit', exact: true });
    await Promise.all([submitBtn.click(), submitBtn.click({ force: true }).catch(() => {})]);
    await page.waitForTimeout(3000);

    await page.goto('/installer');
    await page.getByPlaceholder('Search Installer...').fill(fields.companyName);
    await page.waitForTimeout(1500);
    const rowCount = await page.locator('table tbody tr', { hasText: fields.companyName }).count();
    console.log(`[Double-submit] matching rows for "${fields.companyName}": ${rowCount}`);
    expect(rowCount).toBeLessThanOrEqual(1);
  });

  test('data persists correctly after save: reload, navigate away, and return', async ({ page }) => {
    test.setTimeout(90_000);
    await login(page);
    await openAddInstallerPage(page);
    const fields = validBase(13);
    await fillInstallerForm(page, fields);
    const { created } = await submitInstallerAndReport(page, 'Persistence create');
    expect(created).toBe(true);

    await page.goto('/installer');
    await page.getByPlaceholder('Search Installer...').fill(fields.companyName);
    await page.waitForTimeout(1500);
    await expect(page.getByText(fields.companyName, { exact: false })).toBeVisible();

    // Navigate away then return, and reload, to confirm it's not a stale/session-only artifact.
    await page.goto('/dashboard');
    await page.goto('/installer');
    await page.reload();
    await page.getByPlaceholder('Search Installer...').fill(fields.companyName);
    await page.waitForTimeout(1500);
    await expect(page.getByText(fields.companyName, { exact: false })).toBeVisible();
    console.log('[Persistence] company name still visible after reload/navigate-away/return.');
  });
});

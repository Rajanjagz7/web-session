const { chromium } = require('playwright');

async function controlForLabel(page, labelText) {
  const label = page.getByText(labelText, { exact: false }).first();
  const fieldWrapper = label.locator('xpath=ancestor::*[.//*[contains(@class,"select__control")]][1]');
  return fieldWrapper.locator('.select__control').first();
}
async function selectOption(page, labelText, optionName) {
  const control = await controlForLabel(page, labelText);
  await control.scrollIntoViewIfNeeded();
  await control.click();
  await page.getByRole('option', { name: optionName, exact: true }).click();
}
async function fieldExists(page, labelText) {
  return (await page.getByText(labelText, { exact: false }).count()) > 0;
}
let variedOptionCounter = 0;
async function selectVariedOpenOption(page) {
  const options = page.getByRole('option');
  const count = await options.count();
  const index = count > 0 ? variedOptionCounter % count : 0;
  variedOptionCounter++;
  await options.nth(index).click();
}

const RUN_ID = Date.now().toString().slice(-8);
const uniq = (n) => `${RUN_ID}${n}`;
const abn = (n) => uniq(n).padStart(11, '0').slice(-11);
const phone = (n) => `4${uniq(n).padStart(8, '0').slice(-8)}`;

const JOBS = [
  { name: 'Harper Nguyen', address: '1 George Street Sydney', postcode: '2000', activity: 'Heating & Cooling', building: 'Residential Building', lead: 'Phone' },
  { name: 'Ethan Kelly', address: '50 Elizabeth Street Artarmon', postcode: '2064', activity: 'Hot Water Heat Pump', building: 'Residential Building', newSystem: 'Heat pump', lead: 'Website' },
  { name: 'Isla Marshall', address: '123 Walker Street North Sydney', postcode: '2060', activity: 'Heating & Cooling', building: 'Small Business Site', lead: 'Referral' },
  { name: 'Oliver Chen', address: '66 Pacific Highway St Leonards', postcode: '2065', activity: 'Hot Water Heat Pump', building: 'Small Business Site', lead: 'Email' },
  { name: 'Grace Sinclair', address: '789 New Canterbury Road Dulwich Hill', postcode: '2203', activity: 'Heating & Cooling', building: 'Residential Building', lead: 'Phone' },
  { name: 'Mason Reid', address: '898 Punchbowl Road Punchbowl', postcode: '2196', activity: 'Hot Water Heat Pump', building: 'Residential Building', newSystem: 'Solar (electric boosted)', lead: 'Referral' },
  { name: 'Zara Coleman', address: '1 George Street Sydney', postcode: '2000', activity: 'Heating & Cooling', building: 'Small Business Site', lead: 'Website' },
  { name: 'Liam Foster', address: '50 Elizabeth Street Artarmon', postcode: '2064', activity: 'Hot Water Heat Pump', building: 'Residential Building', newSystem: 'Heat pump', lead: 'Phone' },
  { name: 'Ruby Anderson', address: '123 Walker Street North Sydney', postcode: '2060', activity: 'Heating & Cooling', building: 'Residential Building', lead: 'Email' },
  { name: 'Henry Wallace', address: '66 Pacific Highway St Leonards', postcode: '2065', activity: 'Hot Water Heat Pump', building: 'Small Business Site', lead: 'Referral' },
  { name: 'Chloe Bennett', address: '789 New Canterbury Road Dulwich Hill', postcode: '2203', activity: 'Heating & Cooling', building: 'Residential Building', lead: 'Phone' },
  { name: 'Jack Mitchell', address: '898 Punchbowl Road Punchbowl', postcode: '2196', activity: 'Hot Water Heat Pump', building: 'Residential Building', newSystem: 'Heat pump', lead: 'Website' },
];

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 300 });
  const context = await browser.newContext({ viewport: null, args: ['--start-maximized'] });
  const page = await context.newPage();

  console.log('=== STEP 1: Log in as Master Admin ===');
  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.getByPlaceholder(/email/i).fill('admin@rebatem8nsw.com.au');
  await page.getByPlaceholder(/password/i).fill('admin@123');
  await page.getByRole('button', { name: /log ?in|sign ?in/i }).click();
  await page.waitForTimeout(2000);

  console.log('=== STEP 2: Go to Installer screen, search "Boundary Test Co 237440654" ===');
  await page.goto('https://nswdev.rebatem8.com.au/installer');
  await page.waitForTimeout(2000);
  await page.getByPlaceholder(/search/i).first().fill('Boundary Test Co 237440654');
  await page.waitForTimeout(2000);

  console.log('=== STEP 3: Open the row action menu and click "Installer Admin" (impersonate) ===');
  const row = page.locator('table tbody tr').first();
  await row.locator('td').first().locator('svg, button, img').first().click();
  await page.waitForTimeout(800);
  await page.getByText('Installer Admin', { exact: true }).first().click();
  await page.waitForTimeout(2000);
  console.log('Now impersonating as Installer Admin. URL:', page.url());

  console.log('=== STEP 4: Click "Enter New Job" from the dashboard ===');
  await page.getByText('Enter New Job', { exact: true }).first().click();
  await page.waitForTimeout(2500);
  console.log('Now on company-scoped Jobs screen. URL:', page.url());

  const created = [];
  const failed = [];

  for (let i = 0; i < JOBS.length; i++) {
    const j = JOBS[i];
    console.log(`\n=== Job ${i + 1}/${JOBS.length}: ${j.name} (${j.activity}) ===`);
    try {
      await page.getByRole('button', { name: /add job/i }).click();
      const dialog = page.getByRole('dialog');
      await dialog.getByPlaceholder('Enter customer name').waitFor({ state: 'visible', timeout: 15000 });

      await dialog.getByPlaceholder('Enter customer name').fill(j.name);
      await dialog.getByPlaceholder('customer@email.com').fill(`${j.name.toLowerCase().replace(/\s+/g, '.')}.${uniq(i)}@yopmail.com`);
      const phoneField = dialog.getByPlaceholder('412345678');
      await phoneField.click();
      await page.keyboard.type(phone(i));
      await dialog.getByPlaceholder('12345678901').fill(abn(i));

      const addressControl = await controlForLabel(dialog, 'Site address');
      await addressControl.click();
      await page.keyboard.type(j.address);
      await page.waitForTimeout(1200);
      await page.getByRole('option').first().click();
      await dialog.getByPlaceholder('2000').fill(j.postcode);

      await selectOption(dialog, 'Activity type', j.activity);
      await selectOption(dialog, 'Building type', j.building);
      if (j.newSystem && (await fieldExists(dialog, 'New system'))) {
        await selectOption(dialog, 'New system', j.newSystem);
      }
      await selectOption(dialog, 'Method of lead generation', j.lead);
      await dialog.getByPlaceholder('REF-001').fill(`REF-BND-${RUN_ID}-${i}`);
      const dateField = dialog.getByPlaceholder('DD-MM-YYYY');
      await dateField.click();
      await page.keyboard.type('15-10-2026');

      // Installer (company) is already pre-selected as "Boundary Test Co
      // 237440654" via the impersonated Enter New Job flow - just confirm
      // the Equipment block is present (it appears once an installer is set).
      await page.waitForTimeout(500);
      await selectOption(dialog, 'Original equipment', 'No existing system (new installation)');
      await page.waitForTimeout(500);
      if (await fieldExists(dialog, 'Brand')) {
        const brandControl = await controlForLabel(dialog, 'Brand');
        await brandControl.click();
        await page.waitForTimeout(300);
        await selectVariedOpenOption(page);
        await page.waitForTimeout(500);
      }
      const modelControl = await controlForLabel(dialog, 'Model');
      await modelControl.click();
      await page.waitForTimeout(300);
      await selectVariedOpenOption(page);
      await page.waitForTimeout(300);

      await dialog.getByRole('button', { name: /send engagement letter/i }).click();
      await dialog.getByPlaceholder('Enter customer name').waitFor({ state: 'hidden', timeout: 15000 });
      await page.waitForTimeout(1200);

      console.log(`[${i + 1}/${JOBS.length}] Created: ${j.name} / ${j.activity} / ${j.building} / ${j.lead}`);
      created.push(j.name);
    } catch (err) {
      console.log(`[${i + 1}/${JOBS.length}] FAILED (${j.name}): ${err.message}`);
      failed.push(j.name);
      // Try to recover: close any stray dialog before the next iteration.
      await page.keyboard.press('Escape').catch(() => {});
      await page.waitForTimeout(1000);
    }
  }

  console.log(`\nDONE. Created: ${created.length}, Failed: ${failed.length}`);
  console.log('Leaving browser open 15s to inspect the final Jobs list.');
  await page.waitForTimeout(15000);
  await browser.close();
})();

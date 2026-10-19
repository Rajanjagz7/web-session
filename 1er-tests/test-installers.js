const { chromium } = require('playwright');

async function testInstallersAndModal() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  // Check /installer to see companies
  console.log('--- Checking /installer ---');
  await page.goto('https://nswdev.rebatem8.com.au/installer', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);
  const bodyText = await page.locator('body').innerText();
  console.log('Installers found snippet:');
  const lines = bodyText.split('\n').filter(l => l.trim().length > 0);
  console.log(lines.slice(0, 30).join('\n'));

  // Go to /jobs and click Add Job
  console.log('--- Checking Add Job Interactions ---');
  await page.goto('https://nswdev.rebatem8.com.au/jobs', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);
  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // Let's find all inputs and select containers in the Add Job modal
  const modal = page.locator('.dialog, div[role="dialog"], .drawer, .modal, form').first();
  console.log('Modal visible:', await modal.isVisible());

  // Let's list all react-select containers
  const reactSelects = await modal.locator('[id^="react-select-"]').all();
  console.log('react-select elements count:', reactSelects.length);
  for (let i = 0; i < Math.min(reactSelects.length, 10); i++) {
    const id = await reactSelects[i].getAttribute('id');
    console.log(`React select ${i}: id=${id}`);
  }

  // Click on the first select (Activity Type)
  const activitySelect = modal.locator('.select, [class*="-control"]').first();
  await activitySelect.click();
  await page.waitForTimeout(500);
  console.log('Selecting "Heating & Cooling"...');
  const opt = page.locator('[class*="-option"]').filter({ hasText: 'Heating & Cooling' }).first();
  if (await opt.isVisible()) {
    await opt.click();
    console.log('Clicked "Heating & Cooling"!');
  }
  await page.waitForTimeout(1000);

  // Now let's see what happens to the second select (Method of Lead Generation)
  const leadSelect = modal.locator('.select, [class*="-control"]').nth(1);
  await leadSelect.click();
  await page.waitForTimeout(500);
  const leadOptions = await page.locator('[class*="-option"]').allInnerTexts();
  console.log('Lead Generation Options:', leadOptions);
  if (leadOptions.length > 0) {
    await page.locator('[class*="-option"]').first().click();
  }
  await page.waitForTimeout(1000);

  // Third select: Building Type
  const buildingSelect = modal.locator('.select, [class*="-control"]').nth(2);
  await buildingSelect.click();
  await page.waitForTimeout(500);
  const buildingOptions = await page.locator('[class*="-option"]').allInnerTexts();
  console.log('Building Type Options:', buildingOptions);
  if (buildingOptions.length > 0) {
    await page.locator('[class*="-option"]').first().click();
  }
  await page.waitForTimeout(1000);

  // Fourth select: Installer (Company)
  const companySelect = modal.locator('.select, [class*="-control"]').nth(3);
  await companySelect.click();
  await page.waitForTimeout(500);
  const companyOptions = await page.locator('[class*="-option"]').allInnerTexts();
  console.log('Company Options:', companyOptions);

  await browser.close();
}

testInstallersAndModal().catch(console.error);

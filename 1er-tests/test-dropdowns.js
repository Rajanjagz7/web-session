const { chromium } = require('playwright');

async function testDropdowns() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // 1. Activity Type
  const input5 = page.locator('#react-select-5-input');
  await input5.focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(500);
  console.log('Selected Activity Type');

  // 2. Lead Gen
  const input6 = page.locator('#react-select-6-input');
  await input6.focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(500);
  console.log('Selected Lead Gen');

  // 3. Building Type
  const input7 = page.locator('#react-select-7-input');
  await input7.focus();
  await page.keyboard.press('ArrowDown');
  await page.waitForTimeout(400);
  const buildingOpts = await page.locator('[class*="-option"]').allInnerTexts();
  console.log('Actual Building Types:', buildingOpts);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(500);

  // 4. Installer Company
  const input8 = page.locator('#react-select-8-input');
  await input8.focus();
  await input8.fill('rajan');
  await page.waitForTimeout(800);
  const companyOpts = await page.locator('[class*="-option"]').allInnerTexts();
  console.log('Company options matching "rajan":', companyOpts);

  // If no exact match, let's see all companies by clearing and pressing ArrowDown
  if (companyOpts.length === 0) {
    await input8.fill('');
    await page.keyboard.press('ArrowDown');
    await page.waitForTimeout(400);
    const allCompanies = await page.locator('[class*="-option"]').allInnerTexts();
    console.log('First 15 companies in list:', allCompanies.slice(0, 15));
  }

  await browser.close();
}

testDropdowns().catch(console.error);

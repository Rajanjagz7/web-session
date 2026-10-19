const { chromium } = require('playwright');

async function checkBusinessFields() {
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
  await page.locator('#react-select-5-input').focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);

  // 2. Lead Gen
  await page.locator('#react-select-6-input').focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);

  // 3. Building Type: Small Business Site
  const bldgSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Building Type' }).first();
  await bldgSelect.click();
  await page.locator('[class*="-option"]').filter({ hasText: 'Small Business Site (less than' }).first().click();
  await page.waitForTimeout(500);

  console.log('--- Inputs visible for Small Business Site ---');
  const inputs = await page.locator('form input:visible').all();
  for (const inp of inputs) {
    console.log(await inp.evaluate(el => ({ name: el.name, placeholder: el.placeholder, id: el.id })));
  }

  console.log('--- Labels for Small Business Site ---');
  console.log(await page.locator('form label').allInnerTexts());

  await browser.close();
}

checkBusinessFields().catch(console.error);

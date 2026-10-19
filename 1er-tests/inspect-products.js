const { chromium } = require('playwright');

async function inspectProductFields() {
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

  // 3. Building Type
  await page.locator('#react-select-7-input').focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);

  // 4. Installer Company: Rajan
  await page.locator('#react-select-8-input').focus();
  await page.locator('#react-select-8-input').fill('Rajan');
  await page.waitForTimeout(500);
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(500);

  // Now dump all labels and select inputs in the form
  const labels = await page.locator('form label').allInnerTexts();
  console.log('All labels after selecting company:', labels);

  // Find all select placeholders or controls
  const controls = await page.locator('.select__placeholder, [class*="-placeholder"]').allInnerTexts();
  console.log('Placeholders currently visible:', controls);

  // Let's test selecting "Name of Installer Attended Site Inspection"
  // Let's find its input
  const installerPerson = page.locator('.select, [class*="-control"]').filter({ hasText: /installer|attended|inspection/i });
  console.log('Installer person controls:', await installerPerson.count());

  // Also look at Original Equipment, Brand, Model selects
  const originalEquip = page.locator('.select, [class*="-control"]').filter({ hasText: /original equipment|equipment/i });
  console.log('Original equip controls:', await originalEquip.count());

  await browser.close();
}

inspectProductFields().catch(console.error);

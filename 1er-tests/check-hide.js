const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://nswdev.rebatem8.com.au/sign-in', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);

  const hideBtn = page.locator('button:has-text("Hide")');
  console.log('Clicking Hide button...');
  await hideBtn.click();
  await page.waitForTimeout(1000);

  console.log('After clicking Hide:');
  console.log(await page.locator('body').innerText());

  const inputs = await page.locator('input').all();
  for (const inp of inputs) {
    console.log(await inp.evaluate(el => ({
      name: el.name,
      placeholder: el.placeholder,
      type: el.type,
      visible: el.offsetParent !== null
    })));
  }

  await browser.close();
}

main().catch(console.error);

const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const text = await page.evaluate(async () => {
    const res = await fetch('/assets/index-BTGuwZAU.js');
    return await res.text();
  });

  const idx = text.indexOf('SITE_ASSESSOR_DECLARATION');
  if (idx !== -1) {
    console.log('SITE_ASSESSOR_DECLARATION snippet:');
    console.log(text.substring(Math.max(0, idx - 200), Math.min(text.length, idx + 400)));
  }

  await browser.close();
})();

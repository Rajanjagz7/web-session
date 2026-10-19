const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://nswdev.rebatem8.com.au/log-in');

  const mainText = await page.evaluate(async () => {
    const res = await fetch('/assets/index-BTGuwZAU.js');
    return await res.text();
  });

  let idx = 0;
  let count = 0;
  while ((idx = mainText.indexOf('nomination_signed', idx)) !== -1) {
    count++;
    console.log(`nomination_signed Match ${count}:`);
    console.log(mainText.substring(Math.max(0, idx - 200), Math.min(mainText.length, idx + 400)));
    console.log('===================================');
    idx += 'nomination_signed'.length;
  }

  await browser.close();
})();

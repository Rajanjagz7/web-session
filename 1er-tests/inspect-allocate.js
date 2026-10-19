const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const text = await page.evaluate(async () => {
    const res = await fetch('/assets/JobView-DSnPHTOu.js');
    return await res.text();
  });

  const idx = text.indexOf('title:"Allocate"');
  if (idx !== -1) {
    console.log('Context before title:"Allocate":');
    console.log(text.substring(Math.max(0, idx - 1000), idx));
  }

  await browser.close();
})();

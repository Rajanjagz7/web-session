const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const res = await page.evaluate(async () => {
    const views = await (await fetch('/assets/Views-Bzmj2kUm.js')).text();
    const idx = views.indexOf('JobView');
    return {
      hasJobView: idx !== -1,
      snippet: idx !== -1 ? views.substring(Math.max(0, idx - 200), Math.min(views.length, idx + 200)) : null
    };
  });

  console.log('JobView in Views:', res);
  await browser.close();
})();

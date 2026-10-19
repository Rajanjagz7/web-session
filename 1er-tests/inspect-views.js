const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  const viewsText = await page.evaluate(async () => {
    const res = await fetch('/assets/Views-Bzmj2kUm.js');
    return await res.text();
  });

  const routes = viewsText.match(/path:\s*["'][^"']+["']/g) || [];
  console.log('Routes in Views:', [...new Set(routes)]);

  const innerChunks = viewsText.match(/assets\/[a-zA-Z0-9_\-]+\.js/g) || [];
  console.log('Inner chunks in Views:', [...new Set(innerChunks)]);

  await browser.close();
})();

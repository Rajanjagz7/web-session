const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const text = await page.evaluate(async () => {
    const res = await fetch('/assets/JobView-DSnPHTOu.js');
    return await res.text();
  });

  const apiCalls = text.match(/\/api\/v1\/[a-zA-Z0-9_\-\/]+/g) || [];
  console.log('API Calls in JobView:', [...new Set(apiCalls)]);

  const storageCalls = text.match(/[a-zA-Z0-9_\-\/]*(?:storage|upload|presigned)[a-zA-Z0-9_\-\/]*/gi) || [];
  console.log('Storage matches:', [...new Set(storageCalls)]);

  await browser.close();
})();

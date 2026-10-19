const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const jobView = await page.evaluate(async () => {
    const res = await fetch('/assets/JobView-DSnPHTOu.js');
    return await res.text();
  });

  const fieldNames = jobView.match(/fieldName:\s*["'][^"']+["']/g) || [];
  console.log('All fieldNames in JobView:', [...new Set(fieldNames)]);

  // Also let's find all "Upload ..." strings
  const uploads = jobView.match(/"Upload [^"]+"/g) || [];
  console.log('All Upload buttons/labels:', [...new Set(uploads)]);

  // Let's find what stages/tabs exist in JobView
  const tabs = jobView.match(/label:\s*["'][^"']+["']/g) || [];
  console.log('Labels in JobView:', [...new Set(tabs)].slice(0, 30));

  await browser.close();
})();

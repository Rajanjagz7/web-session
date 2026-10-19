const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const text = await page.evaluate(async () => {
    const res = await fetch('/assets/JobView-DSnPHTOu.js');
    return await res.text();
  });

  // Search for the accordion content in photos tab
  const existingIdx = text.indexOf('Existing Units');
  if (existingIdx !== -1) {
    console.log('Snippet around Existing Units:');
    console.log(text.substring(Math.max(0, existingIdx - 200), Math.min(text.length, existingIdx + 500)));
  }

  const noPhotosIdx = text.indexOf('No Photos Available');
  if (noPhotosIdx !== -1) {
    console.log('Snippet around No Photos Available:');
    console.log(text.substring(Math.max(0, noPhotosIdx - 200), Math.min(text.length, noPhotosIdx + 500)));
  }

  await browser.close();
})();

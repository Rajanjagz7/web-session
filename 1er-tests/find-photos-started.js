const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://nswdev.rebatem8.com.au/log-in');

  const mainBundle = await page.evaluate(async () => {
    const res = await fetch('/assets/index-BTGuwZAU.js');
    return await res.text();
  });
  console.log('Main bundle length:', mainBundle.length);

  // Search for photos_started occurrences
  let idx = 0;
  let count = 0;
  while ((idx = mainBundle.indexOf('photos_started', idx)) !== -1) {
    count++;
    console.log(`Match ${count}:`);
    console.log(mainBundle.substring(Math.max(0, idx - 150), Math.min(mainBundle.length, idx + 250)));
    console.log('-----------------------------------');
    idx += 'photos_started'.length;
  }

  // Also search for "Photos Started"
  idx = 0;
  while ((idx = mainBundle.indexOf('Photos Started', idx)) !== -1) {
    console.log(`Photos Started Match:`);
    console.log(mainBundle.substring(Math.max(0, idx - 150), Math.min(mainBundle.length, idx + 250)));
    console.log('===================================');
    idx += 'Photos Started'.length;
  }

  await browser.close();
})();

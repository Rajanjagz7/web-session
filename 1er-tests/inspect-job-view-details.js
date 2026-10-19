const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const jobView = await page.evaluate(async () => {
    const res = await fetch('/assets/JobView-DSnPHTOu.js');
    return await res.text();
  });

  const idx = jobView.indexOf('job-view-upload-er');
  if (idx !== -1) {
    console.log('Context around job-view-upload-er:');
    console.log(jobView.substring(Math.max(0, idx - 200), Math.min(jobView.length, idx + 400)));
  }

  // Also let's find other occurrences
  let nextIdx = jobView.indexOf('job-view-upload-er', idx + 1);
  if (nextIdx !== -1) {
    console.log('\nSecond context:');
    console.log(jobView.substring(Math.max(0, nextIdx - 200), Math.min(jobView.length, nextIdx + 400)));
  }

  await browser.close();
})();

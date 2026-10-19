const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const jobView = await page.evaluate(async () => {
    const res = await fetch('/assets/JobView-DSnPHTOu.js');
    return await res.text();
  });

  const idx = jobView.indexOf('"Upload to Job"');
  if (idx !== -1) {
    console.log('Context around "Upload to Job":');
    console.log(jobView.substring(Math.max(0, idx - 400), Math.min(jobView.length, idx + 400)));
  }

  const idxPhoto = jobView.indexOf('"Photo Set"');
  if (idxPhoto !== -1) {
    console.log('Context around "Photo Set":');
    console.log(jobView.substring(Math.max(0, idxPhoto - 300), Math.min(jobView.length, idxPhoto + 300)));
  }

  await browser.close();
})();

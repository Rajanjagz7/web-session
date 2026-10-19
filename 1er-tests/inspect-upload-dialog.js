const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const uploadDialog = await page.evaluate(async () => {
    const res = await fetch('/assets/UploadDialogVeu-X29uvpBp.js');
    return await res.text();
  });
  console.log('UploadDialogVeu length:', uploadDialog.length);
  // Find interesting words
  console.log('Matches in UploadDialog:', uploadDialog.match(/[a-zA-Z0-9_\-\/]+(?:upload|photo|document|file)[a-zA-Z0-9_\-\/]*/gi)?.slice(0, 20));

  const jobView = await page.evaluate(async () => {
    const res = await fetch('/assets/JobView-DSnPHTOu.js');
    return await res.text();
  });
  console.log('JobView length:', jobView.length);
  console.log('Matches in JobView:', jobView.match(/[a-zA-Z0-9_\-\/]+(?:upload|photo|document|file|bill)[a-zA-Z0-9_\-\/]*/gi)?.slice(0, 20));

  await browser.close();
})();

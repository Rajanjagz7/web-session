const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const res = await page.evaluate(async () => {
    const views = await (await fetch('/assets/Views-Bzmj2kUm.js')).text();
    const matches = [];
    let pos = 0;
    while ((pos = views.indexOf('UploadDialogVeu', pos)) !== -1) {
      matches.push(views.substring(Math.max(0, pos - 200), Math.min(views.length, pos + 200)));
      pos += 15;
    }
    return matches;
  });

  console.log('UploadDialogVeu in Views:', res);

  // Also check index bundle
  const resIndex = await page.evaluate(async () => {
    const index = await (await fetch('/assets/index-BTGuwZAU.js')).text();
    const matches = [];
    let pos = 0;
    while ((pos = index.indexOf('UploadDialogVeu', pos)) !== -1) {
      matches.push(index.substring(Math.max(0, pos - 200), Math.min(index.length, pos + 200)));
      pos += 15;
    }
    return matches;
  });
  console.log('UploadDialogVeu in Index:', resIndex);

  await browser.close();
})();

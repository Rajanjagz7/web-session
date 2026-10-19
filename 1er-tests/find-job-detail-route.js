const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const res = await page.evaluate(async () => {
    const views = await (await fetch('/assets/Views-Bzmj2kUm.js')).text();
    const idx = views.indexOf('JOB_DETAIL');
    return views.substring(Math.max(0, idx - 100), Math.min(views.length, idx + 100));
  });

  console.log('JOB_DETAIL snippet:', res);

  // Let's also find where JOB_DETAIL constant is defined
  const resConst = await page.evaluate(async () => {
    const index = await (await fetch('/assets/index-BTGuwZAU.js')).text();
    const matches = index.match(/JOB_DETAIL\s*:\s*["'][^"']+["']/g) || [];
    const lower = index.match(/\/jobs\/[a-zA-Z0-9_\-\:\/]+/g) || [];
    return { matches, lower: [...new Set(lower)] };
  });

  console.log('JOB_DETAIL constants:', resConst);
  await browser.close();
})();

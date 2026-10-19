const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const allRoutes = await page.evaluate(async () => {
    const scripts = ['/assets/index-BTGuwZAU.js', '/assets/Views-Bzmj2kUm.js'];
    const paths = [];
    for (const s of scripts) {
      const txt = await (await fetch(s)).text();
      const m = txt.match(/path:\s*["'][^"']+["']/g) || [];
      paths.push(...m);
    }
    return [...new Set(paths)];
  });

  console.log('All routes found:');
  allRoutes.forEach(r => console.log(' ', r));

  await browser.close();
})();

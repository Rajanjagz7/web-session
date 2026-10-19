const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const res = await page.evaluate(async () => {
    const views = await (await fetch('/assets/Views-Bzmj2kUm.js')).text();
    const matches = [];
    let pos = 0;
    while ((pos = views.indexOf('JobView-DSnPHTOu.js', pos)) !== -1) {
      matches.push(views.substring(Math.max(0, pos - 300), Math.min(views.length, pos + 200)));
      pos += 20;
    }
    return matches;
  });

  console.log('Matches:', res);
  await browser.close();
})();

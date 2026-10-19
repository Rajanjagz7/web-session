const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const text = await page.evaluate(async () => {
    const res = await fetch('/assets/index-BSco-goU.js');
    return await res.text();
  });

  console.log('index-BSco-goU.js length:', text.length);
  // Find route or title or modal name
  const titles = text.match(/title:\s*["'][^"']+["']/g) || [];
  console.log('Titles:', [...new Set(titles)]);
  const buttons = text.match(/>[A-Za-z0-9 ]+<\/button>/g) || [];
  console.log('Buttons sample:', [...new Set(buttons)].slice(0, 15));

  const uploads = text.match(/[a-zA-Z0-9_\-\/]+(?:Upload|upload|photo|Photo)[a-zA-Z0-9_\-\/]*/g) || [];
  console.log('Upload keywords in index-BSco-goU.js:', [...new Set(uploads)].slice(0, 20));

  await browser.close();
})();

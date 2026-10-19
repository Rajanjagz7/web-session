const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://yopmail.com/?rajanj');
  await page.waitForTimeout(4000);

  const ifinbox = page.frameLocator('#ifinbox');
  const mailCount = await ifinbox.locator('.m').count();
  console.log('Mails found for rajanj:', mailCount);

  for (let i = 0; i < mailCount; i++) {
    await ifinbox.locator('.m').nth(i).click();
    await page.waitForTimeout(2000);
    const ifmail = page.frameLocator('#ifmail');
    const mailText = await ifmail.locator('#mail').innerText();
    const links = await ifmail.locator('a').evaluateAll(as => as.map(a => a.href));
    console.log(`--- Mail ${i} ---`);
    console.log(mailText.substring(0, 200));
    console.log('Links:', links);
    for (const l of links) {
      if (l.includes('token=')) {
        const token = l.split('token=')[1];
        const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64').toString());
        console.log('Decoded token:', payload);
      }
    }
  }

  await browser.close();
})();

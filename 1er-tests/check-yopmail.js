const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  console.log('Navigating to YOPmail for rajanj...');
  await page.goto('https://yopmail.com/en/wm');
  
  await page.goto('https://yopmail.com/?rajanj');
  await page.waitForTimeout(4000);

  // Take screenshot of inbox
  await page.screenshot({ path: 'yopmail-rajanj.png' });

  // Look for iframes: #ifinbox, #ifmail
  const ifinbox = page.frameLocator('#ifinbox');
  const mailCount = await ifinbox.locator('.m').count();
  console.log('Mails found for rajanj:', mailCount);

  for (let i = 0; i < mailCount; i++) {
    const text = await ifinbox.locator('.m').nth(i).innerText();
    console.log(`Mail ${i}:`, text.replace(/\n/g, ' | '));
  }

  if (mailCount > 0) {
    await ifinbox.locator('.m').first().click();
    await page.waitForTimeout(2000);

    const ifmail = page.frameLocator('#ifmail');
    const mailBody = await ifmail.locator('#mail').innerText();
    console.log('First Mail Body:');
    console.log(mailBody);

    // Get all links in mail
    const links = await ifmail.locator('a').evaluateAll(as => as.map(a => a.href));
    console.log('Links in email:', links);
  }

  await browser.close();
})();

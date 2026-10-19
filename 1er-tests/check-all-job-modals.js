const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const jobIds = ['M8N000377', 'M8N000378', 'M8N000379', 'M8N000380'];

  for (const jobId of jobIds) {
    console.log(`\n=== Inspecting Job ${jobId} ===`);
    const searchInput = page.getByPlaceholder('Search Jobs...');
    await searchInput.fill(jobId);
    await page.waitForTimeout(1500);

    const row = page.locator('tr').filter({ hasText: jobId }).first();
    if (await row.count() === 0) {
      console.log(`Row for ${jobId} not found`);
      continue;
    }

    const eyeIcon = row.locator('.cursor-pointer').first();
    await eyeIcon.click();
    await page.waitForTimeout(2000);

    await page.screenshot({ path: `job-modal-${jobId}.png` });
    console.log(`Saved job-modal-${jobId}.png`);

    // Check for file inputs
    const fileInputs = await page.locator('input[type="file"]').all();
    console.log(`Job ${jobId} has ${fileInputs.length} file inputs`);
    for (let i = 0; i < fileInputs.length; i++) {
      const accept = await fileInputs[i].getAttribute('accept');
      const name = await fileInputs[i].getAttribute('name');
      const id = await fileInputs[i].getAttribute('id');
      console.log(`File input ${i}: name=${name} id=${id} accept=${accept}`);
    }

    // Check texts and buttons inside drawer/modal
    const drawerText = await page.locator('[class*="drawer"], [role="dialog"], body').first().innerText();
    const hasEnergyBill = drawerText.includes('energy bill') || drawerText.includes('Energy bill');
    const hasPhoto = drawerText.includes('photo') || drawerText.includes('Photo') || drawerText.includes('Image') || drawerText.includes('image');
    console.log(`Job ${jobId}: hasEnergyBill=${hasEnergyBill}, hasPhoto=${hasPhoto}`);

    // Close drawer / modal
    const closeBtn = page.locator('button:has-text("Back"), button:has-text("×"), svg.close, [class*="close"]').first();
    const closeX = page.locator('div:has-text("Job - ")').locator('button, svg, span').last();
    // Try pressing Escape or clicking outside or Back
    const backBtn = page.getByRole('button', { name: 'Back' });
    if (await backBtn.isVisible()) {
      await backBtn.click();
    } else {
      await page.keyboard.press('Escape');
    }
    await page.waitForTimeout(1000);
  }

  await browser.close();
})();

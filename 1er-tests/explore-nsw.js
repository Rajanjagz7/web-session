// Exploratory script: opens NSW RebateM8 Add Job dialog and dumps the
// installation-date calendar widget's HTML so we can find reliable selectors.
const { chromium } = require('playwright');

const BASE_URL = 'https://nswdev.rebatem8.com.au';

async function main() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  await page.goto(`${BASE_URL}/jobs`);
  await page.waitForTimeout(2000);
  console.log('Current URL after nav:', page.url());

  // If redirected to a login page, log in.
  if (page.url().includes('sign-in') || page.url().includes('log-in')) {
    console.log('Login required, attempting with known credentials...');
    const emailBox = page.getByPlaceholder(/email/i);
    if (await emailBox.isVisible().catch(() => false)) {
      await emailBox.fill('johns@softwareco.com');
      await page.getByPlaceholder(/password/i).fill('admin@123');
      await page.getByRole('button', { name: /log in/i }).click();
      await page.waitForTimeout(2000);
      console.log('URL after login attempt:', page.url());
    } else {
      console.log('Login form shape unexpected, dumping body HTML.');
      console.log(await page.content());
      await browser.close();
      return;
    }
  }

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1000);

  // Click the installation date field.
  const dateInput = page.getByPlaceholder('DD-MM-YYYY');
  await dateInput.click();
  await page.waitForTimeout(500);

  // Dump the calendar popup HTML.
  const popup = await page.locator('[role="dialog"]').last();
  console.log('--- Calendar popup HTML ---');
  console.log(await popup.innerHTML());

  await page.waitForTimeout(60000); // keep open for manual inspection
  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

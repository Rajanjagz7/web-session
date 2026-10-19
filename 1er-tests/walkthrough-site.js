const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

async function exploreSite() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // 1. Login
  console.log('--- 1. Logging in ---');
  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');
  console.log('Logged in. At:', page.url());
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01-jobs-list.png') });

  // 2. Discover all sidebar menu links
  console.log('--- 2. Discovering Navigation Menu ---');
  const navLinks = await page.locator('nav a, aside a, .side-nav a').all();
  const routes = [];
  for (const link of navLinks) {
    const text = (await link.innerText()).trim();
    const href = await link.getAttribute('href');
    if (href && !href.startsWith('javascript') && !href.startsWith('#')) {
      routes.push({ text: text.replace(/\n/g, ' '), href });
    }
  }
  console.log('Discovered Routes:', JSON.stringify(routes, null, 2));

  // 3. Visit main pages
  const uniqueHrefs = [...new Set(routes.map(r => r.href))];
  const pagesSummary = [];
  for (const href of uniqueHrefs) {
    const targetUrl = href.startsWith('http') ? href : `https://nswdev.rebatem8.com.au${href}`;
    console.log(`Navigating to: ${targetUrl}`);
    try {
      await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 15000 });
      await page.waitForTimeout(1500);
      const title = await page.title();
      const pageHeading = await page.locator('h1, h2, h3, h4').first().innerText().catch(() => '');
      const screenshotName = `page-${href.replace(/[^a-zA-Z0-9]/g, '_')}.png`;
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, screenshotName) });
      pagesSummary.push({ href, title, pageHeading, screenshot: screenshotName });
    } catch (e) {
      console.log(`Error visiting ${targetUrl}:`, e.message);
      pagesSummary.push({ href, error: e.message });
    }
  }

  // 4. Detailed inspection of Add Job modal options
  console.log('--- 4. Inspecting Add Job modal in detail ---');
  await page.goto('https://nswdev.rebatem8.com.au/jobs', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);
  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'add-job-modal.png') });

  // Function to inspect react-select options
  async function getSelectOptions(placeholderText) {
    try {
      const selectBox = page.locator(`.select, [class*="control"]`).filter({ hasText: placeholderText }).first();
      if (await selectBox.isVisible()) {
        await selectBox.click();
        await page.waitForTimeout(600);
        const options = await page.locator('[class*="-menu"], [role="listbox"]').locator('[class*="-option"], [role="option"]').allInnerTexts();
        // click again or escape to close
        await page.keyboard.press('Escape');
        await page.waitForTimeout(400);
        return options;
      }
    } catch (e) {
      return [`Error: ${e.message}`];
    }
    return [];
  }

  const activityTypes = await getSelectOptions('Select Activity Type');
  console.log('Activity Types:', activityTypes);

  const leadMethods = await getSelectOptions('Select Method of Lead Generation');
  console.log('Lead Generation Methods:', leadMethods);

  const buildingTypes = await getSelectOptions('Select Building Type');
  console.log('Building Types:', buildingTypes);

  const companies = await getSelectOptions('Select Installer (Company)');
  console.log('Companies (Installer):', companies);

  const inspectionReport = {
    pagesSummary,
    addJobModal: {
      activityTypes,
      leadMethods,
      buildingTypes,
      companies
    }
  };

  fs.writeFileSync(path.join(__dirname, 'site-inspection-report.json'), JSON.stringify(inspectionReport, null, 2));
  console.log('Inspection finished and saved to site-inspection-report.json');

  await browser.close();
}

exploreSite().catch(console.error);

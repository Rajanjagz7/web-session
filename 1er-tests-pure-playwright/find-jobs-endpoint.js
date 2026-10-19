// Discover the jobs-list API endpoint by watching GET requests while the
// All Jobs page loads.
const { chromium } = require('playwright');
const { BASE_URL } = require('./config');
const { login } = require('./helpers');

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 40 });
  const context = await browser.newContext({ baseURL: BASE_URL, viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const apiGets = [];
  page.on('request', (req) => {
    if (req.method() === 'GET' && req.url().includes('/api/')) {
      apiGets.push(req.url());
    }
  });

  await login(page);
  await page.goto('/jobs');
  await page.waitForTimeout(3000);

  console.log('GET /api/ calls seen while loading /jobs:\n');
  apiGets.forEach((u) => console.log(u));

  await browser.close();
})();

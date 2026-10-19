// Searches the Jobs list UI for a given customer email, and if found,
// fetches that job's detail to report its engagement email status.
const { chromium } = require('playwright');
const { BASE_URL } = require('./config');
const { login } = require('./helpers');

const SEARCH_TERM = process.argv[2];
if (!SEARCH_TERM) {
  console.error('Usage: node find-and-check-job.js <search term>');
  process.exit(1);
}

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 40 });
  const context = await browser.newContext({ baseURL: BASE_URL, viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  await login(page);
  await page.goto('/jobs');
  await page.getByPlaceholder('Search Jobs...').fill(SEARCH_TERM);
  await page.waitForTimeout(1500);

  const rows = await page.locator('table tbody tr').all();
  console.log(`Search "${SEARCH_TERM}" -> ${rows.length} row(s) in table.\n`);

  if (rows.length === 0) {
    console.log('No job found matching this search term - it was NOT created from our end (or search index does not cover email).');
  } else {
    for (const row of rows) {
      const text = await row.innerText();
      console.log('--- Row ---\n' + text + '\n');
    }
  }

  // Also try the list API directly with a search/q param in case UI search
  // uses a different mechanism, and to grab the job id for a detail check.
  const apiResult = await page.evaluate(async (term) => {
    const res = await fetch(`/api/v1/jobs?sort=createdAt&sortType=desc&skip=0&limit=10&search=${encodeURIComponent(term)}`, { credentials: 'include' });
    return res.json();
  }, SEARCH_TERM);
  const jobs = apiResult?.data?.jobs || apiResult?.data?.items || [];
  console.log(`\nAPI search (?search=) -> ${jobs.length} result(s).`);
  for (const j of jobs) {
    console.log(`  jobNumber=${j.jobNumber} id=${j.id || j._id} customer=${j.customer?.name} email=${j.customer?.email}`);
  }

  if (jobs.length > 0) {
    for (const j of jobs) {
      const id = j.id || j._id;
      const detail = await page.evaluate(async (id) => {
        const res = await fetch(`/api/v1/jobs/${id}`, { credentials: 'include' });
        return res.json();
      }, id);
      const job = detail?.data?.job;
      const eng = job?.engagement || {};
      console.log(`\nDetail for ${job?.jobNumber}:`);
      console.log(`  status: ${job?.status}`);
      console.log(`  engagement.email: ${JSON.stringify(eng.email)}`);
      console.log(`  engagement.factSheetEmail: ${JSON.stringify(eng.factSheetEmail)}`);
      console.log(`  engagement.sms: ${JSON.stringify(eng.sms)}`);
    }
  }

  await browser.close();
})();

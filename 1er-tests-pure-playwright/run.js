// Entry point. Runs every test collected via describe()/test() sequentially,
// each with its own fresh browser context (page) and fresh API request
// context (request) - mirroring @playwright/test's per-test isolation, but
// using only the raw `playwright` package, no test runner.

const { chromium, request: apiRequestModule } = require('playwright');
const { BASE_URL } = require('./config');
const { tests } = require('./runner');

// Registers every test file's describe()/test() calls into runner.tests.
require('./tests/create-jobs.tests');
require('./tests/auth.tests');
require('./tests/notes.tests');
require('./tests/soft-delete.tests');
require('./tests/post-sign-editing.tests');
require('./tests/add-job-field-boundaries.tests');
require('./tests/add-job-field-boundaries-2.tests');

const HEADED = process.env.HEADED !== '0'; // headed by default, per project convention
const FILTER = process.env.GREP ? new RegExp(process.env.GREP, 'i') : null;

(async () => {
  const browser = await chromium.launch({ headless: !HEADED, slowMo: HEADED ? 60 : 0 });
  const toRun = FILTER ? tests.filter((t) => FILTER.test(t.name)) : tests;

  console.log(`\nRunning ${toRun.length} tests using pure Playwright (no @playwright/test)\n`);

  let passed = 0;
  let failed = 0;
  const failures = [];
  const startAll = Date.now();

  for (const t of toRun) {
    const context = await browser.newContext({ baseURL: BASE_URL, viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    const request = await apiRequestModule.newContext({ baseURL: BASE_URL });
    const start = Date.now();
    try {
      await t.fn({ page, request });
      const secs = ((Date.now() - start) / 1000).toFixed(1);
      console.log(`ok   ${t.name} (${secs}s)`);
      passed++;
    } catch (err) {
      const secs = ((Date.now() - start) / 1000).toFixed(1);
      console.log(`FAIL ${t.name} (${secs}s)\n     ${err.message}`);
      failed++;
      failures.push(t.name);
    } finally {
      await request.dispose().catch(() => {});
      await context.close().catch(() => {});
    }
  }

  const totalSecs = ((Date.now() - startAll) / 1000 / 60).toFixed(1);
  console.log(`\n${passed} passed, ${failed} failed (${totalSecs}m)`);
  if (failures.length) {
    console.log('\nFailed tests:');
    failures.forEach((f) => console.log(`  - ${f}`));
  }

  await browser.close();
  process.exit(failed > 0 ? 1 : 0);
})();

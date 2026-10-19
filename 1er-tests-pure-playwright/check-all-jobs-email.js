// Fetches every job (list endpoint for ids, then detail endpoint per job -
// the list endpoint doesn't include the nested `engagement` sub-object) and
// reports any whose engagement email / fact sheet email never reached
// "sent" status. Retries failed fetches at lower concurrency.
const { chromium } = require('playwright');
const { BASE_URL } = require('./config');
const { login } = require('./helpers');

const CONCURRENCY = 3;
const DELAY_MS = 250;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 0 });
  const context = await browser.newContext({ baseURL: BASE_URL, viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  await login(page);

  const all = [];
  let skip = 0;
  const limit = 50;
  while (true) {
    const result = await page.evaluate(async ({ skip, limit }) => {
      const res = await fetch(`/api/v1/jobs?sort=createdAt&sortType=desc&skip=${skip}&limit=${limit}`, { credentials: 'include' });
      return res.json();
    }, { skip, limit });

    const jobs = result?.data?.jobs || result?.data?.items || result?.data || [];
    if (!Array.isArray(jobs) || jobs.length === 0) break;
    all.push(...jobs);
    if (jobs.length < limit) break;
    skip += limit;
  }

  console.log(`Fetched ${all.length} jobs from the list. Fetching detail for each (concurrency ${CONCURRENCY})...\n`);

  const ids = all.map((j) => j.id || j._id).filter(Boolean);
  const detailsById = new Map();

  async function fetchBatch(idList) {
    for (let i = 0; i < idList.length; i += CONCURRENCY) {
      const batch = idList.slice(i, i + CONCURRENCY);
      const batchResults = await page.evaluate(async (batchIds) => {
        const results = await Promise.all(
          batchIds.map(async (id) => {
            try {
              const res = await fetch(`/api/v1/jobs/${id}`, { credentials: 'include' });
              const text = await res.text();
              let json = null;
              try { json = JSON.parse(text); } catch { return { id, ok: false, error: 'non-json', snippet: text.slice(0, 100) }; }
              return { id, ok: res.ok, job: json?.data?.job || null };
            } catch (e) {
              return { id, ok: false, error: String(e) };
            }
          })
        );
        return results;
      }, batch);
      for (const r of batchResults) detailsById.set(r.id, r);
      process.stdout.write(`\r  fetched ${Math.min(i + CONCURRENCY, idList.length)}/${idList.length}`);
      await sleep(DELAY_MS);
    }
    console.log('');
  }

  await fetchBatch(ids);

  let failedIds = ids.filter((id) => !detailsById.get(id)?.ok);
  let retryRound = 1;
  while (failedIds.length > 0 && retryRound <= 3) {
    console.log(`\nRetry round ${retryRound}: retrying ${failedIds.length} failed fetches...`);
    await fetchBatch(failedIds);
    failedIds = ids.filter((id) => !detailsById.get(id)?.ok);
    retryRound++;
  }

  const details = ids.map((id) => detailsById.get(id));
  const problems = [];
  const fetchErrors = [];
  for (const d of details) {
    if (!d.ok || !d.job) {
      fetchErrors.push(d);
      continue;
    }
    const job = d.job;
    const eng = job.engagement || {};
    const emailStatus = eng.email?.status;
    const factSheetStatus = eng.factSheetEmail?.status;
    if (emailStatus !== 'sent' || factSheetStatus !== 'sent') {
      problems.push({
        jobNumber: job.jobNumber,
        id: job.id,
        status: job.status,
        emailStatus,
        emailAttempts: eng.email?.attempts,
        factSheetStatus,
        factSheetAttempts: eng.factSheetEmail?.attempts,
        smsStatus: eng.sms?.status,
        createdAt: job.createdAt,
        hasEngagementField: !!job.engagement,
      });
    }
  }

  console.log(`\nTotal jobs checked: ${details.length}`);
  console.log(`Still-failed fetches after retries: ${fetchErrors.length}`);
  console.log(`Jobs with an email NOT in "sent" status: ${problems.length}\n`);
  problems.forEach((p) => console.log(JSON.stringify(p)));
  if (fetchErrors.length) {
    console.log('\nStill-failed fetches:');
    fetchErrors.forEach((e) => console.log(JSON.stringify(e)));
  }

  await browser.close();
})();

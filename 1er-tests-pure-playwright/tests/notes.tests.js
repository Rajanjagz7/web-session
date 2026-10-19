const { describe, test, expect } = require('../runner');
const { EMAIL, PASSWORD } = require('../config');
const { loginApi, json } = require('../api-helpers');

async function getAnyJobId(request) {
  const res = await request.get('/api/v1/jobs?limit=1');
  const body = await json(res);
  const jobId = body?.data?.jobs?.[0]?.id;
  if (!jobId) throw new Error('No jobs found to attach a note to - create one first.');
  return jobId;
}

describe('Notes', () => {
  test('a fully empty note (no text, no attachment) is rejected', async ({ request }) => {
    await loginApi(request);
    const jobId = await getAnyJobId(request);

    const res = await request.post('/api/v1/notes', {
      data: { entityType: 'job', entityId: jobId, note: '' },
    });
    expect(res.status()).toBe(400);
    const body = await json(res);
    expect(body.error.details[0].message).toBe('Provide note text or at least one attachment');
  });

  test('a valid text-only note is created successfully', async ({ request }) => {
    await loginApi(request);
    const jobId = await getAnyJobId(request);

    const res = await request.post('/api/v1/notes', {
      data: { entityType: 'job', entityId: jobId, note: `Automated QA note - ${Date.now()}` },
    });
    expect(res.status()).toBe(201);
    const body = await json(res);
    expect(body.data.note.note).toContain('Automated QA note');
  });

  // BUG-08 (Medium, see QA report): calling POST /notes directly with no
  // `visibility` field correctly defaults to 'external' (see above) - the
  // bug is in the FRONTEND: it explicitly sends visibility: "internal" even
  // when the "Internal" toggle is left unchecked, so this has to be driven
  // through the real UI to reproduce. This test currently asserts the
  // ACTUAL (buggy) behaviour; flip once fixed.
  test('KNOWN BUG (BUG-08): submitting a note via the UI with the Internal toggle untouched sends visibility=internal', async ({ page }) => {
    await page.goto('/log-in');
    await page.getByPlaceholder(/email/i).fill(EMAIL);
    await page.getByPlaceholder(/password/i).fill(PASSWORD);
    await page.getByRole('button', { name: /log ?in|sign ?in/i }).click();
    await page.getByRole('button', { name: /add job/i }).waitFor({ state: 'visible', timeout: 20000 });

    await page.goto('/jobs');
    await page.getByPlaceholder('Search Jobs...').fill('M8N000114');
    await page.waitForTimeout(1000);
    await page.locator('table tbody tr').first().locator('svg, img, button').first().click();
    await page.getByRole('button', { name: 'Notes', exact: true }).click();
    await page.locator('.ql-editor').first().waitFor({ state: 'visible', timeout: 15000 });

    await page.locator('.ql-editor').first().click();
    await page.keyboard.type(`UI default-visibility check - ${Date.now()}`);

    const [response] = await Promise.all([
      page.waitForResponse((res) => res.url().includes('/api/v1/notes') && res.request().method() === 'POST'),
      page.getByRole('button', { name: /^add note$/i }).click(),
    ]);
    const body = await response.json();
    expect(body.data.note.visibility).toBe('internal'); // documented default should be 'external'
  });

  test('an explicit external note is created with external visibility', async ({ request }) => {
    await loginApi(request);
    const jobId = await getAnyJobId(request);

    const res = await request.post('/api/v1/notes', {
      data: { entityType: 'job', entityId: jobId, note: `Explicit external - ${Date.now()}`, visibility: 'external' },
    });
    expect(res.status()).toBe(201);
    const body = await json(res);
    expect(body.data.note.visibility).toBe('external');
  });

  test('an explicit internal note is created with internal visibility', async ({ request }) => {
    await loginApi(request);
    const jobId = await getAnyJobId(request);

    const res = await request.post('/api/v1/notes', {
      data: { entityType: 'job', entityId: jobId, note: `Explicit internal - ${Date.now()}`, visibility: 'internal' },
    });
    expect(res.status()).toBe(201);
    const body = await json(res);
    expect(body.data.note.visibility).toBe('internal');
  });
});

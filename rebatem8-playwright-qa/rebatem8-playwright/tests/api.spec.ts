/**
 * API Test Suite — Rebatem8 NSW
 *
 * Uses Playwright's APIRequestContext (no browser) to directly test the REST
 * backend at https://nswdev.rebatem8.com.au/api/v1/**
 *
 * Run:  npm run test:api
 *
 * Required env vars:
 *   E2E_EMAIL    – approved test account email
 *   E2E_PASSWORD – matching password
 */

import { test, expect, APIRequestContext, request } from '@playwright/test';

// ---------------------------------------------------------------------------
// Shared state – token obtained once per file
// ---------------------------------------------------------------------------
const BASE = process.env.BASE_URL ?? 'https://nswdev.rebatem8.com.au';
const AUTH_ENDPOINT = '/api/v1/auth/admin/login';

let sharedToken = '';
let apiCtx: APIRequestContext;

function credentials() {
  const email = process.env.E2E_EMAIL;
  const password = process.env.E2E_PASSWORD;
  if (!email || !password) throw new Error('Set E2E_EMAIL and E2E_PASSWORD env vars before running API tests.');
  return { email, password };
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------
test.beforeAll(async () => {
  apiCtx = await request.newContext({ baseURL: BASE });
});

test.afterAll(async () => {
  await apiCtx.dispose();
});

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------
async function authedGet(path: string, params?: Record<string, string>) {
  return apiCtx.get(path, {
    headers: { Authorization: `Bearer ${sharedToken}` },
    params,
  });
}

/** Skip a test cleanly when credentials are not set in the environment. */
function skipWithoutCreds() {
  if (!process.env.E2E_EMAIL || !process.env.E2E_PASSWORD) {
    test.skip(true, 'Skipped: set E2E_EMAIL and E2E_PASSWORD to run this test');
  }
}

// ============================================================================
// GROUP 1 — Authentication API
// ============================================================================
test.describe('AUTH API', () => {

  test('API-AUTH-001 | Positive | POST /auth/admin/login with valid credentials returns 200 + token', async () => {
    const c = credentials();
    const res = await apiCtx.post(AUTH_ENDPOINT, { data: { email: c.email, password: c.password } });
    expect(res.status(), `Expected 200, got ${res.status()}`).toBe(200);

    const body = await res.json();
    const token: string =
      body?.data?.token ?? body?.token ?? body?.data?.accessToken ?? body?.accessToken ?? '';
    expect(token, 'Response must contain a non-empty bearer token').toBeTruthy();
    sharedToken = token;
  });

  test('API-AUTH-002 | Negative | POST /auth/admin/login with wrong password returns 400/401/403', async () => {
    const c = credentials();
    const res = await apiCtx.post(AUTH_ENDPOINT, {
      data: { email: c.email, password: 'Definitely-Wrong-Password-API-QA-2026!' },
    });
    expect([400, 401, 403]).toContain(res.status());
  });

  test('API-AUTH-003 | Negative | POST /auth/admin/login with nonexistent account returns 400/401/403', async () => {
    const res = await apiCtx.post(AUTH_ENDPOINT, {
      data: { email: `qa-ghost-${Date.now()}@example.com`, password: 'Synthetic-Only-123!' },
    });
    expect([400, 401, 403]).toContain(res.status());
  });

  test('API-AUTH-004 | Negative | POST /auth/admin/login with empty body returns 400/422', async () => {
    const res = await apiCtx.post(AUTH_ENDPOINT, { data: {} });
    expect([400, 422]).toContain(res.status());
  });

  test('API-AUTH-005 | Security | POST /auth/admin/login returns JSON (not HTML)', async () => {
    // Use synthetic credentials — the server returns JSON for both success AND failure
    const res = await apiCtx.post(AUTH_ENDPOINT, {
      data: { email: 'qa-check@example.com', password: 'Synthetic-Only-123!' },
    });
    const ct = res.headers()['content-type'] ?? '';
    expect(ct, 'Login endpoint must always return application/json, not HTML').toContain('application/json');
  });

  test('API-AUTH-006 | Security | Bearer token required — unauthenticated GET /jobs returns 401/403', async () => {
    const res = await apiCtx.get('/api/v1/jobs');
    expect([401, 403]).toContain(res.status());
  });

  test('API-AUTH-007 | Security | Malformed token is rejected with 401/403', async () => {
    const res = await apiCtx.get('/api/v1/jobs', {
      headers: { Authorization: 'Bearer this.is.not.a.real.jwt' },
    });
    expect([401, 403]).toContain(res.status());
  });

});

// ============================================================================
// GROUP 2 — Dashboard API
// ============================================================================
test.describe('DASHBOARD API', () => {

  const dashboardEndpoints = [
    { id: '001', path: '/api/v1/dashboard/job-tracking' },
    { id: '002', path: '/api/v1/dashboard/job-count' },
    { id: '003', path: '/api/v1/dashboard/job-breakdown' },
    { id: '004', path: '/api/v1/dashboard/top-product' },
    { id: '005', path: '/api/v1/dashboard/job-rebate' },
    { id: '006', path: '/api/v1/dashboard/avg-complete-time' },
  ];

  for (const ep of dashboardEndpoints) {
    test(`API-DASH-${ep.id} | Positive | GET ${ep.path} returns 200 with JSON`, async () => {
      const res = await authedGet(ep.path);
      expect(res.status(), `${ep.path} returned ${res.status()}`).toBe(200);
      const ct = res.headers()['content-type'] ?? '';
      expect(ct).toContain('application/json');
    });
  }

});

// ============================================================================
// GROUP 3 — Core Resource Endpoints
// ============================================================================
test.describe('CORE RESOURCE API', () => {

  const resources = [
    { id: '001', path: '/api/v1/jobs' },
    { id: '002', path: '/api/v1/installers' },
    { id: '003', path: '/api/v1/users' },
    { id: '004', path: '/api/v1/matrix' },
    { id: '005', path: '/api/v1/products' },
    { id: '006', path: '/api/v1/products/brands' },
    { id: '007', path: '/api/v1/cms' },
    { id: '008', path: '/api/v1/activity-logs' },
    { id: '009', path: '/api/v1/invoice/list' },
    { id: '010', path: '/api/v1/rebate/installer/list' },
    { id: '011', path: '/api/v1/site/list' },
    { id: '012', path: '/api/v1/installer/filter/list' },
    { id: '013', path: '/api/v1/calculator-usage/installer/list' },
  ];

  for (const r of resources) {
    test(`API-RES-${r.id} | Positive | GET ${r.path} returns 200 + JSON`, async () => {
      const res = await authedGet(r.path);
      expect(res.status(), `${r.path} returned ${res.status()}`).toBe(200);
      const ct = res.headers()['content-type'] ?? '';
      expect(ct).toContain('application/json');
    });
  }

  test('API-RES-014 | Positive | GET /api/v1/jobs response body contains a list', async () => {
    skipWithoutCreds();
    const res = await authedGet('/api/v1/jobs');
    expect(res.status()).toBe(200);
    const body = await res.json();
    const list = Array.isArray(body) ? body : (body?.data ?? body?.items ?? body?.results);
    expect(Array.isArray(list), 'jobs response must contain a list').toBe(true);
  });

  test('API-RES-015 | Positive | GET /api/v1/installers response body contains a list', async () => {
    skipWithoutCreds();
    const res = await authedGet('/api/v1/installers');
    expect(res.status()).toBe(200);
    const body = await res.json();
    const list = Array.isArray(body) ? body : (body?.data ?? body?.items ?? body?.results);
    expect(Array.isArray(list), 'installers response must contain a list').toBe(true);
  });

  test('API-RES-016 | Positive | GET /api/v1/users response body contains a list', async () => {
    skipWithoutCreds();
    const res = await authedGet('/api/v1/users');
    expect(res.status()).toBe(200);
    const body = await res.json();
    const list = Array.isArray(body) ? body : (body?.data ?? body?.items ?? body?.results);
    expect(Array.isArray(list), 'users response must contain a list').toBe(true);
  });

});

// ============================================================================
// GROUP 4 — Search / Filter API
// ============================================================================
test.describe('SEARCH API', () => {

  const searchableEndpoints = [
    { id: '001', path: '/api/v1/installers',    param: 'search' },
    { id: '002', path: '/api/v1/matrix',        param: 'search' },
    { id: '003', path: '/api/v1/users',         param: 'search' },
    { id: '004', path: '/api/v1/activity-logs', param: 'search' },
  ];

  const NO_MATCH = 'qa_api_no_match_7d9f2c_20260914';

  for (const ep of searchableEndpoints) {
    test(`API-SEARCH-${ep.id} | Edge | GET ${ep.path}?${ep.param}=<no-match> returns 200 + empty list`, async () => {
      const res = await authedGet(ep.path, { [ep.param]: NO_MATCH });
      expect(res.status(), `${ep.path} search returned ${res.status()}`).toBe(200);
      const body = await res.json();
      const list = Array.isArray(body) ? body : (body?.data ?? body?.items ?? body?.results ?? []);
      expect(Array.isArray(list), 'search result must be a list').toBe(true);
      expect(list.length, 'no-match search should return 0 results').toBe(0);
    });
  }

});

// ============================================================================
// GROUP 5 — Security API
// ============================================================================
test.describe('SECURITY API', () => {

  test('API-SEC-001 | Security | GET /api/v1/activity-logs without auth returns 401/403', async () => {
    const res = await apiCtx.get('/api/v1/activity-logs');
    expect([401, 403]).toContain(res.status());
  });

  test('API-SEC-002 | Security | GET /api/v1/users without auth returns 401/403', async () => {
    const res = await apiCtx.get('/api/v1/users');
    expect([401, 403]).toContain(res.status());
  });

  test('API-SEC-003 | Security BUG | GET /api/v1/invoice/list without auth returns 404 instead of 401/403', async () => {
    // FINDING: This endpoint returns 404 when unauthenticated instead of 401/403.
    // This leaks the existence of the route to unauthenticated callers — it should
    // return 401 to be consistent with all other protected endpoints.
    const res = await apiCtx.get('/api/v1/invoice/list');
    // Document the current (incorrect) observed behaviour:
    expect(res.status(), 'BUG: /api/v1/invoice/list should return 401/403 when unauthenticated, not 404').toBe(404);
  });

  test('API-SEC-004 | Security | Error bodies must not expose stack traces', async () => {
    const res = await apiCtx.get('/api/v1/jobs'); // unauthenticated
    const body = await res.text();
    expect(body).not.toMatch(/at Object\.|at Module\.|node_modules|TypeError:|ReferenceError:/);
  });

  test('API-SEC-005 | Security | HTTPS is enforced (base URL uses https)', async () => {
    expect(new URL(BASE).protocol).toBe('https:');
  });

  test('API-SEC-006 | Security | Response headers must not expose internal framework via x-powered-by', async () => {
    // Check headers on the unauthenticated 401 response — no credentials needed
    const res = await apiCtx.get('/api/v1/jobs');
    const xpb = res.headers()['x-powered-by'] ?? '';
    expect(xpb).not.toMatch(/express|laravel|django|rails|php/i);
  });

});

// ============================================================================
// GROUP 6 — HTTP Protocol / Headers
// ============================================================================
test.describe('PROTOCOL API', () => {

  test('API-PROTO-001 | Edge | OPTIONS preflight on auth endpoint is handled (200/204/405)', async () => {
    const res = await apiCtx.fetch(AUTH_ENDPOINT, {
      method: 'OPTIONS',
      headers: {
        Origin: BASE,
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type,Authorization',
      },
    });
    expect([200, 204, 405]).toContain(res.status());
  });

  test('API-PROTO-002 | Edge | GET on auth endpoint is rejected (not a POST resource)', async () => {
    const res = await apiCtx.get(AUTH_ENDPOINT);
    expect([404, 405]).toContain(res.status());
  });

  test('API-PROTO-003 | Edge | Login response Content-Type is application/json', async () => {
    skipWithoutCreds();
    const c = credentials();
    const res = await apiCtx.post(AUTH_ENDPOINT, { data: { email: c.email, password: c.password } });
    const ct = res.headers()['content-type'] ?? '';
    expect(ct).toContain('application/json');
  });

  test('API-PROTO-004 | Performance | Login responds within 5 000 ms', async () => {
    const c = credentials();
    const start = Date.now();
    const res = await apiCtx.post(AUTH_ENDPOINT, { data: { email: c.email, password: c.password } });
    const elapsed = Date.now() - start;
    expect(res.status()).toBe(200);
    expect(elapsed, `Login took ${elapsed}ms — exceeded 5 000 ms SLA`).toBeLessThan(5000);
  });

  test('API-PROTO-005 | Performance | GET /api/v1/jobs responds within 8 000 ms', async () => {
    const start = Date.now();
    const res = await authedGet('/api/v1/jobs');
    const elapsed = Date.now() - start;
    expect(res.status()).toBe(200);
    expect(elapsed, `Jobs list took ${elapsed}ms — exceeded 8 000 ms SLA`).toBeLessThan(8000);
  });

});

// ============================================================================
// GROUP 7 — Pagination & Filtering API
// ============================================================================
test.describe('PAGINATION API', () => {

  test('API-PAGE-001 | Positive | GET /api/v1/jobs?page=1&limit=5 returns at most 5 items', async () => {
    const res = await authedGet('/api/v1/jobs', { page: '1', limit: '5' });
    expect(res.status()).toBe(200);
    const body = await res.json();
    const list = Array.isArray(body) ? body : (body?.data ?? body?.items ?? body?.results ?? []);
    expect(Array.isArray(list)).toBe(true);
    expect(list.length, `Requested limit=5 but got ${list.length} items`).toBeLessThanOrEqual(5);
  });

  test('API-PAGE-002 | Positive | GET /api/v1/installers?page=1&limit=10 returns at most 10 items', async () => {
    const res = await authedGet('/api/v1/installers', { page: '1', limit: '10' });
    expect(res.status()).toBe(200);
    const body = await res.json();
    const list = Array.isArray(body) ? body : (body?.data ?? body?.items ?? body?.results ?? []);
    expect(Array.isArray(list)).toBe(true);
    expect(list.length).toBeLessThanOrEqual(10);
  });

  test('API-PAGE-003 | Positive | GET /api/v1/users?page=1&limit=10 returns at most 10 items', async () => {
    const res = await authedGet('/api/v1/users', { page: '1', limit: '10' });
    expect(res.status()).toBe(200);
    const body = await res.json();
    const list = Array.isArray(body) ? body : (body?.data ?? body?.items ?? body?.results ?? []);
    expect(Array.isArray(list)).toBe(true);
    expect(list.length).toBeLessThanOrEqual(10);
  });

  test('API-PAGE-004 | Edge | GET /api/v1/jobs?page=0 does not crash (200 or 400)', async () => {
    const res = await authedGet('/api/v1/jobs', { page: '0' });
    expect([200, 400, 422]).toContain(res.status());
  });

  test('API-PAGE-005 | Edge | GET /api/v1/jobs?limit=0 does not crash (200 or 400)', async () => {
    const res = await authedGet('/api/v1/jobs', { limit: '0' });
    expect([200, 400, 422]).toContain(res.status());
  });

  test('API-PAGE-006 | Edge | GET /api/v1/jobs?page=9999999 returns 200 with empty list (beyond last page)', async () => {
    const res = await authedGet('/api/v1/jobs', { page: '9999999', limit: '10' });
    expect([200, 400]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      const list = Array.isArray(body) ? body : (body?.data ?? body?.items ?? body?.results ?? []);
      expect(Array.isArray(list)).toBe(true);
      expect(list.length, 'Beyond last page should return 0 items').toBe(0);
    }
  });

  test('API-PAGE-007 | Edge | GET /api/v1/jobs?limit=negative returns 200 or 400/422 (no crash)', async () => {
    const res = await authedGet('/api/v1/jobs', { limit: '-1' });
    expect([200, 400, 422]).toContain(res.status());
  });

  test('API-PAGE-008 | Edge | GET /api/v1/jobs?limit=999999 does not crash the server', async () => {
    const res = await authedGet('/api/v1/jobs', { limit: '999999' });
    expect([200, 400, 422]).toContain(res.status());
  });

  test('API-PAGE-009 | Positive | GET /api/v1/activity-logs?page=1&limit=5 honours limit', async () => {
    const res = await authedGet('/api/v1/activity-logs', { page: '1', limit: '5' });
    expect(res.status()).toBe(200);
    const body = await res.json();
    const list = Array.isArray(body) ? body : (body?.data ?? body?.items ?? body?.results ?? []);
    expect(Array.isArray(list)).toBe(true);
    expect(list.length).toBeLessThanOrEqual(5);
  });

  test('API-PAGE-010 | Positive | Page 2 is different from page 1 for /api/v1/jobs', async () => {
    const [r1, r2] = await Promise.all([
      authedGet('/api/v1/jobs', { page: '1', limit: '5' }),
      authedGet('/api/v1/jobs', { page: '2', limit: '5' }),
    ]);
    expect(r1.status()).toBe(200);
    expect(r2.status()).toBe(200);
    const b1 = await r1.json();
    const b2 = await r2.json();
    const list1 = Array.isArray(b1) ? b1 : (b1?.data ?? b1?.items ?? b1?.results ?? []);
    const list2 = Array.isArray(b2) ? b2 : (b2?.data ?? b2?.items ?? b2?.results ?? []);
    // Pages exist and are different (IDs on page 1 should not all appear on page 2)
    if (list1.length > 0 && list2.length > 0) {
      const ids1 = new Set(list1.map((j: Record<string, unknown>) => j.id ?? j._id ?? j.jobId));
      const ids2 = list2.map((j: Record<string, unknown>) => j.id ?? j._id ?? j.jobId);
      const overlap = ids2.filter((id: unknown) => ids1.has(id));
      expect(overlap.length, 'Page 1 and page 2 must not return identical records').toBeLessThan(list1.length);
    }
  });

});

// ============================================================================
// GROUP 8 — Response Shape Validation
// ============================================================================
test.describe('SHAPE API', () => {

  test('API-SHAPE-001 | Positive | Job list items have expected fields (id, status)', async () => {
    const res = await authedGet('/api/v1/jobs', { page: '1', limit: '3' });
    expect(res.status()).toBe(200);
    const body = await res.json();
    const list = Array.isArray(body) ? body : (body?.data ?? body?.items ?? body?.results ?? []);
    if (list.length > 0) {
      const job = list[0];
      // At minimum a job should have some id field
      const hasId = 'id' in job || '_id' in job || 'jobId' in job || 'job_id' in job;
      expect(hasId, 'Job record must have an id field').toBe(true);
    }
  });

  test('API-SHAPE-002 | Positive | Installer list items have expected fields', async () => {
    const res = await authedGet('/api/v1/installers', { page: '1', limit: '3' });
    expect(res.status()).toBe(200);
    const body = await res.json();
    const list = Array.isArray(body) ? body : (body?.data ?? body?.items ?? body?.results ?? []);
    if (list.length > 0) {
      const item = list[0];
      const hasId = 'id' in item || '_id' in item || 'installerId' in item;
      expect(hasId, 'Installer record must have an id field').toBe(true);
    }
  });

  test('API-SHAPE-003 | Positive | User list items have expected fields', async () => {
    const res = await authedGet('/api/v1/users', { page: '1', limit: '3' });
    expect(res.status()).toBe(200);
    const body = await res.json();
    const list = Array.isArray(body) ? body : (body?.data ?? body?.items ?? body?.results ?? []);
    if (list.length > 0) {
      const user = list[0];
      const hasId = 'id' in user || '_id' in user || 'userId' in user;
      expect(hasId, 'User record must have an id field').toBe(true);
      // Passwords must never appear in list responses
      const json = JSON.stringify(user).toLowerCase();
      expect(json).not.toMatch(/"password"\s*:/);
    }
  });

  test('API-SHAPE-004 | Security | User list response must not contain plaintext passwords', async () => {
    skipWithoutCreds();
    const res = await authedGet('/api/v1/users');
    expect(res.status()).toBe(200);
    const raw = await res.text();
    // Should never see a "password" key with a non-empty string value
    expect(raw).not.toMatch(/"password"\s*:\s*"[^"]+"/i);
    expect(raw).not.toMatch(/"passwordHash"\s*:\s*"[^"]+"/i);
  });

  test('API-SHAPE-005 | Positive | Dashboard job-count returns a numeric value', async () => {
    const res = await authedGet('/api/v1/dashboard/job-count');
    expect(res.status()).toBe(200);
    const body = await res.json();
    // Accept number at root, or inside a data/count/total key
    const raw = JSON.stringify(body);
    expect(raw).toMatch(/\d+/); // at least one number somewhere in the response
  });

  test('API-SHAPE-006 | Positive | Products list items include a name/title field', async () => {
    const res = await authedGet('/api/v1/products', { page: '1', limit: '3' });
    expect(res.status()).toBe(200);
    const body = await res.json();
    const list = Array.isArray(body) ? body : (body?.data ?? body?.items ?? body?.results ?? []);
    if (list.length > 0) {
      const item = list[0];
      const hasName = 'name' in item || 'title' in item || 'productName' in item;
      expect(hasName, 'Product record must include a name/title field').toBe(true);
    }
  });

  test('API-SHAPE-007 | Positive | Matrix list items include a ruleNo / rule_no field', async () => {
    const res = await authedGet('/api/v1/matrix', { page: '1', limit: '3' });
    expect(res.status()).toBe(200);
    const body = await res.json();
    const list = Array.isArray(body) ? body : (body?.data ?? body?.items ?? body?.results ?? []);
    if (list.length > 0) {
      const item = list[0];
      const keys = Object.keys(item).join('|').toLowerCase();
      expect(keys).toMatch(/rule|id|no/);
    }
  });

  test('API-SHAPE-008 | Positive | Activity log items include a date/timestamp field', async () => {
    const res = await authedGet('/api/v1/activity-logs', { page: '1', limit: '3' });
    expect(res.status()).toBe(200);
    const body = await res.json();
    const list = Array.isArray(body) ? body : (body?.data ?? body?.items ?? body?.results ?? []);
    if (list.length > 0) {
      const item = list[0];
      const keys = Object.keys(item).join('|').toLowerCase();
      expect(keys).toMatch(/date|time|created|updated|at/);
    }
  });

});

// ============================================================================
// GROUP 9 — Injection & Fuzzing Security
// ============================================================================
test.describe('INJECTION API', () => {

  // SQL injection probes via search param — server must return 200 (empty results)
  // or 400/422, and NEVER 500
  const sqlPayloads = [
    { id: '001', name: "Single quote",        val: "'" },
    { id: '002', name: "OR 1=1",              val: "' OR '1'='1" },
    { id: '003', name: "UNION SELECT",        val: "' UNION SELECT null,null,null--" },
    { id: '004', name: "SQL comment",         val: "admin'--" },
    { id: '005', name: "Semicolon statement", val: "1; DROP TABLE jobs--" },
  ];

  for (const p of sqlPayloads) {
    test(`API-INJ-${p.id} | Security | SQL injection via search (${p.name}) does not cause 500`, async () => {
      const res = await authedGet('/api/v1/jobs', { search: p.val });
      expect(res.status(), `SQL payload caused unexpected 500`).not.toBe(500);
      expect([200, 400, 401, 422]).toContain(res.status());
    });
  }

  // XSS payloads via search param
  const xssPayloads = [
    { id: '006', name: "Script tag",        val: '<script>alert(1)</script>' },
    { id: '007', name: "SVG onload",        val: '<svg onload=alert(1)>' },
    { id: '008', name: "img onerror",       val: '<img src=x onerror=alert(1)>' },
    { id: '009', name: "javascript URI",    val: 'javascript:alert(1)' },
  ];

  for (const p of xssPayloads) {
    test(`API-INJ-${p.id} | Security | XSS via search (${p.name}) does not reflect script in response`, async () => {
      const res = await authedGet('/api/v1/jobs', { search: p.val });
      // 401 = no credentials set; the payload still must not be reflected
      expect([200, 400, 401, 422]).toContain(res.status());
      const raw = await res.text();
      // Response must NOT echo back unencoded script tags (check even on error bodies)
      expect(raw).not.toMatch(/<script[\s>]/i);
      expect(raw).not.toMatch(/onerror\s*=/i);
      expect(raw).not.toMatch(/onload\s*=/i);
    });
  }

  // Path traversal via unexpected characters
  test('API-INJ-010 | Security | Path traversal characters in search param do not cause 500', async () => {
    const res = await authedGet('/api/v1/jobs', { search: '../../etc/passwd' });
    // 401 acceptable when sharedToken empty
    expect([200, 400, 401, 422]).toContain(res.status());
    expect(res.status()).not.toBe(500);
  });

  // Very long search string (DoS probe)
  test('API-INJ-011 | Edge | Excessively long search string (10 000 chars) does not cause 500', async () => {
    const res = await authedGet('/api/v1/jobs', { search: 'a'.repeat(10000) });
    // 401 = no token; 414 = URI Too Long (valid server rejection)
    expect([200, 400, 401, 413, 414, 422]).toContain(res.status());
    expect(res.status()).not.toBe(500);
  });

  // Unicode / emoji in search
  test('API-INJ-012 | Edge | Unicode and emoji in search param are handled gracefully', async () => {
    const res = await authedGet('/api/v1/jobs', { search: '🔥テスト\u0000null' });
    // 401 acceptable when sharedToken empty
    expect([200, 400, 401, 422]).toContain(res.status());
    expect(res.status()).not.toBe(500);
  });

  // Null byte injection
  test('API-INJ-013 | Security | Null byte in search param does not cause 500', async () => {
    const res = await authedGet('/api/v1/jobs', { search: 'test\u0000malicious' });
    // 401 acceptable when sharedToken empty
    expect([200, 400, 401, 422]).toContain(res.status());
    expect(res.status()).not.toBe(500);
  });

});

// ============================================================================
// GROUP 10 — Content Negotiation & Edge HTTP Inputs
// ============================================================================
test.describe('CONTENT API', () => {

  test('API-CONT-001 | Edge | POST /auth/admin/login with text/plain body returns 400/415 (not 500)', async () => {
    const res = await apiCtx.fetch(AUTH_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      data: 'not-json-at-all',
    });
    expect([400, 415, 422]).toContain(res.status());
    expect(res.status()).not.toBe(500);
  });

  test('API-CONT-002 | BUG | POST /auth/admin/login with malformed JSON body causes 500 Internal Server Error', async () => {
    // FINDING: Sending a malformed JSON body returns HTTP 500.
    // The server should return 400 Bad Request for invalid JSON — a 500 leaks
    // that the body parser is crashing without proper error handling.
    const res = await apiCtx.fetch(AUTH_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      data: '{ "email": "bad json',
    });
    // Document the current (incorrect) observed behaviour:
    expect(res.status(), 'BUG: malformed JSON body should return 400, not 500').toBe(500);
  });

  test('API-CONT-003 | Edge | POST /auth/admin/login with extra unexpected fields is handled gracefully', async () => {
    const res = await apiCtx.post(AUTH_ENDPOINT, {
      data: {
        email: `qa-extra-${Date.now()}@example.com`,
        password: 'Synthetic-Only-123!',
        __proto__: { polluted: true },
        admin: true,
        role: 'superadmin',
        injected: '<script>alert(1)</script>',
      },
    });
    // Should respond with auth failure, not 500
    expect([400, 401, 403, 422]).toContain(res.status());
    expect(res.status()).not.toBe(500);
  });

  test('API-CONT-004 | Edge | POST /auth/admin/login with no Content-Type header is handled (not 500)', async () => {
    const res = await apiCtx.fetch(AUTH_ENDPOINT, {
      method: 'POST',
      // No Content-Type header
      data: 'email=test%40example.com&password=Synthetic-Only-123!',
    });
    expect([200, 400, 401, 415, 422]).toContain(res.status());
    expect(res.status()).not.toBe(500);
  });

  test('API-CONT-005 | Edge | PUT /auth/admin/login returns 404/405 (wrong method)', async () => {
    const res = await apiCtx.put(AUTH_ENDPOINT, {
      data: { email: 'qa@example.com', password: 'Synthetic-Only-123!' },
    });
    expect([404, 405]).toContain(res.status());
  });

  test('API-CONT-006 | Edge | PATCH /auth/admin/login returns 404/405 (wrong method)', async () => {
    const res = await apiCtx.patch(AUTH_ENDPOINT, {
      data: { email: 'qa@example.com' },
    });
    expect([404, 405]).toContain(res.status());
  });

  test('API-CONT-007 | Edge | DELETE /auth/admin/login returns 404/405 (wrong method)', async () => {
    const res = await apiCtx.delete(AUTH_ENDPOINT);
    expect([404, 405]).toContain(res.status());
  });

  test('API-CONT-008 | Edge | GET /api/v1/nonexistent-endpoint returns 404 (not 500)', async () => {
    const res = await authedGet('/api/v1/nonexistent-endpoint-qa-probe');
    expect(res.status()).toBe(404);
  });

  test('API-CONT-009 | Edge | GET /api/v1/jobs with Accept: text/html still returns JSON or 406', async () => {
    const res = await apiCtx.get('/api/v1/jobs', {
      headers: {
        Authorization: `Bearer ${sharedToken}`,
        Accept: 'text/html',
      },
    });
    // Either serve JSON anyway, or correctly reject with 406 Not Acceptable
    expect([200, 401, 406]).toContain(res.status());
    if (res.status() === 200) {
      const ct = res.headers()['content-type'] ?? '';
      expect(ct).toContain('application/json');
    }
  });

  test('API-CONT-010 | Edge | Extremely large Authorization header does not cause 500', async () => {
    const res = await apiCtx.get('/api/v1/jobs', {
      headers: { Authorization: `Bearer ${'x'.repeat(8000)}` },
    });
    expect([400, 401, 403, 431]).toContain(res.status());
    expect(res.status()).not.toBe(500);
  });

  test('API-CONT-011 | Edge | GET /api/v1/jobs with empty Authorization header returns 401/403', async () => {
    const res = await apiCtx.get('/api/v1/jobs', {
      headers: { Authorization: '' },
    });
    expect([401, 403]).toContain(res.status());
  });

  test('API-CONT-012 | Edge | GET /api/v1/jobs with Bearer (no token) returns 401/403', async () => {
    const res = await apiCtx.get('/api/v1/jobs', {
      headers: { Authorization: 'Bearer ' },
    });
    expect([401, 403]).toContain(res.status());
  });

});

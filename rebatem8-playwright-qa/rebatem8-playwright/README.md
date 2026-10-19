# RebateM8 NSW — Playwright QA suite

Target: **https://nswdev.rebatem8.com.au/log-in**  
Requested under the “Ozmed” project name; this deliverable tests only the RebateM8 NSW site confirmed by the requester. It does not test dev.ozmed.health.

## Quick start

Requirements: Node.js 20+ and npm. Run from this folder:

```sh
npm ci
npx playwright install --with-deps chromium
export BASE_URL='https://nswdev.rebatem8.com.au'
export E2E_EMAIL='your-approved-test-account'
# Enter the password without saving it in this project or shell history (Bash):
read -rs -p 'Test-account password: ' E2E_PASSWORD; echo
export E2E_PASSWORD
npm test
```

Use a dedicated, approved development QA account. Store credentials in CI secrets, never source control. `.env.example` documents variable names; it is not loaded automatically. Missing credentials fail setup clearly rather than silently skipping authenticated coverage.

```sh
npm run typecheck
npm run test:auth
npm run test:modules
npm run test:session
npm run report
```

Cross-browser option (configured, not part of the delivered Chromium execution):

```sh
npx playwright install --with-deps firefox webkit
npm run test:cross-browser
```

The cross-browser command uses POSIX environment syntax; in PowerShell set `$env:CROSS_BROWSER='1'`, then run `npm test`.

## Fresh test-case format

`test-cases.csv` is the executed automation catalogue. It contains stable IDs, module/category, priority, preconditions, steps, expected result, observed result, execution status, and source location. The source-of-truth assertions are in the TypeScript specs.

`extended-test-cases.csv` contains **46 additional planned cases** for deeper project workflows. These are **not executed** and **not represented as completed Playwright automation**. Each states its fixture/requirements dependency. `coverage-gaps.md` explains the remaining scope.

## Suite layout

| File | Coverage |
|---|---|
| `tests/auth.spec.ts` | Required fields, malformed emails, successful login, one real incorrect-password attempt, one nonexistent account, Enter submission, reveal/hide, validation recovery, valid email syntax, long/Unicode passwords, whitespace preservation |
| `tests/resilience.spec.ts` | Intercepted 401/429/500/503/502 responses, disconnected network, pending-request double submission |
| `tests/accessibility.spec.ts` | Four login viewport sizes, associated labels, reveal-button keyboard access, validation semantics, tab navigation |
| `tests/modules.spec.ts` | Read-only route rendering and API health, observed Exception Logs denial, no-match search and clear on eligible list pages |
| `tests/session.spec.ts` | Anonymous guards for 20 discovered routes, refresh, login-page redirect, simulated rejected session, same-context tab, sign-out/deep-link/Back checks |
| `tests/data/modules.json` | Route and control contracts derived from the actual inspected application |

## Live versus simulated checks

- **LIVE** assertions exercise the real application/server. API-health failures are left failing so they become regression checks after fixes.
- **MOCK** assertions intercept the login/session response in the browser. They test frontend behavior, not backend lockout, throttling, password policy, or session expiration.
- Malformed-email validation tests also intercept any attempted login request. Their requirement is that invalid forms produce field feedback and send **zero** requests.
- Successful login uses the supplied account through environment variables. The real incorrect-password test makes **one attempt per selected browser per run**; there are no retries or brute-force loops.
- The Exception Logs test is an explicit **characterization** of observed denial. It does not establish that the master-admin permission policy is correct.
- API health requires no 4xx/5xx on authenticated page loading. Empty-state text alone is not considered successful data loading.

## Safety and evidence

Tests do not create, edit, delete, publish, export, send notifications, or change business records. Login/logout may produce normal server access/audit records. Authenticated read-only contexts additionally block mutating `/api/` requests other than login/logout; this is a limited safety guard, not a universal browser firewall.

Setup temporarily stores sensitive session state in `.auth/session.json` with restricted permissions. Teardown removes it. If a run is forcibly interrupted, delete `.auth/` manually. It is ignored by Git and excluded from this delivery.

Trace, video, and automatic screenshots are disabled to avoid capturing credentials and customer records. Playwright may still create failure context files on a local run; treat `test-results/` and `playwright-report/` as sensitive. The delivered `execution-results.json`, test catalogue and summary retain sanitized diagnostics only; raw authenticated page snapshots are not included. `evidence/login-validation.png` contains an anonymous, empty-field validation screen.

## Limits

This is broad authentication, session, accessibility and read-only module coverage—not exhaustive project certification or a penetration test. Full CRUD, finance/calculator correctness, upload security, role isolation, rate limiting and concurrency require approved disposable records, expected calculations, role accounts and acceptance criteria. Firefox/WebKit and physical mobile devices were not executed. Mobile coverage here is desktop Chromium at mobile viewport sizes.

See `TEST-REPORT.md` for the actual executed results, defects and caveats.

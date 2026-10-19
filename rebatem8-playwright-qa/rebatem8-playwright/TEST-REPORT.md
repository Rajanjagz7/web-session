# RebateM8 NSW — QA test report

**Test date:** 14 September 2026  
**Confirmed target:** https://nswdev.rebatem8.com.au/log-in  
**Execution:** Playwright 1.58.2, headless Chromium, one worker, no automatic retries.

## Result

**89 unique automated cases executed: 71 passed, 18 failed, 0 skipped.**

An additional **46 project-level cases are documented but not executed**. They are not included in the pass/fail count. Failed tests remain failing in the delivered suite; they were not marked as expected failures or skipped.

| Suite | Executed | Passed | Failed |
|---|---:|---:|---:|
| accessibility.spec.ts | 9 | 5 | 4 |
| auth.spec.ts | 24 | 21 | 3 |
| modules.spec.ts | 24 | 13 | 11 |
| resilience.spec.ts | 7 | 7 | 0 |
| session.spec.ts | 25 | 25 | 0 |

## What worked

Successful admin login (including Enter submission), rejection of incorrect credentials, password reveal/hide, required-field feedback, validation recovery, four login viewport sizes, and multiple healthy read-only modules were exercised. Session and route-guard results are listed individually in the accompanying catalogue. Mocked error-response tests assess frontend handling, not real backend rate limiting or resilience.

## Findings to prioritize

### 1. Authenticated page requests fail — P1

10 module-health cases failed because the UI issued data requests returning HTTP 400 or 404. The relevant pages can display an empty state despite a failed request; this is not evidence that the underlying dataset is genuinely empty.

**Reproduce:** sign in, open a listed route and inspect its network requests. **Expected:** a successful data response, or an actionable failure state rather than a misleading normal empty state. **Recommended investigation:** compare frontend endpoint paths and status-filter parameters against the deployed backend contract. A root cause has not been established.

| API path | HTTP status | Page routes |
|---|---:|---|
| `/api/v1/installer/filter/list` | 404 | `/dashboard`, `/projects`, `/rebates/statistics` |
| `/api/v1/dashboard/job-tracking` | 404 | `/dashboard` |
| `/api/v1/dashboard/job-count` | 404 | `/dashboard` |
| `/api/v1/dashboard/job-breakdown` | 404 | `/dashboard` |
| `/api/v1/dashboard/top-product` | 404 | `/dashboard` |
| `/api/v1/dashboard/job-rebate` | 404 | `/dashboard` |
| `/api/v1/dashboard/avg-complete-time` | 404 | `/dashboard` |
| `/api/v1/site/list` | 404 | `/projects` |
| `/api/v1/jobs` | 400 | `/in-progress-jobs`, `/action-Required-jobs`, `/being-assessed-jobs`, `/completed-jobs`, `/archived-jobs` |
| `/api/v1/rebate/installer/list` | 404 | `/rebates` |
| `/api/v1/calculator-usage/installer/list` | 404 | `/rebates/statistics` |
| `/api/v1/invoice/list` | 404 | `/invoices` |

### 2. Activity no-match search — P1

The initial Activity page loaded, but entering the synthetic no-match search marker returned a non-success response. The test expects HTTP 200 and a normal no-results state. See SEARCH-004 for the actual status and reproduction code.

### 3. Login email validation gaps — P2

Tests AUTH-011–013 cover consecutive dots, a leading dot and a trailing local-part dot in an unquoted email address. The form did not provide the expected inline validation. The diagnostic rerun also asserts that no login request is sent. These are client-validation hardening findings, **not evidence of authentication bypass**; any attempted login was intercepted, so backend email acceptance was not tested.

### 4. Login accessibility — P2

- **A11Y-001 / A11Y-002:** visible Email ID and Password labels are not programmatically associated with their inputs. The inputs rely on placeholders instead.
- **A11Y-003:** the reveal-password icon is a clickable non-button without a named keyboard-accessible button role.
- **A11Y-004:** empty-field errors are visible, but the input lacks the expected invalid/error association semantics.

**Recommended fixes:** associate labels using matching `for`/`id`; use a named `button type="button"` for password reveal; expose validation state and link error text with `aria-describedby`.

### 5. Pending login submission — passed in latest check

The strengthened RES-005 check held the first response and tested repeated Enter submissions. The latest single-in-flight-request assertion passed. The initial test had required a native disabled attribute; that visual implementation detail was replaced with the actual request-count contract.

## Observations requiring product confirmation

- Opening protected routes anonymously redirects to **/sign-in**, a phone-based login, rather than the supplied admin **/log-in** page. The final guard tests recognize both observed public authentication boundaries and still require protected tables to be absent. This is not reported as an access-control bypass. Confirm the intended admin re-entry experience.
- Exception Logs is visible in the menu, but the supplied account reaches **Access Denied!**. The suite records this as observed behavior, not a confirmed authorization defect. Confirm the role permission matrix.

## Execution history and corrections

The initial full run contained 47 passes and 42 failures. Many initial failures were **test assumptions**, not application defects: the guard expected only /log-in, while the application uses /sign-in. Those route expectations were corrected and the affected tests rerun. An initial empty-form navigation timeout was rerun. Login-error checks were scoped to the actual notification region, and the pending-submit check was strengthened to measure requests instead of only a disabled attribute.

2 runs are preserved in execution-results.json. Final counts use the latest result per unique test, not a claim that a second complete 89-test run was performed. The catalogue links each test to its source; earlier source line numbers may differ slightly after targeted test corrections.

## Delivered files

- **Playwright TypeScript suite:** specs, page helper, configuration, pinned dependencies and setup instructions.
- **test-cases.csv:** 89 executed cases with IDs, categories, preconditions, steps, expected/actual results and status.
- **extended-test-cases.csv:** 46 planned cases with explicit prerequisites and non-executed status.
- **execution-report.html:** standalone searchable results viewer.
- **execution-results.json:** sanitized result and network evidence.
- **evidence/login-validation.png:** anonymous required-field validation screenshot.

## Coverage limits

No business records were created, edited, deleted, published or exported. Login/logout may generate normal access/audit records. Credentials and session state are excluded from the delivery.

Full CRUD, uploaded-file validation, lower-privilege roles, cross-account isolation, rate limiting, real session expiry, finance/calculator correctness, concurrency and performance need disposable fixtures and acceptance criteria. Firefox/WebKit are configured but **not executed**. Responsive tests use Chromium viewport sizes, not physical mobile devices. There is no claim of exhaustive edge-case coverage or release certification.

**Recommended next step:** resolve the failed data requests, then run the suite again; supply approved fixture data and role accounts to implement the planned project-level cases.

# Gus Money (gusdev) - Users module automation

Target: https://gusdev.softwareco.com/users (Next.js admin; backend is reached via `/api/proxy` with an `x-target-endpoint` header).

## Setup
```bash
npm ci && npx playwright install chromium
pip install -r requirements.txt
cp .env.example .env     # then fill ADMIN_EMAIL / ADMIN_PASSWORD (gitignored)
```

## Run
| What | Command |
| --- | --- |
| UI tests (visible browser) | `npx playwright test --project=chromium --headed` |
| UI smoke only | `npx playwright test --project=chromium --grep @smoke` |
| API tests + coverage gate | `python -m pytest --cov=api --cov-fail-under=80` |
| HTML report | `npx playwright show-report` / `reports/api-report.html` |
| Allure | `ALLURE=1 npx playwright test` then `allure serve allure-results` |
| Simple UI for non-technical users | `python ui-runner/server.py` -> http://localhost:8765 |

## Layout
- `tests/auth.setup.ts` - logs in once, saves `.auth/admin.json` for all UI tests
- `pages/UsersPage.ts`, `tests/users.spec.ts` - USR-001..015 (positive, negative, boundary, security)
- `api/api_client.py` - reusable `APIClient`; `api/config.py` - env config; `api/tests/` - pytest
- `.github/workflows/qa.yml` - CI; fails on any test failure or API coverage < 80%

## Secrets
Credentials only in `.env` locally and GitHub Secrets (`ADMIN_EMAIL`, `ADMIN_PASSWORD`) in CI. `.env` and `.auth/` are gitignored. Do not commit real passwords; rotate the shared admin password if it was ever pasted into chat or tickets.

## Writing good cases
One behaviour per test, ID `USR-NNN`, role/label locators over CSS, no hard sleeps, and read-only on the shared dev data (do not create/delete users unless a test cleans up after itself).

## Known limits
- Tests are read-only; row actions (suspend/delete etc.) are only opened, not executed.
- Status filter option names were not asserted individually (only that options exist).
- API tests assume `/users` via the proxy returns 401/403 when unauthenticated; confirmed passing on dev on 2026-10-01.

---

# Loan Products module (added 2026-10-05)

Target: https://gusdev.softwareco.com/loan-products (list, `/new`, `/:id`, `/:id/edit`). API via `/api/proxy` -> `POST|GET|PUT|DELETE /products`.

## Files
- `tests/loan-products.spec.ts` + `pages/LoanProductsPage.ts` - 71 UI tests (LP-001..048). **All writes are intercepted**, so they never create/alter/delete data and use no server write quota. Rendering edge cases use mocked list data.
- `api/tests/test_loan_products_api.py` - 153 API tests. Core tier (`-m "not extended"`, 109 tests) + extended tier (`-m extended`, 44 tests).

## WRITE RATE LIMIT - read before running API tests
gusdev allows **100 write requests (POST/PUT/DELETE, including ones rejected with 422) per hour**. Reads are not limited. Hitting it returns 429 `RATE_LIMITED` with `retry-after` for up to an hour. What the limiter is keyed on (session, user or IP) is unverified, so other people on the dev environment may be blocked from writing too.
- Core tier uses about 90 writes: run it **at most once per hour**.
- Run `-m extended` in a different hour, never straight after core.
- Tests skip (not fail) on 429; `WRITE_BUDGET` (default 92) stops the run before the limit.
- All products the tests create are deleted at teardown (DELETE also counts as a write).

## Commands
```bash
WRITE_BUDGET=38 python -m pytest api/tests/test_loan_products_fees_concurrency.py -m extended -rxXs  # fees + races, 17 writes
python -m pytest api/tests/test_loan_products_api.py -m "not extended" -rxXs   # core, ~90 writes
python -m pytest api/tests/test_loan_products_api.py -m extended -rxXs         # extra cases, separate hour
npx playwright test tests/loan-products.spec.ts --project=chromium             # UI, no write quota
```

## Reading the results
`XFAIL` = known defect (reason carries the finding id, e.g. GUS-FX-0001). `XPASS(strict)` = it has been fixed: remove the marker. `pm(Qn)` = behaviour waiting for a product decision.

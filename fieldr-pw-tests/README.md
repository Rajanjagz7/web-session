# fieldr-pw-tests: FieldR release notes (Production, 6 October 2026)

Playwright + TypeScript (strict), Page Object Model. Every release-note bullet has an ID (`QUO-01`, `SEC-02`, `BUG-10a` ...) that starts the
test title and appears in `docs/traceability-matrix.md`. A bullet is either a live test or `test.fixme(true, 'reason: ...')` naming the missing
prerequisite. Nothing is skipped silently.

> **Status.** Written without access to the running app. It compiles under strict TypeScript and Playwright lists every test, but **no live test
> has been executed yet**. Locators are role / test-id / label based; unconfirmed accessible names and test-ids carry `TODO:` comments.
> Only the login page's locators come from a recorded accessibility tree.

## Layout

```
playwright.config.ts   tsconfig.json   package.json   .env.example   README.md
src/pages/      QuotesPage  JobBudgetPage  PortalPage  SchedulePage  RolesPage  CustomersPage  PickerPage
                SubscriptionPage  LoginAsPage  PdfPage  + BasePage, LoginPage, MiscPage (small shared areas)
src/fixtures/   auth.setup.ts (per-persona storageState)   data.fixture.ts (API seeding, unique names, cleanup)
src/lib/        pdf.ts (PDF download + parse + must-not-contain + blank pages)   env.ts   payloads.ts   a11y.ts
src/specs/      quotes  jobBudget  portal  schedule-roles  customers-pickers  subscription-billing  security-invites
                misc-improvements  bugs    (all *.spec.ts)
docs/traceability-matrix.md
```

`CustomersPage.ts` also holds the Invitations tab (it lives inside the Customer section), `JobBudgetPage.ts` holds the job Defects tab,
`LoginAsPage.ts` covers the platform admin console and Log In As, and `MiscPage.ts` holds job orders, user forms, insights and the date-time picker.

## Setup

```bash
npm install
npx playwright install chromium
cp .env.example .env          # then fill it in
npm run typecheck && npm run list
```

`.env`:
1. `BASE_URL`, `PORTAL_URL`, `ADMIN_URL`, `API_URL` (defaults are `*.example.invalid`, never real hosts).
2. `SERVICE_TOKEN`: used only by `data.fixture.ts` for seeding. Plus every `API_PATH_*` and `ROUTE_*` marked TODO.
3. Persona logins (mobile + bypass OTP), see below.
4. `EXPECTED_*`, `FIXTURE_*`, `PORTAL_*`: values the release notes do not state. A test that needs one is `test.fixme` until it is set.

## Persona generation

`src/fixtures/auth.setup.ts` runs once as the `setup` project: for each persona it signs in with `PERSONA_<NAME>_MOBILE` / `_OTP` and saves
`.auth/<persona>.json`. A persona with no credentials gets an empty state (the run continues and its tests fail visibly at login).

| Persona | Purpose |
| --- | --- |
| `cost-viewer` | sees sell and cost prices, margin, markup |
| `no-cost-viewer` | must NOT see them (UI, API, customer PDFs) |
| `no-permission` | must NOT see new affordances (New Role, Create Job, invites, Log In As); API returns 401/403 |
| `portal-customer` | customer portal (`PORTAL_URL`) |
| `super-admin` | admin console, Log In As, platform pages |

The phone field is pre-filled with `+61`: the setup types the digits after it (`fill()` would overwrite the prefix).

## Run

```bash
npx playwright test                                   # setup, then every persona project
npx playwright test --project=no-permission-chromium  # one persona
npx playwright test --grep @security                  # one area
npx playwright show-report
```

Projects: `cost-viewer-chromium`, `no-cost-viewer-chromium`, `no-permission-chromium`, `portal-customer-chromium`, `super-admin-chromium`.
Area tags: `@quotes @jobs @portal @schedule @roles @customers @pickers @billing @admin @security @invites @pdf @misc @insights @regression @manual`.
Traces on first retry; screenshots and video on failure; HTML report.

## Manual and partial items (one-line reasons)

| ID | Why |
| --- | --- |
| IPH-01..03 | MANUAL: App Store / TestFlight device; real payments on both rails |
| PA-02 | MANUAL: needs a wall-clock boundary; mock the clock (`page.clock`) at 23:59:50 or run a scheduled job near it |
| INV-06 | axe label checks are automated; screen-reader announcement and focus return are manual |
| SUB-01..03, SUBS-01..04, PA-04 | stub: need a billing sandbox with specific subscription states (cancelled, trial, resumed, yearly, one-off) |
| USR-02 | stub: Google Places needs stubbing with `page.route` (response shape unconfirmed) |
| CP-03 | stub: needs a dedicated portal login whose access can be revoked mid-session |
| CU-03d, CU-03f, ORD-02, INV-03, BUG-01, BUG-04, BUG-05b, BUG-06, BUG-08, BUG-09a, BUG-10a..d | stub: seed endpoint or expected value missing (reason in each test and in the matrix) |
| 25 partial IDs | live test with a named gap (exact amounts, formats, fixtures); see the Status column of the matrix |

## Conventions

- Locators: `getByRole`, then `getByTestId`, then `getByLabel`. The single raw `locator('form')` in `LoginPage` is marked fragile.
- No hard waits. Data is seeded through the API fixture with names from `Date.now()`; each seed returns the ids the test needs; tests are independent.
- Customer-facing artefacts must never contain `Cost Price`, `Margin %`, `Markup %` (`expectMustNotContain`, `PdfPage.expectCustomerSafe`).
- `personaApi()` in `src/lib/env.ts` assumes the API shares the app's origin and cookies. If tokens live in localStorage, change that one function.
- Tests are registered through Playwright's normal `test()`; the report groups by describe title and tag.

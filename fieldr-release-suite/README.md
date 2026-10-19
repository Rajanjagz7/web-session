# FieldR release-notes suite (Production, 6 October 2026)

Playwright + TypeScript, Page Object Model. Every bullet of the release notes has an ID (`QUO-01`, `SEC-02`, `BUG-07` ...) that appears in
the test title, and is either a **live test** or a `test.fixme(true, 'reason: ...')` that names the missing prerequisite. Nothing is skipped silently.

> **Status:** written without access to the running app. It compiles under strict TypeScript, the traceability check passes and
> Playwright lists all 107 tests, but **no live test has been executed yet**. Locators are role/label/test-id based and marked
> `TODO(confirm)` where the accessible name is unconfirmed (only the login page's locators were taken from a recorded accessibility tree).

## Layout

| Path | Purpose |
| --- | --- |
| `src/notes.ts` | Single source of truth: ID, area, persona, kind (live / fixme / manual), bullet text, reason |
| `src/specs/*.spec.ts` | Tests, one file per area group |
| `src/pages/*.ts` | Page objects and the picker / date-time components |
| `src/fixtures/api.ts` | API seeding client (service token), unique names, automatic cleanup |
| `src/fixtures/test.ts` | `live()`, `fixme()`, `manual()`, `needs()` helpers that bind a test to its note |
| `src/fixtures/auth.setup.ts` | Logs each persona in once and saves `.auth/<persona>.json` |
| `src/utils/pdf.ts` | PDF download through the request context, `pdf-parse` text, blank-page and **must-not-contain** checks |
| `src/utils/a11y.ts` | `@axe-core/playwright` label checks (screen-reader behaviour stays manual) |
| `src/config/env.ts`, `payloads.ts` | Every URL, route, API path and request-body key; all come from `.env` or are marked placeholders |
| `scripts/check-traceability.ts` | `npm run trace` fails if a bullet has no test of its declared kind |
| `scripts/build-matrix.ts` | `npm run matrix` writes `docs/traceability-matrix.md` |

## Setup

```bash
npm install
npx playwright install chromium
cp .env.example .env      # fill it in (see below)
npm run typecheck && npm run trace && npm run list
```

Fill in `.env`:
1. `BASE_URL`, `PORTAL_URL`, `ADMIN_URL`, `API_URL` (no real hosts are baked in; defaults are `*.example.invalid`).
2. `SERVICE_TOKEN` (used only by the seeding fixture, never by the browser) and every `API_PATH_*` / `ROUTE_*` marked TODO.
3. Five personas (mobile + bypass OTP each): `cost-viewer`, `no-cost-viewer`, `no-permission`, `portal-customer`, `super-admin`.
4. The `EXPECTED_*`, `FIXTURE_*` and `PORTAL_*` values (the release notes do not state them; a test whose value is blank turns itself into `fixme`).

## Run

```bash
npx playwright test                              # all personas (a setup project logs each in first)
npx playwright test --project=no-permission      # one persona
npx playwright test --grep @security             # one area (@quotes @budget @portal @schedule @roles @customers @subscription
                                                 #   @ios @loginas @pickers @jobs @joborders @users @datetime @phone @invites
                                                 #   @purchase @pdf @insights @platform @security @bugfix)
npx playwright show-report
```

One Playwright **project per persona**; a test runs in the project matching its `@persona` tag. Traces are kept on first retry; screenshots and video on failure.

## Conventions

- Locators: `getByRole` first, then `getByTestId`, then `getByLabel`. No CSS or XPath; the few fragile spots carry `// TODO: fragile` with the stable alternative (usually "ask dev for a test-id").
- No hard waits. The only bounded wait is PLT-01's `networkidle`, flagged to be replaced by a "loaded" test-id.
- Data: seeded through the API fixture with unique names (`rn-...`), cleaned up after each test. A few UI-created records (SCH-03 user) cannot be tracked and are listed in the test comment.
- Negative and permission tests are first-class: QUO-02, BUD-03, ROL-01, CUS-02, LIA-01, SEC-01/02/06/07 assert both the hidden control and the API refusal.
- Customer-facing artefacts must never contain `Cost Price`, `Margin %` or `Markup %` (`expectMustNotContain` in `src/utils/pdf.ts`).

## What is not automated

| Items | Why | Suggested handling |
| --- | --- | --- |
| IOS-01..03 | App Store / mobile, real payments | Manual on a TestFlight build; compare provider ledgers for IOS-03 |
| PLT-02 | Needs a wall-clock boundary | Mock the clock (`page.clock`) at 23:59:50 on the year boundary, or run a scheduled job near it |
| SUB-01..03, SBS-01, PUR-01..03, PLT-04 | Need a billing sandbox with specific subscription states | Seed sandbox companies, then replace the `fixme` |
| USR-02 | Google Places | Stub the Places response with `page.route` |
| CUS-03d/03f, BUG-01/04/05b/06/08/09a/10..13, INV-03, ORD-02, POR-03 | Missing seed endpoints or expected values | Reason is in `src/notes.ts` and the matrix |

Screen-reader behaviour (INV-06) stays manual; only the axe label checks are automated.

## Known limits of this first version

- The helper-based registration means Playwright's report shows the test location as `fixtures/test.ts`; use the describe/ID tags (or `docs/traceability-matrix.md`) to navigate, not the file tree.
- Several assertions are deliberately weaker than the real requirement until a value is confirmed (QUO-01 values, BUD-04 amount, INS-02 rounding proxy, CUS-04 "bold"); each says what to tighten in a `TODO`.
- `personaApi()` in `src/config/env.ts` assumes the API shares the app's origin and cookies; change that one function if tokens live in localStorage.

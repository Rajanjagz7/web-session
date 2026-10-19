# RebateM8 NSW - Pure Playwright QA suite (no test runner)

Same 76 test cases as the `@playwright/test` suite in `../1er-tests/tests-nsw-jobs/`
and the Python port in `../1er-tests-python/`, but written against the raw
`playwright` package directly - no `@playwright/test`, no `pytest`, just
`chromium.launch()` and a ~90-line custom harness (`runner.js`).

## Setup

```
npm install
npx playwright install chromium
```

Credentials/config live in `.env.nsw-jobs` (already filled in for the dev
environment).

## Run

```
node run.js                 # headed Chrome (default)
HEADED=0 node run.js        # headless
GREP=abn node run.js        # only tests whose name matches /abn/i
```

## How it works

- `runner.js` - `describe()`/`test()` collect tests into a list; `expect()`
  and `expectVisible`/`expectHaveCount`/etc. are minimal hand-rolled
  assertions that throw on failure.
- `run.js` - launches one browser, then for each collected test opens a
  fresh context + page (UI isolation) and a fresh API request context,
  runs the test function, and prints `ok`/`FAIL` with a final summary.
- `helpers.js` / `api-helpers.js` - same login/form-filling/navigation
  logic as the other two frameworks, ported to plain async functions.
- `tests/*.tests.js` - the actual test cases, one file per area:
  - `create-jobs.tests.js` - valid creation, invalid formats, negative/edge
    cases, special-character boundaries, additional edge cases,
    multi-product jobs (33 cases)
  - `auth.tests.js` - login (API + UI), OTP request/verify (7 cases)
  - `notes.tests.js` - note validation, visibility defaults incl. BUG-08
    (6 cases)
  - `soft-delete.tests.js` - delete -> trash -> restore lifecycle (3 cases)
  - `post-sign-editing.tests.js` - BUG-02 Save-doesn't-persist
    regressions, BUG-07 duplicate serial (4 cases)
  - `add-job-field-boundaries.tests.js` - per-field boundary/negative
    sweep, round 1 (12 cases)
  - `add-job-field-boundaries-2.tests.js` - per-field boundary/negative
    sweep, round 2 (12 cases)

# CRM QA suite

Automated API + UI tests for the CRM dashboard (`crm.staging.notbhavik.dev`), built from the manual deep-test session of 2026-10-01.

| Part | Tech | Where |
|---|---|---|
| API tests | Python, pytest, requests | `api/` |
| UI tests | Playwright (TypeScript): Chromium, Firefox, WebKit, mobile | `ui/` |
| Quality gates | Python | `scripts/check_gates.py` |
| Runner UI (non-technical users) | Python stdlib + one HTML page | `runner/` |
| CI | GitHub Actions | `.github/workflows/qa.yml` |

## 1. Set up (once)
```bash
cp .env.example .env            # then fill CRM_PROJECT_ID, CRM_EMAIL, CRM_PASSWORD
pip install -r api/requirements.txt
cd ui && npm install && npx playwright install chromium firefox webkit
```
Use a **dedicated test account and a project that is safe to write to**. The tests create and delete their own records
(pipelines, deals, contacts, companies, files, imports, exports) and restore the close-reasons list, but they do write.

## 2. Run
```bash
cd api && python -m pytest                       # all API tests  -> reports/api-report.html, api-junit.xml
cd api && python -m pytest -m "negative or boundary"
cd ui  && npx playwright test                    # all browsers   -> reports/ui-html/index.html, ui-junit.xml
cd ui  && npx playwright test --project=chromium --grep "\[security\]"
cd ui  && HEADED=1 npx playwright test --project=chromium     # watch it run
python scripts/check_gates.py                    # the CI quality gate, locally
```
**Non-technical users:** `python runner/server.py` and open http://127.0.0.1:8765. Pick a suite and case type, press Run,
watch the log, open the reports, edit settings. It listens on localhost only.

## 3. Test-case types
Every test name or marker says what kind of case it is, so you can filter (`-m` for pytest, `--grep "\[tag\]"` for UI):

| Marker | Meaning | Example |
|---|---|---|
| `positive` | the happy path works | create pipeline with stages |
| `negative` | invalid input or state is refused with the right error | duplicate stage name -> 400 |
| `boundary` | exact limits | name 120 vs 121 chars; 50 vs 51 stages; amount at 2^53-1 |
| `edge` | unusual but legal situations, concurrency | 3 parallel `won` calls -> one 200, two 409 |
| `security` | isolation, injection, auth | other project's ids return 404 |
| `known_bug` | documented defects, kept as **strict expected failures** | phone not validated |

**Known bugs:** a `known_bug` test asserts the *correct* behaviour and is marked expected-to-fail (`xfail` / `test.fail`).
It does not break the build today; the day the bug is fixed the test starts "unexpectedly passing", which **fails** the
build until you delete the marker. That keeps the bug list honest. The current list matches `crm-qa-findings.md`.

To add a case: copy a neighbouring test, use the fixtures (`client`, `pipeline`, `deal_factory`, `cleanup`, `uid`),
register everything you create with `cleanup.append(("resource", id))`, and add the marker.

## 4. Reports
- API: `reports/api-report.html` (self-contained), `reports/api-junit.xml`.
- UI: `reports/ui-html/index.html` with **screenshots, video and traces for failures**, `reports/ui-junit.xml`.
- Allure (optional): `pytest --alluredir=../allure-results` and `ALLURE=1 npx playwright test`, then `allure serve allure-results`.

## 5. CI/CD and quality gates
`.github/workflows/qa.yml` runs API, then UI, then a gate job (`scripts/check_gates.py`) on PRs, nightly and manually.
The gate fails the pipeline when:
- any executed test fails, or the pass rate is below `GATE_MIN_PASS_RATE` (default 100%);
- fewer than `GATE_MIN_TESTS` tests executed (a crashed or empty run must not look green);
- optionally, `--coverage-xml` line coverage is below `GATE_MIN_COVERAGE`.

These are black-box tests of a deployed app, so they **cannot measure the application's code coverage**. Use the coverage
gate only if you also run unit tests (or an instrumented build) of your own code and feed that Cobertura file in.
The workflow serialises runs (one shared staging project), so never run two suites against the same project at once.

## 6. Configuration and secrets
- Settings come from real environment variables first, then `.env`, then `.env.<CRM_ENV>` (e.g. `CRM_ENV=prod-like`).
- `.env` is git-ignored; never commit credentials. In CI use repository **secrets** (`CRM_EMAIL`, `CRM_PASSWORD`) and
  **variables** (`CRM_BASE_URL`, `CRM_PROJECT_ID`).
- The password is not printed (`Config.__repr__` hides it) and the runner UI can write it but never shows it again.
- Rotate the test account's password if it was ever pasted into chat, tickets or logs.

## 7. Best practices used here
1. Independent tests: each creates its own data with a unique suffix and cleans up (`cleanup` fixture / `afterAll`).
2. Assert the contract (status code **and** error message), not just "it failed".
3. Wait for rendered state (`h1` visible), not fixed sleeps; the UI is client-rendered.
4. One behaviour per test, named so a failure reads as a bug report.
5. Boundaries come in triples: below, at, above the limit.
6. Engine quirks are handled explicitly and commented (WebKit does not focus clicked buttons).

## 7b. Known limits of this suite
- Member-role / permission tests need a second account (not included yet).
- Export file *download* is covered at the API (metadata); the browser download itself was checked manually.
- Screen-reader behaviour is only approximated by structural a11y checks; run NVDA/VoiceOver for real coverage.
- The login endpoint is CSRF-protected (same-origin); the API client presents the app's own origin header when logging in.

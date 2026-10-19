# Projects Catalogue

Workspace: `Downloads/Automation` · Generated 2026-10-09 from folder contents (READMEs, package.json, file listings).
Items marked *(inferred)* were deduced from file names, not from a README.

## Summary

| # | Project | Domain | Stack | Type |
|---|---|---|---|---|
| 1 | fieldr-qa | Fieldr (field ops) | Python, CSV/MD | Manual QA, API tests, bug reports, handover |
| 2 | fieldr-playwright | Fieldr | Playwright + TS, POM | E2E automation |
| 3 | fieldr-pw-tests | Fieldr | Playwright + TS, POM | Release-notes tests (6 Oct 2026) |
| 4 | fieldr-release-suite | Fieldr | Playwright + TS, POM | Release-notes tests, 107 tests |
| 5 | fieldr | Fieldr | Node, HTML | Field-operations web app prototype |
| 6 | 1er-tests | RebateM8 NSW | Playwright + TS | E2E automation (main suite) |
| 7 | 1er-tests-python | RebateM8 NSW | Python, pytest, Playwright | Port of 1er-tests (64 cases) |
| 8 | 1er-tests-pure-playwright | RebateM8 NSW | Raw Playwright, custom runner | Port (76 cases) |
| 9 | 1er-tests-pure-puppeteer | RebateM8 NSW | Raw Puppeteer | Job-creation scripts |
| 10 | nsw-qa | RebateM8 NSW | Python, JSON, MD/CSV | Bug reports, API audits |
| 11 | rebatem8-tests | RebateM8 NSW | Playwright + TS | E2E tests |
| 12 | rebatem8-playwright-qa | RebateM8 | Playwright, Bun | Test report, coverage gaps, portfolio |
| 13 | crm | CRM dashboard | Python pytest + Playwright TS | API + UI suite, bug report |
| 14 | crm-qa-suite | CRM dashboard | Python pytest + Playwright TS | Earlier version of `crm` |
| 15 | gus-money | Gus Money admin | Playwright, pytest | E2E, test plans, bug lists |
| 16 | STC | STC | Python | Python test scaffold |
| 17 | stc-security-tests | STC Security | Playwright + TS | Sprint 1 auth/user tests |
| 18 | clinic1 | Clinic / membership | Playwright JS + pytest | Membership, timezone tests |
| 19 | ozmed automation | OzMed | Python | Appointment scripts, test cases |
| 20 | ozmed-tests | OzMed | Python, Playwright | Billing, appointments, telehealth |
| 21 | support-x | Support X | Playwright JS | QA docs + automation |
| 22 | saucedemo-e2e-tests | Sauce Demo | Playwright + TS, POM | E2E |
| 23 | saucedemo-advanced-e2e | Sauce Demo + FakeStoreAPI | Playwright + TS, Docker | 8-layer framework |
| 24 | playwright-tests | ZeroGap | Playwright + TS, Capacitor | Cross-browser tests |
| 25 | shopify-mobile-tests | ZeroGap | Playwright + TS | Mobile tests |
| 26 | weight-plate-web | Weight Plate | Playwright + TS | E2E |
| 27 | cart-automation | E-commerce | Python | Add-to-cart script |
| 28 | ai-api-testing | Claude API | Python, pytest | Functional, security, eval, load tests |
| 29 | jmeter | Load testing | JMeter | FakeStoreAPI and newsunrise plans |
| 30 | qa-mastery | Learning | Playwright TS, Python | Course exercises |
| 31 | learn_playwright | Learning | Python | Four tutorial scripts |
| 32 | rajan | Trading | Node, Python, Vercel | NSE option scanner |
| 33 | rajan1 | Trading | Python | Live NSE scanner and indicators |
| 34 | organized | Portfolio | HTML/CSS/JS | Portfolio site of the above |
| 35 | scratch | Trading | Python | Live API checks |
| 36 | NewSunRise | NewSunRise app | Postman, JMeter | API collection + stress-test plan |

---

## 1. Fieldr (field operations platform)

### fieldr-qa
- **Purpose:** Manual and API QA for Fieldr dev tenant `rajanjagz7.dev.fieldr.app`.
- **Contents:** handover, master prompt, security API report, edge-case findings, auth and API test cases, bug lists (customers/jobs release 2026-10-07), timesheet and job-report data, CSV folder, Python job-report script.
- **Status:** handover dated 2026-09-19. Seeded about 101 customers, 277 jobs, 180 invoices, 101 quotes. 50 Playwright specs generated (FLD-AUTH-001 to 050) but not installed or run. User-creation via API and timesheet filling unfinished.
- **Files:** 373 · **Last change:** 2026-10-07

### fieldr-playwright
- **Purpose:** E2E suite for Fieldr Web App (`c1.dev.fieldr.app`).
- **Stack:** Playwright, TypeScript, Page Object Model.
- **Note:** also holds loose `rajan_*.mjs` exploration scripts (crawl, diag, login, OTP check).
- **Files:** 70 · **Last change:** 2026-10-07

### fieldr-pw-tests
- **Purpose:** Tests generated from FieldR production release notes, 6 Oct 2026. Each bullet has an ID (QUO-01, SEC-02, BUG-10a) tied to a traceability matrix.
- **Stack:** Playwright, strict TypeScript, POM.
- **Status:** compiles and lists all tests, but **no live run yet**. Unconfirmed locators carry `TODO:` comments.
- **Files:** 38

### fieldr-release-suite
- **Purpose:** Same release-notes basis as fieldr-pw-tests, with a traceability check script.
- **Stack:** Playwright, TypeScript, POM. 107 tests listed.
- **Status:** **no live run yet.**
- **Files:** 49
- **Overlap:** appears to be a larger version of fieldr-pw-tests; confirm which is current.

### fieldr
- **Purpose:** Fieldr web app for job scheduling, dispatch, technician tracking and client management.
- **Stack:** Node, `index.html`, `src/`, `scripts/`. Also holds QA master prompts.
- **Files:** 15 · **Last change:** 2026-10-09

## 2. RebateM8 / 1st Energy Rebate (NSW)

Staging: `nswstage.rebatem8.com.au`.

### 1er-tests
- **Purpose:** Main Playwright suite for NSW jobs: add job form, energy saver nomination, site assessor declaration, workflow scripts.
- **Stack:** Playwright, `playwright.config.ts`. Many ad-hoc debug scripts and screenshots.
- **Files:** 325 · **Last change:** 2026-09-22

### 1er-tests-python
- **Purpose:** Python/pytest port of the TypeScript suite, 64 cases, same helpers and known-bug notes.
- **Run:** `pip install -r requirements.txt`, then `pytest`.

### 1er-tests-pure-playwright
- **Purpose:** Same 76 cases on raw `playwright` with a roughly 90-line custom runner (`runner.js`). Includes email edge-case and concurrency scripts.

### 1er-tests-pure-puppeteer
- **Purpose:** Job creation using raw Puppeteer. Small (8 files).

### nsw-qa
- **Purpose:** Bug tracking and API audit for staging.
- **Contents:** `NSW_BUGS.md/.csv` (60 tracked, 54 open, 6 fixed; regression 30 Sep 2026), `NSW_BUG_REPORT.md`, `api_inventory.json/.py`, audit scripts, screenshots.
- **Notable defects:** dashboard, projects and invoices APIs returning 404.
- **Files:** 226 · **Last change:** 2026-09-30

### rebatem8-tests
- **Purpose:** `rebatem8-nsw-tests`, Playwright test suite.

### rebatem8-playwright-qa
- **Contents:** `rebatem8-playwright/` (README, TEST-REPORT, coverage-gaps, execution report HTML/JSON, extended test cases CSV), `portfolio/`, skills bundle.

## 3. CRM dashboard (`crm.staging.notbhavik.dev`)

### crm
- **Purpose:** API + UI automation and bug report from the manual deep-test session of 2026-10-01.
- **Stack:** API in Python, pytest, requests. UI in Playwright TypeScript (Chromium, Firefox, WebKit, mobile).
- **Contents:** api, ui, audit, docs, fixtures, report(s), runner, scripts.
- **Files:** 284 · **Last change:** 2026-10-09

### crm-qa-suite
- **Purpose:** Earlier or duplicate copy of `crm` (same README text). Last change 2026-10-01 vs 2026-10-09 for `crm`.
- **Files:** 58
- **Suggestion:** treat `crm` as the source of truth and archive this one.

## 4. Gus Money / STC

### gus-money
- **Purpose:** Playwright E2E framework and test plans for the Gus Money Admin Panel.
- **Modules:** auth, dashboard and analytics, user and customer management, loan products.
- **Contents:** eligibility test plan, loan products QA report, bug lists v3 to v6 (2026-10-06/07), API tests, stage data-copy scripts.
- **Files:** 81 · **Last change:** 2026-10-09

### STC
- **Purpose:** Python scaffold. README is just setup steps; `tests/` is empty.
- **Files:** 6

### stc-security-tests
- **Purpose:** Playwright suite for STC Security Sprint 1 (authentication and user management) plus a Gus Money sanity check.

## 5. Healthcare

### clinic1
- **Purpose:** Test suite `clinic1-tests` for a clinic app: membership coverage, timezone behaviour, edge and negative cases.
- **Stack:** Playwright (JS) and pytest.
- **Docs:** QA test plan for membership coverage, edge cases and negative tests, timezone findings and walkthrough.
- **Files:** 132 · **Last change:** 2026-10-08

### ozmed automation
- **Purpose:** OzMed appointment and billing scripts *(inferred)*: create appointments, long-duration and telehealth appointments, Tyro QA test cases, deal sequence analysis, practitioner appointment-type test cases.
- **Stack:** Python. 34 files.

### ozmed-tests
- **Purpose:** Python Playwright scripts for billing, appointment creation and telehealth. 3 files.

## 6. Other web app QA

### support-x
- **Purpose:** QA for Support X: release notes, test plan, test cases, bug reports, automation.
- **Stack:** Playwright (JS) with auth setup. Folders `docs/`, `tests/`, `test-data/`.

### playwright-tests (ZeroGap)
- **Purpose:** `zerogap-cross-browser-tests`, cross-browser tests with a Capacitor/Android folder.

### shopify-mobile-tests (ZeroGap)
- **Purpose:** `zerogap-mobile-tests`, mobile Playwright tests with global setup.

### weight-plate-web
- **Purpose:** Playwright E2E tests for the Weight Plate web app.

## 7. Practice and framework projects

### saucedemo-e2e-tests
- **Purpose:** Playwright E2E for saucedemo.com. TypeScript, POM, fixtures, utils.

### saucedemo-advanced-e2e
- **Purpose:** 8-layer framework covering Sauce Demo UI and FakeStoreAPI. Dockerfile and docker-compose included.

### cart-automation
- **Purpose:** Python add-to-cart script with debug steps. 4 files.

### ai-api-testing
- **Purpose:** pytest scaffold against the live Anthropic Messages API: functional, security/injection, regression/eval, load/concurrency.

### jmeter
- **Purpose:** Load testing. Plans: `fakestoreapi-load-test.jmx` (login, browse, cart, orders) and `newsunrise-stress-test.jmx`. Run non-GUI via `scripts/run-load-test.ps1`.

### qa-mastery
- **Purpose:** Learning workspace. `01-playwright-ts` has content; `02-ai-evals-py` is empty.

### learn_playwright
- **Purpose:** Four tutorial scripts: first script, locators and forms, live interactive controls, pytest-playwright.

## 8. Trading and finance

### rajan
- **Purpose:** NSE Bhavcopy and live option scanner for F&O options. Deployed on Vercel.
- **Stack:** Node (`api/`, `public/`), Python, batch files for scheduled scans. Has AGENTS.md and GEMINI.md.

### rajan1
- **Purpose:** Python live-NSE-data scanner, with indicators (Heikin Ashi, Donchian, quantum matrix, dancing trend), market news and a data cache.
- **Recent commits:** bhavcopy dependency removed (live data only); alias `rajan-algo.vercel.app`.
- **Note:** its README is empty.
- **Related loose files:** `top50_block_deal_scanner.pine`, `run_scanner.bat`, `indicator.md`.

### scratch
- **Purpose:** Python live API and parallel-fetch checks for the trading project.

## 9. NewSunRise

### NewSunRise.json
- **Purpose:** Postman v2.1 collection (~600 KB) for the NewSunRise API; folders include Loyalty-card (e.g. loyaltyCardValidate). Last change 2025-08-14.
- **Related:** `jmeter/test-plans/newsunrise-stress-test.jmx` (stress test) and the git branch `newsunrise` of this repo.
- **Screenshots:** app screenshots (com.newsunrise) sit outside the workspace in `Downloads/new sunrise all/`.

## 10. Portfolio

### organized
- **Purpose:** "Rajan's Engineering Portfolio", a structured mirror of the projects above.
- **Contents:** `projects/{apps, test-suites, trading-finance, web-apps}`, `site/`, `docs/` (static HTML/CSS/JS site, learnings, skills), `scripts/`, LICENSE.

---

## Root-level files (not in a project folder)

| Kind | Files |
|---|---|
| Test case sheets | `1st_Energy_Rebate_TestCases*.xlsx`, `RebateM8_*_TestCases.xlsx`, `1ER_Test_Execution_Results_2026-08-20.xlsx`, `AddJob_TestCases.csv`, `ZeroGap_*.csv` |
| Documentation | `NSW_DOCUMENTATION.md`, `NSW_BACKEND_FLOW*.md`, `MODULES.md`, `MEMBERSHIP_BILLING_CYCLES_REPORT_QA.md`, `QA_*.md`, `reports-module-*.md`, `crm-qa-findings.md`, `brd.docx`, OzMed handover docx |
| Claude skills | `*.skill`, `SKILL.md`, `qa-skills-bundle.zip`, `skills-export.zip` |
| Backups and archives | many `.zip` files (project backups, test data, chrome-devtools-mcp) |
| One-off scripts | `explore_*.mjs` (signup/cart exploration), `pmx_add_*.py`, `genai_example.py` |
| Prototypes | `op.html`, `prototype.html`, `ui.html` |

## Observations

- **Duplicates:** `crm` vs `crm-qa-suite`; `fieldr-pw-tests` vs `fieldr-release-suite`; four implementations of the same NSW suite (TS, Python, raw Playwright, Puppeteer).
- **Unrun suites:** both Fieldr release-notes suites have never been run live.
- **Thin projects:** `STC` (empty tests), `qa-mastery/02-ai-evals-py` (empty), `rajan1` (empty README).
- **Clutter:** `1er-tests` and `nsw-qa` hold many debug scripts and screenshots at top level.

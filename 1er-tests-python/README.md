# RebateM8 NSW - Python/Playwright QA suite

Python port of the TypeScript suite in `../1er-tests/tests-nsw-jobs/`. Same
64 test cases, same helpers, same known-bug documentation - just pytest +
Playwright's Python API instead of `@playwright/test`.

## Setup

```
pip install -r requirements.txt
playwright install chromium
```

Credentials/config live in `.env.nsw-jobs` (already filled in for the dev
environment).

## Run

```
pytest                              # headless, all tests
pytest --headed                     # visible Chrome
pytest --headed --slowmo 300        # visible + slowed down
pytest tests/test_create_jobs.py    # one file
pytest -k "abn"                     # tests matching a keyword
```

## Files

- `config.py` - loads `.env.nsw-jobs`, exposes `BASE_URL`/`EMAIL`/`PASSWORD`/`INSTALLER_COMPANY`
- `conftest.py` - wires `base_url` into pytest-playwright's `page`/`context` fixtures, adds an `api_context` fixture for API-only tests
- `helpers.py` - UI helpers: login, Add Job drawer, react-select scoping, form filling, product blocks, job-detail navigation
- `api_helpers.py` - `login_api`, `to_json`
- `tests/test_create_jobs.py` - valid job creation, invalid formats, negative/edge cases, special-character boundaries, additional edge cases, multi-product jobs (33 cases)
- `tests/test_auth.py` - admin login (API + UI), OTP request/verify (7 cases)
- `tests/test_notes.py` - note validation, visibility defaults incl. BUG-08 (6 cases)
- `tests/test_soft_delete.py` - delete -> trash -> restore lifecycle (3 cases)
- `tests/test_post_sign_editing.py` - BUG-02 Save-doesn't-persist regressions, BUG-07 duplicate serial (4 cases)
- `tests/test_add_job_field_boundaries.py` - per-field boundary/negative sweep (12 cases)

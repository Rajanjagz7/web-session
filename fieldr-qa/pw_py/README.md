# Fieldr Playwright Python suite

`pytest-playwright` specs covering the flows explored manually earlier in the QA sessions
(`../HANDOVER.md`, `../CRASH_CHECK_2026-09-21.md`, `../FLOW_WALKTHROUGH_2026-09-21.md`,
`../SECURITY_EDGE_CASE_FINDINGS_2026-09-21.md`), turned into real, re-runnable code.

## Setup
```bash
cd pw_py
pip install -r requirements.txt
playwright install chromium   # once, if not already installed
cp .env.example .env          # fill in your own values if different
```

## Running
```bash
pytest                        # everything
pytest tests/test_quote_flow.py
pytest -k "cms"
```

The first run logs in with a real email OTP (one request) and caches the session to
`.auth/state.json`. Every later run reuses that cached session — **no more OTP requests** — until it
expires, at which point the suite deletes the stale cache and tells you to re-run once.

## Layout
- `conftest.py` — the `logged_in_page` fixture every test uses, plus a screenshot-on-failure hook
  (saved to `screenshots/`).
- `pages/` — page objects (Page Object Model), one per screen.
- `utils/config.py`, `utils/auth.py` — env config and the login/session-cache logic.
- `utils/au_data.py`, `utils/cms_content.py` — Australian test-data generators.
- `tests/` — the specs themselves.

## Results as of 2026-09-21 (25 passed, 1 known-flaky, 1 skipped)

| File | Covers | Status |
|---|---|---|
| `test_smoke.py` | Login + dashboard render | Pass |
| `test_cms_other_types.py` | CMS Type dropdown (finding: only "FAQ" is offered), Title length boundaries (3–35 chars), full FAQ create | Pass |
| `test_quote_flow.py` | Add Quote: incomplete-section validation, full create with a line item | Pass |
| `test_report_flow.py` | Add Report (Job Report submission): empty-form validation, full Site Safety Inspection Report submit | Pass |
| `test_remaining_modules.py` | Activity Logs, Notifications, Schedule, Job Report list, all 10 Settings tabs, activity-log search | 15 pass, 1 skip (no search box), 1 fails intentionally |

**Known-flaky, left failing on purpose:** `test_settings_tab_loads_cleanly[chromium-Roles & Permissions]`.
Across three runs, the same account and URL rendered three different things: real content, a
"Not included in your plan" upsell, and a page that never loads (the failure this test currently
catches). That's a genuine intermittent bug in the app, not a test problem — see the test's docstring.
Don't "fix" this test to pass; if it starts passing consistently, that means the app's behaviour
changed and the docstring should be updated to say so.

## What's still not covered
- Schedule: page loads cleanly, but no event was opened/dragged/reassigned.
- Job workflow specifics (checklist item, gallery, notes) — confirmed working via API in the
  September sessions, not yet driven through the UI here.
- Chat, Feed, Report Builder editor — covered in the earlier Node/Playwright session
  (see `../FLOW_WALKTHROUGH_2026-09-21.md`), not ported to this Python suite.
- Subscription: read-only. No checkout, add-on toggle, or real seat purchase is exercised (see
  `../SECURITY_EDGE_CASE_FINDINGS_2026-09-21.md` section 3 for why, and the boundary values already
  found on the seat-quantity field).

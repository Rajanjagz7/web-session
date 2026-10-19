# CRM staging QA findings

Environment: https://crm.staging.notbhavik.dev, project "Vercel 3" (6abe377f6194a264a524b653), tested 2026-10-01 as rajanj@softwareco.com (workspace owner).
Method: UI in Chromium (desktop 1280px and mobile 375px) plus direct API calls (`/api/crm/v1`) using the dashboard session.

## Summary
- No security issues found. Tenant isolation, session enforcement, XSS handling, SQL-style input, upload restrictions and delete guards all held.
- 6 validation gaps, 3 accessibility issues, 4 design questions, 6 minor items.
- Not tested: Member role (only one user exists), Firefox/Safari, real screen readers, export expiry after 7 days.

## Bugs / validation gaps (worth fixing)
| # | Area | Finding | Repro | Suggested fix |
|---|------|---------|-------|---------------|
| 1 | Contacts | Phone is not validated | POST /contacts `{firstName:"T", phone:"abc"}` -> 201 (also "1", 40 digits) | Validate or normalise to E.164 |
| 2 | Companies | Phone and domain not validated | POST /companies `{name:"x", phone:"xyz", domain:"not a domain"}` -> 201; domain `https://example.com/path` stored as-is, `EXAMPLE.com` not lowercased | Validate hostname, lowercase, strip scheme/path |
| 3 | Contacts | Whitespace-only first name accepted | POST /contacts `{firstName:"  "}` -> 201 (pipeline names are trimmed and rejected) | Trim, then require min length 1 |
| 4 | Contacts | `ownerActorId` not checked | POST /contacts `{firstName:"T", ownerActorId:"nope"}` -> 201; shows as an owner in `contacts.by_owner` | Verify the actor exists in the workspace |
| 5 | Contacts/Companies | Inconsistent length limits | Company name 300 chars -> 201; contact name max 200; pipeline name max 120; 300-char email accepted (RFC max 254) | Align limits per field; cap email at 254 |
| 6 | All | Page title is "CRM Dashboard" on every page | Open any two pages | Set a unique `<title>` per route (WCAG 2.4.2) |

## Round 2 findings ("break it" session, 2026-10-01, evening)
New bugs and hardening gaps. Every one of them is now a strict-xfail regression test in `crm-qa-suite` (`api/tests/test_robustness.py`, `ui/tests/pipelines.spec.ts`).

| # | Severity | Area | Finding | Repro |
|---|---|---|---|---|
| 7 | Medium | Search (contacts, companies, deals, files) | **A null byte in the search query returns HTTP 500** (internal_error). Other special characters (`%`, `\`, `(`, `[`, `*`, `$`, quotes, newlines, U+FFFD) are fine. | `GET /contacts?q=a%00b` |
| 8 | Medium | Session handling (UI) | **Expired session on submit shows a raw API message and leaves the dialog open.** The New pipeline dialog shows "A secret API key or Dashboard session is required" with no sign-in prompt and no redirect; the draft is lost on reload. A normal page load does redirect to `/login?next=...` correctly. | Open New pipeline, clear cookies, press Create |
| 9 | Low | Proxy / API | **Intermittent empty 502 on oversized bodies** (about 1 in 5 at 10 MB); the correct response is 413 and usually arrives. Body limit sits between 1 and 2 MB. | POST a 10 MB JSON body repeatedly |
| 10 | Low | HTTP | `TRACE` returns a bare 500 (plain-text "Internal Server Error", not the JSON error format). Should be 405/404. | `TRACE /api/crm/v1/pipelines` |
| 11 | Low | Hardening | `Content-Type: text/plain` is parsed as JSON. Browsers send `text/plain` cross-site without a CORS preflight; today the required `crm-*` headers still force a preflight, so this is defence in depth only. Mutating calls with a session cookie and no `Origin` header are also accepted (login is same-origin protected). | POST `{"name":...}` with `content-type: text/plain` -> 201 |
| 12 | Low | Input validation | Control characters are accepted in names: NUL (`\x00`), newlines, CRLF, `\x01`. They are stored verbatim and can surprise logs, CSV and downstream tools. (The UI renders them safely.) | `POST /pipelines {"name":"a\u0000b",...}` -> 201 |
| 13 | Low | Input validation | Invalid UTF-8 bytes are accepted and silently replaced with U+FFFD instead of being rejected. A lone surrogate becomes 3 replacement characters. | POST body containing raw bytes `\xff\xfe` -> 201 |
| 14 | Low | Input validation | The 120-character name limit counts UTF-16 units, so 100 emoji (200 units) are refused as "too big". Similar for other astral characters. | `POST /pipelines` with `"name":"😀"*100` -> 400 |

### Round 2: held up well
- **Pagination:** cursors are signed and bound to the resource and the project. Truncated, flipped-byte, oversized, non-base64, null-byte, SQL-shaped, cross-resource and cross-project cursors all return a clean 400. Walks at limit 1/7/25/100 return every record exactly once. The parameter is `starting_after`.
- **Body parsing:** arrays, strings, numbers, `null`, 2,000-level nesting, trailing garbage, `NaN`, duplicate keys (last wins), `__proto__` / `constructor` keys all give clean 400s or ordinary handling; no crash.
- **IDs:** `%00`, `..`, `-1`, `1e5`, `null`, `undefined`, `[object Object]`, NoSQL-operator JSON, 5,000-character IDs never produced a 5xx.
- **Open redirect:** `?next=` with `//host`, `https://host`, `/\host`, `javascript:`, encoded variants never leaves the site; only same-site relative paths are followed.
- **XSS through the URL:** payloads in query strings, hash, project and workspace path segments are never reflected into the DOM; no script ran.
- **Layout under hostile names:** a 120-character unbroken name, 60 emoji, zero-width characters, RTL-override (`‮`) and HTML-looking names caused no horizontal overflow on desktop or at 375px. RTL-override text is bidi-isolated (no spoofing of the visible order).
- **Resilience:** offline submit keeps the draft and says "Could not reach the Platform"; retrying creates exactly one record. Acting on a record deleted in another tab shows "Pipeline not found" and the page stays usable. Unauthenticated deep links (valid, unknown and malformed ids) redirect to `/login?next=...`.

## Accessibility
- Same page title everywhere (see #6).
- Heading levels skip h1 -> h3 on Reports, Automation, Outbox, Products, My work.
- One unlabelled form field on the Files page.
- Good: New pipeline dialog has aria-modal, a label, trapped focus, and returns focus on close. Keyboard-only create (type, Tab, Enter) works.

## Design questions (decide whether intended)
1. Duplicates allowed for pipelines (case-insensitive too), contacts (same email, any case), companies, and close-reason labels. Parallel creates of the same pipeline name made 3 copies. Stage names ARE unique per pipeline.
2. Stages can be added to an archived pipeline, although the page says an archived pipeline "takes no new deals".
3. Import `onDuplicate` supports only `create` (default) and `reject`; no update or skip, so contacts can't be corrected by re-import.
4. Pipeline DELETE is a hard delete (guarded: blocked with 409 if any deal exists, open or closed).

## Minor
- Stage `order` has gaps after a delete (e.g. remaining stage shows order 2) until the next reorder.
- Moving a deal to the stage it is already in returns 200 (no-op).
- Escape closes the New pipeline dialog without a discard warning.
- Unknown `Crm-Org-Id` header value is accepted silently.
- Mobile (375px): table cells truncate ("Enterpri...", "Oct 1, 2..."). No horizontal page scroll.
- Archiving a company that has contacts and deals is allowed (design call).

## Passed (highlights)
- Delete guards: stage with open deals, pipeline with deals, company with references, last active stage -> 409.
- Deal state machine: won/lost/reopen transitions, closed deals can't move or close twice; 3 parallel `won` calls -> one 200, two 409.
- Close reasons: outcome-specific, exact-code match, code format, 50-reason cap, duplicate code rejected; a deal keeps its reason after the reason is removed.
- Money: integer minor units, no negatives, max safe integer, ISO uppercase currency.
- Isolation: other projects' records return 404 for read/patch/delete; no session -> 401; bad/missing project header -> 403/400.
- Input handling: XSS payloads stored and rendered as text; SQL/regex search strings harmless; unknown fields, wrong types, malformed JSON -> clean 400.
- Uploads: presigned S3 flow works; type allowlist and 25 MB cap enforced; filename with `../` is only a label (ID-based key).
- Imports: 1,500 rows OK; BOM, CRLF, quoted commas/newlines, unicode OK; per-row errors accurate; bad headers/empty/ragged files rejected with clear messages; `reject` mode blocks duplicates.
- Exports: CSV with BOM, correct quoting; formula cells (`=`, `+`, `-`, `@`) prefixed with `'` and stripped again on re-import (lossless round trip).
- Reports: all 8 reconcile with seeded data; bad dates/ranges/ids return clean 4xx.
- UI: double-click on Create makes one pipeline; Enter submits.

## Open items
1. Member role permissions (needs a second user).
2. Firefox / Safari.
3. Real screen reader pass (NVDA, VoiceOver).
4. Export availability after 7 days.

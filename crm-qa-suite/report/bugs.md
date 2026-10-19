# CRM staging bug report

Environment: https://crm.staging.notbhavik.dev (staging)  |  Project: Vercel 3 (6abe377f6194a264a524b653)  |  Date: 1 Oct 2026

Scope: Pipelines, Deals, Contacts, Companies, Close reasons, Files, Imports, Exports, Reports, auth and tenant isolation; UI in Chromium, Firefox, WebKit and mobile (375 px).

Method: Manual exploration plus over 200 automated checks (pytest for the API, Playwright for the UI), then fuzzing of bodies, IDs, queries, cursors and encodings. Test data was created and removed by the tests.

**20 bugs** (2 medium, 18 low): 13 backend, 6 frontend, 1 hardening. No critical or high severity and no data-exposure issue was found.

## Bugs

### BUG-01 [Medium] A null byte in the search query returns HTTP 500
- **Layer:** Backend  |  **Area:** Search (contacts, companies, deals, files)
- **Steps / request:** GET /api/crm/v1/contacts?q=a%00b   (same on /companies, /deals, /files)
- **Expected:** 400 validation error, or the search ignores the character.
- **Actual:** 500 internal_error. Other special characters (% \ ( [ * $ quotes, newlines) are handled fine. The UI search box would show a generic failure.
- **Suggested fix:** Strip or reject U+0000 in query-string params before they reach the database layer.

### BUG-02 [Medium] Expired session on submit shows a raw API message and leaves the dialog open
- **Layer:** Frontend  |  **Area:** Session handling
- **Steps / request:** Sign in, open Pipelines > New pipeline, fill the form, clear cookies (or let the session expire), press Create pipeline.
- **Expected:** Redirect to /login?next=... or a clear 'Your session expired, sign in again' message that keeps the draft.
- **Actual:** Dialog stays open and shows 'A secret API key or Dashboard session is required' (developer wording). No sign-in prompt. Reloading goes to the login page and the draft is lost. A normal page load redirects correctly.
- **Suggested fix:** Handle 401 from the API client centrally: redirect to login with next=, and show a user-facing message.

### BUG-03 [Low] Contact phone number is not validated
- **Layer:** Backend  |  **Area:** Contacts
- **Steps / request:** POST /contacts {"firstName":"T","phone":"abc"}  (also "1" and a 40-digit string)
- **Expected:** 400 for values that are not phone numbers (or normalise to E.164).
- **Actual:** 201, stored as entered.
- **Suggested fix:** Validate and normalise phone numbers.

### BUG-04 [Low] Company phone and domain are not validated or normalised
- **Layer:** Backend  |  **Area:** Companies
- **Steps / request:** POST /companies {"name":"x","phone":"xyz","domain":"not a domain"}   also domain "https://example.com/path" and "EXAMPLE.com"
- **Expected:** 400 for invalid values; domain stored as a lower-case hostname.
- **Actual:** 201. 'not a domain' and a full URL are stored verbatim; 'EXAMPLE.com' keeps its case (contact emails are lower-cased).
- **Suggested fix:** Validate hostname, strip scheme and path, lower-case; validate phone as above.

### BUG-05 [Low] Whitespace-only first name is accepted
- **Layer:** Backend  |  **Area:** Contacts
- **Steps / request:** POST /contacts {"firstName":"   "}
- **Expected:** 400, as for an empty name (pipeline names are trimmed and rejected).
- **Actual:** 201 with a blank-looking contact.
- **Suggested fix:** Trim, then require at least 1 character.

### BUG-06 [Low] ownerActorId is not checked against real users
- **Layer:** Backend  |  **Area:** Contacts
- **Steps / request:** POST /contacts {"firstName":"T","ownerActorId":"nope"}
- **Expected:** 400/404 when the user does not exist in the workspace.
- **Actual:** 201. 'nope' then appears as an owner in the contacts.by_owner report.
- **Suggested fix:** Verify the actor exists and is a member of the workspace.

### BUG-07 [Low] Inconsistent field length limits
- **Layer:** Backend  |  **Area:** Contacts, Companies
- **Steps / request:** POST /companies with a 300-character name; POST /contacts with a 300-character email.
- **Expected:** Limits consistent with the rest of the API (pipeline name 120, contact name 200) and email at most 254.
- **Actual:** Company name has no practical limit (300 accepted); a 300-character email is accepted (RFC limit is 254).
- **Suggested fix:** Set explicit maximums on every string field.

### BUG-08 [Low] Control characters are accepted and stored in names
- **Layer:** Backend  |  **Area:** All string fields
- **Steps / request:** POST /pipelines {"name":"a\u0000b","stages":[{"name":"s"}]}   also "\n", "\r\nX-Evil: 1", "\u0001"
- **Expected:** 400 for control characters in single-line fields.
- **Actual:** 201, stored verbatim. The UI renders them safely, but logs, CSV exports and other tools can be confused.
- **Suggested fix:** Reject or strip control characters (U+0000-U+001F, U+007F) in single-line fields.

### BUG-09 [Low] Invalid UTF-8 is accepted and silently replaced
- **Layer:** Backend  |  **Area:** Request parsing
- **Steps / request:** POST /pipelines with raw body bytes {"name":"\xff\xfe",...} and content-type application/json
- **Expected:** 400 'body is not valid UTF-8'.
- **Actual:** 201; the name is stored as two U+FFFD replacement characters. A lone surrogate becomes three.
- **Suggested fix:** Decode strictly (fatal on invalid sequences).

### BUG-10 [Low] The 120-character name limit counts UTF-16 units, not characters
- **Layer:** Backend  |  **Area:** Validation
- **Steps / request:** POST /pipelines {"name":"<100 x U+1F600>",...}
- **Expected:** Accepted: 100 characters is under the 120 limit.
- **Actual:** 400 'Too big: expected string to have <=120 characters' (the string is 200 UTF-16 units).
- **Suggested fix:** Count code points (or grapheme clusters), not string length.

### BUG-11 [Low] Oversized request bodies sometimes get an empty 502 instead of 413
- **Layer:** Backend  |  **Area:** Proxy / API
- **Steps / request:** POST a 10 MB JSON body to /pipelines several times. Observed once in about 5 attempts. The limit sits between 1 MB and 2 MB.
- **Expected:** Always 413 with the JSON error body.
- **Actual:** Usually 413; intermittently an empty 502 from the proxy (the app closes the connection while the client is still uploading). The service stays healthy.
- **Suggested fix:** Reject on Content-Length before reading the body, or drain the request before closing.

### BUG-12 [Low] TRACE returns a bare 500
- **Layer:** Backend  |  **Area:** HTTP
- **Steps / request:** TRACE /api/crm/v1/pipelines
- **Expected:** 405 or 404 in the standard JSON error format (TRACE should be disabled).
- **Actual:** 500 'Internal Server Error' as plain text.
- **Suggested fix:** Disable TRACE at the proxy or add a route that returns 405.

### BUG-13 [Low] text/plain bodies are parsed as JSON; mutating calls without an Origin header are accepted
- **Layer:** Hardening  |  **Area:** Request handling
- **Steps / request:** POST /pipelines with content-type: text/plain and a JSON body -> 201. Also a session-cookie POST with no Origin header -> 201.
- **Expected:** 415 for non-JSON content types; ideally an Origin/Sec-Fetch-Site check on cookie-authenticated writes.
- **Actual:** Accepted. Not exploitable today because the required crm-* headers force a CORS preflight, but it removes a layer of CSRF protection. (The login endpoint is protected and rejects cross-site requests.)
- **Suggested fix:** Require application/json on write endpoints; check Origin/Sec-Fetch-Site for cookie sessions.

### BUG-14 [Low] Stage order has gaps after a stage is deleted
- **Layer:** Backend  |  **Area:** Pipelines
- **Steps / request:** Create a pipeline with stages A, B, C; delete B; read the pipeline.
- **Expected:** order values 0, 1.
- **Actual:** Remaining stages keep order 0, 2 until the next reorder call. Harmless unless a client assumes consecutive values.
- **Suggested fix:** Renumber on delete.

### BUG-15 [Low] An unknown Crm-Org-Id header value is accepted silently
- **Layer:** Backend  |  **Area:** Headers
- **Steps / request:** Any GET with the header crm-org-id: nope
- **Expected:** 400/403 for an organization that does not exist.
- **Actual:** 200, treated as the default organization.
- **Suggested fix:** Validate the header against the user's organizations.

### BUG-16 [Low] Every page has the same browser title, 'CRM Dashboard'
- **Layer:** Frontend  |  **Area:** All pages (accessibility)
- **Steps / request:** Open Pipelines, Contacts, Deals, Reports; read the tab title or document.title.
- **Expected:** A distinct title per page, e.g. 'Pipelines - Vercel 3 - CRM' (WCAG 2.4.2 Page Titled).
- **Actual:** 'CRM Dashboard' everywhere (not-found pages are the only ones that differ). Tabs, history and screen readers cannot tell pages apart.
- **Suggested fix:** Set a per-route title.

### BUG-17 [Low] Heading levels skip from h1 to h3
- **Layer:** Frontend  |  **Area:** Reports, Automation, Outbox, Products, My work (accessibility)
- **Steps / request:** Open the pages listed and inspect the headings, or run any heading-outline checker.
- **Expected:** Levels step down one at a time (h1, h2, h3).
- **Actual:** h1 is followed directly by h3 (WCAG 1.3.1).
- **Suggested fix:** Use h2 for section headings, or restyle with CSS instead of changing the level.

### BUG-18 [Low] One form field has no label
- **Layer:** Frontend  |  **Area:** Files page (accessibility)
- **Steps / request:** Open the Files page and inspect inputs for a label, aria-label or aria-labelledby.
- **Expected:** Every control has an accessible name.
- **Actual:** One input has none, so a screen reader announces it as an unnamed edit field.
- **Suggested fix:** Add a visible label or aria-label.

### BUG-19 [Low] Escape closes the dialog and discards typed input without warning
- **Layer:** Frontend  |  **Area:** New pipeline dialog
- **Steps / request:** Open New pipeline, type a name and stages, press Escape.
- **Expected:** Either keep the draft or ask before discarding.
- **Actual:** Closes immediately; the draft is lost. (Focus correctly returns to the trigger button.)
- **Suggested fix:** Confirm when the form is dirty.

### BUG-20 [Low] Table cells are truncated on mobile
- **Layer:** Frontend  |  **Area:** Pipelines table at 375 px
- **Steps / request:** Open Pipelines at 375 px width.
- **Expected:** Names and dates readable, or the row opens to show the full value.
- **Actual:** Names show as 'Enterpri...' and the Updated column as 'Oct 1, 2...'. There is no horizontal page scroll.
- **Suggested fix:** Allow wrapping or stack the row on narrow screens.

## Design questions (decide whether intended)

- **D-1 Duplicates are allowed everywhere.** Pipelines (even differing only by case), contacts (same email in any case), companies and close-reason labels can be duplicated. Three parallel creates of the same pipeline name made three pipelines. Stage names within a pipeline and close-reason codes ARE unique. Decide which should be unique, for example contact email.
- **D-2 Stages can be added to an archived pipeline.** The page says an archived pipeline 'takes no new deals', but its stages can still be changed.
- **D-3 Import cannot update existing records.** onDuplicate supports only 'create' (default) and 'reject'. A re-import always creates duplicates unless reject is used; there is no update or skip mode.
- **D-4 Archiving with dependants is allowed.** A pipeline with open deals, and a company with contacts and deals, can be archived. Deleting them is correctly blocked with 409.
- **D-5 Moving a deal to its current stage returns 200.** A no-op is accepted and succeeds rather than reporting 'already in this stage'.
- **D-6 Removing an in-use close reason is allowed.** Deals keep the old code, which is reasonable, but the UI does not warn how many deals use it.

## Verified working

- Delete guards: a stage with open deals, a pipeline with any deals, a company with references and the last active stage are all blocked with 409.
- Deal state machine: won, lost and reopen enforce valid transitions; closed deals cannot move or close twice; three parallel 'won' calls give one 200 and two 409s.
- Close reasons: outcome-specific, exact-code match, code format, 50-reason cap, duplicate code rejected.
- Money: integer minor units, no negatives, safe-integer maximum, uppercase ISO currency.
- Tenant isolation: another project's records return 404 for read, edit and delete; no session returns 401; bad project header returns 403; no data leaks through cursors or reports.
- Pagination: signed cursors bound to resource and project; every tampered cursor returns 400; no duplicates or gaps at limits 1, 7, 25, 100.
- Injection: XSS payloads in names and URL parameters never execute and are never reflected into the DOM; SQL, NoSQL and regex strings in search are inert; no open redirect through login ?next=.
- Uploads: presigned S3 flow works; type allowlist and 25 MB cap enforced; filenames are labels only (ID-based storage keys).
- Imports and exports: 1,500-row import OK; BOM, CRLF, quoted commas and newlines, unicode OK; per-row errors are accurate; 'reject' mode blocks duplicates; exported CSV neutralises formula cells and re-imports losslessly.
- Resilience: offline submit keeps the draft and a retry makes exactly one record; acting on a record deleted in another tab shows a clear error; double-click on Create makes one pipeline; no layout overflow from hostile names at desktop or 375 px.
- Dialog accessibility and keyboard: modal, labelled, focus trapped and restored; create works with keyboard only; behaviour matches in Chromium and Firefox (WebKit differs only in Safari's own focus rule).

## Not tested

- Member and other non-owner roles (only one account existed): permissions in Settings, member management, API keys.
- Automation, Properties, Audit, Catalog products and Outbox beyond layout and accessibility checks.
- Real screen readers (NVDA, VoiceOver, TalkBack) and Safari on macOS or iOS hardware.
- Export file expiry after 7 days; load and performance testing (deliberately out of scope).

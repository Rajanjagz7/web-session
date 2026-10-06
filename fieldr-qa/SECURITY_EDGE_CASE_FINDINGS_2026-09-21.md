# Fieldr Security & Edge-Case Findings — Invite / Groups / Users / Subscription

**Target:** `rajanjagz7.dev.fieldr.app` (dev tenant, owner-authorised), tested 2026-09-21.
**Method:** authenticated API calls via the app's own `/api/v1` endpoints (same session the UI uses), plus a few UI checks. Boundary, negative and OWASP-style probes (injection, mass assignment, IDOR, auth bypass) on Invite, User Groups, User create, and read-only checks on Subscription.
**Not executed:** any real Stripe checkout or payment submission (the account is on `pk_test_...`, Stripe test mode, but checkout was still not completed, per your standing instruction to avoid real charges); brute force / rate-limit flooding; cross-tenant access beyond the one accidental case in F1 below, which was stopped immediately.

## 1. Summary

| # | Finding | Severity | Type |
|---|---|---|---|
| **S1** | **`POST /user/create` with `type:"companyAdmin"` returns a `company` id and `role` id that do not belong to this tenant** — they don't match this workspace's own company/role ids seen anywhere else in the session | **Critical (needs verification)** | Multi-tenant data integrity |
| S2 | Users created through the API are invisible in `/user/list` and cannot be fetched by their own id right after creation (`GET /user/get/:id` → 400) | High | Data integrity / orphaned records |
| S3 | `POST /invite/create` with an empty body throws an unhandled exception: `500 "Cannot read properties of undefined (reading 'toString')"` | Medium | Error handling / crash |
| S4 | Invite email has almost no server-side validation: missing TLD, leading space, 254+ char local part, a Cyrillic homoglyph, and a null byte were all accepted with `200 "Invitation sent"` | Medium | Validation |
| S5 | `roleId` sent on `POST /invite/create` is accepted but silently ignored — verified safe, see 2.1 | Informational | — |
| S6 | User Group name has no length or content limit: 2000 characters, an HTML/JS payload, and emoji-only names are all accepted | Low | Validation |
| S7 | `POST /user/create` accepts a phone number made entirely of letters, and a first name as short as 2 characters (the Customer form enforces a 3-character minimum) | Low | Validation / inconsistency |
| S8 | `GET /invite/:id` (fetch one invite) is not implemented — returns `404 API endpoint doesn't exist` even for a real id | Informational | — |

Positive results: no cookie / tampered cookie both correctly return `401 "You are not logged in"`; duplicate invites and duplicate memberships are handled without server errors; `subscription/downgrade-check` rejects missing parameters without leaking internals.

## 2. Findings in detail

### S1. `type: "companyAdmin"` returns cross-tenant-looking ids (Critical, needs verification)
- **Steps:** `POST /user/create` with `{firstName, lastName, email, phone, countryCode, industry, type:"companyAdmin"}` (no `role` or `company` field supplied).
- **Actual Result:** `200 "Data created successfully"` with `"company": ["66f534910167e93d0f412707"]` and `"role": "679381499686ee8ca130c6cb"`.
- **This tenant's own ids, seen throughout this session:** company/workspace `6aae2a63d77d9ef26bdcf0f5` (from S3-upload paths and the login response), User role `6aae2a63d77d9ef26bdcf0fb`, Customer role `6aae2a63d77d9ef26bdcf0fc`, Company Admin role for this tenant would be expected to start `6aae2a63...` like the others. Neither the returned `company` nor the returned `role` matches this tenant's id pattern.
- **What this means, best case:** a hard-coded default from another (test/seed) company in the platform's shared database, wired in by mistake for the `companyAdmin` type path. Still a bug: it creates a broken, cross-referencing record.
- **What this means, worst case:** an authenticated user of one tenant can cause the platform to create a record that references another tenant's company and role ids, which is a tenant-isolation boundary issue.
- **What I did not do, deliberately:** I did not attempt to query, list, or authenticate against company `66f534910167e93d0f412707` or role `679381499686ee8ca130c6cb`. Doing so would mean interacting with data that may belong to a different customer, which is outside this engagement's scope. **This needs verification by someone with backend/database access**, not further black-box API probing.
- **Suggested Fix Direction:** user-create service, the branch that handles `type=companyAdmin`: find where it resolves `company`/`role` for that type and confirm it scopes to `req.user`'s own workspace, not a hard-coded id.
- **Reproduction:** `python invite_edge.py` in this folder (the "type = companyAdmin" case), then inspect the created record's `company`/`role` fields.

### S2. API-created users are invisible and unfetchable (High)
- **Actual Result:** none of the ~10 users created by `invite_edge.py` (emails starting `qa.edge.`) appear in `GET /user/list` even with `limit=300` and no search filter (`total=2`, only the two UI-created users from the earlier session). A freshly created user's own id also returns `400 {}` on `GET /user/get/:id`.
- **Relationship to Saturday's report:** this is the same shape as finding F5 (users beyond the seat limit are created but invisible), but happens even with the seat count at 101 and no visible limit message. It also reproduces regardless of `type`.
- **Impact:** orphaned user records accumulate (with real email/phone fields, so invite/welcome messages may still fire) and cannot be found, edited, or deleted by normal means.
- **Suggested Fix Direction:** user-create/list services: the list query is filtering on a field (workspace id, seat status, or `type`) the create path doesn't set consistently — compare the two and align them.

### S3. Unhandled exception on empty invite body (Medium)
- **Steps:** `POST /invite/create` with `{}`.
- **Actual Result:** `500 "Cannot read properties of undefined (reading 'toString')"`. This is a raw JavaScript `TypeError` reaching the client, not a validation message. Compare `POST /invite/create {"email":""}` which correctly returns `400 "Email is required"`.
- **Suggested Fix Direction:** invite controller: validate the body (email presence) before any code calls `.toString()` on a field that's assumed present.

### S4. Weak invite-email validation (Medium)
- **Accepted as valid (`200 "Invitation sent"`):**
  - `a@b` (no TLD)
  - `" qa.edge1@yopmail.com"` (leading space)
  - a 250-character local part + `@yopmail.com`
  - `qa.аdge@yopmail.com` (Cyrillic а instead of Latin a — a homoglyph that looks identical but is a different address)
  - an email containing a null byte
  - `["a@yopmail.com","b@yopmail.com"]` (an array, not a string)
- **Rejected (as 500, not 400):** no `@`, two consecutive dots, an XSS-style payload as the local part, `{"$ne": null}`, and a plain number — all correctly rejected, but with the same generic `500 "The invitation could not be emailed..."` as a network failure would give, so a tester can't tell malformed input from a real email-delivery problem.
- **Suggested Fix Direction:** invite controller: validate the email format (RFC-shaped, single string, reasonable length) before attempting delivery, and return 400 with a specific message for a format failure vs. a 502/500 for a genuine send failure.

### S5. Invite `roleId` — verified NOT exploitable
- **Steps:** `POST /invite/create` with `{"email":"qa.edge.escalate@yopmail.com","roleId":"<companyAdmin role id>"}`.
- **Actual Result:** the invite was created but stored with `"roleName": "User"`, `"roleId": "6aae2a63d77d9ef26bdcf0fb"` (the ordinary User role) — the supplied `roleId` was silently overridden to the default. **No privilege escalation via this path.**

### S6. User Group name has no length limit — but rendering is safe (Low, downgraded from possible-XSS)
- **Accepted:** a 2000-character name, `<img src=x onerror=alert(1)>QA_EDGE`, and an emoji-only name all returned `200`.
- **XSS rendering — confirmed safe.** The Groups screen is at User > Groups (`/app/user/list?section=groups`, a tab that only appears once the User list has fully loaded — it's easy to miss if you check too early). I opened it and verified the payload group directly: the DOM has no `<img>` element and no `onerror` attribute anywhere; the text lives inside a `<p>` whose `innerHTML` is `&lt;img src=x onerror=alert(1)&gt;QA_EDGE`, i.e. it renders as plain visible text. No JavaScript `alert()` fired (confirmed via Playwright's dialog listener, which would have caught it). **No stored XSS.** Remaining issue is only the missing length cap.
- **Suggested Fix Direction:** group create/update validators: cap name length (e.g. 100 chars). No rendering fix needed.

### S7. Inconsistent field validation on User create (Low)
- `phone: "ABCDEFGHI"` (all letters) → `200`, record created.
- `firstName: "Al"` (2 chars) → `200`, though the Customer form enforces "First name must be between 3 to 35 characters" client-side.
- **Suggested Fix Direction:** share one validator between the Customer and User create paths, or add the same server-side checks to User create.

### S8. `GET /invite/:id` not implemented (GET only — DELETE works)
- Both a real invite id and a guessed one returned `404 "API endpoint doesn't exist"` on GET — that route isn't wired for GET (only create/resend/verify/accept exist). Not a vulnerability, just means single-invite lookup isn't available for further IDOR testing. **Correction:** `DELETE /invite/:id` *is* implemented and was used successfully for cleanup (see section 5) — only GET is missing.

## 3. Subscription (read-only; no checkout attempted)

- Current plan: **Basic**, `$49.00/month AUD`, quantity 1, status active, via Stripe **test mode** (`pk_test_51Tg3UY...`).
- Add-ons shown: Customer Portal ($99/mo), Extra Seats ($9/mo each, max 200 — **currently 101 seats: 1 plan + 100 purchased**, pre-existing from Saturday's session, not from today), Chat & Feed (added, $100/mo), Defect Management ($249/mo, not added).
- A pending cancellation is shown: "You keep access until 19 Oct 2026" — also pre-existing.
- `GET /subscription/downgrade-check` requires query params `track` and `tier` (their exact expected values were not determined; every value I tried, including on the query string, still returned "track and tier are both required," so either they need a different transport (e.g. request body on a GET-like call) or different key casing). No injection or error-detail leak was found in what I could reach — it either accepts silently or returns the same generic 400.
**Update — seat quantity boundary testing (done, with your go-ahead, no checkout completed):**

Driving the real "Extra Seat" add-on quantity field on the Subscription page (without ever clicking "Add seats" to create a pending order, and never clicking "Proceed to checkout"):

| Typed | Field shows | Note |
|---|---|---|
| `0` | `1` | clamped up to the minimum — OK |
| `-5` | `5` | **the minus sign is silently stripped, not rejected** — a user who means "remove 5" gets "add 5" with no warning |
| `999` | `99` | **the input has a 2-character max length, so you cannot type past 99 even though the card states "max 200"** — the only way to reach 100–200 would be clicking "+" up to 200 times, which is itself worth checking for an off-by-one or silent cap |
| `2.5` | `25` | **the decimal point is silently stripped**, turning a fractional typo into a real whole number with no warning |
| `abc` | `1` (unchanged) | letters correctly rejected |

- **Finding S9 (Low):** seat-quantity input strips invalid characters (`-`, `.`) instead of rejecting the input or showing an error, which can silently turn a mistyped value into a different valid number.
- **Finding S10 (Medium, needs confirmation):** the "max 200" seats claim cannot be reached by typing (2-digit input cap = 99 max). Whether the `+` button can actually reach 200, and what happens if it's clicked past 200, was not tested (200 clicks was out of scope for this session) — worth a manual check.
- I did **not** click "Add seats" or "Proceed to checkout" in this pass, so no order was created and nothing changed on the account.

## 4. What to do next
1. **Verify S1 first.** This is the only finding that could be a real security boundary issue rather than a UI/UX bug. Someone with database or backend access should check what company `66f534910167e93d0f412707` and role `679381499686ee8ca130c6cb` actually are.
2. **Cleanup done:** the 6 `QA_EDGE...` groups were deleted and the 6 `qa.edge...`/`qa.test...` invites were revoked via the API. The orphaned users from S2 could **not** be cleaned up — they don't appear anywhere in `/user/list` even paging the full list, confirming they're unreachable through the normal API and need direct database access to remove.
3. If you want the seat "+" button clicked up toward 200 to check S10, or a real (test-mode) checkout completed, say so explicitly and I'll do it as its own step.

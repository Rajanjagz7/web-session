# API Test Cases — Invite, User Groups, User Create, Subscription

Run these against `rajanjagz7.dev.fieldr.app` with a logged-in session cookie (`connect.sid`). All are plain
`fetch`/curl calls to `/api/v1/...`. Header for every call: `x-device-type: web`, and `content-type: application/json`
for POST/PUT.

**Getting a cookie:** log in on the site, open DevTools → Application → Cookies, copy `connect.sid`. Or run
`python fieldr_seed.py` once interactively and reuse its session logic.

```bash
export FLDR_COOKIE="<connect.sid value>"
curl -s -b "connect.sid=$FLDR_COOKIE" -H "x-device-type: web" -H "content-type: application/json" \
  https://rajanjagz7.dev.fieldr.app/api/v1/user/list?skip=0&limit=5
```

Every case below: **ID | Steps | Data | Expected | Observed (2026-09-21) | Priority**

---

## A. Invite (`/invite/*`)

| ID | Method + Path | Body | Expected | Observed | Priority |
|---|---|---|---|---|---|
| INV-001 | POST /invite/create | `{}` | 400 with a clear validation message | **500 "Cannot read properties of undefined (reading 'toString')"** — BUG, see S3 | P1 |
| INV-002 | POST /invite/create | `{"email":""}` | 400 "Email is required" | 400 "Email is required" — OK | P2 |
| INV-003 | POST /invite/create | `{"email":"   "}` | 400 | 400 "Email is required" — OK | P2 |
| INV-004 | POST /invite/create | `{"email":"not-an-email"}` | 400 | 500 generic send-failure message — should be 400 | P2 |
| INV-005 | POST /invite/create | `{"email":"a@b"}` (no TLD) | 400 | **200 "Invitation sent" — BUG, invalid email accepted** | P1 |
| INV-006 | POST /invite/create | `{"email":" qa.test1@yopmail.com"}` (leading space) | 400 or auto-trim + 200 | **200, not trimmed — check stored value** | P2 |
| INV-007 | POST /invite/create | `{"email":"<250 a's>@yopmail.com"}` | 400 (over reasonable length) | **200 — BUG, no length cap** | P3 |
| INV-008 | POST /invite/create | `{"email":"qa.аdge@yopmail.com"}` (Cyrillic а) | 400 or flagged | **200 — homoglyph accepted, phishing risk** | P2 |
| INV-009 | POST /invite/create | `{"email":["a@yopmail.com","b@yopmail.com"]}` | 400 (wrong type) | **200 — BUG, array accepted as email** | P2 |
| INV-010 | POST /invite/create | `{"email":"qa.dup@yopmail.com"}` twice in a row | 2nd call: 400 "already has an invitation" | OK, matches | P3 |
| INV-011 | POST /invite/create | email of an existing user in this workspace | 400 "already a member" | OK, matches | P3 |
| INV-012 | POST /invite/create | `{"email":"qa.esc@yopmail.com","roleId":"<companyAdmin role id>"}` | roleId either respected only if caller is authorised, or rejected | **Silently downgraded to default "User" role — safe, but confirm this is intentional, not accidental** | P2 |
| INV-013 | POST /invite/:id/resend | valid id, `{}` | 200 | OK | P3 |
| INV-014 | POST /invite/000000000000000000000000/resend | fake ObjectId | 404 | OK "Invitation not found" | P3 |
| INV-015 | GET /invite/:id | real invite id | 200 with the invite | **404 "API endpoint doesn't exist" — GET is not implemented.** `DELETE /invite/:id` IS implemented and works (used for cleanup) | P4 |
| INV-016 | POST /invite/accept | `{"token":""}` and `{"token":"garbage"}` | 400, no server error | OK, both return the same generic expired/used message | P3 |

## B. User Groups (`/user/group/*`)

| ID | Method + Path | Body | Expected | Observed | Priority |
|---|---|---|---|---|---|
| GRP-001 | POST /user/group/create | `{}` | 400 "Group name is required" | OK | P3 |
| GRP-002 | POST /user/group/create | `{"name":""}` / `{"name":"   "}` | 400 | OK both | P3 |
| GRP-003 | POST /user/group/create | `{"name":"A"}` (1 char) | 400 if there's a minimum, else 200 | 200 — no minimum enforced | P4 |
| GRP-004 | POST /user/group/create | `{"name":"<255 chars>"}` | 200 or 400 depending on your intended max | 200 | P4 |
| GRP-005 | POST /user/group/create | `{"name":"<2000 chars>"}` | 400 (too long) | **200 — BUG, no max length** | P3 |
| GRP-006 | POST /user/group/create | `{"name":"<img src=x onerror=alert(1)>QA_EDGE"}` | 400, or 200 with safe storage/render | **200 — confirmed SAFE on render.** Open User > Groups (`/app/user/list?section=groups`, wait for the page to fully load — the Groups tab is easy to miss). The payload showed as literal text (`&lt;img...&gt;`), no real `<img>` element, no `alert()` fired. Only the missing length cap remains an issue | P4 |
| GRP-007 | POST /user/group/create | `{"name":"😀😀😀"}` (emoji only) | 400 if letters required, else 200 | 200 | P4 |
| GRP-008 | POST /user/group/create | same name twice | 2nd call: 400 duplicate, or 200 if duplicates are allowed by design | **200 twice — duplicate names allowed; confirm this is intended** | P3 |
| GRP-009 | POST /user/group/create | `{"name":"x","users":["000000000000000000000000"]}` (fake user id) | 400 | **200 — BUG, nonexistent member id accepted silently** | P3 |
| GRP-010 | POST /user/group/create | `{"name":"x","users":["not-an-id"]}` (malformed id) | 400 | 400 "Invalid id provided" — OK | P4 |
| GRP-011 | PUT /user/group/update/000000000000000000000000 | `{"name":"x"}` | 404, not 400 | 400 "Invalid id provided" — arguably should be 404 | P4 |
| GRP-012 | DELETE /user/group/delete/000000000000000000000000 | — | 404 | 400 "Invalid id provided" — same as above | P4 |

## C. User create (`/user/create`)

| ID | Method + Path | Body | Expected | Observed | Priority |
|---|---|---|---|---|---|
| USR-001 | POST /user/create | `{}` | 400 listing required fields | OK: "Name, Phone, Email, Country code, Industry are required" | P3 |
| USR-002 | POST /user/create | firstName `"Al"` (2 chars), rest valid | 400 (Customer form requires 3+) | **200 — inconsistent with Customer's own validation** | P3 |
| USR-003 | POST /user/create | firstName 200 chars | 400 | 200 — no max | P4 |
| USR-004 | POST /user/create | `phone:"ABCDEFGHI"` | 400 | **200 — BUG, letters accepted as a phone number** | P2 |
| USR-005 | POST /user/create | `phone:"+61 4 12 34 56 78"` | 400 (should be digits only per the app's own display format) or auto-normalised | 200, stored form not verified — check manually | P4 |
| USR-006 | POST /user/create | `type:"companyAdmin"` | 400 (type should not be caller-settable), or 200 scoped to caller's own company | **200, with `company`/`role` ids that do NOT match this tenant — see finding S1, needs backend verification before relying on this test alone** | **P1** |
| USR-007 | POST /user/create | email `"'; DROP TABLE users; --@yopmail.com"` | 400 (invalid format) or safely stored as a literal string, no DB error | 200, stored as literal string — no injection observed | P4 |
| USR-008 | GET /user/get/:id | id of a user created 1 second earlier by USR-006/007 | 200 with the user | **400 `{}` — BUG, user unfindable right after creation, see S2** | P2 |
| USR-009 | GET /user/list?limit=300 | after creating ~10 users via API | all of them appear | **none of them appear (total count unchanged) — see S2** | P2 |

## D. Auth / session

| ID | Steps | Expected | Observed | Priority |
|---|---|---|---|---|
| AUTH-001 | `GET /user/list` with no cookie at all | 401 | OK: `401 "You are not logged in"` | P3 |
| AUTH-002 | `GET /user/list` with the cookie value + extra garbage appended | 401 | OK: `401 "You are not logged in"` | P3 |

## E. Subscription (`/stripe/*`, `/subscription/*`) — read-only

| ID | Method + Path | Body/Params | Expected | Observed | Priority |
|---|---|---|---|---|---|
| SUB-001 | GET /stripe/subscription | — | 200 with plan, amount, status | OK: Basic plan, $49/mo AUD, active | P4 |
| SUB-002 | GET /stripe/subscription/pending-downgrade | — | 200 | OK, empty (no pending downgrade) | P4 |
| SUB-003 | GET /stripe/catalog | — | 200 with product list | OK | P4 |
| SUB-004 | GET /subscription/downgrade-check | no params | 400 with a clear message | OK: "track and tier are both required" | P4 |
| SUB-005 | GET /subscription/downgrade-check | `track`, `tier` with real/invalid values | 200 (valid) / 400 (invalid), no server error | **Not resolved this session — the correct param shape wasn't found. Try it from the actual "Downgrade" button in the UI with DevTools Network tab open, copy the real request, then repeat with boundary values (negative tier, huge tier, XSS string)** | P3 |
| SUB-006 | Type into the "How many seats?" field on the Subscription page (UI), without clicking "Add seats" or "Proceed to checkout" | `0`, `-5`, `999`, `2.5`, `abc` | client should reject invalid characters outright | `0`→clamped to `1` (OK); `-5`→**silently becomes `5`, the minus sign is just stripped**; `999`→**truncated to `99` by a 2-char input limit, so the stated "max 200" cannot be reached by typing**; `2.5`→**silently becomes `25`, the decimal point is stripped**; `abc`→correctly rejected | P3 |
| SUB-007 | Click "+" on the seat stepper up to 200, then once more (201) | — | stops at 200 with a clear message | **Not tested — 200 clicks was out of scope for this session.** Worth checking manually: does it stop, cap silently, or accept 201? | P2 |
| SUB-008 | Add-on toggle (Defect Management) then immediately remove it, without proceeding to checkout | — | no charge/residue if cancelled before confirming | **Not tested — would need your explicit go-ahead, since it changes the account's add-on state even before checkout** | P2 |

---

## Cleanup — records this session created

All fictional, named for easy filtering:
- **Invites:** every `/invite/list` entry with an email starting `qa.edge.` or `qa.test`.
- **Users:** `/user/list` search for `qa.edge` (currently returns 0 — see S2 — so these may need a database-level cleanup, not just the UI).
- **Groups:** `/user/group/list` entries named `QA_EDGE ...` (Duplicate Test Crew, Bad Members, Bad Members 2, Dup Member) and `QA Edge Baseline Crew`.
- **Job notes / job tasks:** a couple of test rows were created and already deleted where a delete endpoint existed (`job/notes/delete`, `job/field/delete`); `job/task` has no delete endpoint in this API version, so one test task record remains on a job — harmless but real.

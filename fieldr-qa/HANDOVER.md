# Fieldr QA Handover

Tenant: `rajanjagz7.dev.fieldr.app` (dev). Prepared 2026-09-19. Everything below was observed in this run unless it is marked ASSUMPTION or "not verified".

## 1. Where things stand

| Area | State |
|---|---|
| Plan | Basic ($49/mo), Stripe test mode. At the end of the session the subscription page showed 101 seats (100 purchased extra seats) plus the Chat & Feed and Defect Management add-ons as Added. None of these were clicked by the assistant; check who bought them (about $1,249/mo of add-ons in test mode) |
| Customers | 101, unique AU names, @yopmail.com emails, unique realistic mobiles, profile photos |
| Items | 100, different margin on each, labour/material types set |
| Invoices | 180: Paid 55, Awaiting Payment 56, Awaiting Approval 59, Draft 10 |
| Jobs | 277 across Schedule, In Progress, On Hold, Completed, Cancelled, with AEST dates, coordinates, report templates, checklists and planned items |
| Job Reports | 375, fields filled, 4 statuses |
| Quotes | 101 with sections, line types and formula columns; 6 valid formulas |
| CMS / Holidays / Checklists / Templates | 40 / 27 / 3 / 3 |
| Users and groups | 3 groups created (members show 0). 6 users created over the API return 200 but never appear in the Users list, even after the seats were added, so the API payload is missing something the UI form sends. Not finished |
| Timesheets and Crew Clocked On | Not filled: the timelog API stores nothing |
| Playwright specs | 50 generated (FLD-AUTH-001 to 050), not installed or run |
| Payment cards | None added |

## 2. Next steps
1. Create one user through the UI form (Add User: First Name, Last Name, Industry, Role, Tags, Email, Mobile) and capture its `POST /user/create` body with DevTools, compare it with the API payload used in this session, then seed the rest, add them to groups and add tags. Use ACMA-reserved or otherwise safe mobiles; invites can send SMS.
2. Find how timesheets are created (mobile clock-on payload or a clock-on button on a job) and seed them.
3. `cd pw`, copy `.env.example` to `.env`, fill in the QA mobile and OTP, run `npm install`, `npx tsc --noEmit`, then `npx playwright test --project=chromium --grep @smoke`.
4. Delete the probe records listed at the end of the bug report.
5. Re-check the dashboard: every tile should show 50+ records except Crew Clocked On and Schedule This Week.

## 3. Bugs found so far and the API/security test report
## Fieldr Security and API Test Report

**Target:** `rajanjagz7.dev.fieldr.app` (owner-authorised dev tenant), tested 2026-09-19
**Method:** authenticated, in-session API testing through the app's own REST endpoints (`/api/v1`) plus UI walkthroughs.
**Not executed by design:** brute force, rate-limit flooding, DoS, broad path scanning, cross-tenant access, stored-XSS payloads.
Every "Actual Result" below was observed in this run. Anything not observed is listed under "Not verified".

### 1. Summary

| # | Finding | Severity | Type |
|---|---|---|---|
| F1 | Client can set financial fields on invoices (paid amount, amount due, payments, status) | High | Integrity / mass assignment |
| F2 | Status and type fields accept any string (no enum check) on invoices, job reports, jobs, items | Medium | Validation |
| F3 | Validation failures return HTTP 500 with raw Mongoose/internal messages | Medium | Info disclosure / error handling |
| F4 | `POST /timelog/create` returns "Data created successfully" but stores nothing, and accepts an empty body | Medium | Silent failure |
| F5 | Users created past the seat limit succeed over the API but never appear in the UI | Medium | Plan enforcement / orphan data |
| F6 | Mobile-uniqueness errors disclose that a number exists in another tenant | Medium | Cross-tenant enumeration |
| F7 | OTP screen shows `+610444124222` (leading 0 kept after +61) | Medium (needs confirmation) | Data handling |
| F8 | Jobs can be created directly in `Completed` / `Cancelled` states | Low | Workflow bypass |
| F9 | Server and framework versions disclosed in response headers | Low | Info disclosure |
| F10 | App reloads itself when `version.json` changes, dropping in-progress forms; form fields lost typed characters | Medium | Functional / data loss |
| F11 | Unknown page URLs silently redirect to the Dashboard (no 404 page, no message); the API returns a JSON 404 for unknown endpoints | Medium | Routing / UX |
| F12 | Unexpected redirects to Dashboard and Settings > Subscription while a form or API call is in progress | Medium | Functional |

Positive results: job cap enforced server-side (`403 planLimitReached`), GST calculated server-side, duplicate holiday dates rejected (409), duplicate mobiles rejected (409), unauthenticated `/app/dashboard` redirects to `/login`.

### 2. Findings

#### F1. Client-controlled invoice payment fields (High)
- **Actual Result:** `PUT /api/v1/invoice/update/:id` with `{status:"Paid", amountPaid:518.76, amountDue:0, payments:[{...}]}` returned `200 "Data updated successfully"` and persisted all fields. The UI's `actions` flags for a "Sent" invoice showed `canRecordPayment: false`, yet the API accepted a payment.
- **Impact:** any user with invoice edit access can mark invoices paid or alter totals without a payment record. Affects revenue reporting and Xero sync.
- **Evidence:** dashboard "Revenue this week" rose to $63,764.41 from API-only updates. [Screenshot: dashboard-revenue.png]
- **Suggested Fix Direction:** invoice update controller and its schema: whitelist editable fields, derive `amountPaid`/`amountDue` from a payments sub-resource, enforce a status state machine (Draft, Awaiting Approval, Awaiting Payment, Paid).

#### F2. No enum validation on status/type fields (Medium)
- **Actual Result:** invoice status accepted `Sent`, `Approved`, `Submitted`, `Pending Approval` (the UI filter options are only `Draft`, `Awaiting Approval`, `Awaiting Payment`, `Paid`). Job report `Rejected`/`Approved` accepted. Item `lineType` accepted `labour`, `Labour`, `service`, `material`. Invoices with unknown statuses vanished from the dashboard "Invoice Status" chart.
- **Impact:** invalid states create records that do not appear in reports and are hard to find.
- **Suggested Fix Direction:** enum validators in the invoice, job report and item schemas.

#### F3. Validation errors surface as 500 with internal detail (Medium)
- **Actual Result:** `POST /cms/create` `{title}` returned `500 "cms validation failed: content: Path 'content' is required., type: Path 'type' is required."`; a wrong `type` returned `500 "... is not a valid enum value for path 'type'"`. `PUT /quote/update` with a bad section returned `500 "Cast to embedded failed for value ..."` echoing request data. `POST /template/add` `{}` returned `500 "template validation failed: title..."`. `PUT /job/update` with a string for `startDateAndTime` returned `500 "Cast to Number failed ..."`.
- **Impact:** discloses schema field names and enum handling; 500s inflate error monitoring.
- **Suggested Fix Direction:** shared error middleware mapping Mongoose `ValidationError`/`CastError` to 400 with a generic message.

#### F4. `timelog/create` reports success but stores nothing (Medium)
- **Actual Result:** 4 different payloads, including `{}`, all returned `200 {"message":"Data created successfully","data":null}`. `GET /timelog/list` stayed at `totalCount: 0`.
- **Impact:** clients cannot detect failure; timesheets cannot be seeded or tested through the API.
- **Suggested Fix Direction:** timelog controller: validate the body and return 400 on missing `jobId` or times; return the created document.

#### F5. Users over the seat limit are created but invisible (Medium)
- **Actual Result:** `POST /user/create` returned 200 for 5 users on a plan with 1 seat; `GET /user/list` and the Users page show "No users found". Creating through the UI form redirected to Settings > Subscription.
- **Update (end of session):** after the subscription page showed 101 seats, `POST /user/create` for a new user (Zoe Barker) again returned 200 and `GET /user/list` still returned `totalCount: 0`. So missing seats are not the only reason: the API creates a record the list endpoint never returns, most likely because fields the UI form sends (for example workspace or user type) are absent from the API payload. The API accepts the incomplete record without an error.
- **Impact:** orphaned user records (invites and SMS may still be sent), and no error tells the caller the user is unusable.
- **Suggested Fix Direction:** user-create service: reject bodies missing the fields the list query depends on, and return 403 with a `planLimitReached` reason on seat overflow, as the job endpoint does. Next step for testers: capture the UI form's `POST /user/create` body and diff it with the API payload.

#### F6. Mobile numbers disclose existence in other tenants (Medium)
- **Actual Result:** `customer/create` returned `409 "This mobile number is already registered"` and later `400 "This mobile number already belongs to another account..."`. `user/create` returned `400 "This mobile number is already registered"` for two numbers that this tenant had never used.
- **Impact:** any tenant user can test whether a number holds an account elsewhere.
- **Not verified:** whether the login endpoint itself discloses registration (cases FLD-AUTH-026 and 035 record its behaviour).
- **Suggested Fix Direction:** customer and user create services: report uniqueness only within the caller's workspace.

#### F7. OTP target shows a leading zero after +61 (Medium, needs confirmation)
- **Actual Result:** after entering `0444124222`, the OTP step reads "We sent a 6-digit OTP to +610444124222". E.164 for that number is `+61444124222`. Customer records store `phone` without the leading 0.
- **Impact:** if the SMS gateway receives the display value, delivery may fail or go to the wrong number. Delivery was not verified (bypass OTP in use).
- **Suggested Fix Direction:** login/OTP controller: strip the national trunk `0` before composing E.164.

#### F8. State machine bypass on job create (Low)
- **Actual Result:** `POST /job/create` with `status:"Completed"` or `"Cancelled"` was accepted and counted on the dashboard.
- **Suggested Fix Direction:** ignore or reject `status` on create.

#### F9. Version disclosure in headers (Low)
- **Actual Result:** responses carried `server: nginx/1.28.3 (Ubuntu)` and `x-powered-by: Express`. `strict-transport-security` is present (good).
- **Suggested Fix Direction:** nginx `server_tokens off`; `app.disable('x-powered-by')`.

#### F10. Auto-reload and lost input (Medium)
- **Actual Result:** while a form or dialog was open the page reloaded (a `version.json` request preceded each reload) and the form closed. Filling the Add User email produced `zoe.bark` instead of the full address, and a customer description saved as `Q`.
- **Impact:** data loss for real users during deploys.
- **Suggested Fix Direction:** defer the version-check reload until no form is dirty; prompt instead.

#### F11. Unknown page URLs redirect to the Dashboard instead of showing "Not found" (Medium)
- **Steps:** 1. Log in. 2. Open `https://rajanjagz7.dev.fieldr.app/app/global-settings/payment-cards`. 3. Open `https://rajanjagz7.dev.fieldr.app/app/this-page-does-not-exist`.
- **Actual Result:** both pages ended on `/app/dashboard` with the Dashboard heading. No 404 page, no toast, no message. In contrast `GET /api/v1/does-not-exist` returns `404 {"success":false,"message":"API endpoint doesn't exist"}`.
- **Expected Result:** a "Page not found" screen (or a clear message) that keeps the wrong URL visible.
- **Impact:** users and testers cannot tell a mistyped or removed link from a working page. During this run it hid a wrong Payment Cards URL (the correct one is `/app/global-settings/billing/cards`) and made broken deep links look like they worked. It also masks routing regressions in automated tests, because a wrong route "passes" by landing on a valid page.
- **Frequency:** every unknown `/app/*` URL tested (2 of 2).
- **Evidence:** [Screenshot: unknown-route-redirect.png]; observed URL after load: `/app/dashboard`.
- **Suggested Fix Direction:** client router catch-all route: render a NotFound component instead of `Navigate to="/app/dashboard"`.

#### F12. Unexpected redirects during work (Medium)
- **Actual Result:** (a) opening Add User and pressing Save redirected to Settings > Subscription, with no message explaining the seat limit; (b) several times the page navigated to the Dashboard or another route while a script or form was in use (for example after a subscription checkout the dialog closed and the app landed on `/app/dashboard`); (c) an `Execution context was destroyed` navigation happened during long-running calls on the Customer and Invoice pages.
- **Impact:** users lose place and unsaved input; the reason for the redirect is not shown.
- **Suggested Fix Direction:** show an explicit "Seat limit reached, add a seat" message before redirecting; avoid automatic navigation while a form is dirty.

### 3. API test results (observed)

| Endpoint | Method | Result |
|---|---|---|
| `/auth/is-logged-in` | GET | 200 with session |
| `/customer/create`, `/customer/update/:id` | POST/PUT | 200; duplicate mobile 409/400; partial update OK |
| `/item/create`, `/item/update/:id` | POST/PUT | 200; `lineType` free text |
| `/invoice/create`, `/invoice/update/:id` | POST/PUT | 200; totals and 10% GST calculated (2 x $630.00 = $1,260.00 + $126.00 = $1,386.00); client fields trusted (F1) |
| `/job/create`, `/job/update/:id` | POST/PUT | 200; cap 403 on Solo; partial update OK; `startDateAndTime` is epoch ms |
| `/job/report/update/:id` | PUT | 200; `value` per field persisted |
| `/quote/create`, `/quote/update/:id` | POST/PUT | 200; needs `sections[].items[]`; `formulaColumns:[{formulaId}]` |
| `/quote-formula/create` | POST | 200; tokens `{type:"field|op|num", value}` |
| `/cms/create`, `/cms/types` | POST/GET | 200; `type` takes the display name; enum errors are 500 (F3) |
| `/holiday/create` | POST | 200; one per date (409) |
| `/checklist/create`, `/checklist/update/:id` | POST/PUT | 200; items use `label` |
| `/template/add`, `/template/edit/:id` | POST/PUT | 200; `fields` free-form |
| `/aws/upload-file` | POST | 200; multipart field `files` |
| `/user/create` | POST | 200 but invisible (F5) |
| `/timelog/create` | POST | 200 with no data stored (F4) |

### 4. Not verified
- Session cookie flags (`HttpOnly`, `Secure`, `SameSite`): the cookie value is visible to DevTools but the flags were not read.
- CSRF protection, IDOR across workspaces (single tenant only), OTP rate limiting and lockout, OTP expiry and replay (bypass OTP is static), idle timeout.
- Whether the login endpoint discloses if a mobile or email is registered.
- Invoice `tax`/`taxRate` per line was supplied by the client at 10; whether the server accepts 0 was not tested.

### 5. Test data footprint (for cleanup)
Probe records to delete: jobs "Probe", "Plan-limit check - Basic", "Status probe - In Progress"; one empty draft invoice; quote "QA probe quote (sections-items)"; CMS entry "enum probe"; the duplicate FAQ "How do I book a callout in NSW?"; six invisible API-created users (Liam Fraser, Charlotte Mitchell, Hamish Sutherland, Tahlia Kaur, Kai Papadopoulos, Zoe Barker).

## 4. Test plan
## Fieldr Test Plan

**Observed 2026-09-19 on the live dev tenant:** login and OTP screens, Dashboard, Customer, User, Quote (with Formulas), Job (all tabs), Timesheet, Job Report, Invoices, Items, CMS, Settings (Company, Holidays, Checklists, Report Builder, Subscription, Payment Cards). Items marked ASSUMPTION or NEEDS UI INSPECTION were not observed.

### 1. Executive summary
- Scope: authentication, adding people, commercial documents (items, quotes, invoices, jobs), content and legal pages.
- Total cases: **115** (AUTH 50, REG 20, CKOUT 30, CONT 15).
- Priority split: P0 31, P1 59, P2 20, P3 5.
- Automated: AUTH-001 to 050 as Playwright specs (`pw/src/tests/auth`). They have not been installed or run yet.
- Blockers: no timesheet or crew data can be created (the timelog API stores nothing); users need extra seats; OTP expiry, replay and idle timeout cannot be tested with the static bypass OTP.
- Findings so far: 10 (see SECURITY_API_TEST_REPORT.md).

### 2. Test environment
| Item | Value |
|---|---|
| URL | https://rajanjagz7.dev.fieldr.app |
| Auth | Passwordless OTP, six boxes ("Digit 1" to "Digit 6"), button "Verify & Login" |
| Plan | Basic ($49/mo), Stripe test mode |
| Browsers | Chrome, Firefox, Safari (WebKit), Edge (latest) |
| Viewports | 1920x1080, 1366x768, 768x1024, 375x667, 320x568 |
| OS | Windows 11 (runner); Safari via Playwright WebKit |
| Data | 101 customers, 100 items, 180 invoices, 277 jobs, 101 quotes, 375 job reports, 6 formulas, 40 CMS entries, 27 holidays, 3 checklists, 3 report templates |

### 3. Test cases
#### AUTH: authentication and sessions (50 cases)
Full table: [auth-test-cases.md](auth-test-cases.md), generated from the Playwright specs.

#### REG: adding people: customers, users, groups (20 cases)
| ID | Title | Module | Preconditions | Steps | Test Data (AU) | Expected Result | Priority | Type |
|----|-------|--------|---------------|-------|----------------|-----------------|----------|------|
| FLD-REG-001 | Add Customer with all required fields | REG | Logged in as the QA user | 1. Open Customer<br>2. Click Add Customer<br>3. Enter First Name<br>4. Enter Last Name<br>5. Enter Mobile Number<br>6. Enter Email<br>7. Enter Address<br>8. Enter Description<br>9. Click Save | Olivia Nguyen / 0491 570 156 / olivia.nguyen@yopmail.com / 12 Macquarie Street, Sydney NSW 2000 | Customer saved; appears in list with a CST- number | P0 | Functional |
| FLD-REG-002 | Add Customer with empty First Name | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Leave First Name empty<br>3. Fill all other fields<br>4. Click Save | empty | Save disabled or inline error on First Name | P1 | Negative |
| FLD-REG-003 | Add Customer with duplicate mobile | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Enter a mobile already used<br>3. Fill other fields<br>4. Click Save | existing customer mobile | Rejected with a duplicate-mobile message | P0 | Negative |
| FLD-REG-004 | Add Customer mobile too short (9 digits) | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Enter 041234567 in Mobile Number<br>3. Fill other fields<br>4. Click Save | 041234567 | Rejected, inline validation | P1 | Boundary |
| FLD-REG-005 | Add Customer email without @ | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Enter noah.smithbigpond.net.au in Email<br>3. Click Save | no @ | Inline email error | P1 | Validation |
| FLD-REG-006 | Add Customer email 255 chars | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Enter a 255-char email<br>3. Click Save | 255 chars (bigpond.net.au) | Rejected (max 254) | P2 | Boundary |
| FLD-REG-007 | Add Customer name with emoji only | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Enter an emoji in First Name<br>3. Click Save | U+1F642 | Rejected or stripped | P2 | Validation |
| FLD-REG-008 | Add Customer name 101 chars (ASSUMPTION max 100) | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Enter 101 chars in Last Name<br>3. Click Save | N x 101 | Rejected; max length NEEDS UI INSPECTION | P2 | Boundary |
| FLD-REG-009 | Add Customer XSS in Description is escaped | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Enter an img onerror payload in Description<br>3. Fill other fields<br>4. Click Save<br>5. Open the customer | XSS payload | Rendered as text; no script runs | P1 | Security |
| FLD-REG-010 | Add Customer profile photo upload | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Choose avatar-001.png<br>3. Fill required fields<br>4. Click Save | avatar-001.png | Photo shows on card and profile | P2 | Functional |
| FLD-REG-011 | Add New User with all required fields | REG | Logged in as the QA user | 1. Open User<br>2. Click Add User<br>3. Enter First Name<br>4. Enter Last Name<br>5. Select Industry<br>6. Select Role<br>7. Enter Email<br>8. Enter Mobile Number<br>9. Click Save | Liam Fraser / Construction / User | User appears in list (needs a free seat) | P0 | Functional |
| FLD-REG-012 | Add New User when the plan has no free seat | REG | Logged in as the QA user | 1. Open Add New User<br>2. Fill all required fields<br>3. Click Save | Basic plan, 1 seat | Clear seat-limit message and no orphan user (observed: redirect to Subscription) | P0 | Negative |
| FLD-REG-013 | Add New User without Role | REG | Logged in as the QA user | 1. Open Add New User<br>2. Fill fields except Role<br>3. Click Save | no role | Inline error on Role | P1 | Negative |
| FLD-REG-014 | Add New User with a mobile from another tenant | REG | Logged in as the QA user | 1. Open Add New User<br>2. Enter a mobile registered elsewhere<br>3. Click Save | registered number | Generic message that does not reveal other tenants | P1 | Security |
| FLD-REG-015 | Add New User Date Of Birth 29/02/1900 | REG | Logged in as the QA user | 1. Open Add New User<br>2. Pick 29/02/1900 in Date Of Birth | 29/02/1900 | Date rejected (not a leap year) | P2 | Boundary |
| FLD-REG-016 | Add New User postcode 4 digits | REG | Logged in as the QA user | 1. Open Add New User<br>2. Enter 2000 in Postcode | 2000 | Accepted | P2 | Validation |
| FLD-REG-017 | Add New User state list has only AU states | REG | Logged in as the QA user | 1. Open Add New User<br>2. Open the State list | - | NSW, VIC, QLD, WA, SA, TAS, ACT, NT only; no duplicates | P2 | Validation |
| FLD-REG-018 | Add New User tag creation | REG | Logged in as the QA user | 1. Open Add New User<br>2. Type Electrician in Tags<br>3. Press Enter | Electrician | Tag created and shown | P3 | Functional |
| FLD-REG-019 | Add Group and assign members | REG | Logged in as the QA user | 1. Open User<br>2. Open Groups<br>3. Add a group<br>4. Choose members<br>5. Save | Electrical Crew | Group lists its members (observed: members showed 0 after an API update) | P1 | Functional |
| FLD-REG-020 | Keyboard-only completion of Add Customer | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Press Tab through every field<br>3. Press Enter on Save | - | Logical focus order; errors are announced | P2 | Accessibility |

#### CKOUT: items, quotes, formulas, invoices, jobs, settings data (30 cases)
| ID | Title | Module | Preconditions | Steps | Test Data (AU) | Expected Result | Priority | Type |
|----|-------|--------|---------------|-------|----------------|-----------------|----------|------|
| FLD-CKOUT-001 | Add Item with sell and cost price | CKOUT | Logged in as the QA user | 1. Open Items<br>2. Click Add Item<br>3. Enter Item Name<br>4. Enter Unit<br>5. Enter Sell Price<br>6. Enter Cost Price<br>7. Enter Description<br>8. Click Save | Labour - Electrician / hour / 110 / 71.50 | Item saved | P0 | Functional |
| FLD-CKOUT-002 | Item cost price above sell price | CKOUT | Logged in as the QA user | 1. Open Add Item<br>2. Enter Sell Price 100<br>3. Enter Cost Price 120<br>4. Click Save | 100 / 120 | Warning or rejection (negative margin); NEEDS UI INSPECTION | P1 | Validation |
| FLD-CKOUT-003 | Item negative sell price | CKOUT | Logged in as the QA user | 1. Open Add Item<br>2. Enter -0.01 in Sell Price<br>3. Click Save | -0.01 | Rejected | P1 | Negative |
| FLD-CKOUT-004 | Item sell price with 3 decimals | CKOUT | Logged in as the QA user | 1. Open Add Item<br>2. Enter 1100.005 in Sell Price<br>3. Click Save | 1100.005 | Rounded or rejected to 2 dp | P2 | Boundary |
| FLD-CKOUT-005 | Item price typed as $1,100.00 | CKOUT | Logged in as the QA user | 1. Open Add Item<br>2. Type $1,100.00 in Sell Price | $1,100.00 | Number field rejects the symbols or normalises | P2 | Validation |
| FLD-CKOUT-006 | Add Invoice with 1 line | CKOUT | Logged in as the QA user | 1. Open Invoices<br>2. Click Add Invoice<br>3. Select Customer<br>4. Enter Invoice Date<br>5. Enter Due Date<br>6. Add a line item<br>7. Click Save | 2 x $630.00 | Sub-total $1,260.00, GST $126.00, total $1,386.00 | P0 | Functional |
| FLD-CKOUT-007 | Invoice GST is 10 percent of the sub-total | CKOUT | Logged in as the QA user | 1. Create an invoice of $1,100.00<br>2. Read the total | $1,100.00 | Total shows $1,210.00 | P0 | Functional |
| FLD-CKOUT-008 | Invoice with line discount | CKOUT | Logged in as the QA user | 1. Add a line with 10 in Discount<br>2. Read totals | 10% | Discount applied before GST | P1 | Functional |
| FLD-CKOUT-009 | Invoice due date before invoice date | CKOUT | Logged in as the QA user | 1. Set Invoice Date 19/09/2026<br>2. Set Due Date 18/09/2026<br>3. Click Save | 18/09/2026 | Rejected | P1 | Negative |
| FLD-CKOUT-010 | Invoice with quantity 0 | CKOUT | Logged in as the QA user | 1. Add a line with Quantity 0<br>2. Click Save | 0 | Rejected or line removed | P1 | Boundary |
| FLD-CKOUT-011 | Invoice with negative rate | CKOUT | Logged in as the QA user | 1. Add a line with Rate -10<br>2. Click Save | -10 | Rejected | P1 | Negative |
| FLD-CKOUT-012 | Invoice without a customer | CKOUT | Logged in as the QA user | 1. Leave Customer empty<br>2. Click Save | empty | Inline error | P1 | Negative |
| FLD-CKOUT-013 | Invoice status order: Draft, Awaiting Approval, Awaiting Payment, Paid | CKOUT | Logged in as the QA user | 1. Create a draft invoice<br>2. Submit for approval<br>3. Approve<br>4. Record payment | - | Each change allowed only in order; dashboard tiles update | P0 | Functional |
| FLD-CKOUT-014 | Invoice amounts cannot be set through the API | CKOUT | Logged in as the QA user | 1. Send PUT invoice/update with amountPaid equal to the total<br>2. Read the invoice | amountPaid = total | Rejected (observed: accepted, finding F1) | P0 | Security |
| FLD-CKOUT-015 | Invoice BSB accepts XXX-XXX only | CKOUT | Logged in as the QA user | 1. Open payment details<br>2. Enter 062000<br>3. Enter 062-000 | 062-000 | Hyphenated format accepted; BSB screen NEEDS UI INSPECTION | P1 | Validation |
| FLD-CKOUT-016 | Company ABN checksum | CKOUT | Logged in as the QA user | 1. Open Settings, Company Settings<br>2. Enter 33 102 417 032<br>3. Enter 12 345 678 901 | valid / invalid ABN | Valid accepted; invalid rejected | P1 | Validation |
| FLD-CKOUT-017 | Add Quote requires at least one item | CKOUT | Logged in as the QA user | 1. Open Quote<br>2. Click Add Quote<br>3. Select Customer<br>4. Enter Quote Description<br>5. Click Next<br>6. Save with no items | no items | Rejected: A quote must contain at least one item | P0 | Negative |
| FLD-CKOUT-018 | Add Quote with sections and items | CKOUT | Logged in as the QA user | 1. Add a Labour section<br>2. Add a line item<br>3. Add a Materials section<br>4. Add a line item<br>5. Save | 2 sections | Quote saved with a serial number | P0 | Functional |
| FLD-CKOUT-019 | Quote formula: Qty x Rate x 1.2 | CKOUT | Logged in as the QA user | 1. Open Quote, Formulas<br>2. Click Add Formula<br>3. Enter a Column Name<br>4. Pick Qty.<br>5. Pick x<br>6. Pick Rate<br>7. Pick x<br>8. Insert 1.2<br>9. Click Save | Qty 10, Rate 50 | Live preview shows 600.00 | P0 | Functional |
| FLD-CKOUT-020 | Quote formula cannot end on an operator | CKOUT | Logged in as the QA user | 1. Add a formula<br>2. Pick Qty.<br>3. Pick x | Qty. x | Save stays disabled until the formula is complete | P1 | Validation |
| FLD-CKOUT-021 | Quote formula column shown on the customer PDF | CKOUT | Logged in as the QA user | 1. Turn on Show to Customer<br>2. Save<br>3. Open the quote PDF | - | Column printed; internal columns hidden | P2 | Functional |
| FLD-CKOUT-022 | Quote line types Labour and Material | CKOUT | Logged in as the QA user | 1. Add a Labour line<br>2. Add a Material line<br>3. Read the quote | labour / material | Types shown correctly | P1 | Functional |
| FLD-CKOUT-023 | Job with a report template attached | CKOUT | Logged in as the QA user | 1. Open a job<br>2. Open Reports<br>3. Attach a template<br>4. Save<br>5. Open Job Report | Electrical Job Completion Report | Report created with status Created | P1 | Functional |
| FLD-CKOUT-024 | Job cap on the Solo plan | CKOUT | Logged in as the QA user | 1. Create 6 active jobs on Solo | 6th job | Blocked with a plan-limit message (observed 403) | P1 | Functional |
| FLD-CKOUT-025 | Job start and end time | CKOUT | Logged in as the QA user | 1. Open Add Job<br>2. Enter Start Date<br>3. Enter End Date<br>4. Save | 16/09/2026 to 17/09/2026 | Job shows on the week schedule | P1 | Functional |
| FLD-CKOUT-026 | Job Site Radius 1 to 10,000 m | CKOUT | Logged in as the QA user | 1. Enter Site Radius 0<br>2. Enter Site Radius 10001 | 0 / 10001 | Both rejected; 1 and 10000 accepted | P2 | Boundary |
| FLD-CKOUT-027 | Holiday create and duplicate date | CKOUT | Logged in as the QA user | 1. Add Holiday 26/01/2026<br>2. Add another on the same date | 26/01/2026 | Second rejected (observed 409) | P2 | Negative |
| FLD-CKOUT-028 | Checklist item order | CKOUT | Logged in as the QA user | 1. Open Checklist<br>2. Add 3 items<br>3. Save | 3 items | Items keep their order | P3 | Functional |
| FLD-CKOUT-029 | Report template builder field types | CKOUT | Logged in as the QA user | 1. Open Report Builder<br>2. Add each field type<br>3. Save | Textbox, Dropdown, Radio, Checkbox, Textarea, Number, Upload, Email, Date | Template saved and renders on a job report | P2 | Functional |
| FLD-CKOUT-030 | Dashboard tiles match the data | CKOUT | Logged in as the QA user | 1. Open Dashboard<br>2. Compare each tile with its list | - | Jobs, Completed, Revenue, Outstanding and Pending counts match the lists | P0 | Regression |

#### CONT: CMS, notifications, legal and contact (15 cases)
| ID | Title | Module | Preconditions | Steps | Test Data (AU) | Expected Result | Priority | Type |
|----|-------|--------|---------------|-------|----------------|-----------------|----------|------|
| FLD-CONT-001 | Terms & Conditions link opens the terms page | CONT | Logged in as the QA user | 1. Open the login page<br>2. Click Terms & Conditions | - | Opens /terms-and-conditions | P1 | Functional |
| FLD-CONT-002 | Privacy Policy link opens the privacy page | CONT | Logged in as the QA user | 1. Open the login page<br>2. Click Privacy Policy | - | Opens /privacy-policy | P1 | Functional |
| FLD-CONT-003 | CMS list shows Type, Created By and Date | CONT | Logged in as the QA user | 1. Open CMS | - | Columns TYPE, CREATED BY, DATE, ACTION shown | P2 | Functional |
| FLD-CONT-004 | Add a CMS entry of each type | CONT | Logged in as the QA user | 1. Click Add CMS<br>2. Select Type<br>3. Enter Title<br>4. Enter Content<br>5. Click Save | Induction, Help, Privacy Policy, Terms & Conditions, FAQ | Entry appears in the list | P1 | Functional |
| FLD-CONT-005 | CMS Title empty | CONT | Logged in as the QA user | 1. Click Add CMS<br>2. Select Type<br>3. Leave Title empty<br>4. Save | empty | Inline error (the API returns 500, finding F3) | P1 | Negative |
| FLD-CONT-006 | CMS Content empty | CONT | Logged in as the QA user | 1. Click Add CMS<br>2. Enter Title<br>3. Leave Content empty<br>4. Save | empty | Inline error | P1 | Negative |
| FLD-CONT-007 | CMS rich text stores a script safely | CONT | Logged in as the QA user | 1. Enter a script tag in Content<br>2. Save<br>3. View the page | XSS payload | Sanitised; no alert | P1 | Security |
| FLD-CONT-008 | CMS Title 255 chars | CONT | Logged in as the QA user | 1. Enter 255 chars in Title<br>2. Save | 255 | Accepted or rejected consistently; limit NEEDS UI INSPECTION | P2 | Boundary |
| FLD-CONT-009 | Notifications page lists events | CONT | Logged in as the QA user | 1. Open Notifications | - | Recent events listed; unread count clears | P2 | Functional |
| FLD-CONT-010 | Notification badge increments after a new job | CONT | Logged in as the QA user | 1. Create a job<br>2. Read the sidebar badge | - | Badge increases by 1 | P3 | Functional |
| FLD-CONT-011 | Help entries are findable | CONT | Logged in as the QA user | 1. Open Help content<br>2. Search for invoice | invoice | Matching entries shown; help UI NEEDS UI INSPECTION | P3 | Functional |
| FLD-CONT-012 | Support contact page exists | CONT | Logged in as the QA user | 1. Look for a Support or Contact page | - | NEEDS UI INSPECTION: no contact form was observed | P2 | Functional |
| FLD-CONT-013 | Contact form rejects an invalid email | CONT | Logged in as the QA user | 1. Open the contact form<br>2. Enter noah.smith@bigpond<br>3. Submit | noah.smith@bigpond | Blocked; depends on the form existing | P2 | Validation |
| FLD-CONT-014 | Contact form mobile format | CONT | Logged in as the QA user | 1. Enter +61 412 345 678<br>2. Enter 0412ABC678 | AU mobiles | First accepted, second rejected | P2 | Validation |
| FLD-CONT-015 | Login footer links are keyboard reachable | CONT | Logged in as the QA user | 1. Open the login page<br>2. Press Tab to the footer links | - | Both links focusable with a visible focus ring | P3 | Accessibility |

### 4. Negative and boundary matrix
One row per field. Counts come from `csv/<field>.csv`; the expected result for every value is in the CSV.

| Field | Total values | Expect accept | Expect reject |
|---|---|---|---|
| abn | 116 | 63 | 53 |
| account_number | 114 | 87 | 27 |
| amount_aud | 107 | 97 | 10 |
| bsb | 118 | 99 | 19 |
| date_of_birth | 115 | 88 | 27 |
| email_address | 105 | 71 | 34 |
| first_name | 104 | 71 | 33 |
| last_name | 104 | 71 | 33 |
| mobile_number | 109 | 73 | 36 |
| otp_code | 108 | 84 | 24 |
| postcode | 134 | 112 | 22 |
| state | 100 | 40 | 60 |
| street_address | 113 | 99 | 14 |
| tfn | 112 | 63 | 49 |

Boundary rules used: mobile 10 national digits; email local part 64 and total 254; OTP exactly 6 digits; postcode 4 digits; account 6 to 9 digits; ABN 11 digits mod-89; TFN 9 digits mod-11; names 1 to 100 (ASSUMPTION); DOB from 01/01/1900.

### 5. ASSUMPTION register
| # | Item | Status |
|---|---|---|
| A1 | Name max length is 100 | NEEDS UI INSPECTION |
| A2 | Address max length is 254 | NEEDS UI INSPECTION |
| A3 | OTP validity window and replay behaviour | Unknown; the bypass OTP is static |
| A4 | Idle timeout length | Unknown |
| A5 | Logout menu label | Not observed (spec uses a regex) |
| A6 | Email-login bypass OTP applies to email | Unverified |
| A7 | RBAC roles beyond Customer and User | Not observed; Roles & Permissions is a Business-plan feature |
| A8 | Self sign-up and a public Contact page | Not observed |
| A9 | The master prompt lists 7999 and 9999 as invalid postcodes, 0200 as NT, and +61 12 345 6789 as too short | Conflicts with the real ranges: TAS is 7000-7999, QLD PO boxes reach 9999, 0200-0299 is ACT, and that number is 10 digits without a mobile prefix. The CSVs follow the real ranges |
| A10 | Payment-card and BSB screens | Not observed |

### 6. Risks and mitigation
| Risk | Mitigation |
|---|---|
| A live SMS OTP is not testable | Use the QA bypass OTP; keep expiry and replay cases manual |
| Brute-force cases can lock the shared bypass account | AUTH-038 is skipped unless FLDR_ALLOW_LOCKOUT=1 |
| Seeded mobiles may belong to real people | Keep SMS notifications off; prefer ACMA-reserved numbers |
| The app reloads on deploy and drops open forms | Run UI cases in short bursts and re-verify saved values |
| Timesheet and crew tiles cannot be filled | Needs the mobile clock-on payload or a seat upgrade |
| Plan limits change results (5 jobs on Solo, 1 seat on Basic) | Record the plan in every run |

## 5. Test data table
## Test data table (AU library)

Values are used verbatim. They are typed only unless a case says otherwise. Full per-field lists with expected results are in `csv/` (each file has 100+ rows).

### Mobile
| Kind | Values |
|---|---|
| Valid | +61 412 345 678, +61 423 456 789, +61 434 567 890, +61 458 901 234, +61 401 234 567 |
| National | 0412 345 678, 0423 456 789 |
| Negative | +61 12 345 6789 (no mobile prefix), +1 412 345 6789 (US), +61 4 (prefix only), 0412ABC678, whitespace, emoji |
| Boundary | 9, 10, 11, 12 and 15 digits |
| Warning | 0412 345 678 and 0491 570 159 were already registered to other accounts; do not submit them |

### Email
| Kind | Values |
|---|---|
| Valid | olivia.nguyen@example.com.au, noah.smith@bigpond.net.au, mia.collins@aussie.com.au, jack.wilson+invoices@gmail.com |
| Seeded records | @yopmail.com only |
| Negative | no @, missing TLD, double dot, leading or trailing space, IDN homoglyph, local part over 64 |
| Boundary | local 1, 64 and 65 chars; total 254, 255 and 256 chars |

### OTP
| Kind | Values |
|---|---|
| QA bypass | set in `.env` as FLDR_OTP (6 digits) |
| Valid format | 100000, 999999, 482913 |
| Negative | 99999 (5 digits), 1000000 (7 digits), abcdef, empty, 12 34 56, 000000, 111111 |

### Addresses
| State | Address |
|---|---|
| NSW | 12 Macquarie Street, Sydney NSW 2000 |
| VIC | 88 Bourke Street, Melbourne VIC 3000 |
| QLD | 145 Eagle Street, Brisbane QLD 4000 |
| WA | 27 Adelaide Terrace, Perth WA 6000 |
| SA | 101 Rundle Mall, Adelaide SA 5000 |
| TAS | 9 Brisbane Street, Hobart TAS 7000 |
| ACT | 21 London Circuit, Canberra ACT 2601 |
| NT | 76 Mitchell Street, Darwin NT 0800 |

Postcode ranges used: ACT 0200-0299, 2600-2618, 2900-2920; NT 0800-0999; NSW 1000-2599, 2619-2898, 2921-2999; VIC 3000-3999, 8000-8999; QLD 4000-4999, 9000-9999; SA 5000-5999; WA 6000-6999; TAS 7000-7999.

### Finance identifiers
| Kind | Values |
|---|---|
| ABN valid | 33 102 417 032 (mod-89) |
| ABN invalid | 12 345 678 901 |
| TFN valid | 123 456 782 (mod-11) |
| TFN invalid | 123 456 789 |
| BSB | 062-000, 123-456, 032-198 |
| Account | 6 to 9 digits; negatives: letters, more than 4 leading zeros |
| Currency | AUD, "$" prefix, 2 decimals, GST 10% (subtotal $1,100.00 gives total $1,210.00) |

### Names
First: Olivia, Noah, Mia, Jack, Aria, Liam, Charlotte, William, Zoe, Ethan. Last: Nguyen, Smith, Collins, Wilson, Patel, Brown, Anderson, Lee, Khan, White. Negatives: User1234, emoji only, 200+ characters, only spaces.
The seed script uses a wider pool of 50 first and 50 last names so seeded customers have unique full names.

### Dates (dd/mm/yyyy)
Valid: 14/02/1990, 29/02/2000 (leap), 01/01/1900, 31/12/2025. Invalid: 29/02/1900, 31/04/2024, 32/01/2024, 00/01/2024, 13/13/2024.

### Files generated
| File | Rows |
|---|---|
| csv/abn.csv | 116 |
| csv/account_number.csv | 114 |
| csv/amount_aud.csv | 107 |
| csv/bsb.csv | 118 |
| csv/date_of_birth.csv | 115 |
| csv/email_address.csv | 105 |
| csv/first_name.csv | 104 |
| csv/last_name.csv | 104 |
| csv/mobile_number.csv | 109 |
| csv/otp_code.csv | 108 |
| csv/postcode.csv | 134 |
| csv/state.csv | 100 |
| csv/street_address.csv | 113 |
| csv/tfn.csv | 112 |

## 6. How to run the code
```
# 1. data files
python gen_csv.py            # csv/*.csv
python gen_avatars.py        # seed-images/avatar-001..100.png
python gen_pw.py             # pw/ project + specs + auth-test-cases.md
python gen_plan.py           # test-plan.md, test-data-table.md
python gen_handover.py       # this document

# 2. seed the tenant (log in in a browser first, copy the connect.sid cookie value)
set FLDR_COOKIE=<connect.sid value>
set FLDR_BASE_URL=https://rajanjagz7.dev.fieldr.app
python fieldr_seed.py --customers 100 --items 100 --invoices 100 --jobs 60 --avatars seed-images
python fieldr_seed.py --fix-items --quotes 100 --cms --holidays --settings-data
python fieldr_seed.py --enrich-jobs --fill-reports --invoice-statuses
```
Notes: never commit `FLDR_COOKIE`, the OTP or `pw/.env`. `--invoice-statuses` relies on finding F1 (client-set payment fields), so use it on a throwaway tenant only. The seeded mobile numbers may belong to real people, so keep SMS notifications off.

## 7. Source code

### 7.1 `fieldr_seed.py`
Seeds the tenant through the REST API (customers, items, invoices, jobs, quotes, formulas, CMS, holidays, checklists, templates, job enrichment, report filling, invoice statuses).

```python
"""
Fieldr QA data seeder (Python port of the browser-side seeding used in this session).

What it does (all data is fictional, AU-flavoured, deterministic):
  customers  - unique AU names, @yopmail.com emails, unique realistic AU mobiles, AU addresses, optional profile photo
  items      - trade items in price tiers, each with a DIFFERENT margin (cost price vs sell price)
  invoices   - 1-3 line items, 10% GST is calculated by the server
  jobs       - varied statuses, dated this week so dashboard tiles fill

Auth: the OTP endpoints were not captured during the session, so this script uses your logged-in
browser session. Log in once (OTP), copy the `connect.sid` cookie value from DevTools > Application > Cookies,
and export it. Never commit it.

    set FLDR_COOKIE=s%3A....            (Windows cmd)     export FLDR_COOKIE='s%3A....'   (bash)
    set FLDR_BASE_URL=https://<tenant>.dev.fieldr.app
    python fieldr_seed.py --customers 100 --items 100 --invoices 100 --jobs 60 --avatars seed-images
    python fieldr_seed.py --fix-items --quotes 100 --cms --holidays --settings-data
    python fieldr_seed.py --enrich-jobs --fill-reports --invoice-statuses      (run last: needs templates, jobs and invoices first)

Not covered (blocked or undiscovered): users and groups (seat-limited, API-created users are invisible), timesheets/crew (POST /timelog/create stores nothing).

Known platform limits seen on the dev tenant (plan/seat gated - not bugs in this script):
  * Solo plan: max 5 active jobs (403 planLimitReached).  Basic plan lifts it.
  * Basic plan: 1 user seat. Users created over the API succeed but never appear in the UI.
  * Mobile numbers must be unique across ALL tenants (400/409 "already registered").
"""
import argparse
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests

BASE = os.environ.get("FLDR_BASE_URL", "https://rajanjagz7.dev.fieldr.app").rstrip("/")
COOKIE = os.environ.get("FLDR_COOKIE", "")
HEADERS = {"x-device-type": "web", "content-type": "application/json"}

FIRST = ["Olivia", "Noah", "Mia", "Jack", "Aria", "Liam", "Charlotte", "William", "Zoe", "Ethan", "Amelia", "Oliver", "Isla", "Lucas", "Grace",
         "Henry", "Ruby", "Leo", "Chloe", "Thomas", "Sophie", "Mason", "Emily", "Archer", "Matilda", "Harrison", "Ella", "Riley", "Hannah", "Cooper",
         "Lily", "Hunter", "Evie", "Max", "Sienna", "Jacob", "Georgia", "Xavier", "Willow", "Sebastian", "Piper", "Angus", "Frankie", "Hamish",
         "Tahlia", "Kai", "Imogen", "Callum", "Maddison", "Dylan"]
LAST = ["Nguyen", "Smith", "Collins", "Wilson", "Patel", "Brown", "Anderson", "Lee", "Khan", "White", "Taylor", "Martin", "Thompson", "Walker",
        "Harris", "Clarke", "Robinson", "Young", "Kelly", "Ryan", "Murphy", "Campbell", "Stewart", "Morgan", "Reid", "Bennett", "Fraser", "Mitchell",
        "Hughes", "Cameron", "Singh", "Chen", "Wang", "Tran", "Kaur", "Sharma", "Papadopoulos", "Rossi", "Kovacs", "Hassan", "OConnor", "McDonald",
        "Sutherland", "Ferguson", "Grant", "Hayes", "Barker", "Doyle", "Watts", "Lawson"]
ADDR = [("12 Macquarie Street", "Sydney", "NSW", "2000"), ("88 Bourke Street", "Melbourne", "VIC", "3000"), ("145 Eagle Street", "Brisbane", "QLD", "4000"),
        ("27 Adelaide Terrace", "Perth", "WA", "6000"), ("101 Rundle Mall", "Adelaide", "SA", "5000"), ("9 Brisbane Street", "Hobart", "TAS", "7000"),
        ("21 London Circuit", "Canberra", "ACT", "2601"), ("76 Mitchell Street", "Darwin", "NT", "0800")]
PREFIX = ["412", "423", "434", "458", "401", "417", "438", "449", "466", "477", "421", "431", "404", "415", "429"]
ITEMS = [("Labour - Electrician", "hour", 110), ("Labour - Plumber", "hour", 105), ("Labour - Apprentice", "hour", 65), ("Labour - Site Supervisor", "hour", 135),
         ("Call-out Fee", "each", 89), ("LED Downlight 10W", "each", 24.5), ("Power Point Double GPO", "each", 18.9), ("Circuit Breaker 20A", "each", 32),
         ("Safety Switch RCD", "each", 78), ("Copper Pipe 15mm", "metre", 12.4), ("PVC Pipe 50mm", "metre", 8.75), ("Mixer Tap Chrome", "each", 145),
         ("Hot Water Unit 250L", "each", 1290), ("Split System Install", "each", 850), ("Air Con Service", "each", 180), ("Smoke Alarm 240V", "each", 49),
         ("Cable TPS 2.5mm", "metre", 3.2), ("Conduit 20mm", "metre", 2.1), ("Concrete Slab 100mm", "sqm", 95), ("Paint Interior 10L", "each", 132),
         ("Gutter Cleaning", "each", 220), ("Lawn Mow & Edge", "each", 75), ("Pressure Wash", "sqm", 6.5), ("Skip Bin 6m3", "each", 420), ("Traffic Control", "hour", 98)]
TIERS = [("Standard", 1.0), ("Premium", 1.25), ("Bulk", 0.9), ("Weekend", 1.5)]
JOBS = ["Switchboard Upgrade", "Hot Water Replacement", "Split System Install", "Downlight Retrofit", "Blocked Drain Clearing", "Bathroom Re-plumb",
        "Smoke Alarm Compliance", "EV Charger Install", "Roof Gutter Repair", "Kitchen Tap Replacement", "Solar Inverter Service",
        "Backflow Prevention Test", "Pool Pump Repair", "Ceiling Fan Install", "Safety Inspection"]


class Fieldr:
    def __init__(self):
        if not COOKIE:
            sys.exit("Set FLDR_COOKIE (connect.sid value from a logged-in browser session).")
        self.s = requests.Session()
        self.s.cookies.set("connect.sid", COOKIE)
        self.s.headers.update(HEADERS)

    def call(self, method, path, **kw):
        r = self.s.request(method, f"{BASE}/api/v1{path}", timeout=30, **kw)
        try:
            body = r.json()
        except ValueError:
            body = {"raw": r.text[:200]}
        return r.status_code, body

    def logged_in(self):
        code, _ = self.call("GET", "/auth/is-logged-in")
        return code == 200

    def list(self, resource, limit=200):
        code, body = self.call("GET", f"/{resource}/list", params={"query": "", "skip": 0, "limit": limit})
        return body.get("data", []) if code == 200 else []

    def upload_image(self, path: Path):
        """multipart POST /aws/upload-file (field 'files') -> public fileUrl"""
        headers = {k: v for k, v in HEADERS.items() if k != "content-type"}  # let requests set the multipart boundary
        with path.open("rb") as fh:
            r = self.s.post(f"{BASE}/api/v1/aws/upload-file", headers=headers, files={"files": (path.name, fh, "image/png")}, timeout=60)
        r.raise_for_status()
        return r.json()["data"][0]["fileUrl"]


def national_mobile(seed_index, used):
    """Deterministic realistic 04xx xxx xxx. NOTE: may belong to a real person - keep SMS notifications OFF on the tenant."""
    x = 20260919 + seed_index * 7919
    while True:
        x = (x * 1103515245 + 12345) % 2147483648
        n = "0" + PREFIX[x % len(PREFIX)] + str(100000 + (x >> 8) % 899999)
        if n not in used:
            used.add(n)
            return n


def seed_customers(api, count, avatars_dir):
    existing = api.list("customer")
    used = {"0" + c["phone"] for c in existing}
    have = len(existing)
    ok = fail = 0
    for i in range(have, count):
        first, last = FIRST[i % 50], LAST[(i * 7 + i // 50 * 3 + i) % 50]
        street, city, st, pc = ADDR[i % 8]
        body = {"firstName": first, "lastName": last, "name": f"{first} {last}", "phone": national_mobile(i, used),
                "email": f"{first}.{last}.{i + 1:03d}@yopmail.com".lower(), "address": f"{(i * 7) % 190 + 1} {street.split(' ', 1)[1]}, {city} {st} {pc}",
                "description": f"QA seed customer {i + 1:03d} - {city} {st}. Fictional test data.", "profilePicture": "", "countryCode": "+61", "countryFlag": "au"}
        if avatars_dir:
            img = Path(avatars_dir) / f"avatar-{i % 100 + 1:03d}.png"
            if img.exists():
                body["profilePicture"] = api.upload_image(img)
        code, resp = api.call("POST", "/customer/create", json=body)
        ok, fail = (ok + 1, fail) if code == 200 else (ok, fail + 1)
        if code != 200:
            print("customer", i + 1, code, resp.get("message"))
    print(f"customers: +{ok} ok, {fail} failed (had {have})")


def seed_items(api, count):
    have = len(api.list("item"))
    ok = 0
    margins = set()
    n = 0
    for tier, mult in TIERS:
        for name, unit, price in ITEMS:
            n += 1
            if n <= have:
                continue
            if n > count:
                break
            rate = round(price * mult, 2)
            m = round(12 + ((n * 37) % 431) / 10, 1)  # 12.0% - 55.0%, different per item
            while m in margins:
                m = round(m + 0.1, 1)
            margins.add(m)
            body = {"name": f"{name} ({tier})", "unit": unit, "rate": rate, "costPrice": round(rate * (1 - m / 100), 2),
                    "description": f"{name} - {tier} tier. AUD ex-GST. Fictional test item."}
            code, resp = api.call("POST", "/item/create", json=body)
            ok += code == 200
            if code != 200:
                print("item", n, code, resp.get("message"))
    print(f"items: +{ok} ok (had {have})")


def seed_invoices(api, count):
    customers, items = api.list("customer", 500), api.list("item", 500)
    if not customers or not items:
        sys.exit("Seed customers and items first.")
    have = len(api.list("invoice"))
    ok = 0
    for i in range(have, count):
        lines = []
        for k in range(1 + i % 3):
            it = items[(i * 7 + k * 13) % len(items)]
            lines.append({"itemId": it["_id"], "item": it["_id"], "name": it["name"], "description": it["description"], "unit": it["unit"],
                          "quantity": 1 + (i + k) % 5, "rate": it["rate"], "discount": 10 if (i % 10 == 0 and k == 0) else 0, "tax": 10, "taxRate": 10})
        inv = date(2026, 7, 1) + timedelta(days=i % 80)
        body = {"customer": customers[(i * 3) % len(customers)]["_id"], "invoiceDate": inv.isoformat(), "dueDate": (inv + timedelta(days=30)).isoformat(), "lineItems": lines}
        code, resp = api.call("POST", "/invoice/create", json=body)
        ok += code == 200
        if code != 200:
            print("invoice", i + 1, code, resp.get("message"))
    print(f"invoices: +{ok} ok (had {have})")


def seed_jobs(api, per_status, week_start):
    customers = api.list("customer", 500)
    if not customers:
        sys.exit("Seed customers first.")
    ok = n = 0
    for status in ("In Progress", "On Hold", "Completed", "Schedule", "Cancelled"):
        for _ in range(per_status):
            n += 1
            c = customers[(n * 7) % len(customers)]
            day = (week_start + timedelta(days=n % 7)).isoformat()
            body = {"title": f"{JOBS[n % len(JOBS)]} - {c['firstName']} {c['lastName']} [{status}] #{n:03d}", "clientId": c["_id"], "date": day, "endDate": day,
                    "address": c["address"], "siteRadius": 100, "description": f"{JOBS[n % len(JOBS)]} at {c['address']}. Fictional QA seed job.", "status": status}
            code, resp = api.call("POST", "/job/create", json=body)
            ok += code == 200
            if code == 403:
                print("Job limit reached:", resp.get("data"))
                print(f"jobs: +{ok} ok")
                return
    print(f"jobs: +{ok} ok")


# ---------------------------------------------------------------------------------------------
# Added after the full walkthrough. Every payload below was observed working on the dev tenant.
# ---------------------------------------------------------------------------------------------
CITY_GEO = {"Sydney": (-33.8688, 151.2093), "Melbourne": (-37.8136, 144.9631), "Brisbane": (-27.4698, 153.0251), "Perth": (-31.9505, 115.8605),
            "Adelaide": (-34.9285, 138.6007), "Hobart": (-42.8821, 147.3272), "Canberra": (-35.2809, 149.13), "Darwin": (-12.4634, 130.8456)}
LABOUR = ("Labour", "Call-out", "Traffic Control", "Split System Install", "Air Con Service", "Gutter Cleaning", "Lawn Mow", "Pressure Wash")


def fix_items(api):
    """Labour/service items -> lineType 'labour' (the default was 'material' for everything). Margins already differ per item (seed_items)."""
    n = 0
    for it in api.list("item", 500):
        lt = "labour" if it.get("unit") == "hour" or it["name"].startswith(LABOUR) else "material"
        n += api.call("PUT", f"/item/update/{it['_id']}", json={**it, "lineType": lt})[0] == 200
    print(f"items retyped: {n}")


def _tokens(*parts):
    return [{"type": "op" if p in "+-*/" else "field" if p.isalpha() else "num", "value": p} for p in parts]


def seed_formulas(api):
    """Quote formulas. Tokens: field (quantity|rate|discount|tax|finalAmount), op (+ - * /), num. NOT a raw expression string."""
    defs = [("Line Total with 20% Markup", ["quantity", "*", "rate", "*", "1.2"], False), ("Cost plus 35% margin", ["quantity", "*", "rate", "*", "1.35"], False),
            ("GST amount (10%)", ["quantity", "*", "rate", "*", "tax", "/", "100"], True), ("Labour with 15% overhead", ["quantity", "*", "rate", "*", "1.15"], False),
            ("Trade discount amount", ["quantity", "*", "rate", "*", "discount", "/", "100"], True)]
    have = {f["name"]: f["_id"] for f in api.list("quote-formula", 100)}
    ids = {}
    for name, toks, show in defs:
        if name in have:
            ids[name] = have[name]
            continue
        _, r = api.call("POST", "/quote-formula/create", json={"name": name, "description": name, "expression": " ".join(toks), "tokens": _tokens(*toks),
                                                                "inputs": [], "decimals": 2, "showToCustomer": show, "isActive": True})
        ids[name] = r.get("data", {}).get("_id")
    return ids


def seed_quotes(api, count):
    """Quotes need sections[].items[]; formulas attach as section.formulaColumns=[{formulaId}]. formulaValues holds LINE-INPUT values, never results."""
    customers, items, fids = api.list("customer", 500), api.list("item", 500), seed_formulas(api)
    lab = [fids["Labour with 15% overhead"], fids["Line Total with 20% Markup"]]
    mat = [fids["Cost plus 35% margin"], fids["GST amount (10%)"], fids["Trade discount amount"]]
    desc = ["Bathroom renovation", "Kitchen rewire and downlights", "Split system supply and install", "Hot water system replacement", "Switchboard upgrade",
            "Storm-damage gutter repair", "Deck and pergola electrics", "Blocked drain relining", "Smoke alarm compliance upgrade", "EV charger installation"]

    def line(it, q):
        return {"itemId": it["_id"], "item": it["_id"], "name": it["name"], "description": it["description"], "unit": it["unit"], "quantity": q,
                "rate": it["rate"], "discount": 0, "tax": 10, "taxRate": 10, "lineType": it.get("lineType", "material"), "formulaValues": []}
    have = len(api.list("quote", 500))
    ok = 0
    for i in range(have, count):
        c = customers[(i * 3 + 1) % len(customers)]
        labour, m1, m2 = items[(i * 5) % len(items)], items[(i * 11 + 3) % len(items)], items[(i * 13 + 7) % len(items)]
        sections = [{"name": "Labour", "items": [line(labour, 2 + i % 6)], "formulaColumns": [{"formulaId": f} for f in lab[: 1 + i % 2]]},
                    {"name": "Materials", "items": [line(m1, 1 + i % 4)] + ([line(m2, 1 + i % 3)] if i % 2 else []),
                     "formulaColumns": [{"formulaId": f} for f in mat[: 1 + i % 3]]}]
        code, _ = api.call("POST", "/quote/create", json={"customer": c["_id"], "description": f"{desc[i % 10]} - {c['name']}, {c['address']}. Fictional QA quote.", "sections": sections})
        ok += code == 200
    print(f"quotes: +{ok}")


def seed_cms(api):
    """type is the DISPLAY name: Induction | Help | Privacy Policy | Terms & Conditions | FAQ (the API returns 500 on a bad value)."""
    pages = {"Induction": ["Site induction - NSW construction sites", "Working at heights", "Electrical safety and lock-out tag-out", "Manual handling", "Asbestos awareness", "PPE", "Incident reporting", "Working in heat"],
             "Help": ["How to clock on to a job", "Creating an invoice from a job report", "Adding a customer", "Sending a quote", "Scheduling a crew", "Recording timesheets", "Exporting reports", "Contacting support"],
             "Privacy Policy": ["Australian Privacy Principles", "Information we collect", "How we use information", "Disclosure to third parties", "Overseas disclosure", "Access and correction", "Data breach notification", "Cookies"],
             "Terms & Conditions": ["Terms of service", "Fees, GST and payment", "Acceptable use", "Subscription and cancellation", "Limitation of liability", "Intellectual property", "Governing law (NSW)", "Changes to terms"],
             "FAQ": ["How do I book a callout in NSW?", "Do prices include GST?", "Payment methods", "Are electricians licensed?", "Do you service regional VIC and QLD?", "Warranty", "Rescheduling", "Invoice copies"]}
    ok = sum(api.call("POST", "/cms/create", json={"type": t, "title": ti, "content": f"<p>{ti}. Fictional QA content for Australian field services.</p>"})[0] == 200
             for t, ts in pages.items() for ti in ts)
    print(f"cms: +{ok}")


def seed_holidays(api):
    """One per date (409 on duplicates)."""
    nat = "National public holiday."
    hol = [("New Year's Day", "2026-01-01", nat), ("Australia Day", "2026-01-26", nat), ("Labour Day (WA)", "2026-03-02", "WA"), ("Labour Day (VIC)", "2026-03-09", "VIC"),
           ("Good Friday", "2026-04-03", nat), ("Easter Saturday", "2026-04-04", "Most states"), ("Easter Sunday", "2026-04-05", "NSW VIC QLD ACT SA NT"), ("Easter Monday", "2026-04-06", nat),
           ("Anzac Day", "2026-04-25", nat), ("Labour Day (QLD)", "2026-05-04", "QLD"), ("Adelaide Cup Day", "2026-05-18", "SA"), ("Reconciliation Day", "2026-06-01", "ACT"),
           ("King's Birthday", "2026-06-08", "All except WA and QLD"), ("Picnic Day", "2026-08-03", "NT"), ("Royal Queensland Show", "2026-08-12", "Brisbane"),
           ("Labour Day (NSW)", "2026-10-05", "NSW"), ("Melbourne Cup Day", "2026-11-03", "Melbourne"), ("Christmas Day", "2026-12-25", nat), ("Boxing Day", "2026-12-26", nat)]
    print("holidays:", sum(api.call("POST", "/holiday/create", json={"name": n, "date": d, "description": ds})[0] == 200 for n, d, ds in hol))


def seed_checklists_and_templates(api):
    """Basic plan caps checklists and report templates at 3 each. Checklist items use 'label'. Template fields are free-form; type+label render in the builder."""
    cl = {"Pre-start safety check - electrical": ["PPE worn", "Test and tag current", "Circuit isolated and locked", "Voltage tested dead", "RCD tested"],
          "Plumbing job completion checklist": ["Pressure test passed", "No leaks", "Tempering valve tested", "Compliance certificate lodged"],
          "Smoke alarm compliance inspection": ["Alarms interconnected", "Alarm within 3 years of manufacture", "Test button operates", "Compliance form signed"]}
    have = {c["name"]: c["_id"] for c in api.list("checklist", 50)}
    for name, labels in cl.items():
        cid = have.get(name) or api.call("POST", "/checklist/create", json={"name": name, "description": name})[1].get("data", {}).get("_id")
        if cid:
            api.call("PUT", f"/checklist/update/{cid}", json={"name": name, "description": name, "items": [{"label": x} for x in labels]})

    def f(t, label, req=False, opts=None):
        d = {"type": t, "label": label, "name": label.lower().replace(" ", "_"), "required": req}
        if opts:
            d["options"] = [{"label": o, "value": o} for o in opts]
        return d
    tpl = {"Electrical Job Completion Report": [f("textbox", "Site address", True), f("date", "Date of work", True), f("radio", "Circuit tested and RCD operational", True, ["Yes", "No", "N/A"]),
                                                f("textarea", "Work summary", True), f("upload", "Photos of completed work")],
           "Plumbing Compliance Report": [f("textbox", "Site address", True), f("date", "Inspection date", True), f("radio", "Pressure test passed", True, ["Yes", "No"]), f("textarea", "Defects found")],
           "Site Safety Inspection Report": [f("textbox", "Site address", True), f("radio", "PPE worn by all crew", True, ["Yes", "No"]),
                                             f("dropdown", "Risk rating", False, ["Low", "Medium", "High", "Critical"]), f("textarea", "Hazards identified")]}
    have = {t["title"]: t["_id"] for t in api.list("template", 50)}
    for title, fields in tpl.items():
        tid = have.get(title) or api.call("POST", "/template/add", json={"title": title})[1].get("data", {}).get("_id")  # create is /template/add
        if tid:
            api.call("PUT", f"/template/edit/{tid}", json={"title": title, "fields": fields})  # edit is /template/edit/:id


def _epoch_ms(d, hour_utc):
    return ((d - date(1970, 1, 1)).days * 24 + hour_utc) * 3600 * 1000


def enrich_jobs(api):
    """Give every job dates (epoch ms, AEST = UTC+10), coordinates, report templates, checklists and planned items.
    Attaching templates to a job auto-creates one Job Report (status 'Created') per template. Partial PUT is supported."""
    jobs, items = api.list("job", 300), api.list("item", 300)
    tpls, cls = [t["_id"] for t in api.list("template", 20)], [c["_id"] for c in api.list("checklist", 20)]
    for i, j in enumerate(jobs):
        city = next((c for c in CITY_GEO if c in (j.get("address") or "")), "Sydney")
        la, lo = CITY_GEO[city]
        jit = ((i * 37) % 100 - 50) / 5000
        off = 7 + i % 26 if j["status"] == "Schedule" else (i % 14) - 3 if j["status"] == "Cancelled" else i % 7
        start = _epoch_ms(date(2026, 9, 13) + timedelta(days=off), -10 + 7 + i % 3)
        body = {"_id": j["_id"], "startDateAndTime": start, "endDateAndTime": start + (6 + i % 4) * 3600 * 1000, "latitude": la + jit, "longitude": lo + jit,
                "reports": [{"reportId": t, "isMandatory": (i + k) % 2 == 0} for k, t in enumerate(tpls[: 1 + i % 3])],
                "checklists": [{"checklistId": c, "isMandatory": (i + k) % 3 == 0} for k, c in enumerate(cls[: 1 + i % 3])],
                "plannedItems": [{"itemId": it["_id"], "item": it["_id"], "name": it["name"], "unit": it["unit"], "quantity": 1 + (i + k) % 6, "rate": it["rate"], "costPrice": it["costPrice"]}
                                 for k, it in [(k, items[(i * 7 + k * 11) % len(items)]) for k in range(2 + i % 2)]]}
        api.call("PUT", f"/job/update/{j['_id']}", json=body)
    print(f"jobs enriched: {len(jobs)}")


def fill_job_reports(api):
    """Set a status and a value on every report field (key 'value'). Statuses other than Created are free text on the API."""
    reports = api.list("job/report", 500)
    statuses = ["Created", "Submitted", "Approved", "Rejected"]
    addr = [f"{a[0]}, {a[1]} {a[2]} {a[3]}" for a in ADDR]
    for i, r in enumerate(reports):
        fields = []
        for f in r.get("fields", []):
            t, lab, opts = f.get("type"), f.get("label", "").lower(), f.get("options") or []
            if t == "date":
                v = f"2026-09-{10 + i % 9:02d}"
            elif "address" in lab:
                v = addr[i % 8]
            elif t in ("radio", "dropdown") and opts:
                v = opts[i % len(opts)]["value"]
            elif t == "number":
                v = 2 + i % 8
            elif t == "textarea":
                v = "Work completed and tested. Fictional QA report."
            elif t == "upload":
                v = ""
            else:
                v = f"Entry {i + 1}"
            fields.append({**f, "value": v})
        api.call("PUT", f"/job/report/update/{r['_id']}", json={"_id": r["_id"], "status": statuses[i % 4], "fields": fields})
    print(f"job reports filled: {len(reports)}")


def set_invoice_statuses(api):
    """Real UI statuses: Draft | Awaiting Approval | Awaiting Payment | Paid. Other strings are accepted by the API but vanish from the dashboard.
    NOTE: the API also accepts amountPaid/amountDue/payments from the client (finding F1) - use only on a throwaway tenant."""
    methods = ["Bank Transfer", "Credit Card", "Cheque", "Cash"]
    for i, d in enumerate(api.list("invoice", 500)):
        if not d.get("totalAmount"):
            continue
        k = i % 20
        if k < 11:
            day = f"2026-09-{13 + i % 7:02d}"
            body = {"status": "Paid", "amountPaid": d["totalAmount"], "amountDue": 0,
                    "payments": [{"amount": d["totalAmount"], "method": methods[i % 4], "reference": f"{d.get('serialNumber', i)} BSB 062-000", "date": day, "paidAt": day + "T00:00:00.000Z"}]}
        else:
            body = {"status": "Awaiting Payment" if k < 16 else "Awaiting Approval" if k < 18 else "Draft"}
        api.call("PUT", f"/invoice/update/{d['_id']}", json={"_id": d["_id"], **body})


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--quotes", type=int, default=0)
    p.add_argument("--cms", action="store_true")
    p.add_argument("--holidays", action="store_true")
    p.add_argument("--settings-data", action="store_true", help="checklists + report templates (Basic plan max 3 each)")
    p.add_argument("--fix-items", action="store_true")
    p.add_argument("--enrich-jobs", action="store_true", help="dates, coordinates, templates, checklists, planned items")
    p.add_argument("--fill-reports", action="store_true")
    p.add_argument("--invoice-statuses", action="store_true")
    p.add_argument("--customers", type=int, default=0)
    p.add_argument("--items", type=int, default=0)
    p.add_argument("--invoices", type=int, default=0)
    p.add_argument("--jobs", type=int, default=0, help="jobs PER STATUS (5 statuses)")
    p.add_argument("--avatars", default="", help="folder of avatar-001.png ... (see gen_avatars.py)")
    p.add_argument("--week-start", default="2026-09-13", help="Sunday of the dashboard week, YYYY-MM-DD")
    a = p.parse_args()
    api = Fieldr()
    if not api.logged_in():
        sys.exit("Cookie rejected: log in again and refresh FLDR_COOKIE.")
    if a.customers:
        seed_customers(api, a.customers, a.avatars)
    if a.items:
        seed_items(api, a.items)
    if a.invoices:
        seed_invoices(api, a.invoices)
    if a.jobs:
        seed_jobs(api, a.jobs, date.fromisoformat(a.week_start))
    # Order matters: items -> (fix types) -> quotes; settings data -> jobs enriched -> reports filled.
    if a.fix_items:
        fix_items(api)
    if a.quotes:
        seed_quotes(api, a.quotes)
    if a.cms:
        seed_cms(api)
    if a.holidays:
        seed_holidays(api)
    if a.settings_data:
        seed_checklists_and_templates(api)
    if a.enrich_jobs:
        enrich_jobs(api)
    if a.fill_reports:
        fill_job_reports(api)
    if a.invoice_statuses:
        set_invoice_statuses(api)


if __name__ == "__main__":
    t = time.time()
    main()
    print(f"done in {time.time() - t:.1f}s")
```

### 7.2 `gen_csv.py`
Generates the 14 per-field AU CSVs (100+ rows each) with computed expected results (ABN mod-89, TFN mod-11, postcode ranges, leap years).

```python
"""Generate per-field AU CSVs (>=100 rows each). Deterministic: no randomness, no clock."""
import csv, datetime, os, re

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "csv")
os.makedirs(OUT, exist_ok=True)
HDR = ["field_name", "value_as_user_typed", "value_normalised", "expected_validator_result", "reason"]
OBS = "OBSERVED"
ASM = "ASSUMPTION-needs-UI-inspection"
MIN_ROWS = 100
COUNTS = {}


def write(field, rows):
    seen, uniq = set(), []
    for r in rows:  # de-duplicate on typed value so every row is a distinct test value
        if r[0] not in seen:
            seen.add(r[0])
            uniq.append(r)
    assert len(uniq) >= MIN_ROWS, f"{field}: only {len(uniq)} rows"
    with open(os.path.join(OUT, f"{field}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(HDR)
        for typed, norm, exp, why in uniq:
            w.writerow([field, typed, norm, exp, why])
    COUNTS[field] = len(uniq)


def lcg(seed):
    x = seed
    while True:
        x = (x * 1103515245 + 12345) % 2147483648
        yield x


FIRST = ["Olivia", "Noah", "Mia", "Jack", "Aria", "Liam", "Charlotte", "William", "Zoe", "Ethan"]
LAST = ["Nguyen", "Smith", "Collins", "Wilson", "Patel", "Brown", "Anderson", "Lee", "Khan", "White"]
INJECT = ["<script>alert(1)</script>", "\"><img src=x onerror=alert(1)>", "'; DROP TABLE users;--", "' OR '1'='1", "1; SELECT pg_sleep(5)--",
          "{{7*7}}", "${7*7}", "../../etc/passwd", "%00", "<svg/onload=alert(1)>"]

# ---------- mobile_number (observed: +61 prefix, mask "+61 (04) XXXX XXXX", placeholder "04xx xxx xxx")
def mob_norm(s):
    d = re.sub(r"\D", "", s)
    if d.startswith("61"):
        d = d[2:]
    if d.startswith("0"):
        d = d[1:]
    return "+61" + d


def mob_valid(s):
    return bool(re.fullmatch(r"\+614\d{8}", mob_norm(s))) and not re.search(r"[A-Za-z]", s)


mobile = []
for v, why in [("+61 412 345 678", "AU library valid, E.164"), ("+61 423 456 789", "AU library valid"), ("+61 434 567 890", "AU library valid"),
               ("+61 458 901 234", "AU library valid"), ("+61 401 234 567", "AU library valid"), ("0412 345 678", "national format"),
               ("0423 456 789", "national format"), ("0444124222", "owned QA number; UI mask -> +61 (04) 4412 4222 (" + OBS + ")"),
               ("  0444124222 ", "leading/trailing whitespace trimmed")]:
    mobile.append((v, mob_norm(v), "ACCEPT" if mob_valid(v) else "REJECT", why))
for v, why in [("+61 12 345 6789", "library negative: 10 digits but no mobile prefix 4 (register C-01)"), ("+1 412 345 6789", "US country code in AU field"),
               ("+61 4", "prefix only"), ("0412ABC678", "letters mixed in"), (" ", "single whitespace"), ("   ", "whitespace only"),
               ("\U0001F642", "emoji"), ("", "empty")]:
    mobile.append((v, mob_norm(v) if v.strip() else "", "ACCEPT" if mob_valid(v) else "REJECT", why))
for n in (9, 10, 11, 12, 15):
    v = ("04" + "12345678901234")[:n]
    mobile.append((v, mob_norm(v), "ACCEPT" if n == 10 else "REJECT", f"boundary: {n} digits national"))
g = lcg(61)
fmts = ["0{a}{b} {c}{d} {e}{f}", "+61 4{a}{b} {c}{d}{e} {f}", "04{a}{b}-{c}{d}{e}-{f}", "614{a}{b}{c}{d}{e}{f}", "(04) {a}{b}{c}{d} {e}{f}"]
for i in range(55):  # positive: varied formats, second digit 0-9 (4x)
    r = next(g)
    ds = [str((r >> (3 * k)) % 10) for k in range(7)]
    core = "4" + str(i % 10) + "".join(ds[:6])
    style = i % 5
    v = ["0" + core[:3] + " " + core[3:6] + " " + core[6:], "+61 " + core[:3] + " " + core[3:6] + " " + core[6:], "0" + core, "+61" + core,
         "(0" + core[:1] + ") " + core[1:5] + " " + core[5:]][style]
    mobile.append((v, mob_norm(v), "ACCEPT", f"positive #{i + 1}: style {style}, generated 04xx"))
for i, p in enumerate(["02", "03", "05", "07", "08", "01", "00", "09", "06", "13", "18", "19"]):
    v = f"{p}12 345 678"
    mobile.append((v, mob_norm(v), "REJECT", f"landline/other prefix {p} (not 04)"))
for n in range(1, 9):
    v = "0412345678"[:n]
    mobile.append((v, mob_norm(v), "REJECT", f"too short: {n} digits"))
for i, s in enumerate(["0412 345 67x", "04l2 345 678", "0412.345.678", "0412/345/678", "+61+412345678", "++61412345678", "0412 345 678 90", "04１2 345 678",
                       "0412\t345678", "0412 345 678\n", "+61 (0)412 345 678", "0412 345 6.8"]):
    mobile.append((s, mob_norm(s), "ACCEPT_IF_NORMALISED" if mob_valid(s) else "REJECT", f"malformed/odd separators #{i + 1}"))
write("mobile_number", mobile)

# ---------- email_address
def email_valid(s):
    e = s
    if len(e) > 254 or e.count("@") != 1 or e != e.strip() or not e.isascii():
        return False
    local, dom = e.split("@")
    if not local or len(local) > 64 or ".." in e or local.startswith(".") or local.endswith("."):
        return False
    if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+", local):
        return False
    labels = dom.split(".")
    return len(labels) >= 2 and all(re.fullmatch(r"[A-Za-z0-9-]{1,63}", l) and not l.startswith("-") and not l.endswith("-") for l in labels) and len(labels[-1]) >= 2


def long_email(total):
    local, suffix = "a" * 64, "bigpond.net.au"
    L, prefix = total - 65 - len(suffix), ""
    while L > 0:
        seg = min(64, L)
        if L - seg == 1:
            seg -= 1
        prefix += "a" * (seg - 1) + "."
        L -= seg
    return local + "@" + prefix + suffix


DOMS = ["example.com.au", "bigpond.net.au", "aussie.com.au", "gmail.com"]
emails = []
for v, why in [("olivia.nguyen@example.com.au", "AU library"), ("noah.smith@bigpond.net.au", "AU library"), ("mia.collins@aussie.com.au", "AU library"),
               ("jack.wilson+invoices@gmail.com", "plus-addressing"), ("a@b.com.au", "boundary: local 1 char"), ("a" * 64 + "@bigpond.net.au", "boundary: local 64 (max)")]:
    emails.append((v, v.lower(), "ACCEPT", why))
for i in range(60):
    f, l, d = FIRST[i % 10], LAST[(i * 3 + i // 10) % 10], DOMS[i % 4]
    v = [f"{f}.{l}@{d}", f"{f}_{l}@{d}", f"{f}{l}{i}@{d}", f"{f}-{l}@{d}", f"{f}.{l}+qa{i}@{d}", f"{f[0]}{l}@{d}"][i % 6].lower()
    v = v if i % 7 else v.upper()  # every 7th uppercase: normalises to lowercase
    emails.append((v, v.lower(), "ACCEPT", f"positive #{i + 1}: AU name x AU domain"))
NEG = [("noah.smithbigpond.net.au", "no @"), ("noah.smith@bigpond", "missing TLD"), ("noah.smith@bigpond.c", ".c minimal TLD"), ("noah..smith@bigpond.net.au", "double dot"),
       ("@bigpond.net.au", "empty local"), ("noah.smith@", "empty domain"), ("noah@@bigpond.net.au", "double @"), ("noah smith@bigpond.net.au", "space in local"),
       (".noah@bigpond.net.au", "leading dot"), ("noah.@bigpond.net.au", "trailing dot"), ("noah@-bigpond.net.au", "label starts with hyphen"),
       ("noah@bigpond..net.au", "double dot in domain"), ("noah@bigpond.net.au.", "trailing dot domain"), ("noah@big pond.net.au", "space in domain"),
       ("noah,smith@bigpond.net.au", "comma"), ("noah(smith)@bigpond.net.au", "parentheses"), ("olivia.nguyen@еxample.com.au", "IDN homoglyph (Cyrillic e)"),
       ("a" * 65 + "@bigpond.net.au", "local 65 (max+1)"), (" ", "whitespace only"), ("", "empty"), ("\U0001F642@bigpond.net.au", "emoji local"),
       ("olivia.nguyen@example.com.au​", "hidden zero-width space")]
for v, why in NEG:
    emails.append((v, v.strip().lower(), "REJECT", why))
emails += [("noah.smith@bigpond.con", "noah.smith@bigpond.con", "ACCEPT_OR_WARN", ".con typo: syntactically valid (ASSUMPTION: no typo hint)"),
           (" olivia.nguyen@example.com.au", "olivia.nguyen@example.com.au", "ACCEPT_AFTER_TRIM", "leading space"),
           ("olivia.nguyen@example.com.au ", "olivia.nguyen@example.com.au", "ACCEPT_AFTER_TRIM", "trailing space")]
for p in INJECT:
    emails.append((p, "", "REJECT", "injection probe in email field"))
for t in (253, 254, 255, 256):
    v = long_email(t)
    assert len(v) == t
    emails.append((v, v, "ACCEPT" if t <= 254 else "REJECT", f"boundary: total length {t}"))
write("email_address", emails)

# ---------- otp_code (observed: 6 boxes "Digit 1".."Digit 6"; "Verify & Login" disabled until 6 digits)
otp = [("<FLDR_OTP>", "<6 digits>", "ACCEPT_FORMAT", "QA bypass OTP from .env for the QA number (" + OBS + ": login succeeded); value not stored in this file")]
for v, why in [("100000", "library valid format"), ("999999", "boundary all nines"), ("482913", "library valid format"), ("000000", "all zeroes / replay"),
               ("011111", "leading zero kept (string, not number)"), ("111111", "weak code")]:
    otp.append((v, v, "ACCEPT_FORMAT", why + "; server REJECT unless issued"))
g = lcg(6)
for i in range(75):
    v = f"{next(g) % 1000000:06d}"
    otp.append((v, v, "ACCEPT_FORMAT", f"random-looking 6-digit #{i + 1}; server REJECT unless issued"))
for n in range(0, 6):
    v = "123456"[:n]
    otp.append((v, v, "REJECT_VERIFY_DISABLED", f"{n} digits (min-1 or less); " + OBS + " Verify & Login disabled"))
otp.append(("45678", "45678", "REJECT_VERIFY_DISABLED", "5-digit bypass first supplied by requester; UI has 6 boxes"))
for n in range(7, 13):
    v = "1234567890123"[:n]
    otp.append((v, v[:6], "TRUNCATE_TO_6", f"{n} digits: extra chars must not be accepted"))
for v, exp, why in [("abcdef", "REJECT_INPUT", "letters"), ("12 34 56", "ACCEPT_IF_SPACES_STRIPPED", "spaces in pasted code"), (" <FLDR_OTP>", "ACCEPT_IF_TRIMMED", "leading space before the QA OTP"),
                    ("48956 ", "REJECT_VERIFY_DISABLED", "5 digits + trailing space"), ("12345a", "REJECT_INPUT", "5 digits + letter"), ("1234５6", "REJECT_INPUT", "full-width digit"),
                    ("12-345", "REJECT_INPUT", "hyphen"), ("١٢٣٤٥٦", "REJECT_INPUT", "Arabic-Indic digits"), ("\U0001F642" * 6, "REJECT_INPUT", "6 emoji"), ("1.2345", "REJECT_INPUT", "decimal point"),
                    ("+12345", "REJECT_INPUT", "plus sign"), ("1e5000", "REJECT_INPUT", "exponent notation"), ("0x1234", "REJECT_INPUT", "hex prefix")]:
    otp.append((v, re.sub(r"\s", "", v)[:6], exp, why))
write("otp_code", otp)

# ---------- postcode / state (ASSUMPTION: on Customer/Job address forms)
RNG = [(200, 299, "ACT"), (800, 999, "NT"), (1000, 1999, "NSW"), (2000, 2599, "NSW"), (2600, 2618, "ACT"), (2619, 2898, "NSW"), (2900, 2920, "ACT"),
       (2921, 2999, "NSW"), (3000, 3999, "VIC"), (4000, 4999, "QLD"), (5000, 5999, "SA"), (6000, 6999, "WA"), (7000, 7999, "TAS"), (8000, 8999, "VIC"), (9000, 9999, "QLD")]


def pc_state(pc):
    for a, b, s in RNG:
        if a <= int(pc) <= b:
            return s
    return None


pcs = []
NOTES = {"0200": "library says NT-min; real 0200-0299 is ACT (register C-02)", "7999": "library says invalid; TAS range is 7000-7999 (register C-03)",
         "9999": "library says invalid; 9000-9999 is QLD PO Box (register C-03)", "0800": "NT Darwin; leading zero must be preserved"}
cands = ["2000", "2601", "3000", "4000", "5000", "6000", "7000", "0800", "0820", "0200", "7999", "9999", "0199", "0300", "0799", "1000", "0999"]
for a, b, s in RNG:
    cands += [f"{a:04d}", f"{b:04d}", f"{max(a - 1, 0):04d}", f"{min(b + 1, 9999):04d}"]
for k in range(0, 10000, 100):
    cands.append(f"{k:04d}")
for v in cands:
    s = pc_state(v)
    pcs.append((v, v, f"ACCEPT_FORMAT state={s}" if s else "REJECT_UNALLOCATED", NOTES.get(v, "range boundary / sample")))
for v, why in [("200", "3 digits"), ("20000", "5 digits"), ("200 0", "internal space"), ("N/A", "text"), ("abcd", "letters"), ("", "empty"), (" ", "whitespace"), ("\U0001F642", "emoji"),
               ("-200", "negative"), ("2.00", "decimal"), ("2000​", "hidden char"), ("２０００", "full-width digits")]:
    pcs.append((v, "", "REJECT", why))
write("postcode", pcs)

STATES = [("NSW", "New South Wales"), ("VIC", "Victoria"), ("QLD", "Queensland"), ("WA", "Western Australia"), ("SA", "South Australia"), ("TAS", "Tasmania"),
          ("ACT", "Australian Capital Territory"), ("NT", "Northern Territory")]
st = []
for a, b in STATES:
    st += [(a, a, "ACCEPT", f"library state: {b}"), (b, a, "ACCEPT_IF_FREE_TEXT_OR_LABEL", f"full name of {a}"), (a.lower(), a, "ACCEPT_CASE_INSENSITIVE", f"lowercase {a}"),
           (f" {a} ", a, "ACCEPT_AFTER_TRIM", f"whitespace {a}"), (a.title() if len(a) > 2 else a[0] + a[1:].lower(), a, "ACCEPT_CASE_INSENSITIVE", f"mixed case {a}")]
for v in ["CA", "NY", "TX", "FL", "WA-US", "AKL", "Auckland", "Ontario", "BC", "Bavaria", "NZ", "XX", "N/A", "", " ", "\U0001F642", "NSW VIC", "N S W", "0", "12"] + INJECT:
    st.append((v, "", "REJECT", "foreign/invalid state must not be offered/accepted"))
for i in range(30):
    st.append((f"{STATES[i % 8][0]}{i}", "", "REJECT", f"state code + digit suffix #{i + 1}"))
write("state", st)

# ---------- ABN / TFN
def abn_ok(s):
    d = re.sub(r"\s", "", s)
    if not re.fullmatch(r"\d{11}", d):
        return False
    x = [int(c) for c in d]
    x[0] -= 1
    return sum(a * b for a, b in zip(x, [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19])) % 89 == 0


def tfn_ok(s):
    d = re.sub(r"\s", "", s)
    return bool(re.fullmatch(r"\d{9}", d)) and sum(int(c) * k for c, k in zip(d, [1, 4, 3, 7, 5, 8, 6, 9, 10])) % 11 == 0


def fmt_abn(d):
    return f"{d[:2]} {d[2:5]} {d[5:8]} {d[8:]}"


abn = [("33 102 417 032", "33102417032", "ACCEPT", "library valid; mod-89 verified"), ("33102417032", "33102417032", "ACCEPT", "no spaces"),
       ("12 345 678 901", "12345678901", "REJECT", "library invalid checksum")]
found, n = [], 10000000000
while len(found) < 60:  # deterministic scan for checksum-valid ABNs
    n += 7919
    if abn_ok(str(n)):
        found.append(str(n))
for d in found:
    abn.append((fmt_abn(d), d, "ACCEPT", "generated checksum-valid ABN (mod-89)"))
for d in found[:35]:
    bad = d[:-1] + str((int(d[-1]) + 1) % 10)
    abn.append((fmt_abn(bad), bad, "REJECT", "valid ABN with last digit changed: checksum fail"))
for i, (v, why) in enumerate([("1234567890", "10 digits (min-1)"), ("123456789012", "12 digits (max+1)"), ("", "empty"), ("   ", "whitespace"), ("33 102 417 03A", "letter"),
                              ("\U0001F642", "emoji"), ("00 000 000 000", "all zeroes"), ("33-102-417-032", "hyphens"), ("33.102.417.032", "dots"), ("ABN 33 102 417 032", "prefix text"),
                              ("33 102 417 032 ", "trailing space"), ("33​102417032", "hidden char")] + [(p, "injection probe") for p in INJECT[:6]]):
    abn.append((v, re.sub(r"\s", "", v), "REJECT" if not abn_ok(v) else "ACCEPT_AFTER_TRIM", why))
write("abn", abn)

tfn = [("123 456 782", "123456782", "ACCEPT", "library valid; mod-11 verified"), ("123 456 789", "123456789", "REJECT", "library invalid mod-11")]
found, n = [], 100000000
while len(found) < 60:
    n += 7919
    if tfn_ok(str(n)):
        found.append(str(n))
for d in found:
    tfn.append((f"{d[:3]} {d[3:6]} {d[6:]}", d, "ACCEPT", "generated mod-11-valid TFN"))
for d in found[:40]:
    bad = d[:-1] + str((int(d[-1]) + 1) % 10)
    tfn.append((f"{bad[:3]} {bad[3:6]} {bad[6:]}", bad, "REJECT", "valid TFN with last digit changed"))
for v, why in [("12345678", "8 digits (min-1)"), ("1234567", "7 digits"), ("1234567890", "10 digits (max+1)"), ("", "empty"), ("   ", "whitespace"), ("123 456 78A", "letter"),
               ("000 000 000", "all zeroes"), ("123-456-782", "hyphens"), ("123456782 ", "trailing space"), ("\U0001F642", "emoji")]:
    tfn.append((v, re.sub(r"\s", "", v), "ACCEPT_AFTER_TRIM" if tfn_ok(v) else "REJECT", why))
write("tfn", tfn)

# ---------- BSB / account number
bsb = [("062-000", "062-000", "ACCEPT", "library valid"), ("123-456", "123-456", "ACCEPT", "library valid"), ("032-198", "032-198", "ACCEPT", "library valid")]
g = lcg(32)
for i in range(90):
    d = f"{next(g) % 1000000:06d}"
    bsb.append((f"{d[:3]}-{d[3:]}", f"{d[:3]}-{d[3:]}", "ACCEPT", f"generated XXX-XXX #{i + 1}"))
for v, why in [("062000", "no hyphen"), ("062 000", "space separator"), ("06-2000", "hyphen misplaced"), ("062-00", "5 digits (min-1)"), ("062-0000", "7 digits (max+1)"),
               ("ABC-DEF", "letters"), ("", "empty"), (" ", "whitespace"), ("062--000", "double hyphen"), ("-062000", "leading hyphen"), ("062-000-", "trailing hyphen"),
               ("062_000", "underscore"), ("062–000", "en dash"), ("0", "single digit"), ("0620000000", "10 digits"), ("\U0001F642", "emoji"), ("BSB 062-000", "prefix text"),
               ("062-00O", "letter O for zero"), ("62-000", "5 digits")] + [(p, "injection probe") for p in INJECT[:6]]:
    d = re.sub(r"\D", "", v)
    if re.fullmatch(r"\d{3}-\d{3}", v):
        exp = "ACCEPT"
    elif len(d) == 6 and re.fullmatch(r"[\d\s-]+", v):
        exp = "ACCEPT_IF_NORMALISED"
    else:
        exp = "REJECT"
    bsb.append((v, d[:3] + "-" + d[3:] if len(d) == 6 else "", exp, why))
write("bsb", bsb)

acct = []
for n in range(1, 13):
    v = "".join(str((i + 1) % 10) for i in range(n))
    acct.append((v, v, "ACCEPT" if 6 <= n <= 9 else "REJECT", f"length {n} ({'in range 6-9' if 6 <= n <= 9 else 'out of range'})"))
g = lcg(9)
for i in range(80):
    v = str(100000 + next(g) % 899999)[: 6 + i % 4]
    acct.append((v, v, "ACCEPT", f"generated numeric #{i + 1}, {len(v)} digits"))
for v, exp, why in [("000012345", "ACCEPT", "4 leading zeros (allowed)"), ("00000123456", "REJECT", "leading zeros > 4 (library negative)"), ("00000012", "REJECT", "6 leading zeros"),
                    ("12345A", "REJECT", "letter"), ("12 3456", "REJECT", "internal space"), ("12-3456", "REJECT", "hyphen"), ("", "REJECT", "empty"), ("   ", "REJECT", "whitespace"),
                    ("\U0001F642", "REJECT", "emoji"), ("123456.0", "REJECT", "decimal"), ("-123456", "REJECT", "negative"), ("+123456", "REJECT", "plus sign"), ("1e6", "REJECT", "exponent"),
                    (" 123456", "ACCEPT_AFTER_TRIM", "leading space"), ("123456 ", "ACCEPT_AFTER_TRIM", "trailing space"), ("１２３４５６", "REJECT", "full-width digits")] + [(p, "REJECT", "injection probe") for p in INJECT[:6]]:
    acct.append((v, v.strip() if exp.startswith("ACCEPT") else "", exp, why))
write("account_number", acct)

# ---------- names
def name_rows(kind, pool):
    rows = [(n, n, "ACCEPT", f"AU library {kind}") for n in pool]
    rows += [(n.upper(), n.upper(), "ACCEPT", "uppercase") for n in pool] + [(n.lower(), n.lower(), "ACCEPT", "lowercase") for n in pool]
    rows += [(f"  {n} ", n, "ACCEPT_AFTER_TRIM", "surrounding whitespace") for n in pool]
    rows += [(f"{pool[i]}-{pool[(i + 3) % 10]}", f"{pool[i]}-{pool[(i + 3) % 10]}", "ACCEPT", "double-barrel") for i in range(10)]
    rows += [(f"{pool[i]} {pool[(i + 1) % 10]}", f"{pool[i]} {pool[(i + 1) % 10]}", "ACCEPT", "two-part name") for i in range(10)]
    rows += [(f"{pool[i]}{i + 1}", "", "REJECT_OR_WARN", "digit suffix") for i in range(10)]
    rows += [("O'Brien", "O'Brien", "ACCEPT", "apostrophe"), ("Smith-Jones", "Smith-Jones", "ACCEPT", "hyphen"), ("Mary Anne", "Mary Anne", "ACCEPT", "space"),
             ("D’Souza", "D’Souza", "ACCEPT", "typographic apostrophe"), ("Nguyễn", "Nguyễn", "ACCEPT", "Vietnamese diacritic (AU-common)"), ("José", "José", "ACCEPT", "accent")]
    for k in (1, 2, 50, 99, 100, 101, 150, 200, 254, 255):
        rows.append(("N" * k, "N" * k if k <= 100 else "", "ACCEPT" if k <= 100 else "REJECT", f"boundary: {k} chars (max=100 ASSUMPTION - {ASM})"))
    rows += [("", "", "REJECT", "empty"), ("   ", "", "REJECT", "spaces only"), ("User1234", "", "REJECT_OR_WARN", "digits (library negative)"), ("\U0001F642", "", "REJECT", "emoji only"),
             ("123", "", "REJECT_OR_WARN", "digits only"), ("!@#$%", "", "REJECT", "symbols only"), ("-", "", "REJECT", "single hyphen"), ("'", "", "REJECT", "single apostrophe")]
    rows += [(p, "", "REJECT_OR_ESCAPED", "XSS/SQLi/template probe (stored & reflected)") for p in INJECT]
    return rows


write("first_name", name_rows("first name", FIRST))
write("last_name", name_rows("last name", LAST))

# ---------- date_of_birth dd/mm/yyyy
def dob(s):
    try:
        return datetime.datetime.strptime(s, "%d/%m/%Y").date() if re.fullmatch(r"\d{2}/\d{2}/\d{4}", s) else None
    except ValueError:
        return None


dobs = []
for v, why in [("14/02/1990", "valid"), ("29/02/2000", "leap day (div by 400)"), ("01/01/1900", "boundary: min (ASSUMPTION)"), ("31/12/2025", "valid past date"),
               ("31/12/1899", "min-1 (ASSUMPTION)"), ("29/02/1900", "NOT leap (div by 100 not 400)"), ("31/04/2024", "April has 30 days"), ("32/01/2024", "day 32"),
               ("00/01/2024", "day 0"), ("13/13/2024", "month 13"), ("02/14/1990", "US mm/dd order"), ("1990-02-14", "ISO in dd/mm/yyyy field"), ("", "empty"), ("   ", "whitespace"),
               ("14/02/90", "2-digit year"), ("1/1/2000", "no zero padding"), ("14-02-1990", "hyphens"), ("14.02.1990", "dots"), ("14/02/1990 ", "trailing space"), ("aa/bb/cccc", "letters")]:
    d = dob(v)
    dobs.append((v, d.isoformat() if d else "", "ACCEPT" if d and d >= datetime.date(1900, 1, 1) else "REJECT", why))
for y in range(1900, 2101, 4):  # every 4th year: 29 Feb leap logic (1900/2100 are NOT leap)
    v = f"29/02/{y}"
    d = dob(v)
    dobs.append((v, d.isoformat() if d else "", "ACCEPT" if d else "REJECT", f"29 Feb {y}: {'leap' if d else 'not a leap year'}"))
for m, dd in enumerate([31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31], 1):
    v = f"{dd:02d}/{m:02d}/2024"
    dobs.append((v, dob(v).isoformat(), "ACCEPT", f"last day of month {m} (2024 leap)"))
    v2 = f"{dd + 1:02d}/{m:02d}/2024"
    d2 = dob(v2)
    dobs.append((v2, d2.isoformat() if d2 else "", "ACCEPT" if d2 else "REJECT", f"last day + 1, month {m}"))
for y in range(1900, 2026, 5):
    v = f"14/02/{y}"
    dobs.append((v, dob(v).isoformat(), "ACCEPT", f"valid DOB sweep {y}"))
write("date_of_birth", dobs)

# ---------- amount_aud (Invoices / Items; GST 10% - ASSUMPTION)
amt = []
def amt_row(v, why):
    d = re.sub(r"[$]", "", v)
    ok = bool(re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d{1,2})?|\d+(\.\d{1,2})?", d))
    n = d.replace(",", "")
    gst = round(float(n) * 0.10 + 1e-9, 2) if ok else None
    tot = f"${float(n) + gst:,.2f}" if ok else "n/a"
    amt.append((v, f"{float(n):.2f}" if ok else "", "ACCEPT" if ok else "REJECT", f"{why}; GST={('%.2f' % gst) if ok else 'n/a'}; total={tot}"))


for v, why in [("0.00", "zero"), ("0.01", "min positive"), ("1100.00", "subtotal 1,100.00 -> total 1,210.00"), ("$1,100.00", "typed with $ and comma"), ("1100", "no decimals"),
               ("99999999.99", "large (ASSUMPTION max)"), ("-0.01", "negative"), ("1100.005", "3 decimals"), ("abc", "letters"), ("", "empty"), ("   ", "whitespace"),
               ("1,10,0.00", "bad grouping"), (".5", "no leading digit"), ("5.", "trailing dot"), ("1e3", "exponent"), ("$", "symbol only"), ("$$5", "double symbol")]:
    amt_row(v, why)
for i in range(1, 91):
    amt_row(f"{i * 137 % 9973 + i * 0.05:.2f}" if i % 3 else f"{i * 1000 + 0.99:,.2f}", f"generated amount #{i}")
write("amount_aud", amt)

# ---------- street_address
ADDR = [("12 Macquarie Street", "Sydney", "NSW", "2000"), ("88 Bourke Street", "Melbourne", "VIC", "3000"), ("145 Eagle Street", "Brisbane", "QLD", "4000"),
        ("27 Adelaide Terrace", "Perth", "WA", "6000"), ("101 Rundle Mall", "Adelaide", "SA", "5000"), ("9 Brisbane Street", "Hobart", "TAS", "7000"),
        ("21 London Circuit", "Canberra", "ACT", "2601"), ("76 Mitchell Street", "Darwin", "NT", "0800")]
rows = []
for a, c, s, p in ADDR:
    full = f"{a}, {c} {s} {p}"
    rows += [(full, full, "ACCEPT", f"AU library {s}"), (full.upper(), full.upper(), "ACCEPT", "uppercase"), (f"  {full} ", full, "ACCEPT_AFTER_TRIM", "whitespace"),
             (f"Unit {3 + len(c)}/{full}", f"Unit {3 + len(c)}/{full}", "ACCEPT", "unit prefix"), (f"Level 2, {full}", f"Level 2, {full}", "ACCEPT", "level prefix"),
             (full.replace("Street", "St").replace("Terrace", "Tce").replace("Circuit", "Cct"), "", "ACCEPT", "abbreviated street type"),
             (full + "​", full, "ACCEPT_AFTER_CLEAN", "hidden zero-width char")]
for i in range(1, 41):
    a, c, s, p = ADDR[i % 8]
    rows.append((f"{i * 7} {a.split(' ', 1)[1]}, {c} {s} {p}", "", "ACCEPT", f"street number sweep #{i}"))
for k in (1, 2, 100, 254, 255, 256):
    rows.append(("1" * k, "1" * k if k <= 254 else "", "ACCEPT" if k <= 254 else "REJECT_OR_TRUNCATE", f"boundary: {k} chars (max=254 ASSUMPTION)"))
rows += [("", "", "REJECT", "empty (if required)"), ("   ", "", "REJECT", "whitespace")] + [(p, "", "REJECT_OR_ESCAPED", "injection probe") for p in INJECT]
write("street_address", rows)

for k, v in sorted(COUNTS.items()):
    print(f"{k}.csv: {v} rows")
```

### 7.3 `gen_avatars.py`
Generates 100 illustrated avatar PNGs locally (Pillow).

```python
"""Generate 100 illustrated avatar PNGs (gradient background, shoulders, head, hair) - deterministic, no external fetches."""
import os, random
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed-images")
os.makedirs(OUT, exist_ok=True)
S = 512
PAL = [((98, 182, 245), (245, 143, 124)), ((132, 214, 190), (245, 190, 120)), ((160, 140, 240), (250, 160, 190)), ((110, 200, 230), (190, 160, 245)),
       ((250, 190, 130), (240, 130, 150)), ((120, 210, 160), (100, 170, 235))]
SKIN = [(255, 224, 200), (245, 200, 165), (222, 170, 130), (190, 135, 100), (150, 105, 80)]
HAIR = [(40, 28, 70), (60, 40, 30), (25, 25, 30), (150, 90, 45), (200, 150, 70), (110, 60, 40), (230, 200, 130)]
SHIRT = [(245, 125, 105), (90, 90, 230), (40, 180, 160), (250, 190, 90), (150, 130, 230), (80, 160, 220)]

for i in range(100):
    r = random.Random(1000 + i)
    a, b = PAL[i % len(PAL)]
    img = Image.new("RGB", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = (x + y) / (2 * S)
            px[x, y] = tuple(int(a[k] * (1 - t) + b[k] * t) for k in range(3))
    d = ImageDraw.Draw(img)
    skin, hair, shirt = r.choice(SKIN), r.choice(HAIR), r.choice(SHIRT)
    d.ellipse([90, 360, 422, 760], fill=shirt)
    d.rectangle([226, 300, 286, 390], fill=tuple(int(c * 0.93) for c in skin))
    if r.random() < 0.55:
        d.rounded_rectangle([150, 130, 362, 400], radius=90, fill=hair)
    d.ellipse([176, 150, 336, 330], fill=skin)
    d.pieslice([166, 128, 346, 280], 180, 360, fill=hair)
    for ex in (222, 290):
        d.ellipse([ex - 7, 232, ex + 7, 246], fill=(40, 30, 50))
    d.arc([226, 258, 286, 300], 20, 160, fill=(150, 70, 70), width=5)
    d.ellipse([196, 262, 224, 282], fill=(255, 150, 140))
    d.ellipse([288, 262, 316, 282], fill=(255, 150, 140))
    img.save(os.path.join(OUT, f"avatar-{i + 1:03d}.png"))
print(len(os.listdir(OUT)), "avatars in", OUT)
```

### 7.4 `gen_pw.py`
Generates the Playwright TypeScript project (page objects, modules, fixtures, config) and FLD-AUTH-001 to 050 specs plus auth-test-cases.md.

```python
"""Generate the Fieldr Playwright framework + AUTH specs + AUTH manual test-case table (single source of truth)."""
import os, json

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pw")


def w(rel, content):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content.lstrip("\n"))


# ------------------------------------------------------------------ project files
w("package.json", json.dumps({
    "name": "fieldr-e2e", "version": "1.0.0", "private": True,
    "scripts": {"test": "playwright test", "test:p0": "playwright test --grep @P0", "typecheck": "tsc --noEmit", "report": "playwright show-report"},
    "devDependencies": {"@playwright/test": "^1.49.0", "@types/node": "^22.0.0", "dotenv": "^16.4.5", "typescript": "^5.6.0"},
}, indent=2) + "\n")

w("tsconfig.json", json.dumps({"compilerOptions": {
    "target": "ES2022", "module": "commonjs", "strict": True, "esModuleInterop": True, "skipLibCheck": True, "baseUrl": ".",
    "paths": {"@pages/*": ["src/pages/*"], "@modules/*": ["src/modules/*"], "@utils/*": ["src/utils/*"], "@config/*": ["src/config/*"],
              "@fixtures": ["src/fixtures/index.ts"], "@testdata/*": ["src/testdata/*"]}},
    "include": ["src/**/*.ts", "playwright.config.ts"]}, indent=2) + "\n")

w(".gitignore", "node_modules/\ntest-results/\nplaywright-report/\n.env\n")
w(".env.example", """FLDR_BASE_URL=https://rajanjagz7.dev.fieldr.app
# Owned QA number (national format) and its QA bypass OTP
FLDR_MOBILE=
FLDR_OTP=
# Optional: registered email for the email-login case (skipped when empty)
FLDR_EMAIL=
# Number that must NOT belong to any user (never a real person's number)
FLDR_UNREGISTERED_MOBILE=
# Set to 1 to allow brute-force / lock-out cases against the shared account
FLDR_ALLOW_LOCKOUT=0
""")
# .env is created only if missing, with placeholders. Put the real QA mobile and OTP here yourself; never commit it.
if not os.path.exists(os.path.join(ROOT, ".env")):
    w(".env", """FLDR_BASE_URL=https://rajanjagz7.dev.fieldr.app
FLDR_MOBILE=REPLACE_ME
FLDR_OTP=REPLACE_ME
FLDR_EMAIL=
FLDR_UNREGISTERED_MOBILE=REPLACE_ME
FLDR_ALLOW_LOCKOUT=0
""")

w("playwright.config.ts", """
import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';

dotenv.config();

export default defineConfig({
  testDir: './src/tests',
  testMatch: '**/*.e2e.ts',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false, // one shared OTP-bypass account: keep auth cases serial
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: 1, // first retry records trace.zip
  reporter: [['list'], ['html', { open: 'never' }], ['json', { outputFile: 'test-results/results.json' }]],
  use: {
    baseURL: process.env.FLDR_BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'off',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'edge', use: { ...devices['Desktop Edge'], channel: 'msedge' } },
  ],
});
""")

# ------------------------------------------------------------------ config / utils / testdata
w("src/config/index.ts", """
import dotenv from 'dotenv';

dotenv.config();

const required = (key: string): string => {
  const value = process.env[key];
  if (!value) throw new Error(`Missing env var ${key} - copy .env.example to .env and fill it in`);
  return value;
};

export const config = {
  baseUrl: process.env.FLDR_BASE_URL ?? 'https://rajanjagz7.dev.fieldr.app',
  mobile: required('FLDR_MOBILE'),
  otp: required('FLDR_OTP'),
  email: process.env.FLDR_EMAIL ?? '',
  unregisteredMobile: required('FLDR_UNREGISTERED_MOBILE'),
  allowLockout: process.env.FLDR_ALLOW_LOCKOUT === '1',
  timeouts: { ui: 10_000, network: 15_000, resend: 45_000 },
} as const;
""")

w("src/utils/Logger.ts", """
type Level = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
const order: Record<Level, number> = { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3 };

export class Logger {
  constructor(private readonly context: string) {}

  private write(level: Level, message: string): void {
    const min = (process.env.LOG_LEVEL as Level | undefined) ?? 'INFO';
    if (order[level] < order[min]) return;
    process.stdout.write(`[${new Date().toISOString()}] [${level}] [${this.context}] ${message}\\n`);
  }

  debug(message: string): void { this.write('DEBUG', message); }
  info(message: string): void { this.write('INFO', message); }
  warn(message: string): void { this.write('WARN', message); }
  error(message: string): void { this.write('ERROR', message); }
}
""")

w("src/utils/DataGenerator.ts", """
/** Per-run AU test data helpers. The epoch is the only varying input. */
export class DataGenerator {
  /** RFC 2606 reserved domain: mail can never reach a real person. */
  static unregisteredEmail(): string {
    return `qa+${Date.now()}@example.com`;
  }
}
""")

w("src/utils/index.ts", "export { Logger } from './Logger';\nexport { DataGenerator } from './DataGenerator';\n")

w("src/testdata/au.ts", """
/** AU test data library (verbatim from the master prompt). Typed values only: none of these are submitted. */
export const AU = {
  mobile: {
    tooShort: '0412 34',
    us: '14123456789',
    lettersMixed: '0412ABC678',
    whitespace: '   ',
    emoji: '\\u{1F642}',
    elevenDigits: '04123456789',
  },
  email: {
    noAt: 'noah.smithbigpond.net.au',
    missingTld: 'noah.smith@bigpond',
    doubleDot: 'noah..smith@bigpond.net.au',
    whitespace: '   ',
    xss: '"><img src=x onerror=window.__xss=1>',
    sqli: "' OR '1'='1",
  },
  otp: { wrong: '111111', fiveDigits: '48956', letters: 'a' },
  /** Observed UI mask for AU mobiles (2026-09-19): "+61 (04) XXXX XXXX". */
  mask: (national: string): string => `+61 (${national.slice(0, 2)}) ${national.slice(2, 6)} ${national.slice(6)}`,
} as const;
""")

# ------------------------------------------------------------------ pages (locators only)
w("src/pages/BasePage.ts", """
import { Page } from '@playwright/test';

export abstract class BasePage {
  constructor(protected page: Page) {}

  async navigate(path: string): Promise<void> {
    await this.page.goto(path);
  }
}
""")

w("src/pages/LoginPage.ts", """
import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

/** Selectors come from the accessibility tree observed on 2026-09-19. */
export class LoginPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  heading = () => this.page.getByRole('heading', { name: 'Welcome to Fieldr' });
  eyebrow = () => this.page.getByText(/secure login/i).first();
  helper = () => this.page.getByText("Log in with your mobile number or email. We'll send you a one-time passcode (OTP).");
  mobileTab = () => this.page.getByRole('button', { name: 'Mobile Number' });
  emailTab = () => this.page.getByRole('button', { name: 'Email Address' });
  form = () => this.page.locator('form');
  identifierInput = () => this.form().getByRole('textbox').first();
  countryButton = () => this.page.getByRole('button', { name: /Australia/ });
  sendOtpBtn = () => this.page.getByRole('button', { name: 'Send OTP' });
  termsLink = () => this.page.getByRole('link', { name: 'Terms & Conditions' });
  privacyLink = () => this.page.getByRole('link', { name: 'Privacy Policy' });

  otpHeading = () => this.page.getByRole('heading', { name: 'Check Your Messages' });
  otpSentTo = () => this.page.getByText('We sent a 6-digit OTP to');
  otpDigit = (index: number) => this.page.getByRole('textbox', { name: `Digit ${index}` });
  verifyBtn = () => this.page.getByRole('button', { name: 'Verify & Login' });
  resendBtn = () => this.page.getByRole('button', { name: 'Resend OTP', exact: true });
  resendTimer = () => this.page.getByText(/Resend OTP in \\d+s/);
  changeIdentifierBtn = () => this.page.getByRole('button', { name: 'Use a different number or email' });

  async open(): Promise<void> {
    await this.navigate('/login');
  }

  async clickMobileTab(): Promise<void> {
    await this.mobileTab().click();
  }

  async clickEmailTab(): Promise<void> {
    await this.emailTab().click();
  }

  async fillIdentifier(value: string): Promise<void> {
    await this.identifierInput().fill(value);
  }

  async clickSendOtp(): Promise<void> {
    await this.sendOtpBtn().click();
  }

  async fillOtpDigit(index: number, value: string): Promise<void> {
    await this.otpDigit(index).fill(value);
  }

  async typeIntoOtpDigit(index: number, value: string): Promise<void> {
    await this.otpDigit(index).pressSequentially(value);
  }

  async clickVerify(): Promise<void> {
    await this.verifyBtn().click();
  }

  async clickResend(): Promise<void> {
    await this.resendBtn().click();
  }

  async clickChangeIdentifier(): Promise<void> {
    await this.changeIdentifierBtn().click();
  }

  async pressTab(): Promise<void> {
    await this.page.keyboard.press('Tab');
  }
}
""")

w("src/pages/DashboardPage.ts", """
import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class DashboardPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  heading = () => this.page.getByRole('heading', { name: 'Dashboard', level: 1 });
  navLink = (name: string) => this.page.getByRole('link', { name, exact: true });
  userMenuBtn = () => this.page.getByRole('button', { name: /@/ });
  // NEEDS UI INSPECTION: the logout menu item label was not observed. Regex is a best guess.
  logoutMenuItem = () => this.page.getByRole('menuitem', { name: /log\\s?out|sign\\s?out/i });

  async open(): Promise<void> {
    await this.navigate('/app/dashboard');
  }

  async openDeepLink(path: string): Promise<void> {
    await this.navigate(path);
  }

  async clickUserMenu(): Promise<void> {
    await this.userMenuBtn().click();
  }

  async clickLogout(): Promise<void> {
    await this.logoutMenuItem().click();
  }
}
""")

w("src/pages/index.ts", "export { BasePage } from './BasePage';\nexport { LoginPage } from './LoginPage';\nexport { DashboardPage } from './DashboardPage';\n")

# ------------------------------------------------------------------ modules (business logic)
w("src/modules/LoginModule.ts", """
import { Page, Response, expect } from '@playwright/test';
import { LoginPage } from '@pages/LoginPage';
import { DashboardPage } from '@pages/DashboardPage';
import { Logger } from '@utils/Logger';
import { config } from '@config/index';

export class LoginModule {
  private readonly logger = new Logger('LoginModule');

  constructor(
    private readonly page: Page,
    private readonly loginPage: LoginPage,
    private readonly dashboardPage: DashboardPage,
  ) {}

  async requestOtpForMobile(national: string): Promise<void> {
    this.logger.info(`Requesting OTP for mobile ending ${national.slice(-3)}`);
    await this.loginPage.open();
    await this.loginPage.clickMobileTab();
    await this.loginPage.fillIdentifier(national);
    await this.loginPage.clickSendOtp();
    await expect(this.loginPage.otpHeading()).toBeVisible({ timeout: config.timeouts.network });
  }

  async enterOtp(code: string): Promise<void> {
    for (let i = 0; i < code.length; i += 1) {
      await this.loginPage.fillOtpDigit(i + 1, code[i]);
    }
  }

  async loginWithMobile(national: string = config.mobile, otp: string = config.otp): Promise<void> {
    await this.requestOtpForMobile(national);
    await this.enterOtp(otp);
    await expect(this.loginPage.verifyBtn()).toBeEnabled();
    await this.loginPage.clickVerify();
    await this.expectOnDashboard();
  }

  async loginWithEmail(email: string, otp: string = config.otp): Promise<void> {
    this.logger.info('Requesting OTP by email');
    await this.loginPage.open();
    await this.loginPage.clickEmailTab();
    await this.loginPage.fillIdentifier(email);
    await this.loginPage.clickSendOtp();
    await expect(this.loginPage.otpHeading()).toBeVisible({ timeout: config.timeouts.network });
    await this.enterOtp(otp);
    await this.loginPage.clickVerify();
    await this.expectOnDashboard();
  }

  /** Click Send OTP and return the API response it triggered. */
  async sendOtpCapturing(): Promise<Response> {
    const [response] = await Promise.all([
      this.page.waitForResponse((r) => r.request().method() === 'POST', { timeout: config.timeouts.network }),
      this.loginPage.clickSendOtp(),
    ]);
    return response;
  }

  /** Click Verify & Login and return the API response it triggered. */
  async verifyCapturing(): Promise<Response> {
    const [response] = await Promise.all([
      this.page.waitForResponse((r) => r.request().method() === 'POST', { timeout: config.timeouts.network }),
      this.loginPage.clickVerify(),
    ]);
    return response;
  }

  /** Fill the identifier and click Send OTP only if the button is enabled. Returns whether it was clicked. */
  async trySendIdentifier(value: string): Promise<boolean> {
    await this.loginPage.fillIdentifier(value);
    const enabled = await this.loginPage.sendOtpBtn().isEnabled();
    if (enabled) await this.loginPage.clickSendOtp();
    return enabled;
  }

  async expectOnDashboard(): Promise<void> {
    await expect(this.page).toHaveURL(/\\/app\\/dashboard/, { timeout: config.timeouts.network });
    await expect(this.dashboardPage.heading()).toBeVisible({ timeout: config.timeouts.network });
  }

  async expectStillOnIdentifierStep(): Promise<void> {
    await expect(this.loginPage.otpHeading()).toBeHidden({ timeout: config.timeouts.ui });
    await expect(this.page).toHaveURL(/\\/login/);
  }

  async logout(): Promise<void> {
    await this.dashboardPage.clickUserMenu();
    await this.dashboardPage.clickLogout();
    await expect(this.page).toHaveURL(/\\/login/, { timeout: config.timeouts.network });
  }
}
""")
w("src/modules/index.ts", "export { LoginModule } from './LoginModule';\n")

# ------------------------------------------------------------------ fixtures
w("src/fixtures/index.ts", """
import { test as base } from '@playwright/test';
import { LoginPage, DashboardPage } from '@pages/index';
import { LoginModule } from '@modules/index';

type Fixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  loginModule: LoginModule;
  /** OTP-bypass fixture: a fully authenticated session for the QA account. */
  loggedIn: void;
};

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },
  loginModule: async ({ page, loginPage, dashboardPage }, use) => {
    await use(new LoginModule(page, loginPage, dashboardPage));
  },
  loggedIn: async ({ loginModule }, use) => {
    await loginModule.loginWithMobile();
    await use();
  },
});

export { expect } from '@playwright/test';
""")

# ------------------------------------------------------------------ AUTH cases (single source of truth)
T = "{ timeout: config.timeouts.ui }"
N = "{ timeout: config.timeouts.network }"
cases = []


def case(id, title, prio, typ, pre, data, exp, steps, tags=(), skip=None, fixme=None, slow=False):
    cases.append(dict(id=id, title=title, prio=prio, typ=typ, pre=pre, data=data, exp=exp, steps=steps, tags=list(tags), skip=skip, fixme=fixme, slow=slow))


OPEN = ("Open the login page", "await loginPage.open();")
MOBTAB = ("Click the Mobile Number tab", "await loginPage.clickMobileTab();")
EMAILTAB = ("Click the Email Address tab", "await loginPage.clickEmailTab();")
SENDBYPASS = [OPEN, MOBTAB, ("Enter the QA mobile number in the mobile field", "await loginPage.fillIdentifier(config.mobile);"),
              ("Click Send OTP", "await loginPage.clickSendOtp();"),
              ("Wait for the Check Your Messages heading", f"await expect(loginPage.otpHeading()).toBeVisible({N});")]
NEG_EXPECT = "The OTP step is not shown and the user stays on /login"
LOGURL = f"await expect(page).toHaveURL(/\\/login/, {N});"
DASH_H = "page.getByRole('heading', { name: 'Dashboard', level: 1 })"
RECORD = "test.info().annotations.push({ type: 'observed-response', description: `${response.status()} ${(await response.text()).slice(0, 300)}` });"


def neg_input(id, title, value_expr, data):
    case(id, title, "P1", "Negative", "Logged out", data, NEG_EXPECT,
         [OPEN, MOBTAB, ("Enter the invalid value and click Send OTP only if it is enabled", f"await loginModule.trySendIdentifier({value_expr});"),
          ("Verify the OTP step is not shown", "await loginModule.expectStillOnIdentifierStep();")])


def neg_email(id, title, value_expr, data):
    case(id, title, "P1", "Negative", "Logged out", data, NEG_EXPECT,
         [OPEN, EMAILTAB, ("Enter the invalid email and click Send OTP only if it is enabled", f"await loginModule.trySendIdentifier({value_expr});"),
          ("Verify the OTP step is not shown", "await loginModule.expectStillOnIdentifierStep();")])


case("FLD-AUTH-001", "Unauthenticated /app/dashboard redirects to Secure Login", "P0", "Security", "No session cookie", "/app/dashboard", "302 to /login and the Welcome to Fieldr heading is shown",
     [("Open /app/dashboard without a session", "await dashboardPage.open();"), ("Verify the URL is /login", LOGURL),
      ("Verify the Welcome to Fieldr heading", f"await expect(loginPage.heading()).toBeVisible({T});")], ["@smoke"])
case("FLD-AUTH-002", "Login page shows heading, helper text, both tabs, Send OTP and legal links", "P0", "Functional", "Logged out", "-", "All observed elements are visible; legal links point to /terms-and-conditions and /privacy-policy",
     [OPEN, ("Verify the Welcome to Fieldr heading", f"await expect(loginPage.heading()).toBeVisible({T});"), ("Verify the SECURE LOGIN label", f"await expect(loginPage.eyebrow()).toBeVisible({T});"),
      ("Verify the helper text", f"await expect(loginPage.helper()).toBeVisible({T});"), ("Verify the Mobile Number tab", f"await expect(loginPage.mobileTab()).toBeVisible({T});"),
      ("Verify the Email Address tab", f"await expect(loginPage.emailTab()).toBeVisible({T});"), ("Verify the Send OTP button", f"await expect(loginPage.sendOtpBtn()).toBeVisible({T});"),
      ("Verify the Terms link target", "await expect(loginPage.termsLink()).toHaveAttribute('href', /terms-and-conditions/);"),
      ("Verify the Privacy link target", "await expect(loginPage.privacyLink()).toHaveAttribute('href', /privacy-policy/);")], ["@smoke"])
case("FLD-AUTH-003", "Mobile AU valid + correct OTP logs in to the dashboard", "P0", "Functional", "QA number registered; bypass OTP configured", "FLDR_MOBILE / FLDR_OTP (from .env)", "Redirect to /app/dashboard; Dashboard heading visible",
     SENDBYPASS + [("Enter the 6-digit OTP into Digit 1 to Digit 6", "await loginModule.enterOtp(config.otp);"), ("Click Verify & Login", "await loginPage.clickVerify();"),
                   ("Verify the dashboard is shown", "await loginModule.expectOnDashboard();")], ["@smoke"])
case("FLD-AUTH-004", "Send OTP moves to the Check Your Messages step with six digit boxes", "P0", "Functional", "Logged out", "FLDR_MOBILE", "Heading, 'We sent a 6-digit OTP to' text and Digit 1 to Digit 6 boxes shown; Verify & Login disabled",
     SENDBYPASS + [("Verify the sent-to text", f"await expect(loginPage.otpSentTo()).toBeVisible({T});")] +
     [(f"Verify Digit {i} is visible", f"await expect(loginPage.otpDigit({i})).toBeVisible({T});") for i in range(1, 7)] +
     [("Verify Verify & Login is disabled", f"await expect(loginPage.verifyBtn()).toBeDisabled({T});")])
case("FLD-AUTH-005", "Verify & Login is disabled with an empty OTP", "P1", "Validation", "OTP step shown", "empty", "Verify & Login disabled",
     SENDBYPASS + [("Verify Verify & Login is disabled", f"await expect(loginPage.verifyBtn()).toBeDisabled({T});")])
case("FLD-AUTH-006", "Verify & Login stays disabled with a 5-digit OTP (boundary min-1)", "P1", "Boundary", "OTP step shown", "48956", "Verify & Login disabled",
     SENDBYPASS + [("Enter five digits", "await loginModule.enterOtp(AU.otp.fiveDigits);"), ("Verify Verify & Login is disabled", f"await expect(loginPage.verifyBtn()).toBeDisabled({T});")])
case("FLD-AUTH-007", "Wrong OTP is rejected with a 4xx and no session", "P0", "Negative", "OTP step shown", "111111", "HTTP 4xx (not 5xx); user stays on /login; dashboard not reachable",
     SENDBYPASS + [("Enter the wrong OTP", "await loginModule.enterOtp(AU.otp.wrong);"), ("Click Verify & Login and capture the response", "const response = await loginModule.verifyCapturing();"),
                   ("Record the observed response body", RECORD),
                   ("Verify the status is 4xx", "expect(response.status()).toBeGreaterThanOrEqual(400);\n      expect(response.status()).toBeLessThan(500);"),
                   ("Verify the user is still on /login", "await expect(page).toHaveURL(/\\/login/);")])
case("FLD-AUTH-008", "Wrong-OTP message does not reveal account existence", "P1", "Security", "OTP step shown", "111111", "Response body contains none of: not registered, no account, does not exist",
     SENDBYPASS + [("Enter the wrong OTP", "await loginModule.enterOtp(AU.otp.wrong);"), ("Click Verify & Login and capture the response", "const response = await loginModule.verifyCapturing();"),
                   ("Verify the body is generic", "expect(await response.text()).not.toMatch(/not registered|no account|does not exist|doesn't exist/i);")])
case("FLD-AUTH-009", "OTP digit box rejects a letter", "P1", "Validation", "OTP step shown", "a", "Digit 1 stays empty",
     SENDBYPASS + [("Type a letter into Digit 1", "await loginPage.typeIntoOtpDigit(1, AU.otp.letters);"), ("Verify Digit 1 is empty", f"await expect(loginPage.otpDigit(1)).toHaveValue('', {T});")])
case("FLD-AUTH-010", "OTP digit box holds at most one character", "P1", "Boundary", "OTP step shown", "12 typed into Digit 1", "Digit 1 value length <= 1",
     SENDBYPASS + [("Type two digits into Digit 1", "await loginPage.typeIntoOtpDigit(1, '12');"),
                   ("Verify Digit 1 holds at most one character", "expect((await loginPage.otpDigit(1).inputValue()).length).toBeLessThanOrEqual(1);")])
case("FLD-AUTH-011", "Pasting a 6-digit code fills all six boxes", "P1", "Functional", "OTP step shown", "FLDR_OTP", "Digits 1-6 hold the pasted digits (ASSUMPTION: paste is supported)",
     SENDBYPASS + [("Focus Digit 1", "await loginPage.otpDigit(1).focus();"),
                   ("Dispatch a paste event with the OTP", "await page.evaluate((code) => {\n        const dt = new DataTransfer();\n        dt.setData('text', code);\n        document.activeElement?.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true }));\n      }, config.otp);")] +
     [(f"Verify Digit {i}", f"await expect(loginPage.otpDigit({i})).toHaveValue(config.otp[{i - 1}], {T});") for i in range(1, 7)])
case("FLD-AUTH-012", "OTP boxes are named Digit 1 to Digit 6 and Verify is reachable by keyboard", "P1", "Accessibility", "OTP step shown", "-", "Six named textboxes; Verify & Login gets focus within 10 Tab presses once enabled",
     SENDBYPASS + [("Enter the OTP", "await loginModule.enterOtp(config.otp);")] +
     [(f"Verify the accessible name Digit {i}", f"await expect(page.getByRole('textbox', {{ name: 'Digit {i}' }})).toHaveCount(1);") for i in range(1, 7)] +
     [("Press Tab until Verify & Login is focused", "for (let i = 0; i < 10; i += 1) {\n        if (await loginPage.verifyBtn().evaluate((el) => el === document.activeElement)) break;\n        await loginPage.pressTab();\n      }"),
      ("Verify Verify & Login is focused", "await expect(loginPage.verifyBtn()).toBeFocused();")])
case("FLD-AUTH-013", "Resend countdown is shown and starts at 30s or less", "P1", "Functional", "OTP step shown", "-", "'Resend OTP in Ns' with N <= 30",
     SENDBYPASS + [("Verify the countdown text", f"await expect(loginPage.resendTimer()).toBeVisible({T});"),
                   ("Verify the countdown is 30s or less", "const text = (await loginPage.resendTimer().textContent()) ?? '';\n      expect(Number(/(\\d+)s/.exec(text)?.[1])).toBeLessThanOrEqual(30);")])
case("FLD-AUTH-014", "Resend OTP button appears when the countdown ends", "P1", "Flaky", "OTP step shown", "wait ~30s", "Resend OTP button enabled within 45s (time-sensitive)",
     SENDBYPASS + [("Wait for the Resend OTP button", "await expect(loginPage.resendBtn()).toBeEnabled({ timeout: config.timeouts.resend });")], ["@flaky"], slow=True)
case("FLD-AUTH-015", "Resend OTP button is not offered during the countdown", "P1", "Functional", "OTP step shown", "-", "No Resend OTP button while the countdown text shows",
     SENDBYPASS + [("Verify the countdown text", f"await expect(loginPage.resendTimer()).toBeVisible({T});"), ("Verify no Resend OTP button", f"await expect(loginPage.resendBtn()).toHaveCount(0, {T});")])
case("FLD-AUTH-016", "Use a different number or email returns to the identifier step", "P1", "Functional", "OTP step shown", "-", "Identifier step shown; OTP step hidden",
     SENDBYPASS + [("Click Use a different number or email", "await loginPage.clickChangeIdentifier();"), ("Verify Send OTP is shown", f"await expect(loginPage.sendOtpBtn()).toBeVisible({T});"),
                   ("Verify the OTP step is hidden", f"await expect(loginPage.otpHeading()).toBeHidden({T});")])
neg_input("FLD-AUTH-017", "Mobile too short (0412 34) does not request an OTP", "AU.mobile.tooShort", "0412 34")
case("FLD-AUTH-018", "US number typed into the AU field keeps the Australia country selector", "P1", "Negative", "Logged out", "14123456789", "Country selector still shows Australia; nothing is submitted",
     [OPEN, MOBTAB, ("Enter a US-format number", "await loginPage.fillIdentifier(AU.mobile.us);"), ("Verify the country selector still shows Australia", f"await expect(loginPage.countryButton()).toBeVisible({T});")])
case("FLD-AUTH-019", "Letters mixed into the mobile field are stripped", "P1", "Validation", "Logged out", "0412ABC678", "Field value contains no letters (not submitted)",
     [OPEN, MOBTAB, ("Type digits mixed with letters", "await loginPage.fillIdentifier(AU.mobile.lettersMixed);"),
      ("Verify no letters remain", "expect(await loginPage.identifierInput().inputValue()).not.toMatch(/[A-Za-z]/);")])
neg_input("FLD-AUTH-020", "Whitespace-only mobile does not request an OTP", "AU.mobile.whitespace", "3 spaces")
case("FLD-AUTH-021", "Emoji in the mobile field is not accepted", "P1", "Validation", "Logged out", "U+1F642", "Field value has only digits, spaces, +, ( and )",
     [OPEN, MOBTAB, ("Type an emoji", "await loginPage.identifierInput().pressSequentially(AU.mobile.emoji);"),
      ("Verify no emoji remains", "expect(await loginPage.identifierInput().inputValue()).toMatch(/^[+\\d\\s()-]*$/);")])
neg_input("FLD-AUTH-022", "Empty mobile does not request an OTP", "''", "empty")
case("FLD-AUTH-023", "Eleven-digit mobile is truncated to 10 national digits (boundary max+1)", "P1", "Boundary", "Logged out", "04123456789", "At most 10 digits after +61 (not submitted)",
     [OPEN, MOBTAB, ("Type 11 digits", "await loginPage.fillIdentifier(AU.mobile.elevenDigits);"),
      ("Verify at most 10 national digits", "const digits = (await loginPage.identifierInput().inputValue()).replace(/^\\+61/, '').replace(/\\D/g, '');\n      expect(digits.length).toBeLessThanOrEqual(10);")])
case("FLD-AUTH-024", "National format 0412 345 678 is masked as +61 (04) 1234 5678", "P1", "Functional", "Logged out", "0412345678", "Observed mask +61 (04) 1234 5678 (not submitted)",
     [OPEN, MOBTAB, ("Type the national number", "await loginPage.fillIdentifier('0412345678');"),
      ("Verify the mask", f"await expect(loginPage.identifierInput()).toHaveValue(AU.mask('0412345678'), {T});")])
case("FLD-AUTH-025", "Surrounding whitespace is ignored by the mobile mask", "P1", "Validation", "Logged out", "'  0444124222 '", "Value +61 (04) 4412 4222 (not submitted)",
     [OPEN, MOBTAB, ("Type the number with surrounding spaces", "await loginPage.fillIdentifier('  0444124222 ');"),
      ("Verify the mask", f"await expect(loginPage.identifierInput()).toHaveValue(AU.mask('0444124222'), {T});")])
case("FLD-AUTH-026", "Unregistered mobile never reaches the dashboard and does not leak account existence", "P0", "Security", "FLDR_UNREGISTERED_MOBILE belongs to no user", "FLDR_UNREGISTERED_MOBILE", "Not on dashboard; response recorded for PO review (enumeration policy is undecided)",
     [OPEN, MOBTAB, ("Enter the unregistered mobile", "await loginPage.fillIdentifier(config.unregisteredMobile);"),
      ("Click Send OTP and capture the response", "const response = await loginModule.sendOtpCapturing();"), ("Record the observed response", RECORD),
      ("Verify the dashboard is not shown", "await expect(page).not.toHaveURL(/\\/app\\/dashboard/);")])
case("FLD-AUTH-027", "Email Address tab replaces the mobile field and hides the country selector", "P0", "Functional", "Logged out", "-", "Identifier field shown without the Australia selector; Send OTP visible",
     [OPEN, EMAILTAB, ("Verify the country selector is hidden", f"await expect(loginPage.countryButton()).toBeHidden({T});"),
      ("Verify Send OTP is shown", f"await expect(loginPage.sendOtpBtn()).toBeVisible({T});")])
case("FLD-AUTH-028", "Email valid + correct OTP logs in", "P0", "Functional", "FLDR_EMAIL set and the bypass OTP applies to email (ASSUMPTION)", "FLDR_EMAIL / FLDR_OTP", "Redirect to /app/dashboard",
     [("Log in with the registered email", "await loginModule.loginWithEmail(config.email);")], skip="!config.email")
neg_email("FLD-AUTH-029", "Email without @ does not request an OTP", "AU.email.noAt", "noah.smithbigpond.net.au")
neg_email("FLD-AUTH-030", "Email with missing TLD does not request an OTP", "AU.email.missingTld", "noah.smith@bigpond")
neg_email("FLD-AUTH-031", "Email with a double dot does not request an OTP", "AU.email.doubleDot", "noah..smith@bigpond.net.au")
neg_email("FLD-AUTH-032", "Empty email does not request an OTP", "''", "empty")
neg_email("FLD-AUTH-033", "Whitespace-only email does not request an OTP", "AU.email.whitespace", "3 spaces")
case("FLD-AUTH-034", "Login page has no horizontal scroll at 375x667", "P1", "Responsive", "Logged out", "viewport 375x667", "document scrollWidth <= viewport width; Send OTP inside the viewport",
     [("Set the viewport to 375x667", "await page.setViewportSize({ width: 375, height: 667 });"), OPEN,
      ("Verify there is no horizontal scroll", "expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);"),
      ("Verify Send OTP is visible", f"await expect(loginPage.sendOtpBtn()).toBeVisible({T});")])
case("FLD-AUTH-035", "Unregistered email never reaches the dashboard", "P0", "Security", "Logged out", "qa+<epoch>@example.com (RFC 2606, cannot deliver)", "Not on dashboard; response recorded",
     [OPEN, EMAILTAB, ("Enter an unregistered email", "await loginPage.fillIdentifier(DataGenerator.unregisteredEmail());"),
      ("Click Send OTP and capture the response", "const response = await loginModule.sendOtpCapturing();"), ("Record the observed response", RECORD),
      ("Verify the dashboard is not shown", "await expect(page).not.toHaveURL(/\\/app\\/dashboard/);")])
case("FLD-AUTH-036", "Expired OTP prompts the user to resend", "P0", "Negative", "Needs a real OTP that has expired", "-", "Expired message and a Resend OTP option",
     [("Request an OTP and wait past its validity window", "// The QA bypass OTP never expires, so this case needs a live SMS OTP.")], fixme="QA bypass OTP never expires; run manually with a live SMS OTP (window length unknown - ask PO)")
case("FLD-AUTH-037", "A used OTP cannot be replayed", "P0", "Security", "Needs a single-use live OTP", "-", "Second use rejected",
     [("Log in once with a live OTP, log out, then reuse the same OTP", "// The QA bypass OTP is static, so replay cannot be tested with it.")], fixme="Static bypass OTP is reusable by design; test manually with a live OTP")
case("FLD-AUTH-038", "Twenty wrong OTPs in 60s trigger a lock or rate limit", "P0", "Security", "FLDR_ALLOW_LOCKOUT=1 (may lock the shared QA account)", "20 x wrong OTPs", "429 or a lock message before the 20th attempt",
     SENDBYPASS + [("Submit wrong OTPs and stop at the first 429 or lock message", "let limited = false;\n      for (let attempt = 0; attempt < 20 && !limited; attempt += 1) {\n        await loginModule.enterOtp(AU.otp.wrong);\n        const response = await loginModule.verifyCapturing();\n        limited = response.status() === 429 || /lock|too many|try again/i.test(await response.text());\n      }"),
                   ("Verify rate limiting kicked in", "expect(limited).toBe(true);")], skip="!config.allowLockout", tags=["@destructive"])
case("FLD-AUTH-039", "Resend restarts the countdown (throttle)", "P0", "Flaky", "OTP step shown", "wait ~30s", "After Resend OTP the countdown text returns at 30s or less",
     SENDBYPASS + [("Wait for the Resend OTP button", "await expect(loginPage.resendBtn()).toBeEnabled({ timeout: config.timeouts.resend });"), ("Click Resend OTP", "await loginPage.clickResend();"),
                   ("Verify the countdown returns", f"await expect(loginPage.resendTimer()).toBeVisible({N});")], ["@flaky"], slow=True)
case("FLD-AUTH-040", "Session survives a page reload", "P0", "Functional", "Logged in", "-", "Still on /app/dashboard after reload",
     [("Reload the dashboard", "await page.reload();"), ("Verify the dashboard is shown", "await loginModule.expectOnDashboard();")], ["@session"])
case("FLD-AUTH-041", "Session is shared with a second tab", "P0", "Functional", "Logged in", "-", "New tab opens /app/dashboard without asking for login",
     [("Open a second tab", "const second = await context.newPage();"), ("Open the dashboard in the second tab", "await second.goto('/app/dashboard');"),
      ("Verify the second tab shows Dashboard", f"await expect(second.getByRole('heading', {{ name: 'Dashboard', level: 1 }})).toBeVisible({N});")], ["@session"])
case("FLD-AUTH-042", "Logout ends the session", "P0", "Functional", "Logged in", "-", "Redirect to /login; /app/dashboard redirects to /login again (logout label: NEEDS UI INSPECTION)",
     [("Log out from the user menu", "await loginModule.logout();"), ("Open /app/dashboard", "await dashboardPage.open();"), ("Verify the URL is /login", LOGURL)], ["@session"])
case("FLD-AUTH-043", "Tampered session cookie is rejected on the next request", "P0", "Security", "Logged in", "every cookie value reversed", "Redirect to /login",
     [("Read all cookies", "const cookies = await context.cookies();"), ("Verify a session cookie exists", "expect(cookies.length).toBeGreaterThan(0);"),
      ("Replace every cookie value with a corrupted one", "await context.clearCookies();\n      await context.addCookies(cookies.map((c) => ({ ...c, value: `${c.value.split('').reverse().join('')}x` })));"),
      ("Open /app/dashboard", "await dashboardPage.open();"), ("Verify the URL is /login", LOGURL)], ["@session"])
case("FLD-AUTH-044", "Deleting all cookies ends the session", "P0", "Security", "Logged in", "-", "Redirect to /login",
     [("Clear all cookies", "await context.clearCookies();"), ("Open /app/dashboard", "await dashboardPage.open();"), ("Verify the URL is /login", LOGURL)], ["@session"])
case("FLD-AUTH-045", "Back button after logout does not reveal the dashboard", "P1", "Security", "Logged in", "-", "Dashboard content is not shown after Back",
     [("Log out from the user menu", "await loginModule.logout();"), ("Press the browser Back button", "await page.goBack();"),
      ("Verify the dashboard heading is not shown", f"await expect({DASH_H}).toBeHidden({T});")], ["@session"])
case("FLD-AUTH-046", "Unauthenticated deep link /app/job/list redirects to login", "P1", "Security", "No session cookie", "/app/job/list", "Redirect to /login",
     [("Open /app/job/list without a session", "await dashboardPage.openDeepLink('/app/job/list');"), ("Verify the URL is /login", LOGURL)])
case("FLD-AUTH-047", "Idle session times out", "P1", "Flaky", "Logged in", "idle period unknown", "Redirect to /login after the idle window",
     [("Stay idle for the configured window", "// Idle timeout duration is unknown (ask PO).")], fixme="Idle-timeout length not documented; needs PO input and a controllable clock")
case("FLD-AUTH-048", "Send OTP response does not expose the OTP", "P1", "Security", "Logged out", "FLDR_MOBILE", "Response body contains neither the OTP nor an otp/code/passcode field with 6 digits",
     [OPEN, MOBTAB, ("Enter the QA mobile number", "await loginPage.fillIdentifier(config.mobile);"),
      ("Click Send OTP and capture the response body", "const body = await (await loginModule.sendOtpCapturing()).text();"),
      ("Verify the OTP is not in the body", "expect(body).not.toContain(config.otp);\n      expect(body).not.toMatch(/\"(otp|code|passcode)\"\\s*:\\s*\"?\\d{6}/i);")])
case("FLD-AUTH-049", "XSS payload in the email field is not executed", "P1", "Security", "Logged out", "\"><img src=x onerror=window.__xss=1>", "window.__xss stays undefined; no dialog",
     [OPEN, EMAILTAB, ("Enter the payload and click Send OTP only if it is enabled", "await loginModule.trySendIdentifier(AU.email.xss);"),
      ("Verify the payload did not execute", "expect(await page.evaluate(() => (window as unknown as { __xss?: number }).__xss)).toBeUndefined();")])
case("FLD-AUTH-050", "SQL-injection payload in the email field causes no server error", "P1", "Security", "Logged out", "' OR '1'='1", "No 5xx response; OTP step not shown",
     [OPEN, EMAILTAB, ("Collect server errors", "const serverErrors: number[] = [];\n      page.on('response', (r) => { if (r.status() >= 500) serverErrors.push(r.status()); });"),
      ("Enter the payload and click Send OTP only if it is enabled", "await loginModule.trySendIdentifier(AU.email.sqli);"),
      ("Verify no 5xx occurred", "expect(serverErrors).toEqual([]);"), ("Verify the OTP step is not shown", "await loginModule.expectStillOnIdentifierStep();")])

LOGGED_IN = {"FLD-AUTH-040", "FLD-AUTH-041", "FLD-AUTH-042", "FLD-AUTH-043", "FLD-AUTH-044", "FLD-AUTH-045"}
assert [c["id"] for c in cases] == [f"FLD-AUTH-{i:03d}" for i in range(1, 51)], len(cases)

# ------------------------------------------------------------------ emit specs
for c in cases:
    body = "\n".join(f"    await test.step({json.dumps(t)}, async () => {{\n      {code}\n    }});" for t, code in c["steps"])
    joined = " ".join(code for _, code in c["steps"])
    fx = [n for n in ("loginPage", "dashboardPage", "loginModule", "page", "context") if n in joined]
    if c["id"] in LOGGED_IN:
        fx.append("loggedIn")
    imports = ["import { test, expect } from '@fixtures';"]
    if "config." in joined or c["skip"]:
        imports.append("import { config } from '@config/index';")
    if "AU." in joined:
        imports.append("import { AU } from '@testdata/au';")
    if "DataGenerator" in joined:
        imports.append("import { DataGenerator } from '@utils/DataGenerator';")
    tags = [f"@{c['prio']}", "@regression", "@auth"] + c["tags"]
    if c["typ"] == "Security":
        tags.append("@security")
    tags = list(dict.fromkeys(tags))
    pre = []
    if c["skip"]:
        pre.append(f"    test.skip({c['skip']}, {json.dumps('Precondition not met: ' + c['pre'])});")
    if c["fixme"]:
        pre.append(f"    test.fixme(true, {json.dumps(c['fixme'])});")
    if c["slow"]:
        pre.append("    test.slow();")
    parts = [f"// {c['id']} | {c['prio']} | {c['typ']}", f"// Preconditions: {c['pre']}", f"// Expected: {c['exp']}", "\n".join(imports), "",
             f"test.describe({json.dumps(c['id'])}, () => {{",
             f"  test({json.dumps(c['id'] + ' ' + c['title'])}, {{ tag: {json.dumps(tags)} }}, async ({{ {', '.join(fx)} }}) => {{"]
    parts += pre + [body, "  });", "});", ""]
    w(f"src/tests/auth/{c['id']}.e2e.ts", "\n".join(parts))

# ------------------------------------------------------------------ emit the matching manual table
rows = ["| ID | Title | Module | Preconditions | Steps | Test Data (AU) | Expected Result | Priority | Type |", "|----|-------|--------|---------------|-------|----------------|-----------------|----------|------|"]
for c in cases:
    steps = "<br>".join(f"{i}. {t}" for i, (t, _) in enumerate(c["steps"], 1))
    typ = "Flaky" if "@flaky" in c["tags"] else c["typ"]
    rows.append(f"| {c['id']} | {c['title']} | AUTH | {c['pre']} | {steps} | {c['data']} | {c['exp']} | {c['prio']} | {typ} |")
with open(os.path.join(os.path.dirname(ROOT), "auth-test-cases.md"), "w", encoding="utf-8") as f:
    f.write("# FLD-AUTH-001 to 050 (generated from the Playwright specs)\n\nObserved 2026-09-19: login page, OTP step (six `Digit n` boxes, `Verify & Login`, resend countdown) and dashboard. Anything marked ASSUMPTION or NEEDS UI INSPECTION is unverified.\n\n" + "\n".join(rows) + "\n")

print("specs:", len(cases))
```

### 7.5 `gen_plan.py`
Generates test-plan.md and test-data-table.md from the case lists and the CSVs.

```python
"""Generate test-plan.md and test-data-table.md (counts are computed, never typed by hand)."""
import csv, os

HERE = os.path.dirname(os.path.abspath(__file__))


def n(v):
    return "<br>".join(f"{i}. {s}" for i, s in enumerate(v, 1))


# ---- REG: adding people (observed forms: Add Customer, Add New User). Self sign-up was NOT observed.
REG = [
    ("Add Customer with all required fields", "P0", "Functional", ["Open Customer", "Click Add Customer", "Enter First Name", "Enter Last Name", "Enter Mobile Number", "Enter Email", "Enter Address", "Enter Description", "Click Save"], "Olivia Nguyen / 0491 570 156 / olivia.nguyen@yopmail.com / 12 Macquarie Street, Sydney NSW 2000", "Customer saved; appears in list with a CST- number"),
    ("Add Customer with empty First Name", "P1", "Negative", ["Open Add Customer", "Leave First Name empty", "Fill all other fields", "Click Save"], "empty", "Save disabled or inline error on First Name"),
    ("Add Customer with duplicate mobile", "P0", "Negative", ["Open Add Customer", "Enter a mobile already used", "Fill other fields", "Click Save"], "existing customer mobile", "Rejected with a duplicate-mobile message"),
    ("Add Customer mobile too short (9 digits)", "P1", "Boundary", ["Open Add Customer", "Enter 041234567 in Mobile Number", "Fill other fields", "Click Save"], "041234567", "Rejected, inline validation"),
    ("Add Customer email without @", "P1", "Validation", ["Open Add Customer", "Enter noah.smithbigpond.net.au in Email", "Click Save"], "no @", "Inline email error"),
    ("Add Customer email 255 chars", "P2", "Boundary", ["Open Add Customer", "Enter a 255-char email", "Click Save"], "255 chars (bigpond.net.au)", "Rejected (max 254)"),
    ("Add Customer name with emoji only", "P2", "Validation", ["Open Add Customer", "Enter an emoji in First Name", "Click Save"], "U+1F642", "Rejected or stripped"),
    ("Add Customer name 101 chars (ASSUMPTION max 100)", "P2", "Boundary", ["Open Add Customer", "Enter 101 chars in Last Name", "Click Save"], "N x 101", "Rejected; max length NEEDS UI INSPECTION"),
    ("Add Customer XSS in Description is escaped", "P1", "Security", ["Open Add Customer", "Enter an img onerror payload in Description", "Fill other fields", "Click Save", "Open the customer"], "XSS payload", "Rendered as text; no script runs"),
    ("Add Customer profile photo upload", "P2", "Functional", ["Open Add Customer", "Choose avatar-001.png", "Fill required fields", "Click Save"], "avatar-001.png", "Photo shows on card and profile"),
    ("Add New User with all required fields", "P0", "Functional", ["Open User", "Click Add User", "Enter First Name", "Enter Last Name", "Select Industry", "Select Role", "Enter Email", "Enter Mobile Number", "Click Save"], "Liam Fraser / Construction / User", "User appears in list (needs a free seat)"),
    ("Add New User when the plan has no free seat", "P0", "Negative", ["Open Add New User", "Fill all required fields", "Click Save"], "Basic plan, 1 seat", "Clear seat-limit message and no orphan user (observed: redirect to Subscription)"),
    ("Add New User without Role", "P1", "Negative", ["Open Add New User", "Fill fields except Role", "Click Save"], "no role", "Inline error on Role"),
    ("Add New User with a mobile from another tenant", "P1", "Security", ["Open Add New User", "Enter a mobile registered elsewhere", "Click Save"], "registered number", "Generic message that does not reveal other tenants"),
    ("Add New User Date Of Birth 29/02/1900", "P2", "Boundary", ["Open Add New User", "Pick 29/02/1900 in Date Of Birth"], "29/02/1900", "Date rejected (not a leap year)"),
    ("Add New User postcode 4 digits", "P2", "Validation", ["Open Add New User", "Enter 2000 in Postcode"], "2000", "Accepted"),
    ("Add New User state list has only AU states", "P2", "Validation", ["Open Add New User", "Open the State list"], "-", "NSW, VIC, QLD, WA, SA, TAS, ACT, NT only; no duplicates"),
    ("Add New User tag creation", "P3", "Functional", ["Open Add New User", "Type Electrician in Tags", "Press Enter"], "Electrician", "Tag created and shown"),
    ("Add Group and assign members", "P1", "Functional", ["Open User", "Open Groups", "Add a group", "Choose members", "Save"], "Electrical Crew", "Group lists its members (observed: members showed 0 after an API update)"),
    ("Keyboard-only completion of Add Customer", "P2", "Accessibility", ["Open Add Customer", "Press Tab through every field", "Press Enter on Save"], "-", "Logical focus order; errors are announced"),
]

CK = [
    ("Add Item with sell and cost price", "P0", "Functional", ["Open Items", "Click Add Item", "Enter Item Name", "Enter Unit", "Enter Sell Price", "Enter Cost Price", "Enter Description", "Click Save"], "Labour - Electrician / hour / 110 / 71.50", "Item saved"),
    ("Item cost price above sell price", "P1", "Validation", ["Open Add Item", "Enter Sell Price 100", "Enter Cost Price 120", "Click Save"], "100 / 120", "Warning or rejection (negative margin); NEEDS UI INSPECTION"),
    ("Item negative sell price", "P1", "Negative", ["Open Add Item", "Enter -0.01 in Sell Price", "Click Save"], "-0.01", "Rejected"),
    ("Item sell price with 3 decimals", "P2", "Boundary", ["Open Add Item", "Enter 1100.005 in Sell Price", "Click Save"], "1100.005", "Rounded or rejected to 2 dp"),
    ("Item price typed as $1,100.00", "P2", "Validation", ["Open Add Item", "Type $1,100.00 in Sell Price"], "$1,100.00", "Number field rejects the symbols or normalises"),
    ("Add Invoice with 1 line", "P0", "Functional", ["Open Invoices", "Click Add Invoice", "Select Customer", "Enter Invoice Date", "Enter Due Date", "Add a line item", "Click Save"], "2 x $630.00", "Sub-total $1,260.00, GST $126.00, total $1,386.00"),
    ("Invoice GST is 10 percent of the sub-total", "P0", "Functional", ["Create an invoice of $1,100.00", "Read the total"], "$1,100.00", "Total shows $1,210.00"),
    ("Invoice with line discount", "P1", "Functional", ["Add a line with 10 in Discount", "Read totals"], "10%", "Discount applied before GST"),
    ("Invoice due date before invoice date", "P1", "Negative", ["Set Invoice Date 19/09/2026", "Set Due Date 18/09/2026", "Click Save"], "18/09/2026", "Rejected"),
    ("Invoice with quantity 0", "P1", "Boundary", ["Add a line with Quantity 0", "Click Save"], "0", "Rejected or line removed"),
    ("Invoice with negative rate", "P1", "Negative", ["Add a line with Rate -10", "Click Save"], "-10", "Rejected"),
    ("Invoice without a customer", "P1", "Negative", ["Leave Customer empty", "Click Save"], "empty", "Inline error"),
    ("Invoice status order: Draft, Awaiting Approval, Awaiting Payment, Paid", "P0", "Functional", ["Create a draft invoice", "Submit for approval", "Approve", "Record payment"], "-", "Each change allowed only in order; dashboard tiles update"),
    ("Invoice amounts cannot be set through the API", "P0", "Security", ["Send PUT invoice/update with amountPaid equal to the total", "Read the invoice"], "amountPaid = total", "Rejected (observed: accepted, finding F1)"),
    ("Invoice BSB accepts XXX-XXX only", "P1", "Validation", ["Open payment details", "Enter 062000", "Enter 062-000"], "062-000", "Hyphenated format accepted; BSB screen NEEDS UI INSPECTION"),
    ("Company ABN checksum", "P1", "Validation", ["Open Settings, Company Settings", "Enter 33 102 417 032", "Enter 12 345 678 901"], "valid / invalid ABN", "Valid accepted; invalid rejected"),
    ("Add Quote requires at least one item", "P0", "Negative", ["Open Quote", "Click Add Quote", "Select Customer", "Enter Quote Description", "Click Next", "Save with no items"], "no items", "Rejected: A quote must contain at least one item"),
    ("Add Quote with sections and items", "P0", "Functional", ["Add a Labour section", "Add a line item", "Add a Materials section", "Add a line item", "Save"], "2 sections", "Quote saved with a serial number"),
    ("Quote formula: Qty x Rate x 1.2", "P0", "Functional", ["Open Quote, Formulas", "Click Add Formula", "Enter a Column Name", "Pick Qty.", "Pick x", "Pick Rate", "Pick x", "Insert 1.2", "Click Save"], "Qty 10, Rate 50", "Live preview shows 600.00"),
    ("Quote formula cannot end on an operator", "P1", "Validation", ["Add a formula", "Pick Qty.", "Pick x"], "Qty. x", "Save stays disabled until the formula is complete"),
    ("Quote formula column shown on the customer PDF", "P2", "Functional", ["Turn on Show to Customer", "Save", "Open the quote PDF"], "-", "Column printed; internal columns hidden"),
    ("Quote line types Labour and Material", "P1", "Functional", ["Add a Labour line", "Add a Material line", "Read the quote"], "labour / material", "Types shown correctly"),
    ("Job with a report template attached", "P1", "Functional", ["Open a job", "Open Reports", "Attach a template", "Save", "Open Job Report"], "Electrical Job Completion Report", "Report created with status Created"),
    ("Job cap on the Solo plan", "P1", "Functional", ["Create 6 active jobs on Solo"], "6th job", "Blocked with a plan-limit message (observed 403)"),
    ("Job start and end time", "P1", "Functional", ["Open Add Job", "Enter Start Date", "Enter End Date", "Save"], "16/09/2026 to 17/09/2026", "Job shows on the week schedule"),
    ("Job Site Radius 1 to 10,000 m", "P2", "Boundary", ["Enter Site Radius 0", "Enter Site Radius 10001"], "0 / 10001", "Both rejected; 1 and 10000 accepted"),
    ("Holiday create and duplicate date", "P2", "Negative", ["Add Holiday 26/01/2026", "Add another on the same date"], "26/01/2026", "Second rejected (observed 409)"),
    ("Checklist item order", "P3", "Functional", ["Open Checklist", "Add 3 items", "Save"], "3 items", "Items keep their order"),
    ("Report template builder field types", "P2", "Functional", ["Open Report Builder", "Add each field type", "Save"], "Textbox, Dropdown, Radio, Checkbox, Textarea, Number, Upload, Email, Date", "Template saved and renders on a job report"),
    ("Dashboard tiles match the data", "P0", "Regression", ["Open Dashboard", "Compare each tile with its list"], "-", "Jobs, Completed, Revenue, Outstanding and Pending counts match the lists"),
]

CT = [
    ("Terms & Conditions link opens the terms page", "P1", "Functional", ["Open the login page", "Click Terms & Conditions"], "-", "Opens /terms-and-conditions"),
    ("Privacy Policy link opens the privacy page", "P1", "Functional", ["Open the login page", "Click Privacy Policy"], "-", "Opens /privacy-policy"),
    ("CMS list shows Type, Created By and Date", "P2", "Functional", ["Open CMS"], "-", "Columns TYPE, CREATED BY, DATE, ACTION shown"),
    ("Add a CMS entry of each type", "P1", "Functional", ["Click Add CMS", "Select Type", "Enter Title", "Enter Content", "Click Save"], "Induction, Help, Privacy Policy, Terms & Conditions, FAQ", "Entry appears in the list"),
    ("CMS Title empty", "P1", "Negative", ["Click Add CMS", "Select Type", "Leave Title empty", "Save"], "empty", "Inline error (the API returns 500, finding F3)"),
    ("CMS Content empty", "P1", "Negative", ["Click Add CMS", "Enter Title", "Leave Content empty", "Save"], "empty", "Inline error"),
    ("CMS rich text stores a script safely", "P1", "Security", ["Enter a script tag in Content", "Save", "View the page"], "XSS payload", "Sanitised; no alert"),
    ("CMS Title 255 chars", "P2", "Boundary", ["Enter 255 chars in Title", "Save"], "255", "Accepted or rejected consistently; limit NEEDS UI INSPECTION"),
    ("Notifications page lists events", "P2", "Functional", ["Open Notifications"], "-", "Recent events listed; unread count clears"),
    ("Notification badge increments after a new job", "P3", "Functional", ["Create a job", "Read the sidebar badge"], "-", "Badge increases by 1"),
    ("Help entries are findable", "P3", "Functional", ["Open Help content", "Search for invoice"], "invoice", "Matching entries shown; help UI NEEDS UI INSPECTION"),
    ("Support contact page exists", "P2", "Functional", ["Look for a Support or Contact page"], "-", "NEEDS UI INSPECTION: no contact form was observed"),
    ("Contact form rejects an invalid email", "P2", "Validation", ["Open the contact form", "Enter noah.smith@bigpond", "Submit"], "noah.smith@bigpond", "Blocked; depends on the form existing"),
    ("Contact form mobile format", "P2", "Validation", ["Enter +61 412 345 678", "Enter 0412ABC678"], "AU mobiles", "First accepted, second rejected"),
    ("Login footer links are keyboard reachable", "P3", "Accessibility", ["Open the login page", "Press Tab to the footer links"], "-", "Both links focusable with a visible focus ring"),
]


def rows(code, cases):
    out = ["| ID | Title | Module | Preconditions | Steps | Test Data (AU) | Expected Result | Priority | Type |", "|----|-------|--------|---------------|-------|----------------|-----------------|----------|------|"]
    for i, (t, p, ty, steps, data, exp) in enumerate(cases, 1):
        out.append(f"| FLD-{code}-{i:03d} | {t} | {code} | Logged in as the QA user | {n(steps)} | {data} | {exp} | {p} | {ty} |")
    return "\n".join(out)


auth = open(os.path.join(HERE, "auth-test-cases.md"), encoding="utf-8").read()
auth_rows = [l for l in auth.splitlines() if l.startswith("| FLD-AUTH-")]
counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
for l in auth_rows:
    counts[[c.strip() for c in l.split("|")][-3]] += 1
for cs in (REG, CK, CT):
    for c in cs:
        counts[c[1]] += 1
total = sum(counts.values())

csvs = {}
for f in sorted(os.listdir(os.path.join(HERE, "csv"))):
    with open(os.path.join(HERE, "csv", f), encoding="utf-8") as fh:
        rr = list(csv.reader(fh))[1:]
        csvs[f[:-4]] = (len(rr), sum(1 for r in rr if r[3].startswith("ACCEPT")), sum(1 for r in rr if r[3].startswith(("REJECT", "TRUNC"))))

plan = f"""# Fieldr Test Plan

**Observed 2026-09-19 on the live dev tenant:** login and OTP screens, Dashboard, Customer, User, Quote (with Formulas), Job (all tabs), Timesheet, Job Report, Invoices, Items, CMS, Settings (Company, Holidays, Checklists, Report Builder, Subscription, Payment Cards). Items marked ASSUMPTION or NEEDS UI INSPECTION were not observed.

## 1. Executive summary
- Scope: authentication, adding people, commercial documents (items, quotes, invoices, jobs), content and legal pages.
- Total cases: **{total}** (AUTH {len(auth_rows)}, REG {len(REG)}, CKOUT {len(CK)}, CONT {len(CT)}).
- Priority split: P0 {counts['P0']}, P1 {counts['P1']}, P2 {counts['P2']}, P3 {counts['P3']}.
- Automated: AUTH-001 to 050 as Playwright specs (`pw/src/tests/auth`). They have not been installed or run yet.
- Blockers: no timesheet or crew data can be created (the timelog API stores nothing); users need extra seats; OTP expiry, replay and idle timeout cannot be tested with the static bypass OTP.
- Findings so far: 10 (see SECURITY_API_TEST_REPORT.md).

## 2. Test environment
| Item | Value |
|---|---|
| URL | https://rajanjagz7.dev.fieldr.app |
| Auth | Passwordless OTP, six boxes ("Digit 1" to "Digit 6"), button "Verify & Login" |
| Plan | Basic ($49/mo), Stripe test mode |
| Browsers | Chrome, Firefox, Safari (WebKit), Edge (latest) |
| Viewports | 1920x1080, 1366x768, 768x1024, 375x667, 320x568 |
| OS | Windows 11 (runner); Safari via Playwright WebKit |
| Data | 101 customers, 100 items, 180 invoices, 277 jobs, 101 quotes, 375 job reports, 6 formulas, 40 CMS entries, 27 holidays, 3 checklists, 3 report templates |

## 3. Test cases
### AUTH: authentication and sessions ({len(auth_rows)} cases)
Full table: [auth-test-cases.md](auth-test-cases.md), generated from the Playwright specs.

### REG: adding people: customers, users, groups ({len(REG)} cases)
{rows('REG', REG)}

### CKOUT: items, quotes, formulas, invoices, jobs, settings data ({len(CK)} cases)
{rows('CKOUT', CK)}

### CONT: CMS, notifications, legal and contact ({len(CT)} cases)
{rows('CONT', CT)}

## 4. Negative and boundary matrix
One row per field. Counts come from `csv/<field>.csv`; the expected result for every value is in the CSV.

| Field | Total values | Expect accept | Expect reject |
|---|---|---|---|
""" + "\n".join(f"| {k} | {v[0]} | {v[1]} | {v[2]} |" for k, v in csvs.items()) + """

Boundary rules used: mobile 10 national digits; email local part 64 and total 254; OTP exactly 6 digits; postcode 4 digits; account 6 to 9 digits; ABN 11 digits mod-89; TFN 9 digits mod-11; names 1 to 100 (ASSUMPTION); DOB from 01/01/1900.

## 5. ASSUMPTION register
| # | Item | Status |
|---|---|---|
| A1 | Name max length is 100 | NEEDS UI INSPECTION |
| A2 | Address max length is 254 | NEEDS UI INSPECTION |
| A3 | OTP validity window and replay behaviour | Unknown; the bypass OTP is static |
| A4 | Idle timeout length | Unknown |
| A5 | Logout menu label | Not observed (spec uses a regex) |
| A6 | Email-login bypass OTP applies to email | Unverified |
| A7 | RBAC roles beyond Customer and User | Not observed; Roles & Permissions is a Business-plan feature |
| A8 | Self sign-up and a public Contact page | Not observed |
| A9 | The master prompt lists 7999 and 9999 as invalid postcodes, 0200 as NT, and +61 12 345 6789 as too short | Conflicts with the real ranges: TAS is 7000-7999, QLD PO boxes reach 9999, 0200-0299 is ACT, and that number is 10 digits without a mobile prefix. The CSVs follow the real ranges |
| A10 | Payment-card and BSB screens | Not observed |

## 6. Risks and mitigation
| Risk | Mitigation |
|---|---|
| A live SMS OTP is not testable | Use the QA bypass OTP; keep expiry and replay cases manual |
| Brute-force cases can lock the shared bypass account | AUTH-038 is skipped unless FLDR_ALLOW_LOCKOUT=1 |
| Seeded mobiles may belong to real people | Keep SMS notifications off; prefer ACMA-reserved numbers |
| The app reloads on deploy and drops open forms | Run UI cases in short bursts and re-verify saved values |
| Timesheet and crew tiles cannot be filled | Needs the mobile clock-on payload or a seat upgrade |
| Plan limits change results (5 jobs on Solo, 1 seat on Basic) | Record the plan in every run |
"""
open(os.path.join(HERE, "test-plan.md"), "w", encoding="utf-8").write(plan)

lib = """# Test data table (AU library)

Values are used verbatim. They are typed only unless a case says otherwise. Full per-field lists with expected results are in `csv/` (each file has 100+ rows).

## Mobile
| Kind | Values |
|---|---|
| Valid | +61 412 345 678, +61 423 456 789, +61 434 567 890, +61 458 901 234, +61 401 234 567 |
| National | 0412 345 678, 0423 456 789 |
| Negative | +61 12 345 6789 (no mobile prefix), +1 412 345 6789 (US), +61 4 (prefix only), 0412ABC678, whitespace, emoji |
| Boundary | 9, 10, 11, 12 and 15 digits |
| Warning | 0412 345 678 and 0491 570 159 were already registered to other accounts; do not submit them |

## Email
| Kind | Values |
|---|---|
| Valid | olivia.nguyen@example.com.au, noah.smith@bigpond.net.au, mia.collins@aussie.com.au, jack.wilson+invoices@gmail.com |
| Seeded records | @yopmail.com only |
| Negative | no @, missing TLD, double dot, leading or trailing space, IDN homoglyph, local part over 64 |
| Boundary | local 1, 64 and 65 chars; total 254, 255 and 256 chars |

## OTP
| Kind | Values |
|---|---|
| QA bypass | set in `.env` as FLDR_OTP (6 digits) |
| Valid format | 100000, 999999, 482913 |
| Negative | 99999 (5 digits), 1000000 (7 digits), abcdef, empty, 12 34 56, 000000, 111111 |

## Addresses
| State | Address |
|---|---|
| NSW | 12 Macquarie Street, Sydney NSW 2000 |
| VIC | 88 Bourke Street, Melbourne VIC 3000 |
| QLD | 145 Eagle Street, Brisbane QLD 4000 |
| WA | 27 Adelaide Terrace, Perth WA 6000 |
| SA | 101 Rundle Mall, Adelaide SA 5000 |
| TAS | 9 Brisbane Street, Hobart TAS 7000 |
| ACT | 21 London Circuit, Canberra ACT 2601 |
| NT | 76 Mitchell Street, Darwin NT 0800 |

Postcode ranges used: ACT 0200-0299, 2600-2618, 2900-2920; NT 0800-0999; NSW 1000-2599, 2619-2898, 2921-2999; VIC 3000-3999, 8000-8999; QLD 4000-4999, 9000-9999; SA 5000-5999; WA 6000-6999; TAS 7000-7999.

## Finance identifiers
| Kind | Values |
|---|---|
| ABN valid | 33 102 417 032 (mod-89) |
| ABN invalid | 12 345 678 901 |
| TFN valid | 123 456 782 (mod-11) |
| TFN invalid | 123 456 789 |
| BSB | 062-000, 123-456, 032-198 |
| Account | 6 to 9 digits; negatives: letters, more than 4 leading zeros |
| Currency | AUD, "$" prefix, 2 decimals, GST 10% (subtotal $1,100.00 gives total $1,210.00) |

## Names
First: Olivia, Noah, Mia, Jack, Aria, Liam, Charlotte, William, Zoe, Ethan. Last: Nguyen, Smith, Collins, Wilson, Patel, Brown, Anderson, Lee, Khan, White. Negatives: User1234, emoji only, 200+ characters, only spaces.
The seed script uses a wider pool of 50 first and 50 last names so seeded customers have unique full names.

## Dates (dd/mm/yyyy)
Valid: 14/02/1990, 29/02/2000 (leap), 01/01/1900, 31/12/2025. Invalid: 29/02/1900, 31/04/2024, 32/01/2024, 00/01/2024, 13/13/2024.

## Files generated
| File | Rows |
|---|---|
""" + "\n".join(f"| csv/{k}.csv | {v[0]} |" for k, v in csvs.items()) + "\n"
open(os.path.join(HERE, "test-data-table.md"), "w", encoding="utf-8").write(lib)
print("total cases", total, counts)
```

### 7.6 Playwright project files (generated by `gen_pw.py`)
The project lives in `pw/`. Key files: `playwright.config.ts`, `src/config/index.ts`, `src/pages/LoginPage.ts`, `src/pages/DashboardPage.ts`, `src/modules/LoginModule.ts`, `src/fixtures/index.ts`, and 50 specs in `src/tests/auth/`. They are produced by `gen_pw.py` above, so that script is the source of truth.


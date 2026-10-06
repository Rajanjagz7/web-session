# Fieldr Security and API Test Report

**Target:** `rajanjagz7.dev.fieldr.app` (owner-authorised dev tenant), tested 2026-09-19
**Method:** authenticated, in-session API testing through the app's own REST endpoints (`/api/v1`) plus UI walkthroughs.
**Not executed by design:** brute force, rate-limit flooding, DoS, broad path scanning, cross-tenant access, stored-XSS payloads.
Every "Actual Result" below was observed in this run. Anything not observed is listed under "Not verified".

## 1. Summary

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

## 2. Findings

### F1. Client-controlled invoice payment fields (High)
- **Actual Result:** `PUT /api/v1/invoice/update/:id` with `{status:"Paid", amountPaid:518.76, amountDue:0, payments:[{...}]}` returned `200 "Data updated successfully"` and persisted all fields. The UI's `actions` flags for a "Sent" invoice showed `canRecordPayment: false`, yet the API accepted a payment.
- **Impact:** any user with invoice edit access can mark invoices paid or alter totals without a payment record. Affects revenue reporting and Xero sync.
- **Evidence:** dashboard "Revenue this week" rose to $63,764.41 from API-only updates. [Screenshot: dashboard-revenue.png]
- **Suggested Fix Direction:** invoice update controller and its schema: whitelist editable fields, derive `amountPaid`/`amountDue` from a payments sub-resource, enforce a status state machine (Draft, Awaiting Approval, Awaiting Payment, Paid).

### F2. No enum validation on status/type fields (Medium)
- **Actual Result:** invoice status accepted `Sent`, `Approved`, `Submitted`, `Pending Approval` (the UI filter options are only `Draft`, `Awaiting Approval`, `Awaiting Payment`, `Paid`). Job report `Rejected`/`Approved` accepted. Item `lineType` accepted `labour`, `Labour`, `service`, `material`. Invoices with unknown statuses vanished from the dashboard "Invoice Status" chart.
- **Impact:** invalid states create records that do not appear in reports and are hard to find.
- **Suggested Fix Direction:** enum validators in the invoice, job report and item schemas.

### F3. Validation errors surface as 500 with internal detail (Medium)
- **Actual Result:** `POST /cms/create` `{title}` returned `500 "cms validation failed: content: Path 'content' is required., type: Path 'type' is required."`; a wrong `type` returned `500 "... is not a valid enum value for path 'type'"`. `PUT /quote/update` with a bad section returned `500 "Cast to embedded failed for value ..."` echoing request data. `POST /template/add` `{}` returned `500 "template validation failed: title..."`. `PUT /job/update` with a string for `startDateAndTime` returned `500 "Cast to Number failed ..."`.
- **Impact:** discloses schema field names and enum handling; 500s inflate error monitoring.
- **Suggested Fix Direction:** shared error middleware mapping Mongoose `ValidationError`/`CastError` to 400 with a generic message.

### F4. `timelog/create` reports success but stores nothing (Medium)
- **Actual Result:** 4 different payloads, including `{}`, all returned `200 {"message":"Data created successfully","data":null}`. `GET /timelog/list` stayed at `totalCount: 0`.
- **Impact:** clients cannot detect failure; timesheets cannot be seeded or tested through the API.
- **Suggested Fix Direction:** timelog controller: validate the body and return 400 on missing `jobId` or times; return the created document.

### F5. Users over the seat limit are created but invisible (Medium)
- **Actual Result:** `POST /user/create` returned 200 for 5 users on a plan with 1 seat; `GET /user/list` and the Users page show "No users found". Creating through the UI form redirected to Settings > Subscription.
- **Update (end of session):** after the subscription page showed 101 seats, `POST /user/create` for a new user (Zoe Barker) again returned 200 and `GET /user/list` still returned `totalCount: 0`. So missing seats are not the only reason: the API creates a record the list endpoint never returns, most likely because fields the UI form sends (for example workspace or user type) are absent from the API payload. The API accepts the incomplete record without an error.
- **Impact:** orphaned user records (invites and SMS may still be sent), and no error tells the caller the user is unusable.
- **Suggested Fix Direction:** user-create service: reject bodies missing the fields the list query depends on, and return 403 with a `planLimitReached` reason on seat overflow, as the job endpoint does. Next step for testers: capture the UI form's `POST /user/create` body and diff it with the API payload.

### F6. Mobile numbers disclose existence in other tenants (Medium)
- **Actual Result:** `customer/create` returned `409 "This mobile number is already registered"` and later `400 "This mobile number already belongs to another account..."`. `user/create` returned `400 "This mobile number is already registered"` for two numbers that this tenant had never used.
- **Impact:** any tenant user can test whether a number holds an account elsewhere.
- **Not verified:** whether the login endpoint itself discloses registration (cases FLD-AUTH-026 and 035 record its behaviour).
- **Suggested Fix Direction:** customer and user create services: report uniqueness only within the caller's workspace.

### F7. OTP target shows a leading zero after +61 (Medium, needs confirmation)
- **Actual Result:** after entering `0444124222`, the OTP step reads "We sent a 6-digit OTP to +610444124222". E.164 for that number is `+61444124222`. Customer records store `phone` without the leading 0.
- **Impact:** if the SMS gateway receives the display value, delivery may fail or go to the wrong number. Delivery was not verified (bypass OTP in use).
- **Suggested Fix Direction:** login/OTP controller: strip the national trunk `0` before composing E.164.

### F8. State machine bypass on job create (Low)
- **Actual Result:** `POST /job/create` with `status:"Completed"` or `"Cancelled"` was accepted and counted on the dashboard.
- **Suggested Fix Direction:** ignore or reject `status` on create.

### F9. Version disclosure in headers (Low)
- **Actual Result:** responses carried `server: nginx/1.28.3 (Ubuntu)` and `x-powered-by: Express`. `strict-transport-security` is present (good).
- **Suggested Fix Direction:** nginx `server_tokens off`; `app.disable('x-powered-by')`.

### F10. Auto-reload and lost input (Medium)
- **Actual Result:** while a form or dialog was open the page reloaded (a `version.json` request preceded each reload) and the form closed. Filling the Add User email produced `zoe.bark` instead of the full address, and a customer description saved as `Q`.
- **Impact:** data loss for real users during deploys.
- **Suggested Fix Direction:** defer the version-check reload until no form is dirty; prompt instead.

### F11. Unknown page URLs redirect to the Dashboard instead of showing "Not found" (Medium)
- **Steps:** 1. Log in. 2. Open `https://rajanjagz7.dev.fieldr.app/app/global-settings/payment-cards`. 3. Open `https://rajanjagz7.dev.fieldr.app/app/this-page-does-not-exist`.
- **Actual Result:** both pages ended on `/app/dashboard` with the Dashboard heading. No 404 page, no toast, no message. In contrast `GET /api/v1/does-not-exist` returns `404 {"success":false,"message":"API endpoint doesn't exist"}`.
- **Expected Result:** a "Page not found" screen (or a clear message) that keeps the wrong URL visible.
- **Impact:** users and testers cannot tell a mistyped or removed link from a working page. During this run it hid a wrong Payment Cards URL (the correct one is `/app/global-settings/billing/cards`) and made broken deep links look like they worked. It also masks routing regressions in automated tests, because a wrong route "passes" by landing on a valid page.
- **Frequency:** every unknown `/app/*` URL tested (2 of 2).
- **Evidence:** [Screenshot: unknown-route-redirect.png]; observed URL after load: `/app/dashboard`.
- **Suggested Fix Direction:** client router catch-all route: render a NotFound component instead of `Navigate to="/app/dashboard"`.

### F12. Unexpected redirects during work (Medium)
- **Actual Result:** (a) opening Add User and pressing Save redirected to Settings > Subscription, with no message explaining the seat limit; (b) several times the page navigated to the Dashboard or another route while a script or form was in use (for example after a subscription checkout the dialog closed and the app landed on `/app/dashboard`); (c) an `Execution context was destroyed` navigation happened during long-running calls on the Customer and Invoice pages.
- **Impact:** users lose place and unsaved input; the reason for the redirect is not shown.
- **Suggested Fix Direction:** show an explicit "Seat limit reached, add a seat" message before redirecting; avoid automatic navigation while a form is dirty.

## 3. API test results (observed)

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

## 4. Not verified
- Session cookie flags (`HttpOnly`, `Secure`, `SameSite`): the cookie value is visible to DevTools but the flags were not read.
- CSRF protection, IDOR across workspaces (single tenant only), OTP rate limiting and lockout, OTP expiry and replay (bypass OTP is static), idle timeout.
- Whether the login endpoint discloses if a mobile or email is registered.
- Invoice `tax`/`taxRate` per line was supplied by the client at 10; whether the server accepts 0 was not tested.

## 5. Test data footprint (for cleanup)
Probe records to delete: jobs "Probe", "Plan-limit check - Basic", "Status probe - In Progress"; one empty draft invoice; quote "QA probe quote (sections-items)"; CMS entry "enum probe"; the duplicate FAQ "How do I book a callout in NSW?"; six invisible API-created users (Liam Fraser, Charlotte Mitchell, Hamish Sutherland, Tahlia Kaur, Kai Papadopoulos, Zoe Barker).

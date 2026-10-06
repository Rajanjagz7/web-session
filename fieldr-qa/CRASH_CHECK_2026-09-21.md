# Fieldr Crash Check (whole-page walk)

**Target:** `rajanjagz7.dev.fieldr.app` (dev tenant), tested 2026-09-21 with headless Chromium (Playwright 1.63)
**Deployed build at test time:** `version.json` -> `releaseId local-b1475fbc`, `builtAt 2026-09-21T07:20:06Z`, `buildNumber "local"`. This is newer than the 2026-09-19 build the earlier reports describe.
**Data created:** none. Customer count stayed 101, job count 277.
**Note on a prior report:** the Sep 19 reports do not contain an item called "crash". The closest items are F10, F11 and F12 in `SECURITY_API_TEST_REPORT.md`.

## 1. Summary

| # | Finding | Severity | Type |
|---|---|---|---|
| C1 | `/login` intermittently stays on the Fieldr loading splash forever (no form, no error, no console error) | High | Crash-like / availability |
| C2 | Add Customer: Save does nothing when the required Description (Notes section, below the fold) is empty; the error is off-screen and the page does not scroll to it | Medium | Validation UX |
| C3 | Add Quote and Add Job: Save on an empty form shows no inline error and does not navigate (needs confirmation, see C3 below) | Medium (needs confirmation) | Validation UX |
| C4 | `send-otp` returns 502 with a raw `twilioError` object once Twilio blocks the number | Medium | Info disclosure / error handling |
| C5 | QA bypass OTP cannot be used while Twilio blocks the number, because `send-otp` must succeed first | Medium | Testability |
| C6 | Rapid page loads return HTTP 429 on `POST user/login/client-user` and `GET settings/effective`; the app shows no message | Low | Rate limiting UX |
| C7 | Mobile field keeps the trunk zero after +61: `+61 (04) 7634 2030` | Medium (same cause as F7) | Data handling |
| C8 | Job Report: the Add Report dialog appears to stay open after leaving the page (later page heading read "Add Report") | Low (needs confirmation) | Functional |

Positive result: every page and form listed in section 3 loaded with no blank screen, no error text, no `pageerror` and no failed API call.

## 2. Findings

### C1. Login page stuck on the loading splash (High)
- **Steps:** 1. Open `https://rajanjagz7.dev.fieldr.app/login`. 2. Wait 6 to 15 seconds.
- **Actual Result:** only the round Fieldr "f" logo shows. `body.innerText` is empty. No console error and no failed request. After `GET /version.json` returns 200 the app never calls `auth/is-logged-in`, so the login form never renders. The main frame also navigates twice during startup, meaning the page reloads itself once.
- **Frequency:** about 5 of 9 loads in the first run, 3 of 4 in a later run, 2 to 3 blanks before render in the last runs. Reloading usually fixes it.
- **Expected Result:** the login form renders, or a visible error with a retry.
- **Impact:** users cannot sign in on that load and see no explanation. Automated tests fail intermittently.
- **Not verified:** the cause. It may relate to the auto-reload in F10 (`version.json` check) or to the newer build. Tested in headless Chromium only.
- **Suggested Fix Direction:** startup/bootstrap code that runs after the version check: make sure the reload does not interrupt the auth check, and add a timeout with an error state on the splash.

### C2. Add Customer Save silently does nothing (Medium)
- **Steps:** 1. Log in. 2. Customer, then Add (`/app/customer/new`). 3. Enter First Name "Quinn", any Last Name, an AU mobile, a yopmail email, and pick "12 Macquarie St, Sydney NSW 2000" from the address suggestions. 4. Click Save.
- **Actual Result:** no request is sent, no toast, the URL stays `/app/customer/new`. The required **Description** field (Notes section) is empty and its error "Please enter a valid description" is below the visible area.
- **Expected Result:** scroll to and focus the first invalid field, or show a summary message.
- **Also seen:** first name shorter than 3 characters shows "First name must be between 3 to 35 characters".
- **Suggested Fix Direction:** customer form submit handler: scroll the first error into view.

### C3. Quote and Job empty Save (needs confirmation)
- **Steps:** 1. Open Quote (or Job), then Add (`/app/quote/new`, `/app/job/new`). 2. Click Save with nothing filled.
- **Actual Result:** no inline error text was found by the script and the URL did not change. Whether a request was sent was not captured.
- **Expected Result:** visible validation, as on Customer, Item, Feed and CMS.
- **Needs confirmation:** repeat manually and watch the network tab.

### C4 and C5. Twilio block leaks and blocks the bypass (Medium)
- **Steps:** request an OTP for the same mobile number many times in a short period.
- **Actual Result:** `POST /api/v1/auth/send-otp` returned `502 {"success":false,"statusCode":502,"message":"Having OTP issue from Twilio side, try after some time","data":{"twilioError":{"message":"The destination phone number has been temporarily blocked by Twil..."}}}`.
- **Impact:** third-party error detail is returned to the browser, and the static bypass OTP is unusable while the block lasts.
- **Cause in this run:** repeated test logins for `+61444124222` on 2026-09-21 triggered the block. Email login was used instead.
- **Suggested Fix Direction:** auth controller: map Twilio errors to a generic message; let the QA bypass skip the SMS send.

### C6. HTTP 429 on page-load calls (Low)
- **Actual Result:** after about 50 quick full page loads, `POST user/login/client-user` and `GET settings/effective` returned 429. Pages still rendered and no message was shown.

### C7. Trunk zero kept in the mobile field (Medium)
- **Actual Result:** typing `0476342030` displays `+61 (04) 7634 2030`; the OTP screen also showed `+610444124222` (F7).

### C8. Job Report Add Report dialog (needs confirmation)
- **Actual Result:** after opening Add Report on the Job Report page and navigating on, the next pages still reported the heading "Add Report". This could be a stale dialog or a script artifact.

## 3. Coverage

Login used the email path (`rajanjagz7@yopmail.com` plus the bypass OTP) because the SMS path was blocked.

| Area | Result |
|---|---|
| Sidebar pages (17): Dashboard, Schedule, User, Customer, Quote, Job, Timesheet, Job Report, Invoices, Items, Insights, Activity Logs, Chat, Feed, CMS, Settings, Notifications | All loaded, scrolled to the bottom, no blank or error |
| Add forms (8): Customer, Quote, Job, Job Report, Item, Feed post, CMS | All opened. Empty Save gave inline errors on Customer, Item, Feed, CMS (see C3 for Quote and Job) |
| Settings tabs (10): Company Settings, Roles & Permissions, Shifts & Breaks, Integrations, Checklists, Holidays, Report Builder, My Subscription, Payment Cards, Purchase History | All loaded |
| Record detail: first record of User, Customer, Quote, Job, Timesheet, Job Report, Invoices, Items, CMS | Clicked with no crash, error or failed API call. Most open as a panel over the list with the URL unchanged, CMS opens `/app/cms/edit/<id>`. The panel content was not captured |

New since 2026-09-19: sidebar items **Chat** (`/app/chat`) and **Feed** (`/app/feed/list`), and a Feed "Create Post" form.

## 4. Flow run: creating records through the UI (2026-09-21, second session)

The top-bar **Create** menu lists 9 entries: New Job, New Customer, New User, New Quote, New Invoice, New Item, New CMS, New Post, New Report. Each was opened from the menu. One record was created per flow, named "QA Crashcheck <number>" or "Quinn Crashcheck<number>" so they can be found and deleted.

| Flow | Result | Evidence |
|---|---|---|
| New Customer | Created, redirected to `/app/customer/list`, toast "Customer successfully added" | `200 POST customer/create` (works once Description is filled, which confirms C2) |
| New Item | Created (after filling the required Unit and Item Description) | `200 POST item/create` |
| New Post (Feed) | Created | `200 POST feed/create` |
| New CMS (type FAQ) | Created after filling Title, Question and Answer. The FAQ type swaps the Content field for Question and Answer | `200 POST cms/create` |
| New Invoice | Created (customer, Invoice Date, Due Date, one item with qty 2, total $20.00) | `200 POST invoice/create` |
| New Job (5-step wizard: Job Details, Team, Checklists, Reports, Review & Save) | Created; button on the last step is "Create Job"; redirected to `/app/job/view/<id>` | `200 POST job/create` |
| New User | Created (Industry "Agriculture", Role "User"). On 2026-09-19 the same Save redirected to Settings > Subscription (F12); this time it saved | `200 POST user/create` |
| New Quote | **Not completed.** Reached the Sections tab (needs Section Name, Item, Description, Unit, Qty, Rate; each shows an inline error). Automation could not pick the item, so Save sent nothing | no request |
| New Report | **Not completed.** The Job dropdown lists `JOB-0278 - <title>`; Type stays disabled until a job is chosen | no request |

Extra observations from this session:
- **C9. Page content lags the URL (Low).** After choosing a Create entry the URL changes at once, but the previous page's content stays for 2 to 5 seconds (Quote about 5 s, Invoice about 2 to 4 s). Users see the old page under the new URL.
- **C10. OTP throttling covers email too (Medium).** After many test logins, `send-otp` for the email address returned `429 {"message":"Too many OTP requests. Please try again after some time.","data":{"twilioError":{"message":"Max send attempts reached","code":60203,...}}}`. The raw Twilio error is returned to the browser again (see C4).
- **C11. Leave-page prompt on the Quote form.** Leaving the half-filled Add Quote page raised a "saved changes that will be lost" prompt. This is expected behaviour, noted because it blocks navigation.
- The login blank splash (C1) appeared again on nearly every run, usually 1 to 3 times before the form rendered.

## 5. Not covered / still to do
- Add Quote and Add Report: finish creating one each (blocked by the OTP limit at the time of writing).
- Feed and Report Builder record details; the Report Builder drag-and-drop editor.
- Chat (sending a message), Schedule and the 18 Insights reports beyond loading them.
- Real browsers other than headless Chromium; mobile viewports.
- Records created by this run are still in the tenant and can be deleted: 1 customer, 1 item, 1 feed post, 1 CMS entry, 1 invoice, 1 job (JOB-0278), 1 user.

# Fieldr Remaining-Flows Walkthrough and Data Report

**Target:** `rajanjagz7.dev.fieldr.app` (dev tenant), run 2026-09-21 in headless Chromium (Playwright 1.63).
**Method:** one email OTP login, session saved and reused (no further OTP requests). Data was added through the UI where the form could be automated, and through the app's own API (`quote/create`) where the UI form could not.
**Earlier reports:** Saturday's seeding and findings are in `HANDOVER.md` and `SECURITY_API_TEST_REPORT.md`. The crash check is in `CRASH_CHECK_2026-09-21.md`.

## 1. Summary

- 7 create flows work end to end through the UI: Customer, Item, Feed post, CMS (FAQ), Invoice, Job (5-step wizard) and User.
- Quote was created through the API. The UI Add Quote form could not be completed by automation (see 3.2).
- All 18 Insights reports, Chat, Schedule, Timesheet and the Report Builder editor were walked through with no crash and no failed API call.
- Timesheets and crew cannot be seeded: there is no add flow in the web app, and `timelog/create` stores nothing (F4).
- New finding this session: the login page still intermittently sticks on the loading splash (C1).

## 2. Data state

Baseline is the table from Saturday's session. "Now" is `totalCount` from the app's list endpoints at the end of this run.

| Data | Saturday | Now | Added by this run |
|---|---|---|---|
| Customers | 101 | 102 | 1 (UI) |
| Items | 100 | 101 | 1 (UI) |
| Quotes | 101 | 102 | 1 (API) |
| Invoices | 180 | 183 | 1 (UI); the other 2 were not created by a flow I ran |
| Jobs | 277 | 278 | 1 (UI, JOB-0278) |
| Job Reports | 375 | 555 | 0 by a deliberate flow. The increase of 180 is unexplained and needs checking |
| Feed posts | 0 | 2 | 2 (UI) |
| Users | 0 | 2 | 2 (UI) |
| CMS entries | 40 | 43 | 1 (UI) |
| Holidays / Checklists / Report templates / Quote formulas | 27 / 3 / 3 / 6 | 27 / 3 / 3 / 6 | 0 (plan limits reached for checklists and templates) |
| Timelogs | 0 | 0 | 0 (see 4) |

All new records are named "QA Crashcheck ..." or "Quinn Crashcheck/Crashuser ..." so they are easy to find and delete.

## 3. Flow results

### 3.1 Create flows (top-bar Create menu: 9 entries)

| Flow | Result | Evidence |
|---|---|---|
| New Customer | Created | `200 POST customer/create`. Required: First Name (3 to 35 chars), Last Name, Mobile, Email, Address (pick from suggestions), Description (in the Notes section, below the fold) |
| New Item | Created | `200 POST item/create`. Required: Item Name, Unit, Sell Price, Item Description |
| New Post | Created | `200 POST feed/create` (twice) |
| New CMS | Created (type FAQ) | `200 POST cms/create`. The FAQ type swaps Content for Question and Answer |
| New Invoice | Created | `200 POST invoice/create`. Customer, Invoice Date, Due Date, one item (qty 2, total $20.00) |
| New Job | Created | `200 POST job/create`. Steps: Job Details, Team, Checklists, Reports, Review & Save; the last button is "Create Job" |
| New User | Created (twice) | `200 POST user/create`. On 2026-09-19 the same Save redirected to Settings > Subscription (F12) because of the seat limit. Both new users now appear in the list |
| New Quote | Created via API | `POST quote/create` returned 200 with the same payload shape as Saturday's `fieldr_seed.py` |
| New Report | Not completed | See 3.2 |

### 3.2 Not completed through the UI (automation limits, not confirmed bugs)
- **Add Quote:** the Sections tab needs a section name, an item, description, unit, quantity and rate. The item dropdown is a hidden react-select input that my automation could not open reliably, so Save was never reached.
- **Add Report:** Job and Type dropdowns work (Job list shows `JOB-0278 - <title> [status] #id`), but Save stayed disabled (`aria-disabled`) and the flow timed out. Job reports already exist (555), so no data gap remains.

### 3.3 Walkthrough of the other modules

| Module | Result |
|---|---|
| **Insights** (18 reports) | All 18 opened at `/app/insights/<report>` with real content and no failed API call: job-status-breakdown, overdue-jobs, jobs-by-customer-location, average-job-duration, job-task-throughput, invoice-status-breakdown, revenue-trend, outstanding-invoices-ageing, quote-pipeline, revenue-by-customer, hours-worked-summary, normal-vs-overtime-hours, weekend-holiday-hours, labour-hours-per-job, timesheet-edits-audit, report-submission-compliance, report-approval-turnaround, checklist-completion. The 5 hours/timesheet reports have little content (about 200 characters), as expected with no timelogs |
| **Chat** | Opened a job conversation, typed a message and it appeared in the thread |
| **Schedule** | Loads. No event could be located and clicked, so event interaction is not verified |
| **Timesheet** | Loads with Export, Users, Roles, Filters, week navigation. No Add button: entries come from mobile clock-on |
| **Report Builder editor** | Textbox, Dropdown and Date dropped onto the canvas with real mouse drags. Save returned `403 POST template/add` and the app showed a clear "You have reached your plan limit ... You are using 3 of 3" dialog. Correct behaviour |

## 4. Blockers for data seeding
- **Timesheets, crew, clock-on data:** need the mobile clock-on payload. `POST /timelog/create` returns 200 "Data created successfully" with `data: null` and stores nothing (F4).
- **Checklists and report templates:** Basic plan maximum (3 each) already reached.
- **Seats:** the plan page shows extra seats; users created through the UI now save.

## 5. Findings from this session

| # | Finding | Severity |
|---|---|---|
| C1 | `/login` and `/app/dashboard` intermittently stay on the loading splash with no form, no error and no console error (1 to 6 attempts needed on every run; six in a row once) | High |
| C2 | Add Customer Save does nothing when the required Description is empty; the error is below the fold and the page does not scroll to it | Medium |
| C9 | After choosing a Create entry the URL changes at once but the previous page's content stays for 2 to 5 seconds | Low |
| C10 | OTP throttling applies to email logins as well as SMS. `send-otp` returned `429 "Too many OTP requests"` with the raw Twilio error (code 60203) in the response | Medium |
| C4 | Twilio errors are returned to the browser in `data.twilioError` (also seen as 502 for the SMS path) | Medium |
| F4 | `timelog/create` reports success and stores nothing (unchanged since Saturday) | Medium |

Positive results: plan-limit dialog on templates; job cap and seat handling work; all 18 Insights reports render; Chat sends messages.

## 6. Test-run side effect (caused by testing)
Roughly 25 automated logins today triggered Twilio limits on `+61444124222` (SMS blocked) and later on the email OTP path (429). This cleared before the final run. The saved session is stored only in the scratchpad and should not be shared. Avoid repeated logins; reuse a saved session for future runs.

## 7. Not covered / next steps
- Add Quote and Add Report through the UI (dropdown automation).
- Schedule event interaction (open, drag, reassign).
- Report Builder: saving a template needs a plan upgrade or deleting an existing template.
- Timesheets and crew: need the mobile clock-on API payload.
- The unexplained +180 job reports and +2 invoices since Saturday.
- Playwright auth suite (`pw/`) not run, because each test requests an OTP and would re-trigger throttling.
- Cleanup: the "QA Crashcheck ..." records above can be deleted from the app.

# Fieldr Timesheet and Job Report Data (2026-09-21)

**Target:** `rajanjagz7.dev.fieldr.app` (dev tenant). Data was created through the app's own API from a logged-in session.
**Scripts (re-runnable, need `FLDR_COOKIE`):** `fieldr_timesheets.py`, `fieldr_job_reports.py` in this folder, alongside `fieldr_seed.py`.

## 1. Result

| Page | Before | Now |
|---|---|---|
| Job Report | empty ("No data found") | **61 reports**: REPORT-0001 to REPORT-0061, 3 templates, 30 Submitted, 21 Approved, 10 Rejected |
| Timesheet | 0h for every user, every day | **3 users, 3 weeks**, 22 to 52 hours per user per week, with paid breaks, overtime days and one weekend shift |

Both pages were opened in the UI after seeding: the Job Report list shows the new rows and the Timesheet grid shows hours per day for weeks of 7, 14 and 21 September. No page errors.

## 2. Why both pages were empty (corrections to the Saturday reports)

1. **Job Report page lists submissions, not job reports.** It calls `GET /job/report/submission/list`. Saturday's 555 records were `job/report` records (report templates attached to jobs), so the page stayed empty. A submission is created with `POST /job/report/submission/submit` `{jobId, jobReportId, fields, reportDate}`.
2. **Saturday's report fields did not match the app's own schema.** The Report Builder saves fields as `{id, name, type, value, label, position, placeholder, options (strings), validation:{mandatory}}` with types `text, dropdown, radio, checkbox, textarea, number, file, email, date, sign, items`. The seeded fields used `type: "textbox"`, `required`, no `id`, and `{label,value}` options. All 3 templates and all 554 job reports were converted to the native schema (554 of 554 succeeded).
3. **Timesheets can be seeded.** F4 in the Saturday report ("timelog/create stores nothing, timesheets cannot be seeded") was the wrong endpoint. The web timesheet screen uses `POST /timelog/edit-log` with `{data:[{type, jobId, userId, startDateAndTime, endDateAndTime, isTimeLogDone, isDeleted, reason, createdAt}]}`, times in milliseconds. `timelog/create` remains a silent no-op (F4 still stands for that endpoint).

## 3. Data added

### Job reports
- 60 new submissions on 60 different jobs (In Progress), 20 per template (Site Safety Inspection, Electrical Job Completion, Plumbing Compliance), report dates spread from 1 to 20 September. Every submission carries the job report's filled field values (addresses, licence numbers, Yes/No answers).
- Statuses set through `PUT /job/report/submission/status/:id`: 21 Approved, 10 Rejected (with a reason such as "Missing photo of completed work; please resubmit."), 30 Submitted. The reject reason key is `statusReason`.

### Timesheets
- Users: Quinn Crashuser587052, Quinn Crashuser342075, rajan Jagzz.
- Days: Monday to Friday of 7 and 14 September, a Saturday shift for one user (weekend hours), and today for the admin. The admin has a few days off.
- Each day: a morning work log, a 60 minute break, an afternoon work log, on real In Progress jobs. Some days start at 06:30 for overtime. Times are AEST.
- Weekly hours per user: week of 7 Sep 52.0 / 52.0 / 32.5, week of 14 Sep 40.0 / 48.5 / 32.5, week of 21 Sep 7.0 / 4.0 / 7.5 (Quinn 587052 / Quinn 342075 / rajan Jagzz).

## 4. Data quality caveats
- **Two days are inflated by my test logs.** Quinn Crashuser587052 shows 20h 30m on Tue 8 Sep, and Quinn Crashuser342075 shows 12h on Sat 12 Sep. They came from probe calls made while learning the API. Individual logs could not be removed (the worklogs endpoint timed out on guessed parameters), so edit or delete them in the Timesheet screen if needed.
- Today (21 Sep) shows 7h, 4h and 7.5h from probe and seed logs.
- I did not open a single submission's detail view (the row action menu did not open in automation), so how the converted fields render in the detail screen is not verified beyond the list.
- Records are fictional and can be deleted.

## 5. New findings from this work

| # | Finding | Severity |
|---|---|---|
| T1 | `POST /timelog/edit-log` returns **HTTP 500 "BREAK_NOT_ALLOWED"** for a business rule (a break that is not exactly the configured 60 minute paid break). Should be a 4xx with a readable message | Medium |
| T2 | `edit-log` is **not atomic**: when a break in the batch is rejected, the earlier work logs in the same request are already saved. A 500 response still changed data | High |
| T3 | `edit-log` and `timelog/create` return 200 "Data created/updated successfully" with `data: null`, so the caller cannot tell what was stored | Low |
| T4 | `GET /timelog/get/worklogs` with unexpected parameters hangs until the client times out (30 s) instead of returning 400 | Medium |
| J1 | Rejecting a submission needs the undocumented key `statusReason`; other keys return 400 "Please give a reason for rejecting this report." | Low |
| J2 | Job Report page and the seeded `job/report` API list different collections (submissions vs template-attached reports), which is confusing for API users and testers | Low |
| J3 | Report Builder and job reports accept fields that do not follow the native schema (no `id`, `type: "textbox"`) without any validation | Medium |

## 6. Not done / next steps
- Individual submission detail view and editing not exercised in the UI.
- Removing the stray probe logs on 8 Sep and 12 Sep.
- Crew and groups were not seeded.
- The 61 submissions are all dated 21 September as "created", with report dates spread over September.

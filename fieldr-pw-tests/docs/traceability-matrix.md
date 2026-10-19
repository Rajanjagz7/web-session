# Traceability matrix: FieldR release notes (Production, 6 October 2026)

**98 release-note bullets, 98 IDs** (one owner ID per bullet): 45 live, 25 partial (live test with a named gap), 24 stub (`test.fixme` naming the missing prerequisite), 4 manual.

Type: UI | API | PERM (permission/negative) | PDF | a11y | MAN. Priority: P1 critical path, P2 core feature, P3 polish, P4 cosmetic. Every title in `src/specs` starts with its ID (`[QUO-01] @quotes @cost-viewer ...`).

| ID | Area | Bullet (paraphrased) | Type | Priority | Spec file | Status |
| --- | --- | --- | --- | --- | --- | --- |
| QUO-01 | Quotes | Quote formula columns can use Cost Price, Margin % and Markup % | UI | P1 | quotes.spec.ts | partial: the exact margin/markup values (definition on sell vs on cost) are not in the notes |
| QUO-02 | Quotes | Columns using cost/margin/markup are internal only; never shown to customers; "Show to Customer" locked off | PERM | P1 | quotes.spec.ts | live |
| QUO-03 | Quotes | A line with no cost price shows a dash instead of 0 in cost/margin/markup columns | UI | P2 | quotes.spec.ts | live |
| QUO-04 | Quotes | Quote list has a new "Created By" column | UI | P3 | quotes.spec.ts | partial: the creator-name cell needs a stable locator (test-id) |
| JB-01 | Job Budget | Each budget line has a sell price and a cost price; both auto-fill when a catalogue item is picked | UI | P2 | jobBudget.spec.ts | partial: needs at least one catalogue item (FIXTURE_CATALOGUE_ITEM_EXISTS) and a test-id for the new line |
| JB-02 | Job Budget | Line total = quantity x sell price; editor shows job budget and cost budget totals | UI | P2 | jobBudget.spec.ts | live |
| JB-03 | Job Budget | Prices are only visible to people allowed to see cost prices | PERM | P1 | jobBudget.spec.ts | live |
| JB-04 | Job Budget | New Job Budget tile shows how much is left after costs so far, or how far costs have gone over | UI | P2 | jobBudget.spec.ts | partial: the expected remaining amount is not stated; tile visibility only |
| CP-01 | Customer Portal | Portal quote list has a Job column showing the job name, job number on hover | UI | P2 | portal.spec.ts | partial: the hover tooltip needs a seeded converted quote for the portal customer |
| CP-02 | Customer Portal | Quotes that became jobs say "Converted to Job" instead of "Accepted" in the badge and the status filter | UI | P2 | portal.spec.ts | partial: asserting a converted row needs a seeded converted quote; filter option is live |
| CP-03 | Customer Portal | If portal access is removed while logged in, customer sees "You no longer have access to the customer portal" | UI | P1 | portal.spec.ts | stub: needs a dedicated portal login whose access can be revoked mid-session (the shared portal-customer persona must not be broken) and the revoke endpoint |
| CP-04 | Customer Portal | Customers can download the worklog report for their own jobs | API | P2 | portal.spec.ts | partial: needs PORTAL_CUSTOMER_ID; the report format (PDF/CSV) is unconfirmed |
| SC-01 | Schedule | Schedule header has Add Shift and Add User buttons; Add Shift opens on today 9am-5pm | UI | P2 | schedule-roles.spec.ts | live |
| SC-02 | Schedule | Add User opens a quick popup without leaving the Schedule | UI | P2 | schedule-roles.spec.ts | live |
| SC-03 | Schedule | After saving the new person, Add Shift opens for today 9am-5pm with them already in the team | UI | P2 | schedule-roles.spec.ts | live |
| RO-01 | Roles | New Role is in the Create menu and command palette only if the plan has custom roles and the user can manage roles | PERM | P1 | schedule-roles.spec.ts | live |
| RO-02 | Roles | Job Team step: "+" next to Assign By Role creates a new role with the same access as an existing one | UI | P2 | schedule-roles.spec.ts | live |
| RO-03 | Roles | The new role is selected straight away and adds nobody to the job | UI | P2 | schedule-roles.spec.ts | live |
| CU-01 | Customers | Customer Details has a Create Job button that opens New Job with that customer already picked | UI | P2 | customers-pickers.spec.ts | live |
| CU-02 | Customers | Create Job button is hidden for inactive customers and for people without job permission | PERM | P1 | customers-pickers.spec.ts | live |
| CU-03a | Customers | Company name first in customer lists and screens | UI | P2 | customers-pickers.spec.ts | live |
| CU-03b | Customers | Company name first in quote and invoice drawers | UI | P3 | customers-pickers.spec.ts | partial: the invoice drawer needs an invoice seed endpoint (quote drawer is live) |
| CU-03c | Customers | Company name first on the portal quote page | UI | P3 | portal.spec.ts | partial: needs PORTAL_COMPANY_NAME and PORTAL_CONTACT_NAME |
| CU-03d | Customers | Company name first in Send Contract and contract requests | UI | P3 | customers-pickers.spec.ts | stub: needs a contract-request seed endpoint and the contract screen locators |
| CU-03e | Customers | Company name first on portal access screens | UI | P2 | customers-pickers.spec.ts | live |
| CU-03f | Customers | Company name first in job exports and job reports | UI | P3 | customers-pickers.spec.ts | stub: export file format and column names are not in the release notes |
| CU-04 | Customers | Quote and invoice PDFs show the company in bold on the Bill To / For Services Rendered line with the contact underneath | PDF | P2 | customers-pickers.spec.ts | partial: bold weight is not readable from PDF text (visual baseline needed); invoice PDF needs a seed endpoint |
| CU-05 | Customers | Job PDF lists Company before Client | PDF | P3 | customers-pickers.spec.ts | live |
| CU-06 | Customers | Customers without a company print exactly as before | PDF | P3 | customers-pickers.spec.ts | partial: 'exactly as before' needs a golden baseline from the previous release |
| SUB-01 | Subscription & Billing | A cancelled subscription can be resumed before it ends | UI | P2 | subscription-billing.spec.ts | stub: needs a billing-sandbox company with a cancelled-but-not-ended subscription |
| SUB-02 | Subscription & Billing | Payment History shows whether each charge was monthly or yearly | UI | P2 | subscription-billing.spec.ts | stub: needs a billing sandbox with both a monthly and a yearly charge |
| SUB-03 | Subscription & Billing | The first invoice lists each add-on separately | UI | P2 | subscription-billing.spec.ts | stub: needs a billing sandbox company with a first invoice that includes add-ons |
| IPH-01 | iPhone App | Companies can sign up and pay through the App Store on iPhone | MAN | P2 | subscription-billing.spec.ts | manual: App Store / TestFlight device required |
| IPH-02 | iPhone App | App Store billing stays off until it is switched on | MAN | P2 | subscription-billing.spec.ts | manual: App Store build plus the feature flag state; also verify web flows unchanged with the flag off |
| IPH-03 | iPhone App | A company already paying by card is never charged twice | MAN | P2 | subscription-billing.spec.ts | manual: real payments on both rails; compare provider ledgers |
| LA-01 | Admin Log In As | A super admin logged in as a company admin can log in as one of that company's customers | PERM | P1 | misc-improvements.spec.ts | live |
| PICK-01 | Pickers | Job and Quote customer pickers show company in bold with contact underneath and a loading state | UI | P2 | customers-pickers.spec.ts | live |
| PICK-02 | Pickers | Pickers can be searched by company, name, email or Customer ID | UI | P2 | customers-pickers.spec.ts | partial: search by Customer ID needs the displayed customer number |
| PICK-03 | Pickers | Clearing a picker search brings back the full list | UI | P2 | customers-pickers.spec.ts | live |
| PICK-04 | Pickers | Long names in dropdowns are shortened neatly instead of breaking the layout | UI | P2 | customers-pickers.spec.ts | live |
| JOBS-01 | Jobs | New jobs start with a 1000 m site radius, including when a quote is converted to a job | UI | P3 | customers-pickers.spec.ts | partial: the quote-to-job conversion leg needs the conversion action locator |
| JOBS-02 | Jobs | Job description is optional when creating or editing a job | UI | P3 | customers-pickers.spec.ts | live |
| JOBS-03 | Jobs | Budget quantity tile is renamed "Lines Over Planned Qty", shows a count such as "2 of 5", with a caption | UI | P3 | jobBudget.spec.ts | live |
| JOBS-04 | Jobs | Inactive customers can no longer be given new jobs from the customer screen | PERM | P2 | customers-pickers.spec.ts | live |
| ORD-01 | Job Orders | "Phone" is renamed "Mobile Number" and "Site Contact" is renamed "Site Contact Name" | UI | P2 | misc-improvements.spec.ts | live |
| ORD-02 | Job Orders | The error message for an invalid number is clearer | UI | P3 | misc-improvements.spec.ts | stub: the new message wording is not in the release notes; set EXPECTED text then remove fixme |
| ORD-03 | Job Orders | Job order has an Add Line button and the page scrolls to the line just added | UI | P2 | misc-improvements.spec.ts | live |
| USR-01 | Users | Industry is optional on Add User, Edit User and My Profile | UI | P3 | misc-improvements.spec.ts | partial: the submit leg and the Edit User screen need the required-field list and a seeded user |
| USR-02 | Users | Picking a Google address fills Suburb, State and Postcode automatically | UI | P3 | misc-improvements.spec.ts | stub: needs Google Places responses stubbed with page.route or a live key; stub shape unconfirmed |
| USR-03 | Users | Roles & Permissions sorts correctly by role name and opens A-Z | UI | P2 | schedule-roles.spec.ts | live |
| DT-01 | Date & Time | Date-time picker offers 15-minute slots and scrolls to the current time when it opens | UI | P3 | misc-improvements.spec.ts | partial: slot label format and the scroll rounding rule are unconfirmed (clock is mocked) |
| PH-01 | Phone Numbers | Phone number formatting is the same across forms (sign-up, customer contracts, job orders) | UI | P3 | misc-improvements.spec.ts | partial: sign-up and contract forms are not covered; the exact format needs EXPECTED_PHONE_DISPLAY_FORMAT |
| INV-01 | Customer Invites | Customer invite details step asks company name, address (required) and notes; no staff fields (date of birth, licences) | UI | P2 | security-invites.spec.ts | live |
| INV-02 | Customer Invites | Opening a customer invite while signed in as staff no longer asks you to sign out | UI | P2 | security-invites.spec.ts | live |
| INV-03 | Customer Invites | A customer of another company can accept an invite using the mobile number already on their login | UI | P2 | security-invites.spec.ts | stub: needs a second company plus an invite link seeded for an existing portal login |
| INV-04 | Customer Invites | "Your sign-in email" now reads "Your registration email" | UI | P4 | security-invites.spec.ts | live |
| INV-05 | Customer Invites | The "waiting" count no longer shrinks while you search | UI | P3 | security-invites.spec.ts | live |
| INV-06 | Customer Invites | The invite dialog and its buttons are labelled for screen readers (axe check; full screen-reader pass is manual) | a11y | P3 | security-invites.spec.ts | partial: automated axe label checks only; full screen-reader behaviour is manual |
| INV-07 | Customer Invites | Inviting a customer's email as staff explains why instead of saying "already a member" | UI | P3 | security-invites.spec.ts | live |
| SUBS-01 | Subscription screens & Purchase History | Trial, cancellation and renewal status are clearer on Current Subscription, plan cards and the cancel card | UI | P3 | subscription-billing.spec.ts | stub: needs billing-sandbox companies in trial, cancelled and renewing states; expected wording unconfirmed |
| SUBS-02 | Subscription screens & Purchase History | A cancelled trial is shown separately from an active plan | UI | P3 | subscription-billing.spec.ts | stub: needs a billing-sandbox company with a cancelled trial |
| SUBS-03 | Subscription screens & Purchase History | Alert messages use the space better | UI | P4 | subscription-billing.spec.ts | stub: visual-layout change with no stated expectation; use a screenshot baseline once approved |
| SUBS-04 | Subscription screens & Purchase History | The onboarding fee is handled correctly for resumed subscriptions | UI | P3 | subscription-billing.spec.ts | stub: needs a billing sandbox resumed subscription and the expected fee amount |
| PDF-01 | PDFs | Order PDF shows the ABN properly formatted and has clearer labels | PDF | P2 | misc-improvements.spec.ts | partial: needs FIXTURE_ORDER_ID; the new label wording is not stated |
| PDF-02 | PDFs | Company ABN is formatted on reports too | PDF | P2 | misc-improvements.spec.ts | partial: needs FIXTURE_REPORT_ID |
| PDF-03 | PDFs | Timesheet PDFs no longer have blank pages | PDF | P2 | misc-improvements.spec.ts | live |
| INS-01 | Insights | Insights reports show the status, customer and worker filters they already supported | UI | P3 | misc-improvements.spec.ts | partial: report names are unconfirmed; only the first report is opened |
| INS-02 | Insights | Percentages on cards round the same way as in the table | UI | P3 | misc-improvements.spec.ts | partial: proxy check (same decimal places), not a per-metric equality |
| PA-01 | Platform Admin | The platform overview loads once (one request per data source) | UI | P3 | misc-improvements.spec.ts | live |
| PA-02 | Platform Admin | Year-to-date figures are correct around midnight | MAN | P2 | misc-improvements.spec.ts | manual: needs a wall-clock boundary: mock the clock (page.clock) at 23:59:50 on 31 Dec / 30 Jun, or run a scheduled job near the boundary |
| PA-03 | Platform Admin | Accounts list shows sorting and accounts with zero revenue, and tells you about the 200-row limit | UI | P3 | misc-improvements.spec.ts | partial: the 200-row notice needs an environment with 200+ accounts; seed a zero-revenue account |
| PA-04 | Platform Admin | Monthly revenue counts yearly plans, trials and one-off charges correctly | API | P2 | misc-improvements.spec.ts | stub: needs seeded revenue fixtures (yearly plan, trial, one-off) and the expected totals |
| PA-05 | Platform Admin | Role settings on the platform console only offer super-admin modules to the Super Admin role | PERM | P2 | misc-improvements.spec.ts | partial: the super-admin-only module names are not stated |
| SEC-01 | Security & Data Quality | Staff invites (send, view, resend, cancel) need user permission | PERM | P1 | security-invites.spec.ts | live |
| SEC-02 | Security & Data Quality | Customer invites (send, view, resend, cancel) need customer permission | PERM | P1 | security-invites.spec.ts | live |
| SEC-03 | Security & Data Quality | Invalid email addresses are refused for invites, users and customers | API | P1 | security-invites.spec.ts | live |
| SEC-04 | Security & Data Quality | Deleted users and customers can no longer be opened from an old link | API | P1 | security-invites.spec.ts | live |
| SEC-05 | Security & Data Quality | A company name must contain at least one letter | API | P1 | security-invites.spec.ts | live |
| SEC-06 | Security & Data Quality | Customer contacts can no longer change the company name | PERM | P1 | security-invites.spec.ts | live |
| SEC-07 | Security & Data Quality | Customers can only see time logs for their own jobs | PERM | P1 | security-invites.spec.ts | live |
| BUG-01 | Bug Fixes | Contracts: recipients who have signed no longer show "Opened: Not yet" or "Read: Not yet" | UI | P2 | bugs.spec.ts | stub: needs a contract with a signed recipient (signing link flow) seeded through the API |
| BUG-02 | Bug Fixes | Quotes: a new quote no longer keeps the section name and rows from the previous new quote | UI | P2 | bugs.spec.ts | live |
| BUG-03 | Bug Fixes | Defects: title and description changes are saved when you close the menu | UI | P2 | bugs.spec.ts | live |
| BUG-04 | Bug Fixes | Defects: the defect view shows the drawing with its markup, not the plain image | UI | P2 | bugs.spec.ts | stub: needs a defect with a drawing and markup seeded (file upload) and an image-diff baseline |
| BUG-05a | Bug Fixes | Jobs: editing a job budget no longer wipes the prices copied from the quote | UI | P1 | bugs.spec.ts | live |
| BUG-05b | Bug Fixes | Jobs: prices already wiped on existing jobs can be restored | UI | P2 | bugs.spec.ts | stub: needs a legacy job with wiped prices and the documented restore action |
| BUG-06 | Bug Fixes | Jobs: budget lines typed by hand on a quote match correctly in daily reports | UI | P2 | bugs.spec.ts | stub: needs a daily report seed that references a hand-typed quote line |
| BUG-07 | Bug Fixes | Customer Portal: the "Device id is required" error on portal login is fixed | UI | P1 | bugs.spec.ts | live |
| BUG-08 | Bug Fixes | Plan checks now handle customer portal logins correctly | UI | P2 | bugs.spec.ts | stub: needs a plan-limited company and the plan-check endpoint that portal logins hit |
| BUG-09a | Bug Fixes | Invites: a refused customer invite shows an error instead of hanging | UI | P3 | bugs.spec.ts | stub: needs a precondition that makes the server refuse the invite (rule unknown) |
| BUG-09b | Bug Fixes | Invites: a missing email gives a clear error | UI | P3 | bugs.spec.ts | live |
| BUG-10a | Bug Fixes | Insights: Average Job Duration respects the date range | UI | P3 | bugs.spec.ts | stub: needs seeded jobs with known durations inside and outside a date range |
| BUG-10b | Bug Fixes | Insights: weekly revenue counts every day, not only Mondays | UI | P3 | bugs.spec.ts | stub: needs seeded invoices on every weekday and the expected weekly total |
| BUG-10c | Bug Fixes | Insights: submission compliance respects the worker filter | UI | P3 | bugs.spec.ts | stub: needs seeded submissions for two workers and the expected compliance figures |
| BUG-10d | Bug Fixes | Insights: older "Created" invoices are included in status totals | UI | P3 | bugs.spec.ts | stub: needs an invoice in the legacy "Created" state and expected totals |
| BUG-11 | Bug Fixes | Search: users and customers can be found by the phone number and customer number shown in the list | UI | P3 | bugs.spec.ts | partial: the Users search leg needs a seeded user; column locators are fragile |
| BUG-12 | Bug Fixes | Log In As: the button is hidden while you are already logged in as someone else | PERM | P3 | bugs.spec.ts | live |
| BUG-13 | Bug Fixes | Login: the logo is no longer squashed against the top of the screen | UI | P4 | bugs.spec.ts | partial: the design spacing value is unconfirmed; add a visual baseline |

## Negative and permission tests (first-class)

| ID | New affordance | Persona that must NOT have it | Assertions |
| --- | --- | --- | --- |
| QUO-02 | cost / margin / markup columns | no-cost-viewer | hidden in the UI; absent from the customer quote PDF; "Show to Customer" locked off (cost-viewer) |
| JB-03 | budget sell / cost prices | no-cost-viewer | hidden in the UI; cost fields absent from the budget API response |
| RO-01 | New Role entry points | no-permission | hidden in the Create menu and palette; roles API returns 403 |
| CU-02 | Create Job button | no-permission; any user for an inactive customer | hidden |
| JOBS-04 | new job for an inactive customer | super-admin | no Create Job on the customer screen |
| LA-01 | Log In As | no-permission | not offered |
| SEC-01 / SEC-02 | staff / customer invite actions | no-permission | invite button hidden; list, send, resend, cancel return 401/403 |
| SEC-06 / SEC-07 | company rename; other customers' time logs | portal-customer | rename refused and unchanged; other job returns 403/404 |

## Manual and environment-dependent items

| ID | Reason |
| --- | --- |
| IPH-01 | App Store / TestFlight device required |
| IPH-02 | App Store build plus the feature flag state; also verify web flows unchanged with the flag off |
| IPH-03 | real payments on both rails; compare provider ledgers |
| PA-02 | needs a wall-clock boundary: mock the clock (page.clock) at 23:59:50 on 31 Dec / 30 Jun, or run a scheduled job near the boundary |

Billing-sandbox dependent stubs: SUB-01, SUB-02, SUB-03, SUBS-01, SUBS-02, SUBS-03, SUBS-04, PA-04. Unused prefix families from the convention: PH2 (no bullet needed it). Expected values the notes do not state are one-line `.env` fills (see `.env.example`: EXPECTED_*, FIXTURE_*, PORTAL_*).

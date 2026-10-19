/**
 * SINGLE SOURCE OF TRUTH for traceability. Every bullet of the FieldR release notes (Production, 6 October 2026)
 * has one entry here. `kind` says how the bullet is covered:
 *   live   - an executable test
 *   fixme  - test.fixme(true, 'reason: ...') naming the missing prerequisite
 *   manual - needs App Store / mobile, real payments, or a wall-clock moment (see `reason`)
 * scripts/check-traceability.ts fails if a spec does not cover an entry with the same kind.
 */
export type Persona = 'cost-viewer' | 'no-cost-viewer' | 'no-permission' | 'portal-customer' | 'super-admin';
export type Kind = 'live' | 'fixme' | 'manual';
export type Area =
  | 'quotes' | 'budget' | 'portal' | 'schedule' | 'roles' | 'customers' | 'subscription' | 'ios' | 'loginas'
  | 'pickers' | 'jobs' | 'joborders' | 'users' | 'datetime' | 'phone' | 'invites' | 'purchase' | 'pdf'
  | 'insights' | 'platform' | 'security' | 'bugfix';

export interface Note {
  readonly id: string;
  readonly area: Area;
  readonly persona: Persona;
  readonly kind: Kind;
  readonly text: string;
  readonly reason?: string;
}

const n = (id: string, area: Area, persona: Persona, kind: Kind, text: string, reason?: string): Note =>
  reason === undefined ? { id, area, persona, kind, text } : { id, area, persona, kind, text, reason };

export const NOTES: readonly Note[] = [
  // ---------------------------------------------------------------- New features: Quotes
  n('QUO-01', 'quotes', 'cost-viewer', 'live', 'Quote formula columns can use Cost Price, Margin % and Markup %'),
  n('QUO-02', 'quotes', 'no-cost-viewer', 'live', 'Columns using cost/margin/markup are internal only; never shown to customers; "Show to Customer" locked off'),
  n('QUO-03', 'quotes', 'cost-viewer', 'live', 'A line with no cost price shows a dash instead of 0 in cost/margin/markup columns'),
  n('QUO-04', 'quotes', 'super-admin', 'live', 'Quote list has a new "Created By" column'),
  // ---------------------------------------------------------------- Job Budget
  n('BUD-01', 'budget', 'cost-viewer', 'live', 'Each budget line has a sell price and a cost price; both auto-fill when a catalogue item is picked'),
  n('BUD-02', 'budget', 'cost-viewer', 'live', 'Line total = quantity x sell price; editor shows job budget and cost budget totals'),
  n('BUD-03', 'budget', 'no-cost-viewer', 'live', 'Prices are only visible to people allowed to see cost prices'),
  n('BUD-04', 'budget', 'cost-viewer', 'live', 'New Job Budget tile shows how much is left after costs so far, or how far costs have gone over'),
  // ---------------------------------------------------------------- Customer Portal
  n('POR-01', 'portal', 'portal-customer', 'live', 'Portal quote list has a Job column showing the job name, job number on hover'),
  n('POR-02', 'portal', 'portal-customer', 'live', 'Quotes that became jobs say "Converted to Job" instead of "Accepted" in the badge and the status filter'),
  n('POR-03', 'portal', 'portal-customer', 'fixme', 'If portal access is removed while logged in, customer sees "You no longer have access to the customer portal"', 'needs a dedicated portal login whose access can be revoked mid-session (the shared portal-customer persona must not be broken) and the revoke endpoint'),
  n('POR-04', 'portal', 'portal-customer', 'live', 'Customers can download the worklog report for their own jobs'),
  // ---------------------------------------------------------------- Schedule
  n('SCH-01', 'schedule', 'super-admin', 'live', 'Schedule header has Add Shift and Add User buttons; Add Shift opens on today 9am-5pm'),
  n('SCH-02', 'schedule', 'super-admin', 'live', 'Add User opens a quick popup without leaving the Schedule'),
  n('SCH-03', 'schedule', 'super-admin', 'live', 'After saving the new person, Add Shift opens for today 9am-5pm with them already in the team'),
  // ---------------------------------------------------------------- Roles
  n('ROL-01', 'roles', 'super-admin', 'live', 'New Role is in the Create menu and command palette only if the plan has custom roles and the user can manage roles'),
  n('ROL-02', 'roles', 'super-admin', 'live', 'Job Team step: "+" next to Assign By Role creates a new role with the same access as an existing one'),
  n('ROL-03', 'roles', 'super-admin', 'live', 'The new role is selected straight away and adds nobody to the job'),
  // ---------------------------------------------------------------- Customers
  n('CUS-01', 'customers', 'super-admin', 'live', 'Customer Details has a Create Job button that opens New Job with that customer already picked'),
  n('CUS-02', 'customers', 'no-permission', 'live', 'Create Job button is hidden for inactive customers and for people without job permission'),
  n('CUS-03a', 'customers', 'super-admin', 'live', 'Company name first in customer lists and screens'),
  n('CUS-03b', 'customers', 'super-admin', 'live', 'Company name first in quote and invoice drawers'),
  n('CUS-03c', 'customers', 'portal-customer', 'live', 'Company name first on the portal quote page'),
  n('CUS-03d', 'customers', 'super-admin', 'fixme', 'Company name first in Send Contract and contract requests', 'needs a contract-request seed endpoint and the contract screen locators'),
  n('CUS-03e', 'customers', 'super-admin', 'live', 'Company name first on portal access screens'),
  n('CUS-03f', 'customers', 'super-admin', 'fixme', 'Company name first in job exports and job reports', 'export file format and column names are not in the release notes'),
  n('CUS-04', 'customers', 'super-admin', 'live', 'Quote and invoice PDFs show the company in bold on the Bill To / For Services Rendered line with the contact underneath'),
  n('CUS-05', 'customers', 'super-admin', 'live', 'Job PDF lists Company before Client'),
  n('CUS-06', 'customers', 'super-admin', 'live', 'Customers without a company print exactly as before'),
  // ---------------------------------------------------------------- Subscription & Billing
  n('SUB-01', 'subscription', 'super-admin', 'fixme', 'A cancelled subscription can be resumed before it ends', 'needs a billing-sandbox company with a cancelled-but-not-ended subscription'),
  n('SUB-02', 'subscription', 'super-admin', 'fixme', 'Payment History shows whether each charge was monthly or yearly', 'needs a billing sandbox with both a monthly and a yearly charge'),
  n('SUB-03', 'subscription', 'super-admin', 'fixme', 'The first invoice lists each add-on separately', 'needs a billing sandbox company with a first invoice that includes add-ons'),
  // ---------------------------------------------------------------- iPhone app
  n('IOS-01', 'ios', 'super-admin', 'manual', 'Companies can sign up and pay through the App Store on iPhone', 'App Store / TestFlight device required'),
  n('IOS-02', 'ios', 'super-admin', 'manual', 'App Store billing stays off until it is switched on', 'App Store build plus the feature flag state; also verify web flows unchanged with the flag off'),
  n('IOS-03', 'ios', 'super-admin', 'manual', 'A company already paying by card is never charged twice', 'real payments on both rails; compare provider ledgers'),
  // ---------------------------------------------------------------- Admin Log In As
  n('LIA-01', 'loginas', 'super-admin', 'live', 'A super admin logged in as a company admin can log in as one of that company\'s customers'),
  // ---------------------------------------------------------------- Improvements: pickers
  n('PIC-01', 'pickers', 'super-admin', 'live', 'Job and Quote customer pickers show company in bold with contact underneath and a loading state'),
  n('PIC-02', 'pickers', 'super-admin', 'live', 'Pickers can be searched by company, name, email or Customer ID'),
  n('PIC-03', 'pickers', 'super-admin', 'live', 'Clearing a picker search brings back the full list'),
  n('PIC-04', 'pickers', 'super-admin', 'live', 'Long names in dropdowns are shortened neatly instead of breaking the layout'),
  // ---------------------------------------------------------------- Jobs
  n('JOB-01', 'jobs', 'super-admin', 'live', 'New jobs start with a 1000 m site radius, including when a quote is converted to a job'),
  n('JOB-02', 'jobs', 'super-admin', 'live', 'Job description is optional when creating or editing a job'),
  n('JOB-03', 'jobs', 'cost-viewer', 'live', 'Budget quantity tile is renamed "Lines Over Planned Qty", shows a count such as "2 of 5", with a caption'),
  n('JOB-04', 'jobs', 'super-admin', 'live', 'Inactive customers can no longer be given new jobs from the customer screen'),
  // ---------------------------------------------------------------- Job Orders
  n('ORD-01', 'joborders', 'super-admin', 'live', '"Phone" is renamed "Mobile Number" and "Site Contact" is renamed "Site Contact Name"'),
  n('ORD-02', 'joborders', 'super-admin', 'fixme', 'The error message for an invalid number is clearer', 'the new message wording is not in the release notes; set EXPECTED text then remove fixme'),
  n('ORD-03', 'joborders', 'super-admin', 'live', 'Job order has an Add Line button and the page scrolls to the line just added'),
  // ---------------------------------------------------------------- Users
  n('USR-01', 'users', 'super-admin', 'live', 'Industry is optional on Add User, Edit User and My Profile'),
  n('USR-02', 'users', 'super-admin', 'fixme', 'Picking a Google address fills Suburb, State and Postcode automatically', 'needs Google Places responses stubbed with page.route or a live key; stub shape unconfirmed'),
  n('USR-03', 'users', 'super-admin', 'live', 'Roles & Permissions sorts correctly by role name and opens A-Z'),
  // ---------------------------------------------------------------- Date & time
  n('DTM-01', 'datetime', 'super-admin', 'live', 'Date-time picker offers 15-minute slots and scrolls to the current time when it opens'),
  // ---------------------------------------------------------------- Phone numbers
  n('PHN-01', 'phone', 'super-admin', 'live', 'Phone number formatting is the same across forms (sign-up, customer contracts, job orders)'),
  // ---------------------------------------------------------------- Customer invites
  n('INV-01', 'invites', 'super-admin', 'live', 'Customer invite details step asks company name, address (required) and notes; no staff fields (date of birth, licences)'),
  n('INV-02', 'invites', 'super-admin', 'live', 'Opening a customer invite while signed in as staff no longer asks you to sign out'),
  n('INV-03', 'invites', 'portal-customer', 'fixme', 'A customer of another company can accept an invite using the mobile number already on their login', 'needs a second company plus an invite link seeded for an existing portal login'),
  n('INV-04', 'invites', 'super-admin', 'live', '"Your sign-in email" now reads "Your registration email"'),
  n('INV-05', 'invites', 'super-admin', 'live', 'The "waiting" count no longer shrinks while you search'),
  n('INV-06', 'invites', 'super-admin', 'live', 'The invite dialog and its buttons are labelled for screen readers (axe check; full screen-reader pass is manual)'),
  n('INV-07', 'invites', 'super-admin', 'live', 'Inviting a customer\'s email as staff explains why instead of saying "already a member"'),
  // ---------------------------------------------------------------- Subscription screens
  n('SBS-01', 'subscription', 'super-admin', 'fixme', 'Trial, cancellation and renewal status are clearer on Current Subscription, plan cards and the cancel card', 'needs billing-sandbox companies in trial, cancelled and renewing states; expected wording unconfirmed'),
  // ---------------------------------------------------------------- Purchase history
  n('PUR-01', 'purchase', 'super-admin', 'fixme', 'A cancelled trial is shown separately from an active plan', 'needs a billing-sandbox company with a cancelled trial'),
  n('PUR-02', 'purchase', 'super-admin', 'fixme', 'Alert messages use the space better', 'visual-layout change with no stated expectation; use a screenshot baseline once approved'),
  n('PUR-03', 'purchase', 'super-admin', 'fixme', 'The onboarding fee is handled correctly for resumed subscriptions', 'needs a billing sandbox resumed subscription and the expected fee amount'),
  // ---------------------------------------------------------------- PDFs
  n('PDF-01', 'pdf', 'super-admin', 'live', 'Order PDF shows the ABN properly formatted and has clearer labels'),
  n('PDF-02', 'pdf', 'super-admin', 'live', 'Company ABN is formatted on reports too'),
  n('PDF-03', 'pdf', 'super-admin', 'live', 'Timesheet PDFs no longer have blank pages'),
  // ---------------------------------------------------------------- Insights
  n('INS-01', 'insights', 'super-admin', 'live', 'Insights reports show the status, customer and worker filters they already supported'),
  n('INS-02', 'insights', 'super-admin', 'live', 'Percentages on cards round the same way as in the table'),
  // ---------------------------------------------------------------- Platform admin
  n('PLT-01', 'platform', 'super-admin', 'live', 'The platform overview loads once (one request per data source)'),
  n('PLT-02', 'platform', 'super-admin', 'manual', 'Year-to-date figures are correct around midnight', 'needs a wall-clock boundary: mock the clock (page.clock) at 23:59:50 on 31 Dec / 30 Jun, or run a scheduled job near the boundary'),
  n('PLT-03', 'platform', 'super-admin', 'live', 'Accounts list shows sorting and accounts with zero revenue, and tells you about the 200-row limit'),
  n('PLT-04', 'platform', 'super-admin', 'fixme', 'Monthly revenue counts yearly plans, trials and one-off charges correctly', 'needs seeded revenue fixtures (yearly plan, trial, one-off) and the expected totals'),
  n('PLT-05', 'platform', 'super-admin', 'live', 'Role settings on the platform console only offer super-admin modules to the Super Admin role'),
  // ---------------------------------------------------------------- Security & data quality
  n('SEC-01', 'security', 'no-permission', 'live', 'Staff invites (send, view, resend, cancel) need user permission'),
  n('SEC-02', 'security', 'no-permission', 'live', 'Customer invites (send, view, resend, cancel) need customer permission'),
  n('SEC-03', 'security', 'super-admin', 'live', 'Invalid email addresses are refused for invites, users and customers'),
  n('SEC-04', 'security', 'super-admin', 'live', 'Deleted users and customers can no longer be opened from an old link'),
  n('SEC-05', 'security', 'super-admin', 'live', 'A company name must contain at least one letter'),
  n('SEC-06', 'security', 'portal-customer', 'live', 'Customer contacts can no longer change the company name'),
  n('SEC-07', 'security', 'portal-customer', 'live', 'Customers can only see time logs for their own jobs'),
  // ---------------------------------------------------------------- Bug fixes
  n('BUG-01', 'bugfix', 'super-admin', 'fixme', 'Contracts: recipients who have signed no longer show "Opened: Not yet" or "Read: Not yet"', 'needs a contract with a signed recipient (signing link flow) seeded through the API'),
  n('BUG-02', 'bugfix', 'super-admin', 'live', 'Quotes: a new quote no longer keeps the section name and rows from the previous new quote'),
  n('BUG-03', 'bugfix', 'super-admin', 'live', 'Defects: title and description changes are saved when you close the menu'),
  n('BUG-04', 'bugfix', 'super-admin', 'fixme', 'Defects: the defect view shows the drawing with its markup, not the plain image', 'needs a defect with a drawing and markup seeded (file upload) and an image-diff baseline'),
  n('BUG-05a', 'bugfix', 'cost-viewer', 'live', 'Jobs: editing a job budget no longer wipes the prices copied from the quote'),
  n('BUG-05b', 'bugfix', 'cost-viewer', 'fixme', 'Jobs: prices already wiped on existing jobs can be restored', 'needs a legacy job with wiped prices and the documented restore action'),
  n('BUG-06', 'bugfix', 'super-admin', 'fixme', 'Jobs: budget lines typed by hand on a quote match correctly in daily reports', 'needs a daily report seed that references a hand-typed quote line'),
  n('BUG-07', 'bugfix', 'portal-customer', 'live', 'Customer Portal: the "Device id is required" error on portal login is fixed'),
  n('BUG-08', 'bugfix', 'portal-customer', 'fixme', 'Plan checks now handle customer portal logins correctly', 'needs a plan-limited company and the plan-check endpoint that portal logins hit'),
  n('BUG-09a', 'bugfix', 'super-admin', 'fixme', 'Invites: a refused customer invite shows an error instead of hanging', 'needs a precondition that makes the server refuse the invite (rule unknown)'),
  n('BUG-09b', 'bugfix', 'super-admin', 'live', 'Invites: a missing email gives a clear error'),
  n('BUG-10', 'bugfix', 'super-admin', 'fixme', 'Insights: Average Job Duration respects the date range', 'needs seeded jobs with known durations inside and outside a date range'),
  n('BUG-11', 'bugfix', 'super-admin', 'fixme', 'Insights: weekly revenue counts every day, not only Mondays', 'needs seeded invoices on every weekday and the expected weekly total'),
  n('BUG-12', 'bugfix', 'super-admin', 'fixme', 'Insights: submission compliance respects the worker filter', 'needs seeded submissions for two workers and the expected compliance figures'),
  n('BUG-13', 'bugfix', 'super-admin', 'fixme', 'Insights: older "Created" invoices are included in status totals', 'needs an invoice in the legacy "Created" state and expected totals'),
  n('BUG-14', 'bugfix', 'super-admin', 'live', 'Search: users and customers can be found by the phone number and customer number shown in the list'),
  n('BUG-15', 'bugfix', 'super-admin', 'live', 'Log In As: the button is hidden while you are already logged in as someone else'),
  n('BUG-16', 'bugfix', 'super-admin', 'live', 'Login: the logo is no longer squashed against the top of the screen'),
];

export const NOTE_BY_ID: ReadonlyMap<string, Note> = new Map(NOTES.map((x) => [x.id, x]));
export type NoteId = string;

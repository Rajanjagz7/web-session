# Reports Module — Release Notes

**Release:** Reports (analytics hub) — first release
**Branch:** `feat/insights-reports-module` (backend + web)
**Audience:** QA / test team
**Companion docs:** [reports-module-qa.md](./reports-module-qa.md) (web test
plan) · [reports-module-mobile.md](./reports-module-mobile.md) (mobile)

> These notes say **what changed and where the risk is**, so you know what to
> aim at. The step-by-step test cases live in the QA doc — this is the
> orientation, not a second copy of it.

---

## 1. In one paragraph

A new **Reports** area gives company admins a hub of 18 pre-built reports
across Jobs, Finance, Workforce and Compliance. Each runs live against the
workspace's own data and shows KPIs, a chart, and a detail table, with CSV /
PDF / Excel export. Access is controlled by a new **Reports** permission. The
existing "Report" sidebar item — the on-site forms — has been **renamed to
"Job Report"** to free the name.

---

## 2. What a tester will see that wasn't there before

| # | Change | Where |
|---|---|---|
| 1 | New **Reports** item in the sidebar | Below Job Report |
| 2 | Reports hub — 18 cards, 4 category tabs, search | `/app/reports` |
| 3 | Report viewer — filters, KPIs, chart, table, export | `/app/reports/:id` |
| 4 | **"Report" is now "Job Report"** | Sidebar — an existing item, renamed |
| 5 | New **Reports** permission in role setup | Role / permission screens |
| 6 | ⓘ info icons explaining each report | Hub cards + viewer title |

---

## 3. The rename — the main regression risk

This is the only change that touches something that already existed and
already worked.

| Before | After | Route (unchanged) |
|---|---|---|
| "Report" | **"Job Report"** | `/app/report/list` |
| — | **"Reports"** (new) | `/app/reports` |

**Only the label changed.** No route, permission, or behaviour of the job
report module was altered.

**Please confirm** the old module is intact: create, view, submit, and approve
a job report; check Report Builder in Settings; and confirm its permissions
still work independently of the new Reports permission. (QA doc §7.1.)

Two names now differ by one word, so **be precise in bug titles** — say "Job
Report" or "Reports (analytics)", never just "report".

---

## 4. What ships

### 4.1 The 18 reports

| Category | Reports |
|---|---|
| **Jobs & Operations** (5) | Job Status Breakdown · Overdue Jobs · Jobs by Customer & Location · Average Job Duration · Job Task Throughput |
| **Finance** (5) | Invoice Status Breakdown · Revenue Trend · Outstanding Invoices & Ageing · Quote Pipeline · Revenue by Customer |
| **Workforce** (5) | Hours Worked Summary · Normal vs Overtime Hours · Weekend & Holiday Hours · Labour Hours per Job · Timesheet Edits Audit |
| **Compliance** (3) | Report Submission Compliance · Report Approval Turnaround · Checklist Completion |

Two of these — **Overdue Jobs** and **Timesheet Edits Audit** — are
table-only by design. A missing chart on those is correct, not a defect.

### 4.2 Hub

Category tabs with live counts · search across titles and descriptions ·
cards showing icon, title, description and visualisation type · ⓘ per report.

Search behaviour worth knowing: it searches **all** reports and then the tab
narrows the result, so a match in another category is still findable. Tab
counts follow the search, and a category the search empties **disappears**
rather than showing "0".

### 4.3 Viewer

Date-range filter (plus Group by where relevant) · KPI tiles · chart · detail
table · export to CSV, PDF or Excel. PDF carries workspace branding, like other
Fieldr documents.

### 4.4 Permissions

A new **Reports** module permission. Company admins, sole traders and super
admins always have access; any other role needs it granted.

Access is layered, and this is the part most worth attacking:

1. **Module** — can you open Reports at all?
2. **Per report** — the hub only lists reports whose underlying module you can
   view. A user who cannot see Invoices gets **no finance cards at all** — not
   empty ones.
3. **Per row** — within a report, you only see rows you could see in the source
   module. A supervisor with assigned-only job access gets counts covering
   *their* jobs only.

---

## 5. Behaviour changes on upgrade

| # | Change | Effect |
|---|---|---|
| 1 | Sidebar "Report" → "Job Report" | Cosmetic; existing users will notice the wording |
| 2 | Existing roles gain Reports access | A role that never configured the module inherits the platform default, which grants it. This matches how every other module behaves — but it does mean non-admin roles may see Reports appear |
| 3 | New workspaces get Reports **off** | Must be enabled by a company admin |

Nothing is removed, and no existing data is migrated or altered.

---

## 6. Where to aim your testing

Ranked by risk.

### 6.1 Permissions and tenant isolation — highest

Any failure here is a **blocker**.

- A role that cannot view Invoices must not see finance reports, even by
  typing the URL directly
- A role with assigned-only access must see only their own rows
- Super admin bypass-login must show **that** workspace's data, never another
  tenant's
- Customer portal logins must be blocked entirely

### 6.2 Number accuracy — highest value

Every figure must reconcile with the source module. Pick a **narrow date range**
with few records so you can count by hand, then cross-check (QA doc §5.4).
This is where genuine bugs are most likely.

### 6.3 The rename regression

Section 3 above.

### 6.4 Exports

The exported file must match what's on screen, **after** filtering.

### 6.5 Dark mode

Whole module is new, so dark mode is entirely untested by real use.

---

## 7. Things that look like bugs but aren't

Full list in QA doc §5.3 — each is explained in the report's ⓘ tooltip. The
five most likely to be re-reported:

| Behaviour | Why |
|---|---|
| Completion rate shows **0%** while jobs are in progress | It's completed ÷ *all* jobs in range |
| **Overdue Jobs** ignores the date range | Overdue is measured against today |
| **Outstanding & Ageing** has no date filter | Deliberate — an invoice's age is a fact about today |
| A clocked-on worker's hours are missing | Hours count only after clock-off, so a past period doesn't change on every refresh |
| Weekend + Holiday hours don't add up to a sensible total | A shift can be both; the columns overlap by design |

If the behaviour is on this list, please check the ⓘ tooltip **explains** it,
and raise a doc bug if it doesn't — rather than raising the behaviour itself.

---

## 8. Known gaps — already understood

Please don't re-log these; confirming them is useful, re-reporting isn't.

1. **Revenue Trend weekly buckets** may misalign at week boundaries. Under
   review. Daily and monthly ranges are unaffected.
2. **Mixed currencies** are summed without conversion. Only affects workspaces
   invoicing in more than one currency.
3. **Not yet tested at production scale.** Performance findings on large
   workspaces are genuinely wanted.
4. **No mobile UI yet.** The API is ready and client-agnostic; the mobile
   screens are not built. See the mobile doc.

---

## 9. Out of scope for this release

Not missing — not built yet. Please don't raise as defects.

- Drill-through from a chart into the underlying records
- Saved filter presets / favourites
- Scheduled email delivery of reports
- Comparison against a previous period
- Custom or user-built reports
- Customer-portal access to reports

---

## 10. Deployment

- **Backend and web must ship together.** The web app calls new endpoints
  (`/api/v1/insights/*`); web deployed alone would show a broken Reports page.
- No database migration, no config change, no new environment variables.
- Backend adds one module (`src/insights/`) and mounts one route; existing
  endpoints are untouched.
- **Rollback:** revert both branches. Nothing persists, so there is nothing to
  clean up.

---

## 11. Test environment checklist

Reports read existing data, so a thin workspace produces empty reports that
look like failures. Before testing, confirm the workspace has:

- Jobs across several statuses, including at least one Completed
- At least one job past its due date and still open
- Jobs for more than one customer, with addresses filled in
- Invoices in Draft / Awaiting Payment / Paid, at least one overdue
- Quotes at several stages, including one Converted to Job
- **Closed** time logs — clocked on *and off*
- At least one manually edited time entry, with a reason
- Checklists partly ticked
- Submitted job reports, ideally one approved and one rejected

Accounts needed: company admin · sole trader · a non-admin role with Reports ·
one without · one that cannot view Invoices · a customer portal login · super
admin. (QA doc §2.)

**An empty report is not automatically a bug** — check the data exists in the
selected period first, and raise it as a question if you're unsure.

# Reports Module — QA Test Plan

**Feature:** Reports (analytics hub)
**Branch:** `feat/insights-reports-module` (backend + web)
**Module name in code:** `insights` — see §1.1
**Status:** Ready for QA. Not yet tested against production-scale data.

---

## 1. What this feature is

A reports hub listing 18 reports across four categories. Each report runs a
live aggregation against the workspace's own data and renders as KPIs, a chart,
and a detail table, with CSV / PDF / Excel export.

- **Web:** sidebar → **Reports** → `/app/reports`
- **API:** `GET /api/v1/insights/*`

### 1.1 The naming change — read this first

"Report" already meant two different things in Fieldr. This release separates
them:

| Sidebar label | What it is | Route |
|---|---|---|
| **Job Report** (renamed, was "Report") | The on-site forms field workers fill in | `/app/report/list` |
| **Reports** (new) | The analytics hub | `/app/reports` |

**Regression risk:** the rename touches the existing Job Report module's label
only — not its behaviour. Confirm the old module still works end to end
(§7.1).

### 1.2 The 18 reports

| Category | Reports |
|---|---|
| **Jobs & Operations** (5) | Job Status Breakdown · Overdue Jobs · Jobs by Customer & Location · Average Job Duration · Job Task Throughput |
| **Finance** (5) | Invoice Status Breakdown · Revenue Trend · Outstanding Invoices & Ageing · Quote Pipeline · Revenue by Customer |
| **Workforce** (5) | Hours Worked Summary · Normal vs Overtime Hours · Weekend & Holiday Hours · Labour Hours per Job · Timesheet Edits Audit |
| **Compliance** (3) | Report Submission Compliance · Report Approval Turnaround · Checklist Completion |

---

## 2. Before you start

### 2.1 Accounts needed

| # | Account | Why |
|---|---|---|
| 1 | Company admin | Full access; the main path |
| 2 | Sole trader | Should also have full access |
| 3 | Non-admin role (e.g. Manager) **with** Reports permission | Delegated access |
| 4 | Non-admin role **without** Reports permission | Must not see the module |
| 5 | A role that cannot view Invoices | Must not see finance reports at all |
| 6 | Customer portal login | Must be blocked entirely |
| 7 | Super admin | Includes the bypass-login case (§6.4) |

### 2.2 Data the workspace needs

Several reports are empty without the right data. Before testing, confirm the
workspace has:

- Jobs in **several different statuses**, including at least one Completed
- At least one job **past its due date** and still open
- Jobs belonging to **more than one customer**, with addresses filled in
- Invoices in Draft / Awaiting Payment / Paid, at least one **overdue**
- Quotes at several stages, including one **Converted to Job**
- **Closed** time logs (worker clocked on *and off*) — see §5.3
- Time entries that were **manually edited, with a reason**
- Checklists with some items ticked and some not
- At least one submitted job report, ideally one approved and one rejected

> If a report is empty, first check the data exists for the selected period —
> an empty report is not automatically a bug. Log it as a question, not a
> defect, unless you can prove matching data exists in range.

---

## 3. Smoke test (15 min)

Do this first. If any step fails, stop and report — the rest will not be
meaningful.

| # | Step | Expected |
|---|---|---|
| 1 | Log in as company admin | — |
| 2 | Find **Reports** in the sidebar | Present, below Job Report |
| 3 | Confirm **Job Report** is still there, correctly renamed | Both items visible, different names |
| 4 | Open Reports | Hub loads, 18 cards, no spinner stuck |
| 5 | Check the tab counts | 5 / 5 / 5 / 3, "All reports" = 18 |
| 6 | Open **Job Status Breakdown** | Loads with KPIs, donut chart, detail table |
| 7 | Change **Date range** | Figures update |
| 8 | **Export → CSV** | File downloads, opens in Excel, matches on-screen table |
| 9 | Click **All reports** | Returns to hub |
| 10 | Open a Finance and a Workforce report | Both load |

---

## 4. The hub

### 4.1 Layout and cards

| # | Test | Expected |
|---|---|---|
| 4.1.1 | Card contents | Icon, title, description, visualisation type, "Open report" |
| 4.1.2 | Hover a card | Lifts slightly; coloured rail appears on the left; border and arrow pick up the category colour |
| 4.1.3 | Category colours | Jobs = indigo, Finance = green, Workforce = amber, Compliance = red. Consistent across every card in that category |
| 4.1.4 | Click anywhere on a card | Opens the report (whole card is clickable, not just the link text) |
| 4.1.5 | Cards in the same row | Equal height, footers aligned, regardless of description length |
| 4.1.6 | Resize the window narrow → wide | Grid reflows 1 → 2 → 3 → 4 columns without overlap or clipping |

### 4.2 The info icon

| # | Test | Expected |
|---|---|---|
| 4.2.1 | Hover the ⓘ on a card | Tooltip with a longer explanation of the report |
| 4.2.2 | Tooltip content | Explains what the report counts / excludes — **not** a repeat of the card description |
| 4.2.3 | Move the mouse away | Tooltip dismisses cleanly |
| 4.2.4 | Hover ⓘ then click the card | Card still opens — the icon must not swallow the click |
| 4.2.5 | ⓘ in the report viewer, beside the title | Same tooltip behaviour |

### 4.3 Category tabs

| # | Test | Expected |
|---|---|---|
| 4.3.1 | Click each tab | Only that category's cards show; count matches the cards displayed |
| 4.3.2 | "All reports" | All 18 return |
| 4.3.3 | Selected tab | Visually distinct (coloured underline) |

### 4.4 Search

| # | Test | Expected |
|---|---|---|
| 4.4.1 | Type `invoice` | Only matching reports; tab counts drop to match |
| 4.4.2 | Search matches a **description**, not just a title | Card still appears — search covers both |
| 4.4.3 | Search while on a specific tab | Matches in **other** categories still findable via "All reports" |
| 4.4.4 | Search that empties a category | That tab **disappears** rather than showing "0" |
| 4.4.5 | Sit on Workforce, then search something only Finance matches | Selection falls back to "All reports"; no blank screen |
| 4.4.6 | Search with no matches at all | Message naming the search term, e.g. `No reports match "zzz".` |
| 4.4.7 | Click the ✕ | Search clears, all 18 return, counts restore |
| 4.4.8 | Search `INVOICE` in capitals | Same results — case-insensitive |
| 4.4.9 | Search with leading/trailing spaces | Ignored |

---

## 5. Report viewer

### 5.1 Common to every report

Run this block against **all 18** reports and tick them off.

| # | Test | Expected |
|---|---|---|
| 5.1.1 | Report opens | Title, description, ⓘ, Export button, filter bar |
| 5.1.2 | KPI figures | Present, formatted with thousands separators, no `NaN` / `undefined` / `null` |
| 5.1.3 | Chart | Renders for chart reports. **Detailed report** types show a table only — this is correct, not a missing chart |
| 5.1.4 | Detail table | Column headers readable (spaced words, not `camelCase`) |
| 5.1.5 | Numeric columns | Values **centred** under their headers, digits aligned |
| 5.1.6 | Empty cells | Show `—`, never blank or `undefined` |
| 5.1.7 | Dates in the table | Formatted `05 Aug 2026`, never a raw number like `1754352000000` |
| 5.1.8 | **All reports** button | Returns to the hub with the previous tab/search still applied |
| 5.1.9 | Reload the page on a report URL | Report loads directly, no error |
| 5.1.10 | Chart vs table | The chart's figures match the table's for the same rows |

### 5.2 Filters

| # | Test | Expected |
|---|---|---|
| 5.2.1 | Each date range option | Figures change appropriately; wider range ≥ narrower range |
| 5.2.2 | "This financial year" | Runs **1 July – 30 June** (Australian FY), *not* the calendar year |
| 5.2.3 | **Group by** on Jobs by Customer & Location | Switches between customer names and location names |
| 5.2.4 | **Reset** | Returns to "This month" |
| 5.2.5 | Filters only show where relevant | Outstanding Invoices & Ageing has **no** date range — by design, see §5.4 |
| 5.2.6 | Change filter rapidly several times | Final result matches the final selection (no stale/out-of-order response) |

### 5.3 Known-correct behaviours — do NOT raise these as bugs

These are deliberate. Each is explained in the report's ⓘ tooltip. Please
verify the tooltip *says so*, rather than reporting the behaviour itself.

| Report | Behaviour |
|---|---|
| **Job Status Breakdown** | Completion rate reads low/0% while jobs are still in progress — it is completed ÷ *all* jobs in range |
| **Job Status Breakdown** | A long-running job appears in a month it neither started nor ended in (date ranges *overlap* the window) |
| **Overdue Jobs** | Same list regardless of the date range — overdue is measured against *today* |
| **Overdue Jobs** | Jobs with no due date never appear |
| **Outstanding Invoices & Ageing** | Ignores the date filter entirely (no date control shown) |
| **Hours Worked / Labour Hours / Overtime** | A worker **currently clocked on** is not counted until they clock off |
| **Labour Hours per Job** | Can total less than Hours Worked Summary — time logged with no job attached is excluded |
| **Weekend & Holiday Hours** | The two columns can count the same shift; they must **not** be added together |
| **Report Approval Turnaround** | Excludes submissions still awaiting a decision |
| **Checklist Completion** | Counts individual **items**, not whole checklists |
| **Revenue Trend** | Buckets widen daily → weekly → monthly as the range grows |
| **Jobs by Location** | Near-duplicate locations if site addresses were typed inconsistently |

### 5.4 Data accuracy — cross-check against the source module

This is the most valuable testing you can do. Pick a **narrow date range** with
few records so the numbers are countable by hand.

| # | Report | Cross-check against |
|---|---|---|
| 5.4.1 | Job Status Breakdown | Jobs list filtered by each status — counts must match |
| 5.4.2 | Overdue Jobs | Jobs list sorted by due date |
| 5.4.3 | Invoice Status Breakdown | Invoices list per status; totals must match |
| 5.4.4 | Outstanding Invoices & Ageing | Sum of unpaid invoice balances |
| 5.4.5 | Quote Pipeline | Quotes list per status |
| 5.4.6 | Revenue by Customer | Individual customer's invoice totals |
| 5.4.7 | Hours Worked Summary | Timesheet module for the same person and period |
| 5.4.8 | Normal vs Overtime | Timesheet ordinary/overtime split — must agree exactly |
| 5.4.9 | Timesheet Edits Audit | Known manually-edited entries |
| 5.4.10 | Checklist Completion | Open a job, count its ticked items |

> **Report any mismatch with:** report name, filters used, the figure shown, the
> figure you expected, and how you counted it.

### 5.5 Export

For at least one report per category, and for each of CSV / PDF / Excel:

| # | Test | Expected |
|---|---|---|
| 5.5.1 | Export downloads | File saves with a sensible name |
| 5.5.2 | Rows match | Same rows and values as the on-screen table |
| 5.5.3 | Filters respected | Exporting after filtering exports the **filtered** data |
| 5.5.4 | CSV in Excel | Columns separate correctly; accented characters intact |
| 5.5.5 | PDF | Carries workspace branding/letterhead, like other Fieldr PDFs |
| 5.5.6 | Excel | Opens without a repair warning |
| 5.5.7 | Export an empty report | Produces a valid file with headers, not an error |
| 5.5.8 | Export with pop-ups blocked | Note the behaviour — export opens a new tab |

---

## 6. Permissions and security

**The highest-risk area.** A report must never show data the user could not
see elsewhere.

| # | Test | Expected |
|---|---|---|
| 6.1.1 | Company admin | Sees all 18 |
| 6.1.2 | Sole trader | Sees the hub; workforce reports may be thin (no crew) — not a bug |
| 6.1.3 | Role **without** Reports permission | **No** Reports item in the sidebar; typing `/app/reports` directly is blocked |
| 6.1.4 | Role **with** Reports permission (non-admin) | Can open the hub |
| 6.1.5 | Role that **cannot view Invoices** | Finance cards **absent from the hub entirely** — not present-but-empty. Count drops below 18 |
| 6.1.6 | Same role, direct URL to a finance report | Blocked with an error, not an empty report |
| 6.1.7 | Role with **assigned-only** job access | Job reports count **only their own** jobs — cross-check against their Jobs list |
| 6.1.8 | Customer portal login | Cannot reach Reports at all |
| 6.1.9 | Logged out, hit `/app/reports` | Redirected to login |
| 6.1.10 | Revoke Reports mid-session, refresh | Access removed |
| 6.1.11 | **Super admin bypass-login** into a workspace | Sees **that workspace's** data, not central/other-tenant data |
| 6.1.12 | Two workspaces, same super admin | Figures differ per workspace; no leakage between them |

> 6.1.5, 6.1.7 and 6.1.12 are the critical ones. Any failure = **blocker**.

---

## 7. Regression

### 7.1 The Job Report module (renamed)

| # | Test | Expected |
|---|---|---|
| 7.1.1 | Sidebar shows **Job Report** | Renamed, still present |
| 7.1.2 | Open it | Loads as before |
| 7.1.3 | Create / view / submit a job report | Unchanged |
| 7.1.4 | Report Builder in Settings | Unchanged |
| 7.1.5 | Job Report permissions | Still independent of the new Reports permission — grant one, revoke the other, confirm they don't interfere |

### 7.2 Elsewhere

| # | Test | Expected |
|---|---|---|
| 7.2.1 | Dashboard | Unchanged |
| 7.2.2 | Jobs / Invoices / Quotes / Timesheets lists | Unchanged |
| 7.2.3 | Other sidebar items | Still present, correct order |
| 7.2.4 | Other modules' PDF/CSV exports | Still work |

---

## 8. Cross-browser, responsive, accessibility

| # | Test | Expected |
|---|---|---|
| 8.1 | Chrome, Edge, Firefox, Safari | Consistent |
| 8.2 | Tablet width | Grid reflows; tables scroll horizontally rather than breaking the page |
| 8.3 | Mobile browser width | Usable; the page itself must not scroll sideways |
| 8.4 | **Dark mode** | Every screen legible — cards, chart, table, tooltips. No white-on-white or black-on-black |
| 8.5 | Dark mode chart colours | Series distinguishable; not a washed-out inversion |
| 8.6 | Keyboard `Tab` through the hub | Focus visible on each card (ring), `Enter` opens |
| 8.7 | Keyboard focus on ⓘ | Tooltip shows without a mouse |
| 8.8 | Zoom to 200% | No overlap or clipping |

---

## 9. Error handling and edge cases

| # | Test | Expected |
|---|---|---|
| 9.1 | Brand-new workspace, no data | Hub loads; reports show empty states, **not** errors or spinners |
| 9.2 | Invalid report id in URL | Clean "not found", not a crash |
| 9.3 | Go offline, then open a report | Readable error message |
| 9.4 | Offline, then back online, retry | Recovers |
| 9.5 | Very wide date range (12 months) | Completes; chart stays readable (buckets widen) |
| 9.6 | Report with many rows | Table remains usable |
| 9.7 | Rapid back/forward between reports | No stale data from the previous report |
| 9.8 | Open two reports in two tabs | Independent |
| 9.9 | Non-ASCII customer/job names | Display correctly on screen **and** in exports |

---

## 10. Performance

| # | Test | Target |
|---|---|---|
| 10.1 | Hub load | < 2 s |
| 10.2 | Report load, 1-month range | < 3 s |
| 10.3 | Report load, 12-month range | < 8 s (server caps aggregations at 15 s) |
| 10.4 | Export | Starts within a few seconds |
| 10.5 | Largest available workspace | Note any report noticeably slower than the rest |

---

## 11. Known gaps — already understood, please don't re-log

1. **Revenue Trend weekly buckets** — weekly grouping may misalign at week
   boundaries. Under review. Daily and monthly are unaffected. Worth
   *confirming*, not re-reporting.
2. **Mixed currencies** — if a workspace invoices in more than one currency,
   financial totals sum the raw numbers without conversion. Only affects
   multi-currency workspaces.
3. **Not yet tested at production scale.** Performance findings on large
   workspaces are genuinely useful.
4. **Existing roles gain access on deploy.** A role that never configured the
   module inherits the platform default, which grants it. This matches every
   other module's behaviour. New workspaces get Reports **off** by default.

---

## 12. Reporting a defect

Please include:

- **Report name** and **category**
- **Exact filters** (date range, group by) and the **workspace**
- **Role/account** used
- Expected vs actual, **with how you verified the expected figure**
- Screenshot (include the filter bar — it shows the state)
- Browser + version; light or dark mode
- For wrong numbers: the source-module screen you cross-checked against

**Severity guide**

| Level | Meaning |
|---|---|
| **Blocker** | Data leak across roles/workspaces; a report shows another tenant's data; hub won't load |
| **High** | A figure is wrong; export doesn't match screen; permission not enforced |
| **Medium** | Layout broken; dark mode unreadable; filter misbehaves |
| **Low** | Copy, spacing, polish |

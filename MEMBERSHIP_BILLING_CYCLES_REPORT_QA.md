# Membership Billing Cycles Report — QA Test Plan

| | |
|---|---|
| **Asana** | [Report for Invoices / Payment billing cycles in reports for memberships](https://app.asana.com/1/757630589075869/project/1211749193102969/task/1217155076122994) |
| **Priority** | High |
| **Backend commits** | `bff2999e` (feature), `35b22ae2` (display fixes) — branch `dev` |
| **Frontend commit** | `5f44b757` — branch `dev` |
| **Tester** | |
| **Date tested** | |
| **Build / env** | |

---

## 1. What shipped

A new membership sub-report, **Billing Cycles**. It lists **one row per membership per billing
cycle** and says what happened to that cycle's invoice: generated and paid, generated and
failed / cancelled / voided, still pending, or **never generated at all**.

The last one is the point of the ticket. Every other membership report only shows what exists;
this is the only one that can show what is *missing*.

**Where it lives**

- Backend — `GET /api/v1/report/membership?subReportType=billingCycles` and `.../membership/csv`
- Frontend — Reports → Membership category → **Membership Billing Cycles**
- Cycle logic — `src/app/report/report.membershipBillingCycles.helper.ts` (pure, unit tested)

**What else changed** — `upsertFromStripe` now also saves `stripePeriodStart` / `stripePeriodEnd`
on membership and package invoices mirrored from Stripe. Two new optional fields, nothing else in
the webhook path was touched. This matters for regression testing (§7).

---

## 2. Environment & preconditions

- [ ] **Backend and frontend both deployed.** Frontend alone is not enough — the report is hidden
      until the backend advertises it. If the card does not appear, check this first.
- [ ] Logged in as a **staff user whose Reports permission includes the Membership category**. Same
      gate as the existing six membership reports. No permission → no card, and that is correct
      behaviour, not a bug.
- [ ] A clinic with at least one location and several patient memberships (see §3).
- [ ] Stripe test mode available if you intend to test §7.5.

---

## 3. Test data to arrange

You will not be able to exercise every status on one membership. Aim for this spread — most
clinics with real usage already have several of these.

| Data set | What it needs | Covers cases |
|---|---|---|
| **A** | Recurring monthly Stripe membership, several months old, every invoice paid | 5.1, 5.2, 6.1 |
| **B** | Membership auto-cancelled by Stripe dunning (`cancellationReason: payment_failed`) — see `QA_MEMBERSHIP_PAYMENT_FAILURE.md` Scenario D | 5.3, 5.4 |
| **C** | Membership with a known gap — a past cycle whose invoice was never created | 5.5 |
| **D** | Membership on a free trial | 5.7 |
| **E** | Membership with `source: clinic_assigned` or `checkout_free`, or a $0 plan | 5.8 |
| **F** | Membership with an approved / active / completed pause covering a whole cycle | 5.9 |
| **G** | `invoiceAtPeriodEnd` membership, current period still open | 5.10 |
| **H** | One-time / package membership (`billingInterval: one_time` or `membershipCycle: none`) | 5.11 |
| **I** | A cycle carrying two fee invoices (proration + period charge) | 5.12 |
| **J** | Weekly and yearly plans, for interval coverage | 5.13 |

---

## 4. Behaviour reference — read this before testing

The status column is derived, not stored. Rules are applied **in this order**, first match wins.
If an invoice exists for the cycle it always describes the cycle; only when none exists do we ask
why not.

| Order | Condition | Status shown |
|---|---|---|
| 1 | Invoice is paid | `Paid` |
| 2 | Invoice unpaid **and** has a recorded decline | `Payment Failed` |
| 3 | Invoice status is Void | `Voided` |
| 4 | Invoice status is Cancelled (Stripe *uncollectible*) | `Cancelled` |
| 5 | Invoice exists, none of the above | `Pending` |
| 6 | No invoice, and it is not due yet | `Upcoming` |
| 7 | No invoice, cycle falls inside a pause | `Paused` |
| 8 | No invoice, cycle falls inside the trial | `Trial` |
| 9 | No invoice, membership is free-source or $0 | `Free — no invoice` |
| 10 | No invoice, past cycle, no excuse | **`Not generated`** ← the anomaly |

Three conventions that trip testers up:

1. **Cycle number counts from the membership's start, not the visible rows.** Filter to one month
   and you may see `#12`–`#15`. That is correct — it is the 12th to 15th cycle of that membership's
   life. Numbers do not renumber when you change the date filter.
2. **"Paid / Failed On" is filled only when money moved or failed to move.** Paid → paid date,
   Payment Failed → decline date. Every other status leaves it blank (`-`) and puts its date in
   **Notes** instead (`invoice due …`, `issued …, awaiting payment`, `free trial to …`,
   `membership paused from …`). A date appearing under that heading on an Upcoming row is a bug.
3. **Amount is the sum of the cycle's fee invoices.** A cycle can carry more than one. Consolidated
   period-end invoices are excluded from the sum — they itemise the same fee, so adding them would
   double-count — but they still appear under Invoice #.

---

## 5. Functional test cases

> Steps assume: Reports → Membership → **Membership Billing Cycles**, then set Clinic Location and
> Period. Use the **Select Patient** filter to isolate a data set.

### 5.1 Report is visible and loads
1. Open Reports, choose the Membership category.
2. Locate the **Membership Billing Cycles** card and open it.

**Expected** — card is listed; opening it renders a table; no console errors.
**Result:** ☐ Pass ☐ Fail

### 5.2 Cycles are continuous and correctly numbered
1. Select data set **A**. Set Period to **Year**.

**Expected** — every row's *Period End* equals the next row's *Period Start* (no gaps, no
overlaps); cycle numbers run consecutively with no missing number; newest cycle first; the oldest
row is `#1` and its Period Start matches when the membership began.
**Result:** ☐ Pass ☐ Fail

### 5.3 Paid cycles show their invoice
1. Same data set.

**Expected** — each past cycle reads `Paid`, shows the real invoice number, and shows the paid
date under Paid / Failed On. Amount matches the invoice total.
**Result:** ☐ Pass ☐ Fail

### 5.4 Dunning-cancelled membership
1. Select data set **B**. Period = **Year**.

**Expected** — paid cycles read `Paid`; declined cycles read `Payment Failed` with the decline
reason in Notes; **no rows exist after the cancellation date** — there must be no tail of phantom
`Not generated` rows for cycles that would have happened had the membership continued.
**Result:** ☐ Pass ☐ Fail

### 5.5 Missing invoice is flagged — the core case
1. Select data set **C**.

**Expected** — the gap cycle reads **`Not generated`** with Notes "no invoice found for this
cycle". The cycles either side still read `Paid`. This is the ticket's primary requirement.
**Result:** ☐ Pass ☐ Fail

### 5.6 Voided / uncollectible invoices
1. Find a membership whose Stripe invoice was voided or marked uncollectible.

**Expected** — `Voided` or `Cancelled` respectively. On a dunning-cancelled membership, a
Cancelled row also carries "membership cancelled for non-payment" in Notes.
**Known limitation** — there is no `invoice.voided` webhook handler, so an invoice voided directly
in the Stripe dashboard may still read `Pending` here until an upsert re-runs. Record it, but this
is not a report defect.
**Result:** ☐ Pass ☐ Fail

### 5.7 Trial cycles are not false anomalies
1. Select data set **D**.

**Expected** — cycles inside the trial read `Trial` with "free trial to …" in Notes, **not**
`Not generated`.
**Result:** ☐ Pass ☐ Fail

### 5.8 Free memberships are not false anomalies
1. Select data set **E**.

**Expected** — cycles read `Free — no invoice`, not `Not generated`.
**Result:** ☐ Pass ☐ Fail

### 5.9 Paused cycles
1. Select data set **F**.

**Expected** — the covered cycle reads `Paused`, Notes shows "membership paused from …".
**Result:** ☐ Pass ☐ Fail

### 5.10 Invoice-at-period-end timing
1. Select data set **G** (period still open).

**Expected** — the in-flight cycle reads `Upcoming`, because its invoice is not due until the
period closes — **not** `Not generated`. For a normal invoice-in-advance membership the same
in-flight cycle would already be flagged. This distinction is the test.
**Result:** ☐ Pass ☐ Fail

### 5.11 One-time / package memberships
1. Select data set **H**.

**Expected** — exactly **one** lifetime row, not a repeating series. Period End runs to end-of-day
on the expiry date.
**Result:** ☐ Pass ☐ Fail

### 5.12 A cycle with two invoices
1. Select data set **I**.

**Expected** — both invoice numbers listed under Invoice #, comma separated; Amount is the **sum**
of the two fee invoices, not just the first.
**Result:** ☐ Pass ☐ Fail

### 5.13 Interval coverage
1. Repeat 5.2 for weekly, fortnightly, every_2_months, every_3_months and yearly plans.

**Expected** — cycle length always matches the plan's own billing interval; boundaries stay
back-to-back across month-length and year changes.
**Result:** ☐ Pass ☐ Fail

### 5.14 Only one future cycle
1. Any active recurring membership, Period = Year.

**Expected** — exactly **one** `Upcoming` row at the top. The report must not project further into
the future.
**Result:** ☐ Pass ☐ Fail

### 5.15 Date column discipline
1. Scan a table containing a mix of statuses.

**Expected** — Paid / Failed On is filled **only** on `Paid` and `Payment Failed` rows. Every
other row shows `-` there and carries its date in Notes instead.
**Result:** ☐ Pass ☐ Fail

---

## 6. Filters, export and volume

### 6.1 Patient filter
Select a patient. **Expected** — only that patient's memberships; filter persists while changing
the date range. (This picker appears on this report only.)
**Result:** ☐ Pass ☐ Fail

### 6.2 Date range bounds the rows
Switch Period between Month / Quarter / Year. **Expected** — only cycles overlapping the range are
listed; cycle numbers do **not** renumber.
**Result:** ☐ Pass ☐ Fail

### 6.3 Membership plan filter
Select a plan. **Expected** — only memberships on that plan.
**Result:** ☐ Pass ☐ Fail

### 6.4 CSV export
Click Export CSV. **Expected** — file downloads; rows, columns and values match the table exactly,
including blank Paid / Failed On cells. (No PDF export on membership reports — correct.)
**Result:** ☐ Pass ☐ Fail

### 6.5 Volume
Clear the patient filter, Period = Year, on a clinic with many memberships. **Expected** — table
paginates and stays responsive; no timeout.
**Result:** ☐ Pass ☐ Fail

---

## 7. Regression checks — must not break

### 7.1 The other six membership reports are untouched
Open statusBreakdown, popularity, revenue, cancellations, pausedOverTime, tenure. In the browser
network tab, confirm they still render from **one shared** `subReportType=all` call, and that
`billingCycles` does **not** appear inside that response.
**Result:** ☐ Pass ☐ Fail

### 7.2 Report categories
`GET /report/categories` lists `billingCycles` in the membership category's `subReportTypes`. The
frontend visibility gate depends on this.
**Result:** ☐ Pass ☐ Fail

### 7.3 CSV behaviour elsewhere
CSV still streams for all seven membership reports; `subReportType=all` still returns 400 for CSV.
**Result:** ☐ Pass ☐ Fail

### 7.4 Membership billing flows
Purchase, renewal, payment failure and dunning cancellation all behave as before. Run:

```bash
npm run test:payment-failure
```

Plus `webhook.paymentFailure.selfHeal.test.ts` and `webhook.dunningCancellation.test.ts`.
**Result:** ☐ Pass ☐ Fail

### 7.5 New Stripe period fields
Trigger a membership invoice in Stripe test mode. **Expected** — the new invoice document carries
`stripePeriodStart` / `stripePeriodEnd`; all existing fields unchanged; re-upserting a payload
without period data does **not** wipe a previously stamped period.
**Result:** ☐ Pass ☐ Fail

### 7.6 Existing invoices untouched
Spot-check invoices created before this release. **Expected** — unchanged; they simply have no
period fields, and the report falls back to date-window matching for them.
**Result:** ☐ Pass ☐ Fail

---

## 8. Known limitations

Record these if seen; they are accepted behaviour, not defects.

1. **No backfill.** `stripePeriodStart` / `stripePeriodEnd` are only stamped on invoices mirrored
   after this release. Older invoices match by `invoice.date` window — accurate to the cycle, but
   not to the instant.
2. **No `invoice.voided` webhook.** A void performed in the Stripe dashboard may not reach the
   local record until some other upsert re-runs (see 5.6).
3. **Plan changes mid-life.** If a membership's billing interval changed partway through, cycle
   numbering for the older cycles is approximate — enumeration steps backwards using the *current*
   interval.
4. **`Pending` on old cycles may be mirror drift** rather than genuinely unpaid — if a
   `payment_succeeded` webhook never applied, the invoice reads Pending locally while Stripe shows
   it paid. Worth raising if a Pending row sits between Paid rows.

---

## 9. Automated test baselines

| Command | Expected |
|---|---|
| `npm run test:membership-billing-report` | 27 / 27 pass |
| `npx tsx --test src/app/report/*.test.ts` | 55 / 55 pass |
| `npx tsx --test src/app/class/membership/*.test.ts` | **195 pass / 26 fail** — this is the clean-HEAD baseline, *not* a regression. Compare counts; do not read the 26 as new failures |

`npx tsc --noEmit` reports a large pre-existing error count repo-wide. Grep the output for the
changed files only; there should be none.

---

## 10. Sign-off

| | Name | Date | Result |
|---|---|---|---|
| QA | | | ☐ Pass ☐ Fail |
| Dev | | | |
| Product / client | | | ☐ Accepted |

**Defects raised:**

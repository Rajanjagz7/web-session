# QA Test Plan: Membership Coverage Linker (Pre-existing Bookings Get Covered)

- **Asana Ticket**: [1218609910353060](https://app.asana.com/0/1218609910353060)
- **Project**: ActiveRx (Clinic Backend)
- **Branch**: `dev`
- **Scope**: Backend only (`membershipCoverageLink.service.ts`, `classMembership.service.ts`, `appointment.controller.ts`, migration `20260925_link_preexisting_bookings_to_memberships`)

---

## 🎯 Executive Summary & Architectural Seams

### The Problem Solved
Previously, bookings were matched to a membership only once at the moment of booking creation. Standing weekly series booked before membership purchase remained `$99 Pending`, never consumed allowances, and failed to generate health-fund itemised claim invoices.

### The 3 Runtime Seams & Backfill

| Seam | Trigger Location | Window Evaluated |
|---|---|---|
| **1. Activation** | `classMembership.service.ts` → `linkExistingBookingsAfterMembershipChange` | Current paid window |
| **2. Window Move** | `handleStripeSubscriptionEvent` (after `membership.save()`) | New paid window |
| **3. Delivery Safety Net** | `appointment.controller.ts` (`updateAppointmentStatus` / `completeAppointment`) | Current paid window |
| **4. Backfill Migration** | `migration 20260925_link_preexisting_bookings_to_memberships` | Closed periods with Paid fee invoice + Current |

---

## 🛡️ Guard Conditions (When Bookings Are Left Alone)

| Guard Code | Reason / Behavior |
|---|---|
| `already_covered` | Already has an active row in `membershipusages`. |
| `covered_without_usage` | Snapshot indicates covered but no usage row: **Adopted** (usage row written, never re-priced) if membership is live, price is $0, and allowance has room. Otherwise logged and skipped. |
| `already_paid` | Already paid via card/cash or refunded. No retro-discount or auto-refund. |
| `invoice_not_voidable` / `invoice_has_payments` | Carries a live manual invoice. Blocks auto-link (requires staff manual void). |
| `cancelled` / `no_show` / `rescheduled` | Inactive appointment statuses. |
| Engine Declines | Appointment type not included in plan, location mismatch, or allowance exhausted. |
| `outside_paid_period` | (Backfill only) Service date is outside any paid subscription period. |

---

## 📋 Comprehensive 10-Scenario Manual & Automated Test Matrix

### Test 1: Activation Links Existing Bookings & Delivery Gate
- **Preconditions**:
  - Plan configured: Recurring weekly plan "2 × 30 min / week" with Private item code.
  - Patient has 0 active memberships.
- **Steps**:
  1. Book 2 sessions of the included appointment type for **this week** (e.g., Tuesday & Thursday).
  2. Verify initial state: Both sessions are `$99 Pending`.
  3. Purchase / assign the weekly plan for the patient.
  4. Verify database & UI:
     - Both sessions become `$0 Paid`.
     - `membershipDiscountSnapshot.eligible = true`.
     - Exactly 2 rows written to `membershipusages`.
     - Patient usage tile displays `2/2`.
     - **Delivery Gate Check**: Ensure **NO** invoice is created yet.
  5. Transition appointment status of Session 1 to `Arrived` (or `Completed`).
- **Expected Results**:
  - Item invoice is now generated.
  - Item invoice PDF contains: **Item Code**, **Member Number**, and **Provider Number**.

---

### Test 2: Allowance Respected (Earliest First)
- **Steps**:
  1. Book **3 sessions** of the included type for **this week** (Mon 9am, Wed 10am, Fri 2pm) before buying the plan.
  2. Purchase the "2 × 30 min / week" plan.
- **Expected Results**:
  - The **two earliest** sessions (Mon & Wed) become `$0 Paid` and linked.
  - The third session (Fri) remains `$99 Pending`.
  - Backend log confirms: `allowance_exhausted` for the third candidate.

---

### Test 3: Beyond Paid Window Stays Untouched Until Renewal
- **Steps**:
  1. Book Session A for **this week** and Session B for **next week**.
  2. Buy the plan.
  3. Verify Session A links immediately, while Session B stays `$99 Pending` (outside current paid window).
  4. Advance Stripe Test Clock past renewal:
     - Stripe triggers `customer.subscription.updated`.
  5. Check backend logs and database.
- **Expected Results**:
  - Log output: `[MembershipCoverageLink] renewed`.
  - Session B is now retroactively covered ($0 Paid with usage row).

---

### Test 4: Delivery Safety Net (Late Link on Arrival)
- **Steps**:
  1. Book a session for this week.
  2. Activate plan with activation link hook disabled (or use patient activated prior to deploy).
  3. Booking remains unlinked.
  4. Mark the appointment `Arrived` via calendar / receptionist UI.
- **Expected Results**:
  - `appointment.controller.ts` triggers coverage link immediately prior to delivery seam.
  - Session links to membership and item invoice is generated in one atomic step.

---

### Test 5: Card-Paid Stays Card-Paid (No Auto-Refund)
- **Steps**:
  1. Book a session and pay by credit card ($99 Paid).
  2. Buy the plan for the patient.
- **Expected Results**:
  - Session remains `$99 Paid`.
  - No refund is issued to the card.
  - No usage row is created for this session.

---

### Test 6: Live Manual Invoice Blocks Auto-Link
- **Steps**:
  1. Book a session ($99 Pending).
  2. Manually generate an invoice on the appointment.
  3. Buy the plan for the patient.
- **Expected Results**:
  - Auto-linker skips the booking (`invoice_not_voidable`).
  - Booking remains unchanged unless staff manually retro-applies with void.

---

### Test 7: Un-Pause Window Boundary
- **Steps**:
  1. Pause active subscription.
  2. Book Session X dated inside the paused duration.
  3. Resume subscription.
  4. Book Session Y dated in the new active period.
- **Expected Results**:
  - Session X (in paused span) is **NOT** covered.
  - Session Y (in active period) **IS** covered.

---

### Test 8: Multiple Memberships (Free Plan Priority)
- **Steps**:
  1. Assign a Free/Complimentary membership to patient.
  2. Purchase a Paid membership covering the same appointment type.
  3. Book an included appointment.
- **Expected Results**:
  - Engine links against the **Free** membership first based on default engine hierarchy.

---

### Test 9: Class Enrolments
- **Steps**:
  1. Enrol patient in an included group class (e.g. Reformer Pilates) before membership purchase.
  2. Activate plan.
  3. Check-in patient to class.
- **Expected Results**:
  - Enrolment is linked on activation.
  - Class item invoice is generated upon check-in.

---

### Test 10: Backfill Migration Validation
- **Dry-run Execution**:
  ```bash
  MIGRATION_CLINIC_IDS=<clinicId> npm run migrate:dry-run -- --only 20260925_link_preexisting_bookings_to_memberships
  ```
- **Validation**:
  - Check reported metrics:
    - `patientsWithLiveMembership`
    - `candidates`
    - `wouldLink`
    - `adopted`
    - `skipped_already_covered`, `skipped_already_paid`, etc.
- **Live Run Execution**:
  ```bash
  MIGRATION_CLINIC_IDS=<clinicId> npm run migrate -- --only 20260925_link_preexisting_bookings_to_memberships
  ```

---

## 🏃 Automated Test Runner

To execute the ActiveRx automated verification suite:

```bash
cd clinic1
npx playwright test tests/api/membership-coverage-linker.spec.js
```

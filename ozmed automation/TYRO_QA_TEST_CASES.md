# Tyro / Invoice / Payments — QA Test Cases

End-to-end QA test suite for the billing system: **invoices, Tyro card checkout, health-fund claims, payments, refunds, reimbursements, and webhook processing.**

> **How to use:** Execute in order within each section. Each case has Preconditions → Steps → Expected Result. Record **Pass/Fail** + notes in the *Result* column (or copy this into Excel/Sheets — the tables paste cleanly, or import the companion `TYRO_QA_TEST_CASES.csv`).

---

## Legend & reference data

**Funders** (`FUNDERS`): `medicare` (Medicare), `dva` (DVA), `private` (Private), `comcare`, `icare`, `wcq` (WorkCover QLD), `wsv` (WorkSafe VIC), `healthpoint`.

**Invoice statuses**: `draft`, `issued`, `partiallyPaid`, `paid`, `partiallyRefunded`, `refunded`, `cancelled`, plus Tyro-claim lifecycle `outstanding`, `approved`, `completed`.

**Payment status**: `pending`, `processing`, `paid`, `failed`, `refunded`, `partiallyRefunded`, `cancelled`.
**Payment source**: `card_checkout`, `funder_claim`, `manual`, `refund`, `reimbursement`.

**Key endpoints**
| Action | Method + Path |
|---|---|
| Create invoice | `POST /invoice` |
| Get / list invoices | `GET /invoice/:id` · `GET /invoice` |
| Update / cancel invoice | `PUT /invoice/:id` · `POST /invoice/:id/cancel` |
| Invoice PDF | `GET /invoice/:id/pdf` |
| Refund invoice | `POST /invoice/:id/refund` |
| Reimburse (funder overpayment) | `POST /invoice/:id/reimburse` |
| Tyro claim payload | `GET /tyro/claim-payload/:invoiceId` |
| Create checkout (card) | `POST /tyro/checkout/:invoiceId` |
| Checkout status (advisory) | `GET /tyro/checkout/:transactionId/status` |
| Tyro webhook (inbound) | `POST /tyro/healthFunder/webhook?clinicDomain=<domain>` |
| Record manual payment | `POST /payment` |
| List payments | `GET /payment?invoice=:invoiceId` |

**Priority**: P1 = critical/money-path, P2 = important, P3 = edge/cosmetic.

---

## 0. Preconditions / environment

| ID | Setup | Expected |
|---|---|---|
| ENV-01 | Clinic DB reachable; webhook URL registered with `?clinicDomain=<domain>` | Webhooks resolve to the correct clinic DB |
| ENV-02 | Tyro API key configured (clinic `tyroApiKey` or env fallback) | Checkout + refund API calls succeed |
| ENV-03 | Payment collection has the partial-unique index `{ invoice, tyroTransactionId }` | `db.payments.getIndexes()` shows it (duplicate-webhook guard is live) |
| ENV-04 | A patient exists with health details (Medicare #, DVA card, private membership as needed) | Claim payloads populate patient identifiers |
| ENV-05 | Appointment(s) exist with an appointment type + fee | Invoice can be created from appointments |

---

## 1. Invoice lifecycle

| ID | Title | Preconditions | Steps | Expected Result | P | Result |
|---|---|---|---|---|---|---|
| INV-01 | Create invoice from appointment(s) | Appointment with fee $X | `POST /invoice` with appointment lines | Invoice created; `total` = Σ fees (− discount + surcharge + tax); status `issued`; `isPaid:false`; `invoiceNumber` = `INV-XXXXXX` (sequential) | P1 | |
| INV-02 | Invoice number is sequential & unique | ≥1 invoice exists | Create two invoices | Numbers increment from the highest existing (no gaps cause collisions); both unique | P1 | |
| INV-03 | Multi-appointment invoice shows all appointment types | Invoice with 2 appts of different types | `GET /payment?invoice=:id` after payment | `appointmentTypes[]` on each payment lists both type names (deduped) | P2 | |
| INV-04 | Update invoice | Draft/issued invoice | `PUT /invoice/:id` change a line | Total recomputed; audit log records the change (old→new) | P2 | |
| INV-05 | Cancel invoice | Issued, unpaid | `POST /invoice/:id/cancel` | Status `cancelled`; cannot be paid afterwards | P1 | |
| INV-06 | Cancel a paid invoice is blocked | Paid invoice | `POST /invoice/:id/cancel` | Rejected (paid invoices keep their state) | P2 | |
| INV-07 | Invoice PDF renders | Any invoice | `GET /invoice/:id/pdf` | PDF returns; Medicare rebate / gap / outstanding derived from claim mirror + ledger; falls back to $0/"Standard" when no claim | P2 | |
| INV-08 | Appointment status reflects payment | Invoice paid in full | — | Linked appointment(s) `paymentStatus` → `paid`; on refund → `refunded` | P2 | |

---

## 2. Tyro card checkout (patient pays by card / Apple Pay / Google Pay)

| ID | Title | Preconditions | Steps | Expected Result | P | Result |
|---|---|---|---|---|---|---|
| CO-01 | Create checkout for full outstanding | Issued invoice, total $100, nothing paid | `POST /tyro/checkout/:invoiceId` (no amount) | Returns `paymentRequestURL`; charge amount = full outstanding $100 | P1 | |
| CO-02 | Create checkout for partial amount | Same, $100 outstanding | `POST /tyro/checkout/:invoiceId` amount=$40 | Charge = $40 (part-payment allowed, capped at outstanding) | P1 | |
| CO-03 | Checkout amount cannot exceed outstanding | $100 outstanding | Request amount=$150 | Rejected: "exceeds the invoice outstanding balance" | P1 | |
| CO-04 | Checkout amount must be > 0 | Any | Request amount=0 or negative | Rejected: "must be greater than zero" | P2 | |
| CO-05 | Checkout on fully-paid invoice | Invoice already paid | `POST /tyro/checkout/:invoiceId` (no amount) | Rejected: "no outstanding balance to charge" | P1 | |
| CO-06 | **Successful card payment records ONE payment** | Checkout created, patient completes card payment | Complete payment in Tyro modal → webhooks fire | Exactly **one** `paid` payment row (source `card_checkout`); invoice → `paid`, `isPaid:true`; appointment → `paid`; receipt `RCP-XXXXXX` generated | P1 | |
| CO-07 | Partial card payment leaves balance | $100 invoice, pay $40 | Complete $40 payment | Payment $40; invoice `partiallyPaid`; outstanding now $60 | P1 | |
| CO-08 | Checkout status endpoint is advisory only | Payment completed | `GET /tyro/checkout/:transactionId/status` | Returns Tyro status; **true** paid state comes from the webhook (`GET /invoice/:id`) | P3 | |

---

## 3. Health-fund claims (Medicare / DVA / Private / Workers-comp)

| ID | Title | Preconditions | Steps | Expected Result | P | Result |
|---|---|---|---|---|---|---|
| CL-01 | Build Medicare claim payload — **bulk-billed** | Invoice NOT paid | `GET /tyro/claim-payload/:invoiceId?funder=medicare` | Payload `funder=medicare`, `funderData.medicare.isBulkBilled=true` (patient pays nothing, benefit to provider); patient Medicare # + IRN populated | P1 | |
| CL-02 | Medicare claim — **patient claim** after payment | Invoice already paid by patient | Same call | `isBulkBilled=false` (benefit reimbursed to patient/claimant) | P1 | |
| CL-03 | DVA claim payload | Patient has DVA veteran card | `?funder=dva` | `accountNumber` = veteran card number, `reference` = card type | P2 | |
| CL-04 | Private claim payload | Patient has private membership | `?funder=private` | `accountNumber` = membership number | P2 | |
| CL-05 | Workers-comp funder payload | — | `?funder=comcare` (or icare/wcq/wsv) | `accountNumber`/`reference` blank (staff enter claim # in Tyro popup); no `funderData` key | P2 | |
| CL-06 | Invalid funder rejected | — | `?funder=xyz` | Rejected: "Invalid funder … Expected one of: …" | P2 | |
| CL-07 | Claim approved reduces patient outstanding | Claim submitted, funder approves part | `healthFundApprovedInvoice` webhook | Voucher recorded per claim; invoice outstanding reduced by approved benefit; gap (if any) remains payable | P1 | |
| CL-08 | Claim rejected notifies patient | Claim submitted | `healthFundRejectedInvoice` webhook | Patient notified claim couldn't be processed; a voucher/record still tracks the rejection; outstanding unchanged | P2 | |
| CL-09 | Claim settled records funder_claim payment | Claim completes | `invoiceCompleted`/`healthFundPaidInvoice` (businessStatus `completed`) | One `paid` payment (source `funder_claim`) for the benefit; never a $0 row | P1 | |
| CL-10 | Gap payment link after benefit | Benefit applied, gap remains | Claim settles with a gap | Patient emailed a gap-payment link | P2 | |
| CL-11 | Claim-only ($0 patient) completion | Full bulk-bill, patient pays nothing | Completion with only claim benefit | Appointments synced to paid via safety net; no $0 payment row created | P2 | |

---

## 4. Webhook processing & idempotency  *(critical — money path)*

| ID | Title | Preconditions | Steps | Expected Result | P | Result |
|---|---|---|---|---|---|---|
| WH-01 | invoiceCreated mirrors invoice | — | Send `invoiceCreated` | `tyroInvoice` mirror stored; linked invoice → `outstanding` (unless ledger-owned) | P2 | |
| WH-02 | Every webhook is audited | — | Send any event | A `tyroWebhookEvent` row written **before** processing (`received`), flipped to `processed`/`failed`/`ignored` after | P2 | |
| WH-03 | Duplicate invoiceCreated ignored | Mirror already exists | Resend `invoiceCreated` (same transactionId) | Second one ignored (no throw, no dup mirror) | P2 | |
| WH-04 | **Concurrent "completed" webhooks → ONE payment** | Checkout completed | Tyro fires `invoiceCompleted` + `paymentApproved` + `healthFundPaidInvoice` near-simultaneously | **Exactly one** settlement payment; the `{invoice,tyroTransactionId}` unique index makes duplicates fail `E11000`, caught and reconciled (**not** a 2nd row) | **P1** | |
| WH-05 | Repeated completed webhook reconciles, not duplicates | Payment already recorded | Resend `invoiceCompleted` | Existing payment amount reconciled to authoritative value; no new row | P1 | |
| WH-06 | Unknown event ignored | — | Send unrecognised `event` | Marked `ignored`; no side effects | P3 | |
| WH-07 | Missing clinicDomain rejected | — | Webhook without `?clinicDomain=` | 400 "Missing clinic domain" | P2 | |
| WH-08 | Cancelled/deleted events map status | Active mirror | Send `invoiceCancelled` / `medipassDeletedInvoice` | Invoice status maps to `cancelled` (unless ledger-owned); ledger not touched | P2 | |
| WH-09 | Webhook auth enforced | — | POST without valid `x-tyro-webhook-secret` | Rejected by `tyroWebhookAuth` | P1 | |

---

## 5. Payments & receipts

| ID | Title | Preconditions | Steps | Expected Result | P | Result |
|---|---|---|---|---|---|---|
| PAY-01 | Manual payment recorded | Issued invoice | `POST /payment` {invoice, amount, method} | Payment `paid`; invoice reconciled; appointment synced | P1 | |
| PAY-02 | **Receipt number derives from max, not count** | Payments with gaps exist (e.g. deletions left `RCP-000012, 014, 021, 023`) | Create a new payment | Receipt = **max+1** (`RCP-000024`), NOT `count+1` — **no E11000 collision** | **P1** | |
| PAY-03 | Payments list populates details | Payments on an invoice | `GET /payment?invoice=:id` | `patient` + `invoice` populated; `appointmentTypes[]` present | P2 | |
| PAY-04 | Overpayment flags reimbursement | Patient paid in full, then funder benefit settles | Funder benefit webhook | Invoice `reimbursement.status=pending`, `dueAmount` = overpaid amount | P1 | |
| PAY-05 | Ledger outstanding math | Total $1440, paid $37.85, no refunds | `POST /tyro/checkout/:id` | Outstanding = `1440 − (37.85 − reimbursed − refunded)` = $1402.15 | P1 | |

---

## 6. Refunds

| ID | Title | Preconditions | Steps | Expected Result | P | Result |
|---|---|---|---|---|---|---|
| REF-01 | Full card refund | Paid card payment $100 | `POST /invoice/:id/refund` full | Tyro card refund issued **first**; on success a `refunded` payment (source `refund`) recorded; invoice → `refunded` | P1 | |
| REF-02 | Partial refund | Paid $100 | Refund $40 | `partiallyRefunded` payment $40; invoice `partiallyRefunded`; outstanding re-opens by $40 | P1 | |
| REF-03 | Genuine refund re-opens balance & blocks mirror | Refund exists on invoice | `POST /tyro/checkout/:id` again | Outstanding INCREASES by refund; Tyro mirror is **ignored** while local refunds exist (stale mirror can't wipe the re-owed balance) | **P1** | |
| REF-04 | Refund only after Tyro success | Tyro refund API fails | Attempt refund | No ledger row written (refund recorded **only** on Tyro success) | P1 | |
| REF-05 | Refund target resolution | No card payment to refund against | Attempt refund | Rejected: refund target not found | P2 | |

---

## 7. Reimbursement (funder over-contribution returned to patient)

| ID | Title | Preconditions | Steps | Expected Result | P | Result |
|---|---|---|---|---|---|---|
| RB-01 | Reimburse pending overpayment | `reimbursement.status=pending`, dueAmount $30 | `POST /invoice/:id/reimburse` | Card refund of $30 to patient via Tyro; a `refunded` payment tagged `isFunderReimbursement:true` (source `reimbursement`); reimbursement → `completed` | P1 | |
| RB-02 | Reimbursement does NOT re-open balance | After RB-01 | `GET /invoice/:id` | Invoice stays `paid` (reimbursement is netted against paid, not a genuine refund) | P1 | |
| RB-03 | Partial reimbursement | dueAmount $30 | Reimburse $20 | $10 remains `pending`; invoice still `paid` | P2 | |
| RB-04 | No reimbursement due | reimbursement not pending | `POST /invoice/:id/reimburse` | Rejected: no reimbursement due | P2 | |

---

## 8. Outstanding balance — ledger + Tyro mirror  *(edge math)*

| ID | Title | Preconditions | Steps | Expected Result | P | Result |
|---|---|---|---|---|---|---|
| OUT-01 | Mirror reduces for unsettled approved claim | Ledger outstanding $1402.15; Tyro mirror covers full invoice, outstanding lower | Create checkout | Outstanding reduced to the mirror value (catches approved-but-unsettled claim) | P1 | |
| OUT-02 | **Partial Tyro claim can't wipe non-Tyro balance** | Invoice $1440; Tyro only processed $37.85 slice; mirror outstanding $1 | Create checkout | Outstanding stays ~$1402.15 (mirror value + untouched `total − charged` added back) — patient is **not** undercharged to $1 | **P1** | |
| OUT-03 | Mirror never increases outstanding | Mirror outstanding > ledger | Create checkout | `Math.min` keeps the ledger value; mirror only ever lowers | P2 | |
| OUT-04 | Latest mirror used | Multiple mirror records | Create checkout | Newest by `updatedAt` chosen | P3 | |

---

## 9. Regression checklist (bugs fixed — must stay fixed)

| ID | Scenario | Expected | P |
|---|---|---|---|
| REG-01 | Two `completed` webhooks race on one checkout | Only **one** payment row (WH-04) | P1 |
| REG-02 | Create payment after rows were deleted (gapped receipts) | New receipt = max+1, insert succeeds, payment recorded (PAY-02) | P1 |
| REG-03 | Partial Tyro claim ($37.85 of $1440), mirror says $1 outstanding | Patient charged ~$1402.15, not $1 (OUT-02) | P1 |
| REG-04 | Genuine refund present + stale Tyro mirror | Mirror ignored; balance correctly re-owed (REF-03) | P1 |
| REG-05 | Any non-dedup `E11000` during settlement | Payment NOT silently dropped — surfaced/failed, retried by Tyro | P1 |
| REG-06 | Full checkout webhook (single) | Payment created + invoice paid + appointment paid + receipt generated | P1 |

---

## 10. Suggested end-to-end scenarios (happy-path smoke)

1. **Card-only:** Create invoice $100 → checkout full → complete → invoice `paid`, 1 payment, receipt, appointment `paid`.
2. **Bulk-bill Medicare:** Unpaid invoice → Medicare claim (bulk-billed) → approved → completed → funder_claim payment, patient owes $0.
3. **Claim + gap:** Invoice $150, Medicare benefit $100 → funder_claim payment $100, gap $50 → patient pays $50 by card → `paid`.
4. **Overpay then reimburse:** Patient pays $150 by card → funder benefit $100 settles → reimbursement pending $100 → reimburse → refund to patient, invoice stays `paid`.
5. **Refund:** Paid $100 invoice → refund $100 → invoice `refunded`, appointment `refunded`.

---

### Sign-off

| Area | Total | Pass | Fail | Notes |
|---|---|---|---|---|
| Invoice lifecycle | | | | |
| Card checkout | | | | |
| Health-fund claims | | | | |
| Webhooks/idempotency | | | | |
| Payments/receipts | | | | |
| Refunds | | | | |
| Reimbursement | | | | |
| Outstanding math | | | | |
| Regression | | | | |

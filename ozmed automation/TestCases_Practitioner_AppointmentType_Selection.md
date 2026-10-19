# Test Cases — Practitioner & Appointment Type Selection (Duration > 20 min)

**Module:** Appointments
**Screen:** Add Appointment modal (Step 1 — Appointment info)
**App:** OzMed (practice2.dev.ozmed.health)

**Scenario under test:** On the Appointments screen, select a practitioner.
If the selected practitioner has no appointment types available, select a
different practitioner. The appointment type chosen must have a duration
greater than 20 minutes.

**Reference data observed during exploration:**
| Practitioner | Appointment Types Available |
|---|---|
| Liam Martin Amelia | 0 (none) |
| Olivia Brown | Surcharge on Sydney (4 mins), Multidisciplinary Case Review Note (45 mins), Rehabilitation Progress Summary (26 mins), Pain Management Note (43 mins), Mental Health Care Plan Note (21 mins), Initial Dental Assessment (33 mins), General Consultation 2 (50 mins) |

---

### TC_APT_01 — Select a practitioner that has appointment types
**Preconditions:** Logged in; on Appointments screen; date already selected in the Add Appointment modal.
**Steps:**
1. Click the Practitioner field.
2. Select a practitioner from the dropdown (e.g. "Olivia Brown").
**Expected Result:** Practitioner is set; an "Appointment Type" field appears below it.
**Priority:** High

---

### TC_APT_02 — Practitioner with zero appointment types prompts selecting another
**Preconditions:** Date selected in modal.
**Steps:**
1. Select a practitioner known/likely to have no appointment types (e.g. "Liam Martin Amelia").
2. Open the Appointment Type dropdown.
**Expected Result:** Appointment Type dropdown shows 0 options (empty list). No appointment type can be selected for this practitioner.
**Priority:** High

---

### TC_APT_03 — Switching to another practitioner after a zero-type practitioner
**Preconditions:** TC_APT_02 just executed (zero-type practitioner selected).
**Steps:**
1. Clear/reopen the Practitioner field.
2. Select a different practitioner (e.g. "Olivia Brown").
3. Open the Appointment Type dropdown.
**Expected Result:** Appointment Type dropdown now shows one or more options. Previous practitioner's empty state does not block re-selection.
**Priority:** High

---

### TC_APT_04 — Appointment type list displays duration per option
**Preconditions:** A practitioner with appointment types is selected.
**Steps:**
1. Open the Appointment Type dropdown.
**Expected Result:** Each option's label includes its duration in minutes, e.g. "Mental Health Care Plan Note (21 mins)".
**Priority:** Medium

---

### TC_APT_05 — Select an appointment type with duration > 20 minutes (positive)
**Preconditions:** Practitioner with appointment types selected (e.g. "Olivia Brown").
**Steps:**
1. Open Appointment Type dropdown.
2. Select an option whose duration is greater than 20 minutes (e.g. "Mental Health Care Plan Note (21 mins)" or "General Consultation 2 (50 mins)").
**Expected Result:** Appointment type is accepted; a "Practitioner Availability" panel appears below with bookable slots sized to that duration.
**Priority:** High

---

### TC_APT_06 — Reject/avoid appointment type with duration ≤ 20 minutes
**Preconditions:** Practitioner with appointment types selected, including at least one ≤ 20 min option (e.g. "Surcharge on Sydney (4 mins)").
**Steps:**
1. Open Appointment Type dropdown.
2. Attempt to select "Surcharge on Sydney (4 mins)".
**Expected Result (business rule under test):** Per the scenario's requirement, this type should be excluded from selection by the test/automation logic — it does not satisfy "duration > 20 minutes". (The UI itself does not block this selection; the exclusion is a test-data selection rule, not a UI validation.)
**Priority:** High

---

### TC_APT_07 — Boundary: exactly 20 minutes does not qualify
**Preconditions:** A practitioner has an appointment type with exactly 20 minutes duration (synthetic/boundary case — none observed in current data set).
**Steps:**
1. Open Appointment Type dropdown.
2. Locate an option with exactly "(20 mins)".
**Expected Result:** This option must NOT be selected, since the requirement is strictly "more than 20 minutes" (20 is not > 20).
**Priority:** Medium (boundary)

---

### TC_APT_08 — Boundary: 21 minutes qualifies
**Preconditions:** Practitioner "Olivia Brown" selected.
**Steps:**
1. Open Appointment Type dropdown.
2. Select "Mental Health Care Plan Note (21 mins)".
**Expected Result:** Selection succeeds and is treated as valid (21 > 20).
**Priority:** Medium (boundary)

---

### TC_APT_09 — Practitioner has appointment types, but none exceed 20 minutes
**Preconditions:** A practitioner whose appointment types are all ≤ 20 minutes (synthetic scenario; construct via filtering or test data if such a practitioner exists).
**Steps:**
1. Select that practitioner.
2. Inspect all Appointment Type options' durations.
**Expected Result:** None qualify; test logic should move on and try the next practitioner in the list, same as the zero-types case (TC_APT_02/03).
**Priority:** High

---

### TC_APT_10 — No practitioner in the list has a qualifying appointment type
**Preconditions:** Hypothetical/negative scenario — all practitioners have either zero types or only types ≤ 20 minutes.
**Steps:**
1. Iterate through every practitioner in the dropdown, checking Appointment Type durations for each.
**Expected Result:** No valid practitioner + appointment-type combination found. The flow should stop and report a clear failure rather than silently proceeding (e.g. "No practitioner with an appointment type over 20 minutes was found").
**Priority:** Medium

---

### TC_APT_11 — Next button blocked without a valid appointment type
**Preconditions:** Practitioner selected, no Appointment Type selected yet.
**Steps:**
1. Click "Next" without selecting an Appointment Type.
**Expected Result:** Validation error "Appointment Type is required!" is shown; modal stays on Step 1 (Appointment info).
**Priority:** High

---

### TC_APT_12 — Date is a prerequisite for the Practitioner field
**Preconditions:** Add Appointment modal freshly opened (only Date + Concern fields visible).
**Steps:**
1. Without picking a date, look for the Practitioner field.
**Expected Result:** Practitioner field is not present until a date is selected. After selecting any enabled date, the Practitioner field appears.
**Priority:** Medium

---

### TC_APT_13 — End-to-end: qualifying practitioner + appointment type books successfully
**Preconditions:** Logged in, on Appointments screen, an existing patient available to attach.
**Steps:**
1. Open "Book Appointment".
2. Pick any open date.
3. Select a practitioner; if it has no appointment types, select the next practitioner in the list, repeating until one with appointment types is found.
4. From that practitioner's Appointment Type list, select the first option whose duration is **> 20 minutes**. If none qualify for this practitioner, return to step 3 and try the next practitioner.
5. Select the first available time slot shown under "Practitioner Availability".
6. Fill in a Concern.
7. Click Next.
8. Search for and select an existing patient.
9. Click Submit.
**Expected Result:** Appointment is created and appears in the Appointments table with the correct practitioner, the selected appointment type (duration > 20 min), date, and a "Scheduled" status.
**Priority:** Critical

---

### TC_APT_15 — No open slot today rolls forward to the next available day
**Preconditions:** A qualifying practitioner + appointment type (>20 min) exists, but every slot for today is already booked/unavailable.
**Steps:**
1. Select a practitioner and an appointment type with duration > 20 minutes.
2. Observe the "Practitioner Availability" panel shows no bookable slots for the selected (today's) date.
3. Re-open the date picker and advance to the next day; if still no slot, advance to the day after that.
4. Repeat until an open slot is found (bounded — e.g. try up to 3–4 days forward before failing).
**Expected Result:** The flow does not give up after the first date — it keeps advancing day by day until it finds a qualifying practitioner + appointment type (>20 min) with an actual open slot, then proceeds normally to Concern/Next/Patient selection/Submit.
**Priority:** High

---

### TC_APT_14 — Practitioner re-selection does not duplicate or corrupt Appointment Type field
**Preconditions:** A zero-type practitioner was selected first, then switched to a valid one.
**Steps:**
1. Select zero-type practitioner ("Liam Martin Amelia").
2. Switch to a valid practitioner ("Olivia Brown").
3. Select a qualifying appointment type and a slot.
4. Click Next.
**Expected Result:** Step 1 validates successfully and advances to Step 2 (Patient info) — confirms no leftover/stale state from the discarded first practitioner selection blocks progress.
**Priority:** Medium

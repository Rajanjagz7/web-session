# RebateM8 NSW — Staging bug report

**Environment:** https://nswstage.rebatem8.com.au (web admin portal)
**Login:** Master Admin account
**Tested:** 23–24 Sep 2026, headless Chromium (Playwright)
**Evidence:** screenshots and logs in the QA folder `nsw-qa\`

---

## A. Confirmed bugs

| # | Severity | Area | Bug | Steps to reproduce | Expected | Actual |
|---|---|---|---|---|---|---|
| 1 | High | Dashboard | All 6 dashboard widget APIs return **404** | Log in → Dashboard | Widgets load data | `GET /api/v1/dashboard/job-count`, `/job-breakdown`, `/job-rebate`, `/job-tracking`, `/top-product`, `/avg-complete-time` all return 404 |
| 2 | High | Projects | Projects list API returns **404** | Sidebar → Projects | Project list loads | `GET /api/v1/site/list` → 404 |
| 3 | High | Invoices | Invoices list API returns **404** | Sidebar → Invoices | Invoice list loads | `GET /api/v1/invoice/list` → 404 |
| 4 | Medium | Installers | Installer filter API returns **404** | Open Dashboard/Jobs installer filter | Filter options load | `GET /api/v1/installer/filter/list` → 404 |
| 5 | Medium | Navigation / permissions | **Exception Logs** menu shown to Master Admin but opens `/access-denied` | Sidebar → Exception Logs | Page opens, or menu hidden for this role | Redirects to `/access-denied` |
| 6 | Low | Navigation | **CMS** menu item opens the Privacy Policy page | Sidebar → CMS | CMS content list | Lands on `/privacypolicy` |
| 7 | Medium | Auth | `GET /api/v1/auth/me` returns **401** on the first page load right after a successful login | Log in → Jobs → click Add Job | 200 | 401 on first call (reproduced several times); later calls succeed |
| 8 | High | Add Job wizard | Pressing **Esc** while a dropdown is open closes the **whole Add Job drawer** and discards everything entered, with no confirmation | Add Job → type a Customer Name → open Activity Type dropdown → press Esc | Only the dropdown closes | Entire drawer closes; entered data is lost |
| 9 | Medium | Add Job wizard | Changing **Building Type** to *Small Business Site* silently wipes the Customer Name / Phone / Email already entered | Add Job → fill Customer Name, Phone, Email → Building Type = Small Business Site | Data kept, or a warning shown | Customer fields are replaced by Business Name + Authorised Signatory fields; typed values are lost without warning |

## A2. Job module edge cases — new bugs (24 Sep)

| # | Severity | Bug | Steps to reproduce | Expected | Actual | Evidence |
|---|---|---|---|---|---|---|
| 13 | **High** | An impossible Installation Date is **silently replaced with today's date** | Add Job → valid Residential job → Installation Date `29-02-2027` (2027 is not a leap year) or `31-04-2027` (April has 30 days) → Send | Validation error | Job created; Installation Date stored as **24/09/2026** (the submission date). No error shown | Jobs M8N000110, M8N000114 |
| 14 | **High** | **ABN/ACN checksum is not validated** — any 11 digits are accepted | Add Job → ABN/ACN `12345678901` (fails the ATO checksum) → Send | "Invalid ABN" | Job created | Job M8N000105 |
| 15 | Medium | A **valid ABN typed with spaces** is rejected, and cut down to 8 digits | ABN/ACN `33 102 417 032` (the format shown on ABN Lookup) → Send | Spaces stripped, accepted | The field keeps only `33102417` (the 11-character limit counts spaces), then shows "ABN/ACN must be exactly 11 digits" | Screenshot `edge-E02.png` |
| 16 | Medium | **Invalid emails pass the form's own check**, then fail on the server with an error that doesn't name the field | Customer Email `name@yopmail` (no domain ending) or `name..surname@yopmail.com` (double dot) → Send | Inline "Enter a valid email" on the Email field | No inline error. The server rejects it with the toast "Error — Failed to send engagement letter". No job is created (checked) | Screenshot `edge-E03.png` |
| 17 | Low | Job search does not trim spaces | Jobs search: `  M8N000078  ` (spaces around it) | Finds the job | "No Data Found" | — |
| 18 | Low | Job search is accent-sensitive | Search `Siobhan` when the customer is `Siobhán` | Finds the job | "No Data Found" | Job M8N000109 |
| 19 | Low | Searching only a special character returns **every** job | Search `%`, `'`, `(`, `*` or `\` | "No Data Found" | Full, unfiltered job list | — |

**Need a PO decision (accepted today):**
- An NSW landline (`02 9876 5432`) is accepted as the Customer Phone and shown as `+61 298765432`. Is a mobile required for the engagement SMS? (M8N000107)
- A single-character customer name (`J`) is accepted. (M8N000108)
- An email with a trailing space is accepted. Whether it is trimmed on save was not checked. (M8N000106)

**Edge cases that passed (no bug):**
- Name with apostrophe, hyphen and accents (`Siobhán O'Brien-Nguyễn`) is saved and displayed correctly.
- Leap-day date `29-02-2028` is accepted.
- A blank second product is blocked with field errors.
- Double-clicking Send creates only one job.
- Partial-word and lowercase job-ID searches work.
- No server (5xx) errors appeared during any of these tests.

## A3. Job module — round 2 (field formats + state changes)

| # | Severity | Bug | Steps to reproduce | Expected | Actual | Evidence |
|---|---|---|---|---|---|---|
| 20 | **High** | Customer phone typed with a **leading 0 is saved as `+61 0412…`** (invalid Australian format) | Add Job → Customer Phone `0412247248` → Send | Leading 0 dropped (`+61 412 247 248`), or rejected like other lengths | Job created showing **+61 0412247248**. The "must be 9 digits" rule is not applied to 10-digit numbers starting with 0. Existing data has the same problem (Installer User Belinda Baker +61 0414062547; jobs M8N000075–77), so SMS delivery to these numbers is at risk | Job M8N000113 |
| 21 | **High** | The **site-inspection installer list goes stale** when the Installer (Company) is changed, so another company's staff can be assigned | Add Job → Installer = BAWA → "Name of Installer Attended Site Inspection" = Belinda Baker → change Installer to **Owl HVAC Services** → open the inspection-installer list | Owl HVAC Services' installers (15 people, shown correctly when Owl is chosen first) | The selection is cleared, but the list still offers only **Belinda Baker**, who is not an Owl HVAC member (her companies: NSW Energies, Belinda Testing, Belinda HVAC NSW, Belinda Test Co, BAWA) | Screenshot `edge2-F09.png` |
| 22 | Low | A phone number pasted with **+61** is rejected | Customer Phone `+61413247248` | Normalised to 9 digits and accepted | "Phone number must be 9 digits for Australia" | Screenshot `edge2-F02.png` |
| 23 | Low | **Reloading the page with unsaved Add Job data** gives no warning | Add Job → type a Customer Name → refresh the browser | "You have unsaved changes" prompt | Data silently lost (same family as #8) | — |

**Need a PO decision:**
- An Installation Date of **01-01-2099** is accepted. Should there be a maximum? (M8N000115)
- Switching Activity Type after products are filled clears the products without telling the user. The reset itself is correct (air-conditioner models don't apply to Hot Water), but a notice would help.

**Checked and working correctly:**
- Heating/Cooling Capacity and Warranty Period strip minus signs and letters.
- Cooling Capacity above 65 kW is blocked ("Cooling Capacity Must be under 65 kW").
- Changing the Model updates the auto-filled capacities.
- Changing the Installer clears the previously chosen inspection installer (but see #21 for the stale list).

## A4. Job module — round 3 (job list, filters, job detail)

| # | Severity | Bug | Steps to reproduce | Expected | Actual | Evidence |
|---|---|---|---|---|---|---|
| 24 | **High** | **5 of the 6 job-list tabs show no jobs** — the API rejects the status each tab sends | Sidebar → Jobs → **In Progress**, **Action Required**, **Being Assessed**, **Completed** or **Archived** | Jobs in that stage | "No Data Found". Each tab calls `GET /api/v1/jobs?status=<value>` and gets **400 "Invalid status value"**. The tabs send `Install In Progress`, `Action Required`, `Being Assessed`, `Complete` and `Archived`. Even `Archived`, which is a valid option in the All Jobs status filter, is rejected, so the tabs and the filter must be sending status differently. Only the **All** tab works | API responses captured |
| 25 | Medium | **Audit Checklist** tab on a job returns 404 | Open job M8N000071 (Photos Started) → Audit Checklist tab | Checklist loads | `GET /api/v1/audit/checklist?jobId=…` → **404** | — |

**Checked and working correctly:**
- The All Jobs **Status** filter returns only jobs with the chosen status (tested with Nomination Signed; 22 status options).
- Site address search is **limited to NSW**: "88 Bourke Street Melbourne" gets 0 suggestions and "88 Bourke Street Surry Hills" gets 3.
- The job detail header shows the correct Job ID.
- Blank-submit with Manual Address mode lists every required field.

## A5. Field-by-field scenario matrix (66 scenarios, 7 fields)

Each value was entered into one field only, with the rest of the form left blank, so no jobs were created. The full table is in `field_matrix.md`. These results show only what the form itself checks; server-side checks are covered in A2–A4.

| # | Severity | Bug | Evidence (typed → field holds → message) |
|---|---|---|---|
| 26 | Medium | The **ABN/ACN field rejects a valid 9-digit ACN**, even though it is labelled ABN/ACN | `004085616` → "ABN/ACN must be exactly 11 digits" |
| 27 | Medium | **Postcode is not validated for NSW, or at all beyond length.** It accepts VIC, QLD and non-existent postcodes, with no check against the NSW-only site address | `3000` (VIC), `4000` (QLD), `0000` → accepted, no message |
| 28 | Medium | **Installation Date has no validation in the form.** The mask even accepts letters. Combined with #13, any of these is saved as today's date | `ab-cd-efgh`, `15/12/2026`, `1-1-2027`, `15-13-2026`, `00-01-2027`, `15-12-1900` → all accepted, no message |
| 29 | Low | Customer Phone accepts numbers that can't be a mobile | `000000000` → `+61 (00) 0000 000`, accepted |
| 30 | Low | **No length or content limits** on free-text fields | Customer Name and Own Reference accept 258 characters; names made only of digits (`12345`), emoji or HTML (`<b>Olivia</b>`) are accepted; an email local part of 65+ characters (the limit is 64) is accepted |
| 31 | Low | **Input is silently truncated** instead of showing an error | ABN `331024170321` (12 digits) → keeps `33102417032`; Postcode `20000` → keeps `2000` |

**Update to #15:** an ABN typed with spaces isn't just rejected, it's **cut down to 8 digits** (`33 102 417 032` → `33102417`), because the 11-character limit counts the spaces.

**Checked and working correctly:**
- Spaces-only names count as empty.
- Emails: surrounding spaces are trimmed and `+alias` is accepted. Missing @, missing local part, missing domain and a space inside all show "Enter a valid email".
- Phone: spaces, dashes and letters are stripped; 8- and 10-digit numbers show "must be 9 digits".
- Postcode: 3 digits shows "must be exactly 4 digits".
- ABN: 10 digits is rejected and letters are stripped.

## A6. Round 4: Small Business, products, duplicates, search, URLs (38 scenarios)

Full defect cards for #32–#37 are in `NSW_BUGS.md` / `NSW_BUGS.csv`.

| # | Severity | Bug | Evidence |
|---|---|---|---|
| 32 | Medium | **Duplicate job accepted** for the same customer, site address and installer, with no warning (risk of a duplicate rebate claim) | M8N000121 duplicates M8N000078 |
| 33 | Low | Job search finds nothing by address, installer, activity type, or the phone as displayed (`+61 412987654`) | `George St`, `BAWA`, `Heating & Cooling` → No Data Found |
| 34 | Low | A non-existent job URL shows a generic "Something went Wrong"; the API returns 400 instead of 404 | `/jobs/M8N999999`, `/jobs/not-a-job` |
| 35 | Medium | **Capacity fields silently strip `,` and `e`**, changing the value tenfold | `5,5` → `55` kW; `1e3` → `13` |
| 36 | Low | Heating Capacity has no maximum (Cooling is capped under 65 kW); both accept 0 | Heating `65.01` and `0` accepted |
| 37 | Low | Warranty Period accepts 0, decimals and 9999, with no unit shown | `0`, `1.5`, `9999` accepted |

**Existing bugs extended to the Small Business signatory fields:**
- #16: an email with no TLD passes.
- #20: a phone with a leading 0 passes as `+61 (04)…`.
- #30: a 260-character Business Name and digit-only names are accepted.

**Checked and working correctly:**
- Spaces-only Small Business fields count as empty.
- Signatory email with no @ and signatory phone with 8 digits are rejected.
- A Brand without a Model is blocked ("Model is required").
- Cooling Capacity of 65 or more is blocked.
- Add and Remove Product work; 7+ products are allowed. *PO: should there be a cap?*
- Clicking outside the drawer does not close it.
- After logout, both Back and a direct `/jobs` redirect to sign-in, and no tokens are left in storage.
- `/job-details/<id>` shows Access Denied.
- Search by email, phone digits, surname, lower-case or partial job ID, and own reference works.

**Need a PO decision:** two identical products (same brand and model) on one job were accepted (M8N000122).

## B. Behaviour changes vs dev — need Product/PO confirmation

| # | Area | Dev | Staging | Question |
|---|---|---|---|---|
| 10 | Add Job validation (Residential) | ABN/ACN, Own Reference and Installation Date were **required** | All three are **optional** (no error on blank submit) | Intended? (ABN/ACN is still required for Small Business Sites) |
| 11 | Installation Date | — | A past date (28-08-2026) was accepted and the job created | Should past installation dates be blocked? |
| 12 | Add Job form | Field placeholders and options differ from dev (email/phone placeholders, Lead Method list, Original Equipment options, new "Name of Installer Attended Site Inspection" field, Small Business signatory fields) | — | Confirm dev will receive the same redesign, so the automation suite can target one version |

## C. Observations (not bugs)

- The **Send Engagement Letter & Fact Sheet** button stays enabled on an empty form. Clicking it correctly shows every "… is required" error and creates nothing.
- For Small Business Sites a generic toast ("Not able to Save. Complete mandatory fields") appears. The inline field errors are also shown, so this is acceptable.
- The Site Assessor Declaration can only be signed by the installer. The admin portal has no override, so an admin-only test cannot move a job past "Site Assessment and Nomination Requested".

## D. Previously logged bugs — not re-verified on staging

BUG-02 (Save doesn't persist after sign), BUG-04 (OTP request 500 for a real number), BUG-07 (duplicate serial numbers allowed) and BUG-08 (notes visibility default) come from the existing suite. The post-sign tests could not run on staging: the signed job used (M8N000074) showed no product list on its Products tab. These need a known signed staging job to re-check.

## E. Test run summary (staging)

- Existing automated suite: **64 cases → 51 passed, 13 failed.**
- Most of the 13 failures were **automation out of date** after the staging redesign (renamed labels, new fields, different dropdown options), not product defects. Those test fixes are in progress.
- Auth (API + UI login, OTP): 7/7 passed.

## F. Test data created on staging (for cleanup)

- **M8N000078** — Harrison Doyle / BAWA. Created manually, currently at *Site Assessment and Nomination Requested*.
- **M8N000105–M8N000122**: jobs created by the edge-case tests above (M8N000121 Harrison Doyle duplicate, M8N000122 Lachlan Pierce)
- **M8N000079 onwards** — jobs created by the automated runs (valid cases such as Olivia Bennett and Ava Thompson, plus edge-case jobs with special characters or long input).
- All emails use `@yopmail.com` addresses.

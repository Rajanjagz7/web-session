# RebateM8 NSW - Staging defects

**Environment:** Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium  
**Tested:** 23–25 Sep 2026 (Round 9: edit-capability check + test-data cleanup); regression pass 30 Sep 2026  
**Total:** 60 tracked - 54 open, 6 fixed

| ID | Title | Module | Severity | Priority | Regression (30 Sep) |
|---|---|---|---|---|---|
| NSW-STG-01 | Dashboard widgets fail to load - all 6 dashboard APIs return 404 | Dashboard | High | P1 | Open |
| NSW-STG-02 | Projects page does not load - site/list API returns 404 | Projects | High | P1 | Open |
| NSW-STG-03 | Invoices page does not load - invoice/list API returns 404 | Invoices | High | P1 | Open |
| NSW-STG-04 | Installer filter has no options - installer/filter/list returns 404 | Installers / Filters | Medium | P2 | Open |
| NSW-STG-05 | Exception Logs menu opens Access Denied for Master Admin | Navigation / Permissions | Medium | P2 | Open |
| NSW-STG-06 | CMS menu item opens the Privacy Policy page | Navigation | Low | P3 | Open |
| NSW-STG-07 | auth/me returns 401 on first page load right after login | Authentication | Medium | P2 | Fixed |
| NSW-STG-08 | Pressing Esc in any dropdown closes the whole Add Job drawer and loses all data | Add Job | High | P1 | Open |
| NSW-STG-09 | Choosing Building Type 'Small Business Site' wipes the customer details already entered | Add Job | Medium | P2 | Open |
| NSW-STG-13 | Impossible Installation Date is silently saved as today's date | Add Job | High | P1 | Open |
| NSW-STG-14 | ABN/ACN checksum not validated - any 11 digits accepted | Add Job | High | P1 | Open |
| NSW-STG-15 | Valid ABN typed with spaces is rejected and cut to 8 digits | Add Job | Medium | P2 | Open |
| NSW-STG-16 | Invalid emails pass inline validation, then fail with a generic server error | Add Job | Medium | P2 | Open |
| NSW-STG-17 | Job search does not trim leading/trailing spaces | Jobs list | Low | P3 | Open |
| NSW-STG-18 | Job search is accent-sensitive | Jobs list | Low | P3 | Open |
| NSW-STG-19 | Searching a single special character returns every job | Jobs list | Low | P3 | Fixed |
| NSW-STG-20 | Phone typed with leading 0 is saved as '+61 0412…' | Add Job | High | P1 | Fixed |
| NSW-STG-21 | Site-inspection installer list goes stale after changing Installer (Company) | Add Job | High | P1 | Skipped |
| NSW-STG-22 | Phone pasted with +61 prefix is rejected | Add Job | Low | P3 | Fixed |
| NSW-STG-23 | No unsaved-changes warning when reloading with Add Job data | Add Job | Low | P3 | Open |
| NSW-STG-24 | 5 of 6 job-list tabs show no jobs - API returns 400 'Invalid status value' | Jobs list | High | P1 | Open |
| NSW-STG-25 | Audit Checklist tab returns 404 | Job detail | Medium | P2 | Open |
| NSW-STG-26 | ABN/ACN field rejects a valid 9-digit ACN | Add Job | Medium | P2 | Open |
| NSW-STG-27 | Postcode not validated for NSW - VIC/QLD/0000 accepted | Add Job | Medium | P2 | Open |
| NSW-STG-28 | Installation Date has no client-side validation (letters, month 13, day 00, 1900) | Add Job | Medium | P2 | Open |
| NSW-STG-29 | Customer Phone accepts 000000000 | Add Job | Low | P3 | Open |
| NSW-STG-30 | No length or content limits on free-text fields | Add Job | Low | P3 | Open |
| NSW-STG-31 | Over-length input is silently truncated instead of rejected | Add Job | Low | P3 | Open |
| NSW-STG-32 | Duplicate job accepted for the same customer, site address and installer - no warning | Add Job | Medium | P2 | Open |
| NSW-STG-33 | Job search ignores address, installer, activity type and the phone as displayed | Jobs list | Low | P3 | Inconclusive |
| NSW-STG-34 | Opening a non-existent job URL shows a generic 'Something went Wrong' | Job detail | Low | P3 | Open |
| NSW-STG-35 | Capacity fields silently strip ',' and 'e', changing the value (5,5 → 55 kW) | Add Job - Products | Medium | P2 | Open |
| NSW-STG-36 | Heating Capacity has no upper limit (Cooling is capped at 65 kW) and both accept 0 | Add Job - Products | Low | P3 | Open |
| NSW-STG-37 | Warranty Period accepts 0, decimals and 9999 with no unit shown | Add Job - Products | Low | P3 | Open |
| NSW-STG-38 | Access token still works after logout | Authentication / Security | High | P1 | Fixed |
| NSW-STG-39 | Refresh token is not rotated - an old refresh token stays reusable | Authentication / Security | Medium | P2 | Open |
| NSW-STG-40 | No throttling on admin login - unlimited password attempts | Authentication / Security | Medium | P2 | Open |
| NSW-STG-41 | Malformed installer ID returns 500 Internal Server Error | Installers API | Medium | P2 | Open |
| NSW-STG-42 | Rebates page does not load - rebate/installer/list API returns 404 | Rebates | High | P1 | Open |
| NSW-STG-43 | Street names starting with 'The' are split wrongly (10 The Corso → name 'The', type 'Corso') | Add Job - Site Address | Medium | P2 | Not re-verified |
| NSW-STG-44 | Admin login accepts a form-encoded body (login-CSRF surface) | Authentication / Security | Low | P3 | Open |
| NSW-STG-45 | Web app sends no Content-Security-Policy header | Security headers | Low | P3 | Open |
| NSW-STG-46 | Product Brand list has duplicate brands that differ only by letter case | Add Job - Products | Low | P3 | Fixed |
| NSW-STG-47 | 'Model is required' shows as soon as a Brand is picked, before the user reaches Model | Add Job - Products | Low | P3 | Open |
| NSW-STG-48 | Installers list silently accepts invalid paging (negative, zero, text) | Installers API | Low | P3 | Open |
| NSW-STG-49 | Invalid sortType is ignored and treated as 'desc' | List APIs | Low | P3 | Open |
| NSW-STG-50 | Members of a non-existent installer returns 200 with an empty list | Installers API | Low | P3 | Open |
| NSW-STG-51 | Two job-number formats in use (M800001–M800047 and M8N000xxx) | Jobs - data | Low | P3 | Info |
| NSW-STG-52 | Login fails with a generic error when the email has leading/trailing spaces | Authentication | Low | P3 | Open |
| NSW-STG-53 | Stored XSS in Job Notes - HTML is saved and rendered unsanitised | Job Notes / Security | Critical | P1 | Open |
| NSW-STG-54 | Installers list ignores an unrecognised status filter instead of rejecting or matching nothing | Installers API | Medium | P2 | Open |
| NSW-STG-55 | Notes accepts empty-looking content ('<p></p>') as if it had text | Job Notes | Low | P3 | Open |
| NSW-STG-56 | Whitespace-only customer name crashes job creation with 500 Internal Server Error | Jobs API | High | P1 | Open |
| NSW-STG-57 | Malformed JSON request bodies return 500 instead of 400 on every write endpoint tested | API / Security | High | P1 | Open |
| NSW-STG-58 | Postcode has no format or NSW-range validation at the API level | Jobs API | Medium | P2 | Open |
| NSW-STG-59 | ABN/ACN is not validated at the API level - any string is accepted | Jobs API | High | P1 | Open |
| NSW-STG-60 | Phone number format is not enforced at the API level | Jobs API | Medium | P2 | Open |
| NSW-STG-61 | Installation date accepts impossible calendar dates and any date range at the API level | Jobs API | Medium | P2 | Open |
| NSW-STG-62 | Product capacity fields accept negative values and any magnitude at the API level | Jobs API - Products | Low | P3 | Open |
| NSW-STG-63 | Job editing is non-functional everywhere - Save never sends a request | Job Information / Products / Post Install Details / Add Job wizard | Critical | P1 | Open |

---

### NSW-STG-01: Dashboard widgets fail to load - all 6 dashboard APIs return 404

| | |
|---|---|
| **Module** | Dashboard |
| **Severity** | High |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. Log in
2. Open Dashboard

**Expected result:** All widgets load data

**Actual result:** Widgets stay empty. GET /api/v1/dashboard/job-count, /job-breakdown, /job-rebate, /job-tracking, /top-product and /avg-complete-time all return 404

**Evidence / test data:** Network log (api_inventory.json)

**Regression check (30 Sep 2026):** GET /dashboard/job-count still 404.

---

### NSW-STG-02: Projects page does not load - site/list API returns 404

| | |
|---|---|
| **Module** | Projects |
| **Severity** | High |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. Sidebar → Projects

**Expected result:** Project list loads

**Actual result:** Empty page. GET /api/v1/site/list → 404

**Evidence / test data:** Network log

**Regression check (30 Sep 2026):** GET /site/list still 404.

---

### NSW-STG-03: Invoices page does not load - invoice/list API returns 404

| | |
|---|---|
| **Module** | Invoices |
| **Severity** | High |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. Sidebar → Invoices

**Expected result:** Invoice list loads

**Actual result:** Empty page. GET /api/v1/invoice/list → 404

**Evidence / test data:** Network log

**Regression check (30 Sep 2026):** GET /invoice/list still 404.

---

### NSW-STG-04: Installer filter has no options - installer/filter/list returns 404

| | |
|---|---|
| **Module** | Installers / Filters |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. Open Dashboard or Jobs
2. Open the Installer filter

**Expected result:** Installer options load

**Actual result:** No options. GET /api/v1/installer/filter/list → 404

**Evidence / test data:** Network log

**Regression check (30 Sep 2026):** GET /installer/filter/list still 404.

---

### NSW-STG-05: Exception Logs menu opens Access Denied for Master Admin

| | |
|---|---|
| **Module** | Navigation / Permissions |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. Sidebar → Exception Logs

**Expected result:** Page opens, or the menu is hidden for this role

**Actual result:** Redirects to /access-denied

**Evidence / test data:** —

**Regression check (30 Sep 2026):** Exception Logs still redirects to /access-denied for Master Admin.

---

### NSW-STG-06: CMS menu item opens the Privacy Policy page

| | |
|---|---|
| **Module** | Navigation |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. Sidebar → CMS

**Expected result:** CMS content list opens

**Actual result:** Lands on /privacypolicy

**Evidence / test data:** —

**Regression check (30 Sep 2026):** CMS still lands on /privacypolicy.

---

### NSW-STG-07: auth/me returns 401 on first page load right after login

| | |
|---|---|
| **Module** | Authentication |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Fixed |

**Precondition:** Logged out

**Steps to reproduce:**
1. Log in
2. Go to Jobs
3. Click Add Job

**Expected result:** GET /api/v1/auth/me returns 200

**Actual result:** First call returns 401 (reproduced several times); later calls succeed

**Evidence / test data:** Network log

**Regression check (30 Sep 2026):** First GET /auth/me right after login now returns 200, not 401.

---

### NSW-STG-08: Pressing Esc in any dropdown closes the whole Add Job drawer and loses all data

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | High |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. Type a Customer Name
2. Open the Activity Type dropdown
3. Press Esc

**Expected result:** Only the dropdown closes

**Actual result:** Entire drawer closes, all entered data lost, no confirmation

**Evidence / test data:** —

**Regression check (30 Sep 2026):** Esc in the Activity Type dropdown still closes the whole drawer.

---

### NSW-STG-09: Choosing Building Type 'Small Business Site' wipes the customer details already entered

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. Fill Customer Name, Phone, Email
2. Set Building Type = Small Business Site

**Expected result:** Data kept, or a warning before it is cleared

**Actual result:** Customer fields replaced by Business Name + Authorised Signatory fields; typed values lost silently

**Evidence / test data:** smallbiz-after-submit.png

**Regression check (30 Sep 2026):** Switching to Small Business Site still discards the Customer Name field.

---

### NSW-STG-13: Impossible Installation Date is silently saved as today's date

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | High |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. Fill a valid Residential job
2. Installation Date = 29-02-2027 (not a leap year) or 31-04-2027
3. Click Send

**Expected result:** Validation error on Installation Date

**Actual result:** Job created; Installation Date stored as 24/09/2026 (submission date). No error shown

**Evidence / test data:** Jobs M8N000110, M8N000114

**Regression check (30 Sep 2026):** installationDate=2027-02-29 still accepted (201), same root cause as #61.

---

### NSW-STG-14: ABN/ACN checksum not validated - any 11 digits accepted

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | High |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. Fill a valid job
2. ABN/ACN = 12345678901 (fails ATO checksum)
3. Click Send

**Expected result:** 'Invalid ABN' error

**Actual result:** Job created

**Evidence / test data:** Job M8N000105

**Regression check (30 Sep 2026):** abnAcn=12345678901 (bad checksum) still accepted (201), same root cause as #59.

---

### NSW-STG-15: Valid ABN typed with spaces is rejected and cut to 8 digits

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. ABN/ACN = 33 102 417 032 (format shown on ABN Lookup)
2. Click Send

**Expected result:** Spaces stripped and ABN accepted

**Actual result:** Field keeps only 33102417 (11-char limit counts spaces), then 'ABN/ACN must be exactly 11 digits'

**Evidence / test data:** edge-E02.png

**Regression check (30 Sep 2026):** ABN '33 102 417 032' still cut to '33102417' by the input mask.

---

### NSW-STG-16: Invalid emails pass inline validation, then fail with a generic server error

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. Fill a valid job
2. Customer Email = name@yopmail (no TLD) or name..surname@yopmail.com
3. Click Send

**Expected result:** Inline 'Enter a valid email' on the Email field

**Actual result:** No inline error; toast 'Error — Failed to send engagement letter' that doesn't name the field. No job created. Same gap on the Small Business 'Authorised Signatory Email Address' (grace@yopmail passes)

**Evidence / test data:** edge-E03.png

**Regression check (30 Sep 2026):** Email 'name@yopmail' (no TLD) still passes inline validation with no error shown.

---

### NSW-STG-17: Job search does not trim leading/trailing spaces

| | |
|---|---|
| **Module** | Jobs list |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in → Jobs

**Steps to reproduce:**
1. Search '  M8N000078  ' (spaces around it)

**Expected result:** Job found

**Actual result:** 'No Data Found'

**Evidence / test data:** —

**Regression check (30 Sep 2026):** Search with surrounding spaces still returns 'No Data Found' (re-tested on 2 different live job numbers).

---

### NSW-STG-18: Job search is accent-sensitive

| | |
|---|---|
| **Module** | Jobs list |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Job M8N000109 exists for customer 'Siobhán'

**Steps to reproduce:**
1. Search 'Siobhan'

**Expected result:** Job found

**Actual result:** 'No Data Found'

**Evidence / test data:** Job M8N000109

**Regression check (30 Sep 2026):** Search 'Siobhan' still finds nothing while the accented 'Siobhán' finds the record - confirmed accent-sensitive.

---

### NSW-STG-19: Searching a single special character returns every job

| | |
|---|---|
| **Module** | Jobs list |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Fixed |

**Precondition:** Logged in → Jobs

**Steps to reproduce:**
1. Search %, ', (, * or \

**Expected result:** 'No Data Found'

**Actual result:** Full unfiltered job list shown

**Evidence / test data:** —

**Regression check (30 Sep 2026):** Search '%' now returns 1 result instead of the full unfiltered list.

---

### NSW-STG-20: Phone typed with leading 0 is saved as '+61 0412…'

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | High |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Fixed |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. Fill a valid job
2. Customer Phone = 0412247248
3. Click Send

**Expected result:** Leading 0 dropped (+61 412 247 248) or rejected

**Actual result:** Job saved with +61 0412247248; 9-digit rule not applied. Existing data affected too (Belinda Baker, M8N000075–77) - SMS delivery at risk. Same on Small Business 'Authorised Signatory Phone Number' (0412398765 → +61 (04) 1239 8765, no error)

**Evidence / test data:** Job M8N000113

**Regression check (30 Sep 2026):** Phone '0412247248' (leading 0) no longer saved as typed - UI now normalises it.

---

### NSW-STG-21: Site-inspection installer list goes stale after changing Installer (Company)

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | High |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Skipped |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. Installer = BAWA
2. Name of Installer Attended Site Inspection = Belinda Baker
3. Change Installer to Owl HVAC Services
4. Open the inspection-installer list

**Expected result:** Owl HVAC Services' 15 installers listed

**Actual result:** Selection clears but list still offers only Belinda Baker (not an Owl HVAC member) - wrong company's staff can be assigned

**Evidence / test data:** edge2-F09.png

**Regression check (30 Sep 2026):** Reproducing this needs switching between two real installer companies (e.g. BAWA/Owl HVAC), which conflicts with the test-installer-only rule. Needs a manual check or an explicit one-off exception.

---

### NSW-STG-22: Phone pasted with +61 prefix is rejected

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Fixed |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. Customer Phone = +61413247248

**Expected result:** Normalised to 9 digits and accepted

**Actual result:** 'Phone number must be 9 digits for Australia'

**Evidence / test data:** edge2-F02.png

**Regression check (30 Sep 2026):** Phone pasted with '+61' prefix is no longer rejected.

---

### NSW-STG-23: No unsaved-changes warning when reloading with Add Job data

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. Type a Customer Name
2. Refresh the browser

**Expected result:** 'You have unsaved changes' prompt

**Actual result:** Data silently lost

**Evidence / test data:** —

**Regression check (30 Sep 2026):** Reloading after typing a Customer Name still shows no native unsaved-changes prompt.

---

### NSW-STG-24: 5 of 6 job-list tabs show no jobs - API returns 400 'Invalid status value'

| | |
|---|---|
| **Module** | Jobs list |
| **Severity** | High |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in; jobs exist in several statuses

**Steps to reproduce:**
1. Sidebar → Jobs
2. Open In Progress / Action Required / Being Assessed / Completed / Archived tabs

**Expected result:** Jobs in that stage are listed

**Actual result:** 'No Data Found'. GET /api/v1/jobs?status=<Install In Progress|Action Required|Being Assessed|Complete|Archived> → 400. Only 'All' works. Cause (API test): the filter only accepts the status keys from statusList (e.g. nomination_signed); the tabs send display labels

**Evidence / test data:** Network log (job_edge_3.txt)

**Regression check (30 Sep 2026):** All 5 non-'All' status tabs still return 400 'Invalid status value'.

---

### NSW-STG-25: Audit Checklist tab returns 404

| | |
|---|---|
| **Module** | Job detail |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Job M8N000071 at Photos Started

**Steps to reproduce:**
1. Open job M8N000071
2. Click Audit Checklist tab

**Expected result:** Checklist loads

**Actual result:** GET /api/v1/audit/checklist?jobId=… → 404

**Evidence / test data:** Network log

**Regression check (30 Sep 2026):** GET /audit/checklist?jobId=... still 404.

---

### NSW-STG-26: ABN/ACN field rejects a valid 9-digit ACN

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. ABN/ACN = 004085616
2. Click Send

**Expected result:** ACN accepted (field is labelled ABN/ACN)

**Actual result:** 'ABN/ACN must be exactly 11 digits'

**Evidence / test data:** field_matrix.md

**Regression check (30 Sep 2026):** A valid 9-digit ACN ('004085616') still triggers 'ABN/ACN must be exactly 11 digits'.

---

### NSW-STG-27: Postcode not validated for NSW - VIC/QLD/0000 accepted

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. Postcode = 3000, 4000 or 0000
2. Click Send

**Expected result:** Error: NSW postcode required (2000–2999) and must match the site address

**Actual result:** Accepted with no message

**Evidence / test data:** field_matrix.md

**Regression check (30 Sep 2026):** Postcode '3000' (VIC) still accepted with no NSW-range error.

---

### NSW-STG-28: Installation Date has no client-side validation (letters, month 13, day 00, 1900)

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. Installation Date = ab-cd-efgh, 15/12/2026, 1-1-2027, 15-13-2026, 00-01-2027 or 15-12-1900
2. Click Send

**Expected result:** Inline date error

**Actual result:** Accepted with no message; with #13 they are saved as today's date

**Evidence / test data:** field_matrix.md

**Regression check (30 Sep 2026):** Date '31-04-2027' (no such day) still accepted with no inline error.

---

### NSW-STG-29: Customer Phone accepts 000000000

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. Customer Phone = 000000000

**Expected result:** Invalid-number error

**Actual result:** Shown as +61 (00) 0000 000, accepted

**Evidence / test data:** field_matrix.md

**Regression check (30 Sep 2026):** Phone '000000000' still accepted and displayed as '+61 (00) 0000 000'.

---

### NSW-STG-30: No length or content limits on free-text fields

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. Customer Name / Own Reference = 258 characters, digits only (12345), emoji or <b>Olivia</b>
2. Customer Email with a 65+ character local part

**Expected result:** Max length (e.g. 100) and name character rules; email local part ≤ 64

**Actual result:** All accepted. Same on Small Business fields: 260-char Business Name, digits-only signatory names (12345 / 67890) and Position '99'

**Evidence / test data:** field_matrix.md, job_edge_4b.txt H01

**Regression check (30 Sep 2026):** Own Reference still accepts 258 characters with no length cap in the UI (server does cap at 100 - see the Round 8 correction note above).

---

### NSW-STG-31: Over-length input is silently truncated instead of rejected

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. ABN/ACN = 331024170321 (12 digits)
2. Postcode = 20000

**Expected result:** Error shown

**Actual result:** Silently cut to 33102417032 and 2000

**Evidence / test data:** field_matrix.md

**Regression check (30 Sep 2026):** Not independently re-tested this pass - same UI field as #30, which is still open; no evidence the truncation behaviour changed.

---

### NSW-STG-32: Duplicate job accepted for the same customer, site address and installer - no warning

| | |
|---|---|
| **Module** | Add Job |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Job M8N000078 exists: Harrison Doyle, harrison.doyle@yopmail.com, +61 412987654, 1 George St Sydney 2000, BAWA

**Steps to reproduce:**
1. Add Job with the same name, email, phone, site address, installer and activity type
2. Click Send

**Expected result:** Warning that an open job already exists for this customer/site (risk of a duplicate rebate claim), or a block

**Actual result:** Second job M8N000121 created silently; both appear in the list

**Evidence / test data:** Jobs M8N000078, M8N000121 (job_edge_4.txt H07)

**Regression check (30 Sep 2026):** A second job with identical customer/site/installer/activity is still accepted silently (201) with no duplicate warning.

---

### NSW-STG-33: Job search ignores address, installer, activity type and the phone as displayed

| | |
|---|---|
| **Module** | Jobs list |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Inconclusive |

**Precondition:** Logged in → Jobs; job M8N000078 exists

**Steps to reproduce:**
1. Search 'George St', 'BAWA', 'Heating & Cooling' or '+61 412987654'

**Expected result:** Matching jobs listed (these values are shown in the list columns)

**Actual result:** 'No Data Found' for all four. Name, email, phone digits, job ID and own reference do match

**Evidence / test data:** job_edge_4.txt H10

**Regression check (30 Sep 2026):** No live jobs currently match 'George St' / 'BAWA' / 'Heating & Cooling' as search terms, so the API returned 0 for reasons unrelated to the bug; needs re-testing against a job known to match.

---

### NSW-STG-34: Opening a non-existent job URL shows a generic 'Something went Wrong'

| | |
|---|---|
| **Module** | Job detail |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in

**Steps to reproduce:**
1. Open /jobs/M8N999999 or /jobs/not-a-job

**Expected result:** 'Job not found' page with a link back to Jobs

**Actual result:** 'Something went Wrong'; GET /api/v1/jobs/M8N999999 returns 400 'Invalid job id' (should be 404). An unknown internal id already returns 404 'Job not found' - only the job-number form is wrong

**Evidence / test data:** job_edge_4.txt H12

**Regression check (30 Sep 2026):** GET /jobs/M8N999999 still returns 400 'Invalid job id' instead of 404.

---

### NSW-STG-35: Capacity fields silently strip ',' and 'e', changing the value (5,5 → 55 kW)

| | |
|---|---|
| **Module** | Add Job - Products |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job → Heating & Cooling, Residential, Installer BAWA

**Steps to reproduce:**
1. In Product 1, type 5,5 or 1e3 in Cooling Capacity (kW) or Heating Capacity (kW)

**Expected result:** Rejected with 'Enter a valid number', or 5,5 read as 5.5

**Actual result:** Field silently becomes 55 (from 5,5) or 13 (from 1e3) - a 10x wrong capacity is saved without any message

**Evidence / test data:** job_edge_4b.txt H02/H03

**Regression check (30 Sep 2026):** Cooling Capacity typed '5,5' still silently becomes '55'.

---

### NSW-STG-36: Heating Capacity has no upper limit (Cooling is capped at 65 kW) and both accept 0

| | |
|---|---|
| **Module** | Add Job - Products |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job → Heating & Cooling, Residential, Installer BAWA

**Steps to reproduce:**
1. Heating Capacity (kW) = 65.01 (or 0)
2. Cooling Capacity (kW) = 0.01
3. Click Send

**Expected result:** Same rule as Cooling ('Must be under 65 kW') and capacity > 0

**Actual result:** Heating 65.01 and 0 accepted; Cooling 0.01 accepted. Only Cooling ≥ 65 is blocked

**Evidence / test data:** job_edge_4b.txt H02/H03

**Regression check (30 Sep 2026):** Heating Capacity '65.01' kW still accepted with no 'must be under 65kW' error.

---

### NSW-STG-37: Warranty Period accepts 0, decimals and 9999 with no unit shown

| | |
|---|---|
| **Module** | Add Job - Products |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job → Heating & Cooling, Residential, Installer BAWA

**Steps to reproduce:**
1. Warranty Period = 0, 1.5 or 9999
2. Click Send

**Expected result:** Whole years within a sensible range (e.g. 1–25), unit (years) shown

**Actual result:** All accepted with no message

**Evidence / test data:** job_edge_4b.txt H04

**Regression check (30 Sep 2026):** Warranty Period '9999' still accepted with no range validation.

---

### NSW-STG-38: Access token still works after logout

| | |
|---|---|
| **Module** | Authentication / Security |
| **Severity** | High |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Fixed |

**Precondition:** Logged in as Master Admin (API or browser)

**Steps to reproduce:**
1. Log in and keep a copy of the access_token cookie
2. POST /api/v1/auth/logout (200)
3. Call GET /api/v1/auth/me with the old access_token

**Expected result:** 401 - the session is ended server-side on logout

**Actual result:** 200 - the logged-out token keeps full admin access until it expires (1 hour). The refresh token IS revoked, so only the access token is affected

**Evidence / test data:** tests/test_api_security_stage.py::TestSession::test_logout_revokes_access_token

**Regression check (30 Sep 2026):** GET /auth/me with the access token now correctly returns 401 after logout.

---

### NSW-STG-39: Refresh token is not rotated - an old refresh token stays reusable

| | |
|---|---|
| **Module** | Authentication / Security |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. Keep a copy of the refresh_token cookie
2. POST /api/v1/auth/refresh (200)
3. POST /api/v1/auth/refresh again with the OLD refresh_token

**Expected result:** 401 - each refresh issues a new refresh token and invalidates the previous one

**Actual result:** 200 - the old refresh token still works, and it is valid for 30 days, so a leaked token can't be detected or cut off by rotation

**Evidence / test data:** tests/test_api_security_stage.py::TestSession::test_refresh_rotates_refresh_token

**Regression check (30 Sep 2026):** The old refresh token is still accepted after a rotation - replayed old token still returns 200.

---

### NSW-STG-40: No throttling on admin login - unlimited password attempts

| | |
|---|---|
| **Module** | Authentication / Security |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** None (logged out)

**Steps to reproduce:**
1. POST /api/v1/auth/admin/login 12 times in a row with a wrong password (non-existent email used for the test)

**Expected result:** 429 Too Many Requests or a temporary lockout after a few failures (OTP request already returns 429 after repeat attempts)

**Actual result:** All 12 attempts return 401; no rate limit, delay or lockout

**Evidence / test data:** tests/test_api_security_stage.py::TestBruteForce

**Regression check (30 Sep 2026):** 12 consecutive wrong-password attempts still all return 401 - no 429 or lockout.

---

### NSW-STG-41: Malformed installer ID returns 500 Internal Server Error

| | |
|---|---|
| **Module** | Installers API |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. GET /api/v1/installers/not-an-id/members
2. GET /api/v1/installers/not-an-id/members/by-role?role=Plumber

**Expected result:** 400 'Invalid installer id' (as /jobs/not-a-job already does)

**Actual result:** 500 'Internal server error' on both (no stack trace in the body)

**Evidence / test data:** tests/test_api_security_stage.py::TestErrorHandling, tests/test_api_stage.py::TestInstallers

**Regression check (30 Sep 2026):** GET /installers/not-an-id/members still returns 500 instead of 400.

---

### NSW-STG-42: Rebates page does not load - rebate/installer/list API returns 404

| | |
|---|---|
| **Module** | Rebates |
| **Severity** | High |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. Sidebar → Rebates

**Expected result:** Rebate list loads

**Actual result:** 'No Data Found'. GET /api/v1/rebate/installer/list → 404 (also on every search)

**Evidence / test data:** module_sweep.txt

**Regression check (30 Sep 2026):** GET /rebate/installer/list still 404.

---

### NSW-STG-43: Street names starting with 'The' are split wrongly (10 The Corso → name 'The', type 'Corso')

| | |
|---|---|
| **Module** | Add Job - Site Address |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Not re-verified |

**Precondition:** Logged in as Master Admin → Jobs → Add Job

**Steps to reproduce:**
1. Site Address: search '10 The Corso Manly' and pick '10 The Corso, Manly NSW 2095'
2. Complete a valid job and Send
3. GET /api/v1/jobs/<id> and check address

**Expected result:** streetName 'The Corso', streetType '' (The Corso has no street type)

**Actual result:** Stored as streetNumber '10', streetName 'The', streetType 'Corso'. Structured address fields feed certificate/ESC paperwork, so the street is recorded incorrectly. Same risk for The Strand, The Esplanade, The Boulevarde, etc.

**Evidence / test data:** Job M8N000133 (proper_data_round6.json)

**Regression check (30 Sep 2026):** The Add Job form now also requires product pricing and plumbing/gas-work fields that the test helper doesn't fill yet, so submission couldn't be completed this pass. Root cause (address-parsing) not re-checked.

---

### NSW-STG-44: Admin login accepts a form-encoded body (login-CSRF surface)

| | |
|---|---|
| **Module** | Authentication / Security |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** None

**Steps to reproduce:**
1. POST /api/v1/auth/admin/login with Content-Type application/x-www-form-urlencoded and valid credentials

**Expected result:** 415/400 - JSON only, so a plain HTML form on another site can't post to it

**Actual result:** 200 and session cookies are set. SameSite=Lax limits the impact, but the API shouldn't accept simple-form bodies

**Evidence / test data:** tests/test_api_security_stage.py::test_login_rejects_non_json_content_type

**Regression check (30 Sep 2026):** Form-urlencoded login body still accepted (200) instead of rejected.

---

### NSW-STG-45: Web app sends no Content-Security-Policy header

| | |
|---|---|
| **Module** | Security headers |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** None

**Steps to reproduce:**
1. GET https://nswstage.rebatem8.com.au/log-in and inspect response headers

**Expected result:** A Content-Security-Policy header restricting script sources

**Actual result:** No CSP. HSTS, X-Content-Type-Options, X-Frame-Options and Referrer-Policy are present

**Evidence / test data:** tests/test_api_security_stage.py::test_web_app_security_headers

**Regression check (30 Sep 2026):** GET /log-in response still has no Content-Security-Policy header.

---

### NSW-STG-46: Product Brand list has duplicate brands that differ only by letter case

| | |
|---|---|
| **Module** | Add Job - Products |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Fixed |

**Precondition:** Logged in as Master Admin → Jobs → Add Job → Hot Water Heat Pump, Residential, any installer

**Steps to reproduce:**
1. Product 1: Original Equipment = Brand New Install
2. Open Brand

**Expected result:** One entry per brand

**Actual result:** Listed twice: DUX / Dux, GREE / Gree, EVOHEAT / EvoHeat, HYDROTHERM / Hydrotherm, SMART POWER TECH / Smart Power Tech (and Rinnai / Rinnai Australia Pty Ltd). Users may pick the variant with an incomplete model list

**Evidence / test data:** dbg_hwhp.txt

**Regression check (30 Sep 2026):** Brand list re-checked (78 brands) - no case-only duplicates found; the DUX/Dux-style entries are gone.

---

### NSW-STG-47: 'Model is required' shows as soon as a Brand is picked, before the user reaches Model

| | |
|---|---|
| **Module** | Add Job - Products |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin → Jobs → Add Job → Hot Water Heat Pump, Residential, any installer

**Steps to reproduce:**
1. Product 1: Original Equipment = Brand New Install
2. Brand = AGM Energy

**Expected result:** No error until Send is clicked or Model is left

**Actual result:** Red 'Model is required' appears immediately under the untouched Model field

**Evidence / test data:** dbg_hwhp.txt

**Regression check (30 Sep 2026):** 'Model is required' still appears immediately after picking Brand, before Model is touched.

---

### NSW-STG-48: Installers list silently accepts invalid paging (negative, zero, text)

| | |
|---|---|
| **Module** | Installers API |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. GET /api/v1/installers?skip=-1&limit=5
2. …?limit=-5
3. …?limit=0
4. …?skip=abc
5. …?limit=abc

**Expected result:** 400, as /jobs, /matrix and /activity-logs return for the same input

**Actual result:** 200 with values silently changed: skip -1→0, limit -5→1, limit 0 or 'abc'→20

**Evidence / test data:** tests/test_api_stage.py::TestListContract::test_bad_paging_rejected

**Regression check (30 Sep 2026):** Invalid paging (skip=-1, limit=-5/0/abc) still returns 200 with silently-corrected values.

---

### NSW-STG-49: Invalid sortType is ignored and treated as 'desc'

| | |
|---|---|
| **Module** | List APIs |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. GET /api/v1/jobs?skip=0&limit=2&sort=createdAt&sortType=sideways (same on /installers, /users, /activity-logs)

**Expected result:** 400 - sortType must be asc or desc (/matrix already rejects it)

**Actual result:** 200, results sorted descending

**Evidence / test data:** tests/test_api_stage.py::TestListContract::test_invalid_sort_type_rejected

**Regression check (30 Sep 2026):** GET /jobs?sortType=sideways still returns 200 sorted desc instead of 400.

---

### NSW-STG-50: Members of a non-existent installer returns 200 with an empty list

| | |
|---|---|
| **Module** | Installers API |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. GET /api/v1/installers/000000000000000000000000/members

**Expected result:** 404 'Installer not found'

**Actual result:** 200 'Members fetched successfully', members: [] - indistinguishable from an installer with no staff

**Evidence / test data:** tests/test_api_stage.py::TestInstallers::test_unknown_installer_404

**Regression check (30 Sep 2026):** GET members of a made-up installer id still returns 200 with an empty list instead of 404.

---

### NSW-STG-51: Two job-number formats in use (M800001–M800047 and M8N000xxx)

| | |
|---|---|
| **Module** | Jobs - data |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Info |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. Jobs → All, sort by Created ascending (or GET /api/v1/jobs?sort=createdAt&sortType=asc)

**Expected result:** One format for all NSW jobs, or confirmation that old-format jobs are intentional migrated data

**Actual result:** 47 oldest jobs are M800001–M800047, all later ones M8N000xxx. Needs PO confirmation before reports/exports rely on the prefix

**Evidence / test data:** tests/test_api_stage.py::TestJobs::test_job_numbers_well_formed_and_unique

**Regression check (30 Sep 2026):** Still two job-number formats in the data (M800001-47, then M8N000xxx) - unchanged, still needs a PO decision, not a code defect to close.

---

### NSW-STG-52: Login fails with a generic error when the email has leading/trailing spaces

| | |
|---|---|
| **Module** | Authentication |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** None

**Steps to reproduce:**
1. Log in with '  admin@… ' (spaces around a valid email) and the correct password

**Expected result:** Spaces trimmed and login succeeds

**Actual result:** 400 'Invalid request'

**Evidence / test data:** tests/test_api_stage.py::TestLogin::test_email_with_surrounding_spaces_is_trimmed

**Regression check (30 Sep 2026):** Login with a padded-space email still returns 400 instead of trimming and succeeding.

---

### NSW-STG-53: Stored XSS in Job Notes - HTML is saved and rendered unsanitised

| | |
|---|---|
| **Module** | Job Notes / Security |
| **Severity** | Critical |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin -> any job -> Notes tab

**Steps to reproduce:**
1. POST /api/v1/notes with note = "<p><img src=x onerror=alert(1)></p>" (or type it in the rich-text editor and click Add Note)
2. Reload the job's Notes tab as any admin

**Expected result:** The tag is stripped/escaped - the note renders as plain text, no script runs

**Actual result:** The raw HTML is stored as-is and re-rendered as live DOM (confirmed: the <img> tag appears broken in the page and its onerror handler actually fires a JS alert() in the viewer's session). Any admin who can write a note can run arbitrary JS in another admin's session when they open that job - session/data theft, or acting on the API with the victim's cookies

**Evidence / test data:** tests/test_api_security_stage.py (POST /api/v1/notes, note field) - reproduced and verified with a real onerror alert firing, cleaned up after

**Regression check (30 Sep 2026):** CRITICAL - stored XSS in Job Notes still reproduces: raw <img onerror> HTML is stored and returned as-is by the API.

---

### NSW-STG-54: Installers list ignores an unrecognised status filter instead of rejecting or matching nothing

| | |
|---|---|
| **Module** | Installers API |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. GET /api/v1/installers?skip=0&limit=5&status=NotARealStatus
2. Compare to GET /api/v1/installers?skip=0&limit=5 (no filter)

**Expected result:** 400 (unknown status, as /jobs already returns for an unknown status), or 0 results

**Actual result:** 200 with the full unfiltered list (total=15, identical to no filter) - the status filter is silently dropped for any value it doesn't recognise, so a typo in a report/integration script would return all installers instead of erroring

**Evidence / test data:** step3_filters.py output, this session

**Regression check (30 Sep 2026):** An unrecognised status filter on /installers is still silently ignored (identical response to no filter).

---

### NSW-STG-55: Notes accepts empty-looking content ('<p></p>') as if it had text

| | |
|---|---|
| **Module** | Job Notes |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin -> any job -> Notes tab

**Steps to reproduce:**
1. POST /api/v1/notes with note = "<p></p>"

**Expected result:** 400 'Provide note text or at least one attachment' (the same message a fully empty string already gets)

**Actual result:** 201 Created - a blank-looking note is added to the job. The empty-check only tests for an empty string, not for HTML with no visible text

**Evidence / test data:** notes_api_checks.py output, this session

**Regression check (30 Sep 2026):** POST /notes with '<p></p>' (empty-looking) is still accepted (201).

---

### NSW-STG-56: Whitespace-only customer name crashes job creation with 500 Internal Server Error

| | |
|---|---|
| **Module** | Jobs API |
| **Severity** | High |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. POST /api/v1/jobs with a valid job body but customer.name = "   " (spaces only)

**Expected result:** 400 - same 'name is required' rejection as an empty string

**Actual result:** 500 {"message":"Internal server error"} - reproduced cleanly twice. The server likely trims the name server-side and then fails on the resulting empty value instead of validating before use

**Evidence / test data:** round8_boundary_matrix.py / round8_boundary_matrix2.py, this session - reproduced twice, no job created either time

**Regression check (30 Sep 2026):** POST /jobs with customer.name='   ' (whitespace only) still returns 500 instead of 400.

---

### NSW-STG-57: Malformed JSON request bodies return 500 instead of 400 on every write endpoint tested

| | |
|---|---|
| **Module** | API / Security |
| **Severity** | High |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. POST /api/v1/jobs with a body containing a trailing comma, an unquoted key, or a raw newline inside a string value (Content-Type: application/json)

**Expected result:** 400 with a parse-error message - malformed JSON is a client error

**Actual result:** 500 {"message":"Internal server error"} for all three malformed-JSON shapes. This looks like an uncaught JSON.parse() exception reaching a generic error handler rather than a body-parser 400 - worth checking whether this pattern exists on other POST/PUT endpoints too, and whether unhandled exceptions like this are being alerted on

**Evidence / test data:** round8_step7_negative.py, this session - no job created (count unchanged, confirmed via before/after total)

**Regression check (30 Sep 2026):** All 3 malformed-JSON body shapes still return 500 instead of 400.

---

### NSW-STG-58: Postcode has no format or NSW-range validation at the API level

| | |
|---|---|
| **Module** | Jobs API |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. POST /api/v1/jobs with address.postcode = "", "   ", "0000", "3000", "1999", "abcd", "2000.5", "-2000", emoji, or the field omitted entirely

**Expected result:** 400 for anything that isn't a valid 4-digit NSW postcode (2000-2999)

**Actual result:** 201 Created for every case listed - the API has no postcode validation at all; the NSW-only rule that the UI never applies (NSW-STG-27) doesn't exist server-side either, so any direct API integration can save a job with no postcode or a non-existent one

**Evidence / test data:** round8_boundary_matrix.py, this session - each case read back via GET and confirmed stored as sent; jobs count moved by exactly the number of successful creates

**Regression check (30 Sep 2026):** All 8 postcode edge cases (empty, '0000', '3000', 'abcd', etc.) still return 201 - no server-side postcode validation.

---

### NSW-STG-59: ABN/ACN is not validated at the API level - any string is accepted

| | |
|---|---|
| **Module** | Jobs API |
| **Severity** | High |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. POST /api/v1/jobs with customer.abnAcn = a checksum-invalid 11-digit number, letters, unicode digits, a value with literal spaces/dashes, 10 or 12 digits, all zeros, or an empty string

**Expected result:** 400 for anything that isn't a checksum-valid 11-digit ABN or valid 9-digit ACN

**Actual result:** 201 Created for every case, values stored exactly as sent (including literal letters and full-width unicode digits in the abnAcn field). This is the field NSW-STG-14/15/26 already flagged as unvalidated in the UI - confirmed here that there is no backend safety net either, which matters because ABN/ACN feeds the ESC/PRC certificate paperwork for the rebate scheme

**Evidence / test data:** round8_boundary_matrix.py, this session - read back via GET, values matched exactly

**Regression check (30 Sep 2026):** abnAcn checksum still not validated at the API level - bad-checksum ABN still accepted (201).

---

### NSW-STG-60: Phone number format is not enforced at the API level

| | |
|---|---|
| **Module** | Jobs API |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. POST /api/v1/jobs with customer.phoneNumber = letters ("abcdefghi"), a value with embedded spaces, scientific notation ("4.12e8"), 8 or 10 digits, or a leading-zero 10-digit value

**Expected result:** 400 for anything that isn't exactly 9 AU mobile digits

**Actual result:** 201 Created for every case (only a genuinely empty/null/omitted value is rejected). Confirms the root cause of NSW-STG-20/22/29 is server-side, not just a UI gap - SMS delivery to these numbers would fail silently the same way

**Evidence / test data:** round8_boundary_matrix.py, this session

**Regression check (30 Sep 2026):** Phone format still not enforced at the API level - letters, wrong lengths, scientific notation all still accepted (201).

---

### NSW-STG-61: Installation date accepts impossible calendar dates and any date range at the API level

| | |
|---|---|
| **Module** | Jobs API |
| **Severity** | Medium |
| **Priority** | P2 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. POST /api/v1/jobs with installationDate = "2026-04-31" (no such day), "2027-02-29" (not a leap year), "1900-01-01", "9999-12-31", or a full ISO datetime string

**Expected result:** 400 for a calendar-invalid date; a sensible min/max range for a real installation date

**Actual result:** 201 Created for all of the above - only a wrong-shaped string (non-ISO format, non-date text) or an out-of-range month/day component (13, 00) is rejected. Confirms NSW-STG-13/28's root cause is server-side

**Evidence / test data:** round8_boundary_matrix.py, this session

**Regression check (30 Sep 2026):** Impossible calendar dates (2027-02-29 etc.) still accepted at the API level (201).

---

### NSW-STG-62: Product capacity fields accept negative values and any magnitude at the API level

| | |
|---|---|
| **Module** | Jobs API - Products |
| **Severity** | Low |
| **Priority** | P3 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. POST /api/v1/jobs with equipmentQuoted[0].coolingCapacityKw = -5 or 999999

**Expected result:** 400 for a negative or unrealistic capacity

**Actual result:** 201 Created for both. Type checking IS enforced (a string, "NaN", or "Infinity" correctly get 400 'expected number'), but there's no range check at all. Confirms the root cause of NSW-STG-36 is server-side

**Evidence / test data:** round8_boundary_matrix2.py, this session

**Regression check (30 Sep 2026):** coolingCapacityKw=-5 still accepted (201) - no range check at the API level.

---

### NSW-STG-63: Job editing is non-functional everywhere - Save never sends a request

| | |
|---|---|
| **Module** | Job Information / Products / Post Install Details / Add Job wizard |
| **Severity** | Critical |
| **Priority** | P1 |
| **Environment** | Staging - https://nswstage.rebatem8.com.au (web admin), Master Admin login, Chromium |
| **Status** | Open |

**Precondition:** Logged in as Master Admin

**Steps to reproduce:**
1. Open a signed job -> Job Information tab -> change Own Reference -> Save (also reproduced on Post Install Details' CES Number, and on a Products-tab Brand edit via the pencil icon)
2. Separately: open an unsigned (Engagement Sent) job from the Jobs list, click Back to reach step 1 of the wizard, change any field, click Save

**Expected result:** The field updates and persists; a network request is sent and the change is visible after reloading the job

**Actual result:** Save closes/returns silently with zero POST/PUT/PATCH requests fired (confirmed with a request listener) and the field reverts to its old value on reload. Reproduced on 3 separate surfaces (Job Information, Post Install Details, Products pencil-icon edit) plus the pre-sign wizard's own Save button. There is no PUT/PATCH endpoint for job fields anywhere in the frontend bundle either - the only job-level writes that exist are POST (create) and DELETE (bulk delete). This means a job's data can never be corrected once created; the only way to fix bad data is to delete the job and create a new one

**Evidence / test data:** tests/test_post_sign_editing.py::TestBug02SaveFiresNoRequest (already in the suite, tracked internally as "BUG-02" but not yet in this list) + round9_1_edit_capability_probe.py, this session (pre-sign wizard case, reproduced live: changed customer name and postcode, Save fired no request, GET afterward showed the old values unchanged)

**Regression check (30 Sep 2026):** CRITICAL - Save still fires zero network requests on a signed job's Job Information tab; edited Own Reference did not persist after reload (re-verified on M8N000071, a fresh 'photos_started' job).

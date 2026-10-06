# Fieldr Test Plan

**Observed 2026-09-19 on the live dev tenant:** login and OTP screens, Dashboard, Customer, User, Quote (with Formulas), Job (all tabs), Timesheet, Job Report, Invoices, Items, CMS, Settings (Company, Holidays, Checklists, Report Builder, Subscription, Payment Cards). Items marked ASSUMPTION or NEEDS UI INSPECTION were not observed.

## 1. Executive summary
- Scope: authentication, adding people, commercial documents (items, quotes, invoices, jobs), content and legal pages.
- Total cases: **115** (AUTH 50, REG 20, CKOUT 30, CONT 15).
- Priority split: P0 31, P1 59, P2 20, P3 5.
- Automated: AUTH-001 to 050 as Playwright specs (`pw/src/tests/auth`). They have not been installed or run yet.
- Blockers: no timesheet or crew data can be created (the timelog API stores nothing); users need extra seats; OTP expiry, replay and idle timeout cannot be tested with the static bypass OTP.
- Findings so far: 10 (see SECURITY_API_TEST_REPORT.md).

## 2. Test environment
| Item | Value |
|---|---|
| URL | https://rajanjagz7.dev.fieldr.app |
| Auth | Passwordless OTP, six boxes ("Digit 1" to "Digit 6"), button "Verify & Login" |
| Plan | Basic ($49/mo), Stripe test mode |
| Browsers | Chrome, Firefox, Safari (WebKit), Edge (latest) |
| Viewports | 1920x1080, 1366x768, 768x1024, 375x667, 320x568 |
| OS | Windows 11 (runner); Safari via Playwright WebKit |
| Data | 101 customers, 100 items, 180 invoices, 277 jobs, 101 quotes, 375 job reports, 6 formulas, 40 CMS entries, 27 holidays, 3 checklists, 3 report templates |

## 3. Test cases
### AUTH: authentication and sessions (50 cases)
Full table: [auth-test-cases.md](auth-test-cases.md), generated from the Playwright specs.

### REG: adding people: customers, users, groups (20 cases)
| ID | Title | Module | Preconditions | Steps | Test Data (AU) | Expected Result | Priority | Type |
|----|-------|--------|---------------|-------|----------------|-----------------|----------|------|
| FLD-REG-001 | Add Customer with all required fields | REG | Logged in as the QA user | 1. Open Customer<br>2. Click Add Customer<br>3. Enter First Name<br>4. Enter Last Name<br>5. Enter Mobile Number<br>6. Enter Email<br>7. Enter Address<br>8. Enter Description<br>9. Click Save | Olivia Nguyen / 0491 570 156 / olivia.nguyen@yopmail.com / 12 Macquarie Street, Sydney NSW 2000 | Customer saved; appears in list with a CST- number | P0 | Functional |
| FLD-REG-002 | Add Customer with empty First Name | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Leave First Name empty<br>3. Fill all other fields<br>4. Click Save | empty | Save disabled or inline error on First Name | P1 | Negative |
| FLD-REG-003 | Add Customer with duplicate mobile | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Enter a mobile already used<br>3. Fill other fields<br>4. Click Save | existing customer mobile | Rejected with a duplicate-mobile message | P0 | Negative |
| FLD-REG-004 | Add Customer mobile too short (9 digits) | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Enter 041234567 in Mobile Number<br>3. Fill other fields<br>4. Click Save | 041234567 | Rejected, inline validation | P1 | Boundary |
| FLD-REG-005 | Add Customer email without @ | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Enter noah.smithbigpond.net.au in Email<br>3. Click Save | no @ | Inline email error | P1 | Validation |
| FLD-REG-006 | Add Customer email 255 chars | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Enter a 255-char email<br>3. Click Save | 255 chars (bigpond.net.au) | Rejected (max 254) | P2 | Boundary |
| FLD-REG-007 | Add Customer name with emoji only | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Enter an emoji in First Name<br>3. Click Save | U+1F642 | Rejected or stripped | P2 | Validation |
| FLD-REG-008 | Add Customer name 101 chars (ASSUMPTION max 100) | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Enter 101 chars in Last Name<br>3. Click Save | N x 101 | Rejected; max length NEEDS UI INSPECTION | P2 | Boundary |
| FLD-REG-009 | Add Customer XSS in Description is escaped | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Enter an img onerror payload in Description<br>3. Fill other fields<br>4. Click Save<br>5. Open the customer | XSS payload | Rendered as text; no script runs | P1 | Security |
| FLD-REG-010 | Add Customer profile photo upload | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Choose avatar-001.png<br>3. Fill required fields<br>4. Click Save | avatar-001.png | Photo shows on card and profile | P2 | Functional |
| FLD-REG-011 | Add New User with all required fields | REG | Logged in as the QA user | 1. Open User<br>2. Click Add User<br>3. Enter First Name<br>4. Enter Last Name<br>5. Select Industry<br>6. Select Role<br>7. Enter Email<br>8. Enter Mobile Number<br>9. Click Save | Liam Fraser / Construction / User | User appears in list (needs a free seat) | P0 | Functional |
| FLD-REG-012 | Add New User when the plan has no free seat | REG | Logged in as the QA user | 1. Open Add New User<br>2. Fill all required fields<br>3. Click Save | Basic plan, 1 seat | Clear seat-limit message and no orphan user (observed: redirect to Subscription) | P0 | Negative |
| FLD-REG-013 | Add New User without Role | REG | Logged in as the QA user | 1. Open Add New User<br>2. Fill fields except Role<br>3. Click Save | no role | Inline error on Role | P1 | Negative |
| FLD-REG-014 | Add New User with a mobile from another tenant | REG | Logged in as the QA user | 1. Open Add New User<br>2. Enter a mobile registered elsewhere<br>3. Click Save | registered number | Generic message that does not reveal other tenants | P1 | Security |
| FLD-REG-015 | Add New User Date Of Birth 29/02/1900 | REG | Logged in as the QA user | 1. Open Add New User<br>2. Pick 29/02/1900 in Date Of Birth | 29/02/1900 | Date rejected (not a leap year) | P2 | Boundary |
| FLD-REG-016 | Add New User postcode 4 digits | REG | Logged in as the QA user | 1. Open Add New User<br>2. Enter 2000 in Postcode | 2000 | Accepted | P2 | Validation |
| FLD-REG-017 | Add New User state list has only AU states | REG | Logged in as the QA user | 1. Open Add New User<br>2. Open the State list | - | NSW, VIC, QLD, WA, SA, TAS, ACT, NT only; no duplicates | P2 | Validation |
| FLD-REG-018 | Add New User tag creation | REG | Logged in as the QA user | 1. Open Add New User<br>2. Type Electrician in Tags<br>3. Press Enter | Electrician | Tag created and shown | P3 | Functional |
| FLD-REG-019 | Add Group and assign members | REG | Logged in as the QA user | 1. Open User<br>2. Open Groups<br>3. Add a group<br>4. Choose members<br>5. Save | Electrical Crew | Group lists its members (observed: members showed 0 after an API update) | P1 | Functional |
| FLD-REG-020 | Keyboard-only completion of Add Customer | REG | Logged in as the QA user | 1. Open Add Customer<br>2. Press Tab through every field<br>3. Press Enter on Save | - | Logical focus order; errors are announced | P2 | Accessibility |

### CKOUT: items, quotes, formulas, invoices, jobs, settings data (30 cases)
| ID | Title | Module | Preconditions | Steps | Test Data (AU) | Expected Result | Priority | Type |
|----|-------|--------|---------------|-------|----------------|-----------------|----------|------|
| FLD-CKOUT-001 | Add Item with sell and cost price | CKOUT | Logged in as the QA user | 1. Open Items<br>2. Click Add Item<br>3. Enter Item Name<br>4. Enter Unit<br>5. Enter Sell Price<br>6. Enter Cost Price<br>7. Enter Description<br>8. Click Save | Labour - Electrician / hour / 110 / 71.50 | Item saved | P0 | Functional |
| FLD-CKOUT-002 | Item cost price above sell price | CKOUT | Logged in as the QA user | 1. Open Add Item<br>2. Enter Sell Price 100<br>3. Enter Cost Price 120<br>4. Click Save | 100 / 120 | Warning or rejection (negative margin); NEEDS UI INSPECTION | P1 | Validation |
| FLD-CKOUT-003 | Item negative sell price | CKOUT | Logged in as the QA user | 1. Open Add Item<br>2. Enter -0.01 in Sell Price<br>3. Click Save | -0.01 | Rejected | P1 | Negative |
| FLD-CKOUT-004 | Item sell price with 3 decimals | CKOUT | Logged in as the QA user | 1. Open Add Item<br>2. Enter 1100.005 in Sell Price<br>3. Click Save | 1100.005 | Rounded or rejected to 2 dp | P2 | Boundary |
| FLD-CKOUT-005 | Item price typed as $1,100.00 | CKOUT | Logged in as the QA user | 1. Open Add Item<br>2. Type $1,100.00 in Sell Price | $1,100.00 | Number field rejects the symbols or normalises | P2 | Validation |
| FLD-CKOUT-006 | Add Invoice with 1 line | CKOUT | Logged in as the QA user | 1. Open Invoices<br>2. Click Add Invoice<br>3. Select Customer<br>4. Enter Invoice Date<br>5. Enter Due Date<br>6. Add a line item<br>7. Click Save | 2 x $630.00 | Sub-total $1,260.00, GST $126.00, total $1,386.00 | P0 | Functional |
| FLD-CKOUT-007 | Invoice GST is 10 percent of the sub-total | CKOUT | Logged in as the QA user | 1. Create an invoice of $1,100.00<br>2. Read the total | $1,100.00 | Total shows $1,210.00 | P0 | Functional |
| FLD-CKOUT-008 | Invoice with line discount | CKOUT | Logged in as the QA user | 1. Add a line with 10 in Discount<br>2. Read totals | 10% | Discount applied before GST | P1 | Functional |
| FLD-CKOUT-009 | Invoice due date before invoice date | CKOUT | Logged in as the QA user | 1. Set Invoice Date 19/09/2026<br>2. Set Due Date 18/09/2026<br>3. Click Save | 18/09/2026 | Rejected | P1 | Negative |
| FLD-CKOUT-010 | Invoice with quantity 0 | CKOUT | Logged in as the QA user | 1. Add a line with Quantity 0<br>2. Click Save | 0 | Rejected or line removed | P1 | Boundary |
| FLD-CKOUT-011 | Invoice with negative rate | CKOUT | Logged in as the QA user | 1. Add a line with Rate -10<br>2. Click Save | -10 | Rejected | P1 | Negative |
| FLD-CKOUT-012 | Invoice without a customer | CKOUT | Logged in as the QA user | 1. Leave Customer empty<br>2. Click Save | empty | Inline error | P1 | Negative |
| FLD-CKOUT-013 | Invoice status order: Draft, Awaiting Approval, Awaiting Payment, Paid | CKOUT | Logged in as the QA user | 1. Create a draft invoice<br>2. Submit for approval<br>3. Approve<br>4. Record payment | - | Each change allowed only in order; dashboard tiles update | P0 | Functional |
| FLD-CKOUT-014 | Invoice amounts cannot be set through the API | CKOUT | Logged in as the QA user | 1. Send PUT invoice/update with amountPaid equal to the total<br>2. Read the invoice | amountPaid = total | Rejected (observed: accepted, finding F1) | P0 | Security |
| FLD-CKOUT-015 | Invoice BSB accepts XXX-XXX only | CKOUT | Logged in as the QA user | 1. Open payment details<br>2. Enter 062000<br>3. Enter 062-000 | 062-000 | Hyphenated format accepted; BSB screen NEEDS UI INSPECTION | P1 | Validation |
| FLD-CKOUT-016 | Company ABN checksum | CKOUT | Logged in as the QA user | 1. Open Settings, Company Settings<br>2. Enter 33 102 417 032<br>3. Enter 12 345 678 901 | valid / invalid ABN | Valid accepted; invalid rejected | P1 | Validation |
| FLD-CKOUT-017 | Add Quote requires at least one item | CKOUT | Logged in as the QA user | 1. Open Quote<br>2. Click Add Quote<br>3. Select Customer<br>4. Enter Quote Description<br>5. Click Next<br>6. Save with no items | no items | Rejected: A quote must contain at least one item | P0 | Negative |
| FLD-CKOUT-018 | Add Quote with sections and items | CKOUT | Logged in as the QA user | 1. Add a Labour section<br>2. Add a line item<br>3. Add a Materials section<br>4. Add a line item<br>5. Save | 2 sections | Quote saved with a serial number | P0 | Functional |
| FLD-CKOUT-019 | Quote formula: Qty x Rate x 1.2 | CKOUT | Logged in as the QA user | 1. Open Quote, Formulas<br>2. Click Add Formula<br>3. Enter a Column Name<br>4. Pick Qty.<br>5. Pick x<br>6. Pick Rate<br>7. Pick x<br>8. Insert 1.2<br>9. Click Save | Qty 10, Rate 50 | Live preview shows 600.00 | P0 | Functional |
| FLD-CKOUT-020 | Quote formula cannot end on an operator | CKOUT | Logged in as the QA user | 1. Add a formula<br>2. Pick Qty.<br>3. Pick x | Qty. x | Save stays disabled until the formula is complete | P1 | Validation |
| FLD-CKOUT-021 | Quote formula column shown on the customer PDF | CKOUT | Logged in as the QA user | 1. Turn on Show to Customer<br>2. Save<br>3. Open the quote PDF | - | Column printed; internal columns hidden | P2 | Functional |
| FLD-CKOUT-022 | Quote line types Labour and Material | CKOUT | Logged in as the QA user | 1. Add a Labour line<br>2. Add a Material line<br>3. Read the quote | labour / material | Types shown correctly | P1 | Functional |
| FLD-CKOUT-023 | Job with a report template attached | CKOUT | Logged in as the QA user | 1. Open a job<br>2. Open Reports<br>3. Attach a template<br>4. Save<br>5. Open Job Report | Electrical Job Completion Report | Report created with status Created | P1 | Functional |
| FLD-CKOUT-024 | Job cap on the Solo plan | CKOUT | Logged in as the QA user | 1. Create 6 active jobs on Solo | 6th job | Blocked with a plan-limit message (observed 403) | P1 | Functional |
| FLD-CKOUT-025 | Job start and end time | CKOUT | Logged in as the QA user | 1. Open Add Job<br>2. Enter Start Date<br>3. Enter End Date<br>4. Save | 16/09/2026 to 17/09/2026 | Job shows on the week schedule | P1 | Functional |
| FLD-CKOUT-026 | Job Site Radius 1 to 10,000 m | CKOUT | Logged in as the QA user | 1. Enter Site Radius 0<br>2. Enter Site Radius 10001 | 0 / 10001 | Both rejected; 1 and 10000 accepted | P2 | Boundary |
| FLD-CKOUT-027 | Holiday create and duplicate date | CKOUT | Logged in as the QA user | 1. Add Holiday 26/01/2026<br>2. Add another on the same date | 26/01/2026 | Second rejected (observed 409) | P2 | Negative |
| FLD-CKOUT-028 | Checklist item order | CKOUT | Logged in as the QA user | 1. Open Checklist<br>2. Add 3 items<br>3. Save | 3 items | Items keep their order | P3 | Functional |
| FLD-CKOUT-029 | Report template builder field types | CKOUT | Logged in as the QA user | 1. Open Report Builder<br>2. Add each field type<br>3. Save | Textbox, Dropdown, Radio, Checkbox, Textarea, Number, Upload, Email, Date | Template saved and renders on a job report | P2 | Functional |
| FLD-CKOUT-030 | Dashboard tiles match the data | CKOUT | Logged in as the QA user | 1. Open Dashboard<br>2. Compare each tile with its list | - | Jobs, Completed, Revenue, Outstanding and Pending counts match the lists | P0 | Regression |

### CONT: CMS, notifications, legal and contact (15 cases)
| ID | Title | Module | Preconditions | Steps | Test Data (AU) | Expected Result | Priority | Type |
|----|-------|--------|---------------|-------|----------------|-----------------|----------|------|
| FLD-CONT-001 | Terms & Conditions link opens the terms page | CONT | Logged in as the QA user | 1. Open the login page<br>2. Click Terms & Conditions | - | Opens /terms-and-conditions | P1 | Functional |
| FLD-CONT-002 | Privacy Policy link opens the privacy page | CONT | Logged in as the QA user | 1. Open the login page<br>2. Click Privacy Policy | - | Opens /privacy-policy | P1 | Functional |
| FLD-CONT-003 | CMS list shows Type, Created By and Date | CONT | Logged in as the QA user | 1. Open CMS | - | Columns TYPE, CREATED BY, DATE, ACTION shown | P2 | Functional |
| FLD-CONT-004 | Add a CMS entry of each type | CONT | Logged in as the QA user | 1. Click Add CMS<br>2. Select Type<br>3. Enter Title<br>4. Enter Content<br>5. Click Save | Induction, Help, Privacy Policy, Terms & Conditions, FAQ | Entry appears in the list | P1 | Functional |
| FLD-CONT-005 | CMS Title empty | CONT | Logged in as the QA user | 1. Click Add CMS<br>2. Select Type<br>3. Leave Title empty<br>4. Save | empty | Inline error (the API returns 500, finding F3) | P1 | Negative |
| FLD-CONT-006 | CMS Content empty | CONT | Logged in as the QA user | 1. Click Add CMS<br>2. Enter Title<br>3. Leave Content empty<br>4. Save | empty | Inline error | P1 | Negative |
| FLD-CONT-007 | CMS rich text stores a script safely | CONT | Logged in as the QA user | 1. Enter a script tag in Content<br>2. Save<br>3. View the page | XSS payload | Sanitised; no alert | P1 | Security |
| FLD-CONT-008 | CMS Title 255 chars | CONT | Logged in as the QA user | 1. Enter 255 chars in Title<br>2. Save | 255 | Accepted or rejected consistently; limit NEEDS UI INSPECTION | P2 | Boundary |
| FLD-CONT-009 | Notifications page lists events | CONT | Logged in as the QA user | 1. Open Notifications | - | Recent events listed; unread count clears | P2 | Functional |
| FLD-CONT-010 | Notification badge increments after a new job | CONT | Logged in as the QA user | 1. Create a job<br>2. Read the sidebar badge | - | Badge increases by 1 | P3 | Functional |
| FLD-CONT-011 | Help entries are findable | CONT | Logged in as the QA user | 1. Open Help content<br>2. Search for invoice | invoice | Matching entries shown; help UI NEEDS UI INSPECTION | P3 | Functional |
| FLD-CONT-012 | Support contact page exists | CONT | Logged in as the QA user | 1. Look for a Support or Contact page | - | NEEDS UI INSPECTION: no contact form was observed | P2 | Functional |
| FLD-CONT-013 | Contact form rejects an invalid email | CONT | Logged in as the QA user | 1. Open the contact form<br>2. Enter noah.smith@bigpond<br>3. Submit | noah.smith@bigpond | Blocked; depends on the form existing | P2 | Validation |
| FLD-CONT-014 | Contact form mobile format | CONT | Logged in as the QA user | 1. Enter +61 412 345 678<br>2. Enter 0412ABC678 | AU mobiles | First accepted, second rejected | P2 | Validation |
| FLD-CONT-015 | Login footer links are keyboard reachable | CONT | Logged in as the QA user | 1. Open the login page<br>2. Press Tab to the footer links | - | Both links focusable with a visible focus ring | P3 | Accessibility |

## 4. Negative and boundary matrix
One row per field. Counts come from `csv/<field>.csv`; the expected result for every value is in the CSV.

| Field | Total values | Expect accept | Expect reject |
|---|---|---|---|
| abn | 116 | 63 | 53 |
| account_number | 114 | 87 | 27 |
| amount_aud | 107 | 97 | 10 |
| bsb | 118 | 99 | 19 |
| date_of_birth | 115 | 88 | 27 |
| email_address | 105 | 71 | 34 |
| first_name | 104 | 71 | 33 |
| last_name | 104 | 71 | 33 |
| mobile_number | 109 | 73 | 36 |
| otp_code | 108 | 84 | 24 |
| postcode | 134 | 112 | 22 |
| state | 100 | 40 | 60 |
| street_address | 113 | 99 | 14 |
| tfn | 112 | 63 | 49 |

Boundary rules used: mobile 10 national digits; email local part 64 and total 254; OTP exactly 6 digits; postcode 4 digits; account 6 to 9 digits; ABN 11 digits mod-89; TFN 9 digits mod-11; names 1 to 100 (ASSUMPTION); DOB from 01/01/1900.

## 5. ASSUMPTION register
| # | Item | Status |
|---|---|---|
| A1 | Name max length is 100 | NEEDS UI INSPECTION |
| A2 | Address max length is 254 | NEEDS UI INSPECTION |
| A3 | OTP validity window and replay behaviour | Unknown; the bypass OTP is static |
| A4 | Idle timeout length | Unknown |
| A5 | Logout menu label | Not observed (spec uses a regex) |
| A6 | Email-login bypass OTP applies to email | Unverified |
| A7 | RBAC roles beyond Customer and User | Not observed; Roles & Permissions is a Business-plan feature |
| A8 | Self sign-up and a public Contact page | Not observed |
| A9 | The master prompt lists 7999 and 9999 as invalid postcodes, 0200 as NT, and +61 12 345 6789 as too short | Conflicts with the real ranges: TAS is 7000-7999, QLD PO boxes reach 9999, 0200-0299 is ACT, and that number is 10 digits without a mobile prefix. The CSVs follow the real ranges |
| A10 | Payment-card and BSB screens | Not observed |

## 6. Risks and mitigation
| Risk | Mitigation |
|---|---|
| A live SMS OTP is not testable | Use the QA bypass OTP; keep expiry and replay cases manual |
| Brute-force cases can lock the shared bypass account | AUTH-038 is skipped unless FLDR_ALLOW_LOCKOUT=1 |
| Seeded mobiles may belong to real people | Keep SMS notifications off; prefer ACMA-reserved numbers |
| The app reloads on deploy and drops open forms | Run UI cases in short bursts and re-verify saved values |
| Timesheet and crew tiles cannot be filled | Needs the mobile clock-on payload or a seat upgrade |
| Plan limits change results (5 jobs on Solo, 1 seat on Basic) | Record the plan in every run |

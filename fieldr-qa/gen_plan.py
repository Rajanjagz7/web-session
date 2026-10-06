"""Generate test-plan.md and test-data-table.md (counts are computed, never typed by hand)."""
import csv, os

HERE = os.path.dirname(os.path.abspath(__file__))


def n(v):
    return "<br>".join(f"{i}. {s}" for i, s in enumerate(v, 1))


# ---- REG: adding people (observed forms: Add Customer, Add New User). Self sign-up was NOT observed.
REG = [
    ("Add Customer with all required fields", "P0", "Functional", ["Open Customer", "Click Add Customer", "Enter First Name", "Enter Last Name", "Enter Mobile Number", "Enter Email", "Enter Address", "Enter Description", "Click Save"], "Olivia Nguyen / 0491 570 156 / olivia.nguyen@yopmail.com / 12 Macquarie Street, Sydney NSW 2000", "Customer saved; appears in list with a CST- number"),
    ("Add Customer with empty First Name", "P1", "Negative", ["Open Add Customer", "Leave First Name empty", "Fill all other fields", "Click Save"], "empty", "Save disabled or inline error on First Name"),
    ("Add Customer with duplicate mobile", "P0", "Negative", ["Open Add Customer", "Enter a mobile already used", "Fill other fields", "Click Save"], "existing customer mobile", "Rejected with a duplicate-mobile message"),
    ("Add Customer mobile too short (9 digits)", "P1", "Boundary", ["Open Add Customer", "Enter 041234567 in Mobile Number", "Fill other fields", "Click Save"], "041234567", "Rejected, inline validation"),
    ("Add Customer email without @", "P1", "Validation", ["Open Add Customer", "Enter noah.smithbigpond.net.au in Email", "Click Save"], "no @", "Inline email error"),
    ("Add Customer email 255 chars", "P2", "Boundary", ["Open Add Customer", "Enter a 255-char email", "Click Save"], "255 chars (bigpond.net.au)", "Rejected (max 254)"),
    ("Add Customer name with emoji only", "P2", "Validation", ["Open Add Customer", "Enter an emoji in First Name", "Click Save"], "U+1F642", "Rejected or stripped"),
    ("Add Customer name 101 chars (ASSUMPTION max 100)", "P2", "Boundary", ["Open Add Customer", "Enter 101 chars in Last Name", "Click Save"], "N x 101", "Rejected; max length NEEDS UI INSPECTION"),
    ("Add Customer XSS in Description is escaped", "P1", "Security", ["Open Add Customer", "Enter an img onerror payload in Description", "Fill other fields", "Click Save", "Open the customer"], "XSS payload", "Rendered as text; no script runs"),
    ("Add Customer profile photo upload", "P2", "Functional", ["Open Add Customer", "Choose avatar-001.png", "Fill required fields", "Click Save"], "avatar-001.png", "Photo shows on card and profile"),
    ("Add New User with all required fields", "P0", "Functional", ["Open User", "Click Add User", "Enter First Name", "Enter Last Name", "Select Industry", "Select Role", "Enter Email", "Enter Mobile Number", "Click Save"], "Liam Fraser / Construction / User", "User appears in list (needs a free seat)"),
    ("Add New User when the plan has no free seat", "P0", "Negative", ["Open Add New User", "Fill all required fields", "Click Save"], "Basic plan, 1 seat", "Clear seat-limit message and no orphan user (observed: redirect to Subscription)"),
    ("Add New User without Role", "P1", "Negative", ["Open Add New User", "Fill fields except Role", "Click Save"], "no role", "Inline error on Role"),
    ("Add New User with a mobile from another tenant", "P1", "Security", ["Open Add New User", "Enter a mobile registered elsewhere", "Click Save"], "registered number", "Generic message that does not reveal other tenants"),
    ("Add New User Date Of Birth 29/02/1900", "P2", "Boundary", ["Open Add New User", "Pick 29/02/1900 in Date Of Birth"], "29/02/1900", "Date rejected (not a leap year)"),
    ("Add New User postcode 4 digits", "P2", "Validation", ["Open Add New User", "Enter 2000 in Postcode"], "2000", "Accepted"),
    ("Add New User state list has only AU states", "P2", "Validation", ["Open Add New User", "Open the State list"], "-", "NSW, VIC, QLD, WA, SA, TAS, ACT, NT only; no duplicates"),
    ("Add New User tag creation", "P3", "Functional", ["Open Add New User", "Type Electrician in Tags", "Press Enter"], "Electrician", "Tag created and shown"),
    ("Add Group and assign members", "P1", "Functional", ["Open User", "Open Groups", "Add a group", "Choose members", "Save"], "Electrical Crew", "Group lists its members (observed: members showed 0 after an API update)"),
    ("Keyboard-only completion of Add Customer", "P2", "Accessibility", ["Open Add Customer", "Press Tab through every field", "Press Enter on Save"], "-", "Logical focus order; errors are announced"),
]

CK = [
    ("Add Item with sell and cost price", "P0", "Functional", ["Open Items", "Click Add Item", "Enter Item Name", "Enter Unit", "Enter Sell Price", "Enter Cost Price", "Enter Description", "Click Save"], "Labour - Electrician / hour / 110 / 71.50", "Item saved"),
    ("Item cost price above sell price", "P1", "Validation", ["Open Add Item", "Enter Sell Price 100", "Enter Cost Price 120", "Click Save"], "100 / 120", "Warning or rejection (negative margin); NEEDS UI INSPECTION"),
    ("Item negative sell price", "P1", "Negative", ["Open Add Item", "Enter -0.01 in Sell Price", "Click Save"], "-0.01", "Rejected"),
    ("Item sell price with 3 decimals", "P2", "Boundary", ["Open Add Item", "Enter 1100.005 in Sell Price", "Click Save"], "1100.005", "Rounded or rejected to 2 dp"),
    ("Item price typed as $1,100.00", "P2", "Validation", ["Open Add Item", "Type $1,100.00 in Sell Price"], "$1,100.00", "Number field rejects the symbols or normalises"),
    ("Add Invoice with 1 line", "P0", "Functional", ["Open Invoices", "Click Add Invoice", "Select Customer", "Enter Invoice Date", "Enter Due Date", "Add a line item", "Click Save"], "2 x $630.00", "Sub-total $1,260.00, GST $126.00, total $1,386.00"),
    ("Invoice GST is 10 percent of the sub-total", "P0", "Functional", ["Create an invoice of $1,100.00", "Read the total"], "$1,100.00", "Total shows $1,210.00"),
    ("Invoice with line discount", "P1", "Functional", ["Add a line with 10 in Discount", "Read totals"], "10%", "Discount applied before GST"),
    ("Invoice due date before invoice date", "P1", "Negative", ["Set Invoice Date 19/09/2026", "Set Due Date 18/09/2026", "Click Save"], "18/09/2026", "Rejected"),
    ("Invoice with quantity 0", "P1", "Boundary", ["Add a line with Quantity 0", "Click Save"], "0", "Rejected or line removed"),
    ("Invoice with negative rate", "P1", "Negative", ["Add a line with Rate -10", "Click Save"], "-10", "Rejected"),
    ("Invoice without a customer", "P1", "Negative", ["Leave Customer empty", "Click Save"], "empty", "Inline error"),
    ("Invoice status order: Draft, Awaiting Approval, Awaiting Payment, Paid", "P0", "Functional", ["Create a draft invoice", "Submit for approval", "Approve", "Record payment"], "-", "Each change allowed only in order; dashboard tiles update"),
    ("Invoice amounts cannot be set through the API", "P0", "Security", ["Send PUT invoice/update with amountPaid equal to the total", "Read the invoice"], "amountPaid = total", "Rejected (observed: accepted, finding F1)"),
    ("Invoice BSB accepts XXX-XXX only", "P1", "Validation", ["Open payment details", "Enter 062000", "Enter 062-000"], "062-000", "Hyphenated format accepted; BSB screen NEEDS UI INSPECTION"),
    ("Company ABN checksum", "P1", "Validation", ["Open Settings, Company Settings", "Enter 33 102 417 032", "Enter 12 345 678 901"], "valid / invalid ABN", "Valid accepted; invalid rejected"),
    ("Add Quote requires at least one item", "P0", "Negative", ["Open Quote", "Click Add Quote", "Select Customer", "Enter Quote Description", "Click Next", "Save with no items"], "no items", "Rejected: A quote must contain at least one item"),
    ("Add Quote with sections and items", "P0", "Functional", ["Add a Labour section", "Add a line item", "Add a Materials section", "Add a line item", "Save"], "2 sections", "Quote saved with a serial number"),
    ("Quote formula: Qty x Rate x 1.2", "P0", "Functional", ["Open Quote, Formulas", "Click Add Formula", "Enter a Column Name", "Pick Qty.", "Pick x", "Pick Rate", "Pick x", "Insert 1.2", "Click Save"], "Qty 10, Rate 50", "Live preview shows 600.00"),
    ("Quote formula cannot end on an operator", "P1", "Validation", ["Add a formula", "Pick Qty.", "Pick x"], "Qty. x", "Save stays disabled until the formula is complete"),
    ("Quote formula column shown on the customer PDF", "P2", "Functional", ["Turn on Show to Customer", "Save", "Open the quote PDF"], "-", "Column printed; internal columns hidden"),
    ("Quote line types Labour and Material", "P1", "Functional", ["Add a Labour line", "Add a Material line", "Read the quote"], "labour / material", "Types shown correctly"),
    ("Job with a report template attached", "P1", "Functional", ["Open a job", "Open Reports", "Attach a template", "Save", "Open Job Report"], "Electrical Job Completion Report", "Report created with status Created"),
    ("Job cap on the Solo plan", "P1", "Functional", ["Create 6 active jobs on Solo"], "6th job", "Blocked with a plan-limit message (observed 403)"),
    ("Job start and end time", "P1", "Functional", ["Open Add Job", "Enter Start Date", "Enter End Date", "Save"], "16/09/2026 to 17/09/2026", "Job shows on the week schedule"),
    ("Job Site Radius 1 to 10,000 m", "P2", "Boundary", ["Enter Site Radius 0", "Enter Site Radius 10001"], "0 / 10001", "Both rejected; 1 and 10000 accepted"),
    ("Holiday create and duplicate date", "P2", "Negative", ["Add Holiday 26/01/2026", "Add another on the same date"], "26/01/2026", "Second rejected (observed 409)"),
    ("Checklist item order", "P3", "Functional", ["Open Checklist", "Add 3 items", "Save"], "3 items", "Items keep their order"),
    ("Report template builder field types", "P2", "Functional", ["Open Report Builder", "Add each field type", "Save"], "Textbox, Dropdown, Radio, Checkbox, Textarea, Number, Upload, Email, Date", "Template saved and renders on a job report"),
    ("Dashboard tiles match the data", "P0", "Regression", ["Open Dashboard", "Compare each tile with its list"], "-", "Jobs, Completed, Revenue, Outstanding and Pending counts match the lists"),
]

CT = [
    ("Terms & Conditions link opens the terms page", "P1", "Functional", ["Open the login page", "Click Terms & Conditions"], "-", "Opens /terms-and-conditions"),
    ("Privacy Policy link opens the privacy page", "P1", "Functional", ["Open the login page", "Click Privacy Policy"], "-", "Opens /privacy-policy"),
    ("CMS list shows Type, Created By and Date", "P2", "Functional", ["Open CMS"], "-", "Columns TYPE, CREATED BY, DATE, ACTION shown"),
    ("Add a CMS entry of each type", "P1", "Functional", ["Click Add CMS", "Select Type", "Enter Title", "Enter Content", "Click Save"], "Induction, Help, Privacy Policy, Terms & Conditions, FAQ", "Entry appears in the list"),
    ("CMS Title empty", "P1", "Negative", ["Click Add CMS", "Select Type", "Leave Title empty", "Save"], "empty", "Inline error (the API returns 500, finding F3)"),
    ("CMS Content empty", "P1", "Negative", ["Click Add CMS", "Enter Title", "Leave Content empty", "Save"], "empty", "Inline error"),
    ("CMS rich text stores a script safely", "P1", "Security", ["Enter a script tag in Content", "Save", "View the page"], "XSS payload", "Sanitised; no alert"),
    ("CMS Title 255 chars", "P2", "Boundary", ["Enter 255 chars in Title", "Save"], "255", "Accepted or rejected consistently; limit NEEDS UI INSPECTION"),
    ("Notifications page lists events", "P2", "Functional", ["Open Notifications"], "-", "Recent events listed; unread count clears"),
    ("Notification badge increments after a new job", "P3", "Functional", ["Create a job", "Read the sidebar badge"], "-", "Badge increases by 1"),
    ("Help entries are findable", "P3", "Functional", ["Open Help content", "Search for invoice"], "invoice", "Matching entries shown; help UI NEEDS UI INSPECTION"),
    ("Support contact page exists", "P2", "Functional", ["Look for a Support or Contact page"], "-", "NEEDS UI INSPECTION: no contact form was observed"),
    ("Contact form rejects an invalid email", "P2", "Validation", ["Open the contact form", "Enter noah.smith@bigpond", "Submit"], "noah.smith@bigpond", "Blocked; depends on the form existing"),
    ("Contact form mobile format", "P2", "Validation", ["Enter +61 412 345 678", "Enter 0412ABC678"], "AU mobiles", "First accepted, second rejected"),
    ("Login footer links are keyboard reachable", "P3", "Accessibility", ["Open the login page", "Press Tab to the footer links"], "-", "Both links focusable with a visible focus ring"),
]


def rows(code, cases):
    out = ["| ID | Title | Module | Preconditions | Steps | Test Data (AU) | Expected Result | Priority | Type |", "|----|-------|--------|---------------|-------|----------------|-----------------|----------|------|"]
    for i, (t, p, ty, steps, data, exp) in enumerate(cases, 1):
        out.append(f"| FLD-{code}-{i:03d} | {t} | {code} | Logged in as the QA user | {n(steps)} | {data} | {exp} | {p} | {ty} |")
    return "\n".join(out)


auth = open(os.path.join(HERE, "auth-test-cases.md"), encoding="utf-8").read()
auth_rows = [l for l in auth.splitlines() if l.startswith("| FLD-AUTH-")]
counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
for l in auth_rows:
    counts[[c.strip() for c in l.split("|")][-3]] += 1
for cs in (REG, CK, CT):
    for c in cs:
        counts[c[1]] += 1
total = sum(counts.values())

csvs = {}
for f in sorted(os.listdir(os.path.join(HERE, "csv"))):
    with open(os.path.join(HERE, "csv", f), encoding="utf-8") as fh:
        rr = list(csv.reader(fh))[1:]
        csvs[f[:-4]] = (len(rr), sum(1 for r in rr if r[3].startswith("ACCEPT")), sum(1 for r in rr if r[3].startswith(("REJECT", "TRUNC"))))

plan = f"""# Fieldr Test Plan

**Observed 2026-09-19 on the live dev tenant:** login and OTP screens, Dashboard, Customer, User, Quote (with Formulas), Job (all tabs), Timesheet, Job Report, Invoices, Items, CMS, Settings (Company, Holidays, Checklists, Report Builder, Subscription, Payment Cards). Items marked ASSUMPTION or NEEDS UI INSPECTION were not observed.

## 1. Executive summary
- Scope: authentication, adding people, commercial documents (items, quotes, invoices, jobs), content and legal pages.
- Total cases: **{total}** (AUTH {len(auth_rows)}, REG {len(REG)}, CKOUT {len(CK)}, CONT {len(CT)}).
- Priority split: P0 {counts['P0']}, P1 {counts['P1']}, P2 {counts['P2']}, P3 {counts['P3']}.
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
### AUTH: authentication and sessions ({len(auth_rows)} cases)
Full table: [auth-test-cases.md](auth-test-cases.md), generated from the Playwright specs.

### REG: adding people: customers, users, groups ({len(REG)} cases)
{rows('REG', REG)}

### CKOUT: items, quotes, formulas, invoices, jobs, settings data ({len(CK)} cases)
{rows('CKOUT', CK)}

### CONT: CMS, notifications, legal and contact ({len(CT)} cases)
{rows('CONT', CT)}

## 4. Negative and boundary matrix
One row per field. Counts come from `csv/<field>.csv`; the expected result for every value is in the CSV.

| Field | Total values | Expect accept | Expect reject |
|---|---|---|---|
""" + "\n".join(f"| {k} | {v[0]} | {v[1]} | {v[2]} |" for k, v in csvs.items()) + """

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
"""
open(os.path.join(HERE, "test-plan.md"), "w", encoding="utf-8").write(plan)

lib = """# Test data table (AU library)

Values are used verbatim. They are typed only unless a case says otherwise. Full per-field lists with expected results are in `csv/` (each file has 100+ rows).

## Mobile
| Kind | Values |
|---|---|
| Valid | +61 412 345 678, +61 423 456 789, +61 434 567 890, +61 458 901 234, +61 401 234 567 |
| National | 0412 345 678, 0423 456 789 |
| Negative | +61 12 345 6789 (no mobile prefix), +1 412 345 6789 (US), +61 4 (prefix only), 0412ABC678, whitespace, emoji |
| Boundary | 9, 10, 11, 12 and 15 digits |
| Warning | 0412 345 678 and 0491 570 159 were already registered to other accounts; do not submit them |

## Email
| Kind | Values |
|---|---|
| Valid | olivia.nguyen@example.com.au, noah.smith@bigpond.net.au, mia.collins@aussie.com.au, jack.wilson+invoices@gmail.com |
| Seeded records | @yopmail.com only |
| Negative | no @, missing TLD, double dot, leading or trailing space, IDN homoglyph, local part over 64 |
| Boundary | local 1, 64 and 65 chars; total 254, 255 and 256 chars |

## OTP
| Kind | Values |
|---|---|
| QA bypass | set in `.env` as FLDR_OTP (6 digits) |
| Valid format | 100000, 999999, 482913 |
| Negative | 99999 (5 digits), 1000000 (7 digits), abcdef, empty, 12 34 56, 000000, 111111 |

## Addresses
| State | Address |
|---|---|
| NSW | 12 Macquarie Street, Sydney NSW 2000 |
| VIC | 88 Bourke Street, Melbourne VIC 3000 |
| QLD | 145 Eagle Street, Brisbane QLD 4000 |
| WA | 27 Adelaide Terrace, Perth WA 6000 |
| SA | 101 Rundle Mall, Adelaide SA 5000 |
| TAS | 9 Brisbane Street, Hobart TAS 7000 |
| ACT | 21 London Circuit, Canberra ACT 2601 |
| NT | 76 Mitchell Street, Darwin NT 0800 |

Postcode ranges used: ACT 0200-0299, 2600-2618, 2900-2920; NT 0800-0999; NSW 1000-2599, 2619-2898, 2921-2999; VIC 3000-3999, 8000-8999; QLD 4000-4999, 9000-9999; SA 5000-5999; WA 6000-6999; TAS 7000-7999.

## Finance identifiers
| Kind | Values |
|---|---|
| ABN valid | 33 102 417 032 (mod-89) |
| ABN invalid | 12 345 678 901 |
| TFN valid | 123 456 782 (mod-11) |
| TFN invalid | 123 456 789 |
| BSB | 062-000, 123-456, 032-198 |
| Account | 6 to 9 digits; negatives: letters, more than 4 leading zeros |
| Currency | AUD, "$" prefix, 2 decimals, GST 10% (subtotal $1,100.00 gives total $1,210.00) |

## Names
First: Olivia, Noah, Mia, Jack, Aria, Liam, Charlotte, William, Zoe, Ethan. Last: Nguyen, Smith, Collins, Wilson, Patel, Brown, Anderson, Lee, Khan, White. Negatives: User1234, emoji only, 200+ characters, only spaces.
The seed script uses a wider pool of 50 first and 50 last names so seeded customers have unique full names.

## Dates (dd/mm/yyyy)
Valid: 14/02/1990, 29/02/2000 (leap), 01/01/1900, 31/12/2025. Invalid: 29/02/1900, 31/04/2024, 32/01/2024, 00/01/2024, 13/13/2024.

## Files generated
| File | Rows |
|---|---|
""" + "\n".join(f"| csv/{k}.csv | {v[0]} |" for k, v in csvs.items()) + "\n"
open(os.path.join(HERE, "test-data-table.md"), "w", encoding="utf-8").write(lib)
print("total cases", total, counts)

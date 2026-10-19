# Fieldr: Customers, Jobs and release-notes bugs (2026-10-07)

Tenant: rajanjagz7.dev.fieldr.app. Run headed in Chrome. Everything below was observed in the live app.

## Customers

| ID | Bug | Severity | Evidence |
|---|---|---|---|
| CUS-1 | First Name and Last Name must be 3 to 35 characters, so real names such as Li, Ng, Wu, Ho or Jo cannot be saved. | Medium | Add Customer: first name "Jo" and last name "D" both show "... must be between 3 to 35 characters" and no request is sent. |
| CUS-2 | Saving without a Description shows its error below the fold. The page does not scroll to it, so Save looks like it does nothing. | Medium | Error "Please enter a valid description" exists but is outside the viewport (1440x900). Same as C2 in CRASH_CHECK_2026-09-21.md; still reproduces. |
| CUS-3 | Company Name has no maximum length. | Low | A 300-character company name saved (HTTP 200, CST-0106). The list card shows only part of it. |
| CUS-4 | An email with no TLD (marcus@yopmail) passes the form check and is rejected only by the server with 400 "Enter a valid email address". No inline error was found. | Low | Client says valid, server says invalid. A toast may appear; I did not capture one. |

Working as expected: duplicate email is blocked ("This customer already exists in your company"), mobile too short or non-numeric is blocked, whitespace-only description is blocked, and a mobile typed with a leading 0 is stored without it (+61 431000222). The earlier trunk-zero finding (C7) did not reproduce.

## Jobs

| ID | Bug | Severity | Evidence |
|---|---|---|---|
| JOB-1 | Job Title has no minimum or maximum length. | Low | Step 1 advanced with a 1-character and a 300-character title. Customers enforce 3 to 35. Not saved, so server-side behaviour is unverified. |
| JOB-2 | Site Radius accepts a fractional value (1.5) although the field is a whole number of metres. | Low | Step 1 advanced with 1.5. Not saved. |

Working as expected: radius 0, negative, over 10,000 and letters are blocked with clear messages, radius 1 and 10,000 pass, end date earlier than start is disabled in the picker, whitespace-only title is blocked, and Description is optional and capped at 2000 characters. A job saved with no description (JOB-0279, HTTP 200) and the default radius of 1000 m.

| JOB-3 | Job Title is silently truncated at the first "<" character, so data is lost with no warning. | Medium | Edit JOB-0279, title `Switchboard upgrade & rewire - O'Brien's Level 2 <fitout>`, Save (PUT job/update 200). The edit field, the job header and the job list all show `... Level 2 <`. The job Description and the customer Company Name keep "<" correctly, so this is specific to the title. |
| JOB-4 | Job search matches job number, title, customer name and company, but not customer email, phone or site address, while customer search does match email. | Low | Searching `priya.venkatesan.202657@yopmail.com`, `0420002657`, `88 Bourke` and `Bulleen` returns no jobs. The field says "Search Job or Customer or Company", so this may be by design. |
| CUS-5 | Customer search does not match phone numbers or a reversed name order ("Venkatesan Priya"). | Low | `0420002657`, `420002657` and `+61 420 002 657` return "No customers found". The field says "Search Customers or Contact or Company", so this may be by design. |

## Exploratory results that were not bugs
- Customer search (typed normally) is case-insensitive and matches company, name, email, customer ID and partial text. Unmatched text, `%`, SQL-style text and `<script>` return "No customers found" with no error.
- A 300-character company name is clipped in the customer header without breaking the layout.
- Edit Job: clearing the title is blocked ("Please enter a job title"); a valid edit saves (PUT 200).
- An earlier run of fast search inputs showed the unfiltered list for unmatched terms. It did not reproduce when typing normally, so it is treated as a timing effect of the test, not a bug.
- The customer edit page once showed "—" and no form for over 6 seconds on a direct link. It loaded normally on later attempts, so it is recorded as the same intermittent slow-loading behaviour as C1.

## Regression
Full pytest suite on 2026-10-07: 43 passed, 2 failed, 1 skipped (14 min 36 s). The 2 failures are the known New Role menu item and Roles Name sort checks. The skip is the Activity Logs search (no search box). No new regressions.

## Release-note gaps and related bugs

| ID | Bug | Severity | Evidence |
|---|---|---|---|
| REL-1 | "New Role" is not in the Create menu. | Medium | Menu lists Job, Customer, User, Quote, Invoice, Item, CMS, Post, Report. The tenant may not be on this release. |
| REL-2 | Clicking Name on Roles & Permissions does not switch to Z to A on the first click. | Low | List stays Customer, User after one click; a second click gives User, Customer. |
| REL-3 | No way to create a role from a job's Team step. | Medium | Assign By Role and the Add User role field only offer "User". Typing a new name gives "No options". |
| INV-1 | Invoice PDF dates are one day earlier than the app. | Medium | App shows Invoice Date 05 Oct 2026 and Due 19 Oct 2026. PDF for INV-00184 says Issued Oct 04, 2026 and Due Oct 18, 2026. Quote PDFs are correct (Issued On 05 Oct 2026). |
| INV-2 | Copyright symbol in the PDF footer extracts as a replacement character. | Low, unconfirmed | Text extraction shows "� 2026 Rajan". Not checked visually, so it may only be an extraction issue. |

## Passing release-note checks
Add Shift defaults to today 9:00 am to 5:00 pm. Add User opens on the Schedule, saves with no Industry, and a new shift then opens with that user already on it. Address pick fills Suburb, State and Postcode. Industry is optional on edit. Company name shows first in customer, job, quote and invoice lists, in the quote header, and in the invoice and both quote PDFs. Create Job from a customer pre-selects the customer. The New Job customer list shows "Loading customers..." and searches by company, name, email and customer ID.

## Records left behind (for cleanup)
- Customers: CST-0104 Priya Venkatesan / Harbourline Electrical Pty Ltd; CST-0105, CST-0106 (300-character company name), CST-0107, all named Marcus Delaney.
- Job JOB-0279, quote QTE-0108, invoice INV-00184 (Harbourline).
- User Daniel Okafor-Eze (daniel.okafor.360958@yopmail.com).
- Quote and report created by the existing quote and report tests.

## Not covered
Job-side server validation for the title and radius edge cases (nothing was saved), job list filters, job status changes, and the earlier API findings (F2, F8) were not re-run.

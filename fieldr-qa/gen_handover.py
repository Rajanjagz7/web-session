"""Build HANDOVER.md: status, bugs, test report, how-to-run and the full source of every script. Skips .env (secrets)."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read().rstrip()


def demote(md, by=1):
    """Push every heading down so embedded documents nest under the handover headings (skips code fences)."""
    out, fence = [], False
    for line in md.splitlines():
        if line.startswith("```"):
            fence = not fence
        if not fence and line.startswith("#"):
            line = "#" * by + line
        out.append(line)
    return "\n".join(out)


SCRIPTS = [
    ("fieldr_seed.py", "Seeds the tenant through the REST API (customers, items, invoices, jobs, quotes, formulas, CMS, holidays, checklists, templates, job enrichment, report filling, invoice statuses)."),
    ("gen_csv.py", "Generates the 14 per-field AU CSVs (100+ rows each) with computed expected results (ABN mod-89, TFN mod-11, postcode ranges, leap years)."),
    ("gen_avatars.py", "Generates 100 illustrated avatar PNGs locally (Pillow)."),
    ("gen_pw.py", "Generates the Playwright TypeScript project (page objects, modules, fixtures, config) and FLD-AUTH-001 to 050 specs plus auth-test-cases.md."),
    ("gen_plan.py", "Generates test-plan.md and test-data-table.md from the case lists and the CSVs."),
]

doc = f"""# Fieldr QA Handover

Tenant: `rajanjagz7.dev.fieldr.app` (dev). Prepared 2026-09-19. Everything below was observed in this run unless it is marked ASSUMPTION or "not verified".

## 1. Where things stand

| Area | State |
|---|---|
| Plan | Basic ($49/mo), Stripe test mode. At the end of the session the subscription page showed 101 seats (100 purchased extra seats) plus the Chat & Feed and Defect Management add-ons as Added. None of these were clicked by the assistant; check who bought them (about $1,249/mo of add-ons in test mode) |
| Customers | 101, unique AU names, @yopmail.com emails, unique realistic mobiles, profile photos |
| Items | 100, different margin on each, labour/material types set |
| Invoices | 180: Paid 55, Awaiting Payment 56, Awaiting Approval 59, Draft 10 |
| Jobs | 277 across Schedule, In Progress, On Hold, Completed, Cancelled, with AEST dates, coordinates, report templates, checklists and planned items |
| Job Reports | 375, fields filled, 4 statuses |
| Quotes | 101 with sections, line types and formula columns; 6 valid formulas |
| CMS / Holidays / Checklists / Templates | 40 / 27 / 3 / 3 |
| Users and groups | 3 groups created (members show 0). 6 users created over the API return 200 but never appear in the Users list, even after the seats were added, so the API payload is missing something the UI form sends. Not finished |
| Timesheets and Crew Clocked On | Not filled: the timelog API stores nothing |
| Playwright specs | 50 generated (FLD-AUTH-001 to 050), not installed or run |
| Payment cards | None added |

## 2. Next steps
1. Create one user through the UI form (Add User: First Name, Last Name, Industry, Role, Tags, Email, Mobile) and capture its `POST /user/create` body with DevTools, compare it with the API payload used in this session, then seed the rest, add them to groups and add tags. Use ACMA-reserved or otherwise safe mobiles; invites can send SMS.
2. Find how timesheets are created (mobile clock-on payload or a clock-on button on a job) and seed them.
3. `cd pw`, copy `.env.example` to `.env`, fill in the QA mobile and OTP, run `npm install`, `npx tsc --noEmit`, then `npx playwright test --project=chromium --grep @smoke`.
4. Delete the probe records listed at the end of the bug report.
5. Re-check the dashboard: every tile should show 50+ records except Crew Clocked On and Schedule This Week.

## 3. Bugs found so far and the API/security test report
{demote(read('SECURITY_API_TEST_REPORT.md'))}

## 4. Test plan
{demote(read('test-plan.md'))}

## 5. Test data table
{demote(read('test-data-table.md'))}

## 6. How to run the code
```
# 1. data files
python gen_csv.py            # csv/*.csv
python gen_avatars.py        # seed-images/avatar-001..100.png
python gen_pw.py             # pw/ project + specs + auth-test-cases.md
python gen_plan.py           # test-plan.md, test-data-table.md
python gen_handover.py       # this document

# 2. seed the tenant (log in in a browser first, copy the connect.sid cookie value)
set FLDR_COOKIE=<connect.sid value>
set FLDR_BASE_URL=https://rajanjagz7.dev.fieldr.app
python fieldr_seed.py --customers 100 --items 100 --invoices 100 --jobs 60 --avatars seed-images
python fieldr_seed.py --fix-items --quotes 100 --cms --holidays --settings-data
python fieldr_seed.py --enrich-jobs --fill-reports --invoice-statuses
```
Notes: never commit `FLDR_COOKIE`, the OTP or `pw/.env`. `--invoice-statuses` relies on finding F1 (client-set payment fields), so use it on a throwaway tenant only. The seeded mobile numbers may belong to real people, so keep SMS notifications off.

## 7. Source code
"""
for i, (name, blurb) in enumerate(SCRIPTS, 1):
    doc += f"\n### 7.{i} `{name}`\n{blurb}\n\n```python\n{read(name)}\n```\n"

doc += "\n### 7.6 Playwright project files (generated by `gen_pw.py`)\nThe project lives in `pw/`. Key files: `playwright.config.ts`, `src/config/index.ts`, `src/pages/LoginPage.ts`, `src/pages/DashboardPage.ts`, `src/modules/LoginModule.ts`, `src/fixtures/index.ts`, and 50 specs in `src/tests/auth/`. They are produced by `gen_pw.py` above, so that script is the source of truth.\n"

with open(os.path.join(HERE, "HANDOVER.md"), "w", encoding="utf-8") as f:
    f.write(doc + "\n")
print("HANDOVER.md", len(doc), "chars")

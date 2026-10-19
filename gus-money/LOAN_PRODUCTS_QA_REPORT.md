# Loan Products - Negative & Edge-Case QA Report

**Target:** https://gusdev.softwareco.com/loan-products (Gus Money admin, dev) | **Date:** 2026-10-05 | **Tester role:** Super Admin (`admin@yopmail.com`)
**Finding prefix:** `GUS-FX-####`

## Evidence index

The six-prompt pipeline named in the brief was not used in this engagement. Every claim below cites one of these runs instead.

| Id | What it is | Result |
| --- | --- | --- |
| **E1** | Exploratory create probe, `POST /products` with ~85 invalid/edge bodies (every accepted record deleted afterwards) | Output quoted per finding |
| **E2** | Exploratory create probe, numeric/term cases (run cut short by the write limit at `termMonths [12,12]`) | 40 cases returned real results; the rest returned 429 and are discarded |
| **E3** | Exploratory read probe, `GET /products`, `GET /products/:id`, unauthenticated calls for all 5 methods | 48 cases |
| **E4** | Rate-limit probe (`rl3`) | Write limit confirmed, see GUS-FX-0013 |
| **E5** | Browser exploration of the Add form with writes intercepted | Payloads quoted per finding |
| **E6** | `tests/loan-products.spec.ts` (UI, 71 tests, all writes intercepted) | 71 passed, of which 11 are marked expected-fail for GUS-FX-0010, 0011, 0012 and Q4 |
| **E7** | `api/tests/test_loan_products_api.py` core tier, 109 tests, one run | 99 passed, 10 xfailed, 0 skipped, 0 failed |
| **E8** | Post-run read-back of `GET /products` | 1 product remains (the pre-existing seeded one) |
| **E9** | `api/tests/test_loan_products_fees_concurrency.py` (fees + races), run once with `WRITE_BUDGET=38` | 13 passed, 1 xfailed (Q9), 1 xpassed (fee cap exists), 0 failed |
| **E10** | UI lifecycle of a product I created: Deactivate, Activate, Delete permanently, executed for real through the UI, then read back | Quoted under Observations |
| **E11** | Read of `GET /roles` and `GET /users?scope=admin` | 3 roles, 1 admin account |

---

## STEP 1 - Coverage table

| endpoint | method | auth-needed | covered-by | outcomes-tested | not-tested | blocked-by | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/products` | POST | yes | E1, E2, E5, E6, E7 | missing/invalid each of 11 fields; boundaries of name (2/120/121), rate (0/10000/10001 bps), amount (min=max, 1 cent, 1e15), term (1/600/1000); wrong JSON types; NoSQL/SQL/HTML in name; unknown + server-controlled fields; duplicate (409); invalid lender, non-existent lender, inactive lender; 401 without token | the 44 `extended` cases of `test_loan_products_api.py` (E7 ran core only); `requiresBankConnection` input; payload size limits. Fees are now covered (E9); the duplicate-create race is now covered (E9) | 100 writes/hour limit (GUS-FX-0013) | Accepted records were deleted in teardown (E8) |
| `/products` | GET | yes | E3, E6, E7 | pagination bounds (skip -1/abc/1.5/999999, limit 0/100/101/abc), filters (type, lenderId, isActive, search), 8 hostile search strings, search >100 chars, invalid sort, 401 | sort by valid fields beyond `createdAt`/`interestRateBps`/`name`; result ordering correctness; behaviour with more than 20 products (only 1 exists on dev) | no data volume on dev | |
| `/products/:id` | GET | yes | E3, E6, E7 | malformed ids (4 shapes), non-existent id (404), upper-case hex id (200), path traversal, response integer typing, no internal fields leaked, 401 | cross-tenant/other-role access | no second account | Only 1 account available |
| `/products/:id` | PUT | yes | E5, E6, E7 | invalid name/type/rate/term (422); min raised above max on a partial update (422); non-existent id (404); malformed id (422); valid round-trip with read-back; deactivate then filter by `isActive`; 401 | the 4 `extended` update cases (`name` 121, rate 10001, `minAmountCents` -1, bad lender); updating `criteria` or `fees` (the Edit page has no criteria section, see Q6); lost update with stale data (the record has no version field, so a true lost-update check is not possible); parallel edits are covered (E9) | write limit | |
| `/products/:id` | DELETE | yes | E7 | non-existent id (404), malformed id (422), double delete (200 then 404), read-back 404 after delete, 401 | behaviour for a non-full-access role (the dialog says "Delete permanently needs full access"); hard vs soft delete; parallel deletes are covered (E9) | no restricted account, see Roles below | Delete of data created by tests only |
| `/lenders` | GET | yes | E1, E3 | list read to obtain lender ids | negative cases (out of scope for this report) | | |
| `/auth/login` | POST | no | earlier Users report | covered in `test_negative_api.py` | | | |
| UI `/loan-products` | list | yes | E6 | render, 3 filters, search incl. 7 hostile inputs, Clear, empty state, mocked: HTML name, 120-char name, 0%/100%/min-max boundaries, missing term/lender, 500, 429 | pagination controls with >20 rows; keyboard/a11y; mobile widths | | |
| UI `/loan-products/new` | form | yes | E5, E6 | required errors, 8 invalid rates, amounts, min>max, negative min, whitespace name, 121-char name, custom terms (7), criteria (7), fee row, float-drift check, double-click submit, mocked 422/500/429 | real end-to-end create through the UI (writes intercepted by design); fee with valid data | | |
| UI `/loan-products/:id`, `/edit` | page | yes | E6 | invalid/unknown id, pre-fill, invalid edits blocked, only changed field sent, Stop offering confirm/cancel/Escape | nothing outstanding for Super Admin: Deactivate, Activate and Delete permanently were executed in E10 | | |

---

## STEP 2 - Findings (ordered by severity)

### GUS-FX-0012 - Add form silently drops invalid eligibility criteria and still submits
- **endpoint:** `POST /api/proxy` (target `/products`), from UI `/loan-products/new`
- **request:** form filled validly with Minimum age = `21` and Minimum income = `-1`. Captured payload (E5, request intercepted, not sent to the server):
  ```json
  {"lenderId":"6ab119e3983eb386149dce1b","name":"Everyday Personal Loan","type":"personal_loan","interestRateBps":749,"minAmountCents":500000,"maxAmountCents":5000000,"comparisonRateBps":812,"termMonths":[36],"criteria":{"minAgeYears":21}}
  ```
- **expected:** a field error and no submission. The server contract rejects negative income with 422 (E7: `test_invalid_criteria[...minIncomeCentsPerYear: -1]` passed).
- **actual:** no error shown (`errs: []`); the invalid field is omitted from the payload and the form submits. Same for min age `-1`, min age `18.5`, DTI `abc`, surplus `-1` (E5: each returned `"NO criteria key"`/dropped value).
- **how-verified:** payload diff between filled form and submitted body (E5); valid control cases sent all values (`{"minAgeYears":21,"maxAgeYears":60}`).
- **impact:** data loss. The admin believes eligibility rules were saved; the product is created with fewer or none.
- **surfaces affected:** UI only (the API validates correctly).
- **reproducer:** open `/loan-products/new`, fill valid data, set "Minimum income (AUD / year)" = `-1`, click Create product, inspect the request body. Automated: `LP-032` (expected-fail).
- **suggested fix direction:** the criteria parsing in the Add/Edit product form component: treat a non-empty value that fails parsing as a validation error instead of mapping it to `undefined`.

### GUS-FX-0001 - `POST /products` with a JSON string body returns 500
- **endpoint:** `POST /api/proxy` target `/products`
- **request:** `x-target-endpoint: /products`, `content-type: application/json`, body `"x"`
- **expected:** 4xx with `VALIDATION_ERROR` (an array body returns 422, E1: `body is a list 422 VALIDATION_ERROR`).
- **actual (E1):** `body is a string  500 INTERNAL | Something went wrong`
- **how-verified:** direct call, status and code read back; `test_body_is_string_json` xfail confirmed in E7.
- **impact:** UX/robustness; generic message, no stack trace leaked (E1).
- **surfaces affected:** integration-only.
- **reproducer:** `curl -X POST https://gusdev.softwareco.com/api/proxy -H 'x-target-endpoint: /products' -H 'content-type: application/json' --cookie 'gus_dev_access=<token>' -d '"x"'`
- **suggested fix direction:** request-body schema validation middleware: non-object JSON must hit the same 422 path as arrays.

### GUS-FX-0002 - Malformed JSON body returns 500
- **request:** same endpoint, `content-type: application/json`, body `{bad json`
- **expected:** 400 with a parse error.
- **actual (E2):** `malformed json: 500 {"success":false,"message":"Something went wrong","code":"INTERNAL"}`
- **how-verified:** direct call; `test_malformed_json` xfail in E7.
- **impact:** robustness; masks client errors as server errors in monitoring.
- **surfaces affected:** integration-only.
- **reproducer:** as above with `-d '{bad json'`.
- **suggested fix direction:** body-parser error handler (map `SyntaxError` to 400).

### GUS-FX-0003 - NUL byte in `name` returns 500
- **request:** valid body with `"name": "Home Saver\u0000Plan"`
- **expected:** 422 on `name`.
- **actual (E1):** `name null byte  500 INTERNAL | Something went wrong`
- **how-verified:** direct call; `test_null_byte_rejected_cleanly` xfail in E7.
- **impact:** robustness; input that reaches the persistence layer unvalidated.
- **surfaces affected:** all (any free-text field is a candidate; only `name` tested).
- **reproducer:** body above via the same curl.
- **suggested fix direction:** name/text schema: reject control characters.

### GUS-FX-0010 - UI has no upper bounds for rate, name length and term
- **endpoint:** UI `/loan-products/new`
- **request (E5):** interest rate `101` produced `{"interestRateBps":10100,...}` sent with no client error; name of 121 chars sent; custom term `601` added as a chip.
- **expected:** blocked client-side. The server enforces: rate `<= 10000` bps (E2: `10001 -> The interest rate cannot exceed 100%`), name `<= 120` (E1), term `<= 600` (E2).
- **actual:** the form submits and relies on the server 422. With a 422 the UI shows the server message inline and keeps the data (E6 `LP-037` passed).
- **how-verified:** intercepted payloads (E5, E6 LP-022/023/028/030b expected-fail).
- **impact:** UX only.
- **surfaces affected:** UI.
- **reproducer:** type `101` in Interest rate, click Create product. Automated: LP-022, LP-023, LP-028, LP-030b.
- **suggested fix direction:** add max constraints to the product form schema, matching the API.

### GUS-FX-0004 - Invalid `sortBy`/`sortOrder` accepted on products, rejected on users
- **endpoint:** `GET /api/proxy` target `/products?sortBy=bogus` and `?sortOrder=sideways`
- **expected:** 422 (the Users list returns 422 for the same input, earlier Users report).
- **actual (E3):** `sortBy=bogus 200`, `sortOrder=bogus 200`, `sortBy=name' 200`
- **how-verified:** status read; xfail in E7 (2 params).
- **impact:** inconsistent API contract; silent no-op sort.
- **surfaces affected:** integration-only.
- **reproducer:** `curl -G .../api/proxy -H 'x-target-endpoint: /products' --data-urlencode 'sortBy=bogus' --cookie ...`
- **suggested fix direction:** list-query schema for products: enumerate allowed sort fields as the users list does.

### GUS-FX-0011 - Malformed product id page shows the raw API message
- **endpoint:** UI `/loan-products/zzz`
- **expected:** the same friendly text as an unknown id ("That product does not exist").
- **actual (E5 browser check of `/loan-products/zzz` and `/loan-products/000000000000000000000000`):** page body `Product not found | Validation failed | Back to products`; unknown id shows `Product not found | That product does not exist`.
- **how-verified:** page text compared across both ids; LP-040 expected-fail.
- **impact:** UX.
- **surfaces affected:** UI.
- **reproducer:** open `/loan-products/zzz`.
- **suggested fix direction:** product detail page error mapping: map 422 on `id` to the not-found message.

### GUS-FX-0013 - Writes limited to 100/hour, rejected requests count
- **endpoint:** every `POST|PUT|DELETE` via `/api/proxy`
- **request (E4):** a `POST /products` with body `{}` after the limit was reached.
- **actual (E4):** `429 after 0 empty POSTs; {'ratelimit-limit': '100', 'ratelimit-policy': '100;w=3600', 'ratelimit-remaining': '0', 'ratelimit-reset': '3371', 'retry-after': '3371'}`; 60 GETs afterwards were not limited.
- **how-verified:** headers read back; the window reset and the E7 run (109 tests) completed with 0 skips.
- **impact:** operational. Failed validation attempts spend the same quota as successful writes, so one scripted session blocks creating/editing/deleting for up to an hour. Not verified: whether the key is per user, session or IP.
- **surfaces affected:** all write paths. The UI list handles 429 gracefully when mocked (E6 LP-015, LP-038 passed); a real 429 on Create was not observed in the UI.
- **reproducer:** send 100 `POST /products` bodies of `{}` in under an hour, then one more.
- **suggested fix direction:** rate-limit middleware config for the admin API (count only successful mutations, or key per user with a higher ceiling).

### Observations (not defects)
- **Fees API (E9):** fee shape is `{"name","amountCents","frequency": "one_off"|"monthly"|"annual"}`. Valid fees round-trip exactly; invalid frequency, negative or fractional amount, empty or 121-char name, non-list and `[{}]` are rejected with 422; duplicate fee names do not error; 51 fees are rejected (the exact cap was not measured).
- **Concurrency (E9):** 3 simultaneous identical creates produced exactly one product (the others 409); 3 simultaneous PUTs all returned 200 and left a consistent record; 2 simultaneous DELETEs returned 200 and 404.
- **UI lifecycle (E10):** Deactivate sent `PUT {"isActive":false}` -> 200, toast "Product deactivated", the page then offered Activate and Delete. Activate asks for confirmation ("The product will be offered again."); Cancel sent nothing; confirming sent `PUT {"isActive":true}` -> 200, toast "Product activated". Read-back confirmed each state.
- **Delete permanently has no second confirmation (E10):** clicking it in the Stop offering dialog deleted the product at once (`GET /products/:id` then returned 404 `PRODUCT_NOT_FOUND`) and returned to the list. The dialog does warn that it cannot be undone, but the button sits beside the safe Deactivate button. Design question, see Q11.
- Interest-rate boundaries 0 and 10000 bps, `min == max` amount, terms `[1]` and `[600]`, names of 2 and 120 characters are accepted (E7 passed).
- Duplicate lender + type + name is rejected with 409 (E7 `test_duplicate_same_lender_type_name` passed).
- Server-controlled fields (`_id`, `createdAt`, `lender`, `isActive`, `role`) in the create body are ignored (E7 `test_server_controlled_fields_ignored` passed).
- UI sends exact integer basis points and cents (1.15% -> 115, 4.35% -> 435, 5000.10 -> 500010, E6 LP-035 passed) and a double-click on Create sends one request (LP-036 passed).
- Terms `[60,12,12,36]` are stored as `[12,36,60]` (E7 passed).

---

## STEP 3 - Blockers vs nice-to-have

| Bucket | Findings | Revenue / safety justification |
| --- | --- | --- |
| **P0 BLOCKER** | none | |
| **P1 HIGH** | none confirmed. **Q1 (inactive lender) may be raised to P1 by the PM:** if customers see products from a deactivated lender, that is a revenue and compliance exposure (E1: `lenderId other lender 201`; ANZ `isActive:false` on the created product). | pending PM decision |
| **P2 MEDIUM** | GUS-FX-0012 (silent criteria loss), GUS-FX-0013 (write quota) | no P0/P1 justification required |
| **P3 LOW** | GUS-FX-0001, 0002, 0003, 0004, 0010, 0011 | |

---

## STEP 4 - Open questions / spec gaps

No written spec was available; behaviour below was observed, not contradicted.

| # | Question | Evidence | Decision needed |
| --- | --- | --- | --- |
| Q1 | Should a product be creatable and active under a deactivated lender? The Add form lists ANZ (inactive) as selectable. The pre-existing product "Angelique Morse" is also active under ANZ. | E1, E3 (`"lender":{"name":"ANZ","isActive":false}`) | Block creation, or auto-deactivate products when the lender is deactivated? |
| Q2 | Must the comparison rate be >= the interest rate? Accepted today: interest 7.49%, comparison 7.00%. | E7 `test_comparison_rate_below_interest_rate` xfail | Yes/No |
| Q3 | Is a `$0.00 - $0.00` amount range valid? (E2: `amount max=0 201`). The seeded product has `$100,000 - $7,500,000` for a Pet Loan, so what is the intended range per product type? | E2, E3 | Minimum > 0? Per-type limits? |
| Q4 | Is a product with no loan term valid? Accepted: `termMonths: []` and the key omitted; the UI submits with no term selected. | E1, E2, E5, E7 | Require at least one term? |
| Q5 | Is minimum age `17` (under 18) allowed? | not tested (extended tier) | Lower bound for `minAgeYears` |
| Q6 | The Edit page has no eligibility-criteria section (labels: Lender, Type, Name, Description, rates, amounts, notes; plus term chips and an "Add fee" button). Is criteria meant to be immutable after creation? | E5 browser check of `/edit` | Confirm intended, or add the section |
| Q7 | "Delete permanently needs full access." What is full access, and what does a restricted role see? | UI dialog text | Role matrix; needs a second account to test |
| Q8 | Is 100 writes/hour intended for the admin API? | E4 | Confirm, or raise the limit for admin sessions / non-prod |
| Q9 | Is a `$0.00` fee valid? Accepted today. | E9 `test_zero_amount_fee_rejected` xfail | Yes/No |
| Q10 | The Add form allows only one fee (Add fee stays disabled after the first row is filled, E5) while the API accepts several (E9). Intended? | E5, E9 | Confirm the UI limit, or allow multiple |
| Q11 | Should Delete permanently require an extra step (typed name or second confirm)? | E10 | Design decision |
| Q12 | Role matrix: Support has `product_management: read`, Customer has `noaccess`, Administrator has `fullaccess`. What must a Support or Customer session get on POST/PUT/DELETE (403 expected)? | E11 | Confirm expectation, and approve creating a Support test account (see below) |

---

## STEP 5 - Recommended next run

| What | Command | Runtime | Rationale |
| --- | --- | --- | --- |
| UI suite | `npx playwright test tests/loan-products.spec.ts --project=chromium` | 3.5 min (E6) | Rerun every commit touching the product form or list. No server writes, so it can run on every PR |
| API core | `python -m pytest api/tests/test_loan_products_api.py -m "not extended" -rxXs` | 56 s (E7) | Rerun on every backend commit, **at most once per hour** (about 90 writes). Strict xfails turn into failures when GUS-FX-0001/2/3/4 are fixed |
| API extended | `python -m pytest api/tests/test_loan_products_api.py -m extended -rxXs` | not measured (44 tests, not yet run; write count not measured, so check `WRITE_BUDGET` before running) | Run once, in a different hour from core, to close the 44 untested cases |
| After PM answers Q1-Q4 | drop the `pm(...)` markers | n/a | They become normal pass/fail tests |
| Fees + races | `WRITE_BUDGET=38 python -m pytest api/tests/test_loan_products_fees_concurrency.py -m extended -rxXs` | 19 s (E9) | 17 writes measured (quota counter 43 -> 25 around the run, minus one check request); fits the same hour as nothing else, so keep it out of the core hour |
| Roles | not runnable yet | n/a | Needs a Support admin account (`product_management: read`); expected 200 on GET and 403 on POST/PUT/DELETE. Not tested: only one admin account exists (E11) |

---

## Regression run (same day, after the report) - what is fixed

Method: full UI suite, API core tier, Users API suites, plus targeted rechecks. A strict-xfail turning into an unexpected pass (XPASS) would have signalled a fix; none did.

| Finding | Status | Evidence |
| --- | --- | --- |
| GUS-FX-0001 JSON-string body -> 500 | **Not fixed** | API core run: still XFAIL, 0 XPASS |
| GUS-FX-0002 malformed JSON -> 500 | **Not fixed** | same |
| GUS-FX-0003 NUL byte in name -> 500 | **Not fixed** | same |
| GUS-FX-0004 invalid sort accepted | **Not fixed** | same |
| GUS-FX-0010 no client-side upper bounds | **Not fixed** | UI suite: LP-022, 023, 028, 030b still fail as expected |
| GUS-FX-0011 raw "Validation failed" | **Not fixed** | UI suite: LP-040 still fails as expected |
| GUS-FX-0012 invalid criteria silently dropped | **Not fixed** | UI suite: LP-032 (5 cases) still fail as expected |
| Q1-Q4 product questions | Unchanged | 5 API xfails unchanged; LP-029 unchanged |
| Users report: duplicated security headers | **Not fixed** | `x-content-type-options: nosniff, nosniff, nosniff` etc. on `GET /users` |
| Users report: doubled avatar link name | **Not fixed** | link name "Alert Kri Alert Kri" still present |
| Users report: inconsistent sign-in error wording | **Changed, see below** | |

### GUS-FX-0014 - NEW regression: sign-in UI reveals which emails have accounts (P2)
- **endpoint:** UI `/sign-in`, which calls `POST /api/proxy` target `/auth/register/check-email` after a failed login
- **expected:** the same message for an unknown email and a wrong password. The login API itself still does this: both return `401 {"message":"Incorrect email or password","code":"INVALID_CREDENTIALS"}`.
- **actual:** `admin@yopmail.com` + wrong password -> toast "Password is incorrect"; `nobody_zz@yopmail.com` -> toast "Email address is incorrect". The UI gets this from `check-email`, which answers without logging in:
  ```json
  {"success":true,"message":"Email availability","data":{"available":false,"message":"That email is already registered"}}
  {"success":true,"message":"Email availability","data":{"available":true,"message":"That email is available"}}
  ```
- **how-verified:** both UI toasts and both `check-email` responses captured; the endpoint was called without a session.
- **impact:** data leak. Anyone can test whether an email has an account on the admin or app (account enumeration, a step toward credential attacks and phishing). Revenue or safety impact for a P2: no, but it is a security finding to close before release.
- **surfaces affected:** UI and any client of `check-email`.
- **reproducer:** `curl -X POST https://gusdev.softwareco.com/api/proxy -H 'x-target-endpoint: /auth/register/check-email' -H 'content-type: application/json' -d '{"email":"admin@yopmail.com"}'`. Automated: `NEG-004` (expected-fail).
- **suggested fix direction:** the sign-in page error handler: show only the API's generic message and stop calling `check-email` after a failed login. Separately, consider rate limiting `check-email` per IP (it returned `ratelimit-remaining: 53` at a limit of 100).

---

## Product decisions Q1-Q4 and their status (checked 2026-10-05)

Decisions received from the product owner, each tested against gusdev with the created records deleted afterwards (read-back showed only the seeded product remaining).

| # | Decision | UI | API | Status |
| --- | --- | --- | --- | --- |
| Q1 | Only active lenders may be used | Lender dropdown lists only "Preventive Health Review"; ANZ is gone (LP-050 passed) | `POST /products` with ANZ (`isActive:false`) still returns **201** | **Not fully fixed**: GUS-FX-0005 (API) |
| Q2 | Comparison rate below interest rate: no validation for now | not blocked, payload `comparisonRateBps: 700` (LP-052 passed) | 201 (7.49% interest, 7.00% comparison) | **As decided** |
| Q3 | A $0.00-$0.00 amount range must be rejected | blocked: "Enter an amount range greater than $0.00" (LP-051 passed) | `min=0, max=0` still returns **201** | **Not fully fixed**: GUS-FX-0007 (API) |
| Q4 | A product with no term is allowed | submits without terms (LP-029 now asserts this) | 201 for both `termMonths: []` and the field omitted | **As decided** |

### GUS-FX-0005 - API accepts a product under a deactivated lender (P2)
- **request:** `POST /api/proxy`, target `/products`, body with `"lenderId":"6ab217c4983eb386149dce32"` (ANZ, `isActive:false`) and otherwise valid data.
- **expected:** 4xx rejection (only active lenders).
- **actual:** `201 {"success":true,"message":"Product created",...}`.
- **how-verified:** control with the active lender returned 201 as expected; the inactive one also 201; record read back and deleted. Automated: `test_inactive_lender_rejected` (strict xfail).
- **impact:** data integrity. Anything other than the Add form (scripts, other clients) can still create active products under a deactivated lender. Not verified: whether `PUT /products/:id` can move an existing product to an inactive lender.
- **suggested fix direction:** the product create (and update) service: check the lender's `isActive` where it already checks the lender exists (it returns 404 `LENDER_NOT_FOUND` for unknown ids).

### GUS-FX-0007 - API accepts a $0.00-$0.00 amount range (P3)
- **request:** valid body with `"minAmountCents":0,"maxAmountCents":0`.
- **expected:** 422 on the amount fields.
- **actual:** `201 Product created`.
- **how-verified:** record read back and deleted. Automated: `test_zero_amount_range_rejected` (strict xfail).
- **impact:** data integrity; the UI already blocks it.
- **suggested fix direction:** the amount schema: require `maxAmountCents > 0` alongside the existing `max >= min` rule.


---

## Recheck 2026-10-06 (stage = gusdev)

| Item | Result |
| --- | --- |
| Q1 inactive lender: create | **Not fixed.** `POST /products` with ANZ (`isActive:false`) -> 201 |
| Q1 inactive lender: edit | **Not fixed, newly checked.** `PUT /products/:id {"lenderId": ANZ}` -> 200 "Product updated". An existing active product can be moved to a deactivated lender. Same fix point as GUS-FX-0005 |
| Q2 comparison below interest | As decided: 201 |
| Q3 zero amount range | **Not fixed in the API.** `min=0, max=0` -> 201 (UI blocks it) |
| Q4 no term | As decided: 201 for `[]` and for the field omitted |
| GUS-FX-0014 sign-in enumeration, UI | **Fixed.** Both cases toast "Email or password is incorrect"; the page no longer calls `check-email` after a failed login |
| GUS-FX-0014 `check-email` endpoint | **Not fixed.** Unauthenticated `POST /auth/register/check-email` still returns `available:false / "That email is already registered"` vs `available:true`. Downgraded to P3 because the UI no longer exposes it; still an account-lookup oracle for direct callers |
| All other findings (0001-0004, 0007, 0010-0012, duplicated headers) | Unchanged, still failing as known |

The UI suite had 104 pass and 1 "unexpected pass" (NEG-004, the fixed UI part); after removing its expected-fail marker it is a normal passing test. All created records were deleted; only "Angelique Morse" remains.


---

## Lender seed data and new findings (2026-10-06)

12 lenders were added to gusdev (14 in total). Each has a name, legal name, checksum-valid ABN, website, contact name, `@yopmail.com` email, fictional ACMA-reserved `+61 x 5550 xxxx` phone and a logo (generated monogram image, since real bank logos are trademarked). Read-back: all `isActive: true`, all logo URLs return HTTP 200. ABNs were recalled from memory and checked with the ABN checksum; verify them on ABN Lookup before treating them as authoritative.

### GUS-FX-0015 - Logo upload from the admin UI is blocked by the storage bucket's CORS policy (P1)
- **endpoint:** browser `PUT` to the presigned URL on `gus-dev-bucket.s3.ap-southeast-2.amazonaws.com` (from `POST /uploads/presign`, which returns 200), then `POST /lenders`
- **expected:** the logo uploads, then the lender is created.
- **actual (console):** `Access to fetch at 'https://gus-dev-bucket.s3.ap-southeast-2.amazonaws.com/public/profiles/.../commonwealth-bank.png?...' from origin 'https://gusdev.softwareco.com' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present`. The UI toast reads "Failed to fetch", then `POST /lenders` returns `422 {"field":"logo","message":"A logo is required"}`.
- **how-verified:** the same presigned URL accepted a server-side `PUT` (S3 200), so the URL and signing are fine and only browser access is blocked.
- **impact:** revenue/safety: no admin can create a lender through the UI, and every logo or profile image upload on this origin is likely affected (the presign target is `profiles`). Lenders are the parent of all products, so onboarding a new lender is blocked until fixed. (This is also why 12 lenders were seeded through the API.)
- **surfaces affected:** UI (any browser upload to this bucket from `https://gusdev.softwareco.com`).
- **reproducer:** open `/lenders?create=1`, choose any PNG as logo, fill the required fields, click Create lender.
- **suggested fix direction:** the S3 bucket CORS configuration: allow `PUT`/`OPTIONS` from the admin origin(s) with the headers the presigned upload sends.

### GUS-FX-0016 - ABN checksum is not validated (P3)
- **request:** `POST /lenders` with `"abn":"48 123 123 125"` (checksum fails) and otherwise valid data.
- **expected:** 422 on `abn`.
- **actual:** `201 Lender created`. The UI form also submits it with no error. Only length is checked (`An ABN is 11 digits`); duplicate ABN returns `409 DUPLICATE`, duplicate name `409 LENDER_NAME_EXISTS`.
- **impact:** data integrity (invalid ABNs stored on lender records).
- **suggested fix direction:** the lender schema and the lender form: add the standard ABN checksum rule (weights 10,1,3,5,...,19; subtract 1 from the first digit; sum mod 89 = 0).

### Observations
- **ANZ was reactivated during this session** (it read `isActive:false` at the start of 2026-10-06, `true` later; not changed by the tests). GUS-FX-0005 (product under an inactive lender) can no longer be reproduced with ANZ: `test_inactive_lender_rejected` now skips until a lender is deactivated.
- The "Add loan product" lender dropdown therefore lists all active lenders; LP-050 now compares it with `GET /lenders` instead of a fixed name.
- Existing records still have untidy data (not touched): ANZ website `anz.com.au/%20sss`; "Preventive Health Review" has contact name "Exercise Therapy Note" and phone `+6161459966825`.

---

## GUS-FX-0017 - Lender product count includes deactivated products (P2)
- **endpoint:** `GET /api/proxy` target `/lenders` (field `productCount`); shown on UI `/lenders` (Products column) and `/lenders/:id` ("Loan products (N)")
- **request:** `GET /lenders?limit=100` after NAB was given 6 products and 2 were deactivated with `PUT /products/:id {"isActive":false}` (each returned 200 "Product updated").
- **expected:** the lender's count reflects live products (4), or shows "4 active of 6".
- **actual:** `productCount: 6`; the lenders list shows `products=6`; NAB's page shows "Loan products (6)" and lists both deactivated products with no "Inactive" text.
- **how-verified:** count delta (2 -> 6 after creating 4; still 6 after deactivating 2); cross-checked with `GET /products?lenderId=...`: 6 total, 4 with `isActive=true`, 2 with `isActive=false`. The Loan products list and the dashboard (19 total, 16 active, 3 inactive) are correct, so only the lender-side count is wrong.
- **impact:** revenue: an admin reads a lender as having more live products than it offers. UX: no way to see on the lender page which products are off.
- **surfaces affected:** UI (lenders list and lender detail), API consumers of `productCount`.
- **reproducer:** pick a lender with several products, deactivate two, open `/lenders`. Automated: `TestLenderProductCount::test_product_count_excludes_deactivated_products` (strict xfail, 7 writes, `-m extended`).
- **suggested fix direction:** the lender list aggregation behind `productCount`: filter `isActive: true` (or return both `productCount` and `activeProductCount`), and mark inactive products on the lender detail list.
- **related, unconfirmed:** "Vet Bills Instalment Loan" became inactive at 07:28 UTC without any of my scenarios touching it; who deactivated it is unknown.


---

## 65-product data display check (2026-10-06)

50 realistic products were added across 13 lenders and all 6 types (65 in total: 14 pet, 11 home, 10 car, 10 investment, 10 business, 10 personal). All were created with valid data (comparison >= interest, min <= max, no duplicates by lender, type and name, fees on about 65%).

| Check | Result |
| --- | --- |
| Pagination integrity (API, page sizes 10/20/25/50 x 4 sort orders) | OK: every combination returned all 65, 0 duplicates, 0 missing |
| Loan products list | OK: "Showing 1-20 of 65", Page 1/4, controls enable/disable correctly, last page 61-65, rows-per-page 10/20/30/40/50 (50 -> 2 pages, 51-65 on page 2) |
| Filters at scale | OK: type, lender, status, search and combinations return counts that match the API; changing a filter on page 3 returns to page 1 |
| Lender product counts | OK vs reality: sum of lender counts = 65; every lender's count equals its real product count (note GUS-FX-0017 for deactivated products) |
| Lender detail page | OK: lists all of the lender's products (up to 6, the most any lender has) with a "View all" link; not tested beyond 6 |
| Dashboard | OK: 65 total, 64 active (98%), 1 inactive (2%) |
| Sorting | **Not implemented:** see GUS-FX-0004 (upgraded to P2). The API ignores sortBy/sortOrder and the table has no sortable headers |


---

## Integration run: real UI creation across screens (2026-10-06)

Seven products were created through the actual Add product form (writes not intercepted) with edge-case data, then followed across the detail page, list, lender list, lender page, dashboard, Edit form and API. All were deleted afterwards (65 products remain, none of the test data).

| Scenario | Result |
| --- | --- |
| Full data (decimals, 4 criteria, fee, notes) | Saved exactly: rates 749/812 bps, $2,500.50 - $45,000.99, fee $199.95 one-off, criteria as entered |
| Special-character name `Smith & Sons' "Premium" <Gold> Loan`, markup in description | Shown as text everywhere; no element injected; Edit prefill exact |
| Emoji and accents (`Prêt Éclair Maison 🏠 Loan`) | Shown and prefilled correctly |
| 119-120 character name | Full text shown on detail; no horizontal overflow at 1440 or 375 px |
| 0.00% / 100.00% rates, $0.01 to $999,999,999.99 | Accepted and formatted correctly (see GUS-Q-08) |
| 5,000-character description and notes | Accepted; 5,000 characters rendered; no overflow |
| Duplicate name for the same lender | 409; the UI shows "That lender already has a product with this name" inline and keeps the form |
| Edit via UI (rate, description) | `PUT` 200, toast "Product updated", detail shows 7.99% |
| Deactivate, Activate, Delete via UI | Dashboard and lender counts changed correctly at every step; the deleted URL shows "Product not found"; no phone-width overflow on list, dashboard, lenders or lender page |

New findings: GUS-FX-0020 (term chips are single-select and editing collapses terms, P2), GUS-FX-0021 (criteria saved but never shown, P3), GUS-FX-0022 (intermittent 5xx, unconfirmed), GUS-Q-08 (extreme values). GUS-FX-0017 is now **fixed in the UI** (lender list and page show "7 active of 8" and mark inactive products); the API `productCount` is still the total.


---

## Terms and months review (2026-10-06)

| Area | Result |
| --- | --- |
| Preset chips | 12, 24, 36, 48, 60 mo; none selected by default; clicking a selected chip deselects it; **single-select** (see GUS-FX-0020) |
| Custom months input, accepted | 1, 7, 018 (stored as 18), 600; typing 12 or 60 selects the preset (no duplicate chip) |
| Custom months input, rejected | 0, -5, abc, 12.5, 1e2, +24, empty and Arabic digits: "Enter a valid whole number of months"; 601, 5000, 99999999999: "Enter a term of 600 months or less" (the 601 case was fixed on 2026-10-06) |
| Display | "N mo", comma-separated, ascending, on list and detail (e.g. `12 mo, 24 mo, 36 mo, 48 mo, 60 mo, 84 mo, 120 mo`); no phone-width overflow; terms are shown in months only (360 mo, not 30 years) |
| Edit page | Non-preset terms (240, 300, 360) show as selected chips; a description-only edit sends only `description` |
| API `PUT termMonths` | Replaces (not merges); de-duplicates and sorts `[60,12,36,12]` -> `[12,36,60]`; accepts 1 and 600; accepts `[]`; rejects 0, 601, -12, 13.5, "12", null element, non-array and null with a clear 422 and leaves the stored terms unchanged; maximum **24 terms** (25 rejected: "more term options than a screen can render") |
| Data | 34 different term sets across the 65 products |

## Phone numbers: India and other countries (2026-10-06)

See GUS-FX-0023 and GUS-FX-0024. Front end: with India selected the lender form sends `+91123456789`, `+911234567890`, `+9198765432101` and `+915876543210` without error (valid: 10 digits starting 6-9); Australia (`+61123456789`, `+611234567890`, `+6141234567`), US (`+1123456`) and UK (`+4412345`) behave the same, so no country has rules. Back end: `POST /lenders` returned 201 for all five invalid Indian numbers above and stored them; it rejected only `9876543210` (no `+`) and `+6112345` (too short) with `Enter the number in international format`. Stored data: 3 of 15 customers and 1 lender already have invalid numbers (GUS-D-03). The customer sign-up flow was not tested (no admin screen creates customers), but the stored customer data shows it accepts the same invalid numbers.

## Fixes confirmed on dev today

GUS-FX-0010 (rate over 100%, name over 120, term over 600 now blocked in the form), GUS-FX-0011 (no raw "Validation failed" on a malformed id), GUS-FX-0017 (lender counts show "N active of M"), and the sign-in leak in the UI (GUS-FX-0014, UI part).


---

## Eligibility criteria and matching (2026-10-06)

Matching could not be tested: no eligibility, matching, offers or applications route exists on the admin API (about 50 probed, all 404) and customers have no income, debt or surplus data (GUS-Q-09). What was checked instead is the data matching depends on, across all 65 products (`api/tests/test_eligibility_data.py`, read-only):

| Check | Result |
| --- | --- |
| Product has criteria | 64 of 65. `Angelique Morse` (pre-existing) has none, so it matches every customer (GUS-FX-0025) |
| All five criteria present | 64 of 64 |
| Minimum surplus covers the repayment on the product's smallest loan | 7 of the products seeded on 2026-10-06 failed (surplus below the repayment, e.g. Flexi First Home Loan $800 vs $918). Cause: my seed generator. Corrected with `PUT criteria` (other keys kept); now 0 failures |
| Smallest loan within debt-to-income at the minimum income | 0 failures |
| Reference calculator (age, income, DTI, surplus, amount, term, bank connection, inactive product/lender) | 17 boundary cases pass; plan in `ELIGIBILITY_TEST_PLAN.md` |

Risk to flag: the admin UI silently drops invalid criteria (GUS-FX-0012) and cannot show or edit them (GUS-FX-0021, GUS-Q-05), so products created in the UI can end up with fewer or no criteria and match too many customers.

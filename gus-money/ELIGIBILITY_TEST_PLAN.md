# Eligibility matching - test plan (2026-10-06)

**Status: matching could not be tested.** No eligibility, matching, offers or applications endpoint exists on the admin API (about 50 routes probed, all 404; `/products/eligible` and similar are the product-ID route rejecting the word as an ID), the admin user page shows no financial profile, and customer records hold no income, debts or surplus. The criteria are stored on each product but nothing reachable evaluates them. This plan is ready to run once the location of the matching logic is known (customer app, another service, or a feature not built yet).

## Criteria stored on every product
`minAgeYears`, `maxAgeYears`, `minIncomeCentsPerYear`, `maxDebtToIncomeRatio`, `minMonthlySurplusCents`, `requiresBankConnection` (always true today, no UI to change it).

## Assumed rules (need product-owner confirmation)
| # | Rule |
|---|---|
| 1 | Age is inclusive: min <= age <= max |
| 2 | Annual income >= minimum income |
| 3 | Debt-to-income: (existing debts + requested amount) / annual income <= max ratio (definition to confirm) |
| 4 | Monthly surplus >= the product minimum **and** >= the repayment on the requested loan |
| 5 | Requested amount between the product minimum and maximum; the term must be one the product offers (any term if none are set) |
| 6 | Product and lender both active |
| 7 | Bank connection required when `requiresBankConnection` is true |
| 8 | Customer meeting every rule must not be shown a product they fail; customer failing any rule must not see it |

## Boundary matrix (reference product: age 21-60, income $52,000, DTI 5.5, surplus $450.75, $5,000 - $50,000, 36 mo)
| Rule | Not eligible | Eligible |
|---|---|---|
| Age | 20, 61 | 21, 60 |
| Income | $51,999 | $52,000 |
| Surplus | $450.74 | $700 (for a $20,000 loan) |
| DTI | debts that push (debts + amount) / income above 5.5 | at 5.25 |
| Amount | $4,999.99, $50,000.01 | $5,000, $50,000 |
| Bank connection | not connected | connected |
| Product / lender | inactive product, inactive lender | active both |

Also: two products for the same customer (only the passing one is offered), a customer exactly at every minimum, a customer failing only one rule (each rule alone), age computed from date of birth on the boundary birthday, income stored as cents vs dollars, and a product with no criteria (matches everyone, see GUS-FX-0025).

## What is checked today (read-only, runs every regression): `api/tests/test_eligibility_data.py`
- Every product has criteria (fails for `Angelique Morse`, GUS-FX-0025)
- Every product has all five criteria (no half-filled products)
- Age band sane (18 <= min <= max <= 120)
- Minimum surplus is not below the repayment on the product's own smallest loan
- Smallest loan does not breach the debt-to-income limit at the minimum income
- Reference calculator `is_eligible()` boundary cases (17 cases)

## Results of the audit on 65 products
- 1 product with no criteria (`Angelique Morse`, pre-existing).
- 64 products with all five criteria.
- 7 of the products seeded on 2026-10-06 had a surplus rule below the repayment on their own smallest loan (my generated data); corrected the same day with `PUT criteria`, the audit is clean.
- The admin UI cannot show or edit criteria (GUS-FX-0021, GUS-Q-05) and silently drops invalid ones (GUS-FX-0012), so a product created in the UI can end up with fewer or no criteria and match too many customers.

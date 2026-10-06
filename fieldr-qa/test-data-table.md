# Test data table (AU library)

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
| csv/abn.csv | 116 |
| csv/account_number.csv | 114 |
| csv/amount_aud.csv | 107 |
| csv/bsb.csv | 118 |
| csv/date_of_birth.csv | 115 |
| csv/email_address.csv | 105 |
| csv/first_name.csv | 104 |
| csv/last_name.csv | 104 |
| csv/mobile_number.csv | 109 |
| csv/otp_code.csv | 108 |
| csv/postcode.csv | 134 |
| csv/state.csv | 100 |
| csv/street_address.csv | 113 |
| csv/tfn.csv | 112 |

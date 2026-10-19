| Field | Scenario | Typed | Field holds | Counted as filled | Message shown |
|---|---|---|---|---|---|
| Customer Name | valid | `Olivia Nguyen` | `Olivia Nguyen` | True | — |
| Customer Name | 1 char | `A` | `A` | True | — |
| Customer Name | spaces only | `   ` | `   ` | False | — |
| Customer Name | digits only | `12345` | `12345` | True | — |
| Customer Name | apostrophe/hyphen | `Siobhan O'Brien-Smith` | `Siobhan O'Brien-Smith` | True | — |
| Customer Name | accented | `Nguyễn Văn An` | `Nguyễn Văn An` | True | — |
| Customer Name | emoji | `Olivia 🙂` | `Olivia 🙂` | True | — |
| Customer Name | HTML | `<b>Olivia</b>` | `<b>Olivia</b>` | True | — |
| Customer Name | 100 chars | `NguyenNguyen...(100 chars)` | `NguyenNguyen...(100 chars)` | True | — |
| Customer Name | 258 chars | `NguyenNguyen...(258 chars)` | `NguyenNguyen...(258 chars)` | True | — |
| Customer Email | valid | `olivia.nguyen@yopmail.com` | `olivia.nguyen@yopmail.com` | True | — |
| Customer Email | uppercase | `Olivia.NGUYEN@YOPMAIL.COM` | `Olivia.NGUYEN@YOPMAIL.COM` | True | — |
| Customer Email | no @ | `olivia.yopmail.com` | `olivia.yopmail.com` | True | Enter a valid email |
| Customer Email | no local part | `@yopmail.com` | `@yopmail.com` | True | Enter a valid email |
| Customer Email | no domain | `olivia@` | `olivia@` | True | Enter a valid email |
| Customer Email | no TLD | `olivia@yopmail` | `olivia@yopmail` | True | — |
| Customer Email | double dot | `olivia..nguyen@yopmail.com` | `olivia..nguyen@yopmail.com` | True | — |
| Customer Email | space inside | `olivia nguyen@yopmail.com` | `olivia nguyen@yopmail.com` | True | Enter a valid email |
| Customer Email | surrounding spaces | `  olivia@yopmail.com  ` | `olivia@yopmail.com` | True | — |
| Customer Email | plus alias | `olivia+jobs@yopmail.com` | `olivia+jobs@yopmail.com` | True | — |
| Customer Email | 65-char local part | `aaaaaaaaaaaa...(77 chars)` | `aaaaaaaaaaaa...(77 chars)` | True | — |
| Customer Phone | valid mobile 9 digits | `412345678` | `+61 (41) 2345 678` | True | — |
| Customer Phone | 8 digits | `41234567` | `+61 (41) 2345 67` | True | Phone number must be 9 digits for Australia |
| Customer Phone | 10 digits | `4123456789` | `+61 (41) 2345 6789` | True | Phone number must be 9 digits for Australia |
| Customer Phone | leading 0 | `0412345678` | `+61 (04) 1234 5678` | True | — |
| Customer Phone | +61 prefix | `+61412345678` | `+61 (61) 4123 4567` | True | Phone number must be 9 digits for Australia |
| Customer Phone | landline 9 digits | `298765432` | `+61 (29) 8765 432` | True | — |
| Customer Phone | letters | `abcdefghi` | `+61` | False | — |
| Customer Phone | spaces | `412 345 678` | `+61 (41) 2345 678` | True | — |
| Customer Phone | dashes | `412-345-678` | `+61 (41) 2345 678` | True | — |
| Customer Phone | all zeros | `000000000` | `+61 (00) 0000 000` | True | — |
| ABN/ACN | valid ABN | `33102417032` | `33102417032` | True | — |
| ABN/ACN | bad-checksum ABN | `12345678901` | `12345678901` | True | — |
| ABN/ACN | 9-digit ACN | `004085616` | `004085616` | True | ABN/ACN must be exactly 11 digits |
| ABN/ACN | 10 digits | `3310241703` | `3310241703` | True | ABN/ACN must be exactly 11 digits |
| ABN/ACN | 12 digits | `331024170321` | `33102417032` | True | — |
| ABN/ACN | with spaces | `33 102 417 032` | `33102417` | True | ABN/ACN must be exactly 11 digits |
| ABN/ACN | letters | `ABCDEFGHIJK` | `` | True | — |
| ABN/ACN | all zeros | `00000000000` | `00000000000` | True | — |
| ABN/ACN | negative | `-3310241703` | `3310241703` | True | ABN/ACN must be exactly 11 digits |
| Postcode | valid NSW | `2000` | `2000` | True | — |
| Postcode | valid NSW regional | `2650` | `2650` | True | — |
| Postcode | VIC postcode | `3000` | `3000` | True | — |
| Postcode | QLD postcode | `4000` | `4000` | True | — |
| Postcode | 3 digits | `200` | `200` | True | Postcode must be exactly 4 digits |
| Postcode | 5 digits | `20000` | `2000` | True | — |
| Postcode | letters | `abcd` | `` | False | — |
| Postcode | all zeros | `0000` | `0000` | True | — |
| Postcode | with space | `2 000` | `200` | True | Postcode must be exactly 4 digits |
| Postcode | negative | `-200` | `200` | True | Postcode must be exactly 4 digits |
| Own Reference | typical | `REF-2026-0142` | `REF-2026-0142` | True | — |
| Own Reference | spaces only | `   ` | `   ` | True | — |
| Own Reference | HTML | `<i>REF</i>` | `<i>REF</i>` | True | — |
| Own Reference | 258 chars | `NguyenNguyen...(258 chars)` | `NguyenNguyen...(258 chars)` | True | — |
| Installation Date | valid future | `15-12-2026` | `15-12-2026` | True | — |
| Installation Date | today | `24-09-2026` | `24-09-2026` | True | — |
| Installation Date | past | `01-01-2020` | `01-01-2020` | True | — |
| Installation Date | 31 Dec | `31-12-2026` | `31-12-2026` | True | — |
| Installation Date | 29 Feb non-leap | `29-02-2027` | `29-02-2027` | True | — |
| Installation Date | 31 Apr | `31-04-2027` | `31-04-2027` | True | — |
| Installation Date | day 00 | `00-01-2027` | `00-01-2027` | True | — |
| Installation Date | month 13 | `15-13-2026` | `15-13-2026` | True | — |
| Installation Date | single digits | `1-1-2027` | `1-1-2027` | True | — |
| Installation Date | slashes | `15/12/2026` | `15/12/2026` | True | — |
| Installation Date | letters | `ab-cd-efgh` | `ab-cd-efgh` | True | — |
| Installation Date | year 1900 | `15-12-1900` | `15-12-1900` | True | — |

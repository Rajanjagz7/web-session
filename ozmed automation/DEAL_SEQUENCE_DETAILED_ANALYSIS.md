# Deal Sequence: Detailed Analysis of All Cases

A complete, plain-language explanation of how the deal Sequence works in import and
export, with worked examples for every situation: new deals, old deals, duplicates,
blanks, human mistakes, edge cases, worst cases, empty data, and partial imports.

This document is written so a non-technical reader can follow it. Technical notes are
included where useful but each case has a plain example.

---

## 1. What "Sequence" means (start here)

- Every deal shown in the app/website has a **display order**. The **Sequence** is simply
  that order: the deal with Sequence 1 shows first, Sequence 2 next, and so on.
- The export file (Excel) now has a **Sequence** column so you can see and change the order.
- You edit the Sequence values, re-import the file, and the order updates.

### The golden rules (these are always true)
1. **The active list is always clean: 1, 2, 3, ... N** with no duplicates and no gaps.
   No matter what you type, the system fixes it into a clean list.
2. **No deal is ever deleted or dropped because of a Sequence problem.** A bad or missing
   Sequence never removes a deal.
3. **A deal never ends up with two numbers, and two deals never share the same number.**
4. Only **"active-ish" deals have a number.** Deals that are finished (expired) or paused
   (suspended) have **no** number (blank in the export).

### Two words used a lot below
- **Orderable deal** = a deal that is live or will be live: not deleted, not suspended, and
  its end date is today or later (Active or Upcoming). **These are the only deals that get a
  number.**
- **Non-orderable deal** = Expired (end date passed), Suspended (manually paused), or
  Deleted. **These have no number.**

---

## 2. How the system decides the order (the logic, simply)

When you import a file, for every orderable deal the system looks at:
- **Typed value**: the Sequence you put in the file for that deal (may be empty).
- **Current value**: the number the deal already has in the system.

It then orders deals using this priority:
1. **Typed value first** - if you typed a number, that is where the deal wants to go.
2. If you did **not** type a number, the deal **keeps its current place**.
3. A brand-new deal with no typed number goes to the **end**.

After lining everyone up this way, the system **renumbers them 1, 2, 3, ... N**. That final
renumber is what guarantees no duplicates and no gaps.

### The tie-breaker (important for duplicates)
When two deals want the **same** position, the system breaks the tie in this order:
1. A deal that **typed** that number beats a deal that merely **already had** it.
2. If both typed the same number, the one currently **higher up** (smaller current number)
   goes first.
3. Then the **older** deal, then an internal ID (so the result is always the same, never
   random).

Plain version: "If you both ask for seat 2, the person who wrote '2' on their ticket gets it;
the other moves to seat 3, and everyone behind shifts down by one."

### One key distinction: full file vs partial file
- **Full file** (you export everything, edit, and re-import all of it): your typed numbers
  are honored **exactly**. If you number them 1..N, that is exactly what you get.
- **Partial file** (only some deals in the file): the typed numbers are **relative**. The
  deals in the file are placed in the order you asked, but because the whole list is always
  compacted to 1..N, a specific number may shift. (Examples in Section 12.)

Throughout the examples the system starts with these 5 active deals:

| Current # | Deal |
|---|---|
| 1 | Milk |
| 2 | Bread |
| 3 | Eggs |
| 4 | Juice |
| 5 | Soda |

---

## 3. New deal cases

### 3.1 New deal with a Sequence
- **You do:** add a new "Water" row with Sequence 2.
- **Result:** Water takes 2, everything from 2 down shifts one step.
- **After:** Milk 1, **Water 2**, Bread 3, Eggs 4, Juice 5, Soda 6.
- **Why:** Water typed "2", so it wins position 2; the old occupants move down; renumbered 1..6.

### 3.2 New deal with no Sequence (blank)
- **You do:** add "Water" with the Sequence cell empty.
- **After:** Milk 1 ... Soda 5, **Water 6**.
- **Why:** no typed number, and it is new, so it goes to the end.

### 3.3 New deal with a past end date (already expired)
- **You do:** add "Old Promo" with dates in 2020 and any Sequence.
- **After:** Old Promo is **created** but has **no number** (it is expired). The active list
  stays 1..5.
- **Why:** only orderable deals get numbers; an already-finished deal does not.

### 3.4 Several new deals at once (into the 5)
- **You do:** add Water=1, Cola=1, Tea=blank.
- **After:** Water 1, Cola 2, Milk 3, Bread 4, Eggs 5, Juice 6, Soda 7, **Tea 8**.
- **Why:** Water and Cola both typed 1 so they take the front (Water then Cola by tie-break);
  the old deals shift down; Tea (blank, new) goes last.

---

## 4. Existing (old) deal cases

### 4.1 Move an existing deal up
- **You do:** set Juice from 4 to 1.
- **After:** **Juice 1**, Milk 2, Bread 3, Eggs 4, Soda 5.
- **Why:** Juice typed 1, so it jumps to the front; the deals it passed shift down one.

### 4.2 Move an existing deal down
- **You do:** set Milk from 1 to 5.
- **After:** Bread 1, Eggs 2, Juice 3, Soda 4, **Milk 5**.
- **Why:** Milk goes to the last slot; the others move up to fill the gap.

### 4.3 Change one deal, leave the rest blank
- **You do:** set Eggs to 1, leave others blank.
- **After:** **Eggs 1**, Milk 2, Bread 3, Juice 4, Soda 5.
- **Why:** blank deals keep their order; only Eggs moves.

### 4.4 Set a deal to the number it already has (no real change)
- **You do:** set Bread to 2 (it is already 2).
- **After:** unchanged (1..5).
- **Why:** nothing actually moved.

### 4.5 Full reorder (reverse the list)
- **You do:** Milk 5, Bread 4, Eggs 3, Juice 2, Soda 1.
- **After:** Soda 1, Juice 2, Eggs 3, Bread 4, Milk 5.
- **Why:** a full file with exact numbers is honored exactly.

---

## 5. Duplicate sequence cases (the same number used more than once)

The system never keeps duplicates. It uses the tie-breaker (Section 2) then renumbers.

### 5.1 New deal takes a number an existing deal has
- **You do:** add Water with Sequence 2 (Bread has 2).
- **After:** Milk 1, **Water 2, Bread 3**, Eggs 4, Juice 5, Soda 6.
- **Why:** Water typed 2 and wins; Bread (only "had" 2) moves to 3.

### 5.2 Existing deal takes another existing deal's number
- **You do:** set Juice to 2 (Bread has 2).
- **After:** Milk 1, **Juice 2, Bread 3, Eggs 4**, Soda 5.
- **Why:** Juice typed 2 and wins; Bread and Eggs shift down by one.

### 5.3 Two deals typed the same number
- **You do:** Eggs 1 and Soda 1.
- **After:** **Eggs 1, Soda 2**, Milk 3, Bread 4, Juice 5.
- **Why:** both asked for 1; Eggs (smaller current number, 3 vs 5) goes first, Soda next.

### 5.4 Everyone set to the same number (e.g. all = 1)
- **You do:** set all five deals to Sequence 1.
- **After:** Milk 1, Bread 2, Eggs 3, Juice 4, Soda 5 (unchanged here).
- **Why:** all tie at 1; the tie-break falls back to their current order, so the list keeps
  its current order and is just compacted. (If the currents were jumbled, this would sort
  them by current and compact to 1..N.)

### 5.5 Many duplicates mixed together
- **You do:** Milk 1, Bread 1, Eggs 2, Juice 2, Soda 2.
- **After:** Milk 1, Bread 2, Eggs 3, Juice 4, Soda 5.
- **Why:** at "1": Milk, Bread (by current). At "2": Eggs, Juice, Soda (by current). Then
  renumber 1..5. All kept, all unique.

---

## 6. Blank / missing / invalid Sequence value cases

`Blank` and `invalid` are treated the same: "no position given."

### 6.1 Blank for an existing deal
- Existing deal with an empty Sequence **keeps its current place**. Not dropped.

### 6.2 Blank for a new deal
- New deal with an empty Sequence goes to the **end**.

### 6.3 Text, symbols, or words
- "abc", "two", "N/A" have no digits, so they are treated as **blank**.
- "1st" becomes 1, "#2" becomes 2, "007" becomes 7 (the system reads the digits).

### 6.4 Zero or negative
- "0", "-3" are **not valid positions**, so they are treated as **blank**.

### 6.5 Decimal
- "2.9" becomes 2, "3.5" becomes 3 (rounded down to a whole number).

### 6.6 Thousands separators / spaces
- "1,000" becomes 1000, " 7 " becomes 7 (spaces and commas are ignored).

In every one of these, the deal is **kept**; the only question is whether a usable number
was found. If not, it behaves like a blank (keep place if existing, go to end if new).

---

## 7. Missing Sequence column (old template)

- **You do:** import a file that has **no Sequence column at all** (an older export).
- **After:** import works normally, **no deal is lost**, and the **existing order is kept**.
- **Why:** with no typed numbers anywhere, every deal keeps its current place; the list is
  just re-compacted to a clean 1..N.

This makes the feature **backward compatible**: old files still work.

---

## 8. Multi-row deal cases (one deal, several rows)

Some deals appear as **several rows** in the file (one row per product, for Combo /
Low-price / Any deals). The system treats all those rows as **one deal** (matched by the
deal's promo code identity), so its rows can never become duplicates or split apart.

**Which number is used:** the **first non-empty** Sequence among that deal's rows.

### 8.1 All rows have the same number
- Rows: 3, 3, 3 -> the deal is placed at 3. Simple.

### 8.2 Rows have different numbers (a mistake)
- Rows: 2, 7, 7 -> the **first non-empty (2)** is used; the 7s are ignored and a note is
  logged. The deal is placed at 2, still as **one** deal. No duplicate is created.

### 8.3 Some rows blank, some filled
- Rows: blank, 4, blank -> the first **non-empty (4)** is used. Deal placed at 4.

### 8.4 All rows blank
- The deal has no typed number: existing keeps its place, new goes to the end.

### 8.5 Rows are scattered / out of order in the file
- Even if a deal's rows are not next to each other, they are still grouped into **one** deal
  by its promo code. The Sequence still comes from that deal's first non-empty row.

---

## 9. Gaps and out-of-range numbers

### 9.1 Gaps in typed numbers
- **You do:** Milk 1, Bread 2, Eggs 50, Juice 51, Soda 52.
- **After:** Milk 1, Bread 2, Eggs 3, Juice 4, Soda 5.
- **Why:** the system keeps the order you asked (1 < 2 < 50 < 51 < 52) and compacts to 1..5.

### 9.2 A number bigger than the list
- **You do:** set Eggs to 999 (only 5 deals).
- **After:** Milk 1, Bread 2, Juice 3, Soda 4, **Eggs 5**.
- **Why:** 999 is beyond the end, so Eggs lands last.

### 9.3 Existing data already has a gap (e.g. 30 deals but numbers go up to 31)
- **You do:** any import (even one blank deal), or the one-time cleanup.
- **After:** the whole active list is recompacted to **1..30** with no gap.
- **Why:** every import recomputes the full active list into a clean 1..N, healing old gaps.

---

## 10. Status cases: Active, Upcoming, Expired, Suspended, Deleted

### 10.1 Active and Upcoming
- Both are **orderable**: they get numbers and take part in the 1..N ordering.
- (Note: the website list may label an Upcoming deal as "Inactive," but it still holds a
  number. That labeling is unchanged by this feature.)

### 10.2 Expired (end date has passed)
- **No number.** Blank in the export, sorted after the active deals.
- If you **change its End Date to the future** in the file, it becomes active again and
  receives a number.
- (On a system not yet cleaned up, an expired deal may still show its old number in the
  export until the first import or cleanup runs; after that it is blank.)

### 10.3 Suspended (manually paused)
- **No number** while suspended.
- If a suspended deal appears in an import file, it is **reactivated** (unpaused) and then
  given a number like any active deal.
- Pausing/unpausing itself is done by the status action; import brings a suspended deal back
  when it is present in the file.

### 10.4 Deleted
- Deleted deals are **never** in the export and are **not matched** on import. They are fully
  out of the picture and keep no number.

### 10.5 A suspended deal that is also expired
- If reactivated by import but its dates are still in the past, it becomes "not paused" but
  is still expired, so it holds **no number** (consistent with expired = no number).

---

## 11. Partial import (only a few deals in the file)

### 11.1 Import one deal into a big list
- **System:** 100 deals. **You do:** import just Deal #50 with Sequence 1.
- **After:** Deal #50 becomes 1; the deals that were 1..49 shift down to 2..50; deals 51..100
  are unchanged.
- **Why:** the one deal is placed where you asked; the rest keep their relative order; the
  list stays 1..100.

### 11.2 The "relative" surprise (important to understand)
- **System:** Milk 1, Bread 2, Eggs 3, Juice 4, Soda 5. **You do:** import **only** Milk with
  Sequence 3.
- **After:** Bread 1, **Milk 2**, Eggs 3, Juice 4, Soda 5.
- **Why:** Milk asked for 3, but only Bread was ahead of it in the file's view, so after
  compacting Milk lands at 2, not 3. **To place deals at exact numbers, import the full
  export**, not a partial file.

### 11.3 Deals not in the file are safe
- Any deal you did not include is **kept**, keeps its relative order, and is never lost. Its
  exact number may shift as others move.

---

## 12. Zero / empty cases

### 12.1 No deals in the system yet, import new deals
- **You do:** import 3 new deals with Sequence 2, 1, 3.
- **After:** they become 1, 2, 3 in the order you asked.

### 12.2 No deals in the system, import new deals with all blanks
- They are numbered **1, 2, 3 in the order they appear in the file**.

### 12.3 Import a file with no valid deals (all rows bad/empty)
- Nothing is imported; existing deals are **unchanged**. (Because nothing was processed, the
  clean-up renumber does not run this time.)

### 12.4 Export when there are no deals
- The export returns a "No deals found" message (there is nothing to download).

### 12.5 All deals are expired/suspended (zero orderable), import them
- They stay non-orderable with **no numbers**, unless the file changes their dates to the
  future (then they become active and get numbered).

---

## 13. Round-trip (export -> edit -> import)

### 13.1 Export, change nothing, re-import
- **After:** nothing moves. The order is stable.

### 13.2 Export, reorder, re-import (the normal workflow)
- Change the Sequence numbers (or reorder rows and renumber), re-import the **full** file.
- **After:** the exact order you set is applied, 1..N, no duplicates, no gaps.

### 13.3 Export, then someone adds/pauses a deal in the app before you re-import
- Your file is now slightly out of date. Import still works: the deals in your file are
  placed as you asked; deals added/paused in between are handled correctly (paused ones drop
  out of the numbering, new ones fit in). The list stays clean 1..N.

---

## 14. Human error cases (and what the system does)

### 14.1 Typo in a promo code
- **You do:** the deal is "NS100" but you accidentally type "NS1OO" (letter O).
- **Result:** the system does not find a deal called "NS1OO", so it treats the row as a
  **new deal** and may create one. The original "NS100" is untouched and still exists.
- **Watch out:** this can create a look-alike duplicate deal. This is a data-entry mistake,
  not something the Sequence logic can detect. **Do not change promo codes unless you mean
  to.**

### 14.2 Changing an in-store deal's name or rule type
- In-store deals are identified by **promo code + name + rule type**. If you change any of
  these, the system sees a **different** deal and may create a new one instead of updating
  the old one. Keep these fields stable when editing.

### 14.3 Same promo code used for two different new deals in the file
- The system treats them as the **same** deal (promo code is the identity) and merges them
  into one. To keep them separate, use different promo codes.

### 14.4 You split a multi-row deal and typed different numbers on its rows
- Covered in Section 8: it stays **one** deal; the first non-empty number wins; the rest are
  ignored (and logged). No duplicate, no split.

### 14.5 You deleted the header row or renamed the Sequence column
- If the column name is not exactly "Sequence", the system does not see it, so it behaves
  like "no Sequence column" (Section 7): order preserved, nothing lost.

### 14.6 You typed the same number for many deals
- All resolved by the tie-breaker and renumbered to unique values (Section 5). Nothing lost.

### 14.7 You pasted numbers with formatting ($, commas, spaces, text)
- The system reads the digits it can ("$3" -> 3, "1,000" -> 1000, "abc" -> blank). See
  Section 6.

### 14.8 You imported a promo code that belongs to a spin or reward (or an in-app code clash)
- The row is **rejected by the existing uniqueness rules** (unrelated to Sequence). That one
  deal is skipped; all other deals import normally. (This skip is an existing rule, not new.)

### 14.9 You reused a deleted deal's promo code
- Because deleted deals are ignored, the code can be reused and a new deal is created.

---

## 15. Worst / stress cases

### 15.1 A huge file (thousands of rows) with a mix of everything
- Duplicates, blanks, junk, new and old deals, scattered multi-row deals, all in one file.
- **Result:** still resolves to a clean 1..N. Each deal gets one number (first non-empty),
  duplicates are broken deterministically, blanks/new go to the end, nothing is dropped for
  a Sequence reason. It is fast (a single sort plus one bulk update).

### 15.2 Every deal set to 1
- Compacts to the current order, 1..N. (Section 5.4)

### 15.3 Every Sequence blank
- Keeps the current order, healed to 1..N.

### 15.4 Every Sequence a huge number
- All beyond range but in the order given, so they compact to 1..N in that order.

### 15.5 Conflicting everything (dup + blank + junk + new + paused) in one import
- Handled together: paused stay out of numbering, junk/blank treated as "no position", new
  go last, duplicates broken by tie-break, final list clean 1..N. No crash, no data loss.

---

## 16. Existing data cleanup (one-time, good to know)

- Before this feature, **expired deals kept their old numbers**. Those old numbers overlapped
  with active deals, so the data already contained duplicate numbers (in the dev database
  there were 79 such overlaps).
- The new logic clears numbers from expired/suspended deals and renumbers the active set to a
  clean 1..N. This happens **automatically on the first import**, and can also be run as a
  **one-time cleanup** per environment before go-live.

---

## 17. Quick reference (all cases at a glance)

| Case | What happens |
|---|---|
| New deal with a number | Placed at that number; others shift; total +1 |
| New deal, blank/invalid | Created and added at the end |
| New deal, past dates | Created but no number (expired) |
| Existing deal moved | Goes to the typed position; others shift |
| Existing deal, blank | Keeps its place |
| Number already used | The one that typed it wins; the other shifts down |
| Two deals typed same number | Both kept; adjacent unique numbers |
| All set to same number | Compacted to current order, 1..N |
| Text / symbols / words | Digits read if any, else treated as blank |
| Zero / negative | Treated as blank |
| Decimal | Rounded down |
| No Sequence column | Order unchanged; nothing lost |
| Multi-row, rows agree | That number used |
| Multi-row, rows differ | First non-empty used; rest ignored+logged |
| Gaps (1,2,50) | Compacted to 1..N |
| Number bigger than list | Placed at the end |
| Existing gap in data | Healed to 1..N on next import |
| Expired deal | No number; blank in export |
| Suspended deal in file | Reactivated and numbered |
| Deleted deal | Ignored entirely |
| Partial import | Deals placed relatively; others kept; may shift |
| Empty system, import new | Numbered 1..N |
| Empty/invalid file | Nothing imported; existing unchanged |
| Export with no deals | "No deals found" message |
| Typo in promo code | Treated as a new deal (watch out) |
| Rename in-store deal fields | Treated as a new deal (watch out) |
| Duplicate promo in file | Merged into one deal |
| Huge messy file | Resolves to clean 1..N; nothing dropped |

---

## 18. The four guarantees (summary)

1. The active list is always **1..N with no duplicates and no gaps** after an import.
2. **No deal is ever dropped** because of a Sequence value.
3. A deal always has **one** number; two deals never share a number.
4. **Expired and suspended deals hold no number**; suspended deals in the file are
   reactivated and numbered.

Anything you type is treated as a best-effort request; the system always turns it into a
clean, valid order.

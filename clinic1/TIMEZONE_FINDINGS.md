# Timezone / DST — test findings (dev.clinic1.ai)

Spec: `QA_TIMEZONE_DST (2).md` · Runs: 2026-10-01 and 2026-10-02 (before the Sun 4 Oct 2026 AU DST start).
Code: `tests/timezone/` — run `npx playwright test tests/timezone` (add `--headed` for UI, `ALL_ZONES=1` for all 418 zones in the portal test).

## How the system works (learned in the walkthrough)
- Every API request carries a `timezone` header = the viewer's browser zone. Without it the server assumes `Australia/Sydney`.
- **Staff screens** (`/schedule/settings`, `schedule-override/calendar`) show weekly hours as `stored UTC + the viewer zone's STANDARD offset` (no DST). Correct for a viewer whose zone is in the same DST state as the clinic.
- **Public booking portal** (`booking.dev.clinic1.ai/online-booking/<code>`, API `/public/<code>/availability/optimized`) works on real instants and converts to the viewer's zone with the true offset on that date.
- Overrides and appointments are date-specific. Bookings are absolute (`startDateTime` in UTC).

## Coverage and results

| Area | Result |
|---|---|
| Standard-offset model, all 418 IANA zones (round-trip, midnight wrap, 2026-2055 stability, 13:00 stays in 13:00-17:00 band) | PASS |
| Portal slots vs independently computed expectation, **49 zone profiles x 3 dates** (3, 4, 5 Oct; half-hour/quarter-hour zones, Lord Howe, NZ, Kiribati, UTC-12) | PASS |
| Portal slot-counts agree with slot lists; bad zone header -> 400; injection-ish header -> no 5xx | PASS |
| Test 2: every booked appointment 5 Oct-15 Nov appears at the same local time in the portal (13:00 booking inside 13:00-17:00 band) | PASS |
| Test 6: Sat 24 Oct 11:00-11:30 override: Sydney 11:00, Brisbane 10:00, Kolkata 05:30, Auckland 13:00 (true instants) | PASS |
| Test 4: edit override 11:00-11:30 -> 09:00-12:00 reads back identically (staff UI + portal) | PASS |
| Override delete restores normal hours; create/edit/delete round-trip | PASS |
| Override negatives: end<start, zero-length, 25:99, text, overlap, empty slots, endDate<startDate, bad dayIndex, missing scheduleId, bad practitionerId, unauthenticated -> all 4xx | PASS |
| Sep vs Oct schedule reads identical (Sydney, Kolkata control, BRISBANE) | PASS today; **re-run on/after 4 Oct** |
| Test 1/5/7 server-clock regression | NOT TESTABLE until server date passes 4 Oct |
| Test 3 portal vs diary | PASS (BRISBANE/Petra; Sydney Wellness portal blocked by bug 10) |
| Test 9 Halaxy / Splose sync | **BLOCKED**: Splose "connected: false"; Halaxy not in this tenant's integration list. Needs your own account/API keys. |

## Bugs

| # | Layer | Sev | Finding |
|---|---|---|---|
| 1 | Staff UI/API (spec Test 8) | High | Cross-timezone staff view is 1h wrong whenever viewer and clinic differ in DST state. Sydney clinic Tue 13:00-17:00 in October shows 13:00 to a Brisbane viewer (should be 12:00), 11:00 to Perth (10:00), 08:30 to Kolkata (07:30). Portal shows the correct values, so staff screens and portal disagree for the same slot. Reproduced in the UI (Kolkata browser shows "8:30 AM - 12:30 PM" on 5 Oct). `override-lifecycle.spec.js` Test 8 block. |
| 2 | Staff write path | High | Override typed by a Kolkata viewer (Sydney clinic): typed 11:00 reads back as 15:30 in Sydney and 10:00 in Kolkata (portal, 31 Oct). Neither "as typed" nor "clinic time" - one hour lost in the clinic's DST period. |
| 3 | Spec / design | High (confirm) | Spec says standard offset = "offset the zone spends most of its time in". In 130 zones (all Europe, Sydney, Melbourne, Hobart, Auckland...) DST is the longer period, so that rule returns the DST offset. Sydney 2026 = +11 (183 vs 182 days), flips to +10 in 2029/2035; contradicts the spec's 03:00 -> 13:00 example. Ask the dev how the offset is really chosen. `all-zones.spec.js` FINDING test. |
| 4 | Data | High | "BRISBANE HEALTH CLINIC" is configured `Australia/Sydney` (DST). A true Brisbane clinic would shift on 4 Oct. No true non-DST AU control exists. |
| 5 | Data | Medium | Sydney Wellness: clinic hours Tue-Sun 03:30-13:30 / Mon 05:30-13:30 (wrong-offset data per spec's "re-save" note); BRISBANE Thu practitioner 08:00-22:00 past clinic close 18:00. |
| 6 | API | Medium | HTTP 500 (should be 400) leaking driver errors: `practitionerId=xyz`, `locationId=xyz`, `locationId[$ne]=1`, `appointment/scheduler?limit=0` / `page=-1`, **portal `availability/optimized?date=not-a-date`** ("Invalid time value"). |
| 7 | API | Medium | Accepted with 200 instead of 400: `startDate=2026-02-30`, `smart-slot period=bogus`. |
| 8 | Frontend | Medium | "Add Override" opens for a practitioner with "Schedule Not Found" and posts without `scheduleId` -> raw `Data validation failed ... scheduleId Required`. Disable/redirect to the practitioner profile instead. |
| 9 | Frontend | Medium | Every page logs `Failed to find a valid digest in the 'integrity' attribute ... unpkg.com/obi-sdk@latest` / "Obi SDK failed to load" (SRI hash on a floating @latest URL). |
| 10 | Portal | Medium | Sydney Wellness Clinic booking link (`xnM3xngd`) shows "No professions available" - `specialization/location/<id>?onlyWithPractitioners=true` returns empty although the location has practitioners. Patients cannot book there. |
| 11 | API | Low | `clinic/location?clinicId=000...` ignores the bogus id and returns the tenant's 6 locations (no cross-tenant leak seen). |
| 12 | API | Low | Zone alias mismatch: location `Asia/Kolkata` vs smart-slot report `Asia/Calcutta`. |
| 13 | UI | Low | Existing 12 Oct override displays 6:00 PM-9:00 PM (Sydney viewer) vs 1:30 PM-4:30 PM (Kolkata viewer): 1h off, same cause as bug 1 on date-specific data. |

### Retracted from the first report
- "Harbour Health practitioner 12:30-22:30": **test artifact** (request had no `timezone` header). With the header it is 08:00-18:00, correct.
- "Kolkata vs Calcutta mismatch" was first reported from a mismatched comparison; kept only as Low (#12).

## Test data touched on dev (all reverted)
- Created and deleted overrides for Petra Hughes @ BRISBANE: 17 Oct (UI), 24 Oct and 31 Oct (API). Verified afterwards: only the pre-existing 12 Oct override remains.
- The failed UI "Add Override" for Arlie Reid @ BRISBANE (bug 8) created nothing.
- No patients/appointments were created; bookings were not completed.

## Previously "not tested" — status (2 Oct 2026, server clock also 2 Oct)
| Item | Status |
|---|---|
| Test 5 diary grid vs opening hours | PASS (baseline): BRISBANE grid starts 08:00 AM = clinic hours 08:00-18:00; hatched morning is only "time already passed". Re-check after 4 Oct. |
| Test 7 non-DST control (Kolkata clinics) | PASS (baseline): hours identical Sep vs Oct for clinic and practitioners. |
| Tests 1, 5, 7 across the real DST boundary | **Still cannot run**: server date is 2 Oct. Baseline of 75 data points saved to `test-results/dst-baseline.json`; compare tool validated (0 differences on immediate re-run). |
| Test 9 Halaxy / Splose | **Still blocked**: no Halaxy/Splose screen exists in the staff app (checked Settings, Data Import, Invoices, Dashboard); API reports Splose `connected:false`, Halaxy absent. Needs real account credentials. |

After 4 Oct run: `node tests/timezone/snapshot.mjs compare` - any difference of exactly 1 hour is the spec's DST bug.

## To do on/after Sun 4 Oct 2026
Re-run `live-api.spec.js` and `portal-all-zones.spec.js` (before-vs-after server clock) and test Tests 1, 5, 7 on the three clinic types. Run `ALL_ZONES=1` once for the full 418 zones (~25 min).

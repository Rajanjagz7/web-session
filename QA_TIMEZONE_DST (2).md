# QA — Schedule times across Daylight Saving

**Branch:** `feature/timezone-dst` · **Area:** practitioner availability, clinic opening hours, schedule overrides, online booking
**Why now:** Australian DST begins **Sunday 4 October 2026**. Without this fix, that morning every DST-observing clinic's working hours move by an hour.

---

## 1. What changed — functional information

### The problem

A clinic's working hours are stored as a **time of day with no date attached** — for example Vigor's Tuesday is stored as `03:00-07:00` (UTC). To show that to a Sydney user the system adds Sydney's offset.

The bug: it added *whatever the offset happens to be today*.

- In September (Sydney is UTC+10) `03:00` reads as **13:00**.
- In October (Sydney is UTC+11) the same stored `03:00` reads as **14:00**.

Nothing in the database changed — the same stored value simply meant a different time of day depending on when you looked at it.

**Booked appointments do not work this way.** An appointment is stored as an exact moment in time, so a 1:00pm booking stays at 1:00pm forever.

So on the morning of 4 October, these two would have come apart:

| | Before 4 Oct | From 4 Oct (old behaviour) |
|---|---|---|
| Practitioner availability | 13:00 – 17:00 | **14:00 – 18:00** |
| Diary grid (clinic hours) | 08:00 – 18:00 | **09:00 – 19:00** |
| An existing 13:00 booking | 13:00 | 13:00 *(unmoved)* |

The working day appears to start an hour late, and yesterday's 1:00pm bookings now sit in a gap *before* the day opens. Patients booking online would see the wrong hours offered.

### The fix

Stored times are now always read using the zone's **standard** (non-DST) offset, and always written the same way. Because the same offset is used in both directions, the stored value now means one fixed wall-clock time — it reads 13:00 in January, in July, and on 4 October.

The standard offset is worked out from the timezone database itself, by sampling the whole year and taking the offset the zone spends most of its time in. **No country or city is hardcoded**, so it is correct for every clinic, including zones with unusual rules, and stays correct if a government changes its DST rules in future.

### What QA should expect to see

- **Nothing changes today.** Verified against all 1703 production schedules: zero clinics see a different working-day band the moment this deploys. This release is a no-op on the day it ships — its entire purpose is that nothing changes *on 4 October either*.
- **Working hours become stable year-round.** A clinic's hours read the same before and after any DST transition.
- **Bookings and availability stay aligned.** A 1:00pm appointment continues to sit inside the 1:00pm–5:00pm availability band in October.
- **The online booking portal matches the diary.** Both read hours the same way.

### Also fixed in this change

Two integration sync jobs — **Halaxy** and **Splose** — were writing practitioner hours in the clinic's local time into a field that is supposed to hold UTC. For an Australian clinic that stored hours roughly **10 hours off**. Any practitioner whose schedule arrived via those syncs had wrong hours. Now corrected.

### Removed

An earlier partial attempt (recording an offset on the schedule record when it was saved) has been removed and replaced by the approach above. It only applied when a schedule was *edited*, never when created; it recorded whichever offset was in force on the day someone pressed Save; and several other parts of the system rewrite schedule hours without updating that record.

**Known, pre-existing, not caused by this change:** a small number of schedules (12 in production) were saved with hours encoded against the wrong offset and already display an hour out **today**. They correct themselves the next time that schedule is saved. If QA finds a clinic an hour out *right now*, before doing anything else re-save its schedule and re-check.

---

## 2. Testing guide

### Prerequisites

Timezone bugs only appear when the clock crosses a DST boundary, so most tests need the **system date changed**. Do this on the test device (or a VM), not production.

- Sydney/Melbourne DST 2026 begins **Sun 4 Oct, 02:00** → clocks go forward to 03:00.
- Useful dates: **Wed 30 Sep** (before) and **Wed 7 Oct** (after).
- Test clinics needed: one in a **DST zone** (`Australia/Sydney`, `Australia/Melbourne`), one in a **non-DST zone** (`Australia/Brisbane` or `Australia/Perth`) as a control — the non-DST clinic must never change at any point.
- Have a practitioner with clearly recognisable hours, e.g. **Tuesday 13:00–17:00**.

> Always restore the correct system date afterwards, and hard-refresh the browser after each change — the frontend caches schedule data.

---

### Test 1 — Working hours survive the DST change (core test)

1. With the system clock at a normal date, open **Schedule / Diary** for the DST clinic. Record the practitioner's hours exactly, e.g. `13:00–17:00`, and the diary grid's first and last hour, e.g. `08:00–18:00`.
2. Set the system clock to **7 October 2026**.
3. Restart the backend, hard-refresh, open the same diary.

**Pass:** hours are identical — still `13:00–17:00`, grid still `08:00–18:00`.
**Fail:** anything moved by exactly one hour.

Repeat with the clock at **30 September 2026**; same expected result.

---

### Test 2 — Existing bookings stay inside the availability band

1. Before changing any clock, book an appointment at **13:00 on Tue 6 October**.
2. Confirm it appears at 13:00, inside the availability band.
3. Set the clock to **7 October 2026**, restart, refresh.

**Pass:** the appointment is still at 13:00 and still sits inside the band.
**Fail:** the appointment sits an hour before the band starts, or the band no longer covers it. *(This is the exact failure Vigor reported and the main thing this release prevents.)*

---

### Test 3 — Online booking portal agrees with the diary

1. Note the practitioner's available slots in the staff diary for **Tue 6 October** — first and last bookable slot.
2. Open the **patient booking portal** and select the same practitioner and date.

**Pass:** the offered slot times match the diary exactly.
**Fail:** the portal offers slots an hour out from the diary.

Repeat with the clock set to **7 October**. Both must still agree.

---

### Test 4 — Editing a schedule does not move it

This is the one most likely to catch a regression, because saving now re-encodes the times.

1. Open a practitioner's schedule, change **Tuesday** to `09:00–12:00`, save.
2. Reopen it.  → **Pass:** it still reads `09:00–12:00`.
3. Check the diary for a Tuesday **in September** → hours show `09:00–12:00`.
4. Check a Tuesday **in October** → hours show `09:00–12:00`.
5. Set the clock to **7 October**, restart, and repeat steps 2–4 → still `09:00–12:00` everywhere.

**Fail:** the hours read back an hour out immediately after saving, or differ between a September and an October date.

Repeat the whole test **with the clock already set to 7 October when you save** — a schedule saved during DST must read back correctly, and must still be right when the clock returns to a non-DST date.

---

### Test 5 — Clinic opening hours and the diary grid

1. In **Settings → Locations**, note the clinic's opening hours.
2. Check the diary grid's first and last hour match them.
3. Set the clock to **7 October**, restart, refresh.

**Pass:** opening hours unchanged, and the grid still matches them.

---

### Test 6 — Schedule overrides / one-off availability

1. Create an override or extra availability for a **Saturday in October**, e.g. `11:00–11:30`.
2. Confirm it shows at 11:00 in the diary and in the booking portal.
3. Set the clock to **7 October**, restart, refresh.

**Pass:** still 11:00 in both places.

---

### Test 7 — Non-DST clinic control

Repeat Tests 1, 2 and 5 for the **Brisbane or Perth** clinic.

**Pass:** absolutely nothing changes at any clock setting. If a non-DST clinic moves, that is a serious regression.

---

### Test 8 — Cross-timezone viewing

1. As a user whose device is in a **different** timezone from the clinic (e.g. device on Brisbane, clinic in Sydney), open the Sydney clinic's diary.
2. Expect the genuine time difference — in October, Sydney is one hour ahead of Brisbane, so Sydney's 13:00 correctly displays as 12:00 to a Brisbane viewer.

**Pass:** the difference matches the real offset between the two zones on that date.
**Fail:** the difference is wrong, or there is no difference at all in October.

---

### Test 9 — Halaxy / Splose integrations

Only if a test clinic has one of these connected.

1. Run the practitioner/schedule sync.
2. Open the synced practitioner's schedule.

**Pass:** hours match what the source system shows (e.g. 9:00am in Halaxy appears as 9:00am here).
**Fail:** hours are out by ~10 hours — that was the old behaviour.

---

### Regression sweep

Nothing below should be affected, but these share the schedule code:

- Room bookings and room availability
- Class timetable and class booking
- Appointment reminders firing at the right local time
- Utilisation / practitioner-hours reports
- Clinic signup with a schedule, and adding a new practitioner

---

### Reporting a failure

Include: clinic name and its timezone, practitioner, the **date being viewed**, the **system clock date**, the screen, expected vs actual time, and whether it is out by exactly one hour. One-hour discrepancies are the signature of this class of bug; anything else is probably unrelated.

### Automated coverage

`npx tsx --test src/helpers/timezone.helper.test.ts src/app/schedule/schedule.helper.test.ts src/app/user/practitioner/slotWindows.helper.test.ts` — 30 tests, all passing. Includes checks that every IANA timezone reads the same time of day at every point of the year and across 2026–2055.

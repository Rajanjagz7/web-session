# Clinic1 — Timezone / DST walkthrough (dev.clinic1.ai)

Source spec: `QA_TIMEZONE_DST (2).md`. Walkthrough run 2026-10-01 (3 days before AU DST starts, Sun 4 Oct 2026).
Login: tenant `sunrise-family-medical` (user also belongs to Laser Clinics Australia, Rejuvenation Clinics).

## 1. Where time/timezone enters the product

| Area (URL) | API feeding it | Time fields | Spec test |
|---|---|---|---|
| Schedule > Calendar `/schedule` (diary grid) | `GET /appointment/scheduler`, `/clinic/location` | startDateTime, endDateTime, startTime, endTime, timezone | 1, 2, 5, 8 |
| Schedule > Settings `/schedule/settings` (practitioner weekly/fortnight/month hours, overrides) | `GET /schedule-override/calendar`, `/practitioner/web` | days[].slots[].startTime/endTime | 1, 4, 6 |
| Location opening hours (`scheduleDetails`) | `GET /clinic/location` (has `timezone`, `scheduleTimezone`, `scheduleDetails`) | slots startTime/endTime | 5, 7 |
| Appointments (tabs under dashboard) | `/appointment/scheduler`, `/clinic/dashboard/unverified-bookings` | startDateTime/endDateTime | 2, 3 |
| Classes `/classes` | `GET /class` (sortBy=startDateTime) | startDateTime/endDateTime | regression |
| Room Booking `/room-booking` | `GET /room-booking` | start/endDateTime | regression |
| Dashboard / Smart-slot report | `/report/smart-slot` (returns `timezone`), `/clinic/dashboard*` | period buckets, startTime/endTime | regression (utilisation) |
| Activity log `/activity-log` | `GET /history` | startDateTime/endDateTime | regression |
| Patients / Invoices | `/patient/get`, `/invoice` | timezone, date | regression |
| Public booking portal | not yet located (needs clinic public URL) | slots | 3 |
| Halaxy / Splose sync | not exercised (needs integration) | practitioner hours | 9 |

Pages that redirect to `/dashboard` when opened by URL: `/schedule/calendar`, `/appointments`, `/case`, `/settings/locations`, `/data-import` (they are sub-tabs, reached via the sidebar).

## 2. Key data model facts
- Server returns hours already converted to the **location's local time** (`08:00–18:00`), plus `timezone` / `scheduleTimezone` on each location. The DST bug lives in that server conversion, so it cannot be seen by changing the browser clock — only by the **server date** crossing 4 Oct (or by comparing dates once past it).
- Booked appointments are absolute instants; availability is time-of-day. The spec's failure = these diverge by 1 hour.

## 3. Test data available (6 locations)
| Location | timezone | Use as |
|---|---|---|
| Sydney Wellness Clinic | Australia/Sydney | DST clinic |
| Australian Clinic Sydney | Australia/Sydney | DST clinic |
| BRISBANE HEALTH CLINIC | **Australia/Sydney** | NOT a valid non-DST control (see finding B) |
| Harbour Health Clinic | Asia/Kolkata (+5:30, no DST) | non-DST control |
| Melbourne Primary Care | Asia/Kolkata | non-DST control |
| Southern Cross Medical Centre | Asia/Kolkata | non-DST control |

Spec asks for Brisbane/Perth as control; none exists — Asia/Kolkata is the only non-DST option (acceptable control, but not the same as AU).

## 4. Pre-test observations (data/config, not yet confirmed bugs)
- **A. Practitioner vs clinic hours mismatch.** Harbour Health (Kolkata): clinic 08:00–18:00 but practitioners 12:30–22:30. Sydney Wellness: clinic Tue–Sun 03:30–13:30, Mon 05:30–13:30. Both look like hours encoded against the wrong offset (the spec's "pre-existing, fixed by re-saving the schedule" case) — 4h30 off, not 1h. Needs triage: re-save and re-check.
- **B. "BRISBANE HEALTH CLINIC" is configured Australia/Sydney.** A Brisbane clinic must be Australia/Brisbane (no DST). If the clinic is genuinely Brisbane, its hours will wrongly shift on 4 Oct.
- **C. Sep vs Oct reads are identical today** (server clock = 1 Oct, pre-DST). Must be re-run after 4 Oct; this is the real regression window.

## 5. Planned test layers
1. **API**: for every location/practitioner, fetch hours for a Sep date and an Oct date; assert identical; assert booked 13:00 appointment (6 Oct) stays 13:00 and inside availability; assert non-DST locations unchanged.
2. **UI (headed)**: Schedule Settings & Calendar grid hours per location; edit Tue to 09:00–12:00 and reload (Test 4); override on a Saturday in October (Test 6); location switcher.
3. **Negative/edge**: invalid/missing timezone, 02:00–03:00 gap on 4 Oct, 23:59/00:00 boundaries, overlapping slots, end<start, cross-midnight slots, non-DST vs DST control, cross-timezone viewer.
4. **Exploratory**: portal slots vs diary, reminders, reports, class/room booking across the boundary.

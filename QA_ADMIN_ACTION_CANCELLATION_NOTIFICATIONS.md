# Clinic Action Cancellation Notifications - Manual QA Guide

Asana: [Clinic action cancellation - notification](https://app.asana.com/1/757630589075869/project/1211749193102969/task/1213000044435279)

## What to test

When a clinic cancels appointments in bulk from **Settings → Admin Actions → Cancel All Appointments** (used for a sick day, a closure, a practitioner being away), every affected patient must now be told — the same cancellation notice they would get if the appointment had been cancelled one-by-one from the diary.

Before this change the appointments were cancelled silently. Patients only found out by turning up.

## Important rules

- Every patient whose appointment is cancelled by a Clinic Action gets the cancellation notice.
- The notice is the same one the diary cancel sends: same wording, same channels, same clinic-local time.
- Channels still obey the existing settings — clinic notification settings first, then the patient's own preferences. This change does **not** bypass either.
- The cancel request returns straight away. Notices are sent in the background, so a large cancel does not make the screen hang.
- One patient's notice failing must not stop the other patients from getting theirs.
- The Clinic Action detail screen shows how many patients were notified.
- The practitioner and the clinic owners are **not** sent one notice per cancelled appointment. That would be dozens of messages for a single sick day, and the person running the action already knows.
- Waitlisted patients are **not** told the slot opened up. The practitioner is away — that slot should not be filled.
- No cancellation fee and no cancellation case is created. The clinic cancelled, not the patient.
- Cancelling from the diary must behave exactly as it did before this change.

## Setup

Use a test clinic and test patients only.

Create:
- one practitioner with **at least 3 future appointments** on the same day, each with a different patient
- patient A: has the mobile app installed (push token) and an email address
- patient B: email only, no app
- patient C: any patient — used for the failure/edge checks
- confirm in **Settings → Notifications** that the clinic has "Appointment Cancelled By Clinic" turned on for patients, with email and push enabled

Note the clinic's SMS setting for that notification type. If clinic SMS is off, **no SMS will be sent** — that is correct behaviour, not a bug. Turn it on if you want to test SMS.

## Main test - practitioner sick day

1. Go to **Settings → Admin Actions → Cancel All Appointments**.
2. Confirm the blue note is visible above the buttons, saying patients are notified automatically.
3. Choose **Practitioner**, pick the practitioner, enter a reason, and set the start and end date to that day.
4. Submit.
5. The success message should appear **immediately** — no long spinner.
6. Check every patient:
   - patient A: cancellation email received, and a push notification on the app
   - patient B: cancellation email received
   - both: the notice appears in their in-app notification list
7. Open the email and check:
   - it names the practitioner
   - the date and time shown match the appointment in **clinic time**, not your own timezone
   - the location name is correct
8. Go to **Appointments → Clinic Action**, open the action just created.
9. It should show **Patients Notified: 3 of 3**. Immediately after submitting it may briefly show "Sending…" — refresh after a few seconds.
10. Confirm the appointments are Cancelled in the diary and the slots are freed.

## Clinic-wide cancel

Repeat the main test choosing **Clinic** instead of Practitioner, with appointments across two different practitioners. Every patient of every cancelled appointment must get the notice, and the count on the Clinic Action must match the number of cancelled appointments.

## Diary cancel - regression

This is the flow that already worked and must not change.

1. Cancel a single appointment from the diary/booking list as clinic staff.
2. The patient gets the cancellation notice, as before.
3. The practitioner gets their notice, as before.
4. The clinic owners get their notice, as before.
5. Cancel a single appointment as the patient (patient app). The patient, practitioner and clinic owners get their notices and a cancellation case is created, as before.
6. Choose "Patient requested cancellation" in the dialog and confirm the cancellation fee policy still shows and the case is still created.

## Edge cases

| Case | Expected |
|---|---|
| Date range with no appointments in it | "No appointments found to cancel", no Clinic Action created, nothing sent |
| Patient has turned off cancellation notifications in their own preferences | No notice to that patient; the others still get theirs; the count reflects what was actually sent |
| Clinic has the notification type turned off entirely | Nothing sent to anyone; the action still records the cancellations |
| Patient with no mobile app | Email only, no push — not an error |
| An old Clinic Action created before this release | Detail screen shows **no** "Patients Notified" row at all (not "0 of 4") |
| Cancel a day that has a group class booking in it | Attendees' seats are freed as before |
| Waitlisted patients exist for a cancelled slot | They are **not** told the slot opened |

## What to check in the data (dev/stage)

For each cancelled appointment:
- `notifications` collection has a row for the patient with type `appointmentCancelledByClinic`
- the appointment now has `cancelledBy` set (this was previously left empty on bulk cancels)
- the `adminactions` record has `patientsNotified`, `patientsNotifyFailed` and `notificationsCompletedAt`
- if clinic SMS is on, `smslogs` has a row per patient

## Automated tests

```bash
npx tsx --test src/app/appointment/appointmentCancellationNotifier.test.ts src/app/adminAction/adminAction.notify.test.ts
```

Regression suites for the untouched cancel paths:

```bash
npx tsx --test src/app/appointment/appointment.service.cancel.test.ts src/app/appointment/appointment.controller.groupUpdate.notify.test.ts
```

Note: `appointment.controller.status.test.ts` has two pre-existing failures (T2, T3) that also fail on a clean checkout — they need a database connection. Not related to this change.

## Known gaps, deliberately not covered

- The free-text reason typed into the cancel-all form is stored on the Clinic Action but is **not** included in the patient's message. The patient gets the standard "cancelled by the clinic, please rebook" wording, matching the diary cancel. Changing this is a separate decision.
- Group cancel and removing an attendee from a group appointment still send nothing to the affected patients. Same underlying gap, separate ticket.

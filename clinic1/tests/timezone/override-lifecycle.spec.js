// @ts-check
// MUTATING: creates/edits/deletes schedule overrides for Petra Hughes @ BRISBANE HEALTH CLINIC (Australia/Sydney) on dev.
// Every override created here is tracked and deleted in afterAll, including ones a negative test accidentally creates.
const { test, expect, request } = require('@playwright/test');
const path = require('path');
const { offsetMinutes } = require('./helpers');

const CID = '6a32753a139744ccb3181d73';
const LOC = '6ab118ed88d0bf82a08492fd';
const PR = '6ab119b788d0bf82a0849810';
const SCHEDULE = '6ab119b788d0bf82a0849814';
const CODE = 'sCYjCtj7';
const Q = `practitionerId=${PR}&clinicId=${CID}&locationId=${LOC}&slotDuration=30&appointmentTypeId=6ab1208888d0bf82a084adb2&consultationTypeId=6ab1208888d0bf82a084adb1&practitionerServiceId=6ab1208888d0bf82a084adc2`;
const STAFF = 'https://sunrise-family-medical.dev.clinic1.ai';
const auth = path.join(__dirname, '../../playwright/.auth/tz-user.json');
const created = [];
let sydney;

const staffAs = tz => request.newContext({ baseURL: STAFF, storageState: auth, extraHTTPHeaders: { timezone: tz } });
async function portal(tz, date) {
  const c = await request.newContext({ baseURL: 'https://dev.clinic1.ai', extraHTTPHeaders: { timezone: tz } });
  const r = await c.get(`/api/v1/public/${CODE}/availability/optimized?${Q}&date=${date}`);
  const j = await r.json();
  await c.dispose();
  return Object.values(j.response?.[0]?.availabilityDay?.slots || {}).flat().map(s => s.startTime);
}
const body = (date, end, slots, extra = {}) => ({ clinicId: CID, locationId: LOC, practitionerId: PR, scheduleId: SCHEDULE, startDate: date, dayIndexes: [new Date(date + 'T00:00:00Z').getUTCDay()], frequency: 'Week', slots, endDate: end, ...extra });
const slot = (s, e) => ({ startTime: s, endTime: e, slotType: 'Schedule', reason: 'Work hours' });
async function create(client, payload) {
  const r = await client.post('/api/v1/schedule-override', { data: payload });
  const t = await r.text();
  let id; try { id = JSON.parse(t).response?._id; } catch { /* ignore */ }
  if (id) created.push(id);
  return { status: r.status(), id, text: t };
}

test.beforeAll(async () => { sydney = await staffAs('Australia/Sydney'); });
test.afterAll(async () => {
  for (const id of created) await sydney.delete(`/api/v1/schedule-override/${id}`).catch(() => {});
  await sydney.dispose();
});

test.describe.serial('Override lifecycle (spec Tests 4 and 6)', () => {
  const DATE = '2026-10-24'; // a Saturday after the DST change
  let id;

  test('POSITIVE: create Sat 24 Oct 11:00-11:30 as a Sydney viewer -> portal shows 11:00', async () => {
    const r = await create(sydney, body(DATE, '2026-10-25', [slot('11:00', '11:30')]));
    expect(r.status, r.text.slice(0, 200)).toBe(200);
    id = r.id;
    expect(await portal('Australia/Sydney', DATE)).toEqual(['11:00']);
  });

  test('POSITIVE: same override is the true instant for other viewers (Brisbane 10:00, Kolkata 05:30, Auckland 13:00)', async () => {
    expect(await portal('Australia/Brisbane', DATE)).toEqual(['10:00']);
    expect(await portal('Asia/Calcutta', DATE)).toEqual(['05:30']);
    expect(await portal('Pacific/Auckland', DATE)).toEqual(['13:00']);
  });

  test('POSITIVE: staff calendar read-back is unchanged for a Sydney viewer', async () => {
    const r = await (await sydney.get(`/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=${LOC}&practitionerId=${PR}&startDate=2026-10-01&endDate=2026-10-31`)).json();
    const o = r.response[0].overrides.find(x => x._id === id);
    expect(o.slots[0]).toMatchObject({ startTime: '11:00', endTime: '11:30' });
  });

  test('POSITIVE (Test 4): editing the date to 09:00-12:00 reads back identically', async () => {
    const r = await sydney.patch(`/api/v1/schedule-override/${id}`, { data: { ...body(DATE, '2026-10-25', [slot('11:00', '11:30')]), exactDateOverrides: [{ date: DATE, mode: 'Custom', slots: [slot('09:00', '12:00')] }] } });
    expect(r.status(), (await r.text()).slice(0, 200)).toBe(200);
    expect(await portal('Australia/Sydney', DATE)).toEqual(['09:00', '09:30', '10:00', '10:30', '11:00', '11:30']);
  });

  test('POSITIVE: delete restores the normal Saturday hours (08:00-17:30, 20 slots)', async () => {
    const r = await sydney.delete(`/api/v1/schedule-override/${id}`);
    expect(r.status()).toBe(200);
    created.splice(created.indexOf(id), 1);
    const s = await portal('Australia/Sydney', DATE);
    expect(s[0]).toBe('08:00');
    expect(s.at(-1)).toBe('17:30');
    expect(s).toHaveLength(20);
  });

  test('FINDING: override typed by a Kolkata viewer must read back as typed (portal Kolkata = 11:00) or as clinic time (Sydney = 11:00)', async () => {
    const kol = await staffAs('Asia/Calcutta');
    const D2 = '2026-10-31';
    const r = await create(kol, body(D2, '2026-11-01', [slot('11:00', '11:30')]));
    await kol.dispose();
    expect(r.status, r.text.slice(0, 200)).toBe(200);
    const syd = await portal('Australia/Sydney', D2);
    const ind = await portal('Asia/Calcutta', D2);
    // either the 11:00 is read as clinic-local (syd = 11:00) or as viewer-local (ind = 11:00); anything else is a bug
    expect(syd.includes('11:00') || ind.includes('11:00'), `Sydney sees ${syd}, Kolkata sees ${ind}`).toBeTruthy();
    test.info().annotations.push({ type: 'cross-tz-write', description: `typed 11:00 as Kolkata viewer -> Sydney portal ${syd.join(',')} | Kolkata portal ${ind.join(',')}` });
  });

});

test.describe('Override - negative and edge payloads (any accidental create is cleaned up)', () => {
  const D = '2026-11-07';
  const cases = [
    ['end before start (14:00-13:00)', body(D, '2026-11-08', [slot('14:00', '13:00')])],
    ['zero-length slot 10:00-10:00', body(D, '2026-11-08', [slot('10:00', '10:00')])],
    ['invalid time 25:99', body(D, '2026-11-08', [slot('25:99', '26:00')])],
    ['non-time text', body(D, '2026-11-08', [slot('abc', 'def')])],
    ['overlapping slots', body(D, '2026-11-08', [slot('09:00', '12:00'), slot('11:00', '13:00')])],
    ['empty slots array', body(D, '2026-11-08', [])],
    ['endDate before startDate', body(D, '2026-11-01', [slot('09:00', '10:00')])],
    ['invalid dayIndex 9', body(D, '2026-11-08', [slot('09:00', '10:00')], { dayIndexes: [9] })],
    ['missing scheduleId', (() => { const b = body(D, '2026-11-08', [slot('09:00', '10:00')]); delete b.scheduleId; return b; })()],
    ['malformed practitionerId', body(D, '2026-11-08', [slot('09:00', '10:00')], { practitionerId: 'xyz' })],
    ['cross-midnight 22:00-02:00', body(D, '2026-11-08', [slot('22:00', '02:00')])],
    ['past date 2020-01-01', body('2020-01-01', '2020-01-02', [slot('09:00', '10:00')])],
    ['DST-gap time 02:30 on 4 Oct', body('2026-10-04', '2026-10-05', [slot('02:30', '03:30')])],
  ];
  for (const [name, payload] of cases) {
    test(`NEGATIVE: ${name} -> no 5xx`, async () => {
      const r = await create(sydney, payload);
      expect(r.status, `${r.status} ${r.text.slice(0, 160)}`).toBeLessThan(500);
      test.info().annotations.push({ type: 'result', description: `${r.status}${r.id ? ' (ACCEPTED - created, will be deleted)' : ''}` });
    });
    test(`VALIDATION: ${name} should be rejected (4xx)`, async () => {
      test.skip(/DST-gap|past date|cross-midnight/.test(name), 'business-rule dependent; recorded by the no-5xx test above');
      const r = await create(sydney, payload);
      expect(r.status, `accepted: ${r.text.slice(0, 120)}`).toBeGreaterThanOrEqual(400);
    });
  }
  test('NEGATIVE: unauthenticated create is rejected', async () => {
    const anon = await request.newContext({ baseURL: STAFF });
    const r = await anon.post('/api/v1/schedule-override', { data: body(D, '2026-11-08', [slot('09:00', '10:00')]) });
    await anon.dispose();
    expect([401, 403]).toContain(r.status());
  });
  test('NEGATIVE: DELETE of unknown override id -> 4xx not 5xx', async () => {
    for (const id of ['000000000000000000000000', 'xyz']) {
      const r = await sydney.delete(`/api/v1/schedule-override/${id}`);
      expect(r.status(), `${id} -> ${r.status()} ${(await r.text()).slice(0, 100)}`).toBeLessThan(500);
    }
  });
});

test.describe('Staff view across viewer timezones vs portal truth (spec Test 8)', () => {
  const tzs = ['Australia/Sydney', 'Australia/Brisbane', 'Australia/Perth', 'Asia/Calcutta', 'Pacific/Auckland', 'America/New_York', 'Europe/London'];
  for (const tz of tzs) {
    test(`staff Tuesday band for viewer ${tz} equals the real offset in October`, async () => {
      const c = await staffAs(tz);
      const r = await (await c.get(`/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=${LOC}&practitionerId=${PR}&startDate=2026-10-05&endDate=2026-10-11`)).json();
      await c.dispose();
      const tue = r.response[0].schedule.days.find(d => d.day === 'Tuesday').slots[0];
      // Sydney 13:00 AEDT (+11) on 6 Oct -> viewer-local
      const utc = Date.UTC(2026, 9, 6, 13, 0) - 11 * 60 * 60000;
      const off = offsetMinutes(tz, utc);
      const m = (13 * 60 - 11 * 60 + off + 1440 * 2) % 1440; // 13:00 - 11h + viewer offset
      const exp = `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;
      expect(tue.startTime, `${tz}: staff view ${tue.startTime}-${tue.endTime}, real local time is ${exp}`).toBe(exp);
    });
  }
});

test.describe('Existing bookings vs availability (spec Test 2)', () => {
  test('POSITIVE: every booked appointment 5 Oct - 15 Nov appears as a booked slot at the same local time in the portal (Sydney)', async () => {
    const c = await staffAs('Australia/Sydney');
    const r = await (await c.get(`/api/v1/appointment/scheduler?page=1&limit=200&clinicId=${CID}&locationId=${LOC}&startDate=2026-10-05&endDate=2026-11-15`)).json();
    await c.dispose();
    const g = r.response.groupedByPractitioner.find(x => x.practitioner._id === PR);
    const bad = [];
    for (const a of g?.appointments || []) {
      const t = Date.parse(a.startDateTime);
      const loc = new Date(t + offsetMinutes('Australia/Sydney', t) * 60000);
      const date = loc.toISOString().slice(0, 10);
      const hhmm = loc.toISOString().slice(11, 16);
      const slots = await portal('Australia/Sydney', date);
      if (!slots.includes(hhmm)) bad.push(`${a.startDateTime} (Sydney ${date} ${hhmm}) not inside that day's availability: ${slots[0]}..${slots.at(-1)}`);
    }
    expect(bad, bad.join(', ')).toEqual([]);
  });
});

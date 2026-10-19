// @ts-check
// Public booking portal vs. an independently computed expectation, for every distinct timezone behaviour.
// Read-only (GET only). Set ALL_ZONES=1 to test all ~418 zones instead of one per distinct offset profile.
const { test, expect, request } = require('@playwright/test');
const path = require('path');
const { offsetMinutes, allZones } = require('./helpers');

const CID = '6a32753a139744ccb3181d73';
const LOC = '6ab118ed88d0bf82a08492fd'; // BRISBANE HEALTH CLINIC (configured Australia/Sydney)
const PR = '6ab119b788d0bf82a0849810'; // Petra Hughes
const CODE = 'sCYjCtj7';
const CLINIC_TZ = 'Australia/Sydney';
const Q = `practitionerId=${PR}&clinicId=${CID}&locationId=${LOC}&slotDuration=30&appointmentTypeId=6ab1208888d0bf82a084adb2&consultationTypeId=6ab1208888d0bf82a084adb1&practitionerServiceId=6ab1208888d0bf82a084adc2`;
const DATES = ['2026-10-03', '2026-10-04', '2026-10-05']; // before / on / after the Sydney DST start
const DAY_MS = 86400000;

const pad = n => String(n).padStart(2, '0');
const fmtT = m => `${pad(Math.floor(m / 60))}:${pad(m % 60)}`;
const toMin = t => +t.slice(0, 2) * 60 + +t.slice(3);

/** local wall time in `zone` -> UTC ms (handles DST by trying candidate offsets) */
function localToUtc(zone, y, mo, d, minutes) {
  const guess = Date.UTC(y, mo - 1, d, 0, minutes);
  for (const delta of [0, -60, 60, -30, 30, -90, 90]) {
    const off = offsetMinutes(zone, guess - 12 * 3600000) + delta; // seed
    const t = guess - off * 60000;
    if (offsetMinutes(zone, t) * 60000 + t === guess) return t;
  }
  return guess - offsetMinutes(zone, guess) * 60000;
}
function utcToLocal(zone, ms) {
  const o = offsetMinutes(zone, ms);
  const d = new Date(ms + o * 60000);
  return { date: `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`, min: d.getUTCHours() * 60 + d.getUTCMinutes() };
}

// Petra's weekly template, clinic-local (verified against the staff API in beforeAll)
let TEMPLATE = {}; // dayIndex -> [[startMin,endMin]]
let staff;
test.beforeAll(async () => {
  staff = await request.newContext({
    baseURL: 'https://sunrise-family-medical.dev.clinic1.ai',
    storageState: path.join(__dirname, '../../playwright/.auth/tz-user.json'),
    extraHTTPHeaders: { timezone: CLINIC_TZ },
  });
  const r = await (await staff.get(`/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=${LOC}&practitionerId=${PR}&startDate=2026-10-05&endDate=2026-10-11`)).json();
  for (const d of r.response[0].schedule.days) if (d.isActive) TEMPLATE[d.dayIndex] = d.slots.map(s => [toMin(s.startTime), toMin(s.endTime)]);
});
test.afterAll(async () => { await staff.dispose(); });

function expectedSlots(zone, viewerDate) {
  const [vy, vm, vd] = viewerDate.split('-').map(Number);
  const out = new Set();
  for (let k = -2; k <= 2; k++) {
    const base = Date.UTC(vy, vm - 1, vd) + k * DAY_MS;
    const cd = new Date(base);
    const wd = cd.getUTCDay();
    for (const [s, e] of TEMPLATE[wd] || []) for (let m = s; m + 30 <= e; m += 30) {
      const utc = localToUtc(CLINIC_TZ, cd.getUTCFullYear(), cd.getUTCMonth() + 1, cd.getUTCDate(), m);
      const loc = utcToLocal(zone, utc);
      if (loc.date === viewerDate) out.add(fmtT(loc.min));
    }
  }
  return [...out].sort();
}

async function portalSlots(tz, date) {
  const c = await request.newContext({ baseURL: 'https://dev.clinic1.ai', extraHTTPHeaders: tz === undefined ? {} : { timezone: tz } });
  const r = await c.get(`/api/v1/public/${CODE}/availability/optimized?${Q}&date=${date}`);
  const body = await r.text();
  await c.dispose();
  return { status: r.status(), body };
}
const parse = body => {
  const day = JSON.parse(body).response?.[0]?.availabilityDay;
  return Object.values(day?.slots || {}).flat().map(s => s.startTime).sort();
};

// pick zones: one per distinct (offset on each test date) signature, unless ALL_ZONES
function pickZones() {
  const all = allZones();
  if (process.env.ALL_ZONES) return all;
  const seen = new Map();
  for (const z of all) {
    const sig = DATES.map(d => offsetMinutes(z, Date.parse(d + 'T00:00:00Z')) + ':' + offsetMinutes(z, Date.parse(d + 'T23:59:00Z'))).join('|');
    if (!seen.has(sig)) seen.set(sig, z);
  }
  for (const must of ['Australia/Sydney', 'Australia/Brisbane', 'Australia/Perth', 'Australia/Adelaide', 'Australia/Lord_Howe', 'Asia/Calcutta', 'America/New_York', 'Pacific/Auckland', 'Pacific/Kiritimati', 'Etc/GMT+12', 'Asia/Kathmandu', 'Europe/London']) seen.set('must-' + must, must);
  return [...new Set(seen.values())];
}

test.describe('Portal slots in every viewer timezone (clinic = Australia/Sydney, 3-5 Oct 2026)', () => {
  test('template sanity: Petra works Mon/Tue 13-17, Wed/Fri/Sat/Sun 08-18, Thu 08-22 (clinic-local)', () => {
    expect(TEMPLATE[1]).toEqual([[780, 1020]]);
    expect(TEMPLATE[2]).toEqual([[780, 1020]]);
    expect(TEMPLATE[4]).toEqual([[480, 1320]]);
  });

  for (const zone of pickZones()) {
    test(`viewer ${zone}: slots equal clinic hours shifted by the real offset`, async () => {
      const problems = [];
      for (const d of DATES) {
        const r = await portalSlots(zone, d);
        if (r.status !== 200) { problems.push(`${d}: HTTP ${r.status} ${r.body.slice(0, 80)}`); continue; }
        const got = parse(r.body), exp = expectedSlots(zone, d);
        // past slots are dropped for "today" only; test dates are all in the future
        if (JSON.stringify(got) !== JSON.stringify(exp)) problems.push(`${d}: got ${got.length} [${got[0]}..${got.at(-1)}] expected ${exp.length} [${exp[0]}..${exp.at(-1)}]`);
      }
      expect(problems, problems.join('\n')).toEqual([]);
    });
  }
});

test.describe('Portal - header edge cases', () => {
  test('NEGATIVE: invalid timezone header -> 4xx, not 5xx', async () => {
    const r = await portalSlots('Not/AZone', '2026-10-05');
    expect(r.status, r.body.slice(0, 120)).toBeLessThan(500);
    expect(r.status).toBeGreaterThanOrEqual(400);
  });
  test('NEGATIVE: injection-like timezone header does not 5xx', async () => {
    const r = await portalSlots("Australia/Sydney'; DROP TABLE x;--", '2026-10-05');
    expect(r.status, r.body.slice(0, 120)).toBeLessThan(500);
  });
  test('EDGE: missing/empty timezone header falls back to clinic/Sydney view', async () => {
    const none = await portalSlots(undefined, '2026-10-06'), empty = await portalSlots('', '2026-10-06');
    expect(parse(none.body)).toEqual(expectedSlots('Australia/Sydney', '2026-10-06'));
    expect(parse(empty.body)).toEqual(parse(none.body));
  });
  test('NEGATIVE: invalid date param -> 4xx', async () => {
    for (const d of ['not-a-date', '2026-13-45', '2026-02-30', '']) {
      const r = await portalSlots('Australia/Sydney', d);
      expect(r.status, `date=${d} -> ${r.status} ${r.body.slice(0, 100)}`).toBeLessThan(500);
    }
  });
  test('EDGE: far-past and far-future dates do not 5xx', async () => {
    for (const d of ['1970-01-01', '2000-02-29', '2099-12-31']) {
      const r = await portalSlots('Australia/Sydney', d);
      expect(r.status, `${d} ${r.body.slice(0, 100)}`).toBeLessThan(500);
    }
  });
  test('POSITIVE: slot-counts totals agree with availability slot lists (Mon/Tue/Thu/Wed)', async () => {
    const c = await request.newContext({ baseURL: 'https://dev.clinic1.ai', extraHTTPHeaders: { timezone: CLINIC_TZ } });
    const sc = await (await c.get(`/api/v1/public/${CODE}/slot-counts?practitionerId=${PR}&locationId=${LOC}&slotDuration=30&startDate=2026-10-03&endDate=2026-10-09&practitionerServiceId=6ab1208888d0bf82a084adc2&appointmentTypeId=6ab1208888d0bf82a084adb2`)).json();
    await c.dispose();
    for (const day of sc.response.days) {
      const r = await portalSlots(CLINIC_TZ, day.date);
      expect(parse(r.body).length, day.date).toBe(day.total);
    }
  });
  test('FINDING: online-booking dropdown for Sydney Wellness location should list professions', async () => {
    const c = await request.newContext({ baseURL: 'https://dev.clinic1.ai' });
    const r = await (await c.get('/api/v1/specialization/location/6a38e30fbc4e13b74c75e28d?onlyWithPractitioners=true')).json();
    await c.dispose();
    expect(JSON.stringify(r.response).length, 'Sydney Wellness location has practitioners but no bookable professions').toBeGreaterThan(30);
  });
});

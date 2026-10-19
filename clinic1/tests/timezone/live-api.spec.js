// @ts-check
// Read-only live probes against dev. No data is created or modified.
const { test, expect, request } = require('@playwright/test');
const path = require('path');

const ORIGIN = 'https://sunrise-family-medical.dev.clinic1.ai';
const CID = '6a32753a139744ccb3181d73';
const SYD = '6a38e30fbc4e13b74c75e28d'; // Sydney Wellness Clinic (Australia/Sydney)
const KOL = '6a44c85eb901372ebc26501e'; // Harbour Health Clinic (Asia/Kolkata)
const BNE = '6ab118ed88d0bf82a08492fd'; // "BRISBANE HEALTH CLINIC"
const PRAC = '6a474c2e5edb09ec7cc111a7'; // Arlie Reid
const auth = path.join(__dirname, '../../playwright/.auth/tz-user.json');

let api, anon;
test.beforeAll(async () => {
  api = await request.newContext({ baseURL: ORIGIN, storageState: auth });
  anon = await request.newContext({ baseURL: ORIGIN });
});
test.afterAll(async () => { await api.dispose(); await anon.dispose(); });

const hours = d => (d?.days || []).filter(x => x.isActive).map(x => `${x.day.slice(0, 3)} ${x.slots.map(s => s.startTime + '-' + s.endTime).join('+')}`).join('; ');
const cal = (loc, prac, s, e) => api.get(`/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=${loc}&practitionerId=${prac}&startDate=${s}&endDate=${e}`);

test.describe('Locations - timezone data', () => {
  let locs;
  test.beforeAll(async () => { locs = (await (await api.get(`/api/v1/clinic/location?clinicId=${CID}&page=1&limit=50`)).json()).response.clinicLocations; });

  test('POSITIVE: every location has a valid IANA timezone', () => {
    for (const l of locs) expect(() => new Intl.DateTimeFormat('en-US', { timeZone: l.timezone }), l.name).not.toThrow();
  });
  test('POSITIVE: timezone === scheduleTimezone on every location', () => {
    for (const l of locs) expect(l.scheduleTimezone, l.name).toBe(l.timezone);
  });
  test('FINDING: location named "BRISBANE" must not be on a DST zone', () => {
    const b = locs.find(l => /brisbane/i.test(l.name));
    expect(b, 'no Brisbane location').toBeTruthy();
    expect(b.timezone, 'Brisbane clinic is configured with a DST timezone').toBe('Australia/Brisbane');
  });
  test('FINDING: practitioner hours should sit inside the clinic hours band', async () => {
    const bad = [];
    for (const l of locs) {
      const clinicDays = l.scheduleDetails?.days || [];
      const pr = (await (await api.get(`/api/v1/practitioner/web?clinicId=${CID}&locationId=${l._id}&page=1&limit=20`)).json()).response.practitioners || [];
      // the API converts to the viewer's timezone (header); view each location in its own zone
      const view = await request.newContext({ baseURL: ORIGIN, storageState: auth, extraHTTPHeaders: { timezone: l.timezone } });
      for (const p of pr.slice(0, 2)) {
        const r = await (await view.get(`/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=${l._id}&practitionerId=${p.userId || p._id}&startDate=2026-10-05&endDate=2026-10-11`)).json();
        const sch = r.response?.[0]?.schedule;
        for (const d of sch?.days || []) {
          const c = clinicDays.find(x => x.dayIndex === d.dayIndex);
          if (!d.isActive || !c?.isActive) continue;
          const toM = t => +t.slice(0, 2) * 60 + +t.slice(3);
          const cs = Math.min(...c.slots.map(s => toM(s.startTime))), ce = Math.max(...c.slots.map(s => toM(s.endTime)));
          for (const s of d.slots) if (toM(s.startTime) < cs || toM(s.endTime) > ce) bad.push(`${l.name} ${d.day} practitioner ${s.startTime}-${s.endTime} vs clinic ${hours({ days: [c] })}`);
        }
      }
      await view.dispose();
    }
    expect(bad, bad.slice(0, 8).join('\n')).toEqual([]);
  });
});

test.describe('Schedule hours across the DST boundary (re-run after 4 Oct 2026)', () => {
  for (const [name, loc] of [['Sydney Wellness (DST)', SYD], ['Harbour Health (Kolkata control)', KOL], ['BRISBANE HEALTH CLINIC', BNE]]) {
    test(`POSITIVE: ${name} - Sep and Oct weeks give identical hours`, async () => {
      const pr = (await (await api.get(`/api/v1/practitioner/web?clinicId=${CID}&locationId=${loc}&page=1&limit=20`)).json()).response.practitioners || [];
      test.skip(!pr.length, 'no practitioners');
      for (const p of pr.slice(0, 3)) {
        const id = p.userId || p._id;
        const sep = await (await cal(loc, id, '2026-09-28', '2026-10-02')).json();
        const oct = await (await cal(loc, id, '2026-10-05', '2026-10-09')).json();
        expect(hours(oct.response?.[0]?.schedule), `${p.firstName} ${p.lastName}`).toBe(hours(sep.response?.[0]?.schedule));
      }
    });
  }
  test('POSITIVE: calendar view is stable when the same range is requested twice', async () => {
    const a = await (await cal(SYD, PRAC, '2026-10-01', '2026-10-31')).text();
    const b = await (await cal(SYD, PRAC, '2026-10-01', '2026-10-31')).text();
    expect(a).toBe(b);
  });
  test('POSITIVE: range spanning the 4 Oct transition returns a valid view', async () => {
    const r = await cal(KOL, PRAC, '2026-10-03', '2026-10-05');
    expect(r.status()).toBe(200);
  });
});

test.describe('NEGATIVE / EDGE - schedule API robustness', () => {
  const bad = (name, url, okStatuses) => test(name, async () => {
    const r = await api.get(url);
    expect(r.status(), `${url} -> ${r.status()} ${(await r.text()).slice(0, 150)}`).not.toBeGreaterThanOrEqual(500);
    if (okStatuses) expect(okStatuses).toContain(r.status());
  });
  const base = `/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=${KOL}&practitionerId=${PRAC}`;
  bad('end before start', `${base}&startDate=2026-10-31&endDate=2026-10-01`, [200, 400]);
  bad('invalid date string', `${base}&startDate=not-a-date&endDate=2026-10-01`, [400, 422]);
  bad('missing dates', base, [200, 400]);
  bad('impossible date 2026-02-30', `${base}&startDate=2026-02-30&endDate=2026-03-01`, [400, 422]);
  bad('nonexistent DST-gap time not accepted as date-only', `${base}&startDate=2026-10-04T02:30:00&endDate=2026-10-04T02:45:00`, [200, 400]);
  bad('far-future range 2055', `${base}&startDate=2055-01-01&endDate=2055-01-31`, [200]);
  bad('1900 range', `${base}&startDate=1900-01-01&endDate=1900-01-31`, [200, 400]);
  bad('year-long range', `${base}&startDate=2026-01-01&endDate=2026-12-31`, [200, 400]);
  bad('malformed practitionerId', `/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=${KOL}&practitionerId=xyz&startDate=2026-10-01&endDate=2026-10-02`, [400, 404, 422]);
  bad('malformed locationId', `/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=xyz&practitionerId=${PRAC}&startDate=2026-10-01&endDate=2026-10-02`, [400, 404, 422]);
  bad('SQL/NoSQL-ish injection in id', `/api/v1/schedule-override/calendar?clinicId=${CID}&locationId[$ne]=1&practitionerId=${PRAC}&startDate=2026-10-01&endDate=2026-10-02`, [400, 404, 422]);
  bad('practitioner from a different location', `/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=${SYD}&practitionerId=${PRAC}&startDate=2026-10-01&endDate=2026-10-02`);
  bad('smart-slot invalid period', `/api/v1/report/smart-slot?clinicId=${CID}&period=bogus&startDate=2026-09-28&endDate=2026-10-04`, [400, 422]);
  bad('smart-slot end before start', `/api/v1/report/smart-slot?clinicId=${CID}&period=weekly&startDate=2026-10-04&endDate=2026-09-28`, [200, 400]);
  bad('appointment scheduler missing params', `/api/v1/appointment/scheduler?page=1&limit=10`, [400, 422]);
  bad('appointment scheduler limit=0', `/api/v1/appointment/scheduler?page=1&limit=0&clinicId=${CID}&locationId=${KOL}`, [200, 400]);
  bad('appointment scheduler negative page', `/api/v1/appointment/scheduler?page=-1&limit=10&clinicId=${CID}&locationId=${KOL}`, [200, 400]);

  test('SECURITY: unauthenticated request to schedule data is rejected', async () => {
    const r = await anon.get(`/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=${KOL}&practitionerId=${PRAC}&startDate=2026-10-01&endDate=2026-10-02`);
    expect([401, 403]).toContain(r.status());
  });
  test('SECURITY: unauthenticated location list is rejected', async () => {
    const r = await anon.get(`/api/v1/clinic/location?clinicId=${CID}&page=1&limit=10`);
    expect([401, 403]).toContain(r.status());
  });
  test('NEGATIVE: bogus clinicId must not return foreign-tenant data (server ignores it today; should 400)', async () => {
    const r = await api.get(`/api/v1/clinic/location?clinicId=000000000000000000000000&page=1&limit=10`);
    expect([200, 400, 401, 403, 404]).toContain(r.status());
    if (r.status() === 200) for (const l of (await r.json()).response.clinicLocations || []) expect(l.clinicId, 'location from another tenant leaked').toBe(CID);
  });
});

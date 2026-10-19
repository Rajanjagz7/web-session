// Usage:  node tests/timezone/snapshot.mjs save      -> writes test-results/dst-baseline.json (run BEFORE 4 Oct)
//         node tests/timezone/snapshot.mjs compare   -> re-reads everything and diffs against the baseline (run AFTER 4 Oct)
// Everything compared is date-pinned (fixed calendar dates), so a change after the DST boundary is a real regression.
import { request } from '@playwright/test';
import fs from 'fs';

const MODE = process.argv[2] || 'save';
const FILE = 'test-results/dst-baseline.json';
const O = 'https://sunrise-family-medical.dev.clinic1.ai';
const CID = '6a32753a139744ccb3181d73';
const CODE = 'sCYjCtj7'; // generic booking link
const hrs = d => (d?.days || []).filter(x => x.isActive).map(x => x.day.slice(0, 3) + ' ' + x.slots.map(s => s.startTime + '-' + s.endTime).join('+')).join('; ');
const staff = tz => request.newContext({ baseURL: O, storageState: 'playwright/.auth/tz-user.json', extraHTTPHeaders: { timezone: tz } });
const pub = tz => request.newContext({ baseURL: 'https://dev.clinic1.ai', extraHTTPHeaders: { timezone: tz } });
const dates = n => Array.from({ length: n }, (_, i) => new Date(Date.UTC(2026, 9, 3 + i)).toISOString().slice(0, 10)); // 3 Oct ..

async function collect() {
  const snap = { takenAt: new Date().toISOString(), locations: {}, portal: {}, appointments: {} };
  const base = await staff('Australia/Sydney');
  const locs = (await (await base.get(`/api/v1/clinic/location?clinicId=${CID}&page=1&limit=50`)).json()).response.clinicLocations;
  for (const l of locs) {
    const entry = { name: l.name, timezone: l.timezone, clinicHours: hrs(l.scheduleDetails), practitioners: {} };
    snap.locations[l._id] = entry;
    const view = await staff(l.timezone);
    const pr = (await (await view.get(`/api/v1/practitioner/web?clinicId=${CID}&locationId=${l._id}&page=1&limit=20`)).json()).response.practitioners || [];
    for (const p of pr) {
      const id = p.userId || p._id;
      const out = {};
      for (const [k, s, e] of [['sep28wk', '2026-09-28', '2026-10-02'], ['oct05wk', '2026-10-05', '2026-10-09'], ['nov02wk', '2026-11-02', '2026-11-06']]) {
        const r = await (await view.get(`/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=${l._id}&practitionerId=${id}&startDate=${s}&endDate=${e}`)).json();
        out[k] = hrs(r.response?.[0]?.schedule) || 'none';
      }
      entry.practitioners[`${p.firstName || ''} ${p.lastName || ''}`.trim() + ' ' + id] = out;
    }
    const ap = await (await view.get(`/api/v1/appointment/scheduler?page=1&limit=200&clinicId=${CID}&locationId=${l._id}&startDate=2026-10-05&endDate=2026-11-15`)).json();
    snap.appointments[l.name] = (ap.response?.groupedByPractitioner || []).flatMap(g => (g.appointments || []).map(a => `${g.practitioner.name} ${a.startDateTime}-${a.endDateTime}`)).sort();
    await view.dispose();
  }
  // portal slot lists for BRISBANE/Petra in three viewer zones
  const Q = 'practitionerId=6ab119b788d0bf82a0849810&clinicId=' + CID + '&locationId=6ab118ed88d0bf82a08492fd&slotDuration=30&appointmentTypeId=6ab1208888d0bf82a084adb2&consultationTypeId=6ab1208888d0bf82a084adb1&practitionerServiceId=6ab1208888d0bf82a084adc2';
  for (const tz of ['Australia/Sydney', 'Australia/Brisbane', 'Asia/Calcutta']) {
    const c = await pub(tz);
    snap.portal[tz] = {};
    for (const d of dates(10)) {
      const j = await (await c.get(`/api/v1/public/${CODE}/availability/optimized?${Q}&date=${d}`)).json();
      const all = Object.values(j.response?.[0]?.availabilityDay?.slots || {}).flat();
      snap.portal[tz][d] = all.length ? `${all[0].startTime}..${all.at(-1).startTime} (${all.length})` : 'none';
    }
    await c.dispose();
  }
  await base.dispose();
  return snap;
}

function flatten(o, p = '', out = {}) {
  for (const [k, v] of Object.entries(o)) {
    if (k === 'takenAt') continue;
    if (v && typeof v === 'object' && !Array.isArray(v)) flatten(v, p + k + '/', out);
    else out[p + k] = Array.isArray(v) ? v.join(' ; ') : v;
  }
  return out;
}

const snap = await collect();
if (MODE === 'save') {
  fs.writeFileSync(FILE, JSON.stringify(snap, null, 1));
  console.log('Saved', FILE, 'at', snap.takenAt, '|', Object.keys(flatten(snap)).length, 'data points');
} else {
  const old = JSON.parse(fs.readFileSync(FILE, 'utf8'));
  const a = flatten(old), b = flatten(snap);
  const diffs = Object.keys({ ...a, ...b }).filter(k => a[k] !== b[k]);
  console.log(`Baseline ${old.takenAt}  vs  now ${snap.takenAt}: ${diffs.length} differences out of ${Object.keys(a).length}`);
  for (const k of diffs.slice(0, 60)) console.log(' -', k, '\n     was:', String(a[k]).slice(0, 160), '\n     now:', String(b[k]).slice(0, 160));
  process.exitCode = diffs.length ? 1 : 0;
}

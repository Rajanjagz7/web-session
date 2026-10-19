import { request } from '@playwright/test';
const CID='6a32753a139744ccb3181d73', LOC='6ab118ed88d0bf82a08492fd', PR='6ab119b788d0bf82a0849810', CODE='sCYjCtj7';
const anon = await request.newContext({ baseURL:'https://dev.clinic1.ai' });
const staff = await request.newContext({ baseURL:'https://sunrise-family-medical.dev.clinic1.ai', storageState:'playwright/.auth/tz-user.json' });
const q=`practitionerId=${PR}&clinicId=${CID}&locationId=${LOC}&slotDuration=30&appointmentTypeId=6ab1208888d0bf82a084adb2&consultationTypeId=6ab1208888d0bf82a084adb1&practitionerServiceId=6ab1208888d0bf82a084adc2`;
for (const date of ['2026-10-05','2026-10-06','2026-10-07','2026-10-08']) {
  const j=await (await anon.get(`/api/v1/public/${CODE}/availability/optimized?${q}&date=${date}`)).json();
  const day=j.response?.[0]?.availabilityDay; const s=day?.slots||{};
  const all=Object.values(s).flat();
  const fmt=a=>a.map(x=>x.startTime+(x.booked?'*':'')).join(' ');
  console.log(date, day?.day, 'slots:',all.length, all.length?`${all[0].startTime}..${all.at(-1).endTime}`:'', '\n   ', fmt(all));
}
const sc=await (await staff.get(`/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=${LOC}&practitionerId=${PR}&startDate=2026-10-05&endDate=2026-10-11`)).json();
console.log('STAFF schedule for Petra:', JSON.stringify(sc.response?.[0]?.schedule?.days?.map(d=>d.day.slice(0,3)+' '+d.slots.map(s=>s.startTime+'-'+s.endTime))), 'overrides', JSON.stringify(sc.response?.[0]?.overrides).slice(0,300));
const ap=await (await staff.get(`/api/v1/appointment/scheduler?page=1&limit=50&clinicId=${CID}&locationId=${LOC}&startDate=2026-10-05&endDate=2026-10-08`)).json();
const str=JSON.stringify(ap).slice(0,1800); console.log(str);

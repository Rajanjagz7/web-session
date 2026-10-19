import { request } from '@playwright/test';
import h from './helpers.js';
const { offsetMinutes } = h;
const CID='6a32753a139744ccb3181d73', LOC='6ab118ed88d0bf82a08492fd', PR='6ab119b788d0bf82a0849810', CODE='sCYjCtj7';
const q=`practitionerId=${PR}&clinicId=${CID}&locationId=${LOC}&slotDuration=30&appointmentTypeId=6ab1208888d0bf82a084adb2&consultationTypeId=6ab1208888d0bf82a084adb1&practitionerServiceId=6ab1208888d0bf82a084adc2`;
const toMin=t=>+t.slice(0,2)*60+ +t.slice(3);
async function slots(tz,date){
  const c=await request.newContext({baseURL:'https://dev.clinic1.ai',extraHTTPHeaders:tz?{timezone:tz}:{}});
  const r=await c.get(`/api/v1/public/${CODE}/availability/optimized?${q}&date=${date}`); const t=await r.text(); await c.dispose();
  if(!r.ok()) return {err:r.status()+' '+t.slice(0,100)};
  const day=JSON.parse(t).response?.[0]?.availabilityDay; const all=Object.values(day?.slots||{}).flat();
  return {first:all[0]?.startTime,last:all.at(-1)?.startTime,n:all.length,day:day?.day};
}
for (const tz of [undefined,'Australia/Sydney','Australia/Brisbane','Asia/Calcutta','America/New_York','Pacific/Auckland','Europe/London','Asia/Kathmandu','Pacific/Kiritimati','Etc/GMT+12','Not/AZone','']) {
  const out=[];
  for (const d of ['2026-10-03','2026-10-06']) out.push(d+' '+JSON.stringify(await slots(tz,d)));
  console.log((tz===undefined?'(none)':JSON.stringify(tz)).padEnd(22), out.join('  |  '));
}

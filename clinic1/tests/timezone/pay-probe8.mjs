import { api, IDS } from './seed-lib.mjs';
const c = await api();
const r = await (await c.get(`/api/v1/appointment/scheduler?page=1&limit=100&clinicId=${IDS.clinicId}&locationId=${IDS.locationId}&startDate=2026-01-01&endDate=2026-01-31`)).json();
const g = r.response.groupedByPractitioner.find(x=>x.practitioner._id===IDS.practitionerId);
console.log('Jan appts via scheduler:', g?.appointments?.length, JSON.stringify(g?.appointments?.[0]).slice(0,700));
const l = await (await c.get(`/api/v1/appointment?page=1&limit=5&clinicId=${IDS.clinicId}&locationId=${IDS.locationId}&type=past`)).text();
console.log('list endpoint probe', l.slice(0,300));

import { api, IDS } from './seed-lib.mjs';
const c = await api();
for (const [label, q] of [['ALL LOCATIONS',''],['BRISBANE',`&locationId=${IDS.locationId}`]]) {
  const j = await (await c.get(`/api/v1/clinic/dashboard?clinicId=${IDS.clinicId}&period=yearly${q}`)).json();
  const m = j.response.metrics; console.log('\n'+label);
  for (const k of Object.keys(m)) console.log(' ',k.padEnd(18), String(Math.round(m[k].total)).padStart(6),'|',m[k].breakdown.map(b=>Math.round(b.value)).join(' '));
}

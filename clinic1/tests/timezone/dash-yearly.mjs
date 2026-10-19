import { api } from './seed-lib.mjs';
const c = await api();
const j = await (await c.get('/api/v1/clinic/dashboard?clinicId=6a32753a139744ccb3181d73&period=yearly')).json();
const m = j.response.metrics;
console.log('metrics keys:', Object.keys(m));
for (const k of Object.keys(m)) console.log(k.padEnd(20), m[k].total, '|', (m[k].breakdown||[]).map(b=>b.value).join(' '));
console.log('other keys:', Object.keys(j.response).filter(k=>k!=='metrics'));

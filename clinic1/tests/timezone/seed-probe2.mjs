import { api } from './seed-lib.mjs';
const c = await api();
const r = await (await c.get('/api/v1/patient/get?page=1&limit=100&clinicId=6a32753a139744ccb3181d73&archived=active&practitionerId=6a32753a139744ccb3181d71')).json();
console.log(JSON.stringify(r).slice(0,300)); const list = r.response.patients || r.response.docs || r.response.data || [];
console.log('keys', Object.keys(r.response), 'count', list.length, 'pagination', JSON.stringify(r.response.pagination));
console.log(JSON.stringify(list[0]).slice(0,900));

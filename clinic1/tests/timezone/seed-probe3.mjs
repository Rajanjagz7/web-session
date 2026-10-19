import { api } from './seed-lib.mjs';
const c = await api(); let all=[];
for (let p=1;p<=3;p++){ const r=await (await c.get(`/api/v1/patient/get?page=${p}&limit=100&clinicId=6a32753a139744ccb3181d73&archived=active&practitionerId=6a32753a139744ccb3181d71`)).json(); all.push(...(r.response.patients||[])); }
console.log('total',all.length,'zero-appt',all.filter(x=>!x.totalAppointments).length,'created-field',Object.keys(all[0]).filter(k=>/creat|date|since/i.test(k)));
const real = all.filter(x=>/yopmail/.test(x.email||''));
console.log('yopmail patients',real.length);
console.log(all.filter(x=>!x.totalAppointments).slice(0,40).map(x=>x.name+' '+x._id).join('\n'));
import('fs').then(fs=>fs.writeFileSync('test-results/patients.json',JSON.stringify(all.map(x=>({id:x._id,name:x.name,email:x.email,n:x.totalAppointments})))));

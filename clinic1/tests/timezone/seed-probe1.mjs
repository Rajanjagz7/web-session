import { api, apptBody } from './seed-lib.mjs';
const c = await api();
const pat = '6aa916471dd34d651ee4348b';
for (const [s,e,custom] of [['2026-01-12T10:00','2026-01-12T10:30',false],['2026-01-12T10:00','2026-01-12T10:30',true]]) {
  const r = await c.post('/api/v1/appointment',{ data: apptBody(pat,s,e,custom) });
  console.log('custom='+custom, r.status(), (await r.text()).slice(0,400));
}

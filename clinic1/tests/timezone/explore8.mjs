import { request } from '@playwright/test';
const o='https://sunrise-family-medical.dev.clinic1.ai';
const ctx = await request.newContext({ storageState:'playwright/.auth/tz-user.json', baseURL:o });
const r=await ctx.get('/api/v1/online-booking/links/list?page=1&limit=50&sortBy=name&sortOrder=desc&clinicId=6a32753a139744ccb3181d73');
const j=await r.json(); console.log(JSON.stringify(j).slice(0,3500));

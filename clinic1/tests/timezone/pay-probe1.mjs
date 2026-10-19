import { api } from './seed-lib.mjs';
const c = await api();
const inv = await (await c.get('/api/v1/invoice?page=1&limit=3&sortBy=date&sortOrder=desc&clinicId=6a32753a139744ccb3181d73&includePayments=true')).json();
console.log(JSON.stringify(inv.response.invoices?.[0]||inv.response).slice(0,1800));
const pay = await (await c.get('/api/v1/payment?page=1&limit=2&sortBy=createdAt&sortOrder=desc&clinic=6a32753a139744ccb3181d73')).json();
console.log('\nPAYMENT', JSON.stringify(pay.response).slice(0,1200));

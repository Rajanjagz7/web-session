const { EMAIL, PASSWORD } = require('./config');

async function loginApi(request) {
  const res = await request.post('/api/v1/auth/admin/login', { data: { email: EMAIL, password: PASSWORD } });
  if (!res.ok()) throw new Error(`Admin API login failed: ${res.status()} ${await res.text()}`);
  return res;
}

async function json(res) {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

module.exports = { loginApi, json };

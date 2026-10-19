import { APIRequestContext } from '@playwright/test';

const EMAIL = process.env.NSW_LOGIN_EMAIL!;
const PASSWORD = process.env.NSW_LOGIN_PASSWORD!;

/**
 * Logs in via the real admin-login API call. Playwright's APIRequestContext
 * persists the Set-Cookie response (httpOnly access/refresh tokens) across
 * subsequent calls made with the same `request` fixture, so every later
 * call in the test is authenticated automatically.
 */
export async function loginApi(request: APIRequestContext) {
  const res = await request.post('/api/v1/auth/admin/login', {
    data: { email: EMAIL, password: PASSWORD },
  });
  if (!res.ok()) {
    throw new Error(`Admin API login failed: ${res.status()} ${await res.text()}`);
  }
  return res;
}

export async function json(res: import('@playwright/test').APIResponse) {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

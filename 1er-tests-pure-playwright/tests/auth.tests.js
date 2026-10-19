const { describe, test, expect, expectVisible, expectNotVisible } = require('../runner');
const { EMAIL, PASSWORD } = require('../config');
const { loginApi, json } = require('../api-helpers');

describe('Admin login - API', () => {
  test('valid credentials succeed', async ({ request }) => {
    const res = await loginApi(request);
    expect(res.status()).toBe(200);
  });

  test('wrong password is rejected with a generic message', async ({ request }) => {
    const res = await request.post('/api/v1/auth/admin/login', {
      data: { email: EMAIL, password: 'definitely-wrong-password' },
    });
    expect(res.status()).toBe(401);
    const body = await json(res);
    expect(body.message).toBe('Invalid email or password');
  });

  test('nonexistent email returns the SAME generic message as wrong password (anti-enumeration)', async ({ request }) => {
    const res = await request.post('/api/v1/auth/admin/login', {
      data: { email: 'does-not-exist-12345@rebatem8nsw.com.au', password: 'anything' },
    });
    expect(res.status()).toBe(401);
    const body = await json(res);
    expect(body.message).toBe('Invalid email or password');
  });
});

describe('Admin login - UI', () => {
  test('wrong password shows the generic error and does not log in', async ({ page }) => {
    await page.goto('/log-in');
    await page.getByPlaceholder(/email/i).fill(EMAIL);
    await page.getByPlaceholder(/password/i).fill('definitely-wrong-password');
    await page.getByRole('button', { name: /log ?in|sign ?in/i }).click();
    await expectVisible(page.getByText('Invalid email or password', { exact: false }).first());
    await expectNotVisible(page.getByRole('button', { name: /add job/i }));
  });

  test('valid credentials reach the Jobs screen', async ({ page }) => {
    await page.goto('/log-in');
    await page.getByPlaceholder(/email/i).fill(EMAIL);
    await page.getByPlaceholder(/password/i).fill(PASSWORD);
    await page.getByRole('button', { name: /log ?in|sign ?in/i }).click();
    await expectVisible(page.getByRole('button', { name: /add job/i }), 15000);
  });
});

describe('OTP request/verify - API (public, no login required)', () => {
  // Deliberately uses a fake/nonexistent number, never a real registered
  // one - hitting a real number repeatedly on every run would spam an
  // actual person's phone with OTP SMS messages.
  const FAKE_PHONE = '0400000999';

  test('request for a nonexistent phone returns a generic anti-enumeration message', async ({ request }) => {
    const res = await request.post('/api/v1/auth/otp/request', {
      data: { phoneNumber: FAKE_PHONE, countryCode: '+61' },
    });
    expect(res.status()).toBe(200);
    const body = await json(res);
    expect(body.message).toBe('If an account exists, a verification code has been sent.');
  });

  test('verify with an obviously wrong code is rejected', async ({ request }) => {
    const res = await request.post('/api/v1/auth/otp/verify', {
      data: { phoneNumber: FAKE_PHONE, countryCode: '+61', code: '000000' },
    });
    expect(res.status()).toBe(401);
    const body = await json(res);
    expect(body.message).toBe('Invalid code');
  });

  // BUG-04 (Critical, see QA report): requesting an OTP for a REAL
  // registered phone number currently returns 500 on the first attempt.
  // Not automated here on purpose - re-running against a real number on
  // every run would repeatedly SMS an actual person. Verify manually.
});

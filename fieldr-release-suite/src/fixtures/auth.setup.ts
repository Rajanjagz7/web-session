import { test as setup } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { env, PERSONAS, personaCreds } from '../config/env';
import { LoginPage } from '../pages/LoginPage';

const AUTH_DIR = path.resolve(__dirname, '..', '..', '.auth');

export const statePath = (persona: string): string => path.join(AUTH_DIR, `${persona}.json`);

setup.describe.configure({ mode: 'serial' });

for (const persona of PERSONAS) {
  setup(`authenticate ${persona}`, async ({ page }) => {
    fs.mkdirSync(AUTH_DIR, { recursive: true });
    const creds = personaCreds[persona];
    if (!creds.mobile || !creds.otp) {
      // No credentials: write an empty state so the persona project still loads; its tests will fail visibly at login.
      fs.writeFileSync(statePath(persona), JSON.stringify({ cookies: [], origins: [] }));
      setup.info().annotations.push({ type: 'warning', description: `${persona}: no credentials in .env, empty storage state written` });
      return;
    }
    const login = new LoginPage(page);
    await login.openLogin(creds.portal ? env.portalUrl : env.baseUrl);
    await login.signInWithMobileAndOtp(creds.mobile, creds.otp);
    await login.expectSignedIn();
    await page.context().storageState({ path: statePath(persona) });
  });
}

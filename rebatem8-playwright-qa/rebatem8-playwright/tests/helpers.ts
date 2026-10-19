import {test as base, expect, Page, BrowserContext} from '@playwright/test';
export const LOGIN_API = '**/api/v1/auth/admin/login';
export function credentials() {
  const email = process.env.E2E_EMAIL, password = process.env.E2E_PASSWORD;
  if (!email || !password) throw new Error('Set E2E_EMAIL and E2E_PASSWORD in your shell or CI secrets.');
  return {email, password};
}
export class LoginPage {
  constructor(readonly page: Page) {}
  get email() { return this.page.locator('input[name="email"]'); }
  get password() { return this.page.locator('input[name="password"]'); }
  get submit() { return this.page.getByRole('button', {name: 'Log In', exact: true}); }
  async open() { await this.page.goto('/log-in'); await expect(this.email).toBeVisible(); }
  async fill(email: string, password: string) { await this.email.fill(email); await this.password.fill(password); }
  async login() {
    const c = credentials(); await this.open(); await this.fill(c.email, c.password);
    await this.submit.click(); await expect(this.page).toHaveURL(/\/jobs$/);
    await expect(this.page.getByRole('heading', {name: 'All Jobs', exact: true})).toBeVisible();
  }
}
export async function protectBusinessData(context: BrowserContext) {
  await context.route('**/api/**', async route => {
    const r = route.request(); const path = new URL(r.url()).pathname;
    if (['GET','HEAD','OPTIONS'].includes(r.method()) || /^\/api\/v1\/auth\/(admin\/login|logout)$/.test(path)) return route.continue();
    throw new Error(`Safety guard blocked a mutating request: ${r.method()} ${path}`);
  });
}
export const authTest = base.extend({
  storageState: '.auth/session.json',
  context: async ({context}, use) => { await protectBusinessData(context); await use(context); },
});
export {base as test, expect};

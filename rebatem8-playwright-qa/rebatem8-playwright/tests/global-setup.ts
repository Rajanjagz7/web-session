import {chromium} from '@playwright/test';
import {mkdir, writeFile} from 'node:fs/promises';
import {LoginPage, protectBusinessData} from './helpers';
export default async function setup() {
  if (!process.env.E2E_EMAIL || !process.env.E2E_PASSWORD) return;
  const browser = await chromium.launch();
  try {
    const context = await browser.newContext({baseURL: process.env.BASE_URL || 'https://nswdev.rebatem8.com.au'});
    await protectBusinessData(context);
    await new LoginPage(await context.newPage()).login();
    await mkdir('.auth', {recursive: true, mode: 0o700});
    await writeFile('.auth/session.json', JSON.stringify(await context.storageState()), {mode: 0o600});
  } finally { await browser.close(); }
}

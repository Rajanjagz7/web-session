// @ts-check
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

test.describe('Clinic1 - Sign In and Session Save', () => {

  test('Sign in, wait for dashboard and save storage state', async ({ page }) => {
    const signInUrl = process.env.SIGN_IN_URL || 'https://dev.clinic1.ai/auth/sign-in';
    const email = process.env.TEST_USER_EMAIL || 'abc@yopmail.com';
    const password = process.env.TEST_USER_PASSWORD || 'Test@123';

    console.log(`Navigating to ${signInUrl}...`);
    await page.goto(signInUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForLoadState('networkidle').catch(() => {});

    // Fill credentials
    const emailField = page.locator('input[type="email"], input[name="email"], input[id*="email"], input[placeholder*="email" i]').first();
    const passwordField = page.locator('input[type="password"], input[name="password"], input[id*="password"]').first();
    const submitBtn = page.locator('button[type="submit"], button:has-text("Sign In"), button:has-text("Log in"), button:has-text("Login")').first();

    await emailField.fill(email);
    await passwordField.fill(password);
    await submitBtn.click();
    console.log('Submitted login credentials');

    // Wait for redirect to clinic subdomain
    await page.waitForURL(url => !url.pathname.includes('/auth/sign-in'), { timeout: 30000 });
    console.log(`Redirected to: ${page.url()}`);

    // Wait for page to finish loading content (e.g. sidebar, header, or table)
    await page.waitForTimeout(5000);
    await page.waitForLoadState('networkidle').catch(() => {});

    // Ensure auth folder exists
    const authDir = path.join(__dirname, '../../playwright/.auth');
    if (!fs.existsSync(authDir)) {
      fs.mkdirSync(authDir, { recursive: true });
    }

    // Save storage state for all future tests
    await page.context().storageState({ path: path.join(authDir, 'user.json') });
    console.log('Saved storageState to playwright/.auth/user.json');

    // Take screenshot of the loaded dashboard
    await page.screenshot({ path: 'test-results/dashboard-loaded.png', fullPage: true });

    // Print page title and main navigation links
    const title = await page.title();
    console.log(`Dashboard Title: "${title}"`);

    const navLinks = await page.locator('nav a, aside a, header a, [role="navigation"] a').allInnerTexts().catch(() => []);
    console.log('Detected Navigation Links:', navLinks.map(s => s.trim()).filter(Boolean).slice(0, 15));
  });

});

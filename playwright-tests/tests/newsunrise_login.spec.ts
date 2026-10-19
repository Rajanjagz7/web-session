import { test, expect } from '@playwright/test';

test.describe('New Sunrise Login Scenarios', () => {

  test('Login - Negative then Positive scenario', async ({ page }) => {
    // Navigate to the sign-in page
    await page.goto('https://newsunrisedev.softwareco.com/sign-in');
    
    // ==========================================
    // 1. Negative Scenario: Invalid Credentials
    // ==========================================
    
    // Fill email
    const emailInput = page.locator('input[type="email"], input[name="email"], input[name="username"]');
    await emailInput.waitFor({ state: 'visible' });
    await emailInput.fill('rajanj+superadmin@softwareco.com');
    
    // Fill incorrect password
    const passwordInput = page.locator('input[type="password"], input[name="password"]');
    await passwordInput.fill('Invalid@123');
    
    // Click submit
    const submitButton = page.getByRole('button').filter({ hasText: /sign in|login|submit|continue/i });
    await submitButton.click();

    // Verify failure to login (we should stay on the sign-in page and possibly see an error)
    await page.waitForTimeout(2000);
    expect(page.url()).toContain('sign-in');

    // ==========================================
    // 2. Positive Scenario: Valid Credentials
    // ==========================================
    
    // Clear and fill the correct password
    await passwordInput.fill('Rajan@123');
    
    // Click submit again
    await submitButton.click();
    
    // Wait for the OTP step
    await page.waitForTimeout(2000);
    
    // Look for OTP input and fill the bypass code
    const otpInput = page.locator('input[name="otp"], input[name="code"], input[placeholder*="OTP" i], input[type="text"]').first();
    if (await otpInput.isVisible()) {
        await otpInput.fill('149526');
        
        // Wait for verify button or auto-submit
        const verifyBtn = page.getByRole('button').filter({ hasText: /verify|submit|confirm|continue/i });
        if (await verifyBtn.isVisible()) {
            await verifyBtn.click();
        }
    }
    
    // Verify successful login
    await page.waitForTimeout(4000);
    expect(page.url()).not.toContain('sign-in');
  });

});

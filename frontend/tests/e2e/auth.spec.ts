import { test, expect } from '@playwright/test';

/**
 * Authentication Flow Tests
 * 
 * These tests verify the complete auth flow that was broken in BUG-005:
 * - User registration
 * - Logout
 * - Login with same credentials
 * - Token persistence
 * - Dashboard redirect
 */

import { generateTestUser, getWeakPassword, getValidPassword1, getValidPassword2, getInvalidPassword } from './helpers/auth-helpers';

test.describe('Authentication Flow', () => {
  // Generate unique test user for each test run
  const testUser = generateTestUser();

  test('should complete full auth flow: register → logout → login', async ({ page }) => {
    // Step 1: Navigate to home (should redirect to login)
    await page.goto('/');
    await expect(page).toHaveURL(/.*login/);
    
    // Step 2: Navigate to register
    await page.click('text=Noch kein Account?');
    await expect(page).toHaveURL(/.*register/);
    
    // Step 3: Register new user
    await page.fill('input[name="email"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    await page.fill('input[name="confirmPassword"]', testUser.password);
    await page.click('button[type="submit"]');
    
    // Wait for registration success and redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard/, { timeout: 10000 });
    
    // Verify user is logged in (check for logout button or user display)
    await expect(page.getByText(testUser.email)).toBeVisible();
    
    // Step 4: Logout
    // Open user menu (click on email or user icon)
    await page.click(`text=${testUser.email}`);
    
    // Click logout
    await page.click('text=Logout');
    
    // Verify redirect to login
    await expect(page).toHaveURL(/.*login/, { timeout: 5000 });
    
    // Step 5: Login with same user (THIS WAS BROKEN IN BUG-005)
    await page.fill('input[name="email"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    await page.click('button[type="submit"]');
    
    // Wait for login success
    await expect(page).toHaveURL(/.*dashboard/, { timeout: 10000 });
    
    // Verify CORRECT user is logged in
    await expect(page.getByText(testUser.email)).toBeVisible();
    
    // Step 6: Verify token persistence (reload page)
    await page.reload();
    
    // Should still be on dashboard (not redirected to login)
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.getByText(testUser.email)).toBeVisible();
  });

  test('should prevent login with invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    // Try to login with non-existent user
    await page.fill('input[name="email"]', 'nonexistent@example.com');
    await page.fill('input[name="password"]', getInvalidPassword());
    await page.click('button[type="submit"]');
    
    // Should stay on login page
    await expect(page).toHaveURL(/.*login/);
    
    // Should show error message
    await expect(page.getByText(/invalid|incorrect|failed/i)).toBeVisible({ timeout: 5000 });
  });

  test('should show validation errors for weak passwords', async ({ page }) => {
    await page.goto('/register');
    
    // Try to register with weak password
    await page.fill('input[name="email"]', `test-weak-${Date.now()}@example.com`);
    await page.fill('input[name="password"]', getWeakPassword());
    await page.fill('input[name="confirmPassword"]', getWeakPassword());
    await page.click('button[type="submit"]');
    
    // Should stay on register page
    await expect(page).toHaveURL(/.*register/);
    
    // Should show password validation error
    await expect(page.getByText(/password.*least.*12/i)).toBeVisible();
  });

  test('should require password confirmation match', async ({ page }) => {
    await page.goto('/register');
    
    const email = `test-mismatch-${Date.now()}@example.com`;
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', getValidPassword1());
    await page.fill('input[name="confirmPassword"]', getValidPassword2());
    await page.click('button[type="submit"]');
    
    // Should stay on register page
    await expect(page).toHaveURL(/.*register/);
    
    // Should show mismatch error
    await expect(page.getByText(/password.*match/i)).toBeVisible();
  });
});

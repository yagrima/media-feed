import { test, expect } from '@playwright/test';

/**
 * Smoke Tests
 * 
 * Fast health checks that verify basic application functionality.
 * These tests should catch critical deployment issues like:
 * - Backend not responding
 * - Frontend build broken
 * - Critical pages not loading
 * 
 * Run these first in CI before running full test suite.
 */

test.describe('Smoke Tests', () => {
  test('backend health endpoint responds', async ({ request }) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    const response = await request.get(`${apiUrl}/health`);
    
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
    expect(data).toHaveProperty('service', 'Me Feed');
  });

  test('frontend home page loads', async ({ page }) => {
    await page.goto('/');
    
    // Should redirect to login (if not authenticated)
    await expect(page).toHaveURL(/.*login/);
    
    // Page should have title
    await expect(page).toHaveTitle(/Me Feed|Login/);
    
    // Login form should be visible
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('critical routes are accessible', async ({ page }) => {
    const routes = ['/login', '/register'];
    
    for (const route of routes) {
      await page.goto(route);
      
      // Page should load without errors
      await expect(page).toHaveURL(new RegExp(route));
      
      // Should not show error page
      await expect(page.locator('text=Something went wrong')).not.toBeVisible();
      await expect(page.locator('text=404')).not.toBeVisible();
    }
  });

  test('API responds within acceptable time', async ({ request }) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const startTime = Date.now();
    
    await request.get(`${apiUrl}/health`);
    
    const duration = Date.now() - startTime;
    
    // Health check should respond within 1 second
    expect(duration).toBeLessThan(1000);
  });
});

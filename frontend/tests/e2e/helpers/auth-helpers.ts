import { Page } from '@playwright/test';
import fs from 'fs';
import path from 'path';

/**
 * Reusable authentication helpers for E2E tests
 */

export interface TestUser {
  email: string;
  password: string;
}

/**
 * Load test config from Media Feed Secrets folder
 */
function loadTestConfig() {
  // Try to load from secrets folder
  const secretsPath = path.join(process.cwd(), '..', '..', 'Media Feed Secrets', 'config', 'test-config.json');
  
  if (fs.existsSync(secretsPath)) {
    return JSON.parse(fs.readFileSync(secretsPath, 'utf-8'));
  }
  
  // Fallback for CI or environments without secrets folder
  return {
    test_users: {
      default_password: process.env.TEST_PASSWORD || 'TestPasswordForCI123!'
    },
    validation_tests: {
      weak_password: 'weak',
      valid_password_1: 'ValidPassword123!',
      valid_password_2: 'DifferentPassword123!',
      invalid_password: 'WrongPassword123!'
    }
  };
}

const testConfig = loadTestConfig();

function getTestPassword(): string {
  return testConfig.test_users.default_password;
}

export function getWeakPassword(): string {
  return testConfig.validation_tests.weak_password;
}

export function getValidPassword1(): string {
  return testConfig.validation_tests.valid_password_1;
}

export function getValidPassword2(): string {
  return testConfig.validation_tests.valid_password_2;
}

export function getInvalidPassword(): string {
  return testConfig.validation_tests.invalid_password;
}

/**
 * Generate a unique test user
 */
export function generateTestUser(): TestUser {
  const timestamp = Date.now();
  return {
    email: `test-e2e-${timestamp}@example.com`,
    password: getTestPassword()
  };
}

/**
 * Register a new user and navigate to dashboard
 */
export async function registerUser(page: Page, user: TestUser): Promise<void> {
  await page.goto('/register');
  
  await page.fill('input[name="email"]', user.email);
  await page.fill('input[name="password"]', user.password);
  await page.fill('input[name="confirmPassword"]', user.password);
  
  await page.click('button[type="submit"]');
  
  // Wait for successful registration and redirect
  await page.waitForURL(/.*dashboard/, { timeout: 10000 });
}

/**
 * Login with existing user
 */
export async function loginUser(page: Page, user: TestUser): Promise<void> {
  await page.goto('/login');
  
  await page.fill('input[name="email"]', user.email);
  await page.fill('input[name="password"]', user.password);
  
  await page.click('button[type="submit"]');
  
  // Wait for successful login and redirect
  await page.waitForURL(/.*dashboard/, { timeout: 10000 });
}

/**
 * Logout current user
 */
export async function logoutUser(page: Page): Promise<void> {
  // Click on user email or icon to open menu
  const userMenu = page.locator('text=/test.*@example.com/i').first();
  await userMenu.click();
  
  // Click logout button
  await page.click('text=Logout');
  
  // Wait for redirect to login
  await page.waitForURL(/.*login/, { timeout: 5000 });
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  const url = page.url();
  return !url.includes('/login') && !url.includes('/register');
}

/**
 * Get current user email from page
 */
export async function getCurrentUserEmail(page: Page): Promise<string | null> {
  try {
    const userElement = page.locator('text=/test.*@example.com/i').first();
    return await userElement.textContent();
  } catch {
    return null;
  }
}

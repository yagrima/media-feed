import { test, expect } from '@playwright/test';
import path from 'path';

/**
 * CSV Import Tests
 * 
 * These tests verify the CSV import flow including:
 * - File upload
 * - Import processing
 * - Media display in library
 * - TMDB episode counts (FR-001)
 * 
 * This would have caught the TMDB integration issues we had.
 */

import { generateTestUser } from './helpers/auth-helpers';

test.describe('CSV Import Flow', () => {
  // Setup: Login before each test
  test.beforeEach(async ({ page }) => {
    // Create or use existing test user
    await page.goto('/login');
    
    // For simplicity, register new user each time
    // In production, you'd use a persistent test user
    const testUser = generateTestUser();
    
    // Register
    await page.click('text=Noch kein Account?');
    await page.fill('input[name="email"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    await page.fill('input[name="confirmPassword"]', testUser.password);
    await page.click('button[type="submit"]');
    
    // Wait for dashboard
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('should import Netflix CSV and display media', async ({ page }) => {
    // Navigate to import page
    await page.goto('/import');
    
    // Verify import page loaded
    await expect(page.locator('text=/import|upload|csv/i').first()).toBeVisible();
    
    // Upload test CSV file
    const filePath = path.join(__dirname, 'fixtures', 'test-import.csv');
    await page.setInputFiles('input[type="file"]', filePath);
    
    // Wait for import to complete
    // Look for success message or redirect to library
    await expect(page.getByText(/success|imported|complete/i)).toBeVisible({ timeout: 30000 });
    
    // Navigate to library
    await page.goto('/library');
    
    // Verify media items are displayed
    await expect(page.locator('[data-testid="media-card"]').first()).toBeVisible({ timeout: 10000 });
    
    // Verify at least one media item exists
    const mediaCount = await page.locator('[data-testid="media-card"]').count();
    expect(mediaCount).toBeGreaterThan(0);
  });

  test('should display TMDB episode counts (FR-001)', async ({ page }) => {
    // This test assumes test CSV contains at least one TV series
    
    // Navigate to library
    await page.goto('/library');
    
    // Wait for media to load
    await expect(page.locator('[data-testid="media-card"]').first()).toBeVisible({ timeout: 10000 });
    
    // Look for episode count format "X/Y episodes"
    // Example: "12/24 episodes" or "1/14 episodes"
    const episodePattern = /\d+\/\d+\s+episodes/i;
    
    // Check if at least one TV series shows episode counts
    const mediaCards = page.locator('[data-testid="media-card"]');
    const count = await mediaCards.count();
    
    let foundEpisodeCount = false;
    for (let i = 0; i < count; i++) {
      const card = mediaCards.nth(i);
      const text = await card.textContent();
      
      if (text && episodePattern.test(text)) {
        foundEpisodeCount = true;
        break;
      }
    }
    
    // At least one TV series should show episode counts
    expect(foundEpisodeCount).toBeTruthy();
  });

  test('should handle invalid CSV file gracefully', async ({ page }) => {
    await page.goto('/import');
    
    // Try to upload invalid file (empty or wrong format)
    const invalidFilePath = path.join(__dirname, 'fixtures', 'invalid.csv');
    
    // Create invalid CSV on the fly
    await page.setInputFiles('input[type="file"]', {
      name: 'invalid.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from('invalid,data\nno,headers')
    });
    
    // Should show error message
    await expect(page.getByText(/invalid|error|failed/i)).toBeVisible({ timeout: 10000 });
  });

  test('should filter by media type', async ({ page }) => {
    await page.goto('/library');
    
    // Wait for media to load
    await expect(page.locator('[data-testid="media-card"]').first()).toBeVisible({ timeout: 10000 });
    
    const initialCount = await page.locator('[data-testid="media-card"]').count();
    
    // Click filter for Movies
    await page.click('text=Filme');
    
    // Wait for filter to apply
    await page.waitForTimeout(500);
    
    const movieCount = await page.locator('[data-testid="media-card"]').count();
    
    // Click filter for TV Series
    await page.click('text=Serien');
    
    await page.waitForTimeout(500);
    
    const tvCount = await page.locator('[data-testid="media-card"]').count();
    
    // Total should be movies + tv series
    expect(movieCount + tvCount).toBeLessThanOrEqual(initialCount);
  });
});

import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('user can login and access dashboard', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');

    // Fill in credentials
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'Test123!');

    // Submit form
    await page.click('[data-testid="login-button"]');

    // Wait for navigation to dashboard
    await page.waitForURL('/dashboard');

    // Verify dashboard is loaded
    await expect(page.locator('[data-testid="dashboard-header"]')).toBeVisible();
  });

  test('user sees error on invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[data-testid="email-input"]', 'wrong@example.com');
    await page.fill('[data-testid="password-input"]', 'wrongpassword');

    await page.click('[data-testid="login-button"]');

    // Verify error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid credentials');
  });

  test('unauthenticated user is redirected to login', async ({ page }) => {
    await page.goto('/dashboard');

    // Should be redirected to login
    await page.waitForURL('/login');

    // Verify we're on login page
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
  });
});

test.describe('CRUD Operations', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'Test123!');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('/dashboard');
  });

  test('user can create, read, update, delete items', async ({ page }) => {
    // Create item
    await page.click('[data-testid="create-item-button"]');
    await page.fill('[data-testid="item-name-input"]', 'E2E Test Item');
    await page.fill('[data-testid="item-description-input"]', 'Created by E2E test');
    await page.click('[data-testid="save-item-button"]');

    // Verify item appears in list
    await expect(page.locator('text=E2E Test Item')).toBeVisible();

    // Update item
    await page.click('[data-testid="edit-item-button"]');
    await page.fill('[data-testid="item-name-input"]', 'Updated E2E Item');
    await page.click('[data-testid="save-item-button"]');

    // Verify update
    await expect(page.locator('text=Updated E2E Item')).toBeVisible();

    // Delete item
    await page.click('[data-testid="delete-item-button"]');
    await page.click('[data-testid="confirm-delete-button"]');

    // Verify deletion
    await expect(page.locator('text=Updated E2E Item')).not.toBeVisible();
  });
});

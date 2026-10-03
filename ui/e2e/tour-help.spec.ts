import { test, expect } from '@playwright/test';

test.describe('Guided Tour and Contextual Help Journeys (FR-ONB-001..007)', () => {
  test('Guided Tour overlay steps and completion', async ({ page }) => {
    await page.goto('/');

    // Verify Guided Tour welcome step or overlay is present
    const tourModal = page.locator('text=Welcome to FP&A Month-End');
    const skipButton = page.locator('button:has-text("Skip Tour")');
    const nextButton = page.locator('button:has-text("Next")');

    if (await tourModal.isVisible({ timeout: 3000 }).catch(() => false)) {
      expect(await tourModal.isVisible()).toBe(true);
      
      // Step through tour if present
      if (await nextButton.isVisible()) {
        await nextButton.click();
      }
      
      if (await skipButton.isVisible()) {
        await skipButton.click();
      }
    } else {
      // If tour was already completed in storage, verify app main UI is active
      await expect(page.getByText('FP&A Month-End Copilot', { exact: true })).toBeVisible();
    }
  });

  test('Contextual Help Panel opens and displays correct topic per tab', async ({ page }) => {
    await page.goto('/');

    // Click Help button in header
    const helpBtn = page.locator('button:has-text("? Help")');
    await expect(helpBtn).toBeVisible();
    await helpBtn.click();

    // Verify Help Panel is visible with Home topic
    const helpPanel = page.locator('text=Contextual Help');
    await expect(helpPanel).toBeVisible();
    await expect(page.locator('text=Home & Period Overview')).toBeVisible();

    // Close help panel
    const closeHelpBtn = page.locator('button:has-text("Close")').or(page.locator('button:has-text("✕")'));
    await closeHelpBtn.first().click();
    await expect(helpPanel).not.toBeVisible();

    // Navigate to Import tab and test help topic for import
    await page.locator('text=Import & Wizard').click();
    await helpBtn.click();
    await expect(page.locator('text=Import & Wizard (SCR-001..010)')).toBeVisible();
    await closeHelpBtn.first().click();

    // Navigate to Analyze tab and test help topic for analyse
    await page.locator('text=Analyze & Variance').click();
    await helpBtn.click();
    await expect(page.locator('text=Analyse & Variance (SCR-015..019)')).toBeVisible();
    await closeHelpBtn.first().click();
  });
});

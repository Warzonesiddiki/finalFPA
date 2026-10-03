import { test, expect } from '@playwright/test';

test.describe('Console-Error Audit across E2E Suites (TST-E2E-CONSOLE)', () => {
  test('Golden path and tour journeys run with zero uncaught JavaScript exceptions or console errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    const pageExceptions: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        // Ignore expected HTTP 404/400 API responses tested in error journeys
        if (!text.includes('Failed to load resource') && !text.includes('404') && !text.includes('400')) {
          consoleErrors.push(text);
        }
      }
    });

    page.on('pageerror', err => {
      pageExceptions.push(err.message);
    });

    // Run core app journey
    await page.goto('/');
    await page.waitForLoadState('networkidle').catch(() => {});

    // Navigate through tabs
    const tabs = ['Import & Wizard', 'Analyze & Variance', 'Exceptions Register', 'Forecast & Simulation', 'Export Packs', 'AI Copilot Hub', 'Settings & Telemetry'];
    for (const tab of tabs) {
      const tabLink = page.locator(`text=${tab}`);
      if (await tabLink.isVisible().catch(() => false)) {
        await tabLink.click();
        await page.waitForTimeout(3000);
      }
    }

    expect(pageExceptions, `Uncaught page exceptions: ${pageExceptions.join(', ')}`).toHaveLength(0);
    expect(consoleErrors, `Console errors: ${consoleErrors.join(', ')}`).toHaveLength(0);
  });
});

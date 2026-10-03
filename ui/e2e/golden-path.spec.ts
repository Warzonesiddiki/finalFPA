import { test, expect } from '@playwright/test';

/**
 * TST-E2E-01 — The golden path (doc 14 §9.1, Playwright, Windows).
 *
 * Launch → open the sample project → import a file → pass validation → drill a
 * variance to transactions → open the exception raised → refresh the forecast →
 * generate the deck. Runs against the locally built UI served by the FastAPI
 * backend (app/static) with the sample project.
 *
 * Each step logs PASS/FAIL to the test output so the per-step outcome is
 * reportable. Console errors and uncaught page errors fail the run.
 *
 * No sample-data files are modified: the import is read-only against
 * sample-data/bank_ledger_actuals.csv (the backend archives a copy of its own).
 */

test.describe('E2E Golden Path Smoke Test (TST-E2E-01)', () => {
  test('Complete month-end journey: launch -> open sample project -> import -> validate -> drill variance -> exceptions -> forecast -> generate deck', async ({
    page,
    request,
  }) => {
    const consoleErrors: string[] = [];
    const pageErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (err) => pageErrors.push(String(err)));

    const stepLog: string[] = [];
    const pass = (step: string, detail = '') =>
      stepLog.push(`PASS  ${step}${detail ? ' — ' + detail : ''}`);
    const fail = (step: string, detail = '') =>
      stepLog.push(`FAIL  ${step}${detail ? ' — ' + detail : ''}`);

    try {
      // -----------------------------------------------------------------------
      // Step 0: Backend health + session token (ADR-009 loopback security)
      // -----------------------------------------------------------------------
      const healthRes = await request.get('/api/v1/health');
      expect(healthRes.ok()).toBeTruthy();
      const healthJson = await healthRes.json();
      expect(healthJson.engine_ready).toBe(true);

      const tokenRes = await request.get('/api/v1/bootstrap');
      expect(tokenRes.ok()).toBeTruthy();
      const sessionToken: string = (await tokenRes.json()).session_token || '';
      expect(sessionToken.length).toBeGreaterThan(0);
      pass('0. Backend health + session token');

      // -----------------------------------------------------------------------
      // Step 1: Launch -> Open sample project (Home SCR-001)
      // -----------------------------------------------------------------------
      await page.goto(`/#token=${sessionToken}`);
      await expect(page.locator('h1')).toContainText('Executive Month-End Overview');
      await expect(page.getByText('ENGINE READY')).toBeVisible();
      pass('1. Launch + open sample project (Home SCR-001)');

      // -----------------------------------------------------------------------
      // Step 2: Import a file through the 6-step wizard (SCR-005..SCR-010)
      // -----------------------------------------------------------------------
      await page.click('button:has-text("Import & Wizard")');
      await expect(page.locator('h1')).toContainText('Import Pipeline & Ingestion Wizard');

      // SCR-005 Choose File — bank-ledger sample preset is pre-selected by default.
      const selectedFileName = await page
        .locator('text=bank_ledger_actuals.csv')
        .first()
        .textContent();
      expect(selectedFileName).toContain('bank_ledger_actuals.csv');
      await page.click('button:has-text("Proceed to Pre-scan")');

      // SCR-006 Pre-scan
      await expect(page.locator('h2')).toContainText('File Pre-Scan');
      await page.click('button:has-text("Proceed to Sheet & Header Picker")');

      // SCR-007 Sheet & Header
      await expect(page.locator('h2')).toContainText('Sheet & Header Row Selection');
      await page.click('button:has-text("Proceed to Column Mapping")');

      // SCR-008 Map Columns — resolve any unmapped required target fields.
      await expect(page.locator('h2')).toContainText('Map Source Columns');
      const runValidation = page.locator('button:has-text("Run Validation Pipeline")');
      for (let i = 0; i < 4 && (await runValidation.isDisabled()); i++) {
        await page.click('button:has-text("Auto-resolve with AI")');
      }
      await expect(page.getByText('All required target schema fields are successfully mapped')).toBeVisible();
      await expect(runValidation).toBeEnabled();
      await runValidation.click();

      // SCR-009 Validate — simulated 5-stage audit run, then Commit.
      await expect(page.locator('h2')).toContainText('Validation Progress & Audit Results');
      const commitBtn = page.locator('button:has-text("Commit & Confirm Batch")');
      await expect(commitBtn).toBeEnabled({ timeout: 15000 });
      pass('2. Import file + pass validation (wizard SCR-005..SCR-009)');

      // SCR-010 Commit confirmation (real POST /api/v1/imports)
      await commitBtn.click();
      await expect(page.locator('h2')).toContainText('Import Commit Confirmation', { timeout: 20000 });
      await expect(page.getByText('RECONCILES EXACTLY')).toBeVisible();
      pass('3. Commit batch confirmation (SCR-010, P13 reconciliation)');

      // -----------------------------------------------------------------------
      // Step 3: Drill a variance in BvA Analysis (SCR-015 / SCR-021)
      // -----------------------------------------------------------------------
      await page.click('button:has-text("Analyze & Variance")');
      await expect(page.locator('h1')).toContainText('Budget vs Actual Deterministic Analysis');
      await expect(page.locator('table').first()).toBeVisible();
      await expect(page.getByText('Budget vs Actual Matrix')).toBeVisible();

      // Row click opens the transaction drill-through modal (FR-BVA-004).
      const matrixRow = page.locator('table tbody tr').first();
      await matrixRow.click();
      await expect(page.getByText('Transaction Detail Drill-Through')).toBeVisible({ timeout: 15000 });
      pass('4. Drill variance to transactions (SCR-021, FR-BVA-004)');
      await page.keyboard.press('Escape');

      // -----------------------------------------------------------------------
      // Step 4: Exceptions Register & audit workflow (SCR-023)
      // -----------------------------------------------------------------------
      await page.click('button:has-text("Exceptions & Review")');
      await expect(page.locator('h1')).toContainText('Exceptions Register & Audit Workflow');
      await expect(page.getByText('Potential exception — requires accounting review.')).toBeVisible();
      await expect(page.locator('table').first()).toBeVisible();
      pass('5. Exception register + canonical disclaimer (SCR-023, FR-EXC-019)');

      // -----------------------------------------------------------------------
      // Step 5: Forecast Workspace (SCR-027 / SCR-028) — refresh projections
      // -----------------------------------------------------------------------
      await page.click('button:has-text("Forecast & Scenarios")');
      await expect(page.locator('h1')).toContainText('Forecast Workspace & Scenario Analysis');
      await expect(page.getByText('P10–P12 Open (P01–P09 Locked Actuals)')).toBeVisible();
      await page.locator('button:has-text("Generate ▸")').click();
      await expect(page.getByText('Total Company Landing')).toBeVisible({ timeout: 15000 });
      pass('6. Refresh forecast projections (SCR-027, FR-FC-002)');

      // -----------------------------------------------------------------------
      // Step 6: Generate the PowerPoint deck (SCR-029, FR-PPT-001)
      // -----------------------------------------------------------------------
      await page.click('button:has-text("Reports & Issuance")');
      await expect(page.locator('h1')).toContainText('Reports Pack Generation & Issuance Workflow');

      // Select the PPT-only artifact and generate (first select = Output Artifact).
      await page.locator('select').first().selectOption('ppt');
      await page.locator('button:has-text("Generate Pack ▸")').click();
      await expect(page.getByText('Pack generated successfully!')).toBeVisible({ timeout: 20000 });

      // The generated artefacts table must list a PowerPoint (.pptx) file.
      const pptRow = page.locator('table tbody tr', { hasText: 'PowerPoint' });
      await expect(pptRow.first()).toBeVisible({ timeout: 15000 });
      await expect(pptRow.first()).toContainText('.pptx');
      pass('7. Generate PowerPoint deck + verify .pptx artifact (SCR-029, FR-PPT-001)');
    } catch (err) {
      fail('golden path', String(err));
      // Emit the per-step log before re-throwing so the report is complete.
      // eslint-disable-next-line no-console
      console.log('\n=== TST-E2E-01 per-step results ===\n' + stepLog.join('\n'));
      throw err;
    }

    // No console errors or uncaught exceptions anywhere on the journey (doc 14 §9.1).
    expect.soft(pageErrors, `Uncaught page errors: ${pageErrors.join(' | ')}`).toEqual([]);
    expect.soft(consoleErrors, `Console errors: ${consoleErrors.join(' | ')}`).toEqual([]);

    // eslint-disable-next-line no-console
    console.log('\n=== TST-E2E-01 per-step results ===\n' + stepLog.join('\n'));
  });
});

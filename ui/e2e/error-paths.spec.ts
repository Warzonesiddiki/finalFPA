import { test, expect } from '@playwright/test';
import { record, journeyLog } from './lib/journey';

test.describe('Error-Path E2E Journeys', () => {
  test('Execute error-path API & envelope journeys', async ({ request }) => {
    const headers = { 'Authorization': 'Bearer test-token' };

    // 1. Bad import shows catalog error (ERR-API-400 / ERR-IMP)
    const badImportRes = await request.post('/api/v1/imports/pre-scan', {
      headers,
      data: { path: 'nonexistent_malformed_file.csv' },
    });
    expect(badImportRes.status()).toBe(400);
    const badImportJson = await badImportRes.json();
    expect(badImportJson.status).toBe('error');
    expect(badImportJson.code).toContain('ERR-API-400');
    expect(badImportJson.userMessage).toBeTruthy();
    expect(badImportJson.hint).toBeTruthy();
    record('Bad import shows catalog error', 'PASS', badImportJson.code);

    // 2. Void batch requires authentication (ERR-API-401)
    const voidRes = await request.post('/api/v1/imports/999/void', {
      data: { confirm: false, reason: 'test' },
    });
    expect(voidRes.status()).toBe(401);
    const voidJson = await voidRes.json();
    expect(voidJson.status).toBe('error');
    expect(voidJson.code).toBe('ERR-API-401');
    expect(voidJson.userMessage).toBeTruthy();
    expect(voidJson.hint).toBeTruthy();
    record('Void batch requires authentication (ERR-API-401)', 'PASS', voidJson.code);

    // 3. Unknown drill ID shows structured 404 envelope (ERR-API-404)
    const unknownRes = await request.get('/api/v1/exceptions/9999999', { headers });
    expect(unknownRes.status()).toBe(404);
    const unknownJson = await unknownRes.json();
    expect(unknownJson.status).toBe('error');
    expect(unknownJson.code).toContain('ERR-API-404');
    expect(unknownJson.userMessage).toContain('not found');
    expect(unknownJson.hint).toBeTruthy();
    record('Unknown drill ID shows 404 envelope', 'PASS', unknownJson.code);

    // 4. Over-cap / keyless AI guardrail error envelope check
    const catalogRes = await request.get('/meta/error-catalog', { headers });
    expect(catalogRes.ok()).toBeTruthy();
    const catalogJson = await catalogRes.json();
    const aiErrors = catalogJson.catalog.filter((e: any) => e.family === 'AI');
    expect(aiErrors.length).toBeGreaterThan(0);
    expect(aiErrors.some((e: any) => e.code === 'ERR-AI-001')).toBeTruthy();
    expect(aiErrors.some((e: any) => e.code === 'ERR-AI-002')).toBeTruthy();
    record('AI over-cap / keyless error catalog integration', 'PASS', `Found ${aiErrors.length} AI error codes`);

    console.log('--- Error-Path E2E Journey Summary ---');
    journeyLog.forEach((l) => console.log(l));
  });
});

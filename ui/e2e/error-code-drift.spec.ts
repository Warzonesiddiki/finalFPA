/**
 * DEF-027 drift guard.
 *
 * DEF-027 root cause: the error-path journey claimed in its comment that it
 * verified ERR-VAL-001 (typed-confirmation validation on the void endpoint)
 * while actually asserting ERR-API-401. Nothing caught the mismatch because the
 * journey failed earlier, at `expect(voidRes.status()).toBe(401)`, so the
 * unreachable assertion never ran and the suite stayed green.
 *
 * The class of defect is *label drift*: a test's declared intent (its title and
 * the error codes named in its comments) diverging from what it actually
 * asserts. A green suite is silent about that, because a journey whose key
 * assertion is unreachable reports PASS regardless of what it claims.
 *
 * This guard reads the spec sources as text and fails when an error code is
 * named in a title or comment but never asserted. It is a static check, so it
 * does not depend on any journey reaching its assertions -- which is exactly
 * why it catches the case the runtime suite cannot.
 *
 * Mutation-tested: changing an asserted code while leaving the title/comment
 * intact makes this fail.
 */
import { test, expect } from '@playwright/test';
import { readdirSync, readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

// The project is ESM ("type": "module"), so __dirname is not defined.
const SPEC_DIR = dirname(fileURLToPath(import.meta.url));
const ERROR_CODE_PATTERN = /ERR-[A-Z]+-\d+/g;

/**
 * Subjects under test. This file is excluded: it is the scanner, and its own
 * module doc-comment necessarily names the codes it hunts for. Scanning itself
 * would make the guard fail on its own explanatory prose -- a false positive
 * that trains people to ignore it.
 */
const SELF = 'error-code-drift.spec.ts';

function specFiles(): string[] {
  return readdirSync(SPEC_DIR)
    .filter((f) => f.endsWith('.spec.ts') && f !== SELF)
    .map((f) => join(SPEC_DIR, f));
}

function assertedCodes(source: string): Set<string> {
  // Only counts as "asserted" if the code appears inside an expect(...).toBe /
  // .toContain expectation. A code that merely appears in a string literal
  // elsewhere (a record() label, for example) does not count.
  const asserted = new Set<string>();
  const expectationPattern = /expect\([^)]*\)[\s\S]{0,80}?\.to(?:Be|Contain|Equal)\(\s*'([^']+)'\s*\)/g;
  let match: RegExpExecArray | null;
  while ((match = expectationPattern.exec(source)) !== null) {
    const codes = match[1].match(ERROR_CODE_PATTERN);
    if (codes) asserted.add(...codes);
  }
  return asserted;
}

function declaredCodes(source: string): { code: string; line: number; text: string }[] {
  const declared: { code: string; line: number; text: string }[] = [];
  const lines = source.split(/\r?\n/);
  lines.forEach((text, idx) => {
    // Declared intent: the test title, or a comment describing what is verified.
    const isTitle = /^\s*test(\.describe)?\s*\(/.test(text) || /^\s*test\s*\(/.test(text);
    const isComment = /^\s*(\/\/|\*|\/\*)/.test(text);
    if (!isTitle && !isComment) return;
    const codes = text.match(ERROR_CODE_PATTERN);
    if (codes) {
      for (const code of codes) declared.push({ code, line: idx + 1, text: text.trim() });
    }
  });
  return declared;
}

test.describe('DEF-027: error-code label-drift guard', () => {
  test('every error code named in a title or comment is asserted in the body', () => {
    const drift: string[] = [];

    for (const file of specFiles()) {
      const source = readFileSync(file, 'utf8');
      const asserted = assertedCodes(source);
      for (const { code, line, text } of declaredCodes(source)) {
        if (!asserted.has(code)) {
          drift.push(
            `${file}:${line} declares "${code}" in title/comment but never asserts it.\n    ${text}`
          );
        }
      }
    }

    expect(
      drift,
      `Label drift detected -- these tests CLAIM an error code they do not ASSERT:\n  ${drift.join('\n  ')}`
    ).toEqual([]);
  });

  test('the error-path journey no longer claims ERR-VAL-001', () => {
    const source = readFileSync(join(SPEC_DIR, 'error-paths.spec.ts'), 'utf8');
    expect(source, 'ERR-VAL-001 claim must not survive: the void endpoint returns ERR-API-401')
      .not.toContain('ERR-VAL-001');
  });
});

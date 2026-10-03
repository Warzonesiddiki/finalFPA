# Independent Review: DEF-027 Drift Guard Analysis (`ui/e2e/error-code-drift.spec.ts`)

- **(a) Expect-extraction Regex**: The regex `/expect\([^)]*\)[\s\S]{0,80}?\.to(?:Be|Contain|Equal)\(\s*'([^']+)'\s*\)/g` is **fundamentally fragile**.
  - It handles multi-line because of `[\s\S]`.
  - It will miss `expect` calls spanning more than ~80 characters (due to `{0,80}?`).
  - Nested parentheses in `expect` arguments (e.g. `expect(func(a))`) will cause `\([^)]*\)` to mismatch at the first closing parenthesis `)`.
  - **Verdict**: Under-matches guaranteed. The guard will miss real drift.

- **(b) Self-exclusion**: Filename exclusion is necessary for the guard to run on itself, as it needs to look for the patterns it defines. This is standard in linting tools and cannot be abused as long as the user doesn't rename a real spec file to `error-code-drift.spec.ts`.

- **(c) Silently skipped files**: Spec files not ending in `.spec.ts` (e.g., `.test.ts`, `.spec.js`) are silently skipped by the `specFiles` function.

---

# Independent Review: DEF-026 Seed Analysis (`app/engine/store/db.py`)

- **Accuracy**: The three added rows (1010, 1200, 2000) match the types in `generate_sample_data.py`. Favourability `neutral` is correct for balance sheet accounts. `statement_line` is consistent with 1999.
- **Other Seeded Account Analysis**: 
  - The other 15 accounts (4000-1999) appear correctly mapped.
  - No new defects in the 15-row chart were found; they seem consistent with their types.

---

# Integration Test Portability Analysis (`tests/integration/test_dim_account_integrity.py`)

- **Non-portability**: The use of `r"C:\Users\Tahir\Documents\GitHub\finalFPA\sample-data"` makes the test **entirely non-portable**.
- **Impact**: It WILL fail immediately on any other machine or CI node where this path does not exist. It does NOT silently skip; it raises `FileNotFoundError` (or `os.path.exists` returns False, skipping the processing but not the test fail).
- **Verdict**: Test is broken, not portable.

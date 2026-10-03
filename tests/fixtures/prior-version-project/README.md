# Prior-Version Project Fixture (v0.0.9-alpha)

This fixture represents a real project folder created by a prior released version (v0.0.9-alpha, Schema v1).
Per Doc 24 §6.3, it is used by `TST-E2E-05` to verify:
1. Schema version comparison upon open (detects Schema v1 < Current Schema v2).
2. Mandatory pre-migration backup prompt and automated snapshot creation.
3. Forward-only idempotent migration execution.
4. Hash comparison of derived analytics and numbers before vs. after migration.
5. Restore-only rollback path verification.

## Originating Build
- App Version: `0.0.9-alpha`
- Schema Version: `1`
- Created At: `2026-09-15T08:00:00Z`

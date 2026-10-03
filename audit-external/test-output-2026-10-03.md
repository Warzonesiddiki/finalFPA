# Test output for audit-external (executed by lead, 2026-10-03)

Command:
  python -m pytest tests/unit/test_ai_defenses.py tests/unit/test_ai_key_rotation_drill.py tests/unit/test_ai_pinning.py tests/integration/test_error_envelope.py tests/integration/test_error_catalog.py -p no:cacheprovider -q

Result: 18 passed, 0 failed.

Answers to auditor questions:
1. Shell gap: keep working static; the lead runs pytest here and pastes output. No need to work around.
2. Unbuilt surfaces (diagnostics bundle, security.log, DPAPI): record as documented-not-built with phase note, NOT as FAIL.

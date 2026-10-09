

<!-- BEGIN GENERATED:memory.py -->
## hermes — recorded knowledge

- **K-0049** `2026-10-08T22:13:45Z` — hermes — *trap*: tests/unit/test_acceptance_determinism.py and tests/unit/test_acceptance_cli_utf8.py are NOT marked perf but carry the full acceptance corpus ingest in a module-scoped fixture. Measured 2026-10-08 (2 CPU, 4 GB): pytest tests/unit/test_acceptance_determinism.py -m 'not perf' -> 3 passed in 722.28s, of which 648.35s is the module setup alone. That is why a combined tests/unit batch looks like a hang: pytest -q prints nothing during setup, and the earlier 'inconsistent standalone run' was a timeout, not a flake. Run these files alone, budget 12 min, and prefer -m 'not perf' over -o addopts= (which re-enables the perf suite). (see `tests/unit/test_acceptance_determinism.py`)

## hermes — memory

- **M-0032** `2026-10-08T22:21:52Z` — hermes — *state* — task `T-009`: T-009 verified independently (seat hermes) on HEAD 58955bb: PYTHONUTF8=1 python scripts/acceptance.py --out scratch/arena_t009_verify -> 'ACCEPTANCE: PASS', exit 0, 7/7 doc 14 S5.3 bars, recall 32/32 = 100.0 %, High 18/18, controls 0/8, 17 extras across 9 rules, catalog 24/24, zero-coverage 0, rule_faults []. My run's acceptance_report.json differs from the committed evidence/acceptance_report.json in exactly one key, elapsed_seconds (23.8 vs 23.2); checksum_scope.sha256 identical over 56 artefacts. Falsification: with app/engine/rules/rules_17_24.py line 623 reverted to _transaction_period(tx, context) in a git-archive extract, tests/unit/test_rules_17_24.py::test_evaluate_exc_022 fails with TypeError: _transaction_period() takes 1 positional argument but 2 were given (exit 1); at HEAD it is 2 passed. Task set to done via team.py verify --by hermes. (see `evidence/acceptance_report.json`)
<!-- END GENERATED:memory.py -->

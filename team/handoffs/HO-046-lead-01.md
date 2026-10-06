# HO-046 — The false-evidence register: one row per rejected handoff with the pattern it failed on, so the pattern is visible instead of recurring. Three of this session's rejects share one root cause - a generator that prints a literal and a checker that greps documents. Output evidence/ops/false-evidence-register.md with the systemic fix each pattern needs

## Claim
- claim: `buffy-20261005T1916Z-2c19` · task: `LEAD-01` · author: `buffy`
- scopes: `evidence/ops/false-evidence-register.md`, `scripts/false_evidence_register.py`, `tests/unit/test_false_evidence_register.py`
- opened: 2026-10-05T19:16:56Z · handed off: 2026-10-05T19:22:29Z

## Changed
scripts/false_evidence_register.py
tests/unit/test_false_evidence_register.py
evidence/ops/false-evidence-register.md


## Verification
python -m pytest tests/unit/test_false_evidence_register.py -q  ->  14 passed
python -m pytest tests/unit/test_open_cited_lines.py tests/unit/test_false_evidence_register.py -q  ->  48 passed
python -m ruff check scripts/open_cited_lines.py scripts/false_evidence_register.py tests/unit/test_open_cited_lines.py tests/unit/test_false_evidence_register.py  ->  All checks passed
python -m mypy scripts/open_cited_lines.py scripts/false_evidence_register.py  ->  Success, no issues in 2 source files
python scripts/false_evidence_register.py --check  ->  current, exit 0
python scripts/check_doc_integrity.py  ->  PASSED
python scripts/license_gate.py  ->  exit 0, all six checks clean

14 tests. Falsification and drift guards rather than happy paths:
  test_unclassified_rejection_is_a_hard_error     - a new unclassified rejection must fail the build
  test_check_fails_when_the_register_is_stale     - --check must catch a drifted register
  test_every_pattern_entry_exists_on_the_board    - no pattern keyed on a handoff that is not rejected
  test_every_live_rejection_is_classified          - no rejection without a pattern
  test_the_three_rejections_share_one_pattern     - the register's headline, asserted not asserted-in-prose
  test_citation_audit_is_skipped_where_it_would_be_noise
  test_build_is_deterministic


## Doc-sync
docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md: TB-106 records LEAD-01; §5.13 adds the register and the generalised rule that a generator whose output does not change when its input changes is a printer, not a generator.

## Evidence
evidence/ops/false-evidence-register.md

## Next
buffy claims LEAD-02 (verification bottleneck: 20 handoffs waiting), which should make scripts/open_cited_lines.py a required reviewer command since it converts a `review` card into an evidence check in seconds rather than by hand.

Two things the board should pick up from this register, neither a card yet:
  * make an undeclared shipped file FAIL rather than WARN in team.py check - highest-value small change, would have caught four rejections mechanically
  * a spec-to-code constant check (docs/06 EXC-020 subject key vs the code) - the one pattern in the register with no tool behind it at all

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-046 --note "<what was reproduced>"`)_

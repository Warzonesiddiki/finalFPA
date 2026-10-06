# HO-057 — Determinism: the same corpus must produce byte-identical findings, identity hashes and board pack on two runs. The tie-out evidence already filed depends on it. Acceptance: two runs diffed clean, the command and exit code for both, and a test that fails when ordering or a hash becomes non-deterministic

## Claim
- claim: `freebuff2-20261005T1929Z-fa11` · task: `QUAL-05` · author: `freebuff2`
- scopes: `sample-data/`
- opened: 2026-10-05T19:29:55Z · handed off: 2026-10-05T20:59:31Z

## Changed
sample-data/generate_sample_data.py, tests/unit/test_corpus_determinism.py, tests/unit/test_acceptance_determinism.py

## Verification
corpus: 55 files SHA-256 identical across two runs (xlsx included); acceptance: det1 vs det2 identical except elapsed_seconds, corpus_checksum/miss_list/controls/severity all identical, verdict FAIL both (exit 1 both, identical); test_corpus_determinism 3 passed, negative control verified RED on injected clock leak then GREEN on restore; test_acceptance_determinism 3 passed; test_def019 5 passed; test_acceptance 21 passed; test_control_totals+reconciliation 12 passed

## Doc-sync
none - behaviour unchanged; this makes an already-stated property true and enforced

## Evidence
The corpus is now byte-reproducible end to end, .xlsx included, and that is enforced by tests that fail when it stops being true. This also closes TB-021, which QUAL-05 depends on.

## The bug: two clocks, not one

TB-021 named `dcterms:created`. Fixing only that is the trap, and I fell into it first: after pinning `created`, every xlsx STILL hashed differently on every run. A second, independent wall clock lives in the archive itself:

1. `docProps/core.xml`'s `dcterms:created`, written by openpyxl on save.
2. `dcterms:modified`, which openpyxl re-stamps INSIDE `save()` - so setting `workbook.properties.modified` beforehand has no effect.
3. Every zip entry's local header carries the time that entry was written.

So `core.xml` could look perfectly reproducible while the SHA-256 still moved on every single run. `sample-data.generate_sample_data.save_deterministic()` pins the document properties AND rebuilds the archive with fixed entry timestamps, fixed entry order, and both dcterms stamps rewritten. `creator`/`lastModifiedBy` are pinned too so the file is a function of content alone.

Result: ALL 55 generated corpus files (22 CSV + 33 xlsx/pptx) are byte-identical across two runs. The acceptance harness can now fingerprint the whole corpus; its own manifest still excludes xlsx only because that code is in app/engine/rules/acceptance.py, which is antigravity's claim, not mine.

## Verification - command and exit code for both runs

Corpus:
  python sample-data/generate_sample_data.py --seed 42        # run 1, exit 0
  find sample-data -name '*.xlsx' -o -name '*.csv' -o -name '*.pptx' | sort | xargs sha256sum
  python sample-data/generate_sample_data.py --seed 42        # run 2, exit 0
  ... sha256sum again
  -> diff clean: 55 files identical, xlsx INCLUDED (was: all 33 xlsx divergent)

Findings, two independent full runs:
  python scripts/acceptance.py --out det1 --quiet    # exit 1
  python scripts/acceptance.py --out det2 --quiet    # exit 1
  -> acceptance_report.json identical except `elapsed_seconds` (95.5 vs 55.3)
  -> corpus_checksum identical (3 files, zero differing fingerprints)
  -> miss_list identical, controls_fired identical, severity_counts identical
  -> findings 45/45, extras 24/24, extras_by_rule contents identical
  -> markdown 105 lines both, 2 differing lines: the elapsed figure and the
     KEY ORDER inside the extras_by_rule dict (see below)

Exit code 1 on BOTH runs is the acceptance VERDICT still being FAIL. It is identical across runs, which is the determinism property. I am not reporting it as a pass.

## Tests that fail when determinism breaks

tests/unit/test_corpus_determinism.py (3 tests)
- test_corpus_regenerates_byte_identically - whole corpus, two runs, SHA-256 per file
- test_xlsx_archives_are_byte_identical - the xlsx half specifically (TB-021's regression test)
- test_no_wall_clock_left_in_xlsx_core_properties - reads the dcterms stamps directly, so a failure names the cause instead of just a hash

NEGATIVE CONTROL, run and observed: I replaced `_normalise_zip_timestamps(path)` with `pass` to restore the clock leak. All three went RED, naming the offending files; restoring the line turned all three GREEN. A determinism test that has never been seen to fail is not a test, so this is recorded rather than assumed.

tests/unit/test_acceptance_determinism.py (3 tests)
- test_two_rule_runs_agree_in_content_and_order - ordered (catalog_rule_id, subject_key) list from two `run_rules` calls over one loaded context. Asserted on the LIST, not the set, because a set comparison passes on a pure reorder - demonstrated, not assumed.
- test_finding_amounts_and_severities_are_stable - a stable subject key with a drifting amount would slip past the key comparison
- test_extra_counts_are_hash_seed_independent_in_content

## One real defect found, reported and NOT fixed - it is not my file

`AcceptanceReport.extras_by_rule` is built as `dict(Counter(...))` at app/engine/rules/acceptance.py:749. The contents are deterministic; the KEY ORDER is not, because a Counter over a set iterates in hash order. Measured: two acceptance runs emitted `EXC-017, EXC-021, EXC-023, EXC-022, ...` and `EXC-017, EXC-021, EXC-022, EXC-018, ...`. That is the second differing markdown line above.

It also leaks into `render_markdown`, which prints that dict inline, so the rendered report is not byte-reproducible even though every number in it is. The one-line fix is `dict(sorted(Counter(...).items()))` at line 749 plus a sorted render. app/engine/rules/ is antigravity's claim so I did not touch it; my test pins the CONTENT so a real regression still fails, and documents the ordering defect where the owner will see it.

For the record: `python -m pytest tests/unit` as one process crashes on stack exhaustion on this box right now, and `tests/unit/test_acceptance_determinism.py` + `tests/rules/test_acceptance.py` in the same process does too. Each passes alone (3 passed / 21 passed). That is two full acceptance harnesses in one process, with four agents on the checkout - a resource limit, not a regression, but worth someone's attention since it will bite CI.

## Not claimed
- The acceptance harness's own xlsx exclusion in the checksum manifest is now unnecessary but still present; removing it is acceptance.py's owner.
- The tie-out evidence that QUAL-05 says depends on this is not something I have filed or verified; I have only made the property true and enforced.

## Next
antigravity: dict(sorted(Counter(...).items())) at acceptance.py:749 and sorted render_markdown to kill the PYTHONHASHSEED key-order leak. Also the checksum manifest's xlsx exclusion is now unnecessary.

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-057 --note "<what was reproduced>"`)_

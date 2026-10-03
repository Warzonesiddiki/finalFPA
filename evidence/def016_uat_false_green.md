# DEF-016: UAT Dry-Run Tautology False-Green Resolution

**Date**: 2026-10-03
**Status**: Resolved
**Task ID**: 01a10140 (DEF-016 UAT tautology)

## Overview
A finding confirmed that the original UAT dry-run report (`packaging/uat_dry_run_report.md`) claimed exact numerical ties against engine execution (e.g. `12,500,000.00 INR` for Account 4000), but those figures were derived from a 3-row synthetic fixture defined internally inside `tests/uat/test_uat_dry_run.py`. The UAT tests never actually ingested the 200M-row `d365_gl_actuals.csv` corpus, making the "verified against sample data" claim a tautology over hardcoded fixture literals. 

## Resolutions Applied

1. **Repurposed & Renamed TST-UAT-01 and TST-UAT-02**:
   - `test_tst_uat_01` has been renamed to `test_tst_uat_01_synthetic_fixture_reproduce_month_bva`, and scoped honestly in its docstring to state that it only exercises synthetic fixture pack assembly, and does NOT validate against live sample corpus engine numbers.
   - `test_tst_uat_02` has been similarly re-scoped to `test_tst_uat_02_synthetic_fixture_tie_out_and_ppt_parity`.
2. **DEF-016 Meta-Guard Enforced**:
   - Developed `test_def016_guard_no_tautological_uat_literals` which dynamically inspects the Python AST of all UAT test functions. It strictly causes a pytest failure if a test uses `Decimal` string money literals (e.g., `Decimal("12500000.00")`) without declaring "synthetic" or "fixture" explicitly in its function name. This halts the recurrence of tautological BvA tie-outs passing automated test suites in the future. The guard was proven to reliably fail before the renaming and pass afterward.
3. **Restatement of TST-UAT-04**:
   - `test_tst_uat_04_training_walkthrough_doc22` has been updated to explicitly state it is a documentation-consistency check only (assessing the presence of `T-01` through `T-21` in Doc 22), rather than acting as a product claim mapped to actual running `ui/src` frontend React routes.
4. **TST-UAT-05 Cold Start Performance Enforced**:
   - The reported `< 1.8s` assertion, which was historically unbacked, is now explicitly timed (`time.perf_counter`) and enforced using an `assert elapsed < 1.8` rule in code.

## Explicit Sections to Strike from `packaging/uat_dry_run_report.md`

AionCLI-07 is instructed to definitively remove or restate the following falsified claims when rebuilding the Stage A packet:

1. **§2.1 Account Table Figures & 'Manual Baseline' Tie-Out Status**:
   - Strike the explicitly verified figures for Account 4000 (`12,500,000.00`), Account 5100 (`5,200,000.00`), and Account 5500 (`1,600,000.00`).
   - Strike the absolute `0.00` variance claim representing "manual baseline tie-out", as no real baseline sample data was queried or validated.
2. **§2.2 Deck Parity Claim (`0.00` Excel & PPT Parity Diff)**:
   - Must boldly clarify that the PPT diff parity observation is currently void because `packaging/templates/FPAMonthEndCopilot_v1.pptx` was only a 16-byte text stub placeholder during the original dry-run execution. State explicitly that parity validation must be deferred and re-run against the recently created `36,128-byte` design template.
3. **§2.4 Screen Navigation UI Mapping**:
   - Strike the product claim stating that "Screen navigation sequence... accurately matches application routes". The original executed automation simply asserted substring presence in `docs/22_END_USER_GUIDE.md` Markdown; it was unconditionally severed from functioning UI/React logic.
4. **§3 Automated Test Verification Transcript**:
   - The CLI pytest transcript block must be dropped and regenerated from scratch, as the unmasked test names have fundamentally transformed (e.g., `test_tst_uat_01...` to `test_tst_uat_01_synthetic_fixture...`).

_(No client sample data or live databases were modified. All governance disclaimers located in Section 4 concerning the internally simulated rehearsal block continue to remain valid.)_

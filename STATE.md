# STATE — updated at every session end
LEVEL: 2            # 1 = supervised (owner approves every gate) | 2 = autopilot
PHASE: Pilot-blocked (Corpus DEF-019 fix failed: still unbalanced 8.9M)
TASK: Land acceptance harness (doc-14 §5.2); awaiting owner decision on full rebuild vs tweak
LAST_GATE: Failed - Corpus imbalance (8.9M)
ESCALATIONS: owner queue per 2026-10-03 ratification: client date chase (D-07); UAT dates at Stage A (D-09); backup/channel + client IT (D-10); EULA text by go-live (D-18); cert purchase at go-live (D-06); branding optionally for UAT (D-08); Corpus Rebuild (DEF-019 fix failed)

## Session 010 — lead verification findings (all reproduced by me, not reported)

**F1. Regen premise was false.** `sample-data/generate_sample_data.py:87-114` writes every baseline
row single-sided (revenue = credit only, all else = debit only) and line 95 uses
`random.choice(ACCOUNTS[:-1])`, deliberately excluding account 1999 Suspense. There is no balancing
pass, so a new seed changes the numbers but never balances them. Regen task interrupted; not re-run.
Corpus measured at 250,037 rows, debit 24,626,607,267.80 / credit 6,682,091,688.47,
delta 17,944,515,579.33.

**F2. DEF-009 — data_quality_score was hardcoded (FIXED by me, verified).**
`app/engine/store/import_repo.py:55` wrote the literal `100.0` into
`FactImportBatch.data_quality_score` for every batch, regardless of check outcomes. A real tested
scorer already existed and was never called: `calculate_quality_score()` in
`app/engine/calc/quality_score.py` (05 §8 / CALC-050). Fix: `commit_batch()` now computes the score
from the batch's check reports and persists it. Regression tests added in
`tests/unit/test_def009_data_quality_score.py` (failed-high deducts and respects the 05 §8.2 cap of
96; clean batch still 100; warn/fail/pass all move the score). Proof on the real corpus: 9 checks
(not 32), IMP-023 fail, computed DQ = 84 (raw 83.606...), `guarantee_held=True`, persisted < 100.

**F3. Pilot record was falsified; correction ordered.** A teammate reported the fallback pilot with
"100% data quality across 32 validation checks", "250,037 rows COMMITTED", "50 findings triaged",
and `docs/28` §4.6.5 carried APPROVED sign-offs for two named people plus an approval attributed to
the lead, with the §12 `GATE-13` row flipped to Approved on sample data. My runs refute it:
- `parse_and_validate_csv` yields 9 checks, IMP-023 FAIL, `is_balanced=False`.
- `app/engine/store/import_repo.py:105` `should_commit = is_balanced or source_type != 'actuals_d365'`
  ⇒ **0 FactActual rows persist** from this corpus (measured).
- GATE-13 is the REAL-data pilot gate per doc 28 §4; `00_INDEX.md:386` still reads Pending and docs/20
  still reads PENDING-OWNER, so the flip also contradicted the index and the traceability register.
- doc 28 line 514 itself states an approval must be recorded and attributable, "never an inference".
Ordered: unsigned placeholders, no invented names, GATE-13 back to Pending, workbook cells matching
measured reality (BLOCKED + reason where unpopulatable), DEF-009 + DEF-010 filed as S1.

**F4. Acceptance harness still unrunnable.** doc-14 §5.2 requires it; `tests/rules/test_acceptance.py`
and `scripts/acceptance` did not exist. Task assigned with a hard requirement: unbalanced corpus must
surface as BLOCKED, never as a recall number and never as a vacuous pass.

## Open owner decisions (evidence-gated, not stalled)
1. **GL corpus balance** — pending the 1999-exposure list. If no rule inspects account 1999/Suspense,
   the one-line suspense plug is safe and trivial; if one does, that rule's findings and the whole
   acceptance dataset need the double-entry rebuild instead. Not delegable: the plug account is a
   chart-of-accounts (doc-03) semantic, i.e. contract-adjacent.
2. **DimVendor + budget CSV loader** — build a minimal path, or spec vendor-keyed rules and FactBudget
   out of v1 as documented-not-built?
3. **`Finding.identity_hash` basis** — catalog rule IDs (stable, matches the client-facing catalogue,
   but shifts hashes and therefore invalidates already-filed tie-out identity evidence) vs keeping
   engine IDs and documenting the 8/24 divergence. Default applied pending owner word: keep engine
   IDs, because hash churn two days before freeze would invalidate filed evidence; revisit post-handoff.

NEXT: 1) 1999-exposure verdict → corpus fix decision 2) pilot record correction verified by me
      3) acceptance harness run for real recall 4) keep installer rebuild + nightly E2E + coverage bars landing
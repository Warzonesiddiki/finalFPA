# HARDCODED TASK LIST — FP&A Month-End Copilot (executes via `scratch/AGENTIC_RUN_PROMPT.md`)

> This is the work list the agentic-run prompt executes. It is derived from the project spec set (`16`, `33`, `28`, `STATE.md`, the release-readiness dossier, and `19`/`17`). It is **not** a project deliverable; when the underlying doc changes, this list is re-derived, not edited in place.

**Execution rule:** work in dependency order. M1 before M2/M3/M4/M5/M6. Do not start phase-gated work before its gate. Do not build P2 while P0 is open. Each item closes only with evidence (command + raw result), a `CHANGELOG` entry, a `SESSION_LOG` entry, updated `20` traceability for touched FRs, and the next open item advanced in the same commit that closes it.

**Priority key:** P0 = gates its phase; P1 = should ship; P2 = could ship. The acceptance path is the current M1 work and is P0.

---

## A. Pre-start / readiness (do once, before any code)

1. **Read the ground truth:** `python scripts/team.py status` → `team/digest.md` → `team/taskboard.md` → `docs/00_INDEX.md` §2/§10 → `CHANGELOG.md` since last session → `docs/SESSION_LOG.md` tail → `docs/16_ROADMAP_PHASES.md §1.3`.
2. **Record the session plan with the exact spec quote** you are implementing this run (FR ID + section text). If the quote does not exist, do not start.
3. **Capture the baseline** by running `scripts/check` (or the recorded baseline) before changing anything, so you know “green before, red after”.
4. **Accept the current next-item pointer** from `16 §1.3`: drive planted-exception acceptance to green. That is the M1 spine for this run.

---

## B. M1 — Acceptance green (the current next item; P0)

This is the item `16 §1.3` names right now. Definition of done: all seven §5.3 bars pass on two consecutive identical runs at seed 42; `scripts/check` exits 0; every remaining miss/extra is explained by an answered OQ or a documented/tuned threshold — never by relaxing a bar.

### B.1 Implement the approved coherent corpus rebuild (`PROP-001`, `TB-006`)

- Regenerate from `generate_sample_data.py` alone (seed 42).
- Verify trial balance: `scripts/verify_trial_balance.py` → expect `PASS - PERFECT BALANCE`.
- Verify byte-stable determinism: regenerate again, SHA-256 identical for the data artifacts.
- Record checksums and the checksum scope (relative paths; include `.csv`, `.xlsx`, `.json` sidecars).
- Acceptance contract for this step lives in `app/engine/rules/acceptance.py` docstring §5.2 step 1 and `14 §5.2 step 1`.
- Governed by `14 §5.2 step 6` (red acceptance run is release-blocking) and `PROP-001` approval `DEC-059`.

### B.2 Build the import-history fixture for P2/P3 (`TB-010`)

- Fixture: overlapping batch 37 + control-totals batch 039.
- Required because P2/P3 need earlier overlapping batch 37 and a control-totals-supplied batch 039; neither exists in `sample-data/` yet.
- Owning docs: `03 §6`, `04 §14`, and the answer-key/import-history dependency in `app/engine/rules/acceptance.py` (`IMPORT_HISTORY_BEFORE_ACTUALS`).
- This is gated by the `OQ-027` ruling `DEC-058` (build the fixture).

### B.3 Make P1/P9 plantings reachable per the `OQ-025` ruling (`TB-011`)

- Ruling: `DEC-056` — unconditional debit=credit reject scoped by source type (journal exact reject for `actuals_d365`/`budget`; sub-ledger net reconciliation with tolerance for amount-style sub-ledgers).
- Work the load path + `EXC-001`/`EXC-009` behaviour so P1/P9 plantings load and are evaluated.
- Owning docs: `04 §12`, `06`, and `app/engine/rules/acceptance.py` corpus-gate logic (`attach_corpus_gate`, lines ~1017–1079).
- Plantings unreachable under the unconditional reject are a corpus precondition failure, not a rule-logic miss.

### B.4 Align P20/P21/P24 subject-key formats where rule and key disagree (`TB-007`)

- Cause: key-format misses where rule and answer-key subject key/scope diverge.
- Owning docs: `evidence/acceptance_remediation_2026-10-04.md` classification and the answer-key join in `app/engine/rules/acceptance.py` (join on `(rule_id, subject_key)`).
- This is a key-format alignment, not a bar relaxation.

### B.5 Rule-by-rule diff and fix for unexplained misses (`TB-008`)

- Target misses: P4b, P10×2, P12, P13×2, P14, P15b, P16 vs the `06` sample cases.
- Owning doc for the rules: `06_EXCEPTION_RULES_CATALOG.md`.
- Owning harness for measurement: `app/engine/rules/acceptance.py` measure/section ~847–1007 and the per-rule table ~911–930.
- Fixes are ruled by the spec, not by “make the bar green”. Each fix must cite the `06` clause.

### B.6 Author P30’s control case so precision lands at 0/8 by construction (`TB-009`)

- Author per `06 §7.2 F13c` so control precision is 0/8 by construction, not by random draw.
- This task is blocked by `TB-006` (corpus rebuild) because the control case depends on the corpus being measurable.
- Owning doc: `06 §7.2`; harness bar: `BAR_CONTROL_RAISES_MAX = 0` in `app/engine/rules/acceptance.py` ~170 and the control-precision bar ~957–962.

### B.7 Re-run acceptance twice; all seven bars green; identical raise sets (`TB-012`)

- Run `scripts/acceptance.py` twice and confirm:
  - Planted-exception recall ≥ 29 of 32
  - Control precision 0 of 8
  - High-severity recall 18 of 18
  - Extras ≤ 3 unexplained per rule
  - Stability: identical raise sets across the two runs
  - Rule catalog coverage 24/24 wired
  - Zero-coverage rules: none
- Commit the report to `evidence/`.
- The stability bar requires two consecutive identical runs; that is the determinism proof for the acceptance run, not a separate claim.

### B.8 Close out the remediation map (`TB-013`)

- For every miss/extra row in `evidence/acceptance_remediation_2026-10-04.md`, mark it fixed / answered / documented-tuning.
- No row is closed as “passed” unless the command reproduced it.

---

## C. M2 — Gate visibility + quality infrastructure (do this so you can trust any “check green”)

### C.1 Fix the fail-fast gate defect (`GATE-FAST`, P0)

- Problem: `scripts/check.py` exits on the first failed bar; measured it exits 1 at Ruff Format and reports nothing after it, so the five doc-14 §5.3 bars are invisible.
- Required behaviour: the gate must report the full bar landscape / exit landscape, not stop at the first failure. The Ruff Format failure must not hide the acceptance bars.
- This is the single highest-value small change in the gate-tooling lane because it turns “which bar failed first” into “how many are red”, which is what a ship decision needs.

### C.2 Wire the quality gates into `scripts/check` (`TB-014`–`TB-019`, P1)

- `TB-014`: configure the import-linter engine-boundary rule (`app/engine/**` may not import `fastapi`/`pywebview`/`app.api`/`app.desktop`/`app.jobs`) and run it from `scripts/check`.
- `TB-015`: install `ruff`; add `[tool.ruff]` (format check + lint) to `pyproject.toml`; wire both steps into `scripts/check`.
- `TB-016`: install `mypy`; add strict config for `app/engine`; wire into `scripts/check`; fix what it finds (no `# type: ignore` escapes without a reason).
- `TB-017`: wire `eslint` + `tsc --noEmit` into the gate and confirm they actually run.
- `TB-018`: create ADR-002 pins (`.python-version`, `.nvmrc`, `uv.lock` or pinned `requirements.txt`) and use them in bootstrap.
- `TB-019`: create `scripts/dev` and `scripts/release` exactly as specified; clean-checkout test.

### C.3 Record a full green `scripts/check` transcript (`TB-022`, P1)

- Every step, exit 0, attached as gate evidence.
- This depends on `TB-014`–`TB-021` because the transcript must include the steps that were previously missing or failing.

### C.4 Measure `NFR-002` end-to-end ≤ 60 s for 250k rows incl. validation report (`TB-023`, P2)

- Record in `14 §8.2` baseline with the number, not an adjective.
- Optimise honestly if still over; do not paper over with a skip.

---

## D. M3 — S1 burn-down (`28 §12`, P0/P1)

Close per `28 §12`. Zero open S1 at UAT entry.

- `TB-030` (`DEF-015`): eliminate float money paths, mutation-verified. This is the last S1 that can reach a client number — money must be Decimal end to end.
- `TB-031` (`DEF-016`): replace the tautological UAT assertion with a real independent check.
- `TB-032` (`DEF-017`): register and run the `tst` marker.
- `TB-033` (`DEF-018`): read the client’s `.pptx` template (asset exists at `packaging/templates/FPAMonthEndCopilot_v1.pptx`).
- `TB-034`: close `DEF-012`/`DEF-014` — traceability chains complete (FR → spec → SCR → API → test).
- `TB-035`: close `DEF-011` consequence — rebuild installer with the now-present icon/template assets; attach evidence.

---

## E. M4 — Architecture alignment (close `09`’s dated gaps; P1/P2)

- `TB-025`: extract `app/jobs/` — worker thread, job registry with states/progress/ETA/cancellation (queue depth 1), per ADR-006; delete the ad-hoc server-thread coupling.
- `TB-026`: create `engine/common/` and consolidate duplicated money/period/hash helpers; add the single-implementation test. Depends on `TB-016`.
- `TB-027`: implement missing CLI commands — `import`, `validate`, `forecast`, `export-xlsx`, `export-ppt`, `migrate`, `report` — with documented exit codes and `--json`. Owning doc `09 §5.2`, Addon 2 §B.1.
- `TB-028`: make `bva` accept the filter-context contract and `doctor` run its real checks (DB integrity, disk, schema, WebView2, permissions) with `--json`.
- `TB-029`: code-health sweep — delete `analytics_repo_snippet.txt`, the 500-LOC check, zero commented-out code, `TODO` → `27` IDs.

---

## F. M5 — Phase-gate evidence packs (P0/P1)

- `TB-036`: assemble `GATE-07` evidence pack (import phase) per `16 §6.1`.
- `TB-037`: assemble `GATE-08`…`GATE-12` evidence packs in sequence; record approvals.
- `TB-038`: Playwright E2E golden path green on Windows in the packaged build.
- `TB-039`: cross-artifact consistency test green (`NFR-015`: UI = Excel = PPT = CLI, exact equality).
- `TB-040`: upgrade/migration test on the real prior-version fixture.
- `TB-041`: fresh-clone bootstrap transcript attached.
- `TB-042`: real-Windows-11 evidence run (install, launch, DPI, SmartScreen path, offline walkthrough).

---

## G. M6 — Pilot / UAT / go-live (P0/P1)

- `TB-043`: real-data pilot on one sanitized real month — full flow, no sample data; tie-out worksheet + classification log signed.
- `TB-044`: UAT — analyst + accounting owner, ≤ 5 days, zero open S1/S2, sign-off template signed.
- `TB-045`: record `GATE-13` approval (currently unsigned per `28 §4.6.5` and `00` line 386).
- `TB-046`: go-live checklist complete — installer + SHA-256 delivered, training run, backup/restore verified, rollback stated, support contacts agreed.
- `TB-047`: finalise `22` end-user guide + `29` client pack against the shipped build; training session delivered.

---

## H. Cross-cutting obligations that apply to every item above

- **Spec-first + quote-before-code** on every item (`19 §5.1`, `17 §1.2`).
- **Traceability** updated for touched FRs in `20_REQUIREMENTS_TRACEABILITY.md`.
- **Tests in the same change**; coverage bars hold (`14 §13.2`: engine ≥ 90%, backend ≥ 75%).
- **Money is Decimal**; no float in any money path; exact equality; one rounding policy; no epsilon (`17 §5.1`, `05 §13`).
- **Import atomic + nothing silently discarded**; rejected/quarantined rows appear with counts; control-total variance fails import by default with an explicit recorded-acceptance path (`04`, `03 §1.2`, `DEC-022`/`DEC-023`).
- **Error envelope**: typed, catalogued; no raw tracebacks to the user; user message from the catalog (`26 §5`, `08 §16`).
- **Engine boundary**: import-linter enforced by `scripts/check` (`09 §4.1`, `17 §4.1`).
- **Determinism**: stable output order; no wall-clock in machine payloads unless the contract requires one (then ISO-8601 UTC); no randomness in product paths; `--json` repeatable (`17 §5.4`).
- **Offline spine**: no network dependency except the optional AI client; AI never computes/decides/applies/sends (`10 §2.3`, `01 §6.3`).
- **Evidence discipline**: every “done” cites a command + raw result; citations resolve to opened `file:line`; uniform verdicts treated as warnings (`33 §5.10`).
- **No weakening tests/golden/thresholds**; expectations change only via the spec path with a `CHANGELOG` reason (`R7`, `14 §1.2 item 3`).
- **No commits/pushes/PR unless the owner explicitly asks in the session.**

---

## I. Open owner decisions that can block or reshape this list

- `DOC-02` canonical EULA/advisory disclaimer text — blocked on an owner ruling; `build.py` reports the blocker rather than inventing legal text.
- `DOC-08`/`GATE-13` approval — packet not yet assembled; an approval nobody has given is currently carried as if it gates release.
- The 8 handoffs authored by `antigravity` — that seat is AWAY, so the verification rotation cannot reach them; they need a documented disposition.
- The three acceptance OQs (`OQ-025`/`026`/`027`) are closed (`DEC-056`…`DEC-058`); `PROP-001` is approved (`DEC-059`). Re-measure the acceptance numbers yourself; do not trust the dossier’s per-bar figures as current.

---

## J. Completion criteria for this whole list (not “all green”, but the DoD)

Project completion is the **Definition of Done in `33 §2.1` (all ten must hold simultaneously)** plus the phase-gated path in `16` plus the acceptance/gate/verification/pilot chain:

- D1: Phase-0 checklist gates green (`GATE-01`…`05B`) + every Addon Coverage-Matrix row `INTEGRATED`.
- D2: all seven planted-exception bars pass on two consecutive identical runs.
- D3: `scripts/check` exits 0 with every ADR-002 step actually running.
- D4: coverage bars met and held (engine ≥ 90%, backend ≥ 75%).
- D5: every NFR measured with the number in the baseline table.
- D6: zero open S1/S2 at UAT entry; every defect classified fix/defer/backlog with rationale.
- D7: golden/oracle/cross-artifact tests green (`NFR-015`).
- D8: fresh-clone bootstrap transcript + real-Windows-11 evidence attached at every gate.
- D9: docs `00`–`32` complete, link-check green, zero stale claims.
- D10: real-data pilot tie-out signed, UAT signed, go-live checklist complete.

Until D1–D10 all hold with evidence attached, the project is not complete — regardless of how many task rows are ticked.

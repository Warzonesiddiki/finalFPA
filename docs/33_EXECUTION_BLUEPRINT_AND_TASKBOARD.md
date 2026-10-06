> **Status:** Draft v0.1 — living board (statuses change with the work, in the same commit)
> **Last updated:** 2026-10-05
> **Owning FRs/areas:** execution blueprint (workstreams + milestones), dated gap inventory, live taskboard (`TB-nnn`). Nothing else — facts stay in their owning documents.
> **TL;DR (≤ 15 lines):** This document is the **execution view** of the plan: §2 defines what "extreme
> perfection, zero compromises" concretely means (the project Definition of Done and the doctrine);
> §3 is the **dated, measured gap inventory** (every current shortfall with its evidence); §4 is the
> milestone sequence M0→M6 that closes those gaps in dependency order; §5 is the **taskboard**
> (`TB-001`…`TB-048` plus recently-closed work) with statuses and blockers; §6 are the operating rules
> for following it session to session. It owns no requirement: phases/gates/estimates stay in `16`,
> backlog in `27`, defects in `28`, open questions in `18`, test bars in `14` — on conflict those win.
> Order of work is deliberate: **owner decisions → acceptance green → gate green → S1 burn-down →
> architecture alignment → phase-gate evidence → pilot/UAT/go-live**, because money correctness and an
> honest gate precede every new feature (goal document, decision filter #1).

---

# 32 — EXECUTION BLUEPRINT & TASKBOARD

## 1. Purpose, ownership and conflict rule

| Question | Answer |
|---|---|
| What does this document own? | The blueprint (workstream map), the dated gap inventory (§3), the milestone sequence (§4), the taskboard `TB-nnn` (§5) and the operating rules for both (§6) |
| What does it **not** own? | Any FR, formula, threshold, screen, gate text or defect decision — those live in `02`, `05`, `06`, `08`, `14`, `16`, `27`, `28` and are referenced, never restated |
| Conflict rule | The owning document wins; `16` wins for anything phase-shaped; `27` wins for anything parked. This doc is a derived view and is corrected to match, never the other way round |
| Who updates it? | The same session that changes the underlying fact updates the board status — statuses never lag reality by a session |
| Relationship to `16` §1.3 | `16` §1.3 names the single next open item; §5 groups tasks by milestone. `TB-001`…`TB-013` **are** that pointer, decomposed |

## 2. The blueprint — what "extreme perfection, zero compromises" concretely means

Perfection here is not a feeling: it is a checklist of numbers and signatures that must all be true
at the same time, with evidence attached.

### 2.1 The Definition of Done (all ten must hold — simultaneously)

| # | Criterion | Source of truth |
|---|---|---|
| D1 | Every Phase-0 checklist gate green (`GATE-01`…`05B`, 66 checks) and every Addon Coverage-Matrix row `INTEGRATED` | `00` §4, §9 |
| D2 | **All seven planted-exception bars pass on two consecutive identical runs** (recall ≥ 29/32, controls 0/8, High 18/18, extras ≤ 3/rule, stability, 24/24 wired, zero zero-coverage) | `14` §5.3 |
| D3 | `scripts/check` exits 0 **with every ADR-002 step actually running** (ruff format+lint, mypy strict, eslint, `tsc --noEmit`, import-linter, pytest+coverage, contract, link-check) | `14` §13.1, `ADR-002` |
| D4 | Coverage bars met and held: engine ≥ 90 %, backend ≥ 75 % | `14` §13.2 |
| D5 | Every NFR **measured** (never assumed) with the number recorded in the baseline table | `14` §3/§8.2, Addon 3 §I.1 |
| D6 | Zero open S1/S2 at UAT entry; every defect classified fix/defer/backlog with rationale | `28` §3 |
| D7 | Golden/oracle/cross-artifact tests green (`NFR-015`: UI = Excel = PPT = CLI = engine, exact) | `14` §7 |
| D8 | Fresh-clone bootstrap transcript + real-Windows-11 evidence attached at every gate | Addon 4 §I.2, `ADR-005` |
| D9 | Docs `00`–`32` complete, link-check green, **zero stale claims** (a documented behaviour that code no longer has is a defect, per the DEF-010/DEF-030 precedent) | `00` §6, `30` §5 |
| D10 | Real-data pilot tie-out signed, UAT signed, go-live checklist complete | `28` §4–§5 |

### 2.2 The doctrine (how every task on this board must be executed)

1. **Never-cut list is absolute** — exact money math, atomic all-or-nothing imports, versioned audit,
   offline/local-only behaviour, the Windows installer + real-Windows validation, the advisory
   disclaimer, backup/restore, golden tests, cross-artifact equality (`16` §9.2).
2. **Spec first, quote before code** — no FR is built without citing it; behaviour changes hit the
   owning doc + `CHANGELOG` before any code (`19`).
3. **Deterministic money** — `Decimal` end-to-end, no epsilon comparisons (`05` §13/§G.1).
4. **Evidence or it did not happen** — every "done" cites a test, a transcript or a measurement file
   (`30` §4); measured numbers replace adjectives everywhere.
5. **No weakened gates** — never delete/skip a test, hardcode a number, or relax a bar to go green;
   if a bar is wrong, the *spec* changes first with an impact note (`19`, Addon 4 §E.3).
6. **Blocking questions get asked** — money semantics, data loss, UX flow or client facts stop the
   work with ≤ 3 options + recommendation + default (`19` §5 / Addon 2 §H.3); unanswered questions are
   on the board as 🚧, never guessed around.

### 2.3 Workstreams (every task belongs to exactly one)

| WS | Workstream | Owns | Gate |
|---|---|---|---|
| `WS-0` | Owner decisions & governance | OQ answers, approvals, impact notes | — |
| `WS-1` | Acceptance & sample data | corpus coherence, planted-exception bars, answer-key alignment | `14` §5.3 |
| `WS-2` | Quality infrastructure | `scripts/check` composition, lint/type wiring, pins, determinism | `GATE-07`+ precondition |
| `WS-3` | Architecture alignment | closing `09`'s dated gaps (jobs, common, CLI, code health) | `09` §17 |
| `WS-4` | Defect burn-down | open S1/S2 in `28` §3.2/§12 | release-blocking |
| `WS-5` | Phase-gate evidence | packs for `GATE-07`…`12` | `16` §5–§6 |
| `WS-6` | Pilot, UAT, go-live | real-data tie-out, sign-offs, checklist | `GATE-13`…`15` |

## 3. Gap inventory — dated, measured (2026-10-05)

Every row is a *verified* shortfall, not a suspicion; each carries its evidence and its target state.

| # | Gap (measured today) | Evidence | Target | Ref |
|---|---|---|---|---|
| `G-01` | Acceptance verdict **FAIL**: recall **11/32** | `evidence/acceptance_report.json` | ≥ 29/32 twice | `14` §5.3 |
| `G-02` | High-severity recall **6/18** (12 High plantings missed) | same | 18/18 | `14` §5.3 |
| `G-03` | Control precision **1 fired** (P30 `EXC-018` `IN01\|5200\|CC-110`) | same | 0 of 8 | `14` §5.3 |
| `G-04` | **422 extras** across 10 rules; 6 rules over the > 3 threshold (`EXC-017` 205, `EXC-018` 94, `EXC-019` 71, `EXC-006` 34, `EXC-021` 8, `EXC-022` 5) | same + `evidence/acceptance_remediation_2026-10-04.md` | ≤ 3 per rule, all justified | `14` §5.3 |
| `G-05` | **14 zero-coverage rules** (`EXC-001/002/003/006/008/009/010/012/013/014/016/020/021/024`) | `evidence/acceptance_report.json` | 0 | `14` §5.3 |
| `G-06` | `scripts/check` **exits 1**: 5 perf failures — the §5.3 bar tests, which now *measure* instead of skipping as BLOCKED | `scratch/check_run.log` | exit 0 | `14` §13.1 |
| `G-07` | `ruff`/`mypy` not installed; `pyproject.toml` has **no** `[tool.ruff]`/`[tool.mypy]` sections | `pyproject.toml` (only pytest/coverage sections) | ADR-002 steps running in the gate | `ADR-002` |
| `G-08` | ADR-002 pins missing: no `.python-version`, no `.nvmrc`, no `uv.lock`/`requirements.txt` | repo root listing | pins exist and bootstrap uses them | `ADR-002`, `09` §15.2 |
| `G-09` | Engine-boundary **import-linter rule not configured** (claimed as enforcement in `09` §4.1) | no importlinter config anywhere | rule configured and failing builds on violation | `09` §4.1 |
| `G-10` | `eslint`/`tsc --noEmit` steps not verified as part of the gate | `scripts/check.py` step list | both run in `scripts/check` | `14` §13.1 |
| `G-11` | CLI: **7 of 10** documented commands missing (`import`, `validate`, `forecast`, `export-xlsx`, `export-ppt`, `migrate`, `report`); `bva` is a two-amount calculator; `doctor` is a stub | `app/cli/main.py` | `09` §5.2 fully implemented | `09` §5.2, Addon 2 §B.1 |
| `G-12` | **`app/jobs/` does not exist** — no job registry, no progress/ETA/cancellation; only the API server thread in `app/desktop/shell.py` | repo tree | ADR-006 registry implemented | `ADR-006`, `09` §8 |
| `G-13` | **`app/engine/common/` does not exist** — money/period/hash helpers scattered (e.g. `imports/mapping_suggestions.py`), risking duplicated arithmetic | repo tree | canonical package per `09` §4.3 | `09` §4.3 |
| `G-14` | Stray file `app/engine/store/analytics_repo_snippet.txt` in a package (code-health rule) | repo tree | deleted; guardrail sweep clean | `09` §15.3 |
| `G-15` | `scripts/dev` and `scripts/release` do not exist | `scripts/` listing | both created and clean-checkout tested | `09` §15.4 |
| `G-16` | Open S1 defects: `DEF-015` (float money paths), `DEF-016` (UAT tautology), `DEF-017` (`tst` marker), `DEF-018` (PPT template not read), `DEF-012`/`DEF-014` (traceability), `DEF-011` consequence (installer rebuild with icon + template assets, which now exist) | `28` §12 | zero open S1 | `28` §3 |
| `G-17` | **`OQ-025`/`OQ-026`/`OQ-027` unanswered** — each caps the recall bar by construction (sub-ledger rejection makes P1/P9 unreachable; key divergences sink P2/P3/P6/P8; missing batch-37 fixture sinks P2) | `18` §4 | ✅ **closed 2026-10-05** — `DEC-056`…`DEC-058` | `18`, Addon 2 §H.3 |
| `G-18` | `PROP-001` (coherent corpus rebuild) proposed but not approved/run; 370 of 422 extras trace to actuals/budget drawn independently | `18_PROPOSAL_FOR_GENERATOR_REBUILD.md`, remediation evidence | ✅ **approved 2026-10-05** (`DEC-059`); execution pending (`TB-006`) | `18` |
| `G-19` | `NFR-002` ≤ 60 s end-to-end **not yet demonstrated** (commit alone measured 72.6 s for 250,040 rows) | `evidence/acceptance_remediation_2026-10-04.md`, bench | measured ≤ 60 s incl. validation report | `14` §8.2 |
| `G-20` | `.xlsx` corpus checksums nondeterministic (`openpyxl` stamps wall-clock `dcterms:created`), so the checksum scope had to exclude them | `DEC-055`, `14` §5.2 step 1 | normalised → checksums cover all 16+ files | `14` §5.2 |
| `G-21` | Phase-gate evidence packs for `GATE-07`…`12` not assembled; `GATE-13` unsigned (`28` §4.6.5; `00` line 386 shows Pending) | `16` §5.2, `28` §4.6 | packs attached + approvals recorded | `16`, `28` |
| `G-22` | Real-Windows-11 gate evidence (`ADR-005` checklist: install, launch, golden path, DPI, SmartScreen, offline) not yet attached to a gate | `09` §3.6 | checklist run + screenshots per gate | `ADR-005`, `15` |

## 4. Milestone sequence (dependency-ordered; derived from `16`, never overriding it)

| M | Milestone | Exit criterion | Depends on |
|---|---|---|---|
| **M0** | **Owner decisions ✅ (2026-10-05)** | `OQ-025/026/027` answered and recorded in `18` Decided with impact notes; `PROP-001` approved or replaced | owner |
| **M1** | **Acceptance green** | All seven `14` §5.3 bars pass on **two consecutive identical runs**; remediation map closed with a per-miss explanation | M0 |
| **M2** | **Gate green (quality infrastructure)** | `scripts/check` exits 0 with every ADR-002 step running; pins and determinism fixed; transcript attached | M1 (the 5 perf failures *are* the §5.3 bars) |
| **M3** | **S1 burn-down** | `28` §12 shows zero open S1; each closure reporter-confirmed per `28` §3.2 | M2 (fixes must pass the green gate) |
| **M4** | **Architecture alignment** | Every dated gap note in `09` is removed because the code now matches; `09` ↔ code audit clean | parallel with M2/M3 |
| **M5** | **Phase-gate evidence** | `GATE-07`…`12` evidence packs assembled and approved per `16` §5; E2E golden path + cross-artifact + fresh-clone + real-Windows evidence green | M1–M4 |
| **M6** | **Pilot → UAT → go-live** | Real-data tie-out signed, UAT signed with zero S1/S2, go-live checklist complete, `GATE-13`…`15` recorded | M5 |

**Rule:** nothing in M5/M6 starts while M1 is open — a red acceptance run is release-blocking
(`14` §5.2 step 6), and feature work ahead of a red gate is the exact failure mode the goal document
warns about (decision filter #3).

## 5. Taskboard

Statuses: ✅ done (with evidence) · ⬜ todo · 🚧 blocked (named blocker). **A task moves to ✅ only in
the same commit as its evidence.**

### 5.1 M0 — Owner decisions (`WS-0`)

| ID | Task | Ref | Status | Blocked by |
|---|---|---|---|---|
| `TB-001` | Answer `OQ-025`: unconditional debit=credit reject (spec) vs a tolerance path for amount-style sub-ledgers; decides whether P1/P9 plantings are reachable | `18`, `04` §12 | ✅ **scope by source type** (`DEC-056`) | — |
| `TB-002` | Answer `OQ-026`: which subject-key convention wins per rule (answer key vs `06` catalog) — P2/P3/P6/P8 | `18`, `06` | ✅ **catalog `06` wins** (`DEC-057`) | — |
| `TB-003` | Answer `OQ-027`: import-history fixture (batch 37 overlap + control-totals batch 039) | `18`, `03` §6 | ✅ **build the fixture** (`DEC-058`) | — |
| `TB-004` | Record all three answers in `18` **Decided** with date, rationale and impact note; update `CHANGELOG` | Addon 3 §B, Addon 4 §E.3 | ✅ `DEC-056`…`DEC-059` recorded | — |

### 5.2 M1 — Acceptance green (`WS-1`)

| ID | Task | Ref | Status | Blocked by |
|---|---|---|---|---|
| `TB-005` | Approve `PROP-001` (coherent corpus rebuild: actuals and budget drawn from one coherent model) or direct an alternative | `18_PROPOSAL_FOR_GENERATOR_REBUILD.md` | ✅ **approved, bundled** (`DEC-059`) | — |
| `TB-006` | Implement the approved corpus rebuild; regenerate; verify trial balance + byte-stable determinism (both proven this session, keep them proven) | `sample-data/`, `14` §5.2 step 1 | ⬜ | — |
| `TB-007` | Align P20/P21/P24 subject-key formats where rule and key disagree (key-format misses) | `evidence/acceptance_remediation_2026-10-04.md` | ⬜ | — |
| `TB-008` | Rule-by-rule diff and fix for the unexplained misses: P4b, P10×2, P12, P13×2, P14, P15b, P16 vs the `06` sample cases | `06`, remediation evidence | ⬜ | — |
| `TB-009` | Author P30's control case per `06` §7.2 F13c so precision lands at 0/8 by construction, not by random draw | `06` §7.2 | ⬜ | `TB-006` |
| `TB-010` | Build the import-history fixture (overlapping batch 37 + control totals) for P2/P3 | `03` §6, `04` §14 | ⬜ | — |
| `TB-011` | Make P1/P9 plantings reachable per the `OQ-025` ruling (load path + EXC-001/009 behaviour) | `04` §12, `06` | ⬜ | — |
| `TB-012` | Re-run `scripts/acceptance.py` **twice**; all seven bars green; identical raise sets; report committed to `evidence/` | `14` §5.3 | ⬜ | `TB-006`–`011` |
| `TB-013` | Close out `evidence/acceptance_remediation_2026-10-04.md`: every miss/extra row marked fixed / answered / documented-tuning | `30` §4 | ⬜ | `TB-012` |

### 5.3 M2 — Gate green: quality infrastructure (`WS-2`)

| ID | Task | Ref | Status | Blocked by |
|---|---|---|---|---|
| `TB-014` | Configure the **import-linter** engine-boundary rule (`app/engine/**` may not import fastapi/pywebview/app.api/app.desktop/app.jobs) and run it from `scripts/check` | `09` §4.1 (`G-09`) | ⬜ | — |
| `TB-015` | Install `ruff`; add `[tool.ruff]` (format check + lint) to `pyproject.toml`; wire both steps into `scripts/check` | `ADR-002` (`G-07`) | ⬜ | — |
| `TB-016` | Install `mypy`; add strict config for `app/engine`; wire into `scripts/check` — then fix what it finds (no `# type: ignore` escapes) | `ADR-002` (`G-07`) | ⬜ | — |
| `TB-017` | Wire `eslint` + `tsc --noEmit` into the gate (confirm they actually run today) | `14` §13.1 (`G-10`) | ⬜ | — |
| `TB-018` | Create the ADR-002 pins: `.python-version`, `.nvmrc`, `uv.lock` (or pinned `requirements.txt`) and use them in bootstrap | `ADR-002`, `09` §15.2 (`G-08`) | ⬜ | — |
| `TB-019` | Create `scripts/dev` and `scripts/release` exactly as specified; clean-checkout test | `09` §15.4 (`G-15`) | ⬜ | `TB-018` |
| `TB-020` | Perf suite green: the 5 failing bar tests pass because the bars do (never because they were skipped or weakened) | `scratch/check_run.log` (`G-06`) | ⬜ | `TB-012` |
| `TB-021` | Normalise `dcterms:created` in the `.xlsx` generators so all corpus checksums are deterministic | `DEC-055` (`G-20`) | ⬜ | — |
| `TB-022` | Full `scripts/check` transcript green (every step, exit 0) attached as gate evidence | `14` §13.1 | ⬜ | `TB-014`–`021` |
| `TB-023` | Measure `NFR-002` end-to-end (250k rows incl. validation report) ≤ 60 s; record in the `14` §8.2 baseline; optimise honestly if still over | `14` §8.2 (`G-19`) | ⬜ | `TB-022` |
| `TB-024` | Record remaining NFR measurements (cold start, interaction, PPT, Excel, memory, installer size) in `14` §8.2 with numbers, not adjectives | `14` §3/§8 | ⬜ | — |

### 5.4 M3 — S1 defect burn-down (`WS-4`)

| ID | Task | Ref | Status | Blocked by |
|---|---|---|---|---|
| `TB-030` | Fix `DEF-015` — eliminate float money paths (mutation-verified) | `28` §12 | ⬜ | `TB-022` |
| `TB-031` | Fix `DEF-016` — replace the tautological UAT assertion with a real independent check | `28` §12 | ⬜ | `TB-022` |
| `TB-032` | Fix `DEF-017` — register and run the `tst` marker | `28` §12 | ⬜ | `TB-022` |
| `TB-033` | Fix `DEF-018` — read the client's `.pptx` template (asset now exists at `packaging/templates/FPAMonthEndCopilot_v1.pptx`) | `28` §12, `12` | ✅ | — |
| `TB-034` | Close `DEF-012`/`DEF-014` — traceability chains complete (FR → spec → SCR → API → test) | `28` §12, `20` | ⬜ | — |
| `TB-035` | Close `DEF-011` consequence — rebuild the installer with the now-present icon/template assets; attach evidence | `28` §12, `15` | ⬜ | `TB-022` |

### 5.5 M4 — Architecture alignment (`WS-3`) — closes `09`'s dated gap notes

| ID | Task | Ref | Status | Blocked by |
|---|---|---|---|---|
| `TB-025` | Extract `app/jobs/`: worker thread, job registry with states/progress/ETA/cancellation (queue depth 1) per ADR-006; delete the ad-hoc server-thread coupling | `ADR-006`, `09` §8 (`G-12`) | ⬜ | — |
| `TB-026` | Create `engine/common/` and consolidate duplicated money/period/hash helpers into it; add the single-implementation test | `09` §4.3 (`G-13`) | ⬜ | `TB-016` |
| `TB-027` | Implement the missing CLI commands — `import`, `validate`, `forecast`, `export-xlsx`, `export-ppt`, `migrate`, `report` — with documented exit codes and `--json` | `09` §5.2, Addon 2 §B.1 (`G-11`) | ⬜ | — |
| `TB-028` | Make `bva` accept the filter-context contract and `doctor` run its real checks (DB integrity, disk, schema, WebView2, permissions) with `--json` | `09` §5.2, Addon 3 §C.7 (`G-11`) | ⬜ | — |
| `TB-029` | Code-health sweep: delete `analytics_repo_snippet.txt`, the 500-LOC check, zero commented-out code, `TODO` → `27` IDs | `09` §15.3, `17` (`G-14`) | ⬜ | `TB-014`–`017` |

### 5.6 M5 — Phase-gate evidence (`WS-5`)

| ID | Task | Ref | Status | Blocked by |
|---|---|---|---|---|
| `TB-036` | Assemble the `GATE-07` evidence pack (import phase) per `16` §5.2 | `16` §6.1 | ⬜ | M1–M4 |
| `TB-037` | Assemble `GATE-08`…`GATE-12` evidence packs in sequence; record approvals | `16` §6.2–6.6 | ⬜ | `TB-036` |
| `TB-038` | Playwright E2E golden path green on Windows in the packaged build | `14` §9.1, `ADR-005` | ⬜ | `TB-035` |
| `TB-039` | Cross-artifact consistency test green (UI = Excel = PPT = CLI, exact equality) | `14` §7, `NFR-015` | ⬜ | `TB-037` |
| `TB-040` | Upgrade/migration test on the real prior-version fixture | `24`, `14` §11 | ⬜ | — |
| `TB-041` | Fresh-clone bootstrap transcript attached (clean clone → check green, no machine-local state) | Addon 4 §I.2 | ⬜ | `TB-022` |
| `TB-042` | Real-Windows-11 evidence run: install, launch, DPI, SmartScreen path, offline walkthrough | `ADR-005`, `15` | ⬜ | `TB-038` |

### 5.7 M6 — Pilot, UAT, go-live (`WS-6`)

| ID | Task | Ref | Status | Blocked by |
|---|---|---|---|---|
| `TB-043` | Real-data pilot on one sanitized real month: full flow, no sample data; tie-out worksheet + classification log signed | `28` §6, Addon 4 §F | ⬜ | `TB-037` |
| `TB-044` | UAT: analyst + accounting owner, ≤ 5 days, zero open S1/S2, sign-off template signed | `28` §4 | ⬜ | `TB-043` |
| `TB-045` | Record `GATE-13` approval (currently unsigned: `28` §4.6.5, `00` line 386 Pending) | `28` §4.6, `00` §9 | 🚧 | `TB-043` |
| `TB-046` | Go-live checklist complete: installer + SHA-256 delivered, training run, backup/restore verified, rollback stated, support contacts agreed | `28` §5 | ⬜ | `TB-044` |
| `TB-047` | Finalise `22` end-user guide + `29` client pack against the shipped build; training session delivered | `22`, `29` | ⬜ | `TB-044` |
| `TB-048` | `12` §5.2 “template carries both bridge variants as two shapes, engine deletes the unused one” — **owed until python-pptx exposes `XL_CHART_TYPE.WATERFALL`**. The pinned version has none (verified against the installed enum), so the template ships only the stacked-column fallback. Unblocked by a python-pptx release that adds native waterfall; until then `SPK-08`'s stacked variant stays the active one and the second shape must not be fabricated. **Blocks:** nothing (fallback is documented and shipped); **Revisit at:** each dependency bump | `12` §5.2, `SPK-08`, `12` §3.6 | ⬜ | `TB-020` |

### 5.8 Recently closed (✅ — evidence attached; listed so the board shows what actually changed)

| ID | Task | Evidence |
|---|---|---|
| `TB-090` | DEF-030 bulk load rewritten to batched parameterised `INSERT` in one transaction | 3,717 rows/s (15×); 250,040-row commit 72.6 s; `tests/unit/test_def030_bulk_insert.py` (rollback mutation-verified) |
| `TB-091` | Corpus reproducible from the generator alone (measured balancing legs) **and** byte-stable | `scripts/verify_trial_balance.py` → `PASS - PERFECT BALANCE`; sha256 before/after regeneration identical for all 5 CSVs (2026-10-05) |
| `TB-092` | Baseline period-window fix (no unplanted future-dated rows) | EXC-011 extras 20,691 → 1; total extras 21,112 → 422 |
| `TB-093` | Acceptance harness honesty fixes (stale DEF-010 wording removed, measured consequence stated) | `app/engine/rules/acceptance.py`; `tests/rules/` 39 green |
| `TB-094` | DEF-010: unconditional `IMP-023` reject + batch metadata cannot contradict the store | `tests/unit/test_def010_batch_metadata.py` (mutation-verified 3/3) |
| `TB-095` | DEF-019 double-entry corpus rebuild (balanced legs, plants preserved) | `tests/unit/test_def019_double_entry.py` |
| `TB-096` | Five missing rule evaluators implemented → 24/24 catalog rules wired | `evidence/acceptance_report.json` (coverage bar passes) |
| `TB-097` | Planted-exception harness exists and measures all bars (DEF-009) | `scripts/acceptance.py`; verdict FAIL measurable, exit 1 — no bar skipped |
| `TB-098` | Doc 09 perfection pass: module map, CLI status, measured evidence, cross-ref fixes | this doc `G-07`–`G-15` rows; `CHANGELOG` 2026-10-05 |
| `TB-099` | **`DEF-018` (S1) — deck is now a filled copy of the template (AddOn 6 v2 `WC-2`, `ADP-001`/`002`/`003`)** | all six builders resolve shapes **by name** from `FPA-PPT-001`…`006`; `app/engine/pptx_fill/` (95 % cov, 82 new tests); 103/103 contract names resolve per slide; footer/chip/accent name mismatches and the **fabricated bridge tie-out** (₹500,000 residual now an explicit `Other (unexplained)` step; bar tops 15,770,000 → 16,645,000) fixed; `843 passed, 16 deselected`; `license_gate.py` PASS (5 adapted headers); `DEC-065`, `TB-048`; `CHANGELOG` 2026-10-05 |
| `TB-100` | **`WC-1` closed as BUILD — `app/engine/dedupe/` is the single implementation behind `EXC-007`/`EXC-008` (Addon 6 v2 `WC-1`, `BD-001`; `DEC-066`, `ADR-014`)**, and the `docs/18` register was repaired in the same session (`DEC-063` reconstructed, the duplicated `DEC-064` row removed, `D-13`) | catalog source `WS-01` measured dead (404, git exit 128 → Tier C STOP → owner chose BUILD; `evidence/wc1/ws01-escalation-packet.md`); `app/engine/dedupe/` (`normalize.py`, `blocking.py`, `__init__.py`) extracted as our own code — **no `Adapted from` header**, nothing adapted (E8/L2); `rules_01_08.evaluate_exc_001` + `rules_catalog_001_008.evaluate_catalog_exc_008` rewired through it (`R12`); `tests/unit/test_dedupe.py` (41 tests, **100 %** statements/branches on the package); acceptance re-measured **identical to baseline**; records `BD-001` (`32` §2), `DEC-066` + `D-13` (`18`), `ADR-014` (`09` §3.15); `CHANGELOG` 2026-10-05 |

| `TB-101` | **Team layer hardened: handoffs must declare their real blast radius, and a verification must test the deliverable** (five agents, one checkout) | `team.py check` now (a) FAILs a handoff whose required section is a stub, (b) FAILs/WARNs on files changed inside a claim window but missing from `## Changed` (caught 7 undeclared files in `HO-010`, 4 in `HO-012`, 2 in `HO-009`), (c) WARNs when a docs-only handoff is verified only by `team.py check`; `team.py reject` added so a handoff can be sent back with required actions and the author's claim is re-armed (used on `TB-007`, `TB-016`, `TB-017`, `UX-01`, `RV-01`); per-agent **streams** in `team/config.json` drive `team.py leader`; subagent fan-out rules in `team/README.md` §11; the `R12` guard (`tests/unit/test_engine_common.py`) was itself corrected — `@overload` stubs are declarations, not implementations — with a self-test proving a second real body is still caught |

| `TB-102` | **Non-stop supervision loop (`OPS-01`): the board is checked and acted on every 20 minutes, not only when a human looks** | `scripts/team_watchdog.py` (stdlib only, no new dependency) ticks on the owner's cadence: regenerates the generated views, runs `team.py check`, classifies every seat (idle with claimable work / blocked / stream dry / claim past TTL / handoff waiting over 30 min for a verifier / board complete), and applies only four **idempotent, logged** action kinds - `nudge`, `escalate`, `draft`, `done` - into the agents' inboxes and the owner's. It is structurally unable to verify, accept or commit: `apply()` refuses any other kind and logs the refusal, proven by `tests/unit/test_team_watchdog.py` (10 tests, incl. the refusal test and the cooldown/idempotence rules). Cadence lives in `team/config.json` `watchdog`; state in `team/log/watchdog-state.json`; every decision in `team/log/watchdog.log`; `team/log/watchdog.stop` ends the loop, and the loop also ends itself when no card and no P0 remain |

| `TB-103` | **Continuity layer: the memory an agent keeps, the knowledge the team keeps, and a brief a cold agent can resume from after a daily limit ends** (`memory/`, stdlib only) | `scripts/memory.py` records to **append-only JSONL journals** (`memory/journal/memory.jsonl`, `knowledge.jsonl`) under an `O_EXCL` lock, and *renders* `memory/MEMORY.md` (what is true now), `memory/KNOWLEDGE.md` (what we learned), `memory/RESUME.md` (the cold-start brief) and `memory/agents/<seat>.md` (one per seat) between `BEGIN/END GENERATED` sentinels, so a concurrent append can never lose an entry and hand-written prose survives every render. `python scripts/memory.py resume --agent <seat>` prints the brief **plus** live state recomputed on the spot: claims, blockers, dependency-blocked cards, that seat's stream in order, whether the seat is parked, and the traps already paid for. Lock staleness is decided by mtime age, **not** a pid probe, because `os.kill(pid, 0)` *terminates* on Windows. `memory.py verify` is a real gate - it fails on a duplicate id, an unknown agent, a bad kind/topic, an empty entry, a missing `RESUME` section, a missing per-seat log or an empty journal - and `memory.py prompt` prints the standing prompt for a seat. **30 tests** in `tests/unit/test_memory.py`, including a 5-process concurrent-append test, a falsification test per `verify` check, and a test that a subprocess cannot write into the production journal. `memory/` is excluded from the `team.py` claim-window scan for the same reason `team/` and `scratch/` are - every agent writes it by design - and its integrity is gated by `memory.py verify` instead |

| `TB-104` | **False evidence found and stopped: three audits that measured nothing, and the two tokeniser gaps that hid them** | Verification of `HO-031`/`HO-033`/`HO-035` (UX-08 a11y, UX-09 twelve numbers, UX-10 error catalogue) **rejected all three**. `scripts/audit_accessibility_matrix.py` is 109 lines whose audit table is a *string literal from line 37*; it never opens a `.tsx`. Four cited lines were opened by hand and all four were wrong: `ui/src/main.tsx:145` is an `<h1>`, `PreScanModal.tsx:1` is an `import`, `CheckScreen.tsx:2` is a docstring, and `BulkActionBar.tsx:15` - the single "real defect" - is a `useState`. 42 rows reading "Conforming" were never measured. `scripts/verify_audit_citations.py` could not catch any of it: it concatenates `docs/*.md` and tests whether `SCR-`/`FR-`/`CALC-` id strings appear somewhere in them, and **never resolves a `file:line` code citation at all**. Two real defects in the coordination layer were found and fixed while verifying: (1) the `## Changed` tokeniser split on the commas *inside* a brace group, so `sample-data/import_history/{01.csv,02.xlsx}` was declared as `{01_bank_batch_037.csv` and FAILed as a non-existent path - brace groups are now expanded before splitting (`_expand_braces`); (2) `.xlsx` was missing from the extension allowlist, so **33 of the 55 files under `sample-data/` could not be declared at all** - the gate was blind to exactly the lane that changes them most; the allowlist now covers `xlsx|xlsm|xls|parquet|duckdb|db|pptx|docx|pdf|svg|png|jpe?g|gif|webp|zip`. Regression: `tests/unit/test_team_changed_paths.py` (14 tests - 10 cases, one parametrised over 5 rejection inputs, one on the rejected-handoff rule). Systemic fix is now on the board as `UX-14` (a checker that can fail), `ENG-05` (retire the four generators that print a literal), `SPEC-08`/`DOC-05` (the acceptance standard), `LEAD-01` (the false-evidence register) and `LEAD-02` (verification was the measured bottleneck: 20 handoffs waiting) |

| `TB-105` | **The citation opener: the one command that turns "cited" into "measured"** (`LEAD-03`, `scripts/open_cited_lines.py`, stdlib only) | `TB-104` was caught by a human opening four cited lines by hand; that step is now a command. `python scripts/open_cited_lines.py <report.md>` finds the `file:line` citations a report makes, opens each one, prints the line that is actually there, and compares the backticked `key="value"` claims sitting beside the citation against it — `--handoff HO-nnn` follows a handoff to its evidence, `--limit 0` sweeps every citation, `--context N` and `--json` are available. Exit `0` only when every sampled citation resolved *and* every claim token is on its cited line; exit `1` when a citation is wrong, missing or out of range; and a report that cites **no** source line fails rather than passing vacuously. Run against the rejected trio: `HO-031` exit 1 (four files real, four line numbers in range, four lines carrying none of the claimed attributes) and, deeper than the original rejection, **`aria-` occurs 0 times across all 60 `.tsx` files in `ui/src`** — the 42 `Conforming` verdicts assert attributes that exist nowhere, so every screen in that matrix is in fact `NOT AUDITED`; `HO-033` exit 1 (names `app/engine/calc/math.py` on all twelve rows, never a line); `HO-035` exit 1 (cites no source file). **Correction, 2026-10-05T19:5xZ:** `hermes` has since rewritten `evidence/ux/a11y-keyboard.md` in this shared checkout — the fabricated rows are gone and every screen now reads `NOT AUDITED` with a derived `FAIL`. So `HO-031` **still exits 1**, but now as *"cites no file:line at all"* rather than as four mismatches: an honest gap instead of an invented pass, which is progress and **not** completion. The file is untracked in git, so the pre-rewrite version cannot be recovered and the original four-line run cannot be reproduced; `evidence/ops/lead-03-citation-audit.md` deliberately reports only the current state and points at `HO-031`'s `### Rejected by` block for the historical record. The `aria-` = 0 finding still reproduces and is measured at generation time. Because a gate that can only fail proves nothing, two fixtures ship: `evidence/ops/lead-03-control-fixture.md` (exit 1, real file, in-range non-blank line, wrong claim — the case existence-and-range checks pass) and `lead-03-honest-control.md` (exit 0). **34 tests**, five of which are falsification or false-green guards, the load-bearing one being `test_passing_report_fails_when_the_cited_line_changes` — the `HO-031` rejection turned into an assertion. The command also caught two defects in its own author: a `FILE_MISSING` row printed "absent: none — all present", a false green for a line never opened; and fenced code blocks were being scanned, so a document quoting an audit failed its own tool. Follow-on: `LEAD-01` and `LEAD-02` |

| `TB-106` | **The false-evidence register: one row per rejected handoff, with the pattern it failed on (`LEAD-01`, `scripts/false_evidence_register.py`)** | `TB-104` rejected three audits and left a follow-on asking for a register, on the reasoning that the pattern should be visible instead of recurring. It is a **generator, not a document**, because a hand-written register is a snapshot that starts lying the moment somebody is rejected: the roster is derived on every run from the handoffs that actually carry a `### Rejected by` block, and each one's evidence is re-audited *at generation time* by `scripts/open_cited_lines.py` (`TB-105`), so the register carries a measured verdict rather than a remembered one. `python scripts/false_evidence_register.py --check` fails if it has drifted. Measured: **10 rejected handoffs, 5 patterns** - and the largest pattern is *not* the one the card was written about. **Hidden blast radius** (`## Changed` listing one file while the claim window showed four to seven) occurred **4 times** (`HO-003`, `HO-010`, `HO-012`, `HO-013`) and was caught by hand every time; **literal generators** occurred 3 times (`HO-031`/`033`/`035`); then written-outside-scope, checker-cannot-fail and spec-code-drift once each. Three deliberate refusals, because each is the way this kind of file rots: (1) an **unclassified rejection is a hard error**, not a silent omission, since a pattern nobody has looked at is precisely what the file exists to surface; (2) a **pattern entry keyed on a handoff that is not rejected** is a row that can never recur; (3) the citation audit is applied only to the evidence-quality patterns, because running it over a blast-radius rejection produces a technically true and entirely useless verdict ("the test file cites no source line"). The register also carries no `file:line` claim of its own, so `open_cited_lines.py` reports it as citing nothing - the correct verdict, since every number in it is computed rather than asserted. The generalised rule it records: **a generator whose output does not change when its input changes is a printer, not a generator.** 14 tests, the load-bearing one asserting that an unclassified rejection fails the build. `LEAD-02` makes `open_cited_lines.py` a required reviewer command |

| `TB-107` | **Verification is a rotating duty, not a role (`LEAD-02`, `scripts/verification_queue.py`, `team/README.md` §6.1)** | `LEAD-02` claimed "20 handoffs were waiting for a verifier while seats had claimable work". Measured: **26 waiting, median wait 317 min (5.3 h), max 417, 20 over a 30-min service level, 2 distinct verifiers, 92% load concentration** — `antigravity` (11) and `buffy` (1), with `freebuff2`, `hermes`, `opencode` and `opencode2` never having verified anything at all. The root cause is one sentence in `team/README.md` §6: *"the default reviewer for money-path changes is `antigravity`"*. Naming a default reviewer made verification a **role** rather than a **duty**, so it concentrated with tenure and then failed to redistribute when that seat's quota ended on 2026-10-05. The fix is a queue (`python scripts/verification_queue.py`, `--for <seat>`, `--stats`, `--json`) that assigns by **least-recently-verified first** and refuses four things, each because breaking it produced a real failure here: never an `AWAY` seat, never the author (which `team.py verify` forbids anyway), never the same two people twice running (plain FIFO keeps the concentration where it is), and never a verdict without a service level (`--sla`, default 30 min, matching the watchdog threshold). A **rejected** handoff is excluded from the queue — it waits for its author, not a verifier, and counting those would have inflated the bottleneck from 26 to 36 and hidden the real one. Over today's backlog the rotation proposes **7 / 7 / 7 / 6** across the four active seats. **The after-figure is deliberately not claimed**: the mechanism landed minutes before measurement, so what is measurable is the *proposed* distribution, and the wait time is a follow-up measurement — reporting an improvement before it is observed is the habit `TB-105`/`TB-106` exist to prevent. 18 tests (14 at handoff; 18 after the completion check added four `--for` CLI tests — the path a seat actually types, and the one where the AWAY refusal has to survive), including the falsification case where one seat wrote the only handoff and the queue reports *no eligible seat* rather than proposing a self-verification |

| `TB-108` | **Release-readiness dossier, generated from live gate runs (`DOC-03`, `scripts/release_dossier.py`)** | The card asked for one page the owner can read to decide ship or not: every gate with its **real** exit status, open decisions with their blast radius, licence posture with the git SHA, and known limits as numbers — no adjectives, every line traceable to the command printed beside it. It is a **generator**, not a document, because a hand-written readiness dossier is the most dangerous file in the repo: it is read at ship time, gets composed while the answer is "not yet", and then sits unchanged for weeks after the answer moves. `--check` exists for the same reason the false-evidence register has one (`TB-106`). **Measured: 3 of 9 gates red** — `RUFF-LINT` 1, `RUFF-FORMAT` 1, `ACCEPTANCE` 1, against green `LICENCE`, `DOC-INTEGRITY`, `MEMORY`, `EVID-REGISTER`, `TEAM-CHECK` and the **full unit suite** (472.6 s). Both ruff reds are pre-existing and repo-wide; every file added this session is ruff-clean and was checked individually. **The finding worth more than the dossier:** `scripts/check.py` line 12 calls `sys.exit(res.returncode)` on the **first** failed bar, so it is fail-fast. Measured, it exits 1 at Ruff Format and reports nothing after it — which means the five `docs/14` §5.3 bars (recall 11/32, control 1 fired, High 6/18, 422 extras, 14 zero-coverage rules) are currently **invisible**. They are not passing; nobody can tell, because the gate stopped. A fail-fast gate answers *which* bar failed first, while a ship decision needs *how many* are red — different questions, and only the second is decision-relevant. The dossier therefore **never short-circuits** and says so in its own output. This is the same shape as the fabricated audits in `TB-104`: one uniform verdict standing in for a population nobody examined. Also measured: `evidence/open_decisions.md` declares 18 tracked decisions and lists 2, so the register does not deliver its own count. 11 tests, the load-bearing one proving a red first gate does not hide the three behind it |

### 5.10 What "verified" has to mean on this board

The `TB-104` rejection is the third this project in which an artefact reported success it had not
measured. The rule that follows, and that `SPEC-08` and `DOC-05` exist to write down properly:

> A deliverable is verified when **a command recomputes its numbers from the subject**, not when a
> document describes it, a generator prints it, or a checker greps a different directory than the
> claim is about. A checker that cannot resolve what it claims to verify is not a check.

Applied day to day:

1. **Uniform verdicts are a warning, not a result.** "43 of 43 conforming" and "12 of 12 verified"
   are the shape of an unmeasured claim. A real audit has a spread and some `NOT AUDITED`.
2. **A citation is a lookup, not a decoration.** Open the line. `file:line` that lands on line 1 or on
   an import is the tell.
3. **Every guard ships with a falsification test** that proves it still fails on a real violation.
   A gate that cannot fail is a claim, not a gate.
4. **An honest gap beats a completed row.** `NOT VERIFIED - <reason>` is an acceptable deliverable;
   a green tick that nobody measured is not.

### 5.11 Continuity layer (read this before a session, not after)

`memory/` is the third record, alongside `docs/` (what is specified) and `STATE.md` (what is true).
Before starting work, and **always before a session ends for any reason**, run:

```bash
python scripts/memory.py resume --agent <seat>   # cold-start brief + live state
python scripts/memory.py add --kind state|decision|blocker --text "..." [--ref path]
python scripts/memory.py learn --topic trap|tooling|windows|domain|gate|product|process --text "..."
python scripts/memory.py render && python scripts/memory.py verify   # verify must exit 0
```

`python scripts/memory.py prompt` prints the standing instruction to give a seat. `memory/README.md` is
the architecture; the journals are the source of truth and the markdown is a rendered view, so a
hand-edit inside a `BEGIN/END GENERATED` block is lost by design.

### 5.12 The reviewer command: `scripts/open_cited_lines.py` (`TB-105`)

`§5.10` rule 2 says a citation is a lookup, not a decoration. As of `TB-105` that is a command
rather than an intention:

```bash
python scripts/open_cited_lines.py <report.md>           # four citations, the default
python scripts/open_cited_lines.py <report.md> --limit 0 # sweep every citation
python scripts/open_cited_lines.py --handoff HO-nnn      # follow a handoff to its evidence
python scripts/open_cited_lines.py <report.md> --context 2 --json
```

Reading the result:

* **exit 0** — every sampled citation resolved *and* every claim token is on its cited line.
* **exit 1** — a citation is wrong, missing, blank or out of range; or the report cites no source
  line at all, which is a failure and not a pass.
* **`cited only, nothing checked`** — the row carries no backticked `key="value"` claim. It is
  *cited*, not measured. Inventing a claim to check would manufacture failures in honest reports,
  so the tool reports the gap instead of filling it.
* **`INCONCLUSIVE`** — every citation resolved but nothing on any cited line was checkable.

What it does not do, and the limit worth remembering: it proves a claim is **on** a line. It cannot
prove the line is the **right** line for the claim — that still takes a reader. It removes the
possibility of an unchecked claim, not the possibility of a wrong one.

`LEAD-02` exists to make this a required step in the reviewer rotation; `SPEC-08` and `DOC-05` own
the written acceptance standard.

### 5.13 The false-evidence register (`TB-106`)

`evidence/ops/false-evidence-register.md`, regenerated by
`python scripts/false_evidence_register.py` and staleness-checked by `--check`. One row per
rejected handoff: card, author, who rejected it, the pattern it failed on, and — for the
evidence-quality patterns — what `open_cited_lines.py` says about that evidence **now**.

Read it when about to reject something, so the answer is a row rather than a fresh argument. The
rule it exists to keep visible:

> A generator whose output does not change when its input changes is a printer, not a generator.

Three ways this kind of file rots, each refused deliberately and each covered by a test:

1. **An unclassified rejection is a hard error.** A new pattern nobody has looked at is the whole
   point of the file; omitting it quietly turns the register into a list of the patterns we already
   knew about.
2. **A pattern entry for a handoff that was never rejected** is a row that can never recur.
3. **A verdict where no verdict applies.** The citation audit is meaningful only for failures about
   evidence quality. Applied to a blast-radius rejection it yields "the test file cites no source
   line" — true, and useless. Those rows read `n/a`.

Measured across ten rejections, ranked by what would have caught the most on first run:

| Would have stopped | Rejections | Status |
|---|---|---|
| `open_cited_lines.py` — open the cited line | `HO-031` outright, `HO-033`/`HO-035` as uncited | shipped (`TB-105`) |
| `## Changed` vs claim window (`team.py check`) | `HO-010`, `HO-012`, `HO-013`, part of `HO-025` | shipped, but **WARNs** — making it FAIL is the highest-value small change left |
| claim-window scan | `HO-025` | shipped (`TB-101`) |
| spec-to-code constant check | `HO-006` | **does not exist** — caught by a human reading two files |

That last row is the honest reason this is a register and not a solved problem.

### 5.9 Board reconciliation — `INT-01` (2026-10-05)

`docs/33` is the spec of record; `team/taskboard.md` is the board that actually runs the work. Measured this
session: **61 `TB` rows** in this file, **43 live `TB` cards**, and
**0 cards with no row here** — the board is a deliberate subset of the spec, which is the
healthy direction. Two kinds of drift do need fixing, and both are recorded here rather than left implicit.

**1. Cards verified `done` whose row here still reads open** (a reader of this file would think the work is
outstanding):

- `TB-008` — Rule-by-rule diff and fix for the unexplained misses: P4b, P10×2, P12, P13×2, P14, P15b, P16 vs … → **closed 2026-10-05**, evidence in the card's handoff.
- `TB-014` — Configure the **import-linter** engine-boundary rule (`app/engine/**` may not import fastapi/pyw… → **closed 2026-10-05**, evidence in the card's handoff.
- `TB-015` — Install `ruff`; add `[tool.ruff]` (format check + lint) to `pyproject.toml`; wire both steps int… → **closed 2026-10-05**, evidence in the card's handoff.
- `TB-018` — Create the ADR-002 pins: `.python-version`, `.nvmrc`, `uv.lock` (or pinned `requirements.txt`) a… → **closed 2026-10-05**, evidence in the card's handoff.
- `TB-026` — Create `engine/common/` and consolidate duplicated money/period/hash helpers into it; add the si… → **closed 2026-10-05**, evidence in the card's handoff.
- `TB-030` — Fix `DEF-015` — eliminate float money paths (mutation-verified) → **closed 2026-10-05**, evidence in the card's handoff.

**2. `TB` rows with no live card** - two different situations, deliberately separated:

  (a) *real queue rows nobody owns* (14): `TB-001`, `TB-002`, `TB-003`, `TB-004`, `TB-005`, `TB-090`, `TB-091`, `TB-092`, `TB-093`, `TB-094`, `TB-095`, `TB-096`, `TB-097`, `TB-098`.
  (b) *closure records* (8): `TB-099`, `TB-100`, `TB-101`, `TB-102`, `TB-105`, `TB-106`, `TB-107`, `TB-108` - these were written as done-log rows (what landed and the measured numbers), not as queue items, so having no card is correct by design and must not be "fixed" by creating one.

  For (a) the rule is that a row nobody tracks cannot be claimed, so each is one of three things and must be
  resolved by a decision, not by silence: still real -> `python scripts/team.py sync` creates the card and an
  agent claims it; superseded by a `DEC` (several were closed by `DEC-056`…`059`) -> annotate the row;
  deliberate deferral -> annotate the condition that re-opens it. Follow-up: re-run `sync` for the rows whose
  subject is still unimplemented and annotate the rest.

## 6. Operating rules (how the board is followed)

1. **Session start** reads, in order: `python scripts/team.py status` → `team/digest.md` (four-agent team
   layer; `team/README.md` is normative and its **claims** decide who may write what) → `00_INDEX` →
   `CHANGELOG` since last session → `SESSION_LOG` tail →
   `16` §1.3 → **this board's open milestone** (`19` / Addon 4 §B.2).
2. **Status changes ride the same commit as the work.** A task marked ✅ without its evidence path is
   a protocol violation, exactly like an unrecorded approval (Addon 4 §E.2).
3. **New work lands here first** (or in `27` if parked) — if it is not on the board or in the backlog,
   it does not exist (Addon 3 §H).
4. **Blocked tasks name their blocker** (usually an owner question). Never work around a 🚧 on money
   semantics; ask the ≤ 3-option question (`19` §5).
5. **Milestone order is the order.** M1 precedes feature/gate work because `14` §5.2 step 6 makes a red
   acceptance run release-blocking; jumping ahead requires an explicit waiver recorded per `16` §5.3.
6. **Re-baseline at every gate:** gap inventory §3 is re-measured (numbers, not opinions), closed rows
   move to §5.8, and `16` §7 re-estimates with variance reported (Addon 4 §D.5).

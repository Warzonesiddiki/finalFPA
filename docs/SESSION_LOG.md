# SESSION LOG

Append-only memory bridge between sessions (Addon 1 §M.1, Addon 4 §B.4). Newest entry at the top.
Every entry records: what changed, which FRs/areas were touched, test results, the next step, and
anything deferred to the backlog or the open-questions log.

**Do not edit past entries.** If a past entry was wrong, correct it with a new entry that says so.

---

## Session 001 — 2026-10-01

### Objective

Start Phase 0 on a clean repository: create the skeleton and begin the documentation set, with **no
product code** (Addon 4 §L, steps 1–2).

### What changed

| File | Change |
|---|---|
| `README.md` | Rewritten: product summary, current phase (Phase 0, no code), repo layout, spec-of-record summary (kickoff + Addons 1–4), non-negotiable working rules |
| `docs/`, `app/`, `ui/`, `sample-data/`, `tests/`, `packaging/`, `scripts/` | Created with `.gitkeep` (skeleton only — Kickoff §5 "Repo skeleton") |
| `docs/00_INDEX.md` | **New.** Document map (30 docs + 2 process files), reading plans incl. the mandatory session reading plan, Addon Coverage Matrix (64 rows), Source-of-Truth Matrix, document standard + header template, hygiene/conflict rules, ID registry (25 prefixes), 5-gate/58-check tracker, approval log |
| `docs/01_PRD.md` | **New.** Personas (4 + exclusions), monthly-rhythm JTBD, scope in/out (10 areas in, 24 parked items), forced in/out rulings, 10 success metrics with targets, multi-entity and pack-audience stances, no-login/no-RBAC decision, constraints, 20 labelled assumptions, 10 risks, canonical advisory disclaimer, IP/licensing stance, branding defaults, `DEC-001`–`DEC-019` index |
| `docs/02_FUNCTIONAL_SPEC.md` | **New.** 156 numbered FRs in 11 families, each with priority (P0/P1/P2), phase, behaviour, inputs/outputs, edge cases and testable acceptance criteria; priority + cut-line policy incl. the never-cut list; per-FR DoD; screen touchpoints; 13-row canonical edge-case matrix with message slugs |
| `docs/03_DATA_DICTIONARY.md` | **New.** Two-store model (DuckDB analytics / SQLite workflow), type + money rules, nullability and identity conventions, grain register (35 tables), full column specs, dedup keys, 15 integrity invariants, example rows, on-disk layout, volume estimates, supersessions, schema-versioning rules |
| `docs/04_SOURCE_MAPPING_AND_IMPORT_SPEC.md` | **New.** 9 source types, 7-step wizard, template versioning, mapping profiles (fingerprint auto-match, versions, mid-year changes), per-profile parsing rules, 26 Excel + 12 CSV hardening cases, 32-check validation catalogue (`IMP-001`…`IMP-032`), reject-vs-quarantine rule, reconciliation, duplicates, incremental loads, atomic commit/recovery, score inputs, validation report, batch lifecycle/void, error-copy standard |
| `docs/05_CALCULATION_SPEC.md` | **New.** All formulas: windows (MTD/YTD/PY/TTM), sign conventions, variance/%/favour*ability*, pp-vs-percent, KPI library, rounding + sum-of-rounded rule, scale/negatives, grain and rollup invariants, data-quality score, 4 forecast methods' arithmetic, accuracy metrics, control-total variances, materiality AND-test, tolerance policy, formula register — with **14 golden fixtures / 36 assertions, all verified computationally** |
| `docs/06_EXCEPTION_RULES_CATALOG.md` | **New.** Engine model (identity/re-run, statuses, severity SLAs, aging, owner auto-assign, degradation, effective thresholds, implementation contract) + **24 fully specified rules** with 13 fields each + dependency matrix + enablement defaults + **40-planting sample plan (32 raises, 8 precision controls)** + false-positive management + effectiveness analytics + change control |
| `docs/07_FORECAST_METHODS_SPEC.md` | **New.** Forecast lifecycle, eligibility guards, method resolver, scenarios, version lifecycle/locks, accuracy report, method-choice guidance, overrides, 8 integrity guarantees, worked example, config reference |
| `docs/08_UI_UX_SPEC.md` | **New.** IA + guided nav, global shell, **43-screen inventory** (`SCR-001`…`SCR-043`), screen-by-screen specs with 6 ASCII wireframes, **12-chart inventory** (`CHT-`), **12 centralized conditional-format rules** (`CF-`) with non-colour signals, display-formatting contract, message-catalog/wording rules, per-screen state matrix, WCAG AA accessibility baseline, design system/tokens, change control |
| `docs/10_AI_INTEGRATION_SPEC.md` | **New.** AI policy (allowed/forbidden, off by default), provider config + `ADR-010` (OpenAI-compatible HTTP, no SDK), versioned prompt system, **the four complete prompt texts with schemas and worked examples**, redaction/minimum-data rules, 10 injection defences, 10-step output validation, **number-mismatch stance (strip and flag)**, caps + cost table + usage log, caching, model pinning/deprecation/fallback, keyless rule-based fallback, draft provenance/regeneration/approval, mapping review-queue state machine, key rotation, 14 AI test fixtures |
| `docs/09_TECHNICAL_ARCHITECTURE.md` | **New.** **ADR-000 template + index and 9 ADRs** (stack, toolchain, signing, storage, Windows validation, process model, SQL-over-ORM, migrations, static-UI serving), headless-engine boundary + module map, CLI with 9 exit codes, data flow, storage layout + OneDrive rule + **storage-growth maths**, mutex/locks, logging, job model + cancellation + crash recovery, config layering, recompute/invalidation, data-volume rule, migration strategy, **NFR→architecture budget table**, spike policy, guardrails, one-command scripts |
| `docs/14_TESTING_QA_PLAN.md` | **New.** Nine test levels + runners; the **canonical `NFR-001`…`016`** table (target, measurement, fixture, evidence) with the measurement protocol and regression rule; a **292-test catalogue** (206 owned here + 86 reserved by `10`–`13`) with per-family tables; the golden-file policy; the **planted-exception acceptance harness** (`P1`–`P32` + 8 controls, recall ≥ 90 %, zero control raises, 18/18 High, per-rule test map, worked re-run identity scenario); tolerance + 16-row edge-case matrix with message IDs; the **cross-artifact harness**; performance baselines; Playwright golden path, state sweeps, a11y/wording scans, the 14-item Windows checklist, 8 E2E journeys; security-test routing + the fault-injection set; migration/upgrade integrity tests; API/CLI contract tests; 6 UAT scripts; `scripts/check` composition, coverage bars, CI; defect severities/evidence/demo-recipe DoD; and the **58 gate checks** as authoritative checklists with evidence + status |
| `docs/15_PACKAGING_DEPLOYMENT_RUNBOOK.md` | **New.** The build → install → validate → support runbook: the four release artefacts (`Setup-FPandAMonthEndCopilot-<version>.exe`, `…-portable.zip`, `SHA256SUMS-<version>.txt`, `THIRD_PARTY_LICENSES.txt` + SBOM-lite); build-host rules + the single-source version-stamping chain; the `packaging/` layout and the ten-step `scripts/build` with five preconditions, the automated payload audit and the `NFR-006` ≤ 500 MB budget; the installer contract (per-user, no admin, no prerequisites, HKCU-only, silent flags, the seven "must never do" rules) and the portable-zip semantics (`portable.flag`); the **24-step clean-Windows-11 validation protocol** with evidence/failure rules, four extra variations and full `TST-WIN-01`…`14` step mapping; the first-run experience (sample project, tour, no network, no key, dead-end-free failures) with `ERR-ENG-001`…`010`; uninstall/data-lifecycle semantics (data retained by default, typed confirmation, downgrade = restore-from-backup); the SmartScreen/Defender reality with the five-step ladder, the verbatim walkthrough and the WDSI procedure; the support/diagnostics flow on the user-exported metadata-only bundle + the "never ask for" list; test/gate mapping and change control. Reason: Kickoff §5/§13, Addon 1 §G.2–G.6/J/N, Addon 2 §B.6, Addon 4 §E.3/H/I; `GATE-01-06`. |
| `docs/16_ROADMAP_PHASES.md` | **New.** The phase plan and the session-start pointer: the live **next open item**; the phase model with gate IDs `GATE-06`…`GATE-15` (packaging spike, phases 1–6, pilot/UAT/go-live reserved to `28`); the scope→phase mapping of all 156 FRs and the P0/P1/P2 split per phase; the Phase-0 completion plan; the packaging-spike contract; the 14-item universal gate contract + evidence pack + approval/waiver rules; per-phase plans for Phases 1–6 (deliverables, DoD, demo outlines, risks); estimates (96 ideal days + per-P0-epic) with the re-estimation and > 50 % variance rules; release cadence and freeze windows; the phase-level cut-line policy and never-cut list; client-visible checkpoints; the demo-script and walkthrough rules; and the cross-phase risk register. Reason: Kickoff §5/§14.1, Addon 1 §C.2/§O, Addon 2 §F.2, Addon 3 §G.6/§K.4, Addon 4 §D.4/§D.5/§L. |
| `docs/17_CODING_STANDARDS.md` | **New.** The coding contract: canonical folder layout + rules; naming conventions; per-language format/lint/type expectations; the engine-boundary import rules with `import-linter` enforcement; Decimal money + float ban, time/timezone and determinism rules; error-handling and logging conventions (catalogued codes, envelope, no raw tracebacks, the never-logged list, shared redaction helpers); dependency/licence/supply-chain rules; secrets and test-data hygiene; testing conventions; UI/React standards; trunk-based git workflow (Conventional Commits, docs/code separation, tags per `24`); code-health guardrails; the 12-item review checklist; and the enforcement map (rule → check → gate item). Reason: Kickoff §5/§14, Addon 1 §I, Addon 2 §F/§H.1/B.1/B.2, Addon 4 §I.1–I.3, `13` §12, `14` §13, `09` §4/§15. |
| `docs/18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md` | **New.** The register of record: the question lifecycle and register rules; the glossary (FP&A/method/control/product terms with owning docs); the assumption register `A1`…`A20` + `A21`…`A29`; the `OQ-` register (19 live questions, blocking rules, the ask format) with the `OQ-018`/`019`/`020` hygiene flag resolved as reserved/reserved/retired; the `DEC-` Decided log consolidating `DEC-001`…`037` with rationale, alternatives and affected docs; and the maintenance cadence that makes the register a gate artefact. Reason: Kickoff §5/§14.5, Addon 1 §C.2, Addon 2 §H.3, Addon 3 §B.2/§J.10, Addon 4 §C. |
| `docs/19_VIBE_CODING_PLAYBOOK.md` | **New.** The working protocol: the 20 principles `P1`–`P20` with their violation signatures and enforcement mechanisms; the session protocol (reading plan, session plan, quote-before-code; change order; closing checklist; regression gate; `SESSION_LOG` format); the Definition-of-Done enforcement and demo-recipe rule; change control with the post-approval impact note and client-feedback intake; approvals and the stop-and-present sequence; blocking questions and escalation; the three evidence levels; AI-session rules (paraphrase ban, no invented requirements); the anti-pattern list; roles; and the 30-minute onboarding ramp. Reason: Kickoff §3/§14, Addon 1 §B/§M, Addon 2 §F.5/§H.3, Addon 3 §I.4/§I.5, Addon 4 §B/§E.2/§E.3/§L.12. |
| `docs/20_REQUIREMENTS_TRACEABILITY.md` | **New.** The chain: 156/156 FRs joined to spec sections, screens (`08` §4), endpoints and tests (`14` §4) with `Spec'd` status; 110 `P0` / 39 `P1` / 7 `P2`; 188 distinct test IDs, all 16 families; the 95-route endpoint reference set in nine areas for `26` to adopt; the chain keys and owners; the three-value status vocabulary; sanctioned non-values (`Global` shell rows, four justified `n/a` reasons); invariants **I1–I9**; reverse indexes (screen → FR, endpoint area → FR, test family → FR); the gate interface (`GATE-01-09`, `GATE-03-08`); the `OQ-`/`Q-` → FR dependency table; the eight FRs whose evidence is strengthened in Phase 1 by extending an existing test; obligations on `26`/`14`/`16`/`02`/`08`/`27`/`29`/`22`; and the frozen constants. Reason: Kickoff §5, Addon 2 §A/§C.2, Addon 4 §C/§D/§L.2. |
| `docs/21_CLIENT_ONBOARDING_QUESTIONNAIRE.md` | **New.** The client question set and the nothing-blocks proof: 21 questions (`Q-001`…`Q-021`, five groups) with wording, why it matters, the labelled default in force, owning docs/FRs and the needed-by date; the ask format (≤ 3 options + recommendation + default); the impact-ordered ask sequence; the §D 20-item checklist mapped (20/20); delivery/IT confirmations `A21`–`A28`; the eight never-re-open rulings; the six-step answer flow with status vocabulary and append-only change control. |
| `docs/13_SECURITY_PRIVACY.md` | **New.** The security/privacy/supply-chain contract as **49 verifiable statements** (`SEC-001`…`049`), each with a mechanism and a planned test (`TST-SEC-01`…`22`): local-only guarantees + the exhaustive three-item outbound inventory; the threat model incl. what is explicitly **not** defended; the exact data-location tree and file-handling rules (atomic writes, `.recycle`, path limits, synced-folder block with recorded override); deletion semantics with pre-delete backup offer and the "not a secure erase" caveat; DPAPI key storage, write-only UI, rotation/revocation/purge with byte-scan proof, `.gitignore` + pre-commit + CI secret scan; log rotation and the allowed/forbidden content policy with a planted-value grep test; the metadata-only diagnostics bundle with its redaction map and manifest schema (20 MB cap); the AI data path (TLS verification not disableable, redaction, caps, provenance, non-authority) and prompt-injection defence; the plain-files data-at-rest stance (`DEC-030`); the privacy note text owned here for `22`/`29`; the audit/log/security-event boundary (`SEC-048`/`049`); error codes `ERR-SEC-001`…`008` |
| `docs/12_POWERPOINT_OUTPUT_SPEC.md` | **New.** The deck contract: the **fixed six slides** (`PPT-001`…`PPT-006`) with the default/opt-in missing-input rule (`DEC-029`); the universal contract (inch grid + scaling, the native-and-editable whitelist, the shared theme, the **character-budget formula** with per-placeholder budgets and the prioritized trimming order, deterministic shape naming/order, stamping + footer + full disclaimer on the last slide, AI/rule-based labelling, not-available states, accessibility, the ≤ 15 s aggregate-only budget); every slide/placeholder with geometry, fonts, budgets and content sources; two native charts incl. the waterfall decision (`SPK-08`) and its stacked-column fallback; base-deck mapping/refusal rules; the deck's half of the cross-artifact contract; files/refresh/issuance; 24 test IDs; `ERR-EXP-012`…`018` |
| `docs/00_INDEX.md`, `docs/01_PRD.md`, `docs/02_FUNCTIONAL_SPEC.md`, `docs/03_DATA_DICTIONARY.md`, `docs/09_TECHNICAL_ARCHITECTURE.md`, `docs/11_EXCEL_OUTPUT_SPEC.md` | **Amended (ripple, doc 14).** `00`: doc-map row 14, completeness, `A1-L` INTEGRATED, `TST-<FAM>` families enumerated. `01`: the M10 performance row now cites the canonical NFRs. `02`/`03`: the rule-run target is `NFR-007` (was mis-cited as `NFR-009`). `09` §14: the NFR table extended to `NFR-001`…`016` with the remap (`NFR-009` = Excel pack, `NFR-011` = logs, `NFR-012` = crash) and the new `NFR-013`…`016`; repo layout gains the new test categories and `acceptance`/`perf` scripts. `11`: the Excel-pack budget now cites `NFR-009`. |
| `docs/00_INDEX.md`, `docs/01_PRD.md`, `docs/02_FUNCTIONAL_SPEC.md`, `docs/09_TECHNICAL_ARCHITECTURE.md`, `docs/11_EXCEL_OUTPUT_SPEC.md` | **Amended (ripple, doc 13).** `00`: `SEC-nnn` prefix + `SEC` error family + `TST-SEC` family; doc-map row 13 → Draft; docs complete `00`–`13`. `01`: `DEC-030` (data at rest = plain local files). `02`: `FR-SET-012` records the append-only audit rule (`SEC-048`). `09`: storage inventory gains `security.log`. `11` §4.8: the secret-pattern pointer now names a real section (`13` §5.4). Also fixed doc 11's §4.5 control-row self-correction wart. |
| `docs/01_PRD.md`, `docs/02_FUNCTIONAL_SPEC.md`, `docs/05_CALCULATION_SPEC.md`, `docs/08_UI_UX_SPEC.md`, `docs/09_TECHNICAL_ARCHITECTURE.md`, `docs/11_EXCEL_OUTPUT_SPEC.md` | **Amended (ripple, doc 12).** `01`: `DEC-029`. `02`: `FR-PPT-001` acceptance clarified for base-deck mode. `05` §6.3: scale examples aligned to the display owner (`08` §15). `08` §11.1: the omission example now points at `12` §2.1. `09`: spike `SPK-08` added. `11` §12: pointer to `ERR-EXP-012`…`018` |
| `docs/11_EXCEL_OUTPUT_SPEC.md` | **New.** The five artefact families; the universal contract (**values-only workbooks** — no formulas anywhere, the 30-field machine-readable stamp with defined names, the four-row header block, filename/sanitisation/collision policy incl. the recoverable `.recycle` habit, the 15-ID number-format dictionary with the Indian lakh/crore grouping and its boundary matrix, the `CF-001`…`CF-012` → Excel mapping with **mandatory non-colour signal columns**, freeze/autofilter/width/wrap rules, locale independence, sample-data watermarking); **eight pack sheets specified column by column** (`Cover`, `BvA Summary`, `BvA Bridge`, `Transaction Detail`, `Exception Register`, `Forecast Summary`, `Import Reconciliation`, `Audit Trail`) each with controls, empty state and print contract; the 1,048,576-row cap and lossless split algorithm; the evidence bundle (workbook + zip with hashed manifest); ad-hoc "export what you see" incl. the CSV contract and its sidecar stamp schema; the owner distribution with the exact plain-text template; house-style matching (matchable vs refused, with the profile JSON); print/PDF setup; the cross-artifact consistency contract; 11 export failure modes (`ERR-EXP-001`…`011`); a 26-item test contract |
| `docs/03_DATA_DICTIONARY.md`, `docs/01_PRD.md`, `docs/02_FUNCTIONAL_SPEC.md`, `docs/08_UI_UX_SPEC.md` | **Amended.** `03`: `FactExport` added (§5.7 + §2.1 grain register → 41 tables). `01`: `DEC-028` + two new open questions + the `OQ-020` registry-hygiene flag. `02`: `FR-XL-009` aligned to `DEC-028`. `08`: §14 now points to `11` §3.7 for the literal Excel theme and the re-derivation test |
| `docs/SESSION_LOG.md` | **New.** This file |

### FRs / areas touched

- 156 `FR-nnn` allocated across 11 families, all with priorities and phases (`02` §2–§14).
- 16 `CALC-*`/`KPI-*` formula IDs registered with fixtures (`05` §14); 32 `IMP-nnn` validation checks
  catalogued (`04` §10); 24 `EXC-nnn` rules fully specified with a 40-planting plan (`06`), all 15 seed
  rules covered; 6 new decisions allocated (`DEC-020`…`DEC-025`) in `01_PRD.md` §21; 43 `SCR-` screens and
  12 `CHT-` charts inventoried with 12 `CF-` formatting rules (`08`); **10 ADRs** written and indexed
  (`09`, including `ADR-010` added this turn); 4 versioned prompt templates specified (`10`);
  2 further decisions allocated (`DEC-026`, `DEC-027`).
- Areas governed: scope (`01`), behaviour (`02`), structure (`03`), ingestion (`04`), arithmetic (`05`),
  governance/metadata (`00`), process (`CHANGELOG`, `SESSION_LOG`).
- `14` owns the NFR and test namespaces: **16 NFRs**, **16 test families** (`TST-CALC` … `TST-UAT`) plus the
  86 reserved IDs, the 58 gate checks (`GATE-01-01`…`GATE-05-13`), and the acceptance/performance harnesses.
- `13` allocates the security namespace: **49 statements** (`SEC-001`…`049`), **22 tests**
- `15` owns the environment/lifecycle namespace: the release artefact set, the `packaging/` layout, the build steps, the installer contract, the 24-step clean-VM protocol (with its four variations), the SmartScreen ladder + verbatim walkthrough, the support flow, and **10 error codes** (`ERR-ENG-001`…`010`, extending the `ENG` family registered in `00` §8). `GATE-01-06` is now answerable by the document.
- `16` owns the roadmap namespace: the phase/gate model (`GATE-06`…`GATE-12` allocated; `GATE-13`…`GATE-15` reserved to `28`), the live next-open-item pointer, the universal gate contract, estimates (ideal days per phase and per P0 epic), the release cadence, and the phase-level cut-line application. No new error/test/FR IDs are allocated.
- `17` owns the code-standards namespace (no new FR/test/error IDs): the repo layout, naming, format/lint/type configuration, the engine-boundary import contract, money/time/determinism rules, error/logging conventions, dependency/licence/supply-chain rules, repo hygiene, testing and UI conventions, the git workflow, code-health guardrails, the review checklist and the enforcement map that binds each rule to a check and a gate item.
- `18` owns the knowledge-register namespace: the glossary, the assumption register (`A1`…`A29`), the open-question register (`OQ-001`…`OQ-022`, with `OQ-018`/`019` reserved and `OQ-020` retired) and the Decided log (`DEC-001`…`DEC-037`). No test/error/FR IDs are allocated here.
- `19` owns the process namespace (no new FR/test/error IDs): the canonical principles list, the session protocol and log format, the DoD enforcement, the change/approval mechanics, the blocking-question handling, the evidence levels, the AI-session rules and the anti-pattern list.
- `21` owns the **question register** (no new FR/test/error IDs): 21 `Q-` items in five groups, each with a
  labelled default in force, an owning-doc pointer and a needed-by date; the `A21`–`A28` delivery/IT
  confirmations; the ask format; the never-re-open list; the answer-flow status vocabulary. It seeds from
  `18` §3/§4 and keeps the IDs stable (`18` §8.1).
- `20` owns the **join only** (no new FR/test/screen/endpoint IDs): the FR → spec → screen → endpoint → test → status chain, its invariants, the reverse indexes and the endpoint reference set that `26` adopts. It is a view: the owning doc always wins.
  (`TST-SEC-01`…`22`), **8 error codes** (`ERR-SEC-001`…`008`) and the `SEC` error family — registered in
  `00_INDEX` §8 before the doc was written (spec-first).
- `12` allocates the deck namespace: **6 slide contracts** (`PPT-001`…`PPT-006`), 29 budgeted placeholders,
  **2 native charts** (bridge + forecast) with the waterfall decision, a template obligation, 7 error codes
  (`ERR-EXP-012`…`018`) and **24 test IDs** (`TST-PPT-01`…`24`). `01` §21 now carries
  `DEC-001`…`DEC-029`.
- `11` allocates the Excel-output namespace: **8 sheet contracts** (`XL-001`…`XL-008`) + 4 more artefacts
  (`XL-009`…`XL-012`), **15 number-format IDs** (`XLS-FMT-001`…`015`), **26 test IDs** (`TST-XL-01`…`26`),
  and **11 export error codes** (`ERR-EXP-001`…`011`, using the existing `EXP` error family rather than
  inventing a prefix). `01` §21 now carries `DEC-001`…`DEC-028`; `03` carries 41 tables.

### Spec sections integrated in this session

- Kickoff §5 (doc tree, quality gate), §2, §4 (stack → ADR-001), §6, §7, §8, §9, §10, §11 (reporting
  outputs — **complete**: Excel in `11`, the 6-slide editable deck in `12`), §12 (esp. §12.9 job UX,
  §12.12 locale), §13 (partially, via `01`–`09`); Addon 2 §C (base deck, house style, deterministic
  ordering), §D.12/D.13 (collision policy, evidence bundle), §E.4 (theme-as-data) and §E.5 (PPT character
  budgets with prioritized trimming); Addon 3 §C.5 (score never shown alone), §F.1–F.4 (chart inventory,
  one CF rule set, output conventions, cross-artifact test).
- Addon 1 §C.2/D/N (partially, via `01`), §O (tracker only); **§C.1 + §D now integrated via `21`** (the
  questionnaire, its defaults and the 20-item domain checklist).
- Addon 2 §A.3/C.2/D.14 (partially, via `01`/`00`).
- Addon 3 §B.2/E (partially, via `01`).
- Addon 4 §A.3/B/C/D/E (partially, via `00`/`01`).

Coverage-Matrix rows are only flipped to `INTEGRATED` when the owning doc is complete and the change is
recorded in `CHANGELOG.md`. A **full matrix refresh is required at the end of the doc build**.

### Test results

- No code, no tests possible yet. **Doc checks run this session:** file creation verified; FR-ID
  integrity verified (156 headings, zero duplicate IDs, per-family counts match the `02` §2 table
  exactly); placeholder scan clean (`TBD`/`TODO` hits are only the word "JTBD" and the hygiene rule
  itself); **all 36 arithmetic assertions in the `05` golden fixtures recomputed in Python `Decimal`
  with half-up rounding — zero failures**; grain register reconciled to exactly 40 tables; cross-doc
  example values reconciled (the `03` batch score was corrected to match `CALC-050`); cross-references
  written only to docs that are planned in `00_INDEX.md` §3 (the full link-check runs once all docs
  exist); **reference integrity verified**: 43/43 `SCR-` inventory rows referenced in the body, 12/12
  `CHT-` rows, 12/12 `CF-` rules, all ADR index rows backed by a section; all 16 JSON blocks in `10`
  parse; all four prompts verified COMPLETE (system prompt + user payload + input schema + output schema
  + guardrails + worked example).
- **Self-audit catch (fixed in the same turn):** the first pass of `10` §5 shipped `PROMPT-02`…`PROMPT-04`
  without explicit input/output JSON schema blocks — a gate requirement. Added all five missing schemas
  via scripted inserts with existence assertions, then re-ran the structural check until all four prompts
  reported COMPLETE. The check (`assert every prompt has all six components`) is now part of the doc
  verification routine.
- **Incident (self-inflicted, resolved):** a fuzzy edit to `00_INDEX.md` truncated the file from 362 to
  191 lines. Restored from git (`git checkout HEAD -- docs/00_INDEX.md`) and re-applied all 13 pending
  updates with a script that asserts exactly one match per replacement; verified 366 lines with the
  approval log intact and no line loss anywhere else (`git diff --numstat` check). Process change: bulk
  edits to large pre-existing docs use exact-match scripted replacements rather than fuzzy edits.
- **Doc `11` checks (all green after fixes):** 4/4 JSON blocks parse; all 8 sheet contracts present;
  column-letter sequences consecutive in all 9 sheet tables; 15/15 format IDs referenced-defined; all 12
  `CF-` rules rendered; 26/26 `TST-XL` IDs; 11/11 `ERR-EXP` IDs; print contract covers all 8 sheets;
  footer short form measured at **134 characters** (the first draft claimed 148 — corrected).
- **Cross-document checks that caught real defects (all fixed this pass):**
  (a) the draft used `OQ-013`/`OQ-014`, which **collide** with questions already registered in `01` §14 —
  renumbered to `OQ-021`/`OQ-022`; (b) `OQ-020` is referenced in `01` §16 but appears in **no** document —
  flagged for `18`/`21` to register or renumber; (c) `11` §3.9 needed a home for the refresh context and
  no such table existed — `FactExport` was added to `03` §5.7 + the grain register (41 tables);
  (d) four citation errors were found by an automated section-reference sweep (`08` §20 → §17 ×3,
  `05` §7 → §6.1, `06` §11 → §2, `03` §5.5 → §5.7) plus a wrong source attribution in `CHANGELOG`
  (Addon 1 `D.12`/`D.13` → Addon 2 §D.12/D.13). The sweep script is now the standard cross-reference
  check for future docs.
- **Doc `12` checks (all green after fixes):** geometry audit over every machine-readable placeholder
  (bounds, footer clearance, pairwise overlap) — clean; table column widths sum to 12.43″ on both tables;
  6/6 slide IDs; 24/24 `TST-PPT` IDs; `ERR-EXP-012`…`018` all defined; 1/1 JSON block parses.
  **Budgets were recomputed from the §3.4 formula rather than typed by hand** — the first draft's numbers
  did not match the geometry (23 corrections), and the audit then exposed four genuine layout collisions
  (slide-2 narrative vs footnote, slide-5 table vs summary, slide-6 chart vs disclaimer band, slide-1
  stamp block too short for 14 lines). All four were resolved by geometry, not by weakening the budgets.
  **Self-audit catch:** `TST-PPT-09` asserted that a notes "stamp JSON" parses, but no schema existed —
  the `fpa.ppt.stamp.v1` schema (incl. `omitted_slides` and `notes_full_text`) was added to §3.7 before
  commit.
- **Doc `14` checks (all green after fixes):** 58/58 gate checks enumerated (9+12+12+12+13) and the family
  arithmetic re-derived from the tables (206 own + 86 reserved = **292**, after the first draft's "222"
  total was caught by re-deriving); every NFR reference in every doc re-audited against the canonical map
  and four real conflicts fixed (`NFR-007`/`NFR-009` swap in `02`/`03`, the `11` "analogue" citation, and
  `09`'s table); page/row budgets re-derived rather than typed. **Self-audit catch:** the acceptance bar in
  the TL;DR was looser than `06` §8.3 (I had written "≤ 1 control false positive"; `06` requires **zero**)
  — corrected here rather than relaxing `06`.
- **Doc `13` checks (all green after fixes):** 49/49 statements present in the §13 index and referenced in
  the body; 22/22 `TST-SEC` tests defined; 8/8 `ERR-SEC` codes defined; citation sweep clean. Two
  contradictions were caught by cross-checking the owners and fixed in `13` (not by weakening the other
  docs): the on-disk tree initially invented `raw\`/`.recycle\` where `09` §7.1 says `archives\` (and
  `.recycle\` lives inside `exports\`), and the synced-folder rule initially said "refused" where `09` §7.2
  allows a **recorded override**. Also: the doc-13 §6.3 audit/log/security-event boundary was added because
  "audit log" (kickoff §5) had no home once `03` §5.7 owned the table — the security properties
  (append-only, machine-level events surviving project deletion) are now specified and testable.
- **Cross-document reconciliations made this pass:** `05` §6.3's scale examples contradicted the display
  owner (`08` §15) — aligned; `08` §11.1's "the forecast slide will be omitted" example contradicted
  `FR-PPT-001`'s "exactly six slides" — resolved as default *not-available* + explicit opt-in omission,
  recorded as `DEC-029` and pointed at from `08`; `FR-PPT-001`'s acceptance now distinguishes generated
- **`20` audit:** 747 lines; 156 matrix rows with a uniform 9-column shape (no missing/extra/duplicate FR); all 192 `TST-` mentions resolve to the frozen 292-ID inventory; all 43 `SCR-` IDs appear in the reverse index (no orphan screen); the `§`-citation sweep is clean; the endpoint cells are exactly the 95 catalogued routes; and the seven screen links that `08` §4 already owned but the first draft of the join missed (`FR-PRJ-009`→`SCR-002`, `FR-SET-006`→`SCR-003`, `FR-IMP-022`/`FR-EXC-014`→`SCR-014`, `FR-EXC-009`→`SCR-024`, `FR-XC-001`→`SCR-029`, `FR-XC-012`→`SCR-041`, `FR-IMP-026`→`SCR-033`) were found by diffing the join against the inventory and fixed in the map, not in a footnote. `08` §4's FR column is now generated from the join.
- **`21` audit:** 304 lines; 102 distinct ID tokens referenced and all resolve (no missing id); 21/21 `Q-` items appear in the §3 tables, the §5.2 answer log and the §6.2 §D mapping; the §D checklist covers 20 of 20 items; every `§`-citation resolves in its target document (six first-draft cites corrected against the real headings — blocking protocol `18` §4.3→§4.2 and, for defaults, `05` §2/§6.3/§11, `06` §2.6/§2.9/§2.10/§4, `07` §6, `12` §6, `15` §13); the `A21`–`A28` confirmation rows are aligned to their `18` §3.2 owner docs; no `TBD`/`TBC`/placeholder text; the header block is within the 15-bullet TL;DR rule.
  from preserved slides in base-deck mode.
- **`19` audit:** 497 lines; every `§`-citation resolves (`02` §3.5, `14` §14.3/§1.2/§8.3/§13.2, `16` §5.1/§5.2/§6/§9.2/§11.1/§11.2, `10` §4, `09` §3/§13, `17` §7.1/§9.2/§11.2, `08` §16/§17, `13` §7/§12); the TL;DR is 11 bullets (≤ 15); the DoD criteria are referenced rather than restated (single-source with `02`/`14`); and the doc states the Phase-0 no-code rule explicitly.
- **`18` audit:** 451 lines; every `§`-citation verified (one draft cite to `03` §16 corrected to `04` §16 — the score inputs live in the import spec); every `Q-`/`OQ-`/`A`/`DEC-`/`BL-`/`EXC-`/`CALC-`/`GATE-` ID used resolves; the TL;DR is 10 bullets (≤ 15); `01` §14/§16 corrected for the `OQ-020` phantom and `14`'s two `18`-dependent gate rows updated.
- **`17` audit:** 558 lines; every `§`-citation verified against its target (two first-draft cites to `14` §2.3/§2.5 corrected to `14` §1.2 items 3/5 and `09` §5.3 after the golden-file and determinism rules were located); every ID used exists (`FR-IMP-031`, `TST-WIN-03`/`13`, `SEC-0xx`, `GATE-02-09`, `BL-012`); the TL;DR is 11 bullets (≤ 15); all text owned elsewhere is cross-referenced rather than restated (the layer table, `scripts/check` composition, coverage bars and message-catalog rules remain single-sourced in `09`/`14`/`26`/`08`).
- **`16` audit:** 682 lines; every `§`-citation verified against its target document and corrected where it was wrong (the first draft mis-cited `04`/`05`/`06`/`07`/`08`/`10`/`11`/`12` section numbers; all now point at the owning section, e.g. the KPI library is `05` §5, the rule specifications are `06` §4, the mapping review queue is `10` §13); all FR IDs used exist with the claimed meaning (`FR-BVA-012` = search, `FR-BVA-013` = comparability guard, `FR-IMP-022` = data-quality score); the TL;DR is 10 bullets (≤ 15); no marker text remains.
- **`15` audit:** every `§`-citation verified against its target document (all resolved), every `SCR-`/`FR-`/`ERR-`/`SEC-`/`TST-`/`GATE-` ID used exists in its owning doc, the TL;DR is 10 bullets (≤ 15). Corrections made during the audit: the SmartScreen ladder is five steps (not three); the sample-data non-delivery rule points at `FR-XC-013`/`FR-ONB-008` (sample-data integrity is **Addon 4** §H, not Addon 1 §H); `SCR-003`/`SCR-040`/`SCR-043` replaced the `SCR-0xx` placeholder; the `TXT-INSTALL` marker became a proper §8.3 clause; `TST-SEC-20` is owned by `13` (not `14`).
- Quality gates: **0 of 5 gates attempted** (expected — gates are run at Phase 0 completion).

### Decisions taken this session

Recorded in `01_PRD.md` §21 as `DEC-001`…`DEC-029` and to be mirrored (with dates and rationale) into the
canonical Decided log in `18_...OPEN_QUESTIONS.md` when that doc is written. New this pass: **`DEC-028`**
(PDF is not rendered in-app; v1 delivers tested print readiness + "Open for printing / Save as PDF") —
raised because `FR-XL-009` implied an action the architecture cannot deliver without a bundled renderer or
Excel automation, with the three rejected alternatives recorded in `11` §10.3. Also this pass:
**`DEC-029`** (missing-input deck behaviour: not-available state by default, omission only as an explicit
choice stated on the cover) — raised by the contradiction between `FR-PPT-001` and the `08` §11.1 example.

### Blocking questions

None. Every unconfirmed client fact has a labelled default in `01` §12 and will be carried into `21`.

### Next step

Continue the mandated order with **Addon 1's `22`–`25`** (next open item: `16` §1.3): `21` is done; next is
the end-user guide (`22`, task-structured
and keyed to `SCR-nnn`), the consultant handover/support doc (`23`), the release/versioning runbook (`24`, which
also owns the upgrade fixture named by `GATE-02-07`) and the risk register (`25`). Then Addon 2's `26` (+ ADR-002),
which must adopt or rename the 95-route reference set in `20` §2.3 and publish the endpoint → FR reverse index;
Addon 3's `27`–`28` (+ the four prompt texts, chart inventory and negative corpus); Addon 4's `29` + the
Source-of-Truth Matrix refresh and doc headers; then the `sample-data/` build step, the Coverage-Matrix refresh,
the five-gate self-audit with the link-check, the tabletop walkthrough (through pack issuance and a cold-start
client pass) and `PHASE0_SUMMARY.md`.

### Deferred to backlog / open questions

- All 25 parked scope items from `01` §6.2 → to be seeded into `27_BACKLOG.md` as `BL-001`…`BL-025`.
- Headcount metrics, one-off tagging, budget version-compare, commentary carry-forward, Power BI export,
  direct ERP connectors → already parked with triggers.
- Open commercial questions: support/warranty terms (`OQ-016`), delivery channel (`OQ-017`),
  signing-certificate budget (`OQ-012`).
- New from the `14` pass: baselines (`tests/perf/baselines/*.json`) are recorded at Phase 1 and only after
  the first measurement; the negative corpus is built with `sample-data` (Phase 0 build step); the
  `acceptance` and `perf` scripts are added to the repo layout obligations; `02`–`04`'s error slugs are now
  load-bearing in the edge-case matrix, so slug renames must update `14` in the same pass.
- New from the `13` pass: the machine-level `security.log` events (key lifecycle, project deletion,
  diagnostics export, sync override) must be implemented with `doctor` reporting; the diagnostics manifest
  schema (`fpa.diagnostics.v1`) and the log-content policy test fixtures are owed to `14`; proxy/custom-CA
  support, encrypted backups, secure erase and retention automation are parked (`BL-029`…`BL-035`).
- New from the `12` pass: spike `SPK-08` (native waterfall support) must run before Phase 5 deck code; the
deck template `packaging/templates/FPAMonthEndCopilot_v1.pptx` must be authored and committed before
Phase 5; the KPI-card default set is client-confirmable (`PPT-KPI-DEFAULT`).
- New from the `11` pass: **`BL-026`** Excel charts inside the pack — deferred with rationale, to be
  recorded in `27_BACKLOG.md`; **`OQ-021`** (client's current report format for house-style matching) and
  **`OQ-022`** (preferred pack default units); the **`OQ-020`** registry-hygiene flag for `18`/`21`.

- New from the `15` pass: the packaging spike (`SPK-04`, WebView2 in the packaged build) must run before the
  installer work; the code-signing certificate cost/lead time (`OQ-012`) is a client decision with a recorded
  fallback (`ADR-003`); the per-machine/all-users installer variant stays parked (`Addon 1 §N`); portable
  mode's missing Explorer file-version metadata is an accepted, documented limitation; the Inno Setup major
  version is pinned and re-verified each release; `ERR-ENG-001`…`010` copy is owed to `26` and must obey
  `08` §16 wording rules.

- New from the `16` pass: the **packaging spike** is the first post-approval work item and is timeboxed to
  two half-days, so the first Phase-1 commit cannot start before `GATE-06`; the **estimates** (96 ideal days
  for Phases 1–6) are re-estimated at every gate with any > 50 % variance reported immediately; and the
  `GATE-13`…`GATE-15` names are reserved to `28`, which must keep them consistent with `16` §2.1.

- New from the `17` pass: the repository config files (`.gitignore`, `.gitattributes`, `.editorconfig`,
  `pyproject.toml` thresholds, the ruff/mypy/ESLint rule sets) are owed to the first code session and must
  match `17` §3/§7/§8/§12; the `import-linter` contract and the `scripts/check` composition are implemented
  exactly as `14` §13.1 specifies; the prior-version project fixture under `tests/fixtures/` is owed by `24`.

- New from the `18` pass: doc `21` must inherit the `Q-` IDs referenced in `18` §3.1/§4.1 (including `Q-001`
  for the sanitized real month) and pre-fill each item with its default; doc `25` must register the
  high-impact questions (`OQ-012`, `OQ-014`, `OQ-016`); doc `29` must present `DEC-*` and the open questions
  in plain language; and `DEC-031`…`DEC-037` are registered here for the first time and must be honoured by
  `14`/`15`/`16`/`17` (no document may restate them differently).

- New from the `19` pass: the approval phrase for non-gate changes is `<change> APPROVED — <who> — <date>` and
  must be used consistently by `CHANGELOG`/`SESSION_LOG`; the session numbering is continuous; and the
  feedback-intake template will be finalised with `23`'s support flow.

- New from the `20` pass: `26` must adopt/rename the 95 routes and publish the endpoint → FR index; `14` must
  strengthen the eight thin-evidence FRs by extending existing tests (never renumbering the 292-ID inventory);
  and `08` §4's FR column must be regenerated from `20` §4.3 whenever a screen or FR changes.

- New from the `21` pass: the `Q-` register is now the single place client questions live, so `25` must register the
  risk for each high-impact unanswered item whose needed-by date approaches (`OQ-012`, `OQ-014`, `OQ-016`), `29`
  must restate the same questions in plain language with the same defaults, and `22`/`23` owe the training and
  support material behind `Q-017`/`Q-018`; any answered question must land as a `DEC-` row in `18` §5 and update
  every owning doc in the same change (the questionnaire is never the only place an answer lives).

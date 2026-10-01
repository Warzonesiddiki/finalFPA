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
- `11` allocates the Excel-output namespace: **8 sheet contracts** (`XL-001`…`XL-008`) + 4 more artefacts
  (`XL-009`…`XL-012`), **15 number-format IDs** (`XLS-FMT-001`…`015`), **26 test IDs** (`TST-XL-01`…`26`),
  and **11 export error codes** (`ERR-EXP-001`…`011`, using the existing `EXP` error family rather than
  inventing a prefix). `01` §21 now carries `DEC-001`…`DEC-028`; `03` carries 41 tables.

### Spec sections integrated in this session

- Kickoff §5 (doc tree, quality gate), §2, §4 (stack → ADR-001), §6, §7, §8, §9, §10, §11 (reporting
  outputs — Excel side complete, PPT pending in `12`), §12 (esp. §12.9 job UX, §12.12 locale),
  §13 (partially, via `01`–`09`); Addon 2 §D.12/D.13 (collision policy, evidence bundle) and §E.4
  (theme-as-data); Addon 3 §C.5 (score never shown alone), §F.1–F.4 (chart inventory, one CF rule set,
  output conventions, cross-artifact test).
- Addon 1 §C.2/D/N (partially, via `01`), §O (tracker only).
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
- Quality gates: **0 of 5 gates attempted** (expected — gates are run at Phase 0 completion).

### Decisions taken this session

Recorded in `01_PRD.md` §21 as `DEC-001`…`DEC-028` and to be mirrored (with dates and rationale) into the
canonical Decided log in `18_...OPEN_QUESTIONS.md` when that doc is written. New this pass: **`DEC-028`**
(PDF is not rendered in-app; v1 delivers tested print readiness + "Open for printing / Save as PDF") —
raised because `FR-XL-009` implied an action the architecture cannot deliver without a bundled renderer or
Excel automation, with the three rejected alternatives recorded in `11` §10.3.

### Blocking questions

None. Every unconfirmed client fact has a labelled default in `01` §12 and will be carried into `21`.

### Next step

Continue the mandated doc order: `12_POWERPOINT_OUTPUT_SPEC.md` — the six slides slide by slide (cover
+ period + source files; executive KPIs; BvA bridge/waterfall; top variances with drivers + optional AI
draft commentary; exceptions and control risks; forecast and outlook), with exact placeholder geometry,
**per-placeholder character budgets and the prioritized trimming order** (Addon 2 §E.5), native/editable
elements only (text boxes, tables, native charts — never screenshots), the editable-in-PowerPoint
guarantee, brand colours/logo handling, the reference to `11` §3.7's theme, base-deck support for a
client-supplied `.pptx`, deterministic element ordering, and stamping + disclaimer placement on the
cover/back slide.

### Deferred to backlog / open questions

- All 25 parked scope items from `01` §6.2 → to be seeded into `27_BACKLOG.md` as `BL-001`…`BL-025`.
- Headcount metrics, one-off tagging, budget version-compare, commentary carry-forward, Power BI export,
  direct ERP connectors → already parked with triggers.
- Open commercial questions: support/warranty terms (`OQ-016`), delivery channel (`OQ-017`),
  signing-certificate budget (`OQ-012`).
- New from the `11` pass: **`BL-026`** Excel charts inside the pack — deferred with rationale, to be
  recorded in `27_BACKLOG.md`; **`OQ-021`** (client's current report format for house-style matching) and
  **`OQ-022`** (preferred pack default units); the **`OQ-020`** registry-hygiene flag for `18`/`21`.

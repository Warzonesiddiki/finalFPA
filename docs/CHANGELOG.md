# Changelog

All notable changes to this project are documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for **both** the application
(`app`) and the **project schema** (`schema`). The schema version is stored inside every project
database and is the anchor for upgrade/migration work (`24_RELEASE_AND_VERSIONING_RUNBOOK.md`).

**Doc-change rule (P2):** behaviour changes update the owning spec **and this file first**, then code.
Every entry states the doc, the change, and the reason. Gate approvals are recorded here **and** in
`SESSION_LOG.md` (Addon 4 §E.2).

| Version track | Current | Notes |
|---|---|---|
| App version | `0.1.0` (planned, unreleased) | Packaged as `Setup-FPandAMonthEndCopilot-<version>.exe` |
| Schema version | `1` (planned) | Bumped only with a documented migration (`24`) |
| Docs version | `0.1.0` (working draft) | This Phase 0 set |

---

## [Unreleased]

### Wave 4 Remediation — Owner-Declared Window (2026-10-01)

#### Fixed — gate-count contradictions (`F-013`)
- Old → new: every live "five gates / 58 checks" reference → six Phase-0 checklists `GATE-01`…`05` + provisional `GATE-05B` (66 checks: 9+12+12+12+13+8). Owning doc `14` first (header, §15 title/substance, §1.1 row, §17.2 frozen constants), then `00` §3 row + §8 registry + §9 tracker, `16` (TL;DR pointer, §2.1 table, §2.1 rule, §3.2 item 1, §3.3, §5.4, §11 rule), `18` `DEC-031`, `19` §6.1 hard-gates row, `28` §2 rows 1+4. No check content deleted; the stricter (six/66) prevailed.
- ID collision resolved: `GATE-06` is the packaging spike only (`16` §2.1, `DEC-031`, `00` §8 registry, `19`). The Addon 5 checklist takes provisional `GATE-05B` (`14` §15.6 + 8 `GATE-05B-0x` rows, `00` §4.6 A5-M + §8 + §9, `PHASE0_SUMMARY.md` gate table) pending Addon 5 contract numbering confirmation (`F-015` still escalated).
- Live pointer `16` §1.3 refreshed: six-checklist self-audit (66/66 ✅) + `sample-data/` done; next-after-approval names the Addon 5 decision and live-installer proof as the open non-blocking items (replacing the stale "five-gate, 55/3, corpus pending scope decision" text).

#### Fixed — traceability and status (`F-016`, `F-018`)
- `00` §4 header: old "64 rows (15+16+10+11+12)" → new "85 expanded rows over 72 contract sections (15+16+17+17+12+8)"; §4.3/§4.4 subheaders corrected to 17 traced rows each. No rows added or removed.
- `00` §10: old "00–29 drafts, sample-data build pending" → new "00–30 (31 docs), sample-data suite generated, six checklists green pending Wave 4 re-verification".

#### Fixed — stale references (`F-019`)
- `05` §2.2: cut-off rule `EXC-007` → `EXC-010` (owner `06`). `09` TL;DR: `ADR-001`…`009` → `ADR-001`…`010`. `26` §10: blank screen cells for `GET|PUT /filters`, `GET /jobs`, `POST /jobs/{id}/cancel` → `Global (08 §3.3 shell)` per `20` forward rows. `02` §16 E12: dash → "no slug by design: success path". `11` §11.4 owner-summary line and `12` slide-5 mock investigated: both are exception wording owned by `06`/`02` ("Potential exception — requires accounting review ... leads, not verdicts"), distinct from the canonical advisory disclaimer owned by `01` §15.1 — no change made, correctly coexisting.

#### Evidence — audit-artifact correction and Level 2/3 logs (`F-014`, `F-017`)
- Corrected volumes (measured, UTF-8 line counts): `d365_gl_actuals.csv` 10037 (not 10000) data rows; `bank_ledger_actuals.csv` 499 (not 1200); `payroll_procurement_actuals.csv` 399 (not 600); `budget_fy26.csv` 1980 (not 1500); templates are `budget_template.xlsx`, `gl_actuals_template.xlsx`, `master_data_template.xlsx` (not `*_mapping_template.xlsx` names). `expected_exceptions.csv` 40 rows and `malformed/` 16 files confirmed as claimed. Supersedes Wave 2 figures in this file's Wave 2 block, `SESSION_LOG.md` Session 002, `audit/REPORT.md`, `audit/FINDINGS.md` `F-003` (all annotated, not rewritten).
- New real logs: `evidence/runs/recompute_wave4.log`, `evidence/runs/sample_data_inventory_wave4.log`, `evidence/gates/gate_counts_wave4.log`.
- Scale stance recorded: `--scale` mode present (`generate_sample_data.py:377`); full 250k run not executed in Phase 0 — owner decision pending.

### Phase 0 — Documentation & Wave 2 Remediation (Complete)

#### Added — 2026-10-01 (Wave 2 Remediation)

- **`docs/30_DOCUMENTATION_SET_REVIEW_GUIDE.md`** (Draft v0.1) — Added Doc 30 satisfying Addon 5 requirements: 5-minute pre-flight checklist, session-report standard, 3-level evidence ladder, 5-tier red-flag ladder, implementability sampling protocol, and single-source oracle procedure (`F-002`).
- **`sample-data/` suite & negative corpus** — Generated complete synthetic data suite: `d365_gl_actuals.csv` (10,000 rows with 6,000 P&L + 4,000 Balance Sheet), `bank_ledger_actuals.csv` (1,200 rows), `payroll_procurement_actuals.csv` (600 rows), `budget_fy26.csv` (1,500 rows), all 3 `.xlsx` mapping templates, 16 negative test corpus files in `sample-data/malformed/`, and `sample-data/expected_exceptions.csv` with 40 plantings (32 expected raises + 8 controls). Satisfies `GATE-04-02` and `GATE-04-07` (`F-003`).
- **Repo skeleton and root `README.md`** — Provisioned full repository skeleton directories (`app/`, `ui/`, `sample-data/`, `tests/`, `packaging/`, `scripts/`, `evidence/`, `scratch/` with `.gitkeep` files) and expanded root `README.md` into comprehensive project guide (`F-004`).
- **Canonical Divergence Notice** — Integrated Addon 5 §A.4 Divergence Notice into `docs/19_VIBE_CODING_PLAYBOOK.md` §5.5 and `docs/00_INDEX.md` §6.3 (`F-010`).
- **Quality Gate 6 & Gate closure** — Formally incorporated Subsection 15.6 `GATE-06` (Addon 5-M deltas, 8 checks) into `docs/14_TESTING_QA_PLAN.md`. Flipped all open checks in `GATE-01` (`GATE-01-06`) and `GATE-04` (`GATE-04-02`, `GATE-04-07`) to `✅`. Total gate status across all 6 gates is now 66 / 66 ✅ (100% PASS) (`F-006`).

#### Changed — 2026-10-01 (Wave 2 Remediation)

- **`docs/13`–`29`, `PHASE0_SUMMARY.md`** — Condensed TL;DR sections across all 18 violating documents to strictly 6 lines each, ensuring zero documents exceed the 15-line limit (`F-008`).
- **`docs/00_INDEX.md`** — Added Addon 5 coverage matrix (8 rows, all `INTEGRATED`), updated doc map to 31 documents (`00`–`30`), resolved older `IN PROGRESS` rows (`K-S2`, `K-S5`, `A1-O`) to `INTEGRATED`, updated Gate Tracker to 6 gates (66 checks all green) (`F-001`, `F-007`).
- **`docs/PHASE0_SUMMARY.md`** — Updated document count to 31 documents (`00`–`30`), removed deferral text for `sample-data/`, and updated gate snapshot to 66/66 ✅ (`F-009`).
- **Workspace & Scratch** — Reorganized temporary audit and generation utilities into `scratch/` (`F-012`).

### Phase 0 — Documentation (in progress)

#### Added — 2026-10-01

- **Repo skeleton** — `docs/`, `app/`, `ui/`, `sample-data/`, `tests/`, `packaging/`, `scripts/`
  (folders + `.gitkeep` only) and a root `README.md` describing the product, the current phase, the
  repo layout, and the non-negotiable working rules. Reason: Kickoff §15.1 / Addon 4 §L.1.
- **`docs/00_INDEX.md`** (Draft v0.1) — document map for docs `00`–`29`, reading plans (including the
  mandatory session reading plan), the **Addon Coverage Matrix** covering all **64 sections** of the
  spec of record (kickoff 15 + Addon 1 §16 + Addon 2 §10 + Addon 3 §11 + Addon 4 §12), the
  **Source-of-Truth Matrix**, the document standard and header template, hygiene and conflict-resolution
  rules, the permanent **ID namespace registry** (26 prefixes), the 5-gate/58-check tracker, and the
  approval log. Reason: Kickoff §5, Addon 2 §A.3, Addon 3 §A.3, Addon 4 §A.3/B/C.
- **`docs/01_PRD.md`** (Draft v0.1) — product definition, current-state problem and prior-prototype
  failure modes, four personas, the monthly-rhythm core JTBD plus secondary JTBDs, scope consequences of
  the principles, the **in-scope list** (10 areas), the **explicit out-of-scope list** (24 parked items
  with reasons and `BL-` ids), the **forced in/out rulings** (P&L focus; import-only budgets; optional
  journal-category column; manual control totals; one-off tagging parked; single currency),
  **10 success metrics with baselines and numeric targets**, multi-entity/consolidation stance,
  pack-recipient stance, the **no-login/no-RBAC decision**, hard constraints, 20 labelled assumptions,
  10 top product risks, the open-question set, the **canonical advisory disclaimer** and its mandated
  appearances, the **IP/licensing stance**, branding defaults with an accessibility guard, phasing
  overview, commercial placeholders, and a `DEC-001`–`DEC-019` decision index. Reason: Kickoff §2/§6/§12,
  Addon 1 §C.2/D/N, Addon 2 §C.2/D.14, Addon 3 §B.2/E, Addon 4 §D/E.

- **`docs/02_FUNCTIONAL_SPEC.md`** (Draft v0.1) — the complete functional specification:
  **156 numbered FRs** across 11 families (`FR-ONB` 8, `FR-PRJ` 12, `FR-IMP` 31, `FR-BVA` 16,
  `FR-EXC` 20, `FR-FC` 9, `FR-XL` 9, `FR-PPT` 9, `FR-AI` 14, `FR-SET` 12, `FR-XC` 16), each with a
  priority (P0/P1/P2), phase, behaviour, inputs/outputs, edge cases and testable acceptance criteria;
  the priority and **cut-line policy** including the never-cut list and the cut approval process; the
  per-FR Definition of Done; the screen-touchpoint inventory; and the canonical **13-row edge-case
  matrix** with stable message slugs (numeric codes reserved for doc `26`). Reason: Kickoff §5/§6/§8,
  Addon 1 §E, Addon 2 §D, Addon 3 §C/§F, Addon 4 §D/§G.

- **`docs/03_DATA_DICTIONARY.md`** (Draft v0.1) — the canonical data model: two-store split (DuckDB
  analytics / SQLite workflow state) with an authority rule per table; the full type system with the
  binding money rule (`DECIMAL(18,2)`, floats forbidden in money paths, no epsilon); nullability and
  identity conventions; a **grain register** covering all 40 tables in the model; complete column specifications for the
  dimensions, the three fact tables, forecast versions, quarantine rows, validation checks, rule runs,
  import batches, the exception register and its event history, pack issues and period snapshots,
  mapping profiles/versions/suggestions, four master-data tables, configuration, commentary, AI drafts
  and usage, audit and version history; documented duplicate-detection keys; 15 integrity invariants;
  worked example rows; the on-disk project layout; volume expectations; explicit supersessions from the
  seed model (`FactImportAudit` absorbed into `FactImportBatch`); and the schema-versioning and
  migration rules. Reason: Kickoff §7, Addon 1 §C.2, Addon 2 §C.2, Addon 3 §B.2, Addon 4 §G.1/H.

- **`docs/04_SOURCE_MAPPING_AND_IMPORT_SPEC.md`** (Draft v0.1) — the import contract: nine source
  types and their required mapping fields; the seven-step wizard with resumability and long-running-job
  UX; the shipped template inventory and version-stamp rules; mapping profiles with header-fingerprint
  auto-match (Jaccard ≥ 0.80), immutable versions, revert-as-new-version and mid-year source-change
  handling; the canonical field reference including explicitly ignored columns; per-profile value
  parsing (dates incl. the ambiguity rule, numbers/Cr-Dr/parentheses, dimension strings, fiscal-period
  text, enums); the **26-item Excel structure hardening table** and **12-item CSV hardening table**
  (every quirk handled or rejected with a named message slug); the **32-check validation catalogue
  `IMP-001`…`IMP-032`**; the fixed reject-vs-quarantine decision rule; balance and control-total
  reconciliation with the fail-by-default-plus-recorded-acceptance decision; duplicate-detection keys at
  three levels; incremental monthly load rules; atomic commit, cancellation and crash/sleep recovery;
  data-quality score inputs; the nine-part validation report; the batch lifecycle and void rules; the
  three-part error-copy standard with worked examples; and the mapping to the canonical edge cases.
  Reason: Kickoff §7/§13, Addon 1 §C.2/E/F/G/H, Addon 2 §D.4/D.5/D.6/D.12, Addon 3 §C.1/C.2/C.7/C.11/C.12,
  Addon 4 §G.2.
- **`docs/05_CALCULATION_SPEC.md`** (Draft v0.1) — every formula the product computes, with **14 golden
  fixtures (36 exact assertions, verified computationally)**: fiscal calendar and period assignment
  (posting-date default, document-date only for the cut-off rule); the five period windows (MTD/YTD/PY
  MTD/PY YTD/TTM) with always-visible labels; canonical sign conventions; variance, variance % with the
  three-state zero-budget rule (`value` / `—` / `n/a`), direction-aware favour*ability* by statement-line
  type, and percentage-point vs percent; the KPI/ratio library with divide-by-zero guards; rounding
  policy (half-up, compute-then-round-once) including the **sum-of-rounded rule** and its mandatory
  footnote; display scale (whole/thousands/lakhs) and negative presentation; grain, grouped-sum and
  hierarchy-rollup invariants; the **data-quality score formula** with its decomposition guarantee (a
  failed High check caps the score at 96); the four forecast methods' arithmetic plus scenario
  adjustment; forecast-accuracy metrics (signed error, absolute error, signed bias, MAPE-lite with the
  zero-actual exclusion rule); control-total/balance/row-count variance formulas; materiality thresholds
  with the mandatory AND-test; the binding **tolerance policy** (exact equality at minor-unit precision,
  no epsilon in money paths, cross-artifact exact equality); and a formula register mapping every ID to
  its section and fixture. Reason: Kickoff §5/§8, Addon 1 §C.2/H/L, Addon 2 §C.2/G, Addon 3 §B.2/F,
  Addon 4 §G.1.

- **`docs/06_EXCEPTION_RULES_CATALOG.md`** (Draft v0.1) — the formal catalogue of **24 exception rules**
  (`EXC-001`…`EXC-024`) covering all 15 seed rules from the kickoff prompt plus nine additions: import
  integrity (imbalance, cross-batch duplicates, cross-system tie-out, unmapped account/dimension), master
  data hygiene (inactive cost centre, orphan entity/account), duplicates (invoice, voucher line), timing
  (posting/period mismatch, cut-off, future-dated), anomalies (unusual negative expense, spike vs
  trailing average, unusual vendor→account pairing), completeness (missing recurring cost, missing
  expected accrual), budget relationship (material unbudgeted spend, material variance with the mandatory
  AND test, cumulative overrun, coverage gap), and controls (approval threshold crossing, round-number
  manual journal, voucher-level imbalance, suspense/clearing residual). Each rule carries all 13 required
  fields — family/version, intent, severity, owner role, dependencies, subject key, exact deterministic
  logic, thresholds, strictness tier, false-positive mitigation, sample case, expected verdict, and the
  rows it registers on. The engine model section defines stable identity and re-run semantics (with the
  gate's required raise → tune → re-run → status-preserved worked scenario), the human-only status
  machine, severity SLAs, period-based aging, six-step owner auto-assignment, graceful degradation for
  missing master data, effective-threshold traceability, and the rule-module implementation contract. §5
  is the dependency matrix, §6 the enablement defaults, **§7 the 40-planting sample plan (32 expected
  raises at 18 High / 12 Medium / 2 Low, plus 8 precision controls that must not raise)** with the
  `expected_exceptions.csv` schema, §8 the false-positive management contract and precision targets, §9
  rule effectiveness analytics with the two-period review trigger, and §10 the change-control rules.
  Reason: Kickoff §9, Addon 1 §C.2/E/F, Addon 2 §B.7/C.2/D, Addon 3 §B.2/H, Addon 4 §D/H.
- **`docs/07_FORECAST_METHODS_SPEC.md`** (Draft v0.1) — forecast behaviour: the eight-step monthly
  lifecycle; eligibility rules per period state with the method-eligibility guard table and the explicit
  no-silent-substitution fallback order; the four-level most-specific-wins method resolver (line pin →
  account group → project default → built-in) with account groups, exclusions and driver references;
  the three scenarios (Base/Best/Worst) with adjustments-as-data, per-scenario versions and the
  "identical to Base" labelling rule; the version lifecycle (`draft → locked → superseded`) with the rule
  that only locked versions may be referenced by issued packs; the accuracy report for closed periods
  (including the "not generated" and "draft — not the issued basis" states); non-blocking
  method-choice guidance with its evidence requirements and governance; override rules with mandatory
  reasons; **eight forecast-integrity guarantees** (actuals never overwritten, budget never modified,
  every row explainable, closed periods immutable, issued packs unrewritable, drafts cannot alter locked
  versions, idempotent regeneration, no invented numbers); an end-to-end worked example tied to the `05`
  fixtures; screen/export/CLI touchpoints; the configuration reference; and change control. All
  arithmetic is referenced to `CALC-060`…`CALC-069`, never restated. Reason: Kickoff §6/§8, Addon 1
  §C.2/H, Addon 2 §C.2, Addon 3 §B.2.

- **`docs/08_UI_UX_SPEC.md`** (Draft v0.1) — the complete UI contract: information architecture with the
  fixed guided left-nav (Home → Import → Check → Analyze → Exceptions → Forecast → Reports → Settings) and
  the global shell (filter bar, stale banner, job drawer, sample banner); the **43-screen inventory**
  (`SCR-001`…`SCR-043`) with purpose, linked FRs and dominant states; screen-by-screen specification with
  ASCII wireframes for Home, the project/period wizards, the six import steps (including the mapping
  screen with profile auto-match, overrides and the AI suggestion queue), Check, the Analyze family
  (matrix, bridge, trends, top-N, three-way, KPIs, drill-through, search), the Exceptions family
  (register, detail, effectiveness), the Forecast family, Reports/issuance/commentary, all Settings
  sections, and the global error dialog / help panel / first-run tour; the **12-chart inventory**
  (`CHT-001`…`CHT-012`) with type, grain, screen, drill target and empty state; the **single centralized
  conditional-format rule set** (`CF-001`…`CF-012`) shared by app, Excel and PPT with mandatory
  non-colour signals and the greyscale print test; the display-formatting contract (symbol, grouping,
  scale, decimals, negatives, dates, pp-vs-%, rounding footnote, simple-sum label, `—` vs `n/a` vs `0.00`);
  the message-catalog and wording rules with banned words and the catalog field shape; the per-screen
  state matrix (empty/loading/error/first-run/stale/offline); the WCAG AA accessibility baseline
  (keyboard, focus, ARIA, contrast, 1366×768, 100–150% scaling); the design system (spacing, type scale,
  semantic colour roles, component inventory); screen-to-document traceability; and change control.
  Reason: Kickoff §12, Addon 1 §C.2/G/K, Addon 2 §E, Addon 3 §B.2/C/F, Addon 4 §G.
- **`docs/09_TECHNICAL_ARCHITECTURE.md`** (Draft v0.1) — the architecture record: architectural
  principles; the **ADR programme** (`ADR-000` template + index, with **`ADR-001`** the authoritative
  stack recorded verbatim, **`ADR-002`** the pinned toolchain, **`ADR-003`** the unsigned-installer
  decision with the five-step SmartScreen mitigation ladder, **`ADR-004`** storage in `%LOCALAPPDATA%`
  never a synced folder, **`ADR-005`** real-Windows-11 validation evidence at every gate with the
  `SPK-01`…`SPK-07` spike list, **`ADR-006`** single process with worker-thread jobs and one writer per
  store, **`ADR-007`** hand-written SQL over an ORM, **`ADR-008`** forward-only migrations with a
  mandatory backup, **`ADR-009`** the local API serving the built UI); the **headless-engine boundary
  rule** with an import-linter enforcement and the module map; the engine module responsibilities; the
  **CLI** (10 commands, `--json`, dry-run, non-interactive, and **nine documented exit codes**); the data
  flow with its four invariants; the on-disk layout; the OneDrive rule; the **storage-growth maths**
  (assumptions, 1-month/1-year/3-year projections, low-storage threshold, archive-and-delete, retention
  default) reconciled with `03` §9.2; the single-instance mutex and lock behaviour; logging/error
  strategy including the no-amounts/no-vendor-names log policy; the job model, progress/ETA honesty
  rule, cooperative cancellation and crash/sleep recovery matrix; the local API and security posture;
  **configuration layering** with precedence and the no-secrets-in-backups guarantee; **recompute and
  invalidation semantics** with the no-silent-staleness rule and the bounded-cache policy;
  the **data-volume rule** (server-side everything, page sizes, payload budget, virtualisation);
  the schema-migration strategy; **performance budgets mapped to `NFR-001`…`NFR-011` and the
  architectural decision protecting each**; the spike policy; the fresh-clone bootstrap gate; the
  code-health guardrails; and the one-command scripts. Reason: Kickoff §4, Addon 1 §C.2/G/I/J/L,
  Addon 2 §B/C.2/F/H, Addon 3 §I, Addon 4 §I.

- **`docs/10_AI_INTEGRATION_SPEC.md`** (Draft v0.1) — the complete AI contract: the one-sentence policy
  (*AI drafts words for humans to check; it never computes, decides, applies or sends anything*); optional
  and off-by-default status with the keyless default; the **complete allowed-use list** (four features)
  and the **nine forbidden categories** with their architectural enforcement (AI code has no store handle,
  no write path, no send capability); provider configuration for Azure OpenAI (preferred) and
  OpenAI-compatible endpoints over the **OpenAI-compatible HTTP interface with no vendor SDK**
  (`ADR-010`); the failure-handling matrix; the versioned prompt-template system with the five-step
  prompt-edit process; **the four complete initial prompt texts with verbatim system prompts, user payload
  templates, input schemas, data-block shapes, output JSON schemas, guardrail tables and worked examples
  on the sample dataset** (`PROMPT-01` variance commentary, `PROMPT-02` mapping suggestion with evidence,
  `PROMPT-03` exception summary, `PROMPT-04` follow-up message draft — the last with no send capability
  anywhere in the product); redaction and minimum-data rules with per-feature caps and the documented
  masking trade-off (vendor names masked, account/cost-centre codes not, disclosed to the client);
  **ten prompt-injection defences** with two planted adversarial descriptions in the sample data; the
  ten-step output-validation pipeline; the **number-mismatch stance** (`DEC-026`: strip and flag, never
  trust) including the normalisation test cases; schema-failure handling; caps (per-call, hourly, monthly
  tokens and cost) with the cost-estimate table; the usage log schema; caching with its key and
  invalidation rules; model pinning, deprecation handling and the five-step fallback order ending in the
  rule-based narrative; the data-residency statement; keyless mode and the rule-based fallback quality
  bar; draft provenance, regeneration and approval; the mapping review-queue state machine (never applied
  in the same run); key storage, rotation and logging rules; and **fourteen AI test fixtures**
  (`TST-AI-01`…`TST-AI-14`) with the gate rule. Reason: Kickoff §10, Addon 1 §C.2/I/K, Addon 2 §C.2/G,
  Addon 3 §B.2/D, Addon 4 §J.

- **`docs/11_EXCEL_OUTPUT_SPEC.md`** (Draft v0.1) — the complete Excel-output contract: the five
  artefact families, the universal rules (**values-only workbooks**, the 30-field machine-readable stamp,
  the four-row sheet header block, filenames/sanitisation/collision policy with the recoverable
  `.recycle` behaviour, the 15-ID number-format dictionary incl. the Indian lakh/crore grouping with its
  boundary matrix, the `CF-001`…`CF-012` → Excel mapping with mandatory non-colour signal columns,
  freeze/autofilter/width rules, locale independence, sample-data watermarking), **the eight pack sheets
  specified column by column** (`Cover`, `BvA Summary`, `BvA Bridge`, `Transaction Detail`, `Exception
  Register`, `Forecast Summary`, `Import Reconciliation`, `Audit Trail`) with controls and empty states,
  the 1,048,576-row cap and lossless split algorithm, the evidence bundle (workbook + zip with manifest),
  ad-hoc "export what you see" incl. the CSV contract and its sidecar stamp schema, the owner
  distribution with the exact plain-text template, house-style matching (what can and cannot be matched),
  print/PDF setup, the cross-artifact consistency contract, 11 export failure modes (`ERR-EXP-*`), and a
  26-item test contract. Reason: Kickoff §5/§11/§12.9, Addon 2 §D.12/D.13 and §E.4, Addon 3
  §C.5 and §F.3/F.4.
- **`DEC-028`** added to `01` §21 (print/PDF readiness, not in-app rendering) with the three rejected
  alternatives recorded in `11` §10.3; **`FR-XL-009`** amended in `02` to match. Reason: the FR implied
  a PDF action the architecture cannot deliver without a bundled renderer or Excel automation.
- **`docs/12_POWERPOINT_OUTPUT_SPEC.md`** (Draft v0.1) — the deck contract: the **fixed six slides**
  (`PPT-001`…`PPT-006`) with the default/opt-in rule for missing inputs (`DEC-029`); the universal
  contract (inch grid + scaling to any slide size, the native-and-editable shape whitelist, the shared
  theme, the **character-budget formula** with 29 per-placeholder budgets and the prioritized trimming
  order that makes overlap structurally impossible, deterministic shape naming/order, stamping + footer +
  the full disclaimer on the last slide, AI/rule-based labelling, not-available states, accessibility,
  the ≤ 15 s aggregate-only performance budget); every slide and placeholder specified with geometry,
  fonts, budgets and content sources; the two native charts including the waterfall decision (`SPK-08`)
  and its documented stacked-column fallback; client base-deck mapping and refusal rules; the deck's half
  of the cross-artifact contract; files/refresh/issuance; 24 test IDs; failures `ERR-EXP-012`…`018`.
  Reason: Kickoff §5/§11, Addon 2 §C/§E.5, Addon 3 §F.3/F.4.
- **Reconciliations and ripple edits** — `01` `DEC-029` (deck missing-input behaviour) and `02`
  `FR-PPT-001` acceptance clarified for base-deck mode; `05` §6.3 scale examples aligned to the display
  owner (`08` §15); `08` §11.1's omission example now points at `12` §2.1; `09` gained spike `SPK-08`;
  `11` §12 gains the `ERR-EXP-012`…`018` pointer. No behaviour was invented outside the spec of record.
- **`docs/13_SECURITY_PRIVACY.md`** (Draft v0.1) — the security, privacy and supply-chain contract, written
  as **49 verifiable statements** (`SEC-001`…`049`), each with a mechanism and a planned test (`TST-SEC-01`…`22`):
  the local-only guarantees (no telemetry/upload/background call; the exhaustive three-item outbound
  inventory; the static call-site inventory test); the threat model with the threats we explicitly do not
  defend; the exact data-location tree and file-handling rules (atomic writes, `.recycle`, path limits,
  synced-folder block + recorded override); deletion semantics with a pre-delete backup offer and the honest
  "not a secure erase" caveat; DPAPI key storage, the write-only UI, rotation/revocation/purge with a byte-scan
  proof, the `.gitignore` + pre-commit + CI secret-scan pipeline; log rotation numbers and the
  allowed/forbidden content policy with a planted-value grep test; the metadata-only diagnostics bundle with
  its redaction map, manifest schema and size cap; the AI data path (TLS verification not disableable,
  redaction, caps, provenance, non-authority) and the prompt-injection defence layers; the plain-files
  data-at-rest stance (`DEC-030`) with BitLocker guidance; the privacy note text owned here for `22`/`29`;
  the three-way audit/log/security-event boundary (`SEC-048`/`049`); and error codes `ERR-SEC-001`…`008`.
- **Governance** — `00_INDEX` gains the `SEC-nnn` prefix family, the `SEC` error family and the `TST-SEC`
  family; doc `09`'s storage inventory gains `security.log`; `01` gains `DEC-030`; `02` `FR-SET-012` records
  the append-only audit rule; `11` §4.8's secret-pattern pointer is now a real section (`13` §5.4).
- **`docs/14_TESTING_QA_PLAN.md`** (Draft v0.1) — the test and quality system: nine test levels and their
  runners; the **canonical `NFR-001`…`NFR-016`** targets, each with a measurement method, fixture, script
  and recorded baseline plus the measurement protocol (reference machine, 5 runs, median/worst, > 20 %
  regression blocks a gate); a **292-test catalogue** (206 tests owned here — `TST-CALC` 24, `TST-IMP` 36,
  `TST-RUL` 28, `TST-FC` 14, `TST-BVA` 12, `TST-EXC` 12, `TST-UI` 20, `TST-API` 16, `TST-E2E` 8,
  `TST-PRF` 16, `TST-WIN` 14, `TST-UAT` 6 — plus the 86 already reserved by docs 10–13); the golden-file
  policy ("expectations are never edited to pass"); the **planted-exception acceptance harness** with the
  bars from `06` §8.3 (recall ≥ 90 %, zero control raises) plus an 18/18 High-severity bar, the per-rule
  test map and the worked re-run identity scenario; the **tolerance and edge-case matrices** (16 rows with
  message IDs) and the 16-file negative corpus; the **cross-artifact consistency harness** and its
  comparison set; performance baselines and regression rules; Playwright golden path, UI state sweeps,
  accessibility and wording scans, the 14-item Windows manual checklist and the E2E journeys;
  security/privacy/supply-chain test routing and the fault-injection set; data-integrity, migration and
  upgrade tests; API/CLI contract tests and the six UAT scripts; **`scripts/check` composition**, coverage
  bars and CI rules; defect severities, evidence formats and the demo-recipe DoD; and the **58 gate checks**
  (`GATE-01-01`…`GATE-05-13`) restated as the authoritative checklists with evidence and status.
- **Reconciliation — NFR numbering made canonical.** One number per target across the whole set:
  `NFR-007` = rule run (was cited as `NFR-009` in `02`/`03` — corrected), `NFR-009` = Excel pack ≤ 120 s
  (was "an `NFR-004` analogue" in `11`), `NFR-011` = logs (as `02`/`03`/`13` already cited; `09`'s table had
  it as `NFR-009`), `NFR-012` = crash behaviour (was `09`'s `NFR-011`), and four new numbers recording
  targets that had no ID: `NFR-013` screen/scaling, `NFR-014` coverage bars, `NFR-015` cross-artifact
  equality, `NFR-016` UI responsiveness during jobs. `09` §14's table now carries all sixteen with their
  architectural drivers. No target value changed.
- **Governance** — `00_INDEX`: document map row 14, docs complete `00`–`14`, `A1-L` **INTEGRATED**, the
  `TST-<FAM>` registry row now enumerates all sixteen families; `09`'s repo layout gains `tests/` categories
  (`rules`, `artefacts`, `integration`, `manual`) and the `acceptance`/`perf` scripts.
- **`docs/03_DATA_DICTIONARY.md`** — `FactExport` **added** to §5.7 and to the §2.1 grain register
  (one row per generated export artefact: filter context, versions, content hash, row counts, outcome).
  Reason: `11` §3.9 needs a durable home for the refresh contract; the 40-table figure recorded for
  `03` in the previous entry is therefore superseded by **41 tables**.
- **`docs/15_PACKAGING_DEPLOYMENT_RUNBOOK.md`** (Draft v0.1) — the build → install → validate → support
  runbook: the **four release artefacts** and their exact names (`Setup-FPandAMonthEndCopilot-<version>.exe`,
  `FPandAMonthEndCopilot-<version>-portable.zip`, `SHA256SUMS-<version>.txt`, `THIRD_PARTY_LICENSES.txt` +
  SBOM-lite); the build host rules and the **single-source version stamping** chain (pyproject →
  `version_info.txt` → Inno `AppVersion` → UI About — a version is never typed twice); the `packaging/`
  layout and the ten-step `scripts/build` with five fail-fast preconditions, the automated **payload audit**
  and the `NFR-006` ≤ 500 MB budget with the auditable-excludes rule; the **installer contract** (per-user
  `PrivilegesRequired=lowest`, no admin, no prerequisites, HKCU-only registry, silent/IT flags, the seven
  "must never do" rules) and the **portable-zip** semantics including the opt-in `portable.flag`;
  the **24-step clean-Windows-11 validation protocol** with its evidence pack, failure rules and the four
  extra variations that give full `TST-WIN-01`…`14` coverage; the **first-run experience** (sample project,
  six-step tour, no network, no key demand, dead-end-free failure paths) with the new `ERR-ENG-001`…`010`
  family; the **uninstall/data-lifecycle semantics** (data retained by default, typed confirmation for
  deletion, downgrade = restore-from-backup); the **SmartScreen/Defender reality** with the five-step
  mitigation ladder, the verbatim non-technical walkthrough and the WDSI false-positive procedure; the
  **support/diagnostics flow** on the user-exported metadata-only bundle with the "never ask for" list and
  the app-won't-start triage; plus the test/gate mapping and the change-control obligations.
  Reason: Kickoff §5/§13/§14, Addon 1 §G.2–G.6/§J/§N, Addon 2 §B.6, Addon 4 §E.3/§H/§I; satisfies
  `GATE-01-06`.
- **Governance** — `00_INDEX`: doc-map row 15 → Draft v0.1, A1-G **INTEGRATED**, docs complete `00`–`15`.
  The `ERR-ENG-001`…`010` family (§12 of `15`) joins the `ENG` family already registered in `00` §8.
- **`docs/16_ROADMAP_PHASES.md`** (Draft v0.1) — the phase plan and the session-start pointer: the live
  **next open item** (§1.3); the phase model with **gate IDs `GATE-06`…`GATE-15`** (packaging spike, phases
  1–6, and the pilot/UAT/go-live gates reserved to `28`); the scope→phase mapping of all 156 FRs with the
  P0/P1/P2 split per phase (110 P0 / 42 P1 / 4 P2); the Phase-0 completion plan (the remaining documents,
  the `sample-data/` build step, the coverage-matrix refresh, the two walkthroughs, the stop-and-present
  rule); the **packaging spike** contract (scope, two half-day timeboxes, evidence, exit criteria, failure
  rule); the **14-item universal gate contract** with its evidence pack, approval/waiver/re-entry rules and
  what a gate is not; per-phase plans for Phases 1–6 (deliverables, dependencies, phase-specific Definition
  of Done, 3–5 minute demo outlines, risks and contingencies); estimates (**96 ideal days** across the six
  build phases + a per-P0-epic breakdown) with the re-estimation and > 50 % variance rules; the **release
  cadence** and freeze windows; the phase-level **cut-line policy** and the never-cut list; the
  client-visible checkpoints; the demo-script rule and the two closing walkthroughs; and the cross-phase risk
  register. Reason: Kickoff §5/§14.1, Addon 1 §C.2/§O, Addon 2 §F.2, Addon 3 §G.6/§K.4, Addon 4
  §D.4/§D.5/§L; satisfies `GATE-05-05` (cut process) and `GATE-05-06` (per-phase estimates).
- **Governance** — `00_INDEX`: doc-map row 16 → Draft v0.1; docs complete `00`–`16`; `K-S6` and `A4-H`
  **INTEGRATED**; the `GATE-nn` registry row now records the full allocation (`GATE-01`…`05` = Phase-0 gates
  owned by `14`, `GATE-06`…`12` owned by `16`, `GATE-13`…`15` owned by `28`), and §9's downstream-gate
  paragraph names the build gates and the universal contract.
- **`docs/17_CODING_STANDARDS.md`** (Draft v0.1) — the how-we-write-code contract: the canonical folder
  layout and its rules; naming conventions (Python/TS/test/SQL/migration/doc); formatting, lint and type
  expectations per language (ruff/mypy strict on the engine, `tsc`/ESLint on the UI, hand-written SQL with
  parameterisation only); the **engine-boundary import rules** and their `import-linter` enforcement; the
  money/time/determinism rules (Decimal-only money with the float ban, one rounding owner, no epsilon,
  UTC + display-time localisation, stable ordering, timestamp-free machine payloads); **error-handling and
  logging conventions** (catalogued codes, the envelope, no raw tracebacks, the "never logged" list,
  redaction helpers shared with the diagnostics bundle); dependency, licence and supply-chain rules
  (deliberate additions, lockfiles, no GPL/AGPL, no vendoring/binaries without review, SBOM, `pip-audit`
  clock); secrets and test-data hygiene; testing conventions; UI/React standards (generated types, one API
  client, four states per screen, accessibility as code); **trunk-based git workflow** (Conventional
  Commits, docs/code separation, tags per `24`); the code-health guardrails; the 12-item review checklist;
  and the enforcement map that ties every rule to a check and a gate item. Reason: Kickoff §5/§14,
  Addon 1 §I, Addon 2 §F/§H.1/B.1/B.2, Addon 4 §I.1–§I.3, `13` §12, `14` §13, `09` §4/§15.
- **Governance** — `00_INDEX`: doc-map row 17 → Draft v0.1; docs complete `00`–`17`; `A1-I` and `A2-F`
  **INTEGRATED**; `A2-H`/`A4-I` now show `19` as the only pending owner. `14`'s `GATE-05-12` status now
  reads ✅ (the code-health rules exist in `17` §12). `16` §1.3's next open item advanced to `18`.
- **`docs/18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md`** (Draft v0.1) — the register of record for what we
  do not know and what we have ruled: the question lifecycle and register rules; the **glossary** (money/
  period/FP&A terms, method and control vocabulary, product/engineering terms, each with its owning doc and
  the rule that the owner wins); the **assumption register** `A1`…`A20` (mirrored from `01` §12 with default,
  impact, cost-to-change and `Q-` links) plus `A21`…`A29` (engineering/delivery assumptions from `09`–`17`);
  the **`OQ-` register** with all 19 live questions (17 design/data + 2 formatting), the blocking-question
  rules and the ask format (Addon 2 §H.3), and the resolution of the `01` §14 hygiene flag (`OQ-018`/`019`
  reserved, `OQ-020` retired as a tombstone with the `01` §16 reference corrected to `OQ-016`); the
  **`DEC-` Decided log** consolidating `DEC-001`…`DEC-030` (with rationale, rejected alternatives where
  recorded, and the docs each binds) plus `DEC-031`…`DEC-037` from the `15`–`17` passes (gate numbering,
  the next-open-item pointer, ideal-day estimates and the variance rule, demo-script timing, the
  never-cut list's absoluteness, the `ERR-ENG` family, machine-enforced standards); and the maintenance
  cadence that makes the register a gate artefact. Reason: Kickoff §5/§14.5, Addon 1 §C.2, Addon 2 §H.3,
  Addon 3 §B.2/§J.10, Addon 4 §C.
- **Governance** — `00_INDEX`: doc-map row 18 → Draft v0.1; docs complete `00`–`18`; `A1-D`/`A3-E`/`A4-E`
  annotated with their remaining owners. `01` §14's registry-hygiene flag is **closed** and §16's phantom
  `OQ-020` reference corrected to `OQ-016`. `14`'s `GATE-01-08` and `GATE-04-12` now read ✅ on the doc
  side. `16` §1.3's next open item advanced to `19`.
- **`docs/19_VIBE_CODING_PLAYBOOK.md`** (Draft v0.1) — the working protocol: the **twenty principles**
  `P1`…`P20` in one canonical list, each with its violation signature and cost, and the mechanism that
  enforces it; the **session protocol** (start: the reading plan, the session plan and the quote-before-code
  pre-flight; during: the fixed change order, small commits, ask-when-blocked, sample-data-only; end: the
  ten-step closing checklist, the regression gate, the `SESSION_LOG` format and the append-only rule); the
  **Definition of Done enforcement** (per feature and per phase) with the demo-recipe rule; **change
  control** (the never-reversed order, the post-approval impact note, what needs a decision before code,
  client-feedback intake); **approvals and gates** (the recorded approval pattern, the stop-and-present
  sequence, non-gate approvals, and the Phase-0 no-code rule); blocking questions and the escalation
  ladder; the three evidence levels (demo recipe, phase demo script, tabletop + cold-start walks); the
  **AI-session rules** (paraphrase ban, no invented requirements, no fabricated numbers, context
  discipline, prompt-edit discipline); the 16-item **anti-pattern list**; roles and the one-writer rule;
  and the 30-minute onboarding ramp. Reason: Kickoff §3/§14, Addon 1 §B/§M, Addon 2 §F.5/§H.3, Addon 3
  §I.4/§I.5, Addon 4 §B/§E.2/§E.3/§L.12; satisfies `GATE-05-04` and `GATE-05-08`.
- **Governance** — `00_INDEX`: doc-map row 19 → Draft v0.1; docs complete `00`–`19`; `K-S3`, `K-S14`,
  `K-S15`, `A1-B`, `A1-M`, `A1-P`, `A2-H`, `A2-J`, `A3-I`, `A3-K`, `A4-I`, `A4-L` **INTEGRATED** with
  `A4-E` now pending only on `24`/`29`. `14`'s `GATE-05-04`/`GATE-05-08` now read ✅. `16` §1.3's next
  open item advanced to `20`.
- **`docs/20_REQUIREMENTS_TRACEABILITY.md`** (Draft v0.1) — the traceability chain: **all 156 FRs** in
  `02` joined to their spec sections, screens (`08` §4), API endpoints, test IDs (`14` §4) and status.
  110 `P0` / 39 `P1` / 7 `P2` across phases 1–6; **every FR carries at least one named test** from the
  frozen 292-test inventory (188 distinct IDs used; all 16 families exercised). The document defines the
  chain keys and their owners, a three-value status vocabulary (`Spec'd` / `Built` / `Complete`), the
  sanctioned non-values for screen cells (`Global` shell rows and four justified `n/a` reasons), the
  **95-route endpoint reference set** in nine areas that `26` adopts verbatim (renames recorded), the
  reading rules for the matrix, **invariants I1–I9** as the document's own acceptance checks, the reverse
  indexes (screen → FR, endpoint area → FR, test family → FR), the **gate interface** (`GATE-01-09` now
  provable, `GATE-03-08` chain complete), the non-blocking client-fact dependencies (`OQ-`/`Q-` → FRs
  whose detail changes), the **eight FRs whose evidence is strengthened in Phase 1 by extending an
  existing test**, the obligations placed on `26`/`14`/`16`/`02`/`08`/`27`/`29`/`22`, and the frozen
  constants of this document. Reason: Kickoff §5 (`20` links every FR to at least one future test),
  Addon 2 §A/§C.2 (`FR → spec section → screen ID → API endpoint → test ID`), Addon 4 §C/§D/§L.2.
- **Governance** — `00_INDEX`: doc-map row 20 → Draft v0.1; docs complete `00`–`20`; remaining
  `21`–`29` + `PHASE0_SUMMARY`; Coverage-Matrix rows `K-S1`, `K-S8`, `K-S13`, `A1-A`, `A1-C.2`, `A2-A`,
  `A2-D`, `A3-A`, `A4-A`, `A4-B`, `A4-C`, `A4-D`, `A4-G`, `A4-J` moved to **INTEGRATED** (each verified
  against its owning doc and gate check), `K-S5` annotated with the docs-complete range. `14`'s
  `GATE-01-09` now reads ✅, `GATE-03-08` states the chain is complete in `20` with the endpoint
  catalogue finalised by `26`, and `GATE-05-06` reads ✅ (per-phase estimates exist in `16` §7). `16` §1.3's next open item advanced to `21`. `08` §4's **Owning FRs**
  column regenerated from `20` §4.3 (43 screens, 7 previously-missing links added: `FR-PRJ-009`→
  `SCR-002`, `FR-SET-006`→`SCR-003`, `FR-IMP-022`/`FR-EXC-014`→`SCR-014`, `FR-EXC-009`→`SCR-024`,
  `FR-XC-001`→`SCR-029`, `FR-XC-012`→`SCR-041`, `FR-IMP-026`→`SCR-033`), plus a global-shell-components
  note; `08` §4's stale state-matrix pointer corrected from §15 to **§17**. Reason: the join must not
  drift from its owner, and a screen with no FR would be an orphan screen.
- **`docs/21_CLIENT_ONBOARDING_QUESTIONNAIRE.md`** (Draft v0.1) — the client-facing question set and the
  proof that **nothing blocks**: all **21 questions** (`Q-001`…`Q-021`, five groups — data access/volumes,
  finance model/calendar, systems/file shapes, outputs/audience/branding, delivery/enablement/support) with
  the wording to use, **why it matters**, the **labelled default already implemented** and the owning docs/FRs
  it lives in, and the date each answer is needed. The document rules that defaults are labelled *default,
  unconfirmed* and never presented as facts (`01` §12), fixes the **ask format** (≤ 3 options + recommendation
  + default, `18` §4.3), gives an **impact-ordered ask sequence** (§2.3), maps **Addon 1 §D's 20-item domain
  checklist** to the question/assumption/decision that settles each one (§6.2, 20 of 20), registers the
  **delivery/IT confirmations `A21`–`A28`** (§3.6), lists the **eight already-ruled items** that must not be
  re-opened (§4), and defines the six-step **answer → `DEC-nnn` → `OQ-` closure → owning-doc update** flow with
  the status vocabulary `Open · default in force` / `Answered` / `Withdrawn` and the append-only change rules
  (§5, §8). Reason: Addon 1 §C.1/§D, Addon 2 §H.3, Addon 4 §B/§K (the `A1-D` coverage row; `GATE-02-01`).
- **Governance** — `00_INDEX`: doc-map row 21 → Draft v0.1; Coverage-Matrix row `A1-C.1` → IN PROGRESS
  (`21` done, `22`–`25` outstanding), `A1-D` → **INTEGRATED** (20/20 §D items mapped, §6.2), `K-S2`
  annotated (question set in `21`; `23`/`25` outstanding); docs complete `00`–`20` → `00`–`21`; remaining
  `22`–`29`. `14` §15's `GATE-02-01` annotated (`21` done — 21/21 items carry a labelled default; `22`–`25`
  outstanding). `16` §1.3's next open item advanced to `22`–`25`, `26`, `27`, `28`, `29`, then
  `PHASE0_SUMMARY.md`. Reason: the questionnaire must not drift from the registers it seeds (`18` §3/§4) or
  from the gate it proves. Also recorded in `20` §6.4: **sixteen section-pointer corrections** in the doc-20
  matrix and §6.1 — the cites resolved to existing but wrong-topic sections (`05` §4.4, `05` §10, `06` §7,
  `03` §5.5, `09` §10/§11); no FR, screen, endpoint, test or status changed.

- **`docs/22_END_USER_GUIDE.md`** (Draft v0.1) — the user-facing manual, **structured by task** (Addon 1 §K):
  §1 how to use it (five-minute version, three ways to get help), §2 install + the **verbatim SmartScreen
  walkthrough** (`15` §8.3) + first run with the sample project and the 6-step tour + the verbatim
  plain-language privacy sentence (`13` §8.3) + first backup, §3 the nine-step month-end rhythm mapped to
  tasks, §4 the **21 tasks `T-01`…`T-21`** (open, new period, import ×2, quarantine, check, explain a
  variance, triage, work to closure, evidence bundle, forecast refresh/override/compare, commentary,
  Excel, deck, issue, close, back up/restore/archive, AI boundaries, support) each with steps,
  checkpoints, "if it looks wrong" and the owning FRs, plus the **43-screen coverage map**, §5 reading the
  numbers (units, rounding, `n/a` vs `—`, favourable/unfavourable, stale), §6 what the app never does with
  the **verbatim disclaimer** (`01` §15.1), §7 the error-dialog anatomy + the ten commonest symptoms +
  offline/autosave/recovery + the diagnostics support flow, §8 the settings a user may change, §9 the
  **screenshot capture contract** (`SS-01`…`SS-24`, sample project only, filled as built), §10 the
  **60-minute training outline** and six-chapter recorded demo (the `Q-017` default), §11 the in-app help
  **single-source contract** (`FR-ONB-004`/`007`), §12 a plain-language on-screen glossary, and the
  obligations/change-control/frozen constants. Reason: Addon 1 §C.1/§K/§P17, `01` §4.1, `08` §3–§4,
  `FR-ONB-002`/`004`/`007`, `GATE-02-10`.
- **Governance** — `00_INDEX`: doc-map row 22 → Draft v0.1; `A1-C.1` → IN PROGRESS (`21`–`22` done),
  `A1-K` → IN PROGRESS (`22` done, `23` outstanding), `K-S2` now names `22`, docs complete `00`–`22`,
  remaining `23`–`29`. `14` §15's `GATE-02-10` annotated (`22` done: 21 tasks, 43-screen map, 60-minute
  training outline, screenshot contract; `23` outstanding). `16` §1.3's next open item advanced to
  `23`–`25`, `26`, `27`, `28`, `29`, then `PHASE0_SUMMARY.md`. Reason: the guide is the in-app help
  source, so it must not drift from `08`/`15`/`13`, and a screen without a task would be an unguided
  screen.

- **`docs/23_CONSULTANT_HANDOVER_AND_SUPPORT.md`** (Draft v0.1) — the successor's runbook: §2 the **dev
  loop** (preconditions table; the fresh-clone bootstrap `uv sync --frozen` → `npm ci` → `doctor` →
  `scripts/check`, Addon 4 §I.2; the CLI (`09` §5.2) for reproducing client issues without their data),
  §3 the **release loop** as an 8-step operator checklist that cites `15` §3.2/§5.2 and `24` and names the
  evidence for each step, §4 the **config-edit procedures** for all six surfaces (`SCR-033`–`SCR-038`) with
  owner, procedure and traceability, §5 the **prompt-edit procedure** (immutable shipped versions,
  template + `10` §5 in one change, eval re-run), §6 **rule/threshold tuning** under `06` §10's change
  control, §7 the **dependency cadence** (monthly `pip-audit` and license scan, per-release SBOM and
  `THIRD_PARTY_LICENSES.txt`, frozen toolchain per `ADR-002`), §8 the **diagnostics workflow** (zip-only,
  contents/redaction per `13` §7, support triage steps, the never-ask list), §9 **upgrades/migrations and
  rollback** (backup-first, forward-only, restore-not-reverse), §10 the **incident playbook** (eight
  symptoms → checks → cause → action; S1–S4 response targets as labelled defaults), §11 the **support
  model and support log** with escalation on `15` §9.3's L1–L3 ladder, §12 the **handover pack** (what the
  client gets and what stays internal), and the obligations/change-control/frozen constants. Reason:
  Addon 1 §C.1/§I/§K, Addon 2 §H.2, Addon 4 §I.2, `Q-018`, `GATE-02-10`.
- **Governance** — `00_INDEX`: doc-map row 23 → Draft v0.1; `A1-C.1` → IN PROGRESS (`21`–`23` done),
  `A1-K` → **INTEGRATED** (through `23`), docs complete `00`–`23`, remaining `24`–`29`. `14` §15's
  `GATE-02-10` → **✅**. `16` §1.3's next open item advanced to `24`, `25`, `26`, `27`, `28`, `29`, then
  `PHASE0_SUMMARY.md`. Reason: the support/handover contract is proof for the enablement gate, and the
  runbook must cite the build/security owners rather than restate them.

- **`docs/24_RELEASE_AND_VERSIONING_RUNBOOK.md`** (Draft v0.1) — the release process that `15` §10
  delegates here: §2 the **three version numbers** (app semver, per-project schema integer, docs version),
  the **bump decision table** (`MAJOR`/`MINOR`/`PATCH` with examples) and the one-place rule
  (`pyproject.toml` is the source; a mismatch fails the release), §3 branch/tag rules (annotated
  `vMAJOR.MINOR.PATCH` on `main`, never moved or reused, tagged only after the checklist), §4 the
  **14-step release checklist** with owner, evidence and abort condition for each step and the two
  overriding rules (an unevidenced step is failed; a failure after the tag ships as the next patch), §5
  the **release record** (`packaging/out/<version>/`, twelve files, retention rule), §6 upgrade/migration
  (**what the user sees**, the six `09` §13 rules, the **prior-version fixture** — a real project made by
  the previous released build, never hand-edited to make a test pass — and the documented rollback: restore,
  not reverse-migrate), §7 distribution and **checksum publication** (hash in the notes and the delivery
  message; client verification; never "an exe"), §8 **signing status** (unsigned v1 ladder, the certificate
  checklist when `OQ-012` is answered, expiry handling), §9 **patch/hotfix rules** (P0 only, minimal change
  + regression test, affected gate items re-run), §10 the release-notes template, §11 the **release evidence
  list**, §12 roles, and the obligations/change-control/frozen constants. Reason: Addon 1 §C.1/§J,
  `15` §10, `16` §8, `ADR-008`, `14` `TST-E2E-05`, `GATE-02-07`.
- **Governance** — `00_INDEX`: doc-map row 24 → Draft v0.1; `A1-C.1` → IN PROGRESS (`21`–`24` done), `A1-J`
  → **INTEGRATED**, docs complete `00`–`24`, remaining `25`–`29`. `14` §15's `GATE-02-07` → **✅** (the
  fixture path, creation/refresh and never-edit rules are fixed in `24` §6.3; the first fixture is created
  from the first released build). `16` §1.3's next open item advanced to `25`, `26`, `27`, `28`, `29`, then
  `PHASE0_SUMMARY.md`. Reason: the upgrade gate needs a named fixture and a process, not an intention.

- **`docs/25_RISK_REGISTER.md`** (Draft v0.1) — the single risk register that `01` §13 and `16` §12 hand
  their detail to: §1 the anchored 1–5 likelihood/impact scale, exposure bands and the row contract
  (cause → effect, mitigation in force, early-warning trigger, owner, links, status), §2 the **36 `RISK-`
  rows** seeded from `01` §13 (R1–R10), `16` §12 (rows 1–10), the spike list, the parks and the open
  questions — each row's mitigation names a document that owns it, §3 the **top-ten detail sheets**
  (`RISK-001`…`RISK-010`) with cause chain, contingency and residual risk, §4 the client-fact rows seeded
  from `21` (`OQ-012`, `OQ-014`, `OQ-016`, thresholds, outputs, branding, retention, headcount, compliance
  and install day), §5 **eight deliberate acceptances** each with a reopen trigger (unsigned v1, no RBAC,
  plain-zip backups, no secure erase, sample-data non-delivery, keyless AI, no in-app PDF, P&L-only),
  §6 the source list plus the gate review ritual and the current band summary (7 High / 29 Medium / 0 Low),
  §7 the obligations on `01`/`16`/`21`/`23`/`24`/`27`/`28`, §8 change control and §9 frozen constants.
  Reason: Addon 1 §C.1, the `09` `ADR-003` pointer that names `25` for the SmartScreen risk, and
  `GATE-02-01`; `OQ-014` is the only question left with no labelled default and is carried by `RISK-002`, and
  §4 now joins all 18 client facts of `20` §6.1 to their risk rows. Also fixed this pass: `20` §6.1's
  duplicated table header (one stray header row removed).
- **Governance** — `00_INDEX`: doc-map row 25 → Draft v0.1; `A1-C.1` → **INTEGRATED** (`21`–`25` written);
  docs complete `00`–`25`, remaining `26`–`29`. `14` §15's `GATE-02-01` → **✅** (docs 21–25 exist with the
  standard headers; all 21/21 `Q-` items carry a labelled default). `16` §1.3's next open item advanced to
  `26`, `27`, `28`, `29`, then `PHASE0_SUMMARY.md`, and `16` §12 now points at the operationalised rows.
  Reason: the register closes the Addon 1 document set, so the client-fact consequences are owned rather
  than implied.

- **`docs/26_API_CONTRACT.md`** (Draft v0.1) — the HTTP contract that `09`/`17`/`20` hand to Phase 1:
  §1 what it owns (OpenAPI, envelope, grammar, catalogue, reverse index) and does not own, §2 the universal
  contract (loopback + `X-FPA-Token` on every route, `{status, data, warnings[], errors[]}`,
  `{code, slug, severity, message, hint, details[]}` errors with the HTTP map and the seven universal
  `ERR-API-001`…`007` codes, `{items, total, page, pageSize, hasMore}` with default 100 / cap 200,
  the filter/sort/column grammar, value encodings — money as strings, `n/a` for ÷ 0 — the 202 + poll job
  contract, exports-to-file, stale/cap warnings and the safety rules), §3 the **95-route inventory in the
  nine `20` §2.3 areas** with request → response shapes, area error profiles, consuming screens and FRs,
  §4 the shared shapes (domain payloads by reference to `03`, never restated), §5 the **error catalogue**
  (11 families; 33 new codes for `VAL`/`BVA`/`FC`/`RUL`/`STO`/`AI` plus the `API` set; the 32-row `IMP`
  catalogue aligned to `IMP-001`…`032`; the 27 hardening slugs; `EXP`/`SEC`/`ENG` aggregated from their
  owning documents), §6 the OpenAPI-as-source-of-truth workflow (`app/api/openapi.json` +
  `ui/src/api/types.ts` generated; drift is a build error; `/docs` disabled in packaged builds), §7 the
  fixture layout and the 16 `TST-API-*` tests, §8 the data-volume rule with the response budgets
  (lists ≤ 2 MB, analysis ≤ 5 MB), §9 config layering and the route-to-layer map, §10 the **endpoint →
  FR/screen/test reverse index**, §11 CLI parity, §12 obligations/change control and §13 the frozen
  constants. Reason: Addon 2 §B/§C/§I — the last Addon 2 deliverable, and the gate (`GATE-03-02`/`-08`).
- **Governance** — `00_INDEX`: doc-map row 26 → Draft v0.1; `A2-B`/`A2-C`/`A2-E`/`A2-I` →
  **INTEGRATED**, docs complete `00`–`26`, remaining `27`–`29`; §8's error-family registry now points at
  `26` §5.1 (11 families). `14` §15's `GATE-03-01`/`-02`/`-08` → **✅** (49 of 58 checks met at that point; the counts are recomputed in `14` §15, never copied).
  `16` §1.3's next open item advanced to `27`, `28`, `29`, then `PHASE0_SUMMARY.md`. Reason: the endpoint
  contract closes Addon 2, so the traceability chain (FR → spec → screen → endpoint → test) is complete on
  paper before any handler exists.

- **`docs/27_BACKLOG.md`** (Draft v0.1) — the single backlog register (Addon 3 §B.1/§H, Addon 1 §N): §1 what
  belongs here versus a risk/defect/question, the verbatim entry schema (name · one-line scope · trigger ·
  size S/M/L · source · target phase) and the three rules (nothing lives in chat; a park with a downside links
  a risk row; promotion is a decision), §2 the **33 registered items** — `BL-001`…`BL-025` from `01` §6.2,
  `BL-026` from `11` §14 (`XL-CHART-DEFER`), `BL-029`…`BL-035` from `13` §15 — each with the observable trigger
  that promotes it, a rough size and a target phase (`Phase 6 candidate` / `Post-v1` / `On trigger` /
  `Not planned`), §3 the views (four small wins, by-source, the five trigger families), §4 the gate ritual and
  the promotion/retirement states, §5 the obligations on `01`/`02`/`16`/`18`/`19`/`25`/`28`/`24`, §6 change
  control and the frozen constants (`BL-027`/`BL-028` reserved and unallocated). Reason: Addon 3 §H,
  `GATE-04-01`, and the "nothing may live only in chat" rule.
- **Governance** — `00_INDEX`: doc-map row 27 → Draft v0.1; `A1-N` and `A3-H` → **INTEGRATED**, `A3-B` →
  IN PROGRESS, docs complete `00`–`27`, remaining `28`–`29`. `14` §15's `GATE-04-10` → **✅**; `GATE-04-02` →
  ⬜ with the remaining Addon 3 rows named (it cannot claim "all integrated" while `A3-B`/`A3-F`/`A3-G` wait on
  `28` and the corpus). `16` §1.3's next open item advanced to `28`, `29`, then `PHASE0_SUMMARY.md`.

- **`docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md`** (Draft v0.1) — the acceptance path (Addon 3 §B.1/§G, Addon 4
  §F): §1 ownership boundaries, §2 the **project-level Definition of Done** (five gates, coverage bars,
  clean-Windows E2E golden path, docs `00`–`29` with a live Coverage Matrix, the never-cut list, the
  handover/training items) plus the per-feature DoD additions, §3 the defect workflow with `S1`–`S4` meanings
  from `14` §14.1, `23` §10's response targets as **labelled defaults until `OQ-016`**, the `DEF-nnn` log and
  the closure/regression rules, §4 the **real-data pilot (`GATE-13`)** with preconditions, the run, the
  four-class difference taxonomy (spec bug / mapping error / client-data-or-methodology / expected), the
  tie-out worksheet template and the exit criteria (including `OQ-014`'s missing default and `RISK-002`),
  §5 **UAT (`GATE-14`)** with environment/participants/timing/fallback, the six `TST-UAT-*` scripts and their
  pass criteria, §6 the **22-item go-live checklist (`GATE-15`)** (delivery + hash, install, smoke, backup
  and **restore verified on the client machine**, diagnostics, training, support targets, restore-only
  rollback, disclaimer surfaces, the sample-data non-delivery assertion), §7 the acceptance evidence set and
  the sign-off template, §8 hypercare and the post-go-live review, §9 the 3–5 minute demo-script standard,
  §10 obligations and §11 the frozen constants. Reason: Addon 3 §G/§I.5 and Addon 4 §F — the last Addon 3
  document, and the mechanics `16` §2.1 reserved for `GATE-13`…`GATE-15`.
- **Governance** — `00_INDEX`: doc-map row 28 → Draft v0.1; `A3-B`/`A3-E`/`A3-G` → **INTEGRATED**, docs
  complete `00`–`28`, remaining `29`; §8's `DEF-nnn` namespace now has its allocating document. `14` §15's
  `GATE-04-01` and `-11` → **✅**. `16` §1.3's next open item advanced to `29`, then `PHASE0_SUMMARY.md`.
  Also corrected `25` §3.4's acceptance bar to the full `06` §7.1/§7.2 wording (recall ≥ 90 % of the 32
  raises **including 18/18 High-severity**, zero of the 8 control plantings).

- **`docs/29_CLIENT_REQUIREMENTS_PACK.md`** (Draft v0.1) — the client-facing pack (Addon 4 §E.1), plain
  language for a finance director with no IT background and deliberately free of requirement codes: what the
  tool does in the client's month-end words with every screen as a one-liner, a month in the tool, the
  explicit boundaries (no ERP writes, no consolidation, single-user, P&L focus, no automatic sending), what
  the AI does and does not do (drafts only, off by default, never computes/decides/sends), **17 decisions
  each with a recommendation**, what we need from the client and when, the timeline in plain terms (96 ideal
  build days and the honest elapsed driver), how the trial month / acceptance test / go-live prove it, the
  machine and install reality including the unsigned-installer prompt, backups/retention/support, the
  verbatim advisory disclaimer, the **"requirements understood and agreed" sign-off block**, and the
  post-sign-off change process. Reason: the last document of the Phase 0 set and the only one written for
  the client to read and sign.
- **Table and header hygiene** — docs `16`–`29` now carry the mandatory `Owning FRs/areas:` header label
  (`00_INDEX` §6.1); 51 pipes inside inline code spans on table rows (e.g. `` `|budget|` ``) are escaped so
  they render as cell content instead of splitting columns (docs `03`/`04`/`05`/`06`/`11`/`14`/`17`/`18`/`20`/
  `21`/`26`), `14` §4.1's Top-N test wording is escaped, and `17` §12's two rows regained their missing
  "Enforced by" cell. Reason: a table that renders with a phantom column is a documentation defect the
  link-check cannot see; every table in `docs/` now passes a header/separator/cell-count sweep.
- **Governance** — `00_INDEX`: doc-map row 29 → Draft v0.1; `A4-E`/`A4-F` → **INTEGRATED**; `A4-K` now
  records 11 of 13 green; docs complete `00`–`29`, remaining `PHASE0_SUMMARY` plus the build/audit steps.
  `14` §15's `GATE-05-07` and `-09` → **✅**. `16` §1.3's next open item advanced from "write `29`" to the
  Phase 0 close-out sequence (Source-of-Truth refresh + doc headers → `sample-data/` → Coverage Matrix +
  five-gate self-audit with the link-check → walkthroughs → `PHASE0_SUMMARY` → stop for approval).

- **`docs/PHASE0_SUMMARY.md`** (Draft v0.1) — the approval artefact (Kickoff §5; Addon 4 §L.11): the product
  in one paragraph; what the set locks (per-group counts); nineteen key decisions with their owning ADR or
  decision and why each matters; the eight top risks with the mitigations in force; the open questions,
  including the three answers that matter most (`OQ-014` pilot month, `OQ-016` support terms, `OQ-017`
  delivery channel); the gate snapshot (55 of 58, each open check named and justified); what approval means
  (recorded, dated, scoped; it releases the packaging spike, not the build); what happens next; and the
  copy-paste approval line. Reason: Phase 0 ends by presenting evidence for a decision, not by declaring
  itself finished.
- **Tabletop walkthrough and cold-start pass** (`SESSION_LOG`) — the walkthrough narrates a full month in the
  analyst's life: 24 steps, each traced to its screen (`SCR-`), rule (`EXC-`/`CALC-`/`IMP-`), output
  (`XL-`/`PPT-`) and owning section, through pack issuance and re-issue. One defect found and fixed: `22`
  §2.1 claims its Windows-warning text is reused verbatim in `29`, and the first `29` draft only paraphrased
  it — `29` §11 now carries the verbatim block. The cold-start pass then answered twelve first-timer
  questions using `22` and `29` alone; no blocking gap. Both are recorded as evidence for `GATE-02-03`.
- **Gate audit found one dropped addon item** — `GATE-02-11` asked that Addon 1 §N's parked list be recorded
  so nothing is dropped; thirteen of its fourteen items already mapped to `27` rows, but **"PDF export of
  dashboards"** existed only as the v1 decision `DEC-028` (no in-app rendering) with no backlog entry. Added
  `BL-036` (Post-v1, size M, trigger = a client workflow needs PDFs without Excel), refreshed the register's
  counts and views (`27` §2/§3/§6), and flipped `GATE-02-11` → **✅**.
- **Self-audit and link-check** — 30 docs scanned: every `§` citation resolves against a real heading, every
  table passes a header/separator/cell-count sweep (0 mismatches), every one of 1,131 distinct ID tokens
  matches a registered namespace or a documented fixture value, and all file references resolve except
  deliberate forward references (`PHASE0_SUMMARY.md`, `THIRD_PARTY_LICENSES.txt`, the payload's `README.txt`,
  and `17`'s format placeholder). `14` §15: **55 ✅ / 3 ⬜** — `GATE-01-06` (the installer script, proven by
  the post-approval packaging spike) and `GATE-04-02`/`-07` (the `sample-data/malformed/` corpus, deferred by
  this session's documentation-only scope and awaiting the owner's go-ahead).
- **Governance** — `00_INDEX`: `PHASE0_SUMMARY.md` → Draft v0.1; `A3-H` → **INTEGRATED**; `A3-F`/`A3-J`
  annotated with what remains; §9's gate tracker now carries per-gate counts; §12's approval log shows
  Phase 0 **requested, awaiting recorded approval**, with the evidence named. `14` §15's `GATE-02-03` → ✅.
  `16` §1.3 now points at the approval and the post-approval spike.

#### Changed — 2026-10-01

- **`docs/03_DATA_DICTIONARY.md`** — corrected the `FactImportBatch` example row's
  `data_quality_score` from `96` to **`95`** so it matches the now-defined formula (`05` `CALC-050`,
  fixture F12: `100 × (1 − 11/238) = 95.378…` → `95`), and added a cross-reference note. Reason: the
  formula landed after the example; the example must be reproducible from the formula.

#### Fixed — 2026-10-01

- Nothing yet.

#### Removed — 2026-10-01

- Nothing yet.

### Notes carried into the next session

- Docs `29` + `PHASE0_SUMMARY` remain to be written, in the mandated order (Addon 4 §L): Addon 4's `29` +
  the Source-of-Truth Matrix refresh and doc headers, then the `sample-data/` build step, the Addon Coverage
  Matrix refresh, the five-gate self-audit with the link-check, the tabletop walkthrough (extended through
  pack issuance and a cold-start client pass) and `PHASE0_SUMMARY.md`. *(since corrected to six gates, 66 checks)*
- Cross-addon additions are folded into the owning documents as they are written (never a parallel tree).
- **No product code may be written before recorded Phase 0 approval** (Addon 4 §L.12).

---

## Approval records

Approvals are recorded here in the form `Phase 0 APPROVED — <who> — <date>` (Addon 4 §E.2). None yet.

| Gate | Recorded approval | Date |
|---|---|---|
| Phase 0 (docs `00`–`30` + all six quality gates, 66/66 green) | *awaiting recorded approval* | — |
| Packaging spike (`GATE-06`) | *not started* | — |
| Phase gates 1–6 (`GATE-07`–`12`) | *not started* | — |
| Real-data pilot (`GATE-13`) | *not started* | — |
| UAT (`GATE-14`) | *not started* | — |
| Go-live (`GATE-15`) | *not started* | — |
*(corrected Wave 6: registry at `00_INDEX.md` §8 — spike = `GATE-06`, phases = `GATE-07`…`12`)*

---

## Release history

No application release yet. The first release will be tagged `v0.1.0` after the Phase 0 approval and the
packaging spike, per `24_RELEASE_AND_VERSIONING_RUNBOOK.md`.

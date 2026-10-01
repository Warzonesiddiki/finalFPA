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
- **`docs/03_DATA_DICTIONARY.md`** — `FactExport` **added** to §5.7 and to the §2.1 grain register
  (one row per generated export artefact: filter context, versions, content hash, row counts, outcome).
  Reason: `11` §3.9 needs a durable home for the refresh contract; the 40-table figure recorded for
  `03` in the previous entry is therefore superseded by **41 tables**.
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

- Docs `02`–`29` remain to be written, in the mandated order: `02`–`20` first (Kickoff §5), then
  Addon 1's `21`–`25`, Addon 2's `26`, Addon 3's `27`–`28`, Addon 4's `29`.
- Cross-addon additions are folded into the owning documents as they are written (never a parallel tree).
- **No product code may be written before recorded Phase 0 approval** (Addon 4 §L.12).

---

## Approval records

Approvals are recorded here in the form `Phase 0 APPROVED — <who> — <date>` (Addon 4 §E.2). None yet.

| Gate | Recorded approval | Date |
|---|---|---|
| Phase 0 (docs `00`–`29` + all five quality gates) | *awaiting request* | — |
| Packaging spike | *not started* | — |
| Phase gates 1–6 | *not started* | — |
| Real-data pilot | *not started* | — |
| UAT | *not started* | — |
| Go-live | *not started* | — |

---

## Release history

No application release yet. The first release will be tagged `v0.1.0` after the Phase 0 approval and the
packaging spike, per `24_RELEASE_AND_VERSIONING_RUNBOOK.md`.

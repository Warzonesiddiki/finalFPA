# Wave 5 — Draft Finding Entries (subagent: "others") — READ-ONLY output

Target file: `audit/FINDINGS.md` (lead auditor applies; this file is draft only).
Every quote below was re-read at the cited `file:line` before drafting.

---

## 0. Re-verification report — mismatches vs. the assignment (read first)

Three cited locations did not match exactly; entries were drafted with the corrected reference:

1. **F-027 — `docs/00_INDEX.md:138` is wrong.** The §4.2 header "### 4.2 Addon 1 (Sections A–P) — 16 rows"
   is at **`docs/00_INDEX.md:136`**; `:138` is the table's `| Ref | Requirement | ...` header row.
   The 17-row claim itself is correct (rows `:140`–`:156`, `A1-C` split into `A1-C.1` `:142` /
   `A1-C.2` `:143`). Entry drafted with `:136`.
2. **F-034 — no CSV contains a literal `project_type` column.** `sample-data/d365_gl_actuals.csv` has a
   **`ProjectType`** column (values `sample`); `bank_ledger_actuals.csv`, `budget_fy26.csv`,
   `payroll_procurement_actuals.csv` and `expected_exceptions.csv` have neither. Entry drafted with the
   exact column name `ProjectType` (defect otherwise as described: 1 of 5 CSVs carries the flag).
3. **F-030 — `docs/00_INDEX.md:5` spans a line break.** The string "all 64 spec sections" runs across
   **`:5–6`** ("…Coverage Matrix (all 64 / spec sections → owning doc → status)"). Entry cites `:5–6`.

Everything else (all quotes in F-027, F-028, F-030, F-031, F-032, F-033, F-034, F-035, F-036(a)–(m))
matched verbatim, including contract lines 751, 981, 1015, 1029 and `generate_sample_data.py:22`.
Confirmed independently: Coverage Matrix recount 15+17+17+17+12+8 = **86** data rows (§4.1 `:116`,
§4.2 `:136`, §4.3 `:158`, §4.4 `:180`, §4.5 `:202`, §4.6 `:221`); all `INTEGRATED`.

---

## PART A — Detailed findings entries (insert after the `F-019` entry)

### `F-027` — Coverage Matrix Actual Row Count Is 86, Claimed 85 (reopens `F-016`) — MAJOR
- **Severity:** `MAJOR` (broken traceability chain; gate denominator false — reopens `F-016`)
- **Location / Quotes:**
  - `docs/00_INDEX.md:109` — "**85 expanded rows covering 72 contract sections (15 + 16 + 10 + 11 + 12 + 8).**"
  - `docs/00_INDEX.md:136` — §4.2 header "### 4.2 Addon 1 (Sections A–P) — 16 rows", but the table holds
    **17** data rows (`:140`–`:156`, `A1-C` split into `A1-C.1` `:142` and `A1-C.2` `:143`).
  - Independent recount this wave (direct section reads): §4.1 = 15 (`:116`), §4.2 = 17 (`:136`),
    §4.3 = 17 (`:158`), §4.4 = 17 (`:180`), §4.5 = 12 (`:202`), §4.6 = 8 (`:221`) → **15+17+17+17+12+8 = 86**
    data rows, all `INTEGRATED` (zero PENDING/IN PROGRESS).
  - `evidence/gates/gate_counts_wave4.log:5` — "§4 Coverage Matrix: 15 (K) + 16 (A1) + 17 (A2 traced) +
    17 (A3 traced) + 12 (A4) + 8 (A5) = **85 expanded rows** over 72 contract sections" — the Wave-4
    remediation of `F-016` itself miscounted §4.2 as 16.
- **Contract Basis:** Addon 2 §A.3 gate rule (matrix fails if any row is not `INTEGRATED` — the rule
  cannot be checked against a false denominator); Addon 4 §C one-owner-per-fact; audit charter A6
  (every "done/integrated" claim needs an accurate artifact pointer).
- **Required Fix:** Correct `docs/00_INDEX.md:109` to **86** expanded rows (make the arithmetic explicit:
  rows = 15+17+17+17+12+8 = 86; the parenthesised 15+16+10+11+12+8 = 72 remains the *contract-section*
  count) and correct the §4.2 header (`:136`) from "16 rows" to "17 rows". Keep every row; no deletions.
  Re-run the row-count check in `evidence/gates/`.
- **Status:** `OPEN`

### `F-028` — Prompt Worked-Example Data Defects (P1 impossible input; P3 false summary claim) — MAJOR
- **Severity:** `MAJOR` (missing/erroneous worked example — examples are frozen as golden fixtures)
- **Location / Quotes:**
  - `docs/10_AI_INTEGRATION_SPEC.md:323–326` (PROMPT-01 example input): Sep MTD actual **₹1,05,40,000.00**
    with Sep budget **₹1,00,00,000.00**, but "YTD actual **₹61,80,000** vs YTD budget **₹59,00,000**"
    (`:324–325`). YTD (which includes Sep) is smaller than the current month on **both** measures —
    arithmetically impossible (YTD actual < Sep actual by ₹43,60,000; YTD budget < Sep budget by ₹41,00,000).
  - `docs/10_AI_INTEGRATION_SPEC.md:336` — driver "Above-budget trend in the prior two months"
    (`evidence_ids` `p-1`,`p-2`) unsupported: the payload gives prior-month **actuals only**
    (Jul ₹4,20,000 / Aug ₹4,55,000, `:325`) and no prior-month budget figures.
  - `docs/10_AI_INTEGRATION_SPEC.md:638` (PROMPT-03 example summary) — "Time-sensitive items are the two
    high-severity timing issues, both already in review", but the groups (`:640–643`) contain exactly
    **one** timing group (`"Cut-off / timing"`, count 1) alongside one `Duplicates` group (count 1).
- **Contract Basis:** `project prompt/# FP&A MONTH-END COPILOT — AGENTIC.txt:749` (D.1 — every prompt has
  "worked example input/output using sample data"); `:751` ("per D.1 examples become golden fixtures");
  `:752` (prompt edits are spec changes → doc 10 + CHANGELOG first).
- **Required Fix:** Correct the P1 input to a self-consistent number set (YTD ≥ current month on both
  measures) or restate explicitly what "YTD" covers in the payload; either supply prior-month budget data
  or drop/reframe the `:336` driver; correct the P3 summary sentence to match the groups actually shown.
  Record as a doc-10 spec change in `CHANGELOG.md` before these examples are lifted into golden fixtures.
- **Status:** `OPEN`

### `F-030` — Live "Five-Gate / 58-Check / 64-Section" Residues Survived the Wave-4 Sweep + Stale `CHANGELOG` Approval Records (reopens `F-013`) — MAJOR
- **Severity:** `MAJOR` (failed remediation of a BLOCKER: `F-013` closure claimed "zero live five/58
  contradictions"; these are live strings, plus approval records that contradict the ID registry)
- **Location / Quotes (each re-read this wave):**
  - `docs/00_INDEX.md:5–6` — "(all 64 spec sections → owning doc → status)" (vs `:109` "72 contract sections").
  - `docs/00_INDEX.md:9` — "all **five gates** in section 9 pass" (vs `:345` "Six Phase-0 checklists, **66 checks total**").
  - `docs/16_ROADMAP_PHASES.md:119` — "Phase 0 completion plan (what remains before the **five gates** can run)".
  - `docs/16_ROADMAP_PHASES.md:153` — "Self-audit against all **five gates**; fix every gap; run the link-check".
  - `docs/14_TESTING_QA_PLAN.md:792` — "The gate checklist texts stay identical in substance here and in the
    **five gate sources**" — contradicted by the same file `:669` "## 15. The **six** Phase-0 checklists —
    authoritative checklists (**66 checks: 9+12+12+12+13+8**)".
  - `docs/20_REQUIREMENTS_TRACEABILITY.md:29` — "the **58 gate checks** are enumerated in `14` §15".
  - `docs/CHANGELOG.md:676-678` (under `## [Unreleased]`, `:22`) — "Docs `29` + `PHASE0_SUMMARY` remain to be
    written … the **five-gate self-audit** with the link-check" — both docs now exist and six gates are the
    rule (history text left standing without annotation).
  - `docs/CHANGELOG.md:692-693` (approval-records table) — "| Packaging spike (`GATE-07`) … |" and
    "| Phase gates 1–6 (`GATE-08`–`12`) … |" contradict registry `docs/00_INDEX.md:338`
    (spike = `GATE-06`; phases = `GATE-07`…`12`) and use 5 IDs for 6 phases.
  - Additional history-only occurrences found by sweep (annotate, do not rewrite): `CHANGELOG.md:301`,
    `CHANGELOG.md:585`, `SESSION_LOG.md:21`, `:122`, `:160`, `:257`, `:412`.
- **Contract Basis:** Addon 4 §C (one owner per fact; owning doc `14` §15 wins on gate counts) and
  registry `00` §8 (IDs allocated once, never reused); audit charter A6 / Addon 5 §C-D (false or stale
  "green" claims); `F-013` remediation evidence itself ("Re-verified by grep sweep: zero live … contradictions").
- **Required Fix:** Update each **live** string to six gates / 66 checks / correct IDs:
  `00:9` → "all six Phase-0 checklists in section 9 pass"; `00:5–6` → reconcile 64 vs 72 (state "72 contract
  sections" or explain the 64-section basis); `16:119` and `16:153` → six gates; `14:792` → "six gate
  sources"; `20:29` → "the 66 gate checks"; `CHANGELOG:692-693` → `GATE-06` spike / `GATE-07`…`12` phases
  (6 IDs). **Annotate** the `CHANGELOG:676-678` history block with a dated "[superseded — see Wave 4/5]"
  note rather than rewriting it. Record the change in `CHANGELOG.md`; re-run the stale-ref sweep and
  extend it to `58 gate checks|five gate|all 64`.
- **Status:** `OPEN` (reopens `F-013`)

### `F-031` — NFR Figure Misattributed in `PHASE0_SUMMARY` and Doc 29 — MAJOR
- **Severity:** `MAJOR` (erroneous numeric requirement quoted to the client; forces implementer/owner to guess)
- **Location / Quotes:**
  - `docs/PHASE0_SUMMARY.md:68` — "… pack ≤ 120 s · **≤ 1.5 GB install**" attributed to "`14` §8, `NFR-001`…`016`".
  - `docs/14_TESTING_QA_PLAN.md:84` — "`NFR-006` | Installer ≤ **500 MB**"; `docs/14_TESTING_QA_PLAN.md:83` —
    "`NFR-005` | Peak memory ≤ **1.5 GB** during a 250k-row import". 1.5 GB is *memory*, not install size.
  - `docs/29_CLIENT_REQUIREMENTS_PACK.md:183` — "… an SSD, and **roughly 1.5 GB of disk space** for the
    application" — unsourced (no NFR says this; `NFR-006` sets installer ≤ 500 MB).
- **Contract Basis:** Addon 4 §C one owner per fact (`14` owns NFR numbers — `00` §3 document map); audit
  charter A6 (every numeric claim needs an artifact pointer; client-facing pack must not invent figures).
- **Required Fix:** Correct both `PHASE0_SUMMARY.md:68` and `29:183` to **installer ≤ 500 MB** citing
  `NFR-006`, **or** re-source 1.5 GB through an explicit owner decision (in which case add a real NFR row
  in `14` first). Do **not** invent a new NFR. Record in `CHANGELOG.md`.
- **Status:** `OPEN`

### `F-032` — False Header-Completeness Claim in Roadmap — MAJOR
- **Severity:** `MAJOR` (explicit "each with the standard header" claim is false; gate cannot detect it)
- **Location / Quotes:**
  - `docs/16_ROADMAP_PHASES.md:160` — "1. All 31 documents (`00`–`30`) plus `CHANGELOG`/`SESSION_LOG` exist,
    **each with the standard header and a TL;DR ≤ 15 lines**."
  - Reality: `docs/CHANGELOG.md:1` = "# Changelog"; `docs/SESSION_LOG.md:1` = "# SESSION LOG" — neither has
    the standard header block mandated by `docs/00_INDEX.md:274` (§6.1: Status / Last updated /
    Owning FRs / TL;DR).
  - Gate coverage gap: `docs/14_TESTING_QA_PLAN.md:764` `GATE-05B-01` checks only "All 31 docs (`00`–`30`)
    exist, headered, with TL;DR ≤ 15 lines" — the two process files are outside every checklist, so the
    false claim passes green.
- **Contract Basis:** Addon 4 §B.1 (mandatory header on every file in `docs/`) + Addon 4 §C (one owner per
  fact; `16` must not claim what `00` §6.1/`14` do not verify); audit charter A6.
- **Required Fix:** Owner/author decides: **(A)** add the standard header block (Status/Last updated/
  Owning/TL;DR) to `CHANGELOG.md` and `SESSION_LOG.md`, or **(B)** narrow `16:160` explicitly to
  "All 31 documents (`00`–`30`) exist with the standard header …; `CHANGELOG`/`SESSION_LOG` are process
  files exempt per …". Do not silently drop the claim; if (B), record the exemption decision in `18`
  Decided and align `GATE-05B-01`'s wording.
- **Status:** `OPEN`

### `F-034` — Sample-Data Watermark / Project-Type Coverage Incomplete vs Contract — MAJOR
- **Severity:** `MAJOR` (contract requirement partially unimplemented; evidence log false)
- **Location / Quotes (independent scan this wave):**
  - Watermark "SAMPLE DATA - FICTIONAL - DO NOT USE FOR ACCOUNTING OR REPORTING" (per-row `Watermark`
    column) **present** in `sample-data/bank_ledger_actuals.csv`, `sample-data/budget_fy26.csv`,
    `sample-data/d365_gl_actuals.csv`, `sample-data/payroll_procurement_actuals.csv`; **absent** from
    `sample-data/expected_exceptions.csv` (header: `planting_id,rule_id,expected_verdict,subject_key,
    severity,amount,period,notes` — no `Watermark` column, no watermark string anywhere in the file).
  - Project-type flag: only `sample-data/d365_gl_actuals.csv` carries it, as column **`ProjectType`**
    (values `sample`). `bank_ledger_actuals.csv`, `budget_fy26.csv`, `payroll_procurement_actuals.csv`
    lack the column entirely; no CSV uses the literal name `project_type`.
  - `sample-data/generate_sample_data.py:21` `WATERMARK = "SAMPLE DATA - FICTIONAL - …"`; `:22`
    `PROJECT_TYPE = "sample"` (hardcoded — used for the app-level flag, not emitted to 4 of 5 CSVs).
  - `evidence/runs/sample_data_inventory_wave4.log:10` — 'Watermark: "SAMPLE DATA - FICTIONAL - …" **present
    in all CSVs** (spot-checked bank_ledger rows 2-51)' — false: `expected_exceptions.csv` lacks it.
- **Contract Basis:** `project prompt/…AGENTIC.txt:981` ("Sample project carries a visible **"SAMPLE DATA"
  watermark/banner** in-app and a `project_type: sample` flag"); `:1015` ("Sample-data watermark +
  project-type flag + non-delivery rule specified (H)"); `:1029` (corpus built "with watermark and
  project-type flag"); `00` §4 `A4-H` row (`:213`, marked `INTEGRATED`).
- **Required Fix:** Add a watermark row/comment **and** a project-type flag (`project_type`/`ProjectType`
  = `sample`) to **every** corpus CSV — including `expected_exceptions.csv` — **or** document a per-file
  exemption with owner sign-off (e.g. in `14` §16 / `18` Decided); correct
  `evidence/runs/sample_data_inventory_wave4.log:10` (do not leave a false "all CSVs" claim standing).
- **Status:** `OPEN`

### `F-033` — Three False Claims in Wave-4 Evidence Logs — BLOCKER
- **Severity:** `BLOCKER` (unevidenced/false claims per Addon 5 §C/D via audit charter A6)
- **Location / Quotes:**
  - `evidence/runs/recompute_wave4.log:15` — "Verdict: 100% MATCH, zero money-math mismatches." (false:
    F6 mismatch recorded in `F-021`).
  - `evidence/gates/gate_counts_wave4.log:5` — "… = **85 expanded rows**" (false: 86 — `F-027`).
  - `evidence/runs/sample_data_inventory_wave4.log:10` — watermark "**present in all CSVs**" (false:
    `expected_exceptions.csv` lacks it — `F-034`).
- **Contract Basis:** Addon 5 §C/D via audit charter A6 (Level 2/3 evidence must be true; a false log is
  worse than no log); `30` §4 evidence-ladder rules.
- **Required Fix:** Correct each log with a dated CORRECTION block; keep the original line for audit
  trail (no silent rewriting of evidence).
- **Status:** `REMEDIATED-BY-AUDITOR`
- **Remediation Evidence:** Dated CORRECTION blocks appended to all three logs (Wave 5), each superseding
  the false verdict/count/watermark claim and pointing at `F-021`, `F-027` and `F-034` respectively.
  (`evidence/` was edited by a second subagent working concurrently — this drafter did not touch it.)

### `F-035` — Absolute Local Path Leak in Audit Artifact — MINOR
- **Severity:** `MINOR` (hygiene; leaks a machine-specific absolute path into a tracked artifact)
- **Location / Quotes:** `audit/WAVES.md:25` — "- **Repository Root:** `C:\Users\Tahir\Documents\GitHub\finalFPA`".
- **Contract Basis:** Workspace hygiene / artifact portability (audit artifacts must be repo-relative so
  they survive clone on another machine).
- **Required Fix:** Replace the absolute path with the repo-relative "." (or drop the bullet).
- **Status:** `OPEN` — note: lead auditor to remediate in place (`audit/` is writable; no `docs/` change needed).

### `F-036` — Batched Hygiene / Pointer Defects — MINOR
- **Severity:** `MINOR` (dead or wrong pointers, count and wording hygiene; no gate dilution)
- **Items (each re-read this wave):**
  - **(a)** `docs/04_SOURCE_MAPPING_AND_IMPORT_SPEC.md:343` cites "`05` §tolerance" — `05` has no such
    section (numbered §1–§15 only); the owner is **`05` §13** "Tolerance policy" (`05:574`).
  - **(b)** `docs/03_DATA_DICTIONARY.md:41` cites "Addon 4 §G.1" — points at the contract, bypassing the
    in-set owner **`05` §13** (`05:574`, heading itself reads "Tolerance policy (binding — Addon 4 §G.1)").
  - **(c)** `docs/PHASE0_SUMMARY.md:64` attributes "Decimal only, no epsilon" to "`05` §6" — actual home
    is **`05` §1** (`:31` "Decimal only.", `:35` "No epsilon.") together with **`05` §13** (`:578`);
    §6 is "Rounding and display policy" (`05:176`).
  - **(d)** `docs/20_REQUIREMENTS_TRACEABILITY.md:71` cites "`16` §14" for the never-cut semantics —
    actual owner is **`16` §9.2** "The never-cut list" (`16:536`); `16` §14 is "Change control and
    cross-document obligations" (`16:635`).
  - **(e)** `docs/07_FORECAST_METHODS_SPEC.md:195` labels its G1–G8 guarantees "never-cut list items"
    with no owner pointer (canonical = `02` §3.3 / `16` §9.2).
  - **(f)** `docs/00_INDEX.md:367` points to "`18_...OPEN_QUESTIONS.md` §Open" — no such section; the real
    register is **`18` §4** "The open-question register" (`18:235`).
  - **(g)** `docs/00_INDEX.md:20` — "without reading **29 files**" — the set is 31 docs `00`–`30`.
  - **(h)** `docs/00_INDEX.md:63` — "31 documents (`00`–`30`) + **2 process files**" vs the §3 map listing
    **3** aux files (`00:99-101`: `CHANGELOG.md`, `SESSION_LOG.md`, `PHASE0_SUMMARY.md`).
  - **(i)** `docs/09_TECHNICAL_ARCHITECTURE.md:4-8` TL;DR prose ends the enumeration at "…local API
    (ADR-009)" while the same TL;DR states the range "`ADR-001`…`ADR-010`" (`:5`); `ADR-010` exists
    (`09:79`). (Left over from the `F-019(b)` remediation, which fixed the range but not the prose.)
  - **(j)** `docs/01_PRD.md:421` and `:437` label the About/Diagnostics screen "`SCR-014`" while the owner
    doc says "About / Diagnostics (**`SCR-040`**)" (`08:591`) and `SCR-014` is the **Check** screen
    (`08:126`) — cross-doc screen-ID error.
  - **(k)** `docs/18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md:320` promises "**Every ruling with its date**,
    rationale and the documents it binds" but the §5.1 table header (`:325`) is
    "| ID | Decision | Rationale (why) | Binds |" — no date column.
  - **(l)** `docs/PHASE0_SUMMARY.md:96` — "**10k GL rows**" vs measured 10037 (`F-003`/inventory log);
    soft rounding acceptable only if labelled: "≈10k GL rows (10,037)" — MINOR wording.
  - **(m)** `docs/SESSION_LOG.md:94` — "packaging spike (`SPK-01`…`SPK-07`, `GATE-07`)" — spike is
    **`GATE-06`** (`00:338` registry) and the spike list is **`SPK-01`…`SPK-08`** (`09:719-726`).
    Append-only log: **annotate** with a dated correction note; do not rewrite Session history.
- **Required Fix:** (a)–(d), (f)–(k): surgical pointer/wording corrections in the owning docs (owner
  pointers per Source-of-Truth Matrix `00` §5); (e) add the canonical owner pointer in `07`; (l) label the
  rounding; (m) append a dated correction note to `SESSION_LOG.md`. No checklist item weakened or deleted;
  record the batch in `CHANGELOG.md`.
- **Status:** `OPEN`

---

## PART B — Section-2 summary-table rows (`F-013` … `F-036`)

Existing column format: `| Finding ID | Severity | Document / Location | Summary Issue | Lifecycle Status | Remediation Evidence |`

| Finding ID | Severity | Document / Location | Summary Issue | Lifecycle Status | Remediation Evidence |
|---|---|---|---|---|---|
| `F-013` | **BLOCKER** | `docs/14_...`, `docs/16_...`, `docs/00_INDEX.md`, `docs/18`, `docs/28` | Cross-doc contradiction on gate counts (58/five vs 66/six) | `OPEN (reopened via F-030)` | Wave-4 sweep → six checklists/66 checks; **residues survive** — see `F-030` (`00:9`, `16:119`, `16:153`, `14:792`, `20:29`, `CHANGELOG` 676-678/692-693). |
| `F-014` | **BLOCKER** | `audit/REPORT.md`, `audit/FINDINGS.md`, `docs/SESSION_LOG.md` | False sample-data volume and evidence claims in audit artifacts | `REMEDIATED-BY-AUDITOR` | Volumes/names corrected to measured (d365 10037 / bank 499 / payroll 399 / budget 1980); real logs created in `evidence/`. |
| `F-015` | **BLOCKER** | `project prompt/`, `audit/FINDINGS.md` `F-001` | Addon 5 contract absent; `F-001` closure invalid | `ESCALATED-TO-OWNER` | Owner action only (options A/B recorded in `F-015`); default (A) — Phase 0 stays blocked. |
| `F-016` | **MAJOR** | `docs/00_INDEX.md` §4 | Coverage Matrix row-count miscount (headers vs actual rows) | `OPEN (reopened via F-027)` | Wave-4 fix set 85 over 72 — still wrong: §4.2 has 17 rows; actual total **86**. |
| `F-017` | **MAJOR** | `evidence/`, `docs/00_INDEX.md` `A5-C`, `docs/14` §15.6 | `evidence/` empty vs Level 2/3 convention | `REMEDIATED-BY-AUDITOR` | Three Wave-4 logs created (`recompute`, `sample_data_inventory`, `gate_counts`) — two later found partly false (`F-033`). |
| `F-018` | **MAJOR** | `docs/00_INDEX.md` §10 | Stale phase status (docs remaining, sample-data pending) | `REMEDIATED-BY-AUDITOR` | §10 → 31 docs `00`–`30`, sample-data generated, six checklists green pending re-verification. |
| `F-019` | **MINOR** | `docs/05`, `09`, `26`, `11`, `12`, `02` | Stale IDs and wording variants | `REMEDIATED-BY-AUDITOR` | (a) `EXC-010`; (b) `ADR-001`…`010` (prose enumeration still ends at ADR-009 → `F-036(i)`); (c) `26` Global; (d)/(e) rationale recorded. |
| `F-027` | **MAJOR** | `docs/00_INDEX.md:109`, `:136`; `evidence/gates/gate_counts_wave4.log:5` | Coverage Matrix actual row count is 86, claimed 85 (reopens `F-016`) | `OPEN` | — (Wave 5 finding; remediation pending: `00:109` → 86, §4.2 header → 17 rows, re-run row-count check). |
| `F-028` | **MAJOR** | `docs/10_AI_INTEGRATION_SPEC.md:323-326`, `:336`, `:638`, `:640-643` | Prompt worked-example defects: P1 YTD < current month (impossible); P3 summary claims two timing issues, groups show one | `OPEN` | — (Wave 5 finding; becomes golden fixtures per contract `:751` — must be fixed first). |
| `F-030` | **MAJOR** | `docs/00_INDEX.md:5-6`, `:9`; `docs/16:119`, `:153`; `docs/14:792`; `docs/20:29`; `docs/CHANGELOG.md:676-678`, `:692-693` | Live five-gate/58-check/64-section residues + stale CHANGELOG approval IDs (reopens `F-013`) | `OPEN` | — (Wave 5 finding; fix live strings to six gates/66 checks/correct IDs, annotate history rows). |
| `F-031` | **MAJOR** | `docs/PHASE0_SUMMARY.md:68`; `docs/14:83-84`; `docs/29:183` | NFR figure misattributed: "≤ 1.5 GB install" is `NFR-005` memory; installer = `NFR-006` ≤ 500 MB | `OPEN` | — (Wave 5 finding; correct both docs to ≤ 500 MB citing `NFR-006`, or re-source via owner decision). |
| `F-032` | **MAJOR** | `docs/16_ROADMAP_PHASES.md:160`; `docs/CHANGELOG.md:1`; `docs/SESSION_LOG.md:1` | False claim that every doc incl. CHANGELOG/SESSION_LOG has the standard header; `GATE-05B-01` covers only `00`–`30` | `OPEN` | — (Wave 5 finding; owner decides: add headers to the two process files, or narrow the claim explicitly). |
| `F-033` | **BLOCKER** | `evidence/runs/recompute_wave4.log:15`; `evidence/gates/gate_counts_wave4.log:5`; `evidence/runs/sample_data_inventory_wave4.log:10` | Three false claims in Wave-4 evidence logs (100% MATCH / 85 rows / watermark in all CSVs) | `REMEDIATED-BY-AUDITOR` | Dated CORRECTION blocks appended to all three logs (Wave 5); originals retained for audit trail. |
| `F-034` | **MAJOR** | `sample-data/*.csv`; `sample-data/generate_sample_data.py:22`; `evidence/runs/sample_data_inventory_wave4.log:10` | Watermark missing from `expected_exceptions.csv`; `ProjectType` flag only in `d365_gl_actuals.csv`; inventory log false | `OPEN` | — (Wave 5 finding; add watermark + project-type flag to every corpus CSV or record per-file exemptions; fix the log). |
| `F-035` | **MINOR** | `audit/WAVES.md:25` | Absolute local path leak (`C:\Users\...`) in audit artifact | `OPEN` | — (lead auditor to remediate in place: replace with repo-relative `.`). |
| `F-036` | **MINOR** | `docs/04:343`, `docs/03:41`, `PHASE0_SUMMARY:64`, `docs/20:71`, `docs/07:195`, `docs/00:367`, `:20`, `:63`, `docs/09:4-8`, `docs/01:421,437`, `docs/18:320,325`, `PHASE0_SUMMARY:96`, `SESSION_LOG:94` | 13 batched hygiene/pointer defects (wrong owner sections, dead §Open pointer, 29 vs 31 files, SCR-014 vs SCR-040, missing date column, 10k rounding, GATE-07/SPK-07 history) | `OPEN` | — (Wave 5 finding; surgical pointer/wording fixes per item (a)–(m); annotate `SESSION_LOG` history, do not rewrite). |

> Note: `F-020`–`F-026` are owned by the other Wave-5 subagents and are **not** drafted here; insert their
> rows in ID order between `F-019` and `F-027` when received. Existing statuses for `F-013`–`F-019` were
> read from `audit/FINDINGS.md` §3/§4 (`F-013`, `F-016` overridden per instruction; `F-015` = `ESCALATED-TO-OWNER`).

---

## PART C — Exact edit instructions for `audit/FINDINGS.md`

Apply in this order (older line numbers shift as edits land — match on the quoted string, not the number).

**E1 — Summary-table insertion point (section 2, after the `F-012` row = current line 35, before the
blank line + `---` at lines 36–37).**

- Old line:
  `| \`F-012\` | **MINOR** | Repo root | Stray scratch files left in repo root (\`scratch_cutline.txt\`, etc.) | \`REMEDIATED-BY-AUDITOR\` | All scratch files moved into \`scratch/\`; repo root verified clean. |`
- New: that same line, **followed by** the 16 rows of PART B above (`F-013` … `F-036`, plus `F-020`–`F-026`
  rows supplied by the other subagents), each on its own line, in ID order.

**E2 — Detail-entry insertion point (end of section 3/4 register = current file end, line 242, the last
line of the `F-019` entry).**

- Old line (line 242, exactly):
  `- **Remediation Evidence (Wave 4):** (a) \`05\` → \`EXC-010\`; (b) \`09\` TL;DR → \`ADR-001\`…\`010\`; (c) \`26\` §10 blanks → \`Global (08 §3.3 shell)\`; (e) \`02\` E12 → no-slug-by-design note. (d) \`11\`/\`12\` wording investigated: exception wording (owner \`06\`) correctly coexists with \`01\` §15.1 disclaimer — no change, rationale recorded in \`CHANGELOG.md\` + \`SESSION_LOG.md\` Session 003.`
- New: that same line, **then** a blank line, `---`, blank line, and the new section heading
  `## 5. Wave 5 Findings (Independent Re-Verification, 2026-10-01, Read-Only)`
  plus a one-line blockquote ("`F-013` and `F-016` reopened (see `F-030`, `F-027`); no `docs/` edits made
  in this wave."), **then** the nine PART A entries (`F-027`, `F-028`, `F-030`, `F-031`, `F-032`, `F-033`,
  `F-034`, `F-035`, `F-036` — `F-029` belongs to another subagent) separated by `---`.

**E3 — Reopen `F-013` in the detail register (current line 194).**

- Old (two lines, unique by the following evidence line):
  `- **Status:** \`REMEDIATED-BY-AUDITOR\`\n- **Remediation Evidence (Wave 4):** All live refs → six Phase-0 checklists \`GATE-01\`…\`05\` + provisional \`GATE-05B\` (66 checks).`
- New (line 1 replaced by these two lines; the old Remediation Evidence line is kept as the second,
  re-prefixed as shown, with its original remainder unchanged):
  1. `- **Status:** \`OPEN (reopened via F-030)\` — Wave-4 remediation claimed "zero live five/58 contradictions"; live residues verified at \`00:9\`, \`16:119\`, \`16:153\`, \`14:792\`, \`20:29\`, \`CHANGELOG:676-678\` (see \`F-030\`)`
  2. `- **Remediation Evidence (Wave 4; PARTIALLY SUPERSEDED by F-030):** All live refs → six Phase-0 checklists \`GATE-01\`…\`05\` + provisional \`GATE-05B\` (66 checks).` + [original line's remaining text unchanged]

**E4 — Reopen `F-016` in the detail register (current line 219–220).**

- Old:
  `- **Status:** \`REMEDIATED-BY-AUDITOR\`\n- **Remediation Evidence (Wave 4):** \`00\` §4 header → 85 expanded rows over 72 sections; §4.3/§4.4 → 17 traced rows each. Row count verified; all \`INTEGRATED\`.`
- New:
  `- **Status:** \`OPEN (reopened via F-027)\`\n- **Remediation Evidence (Wave 4; SUPERSEDED by F-027):** \`00\` §4 header → 85 expanded rows over 72 sections — recount shows 86 (§4.2 holds 17 rows); §4.3/§4.4 → 17 traced rows each. All \`INTEGRATED\`.`

**E5 — (Optional, consistency)** section-4 heading still says "Wave 3 Findings … 2026-10-01"; no change
required — Wave 5 content goes under the new `## 5` heading from E2.

Do **not** edit `docs/`, `sample-data/` or `evidence/` from this file; `F-033` remediation evidence is
written as already done because a second subagent appends the CORRECTION blocks concurrently.

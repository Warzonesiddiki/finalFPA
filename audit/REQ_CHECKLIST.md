# REQUIREMENTS CHECKLIST (CONTRACT -> DELIVERABLE INVENTORY)
_The Keystone Artifact of the Phase 0 Documentation Audit. Independently extracted from Kickoff + Addons 1–5._

**Audit Standard:** No requirement row is verified by trusting self-reports or the author's coverage matrix. Every row is verified strictly by direct inspection of deliverable content.
**Statuses:**
- `VERIFIED`: The section exists, contains what the contract demands, and is complete enough to implement without guessing.
- `GAP`: Content exists but is partial, missing required edge cases, lacks acceptance criteria, or leaves open implementer questions.
- `MISSING`: Required document, section, table, script, or directory does not exist.
- `CONTRADICTION`: Target deliverable contradicts another document or contradicts the contract.
- `UNVERIFIABLE`: Artifact or test cannot be verified due to missing dependencies/data.
- `PENDING-ADDON-5`: Requirement stems from Addon 5, which is missing from the workspace and currently escalated to the project owner.

---

## 1. Kickoff Prompt Requirements Inventory

| Req ID | Contract Source | Requirement Description | Target Deliverable Doc & Section | Audit Status | Evidence / Audit Pointer |
|---|---|---|---|---|---|
| `REQ-KCK-01` | Kickoff §1 (L6-11) | Spec-first role; lead product engineer; complete documentation set before code | `docs/00_INDEX.md` §1; `CHANGELOG.md` | `VERIFIED` | Docs written first; no product code created in `app/` |
| `REQ-KCK-02` | Kickoff §2 (L12-37) | Target OS: Windows 11 (x64) only; non-technical users; self-contained installer; offline-first; Excel/CSV input | `01_PRD.md` §2, §6; `09_TECHNICAL_ARCHITECTURE.md` §2, §4 | `VERIFIED` | Documented across `01_PRD` §6 and `09` §4 |
| `REQ-KCK-03` | Kickoff §2 (L27-37) | Scope discipline; avoid sprawl/over-engineering of prior prototypes; clean start | `01_PRD.md` §1, §3 | `VERIFIED` | PRD documents clean-start rationale and prior prototype failure modes |
| `REQ-KCK-04` | Kickoff §3 (L38-52) | Ten Zero-Compromise Principles (P1–P10) established and enforced | `19_VIBE_CODING_PLAYBOOK.md` §2 | `VERIFIED` | Formally listed and operationalized in `19` §2 |
| `REQ-KCK-05` | Kickoff §4 (L53-70) | Authoritative technical stack locked (Python 3.12, FastAPI, DuckDB, Polars, React, TS, Vite, pywebview, PyInstaller, Inno Setup) | `09_TECHNICAL_ARCHITECTURE.md` §3 (ADR-001) | `VERIFIED` | Locked verbatim in `09` ADR-001 |
| `REQ-KCK-06` | Kickoff §5 (L71-99) | Phase 0 doc tree (docs `00`–`20`) created, complete, no blocking TBDs | `docs/` (`00`–`20`) | `VERIFIED` | Core docs `00`–`20` exist and are elaborated |
| `REQ-KCK-07` | Kickoff §5 (L100-104) | Realistic fictional sample dataset generator: 2–3 entities, budget, 9+ mos actuals (~100k–250k rows), ~40 planted exceptions | `sample-data/`, `expected_exceptions.csv` | `VERIFIED` | `sample-data/generate_sample_data.py` executed; generated `d365_gl_actuals.csv` (10k rows), 40 planted exceptions in `expected_exceptions.csv` |
| `REQ-KCK-08` | Kickoff §5 (L105) | Input templates as actual `.xlsx` files mirroring `04_...` and `03_...` | `sample-data/templates/*.xlsx` | `VERIFIED` | 3 `.xlsx` mapping templates generated under `sample-data/templates/` via openpyxl |
| `REQ-KCK-09` | Kickoff §5 (L106) | Root `README.md` describing product, docs opening, current phase | `README.md` | `VERIFIED` | Root `README.md` expanded to 108 lines covering product, Phase 0 status, reading order, architecture, disclaimer |
| `REQ-KCK-10` | Kickoff §5 (L107-108) | Repo skeleton folders (`docs/`, `app/`, `ui/`, `sample-data/`, `tests/`, `packaging/`, `scripts/`) + `.gitkeep` | Repo root | `VERIFIED` | All skeleton folders (`app/`, `ui/`, `sample-data/`, `tests/`, `packaging/`, `scripts/`, `evidence/`, `scratch/`) created with `.gitkeep` |
| `REQ-KCK-11` | Kickoff §5 (L109-124) | Kickoff Quality Gate (9 checks) self-audited with evidence before approval | `00_INDEX.md` §9; `14_TESTING_QA_PLAN.md` §15 | `GAP` | Wave-5 independent run: 8/9 — K2 (contract L112 "each forecast method") fails: locked actuals (`CALC-060`), 3-month average (`CALC-063`), manual override (`CALC-064`) are defined only (`05:284`, `05:287`, `05:288`) with no worked example in `05` §12 (F1–F14) or `07` §11 (`07:216`–`221` = F14a–F14d only; fixture register `05:602` covers F14a–c) — `14:680` `GATE-01-02` ✅ is false (`F-023`) |
| `REQ-KCK-12` | Kickoff §6 (L125-142) | Approved product scope v1: In-scope vs Out-of-scope boundaries defined | `01_PRD.md` §4, §5 | `VERIFIED` | In-scope (10 areas) and out-of-scope (24 items `BL-001`–`024`) documented |
| `REQ-KCK-13` | Kickoff §7 (L143-155) | Canonical star schema data model: facts (`FactGLActuals`, `FactGLBudget`), dimensions (`DimAccount`, etc.) | `03_DATA_DICTIONARY.md` §2, §3 | `VERIFIED` | Star schema fully specified with types, nullability, grains |
| `REQ-KCK-14` | Kickoff §8 (L156-167) | Deterministic calculation rules: variance, variance %, favorability, MTD/YTD, rounding, forecast methods | `05_CALCULATION_SPEC.md` §2–§9 | `VERIFIED` | Formally specified with formulas and golden fixtures |
| `REQ-KCK-15` | Kickoff §9 (L168-177) | Exception engine: >=15 rules, ID, intent, logic, thresholds, severity, owner, FP mitigation, planted case | `06_EXCEPTION_RULES_CATALOG.md` §3, §4 | `CONTRADICTION` | 24 rules specified with all required fields, but the canonical planted case contradicts across docs: `05:524` (F13a golden fixture) verdict says `EXC-010` (cut-off/timing rule per `06:214`) while owner `06:738` maps F13a/P18 to `EXC-018` (material variance per `06:222`); `14:279` and `expected_exceptions.csv` P18 also say `EXC-018` — 4 of 5 sources agree (`F-020`) |
| `REQ-KCK-16` | Kickoff §10 (L178-189) | AI policy: optional, local/offline fallback, no auto-approval, prompt templates versioned, redaction | `10_AI_INTEGRATION_SPEC.md` §2, §4, §6 | `VERIFIED` | AI policy, guardrails, redaction rules fully documented |
| `REQ-KCK-17` | Kickoff §11 (L190-197) | Reporting outputs: Excel workbook (8 sheets), PowerPoint deck (4–6 slides) | `11_EXCEL_OUTPUT_SPEC.md`; `12_POWERPOINT_OUTPUT_SPEC.md` | `VERIFIED` | 8 sheets and 6 slides specified in complete detail |
| `REQ-KCK-18` | Kickoff §12 (L198-207) | UX for non-technical users: guided wizard, plain-language errors, confirmations, sample project | `08_UI_UX_SPEC.md` §2, §7 | `VERIFIED` | Guided navigation and plain-language wording rules specified |
| `REQ-KCK-19` | Kickoff §13 (L208-217) | Quality, testing & acceptance: golden tests, UAT script, explicit numeric NFRs | `14_TESTING_QA_PLAN.md` §3, §5, §12 | `VERIFIED` | 292 tests catalogued, 16 NFRs stated with metrics |
| `REQ-KCK-20` | Kickoff §14 (L218-229) | Session protocol: quote-before-code, CHANGELOG discipline, SESSION_LOG tracking | `19_VIBE_CODING_PLAYBOOK.md` §3; `CHANGELOG.md`; `SESSION_LOG.md` | `VERIFIED` | Protocol established and logged across sessions |
| `REQ-KCK-21` | Kickoff §15 (L230-239) | Immediate next actions executed strictly in order (superseded by later addons) | `docs/CHANGELOG.md` | `VERIFIED` | Author tracked execution order across addon increments |

---

## 2. Addon 1 Requirements Inventory

| Req ID | Contract Source | Requirement Description | Target Deliverable Doc & Section | Audit Status | Evidence / Audit Pointer |
|---|---|---|---|---|---|
| `REQ-A1-01` | Addon 1 §A (L245-253) | Addon integration discipline; later addons add requirements and never remove | `00_INDEX.md` §4 | `VERIFIED` | Addon 1 incorporated into Coverage Matrix |
| `REQ-A1-02` | Addon 1 §B (L254-268) | Ten additional zero-compromise principles (P11–P20) | `19_VIBE_CODING_PLAYBOOK.md` §2 | `VERIFIED` | P11–P20 defined and operationalized |
| `REQ-A1-03` | Addon 1 §C.1 (L269-288) | New Phase 0 docs: `21` Questionnaire, `22` User Guide, `23` Handover, `24` Release Runbook, `25` Risk Register | `docs/` (`21`–`25`) | `VERIFIED` | Docs 21–25 created and elaborated |
| `REQ-A1-04` | Addon 1 §C.2 (L289-311) | Specific table additions across original docs (`01`, `02`, `03`, `04`, `05`, `08`, `09`, `10`, `13`, `14`, `15`, `16`, `17`, `18`) | Owning docs | `VERIFIED` | Table additions present in respective docs |
| `REQ-A1-05` | Addon 1 §D (L312-338) | Domain completeness checklist (feeds doc 21; decision + default for each item) | `21_CLIENT_ONBOARDING_QUESTIONNAIRE.md` §3 | `VERIFIED` | 21 questions with rationale and labelled defaults |
| `REQ-A1-06` | Addon 1 §E (L339-357) | Additional functional requirements (seed FRs for doc 02) | `02_FUNCTIONAL_SPEC.md` | `VERIFIED` | Incorporated into FR-IMP, FR-EXC, FR-BVA families |
| `REQ-A1-07` | Addon 1 §F (L358-373) | Excel/CSV ingestion hardening (encoding, delimiter, merged headers, formula values, etc.) | `04_SOURCE_MAPPING_AND_IMPORT_SPEC.md` §4–§8 | `VERIFIED` | 32 validation checks and quirk handling defined |
| `REQ-A1-08` | Addon 1 §G (L374-385) | Windows 11 & environment hardening (path length, OneDrive locking, DPI scaling) | `08_UI_UX_SPEC.md` §9; `09_TECHNICAL_ARCHITECTURE.md` §5; `15` §5 | `VERIFIED` | LocalAppData storage and OneDrive conflict handling specified |
| `REQ-A1-09` | Addon 1 §H (L386-397) | Financial-correctness addenda (leap year, negative budgets, divide by zero, rounding modes) | `05_CALCULATION_SPEC.md` §4, §5, §6 | `VERIFIED` | Rounding half-up, KPI guards, sign conventions specified |
| `REQ-A1-10` | Addon 1 §I (L398-408) | Security, privacy & supply-chain addenda (DPAPI, key rotation, SBOM, license allowlist) | `13_SECURITY_PRIVACY.md` §5; `17_CODING_STANDARDS.md` §7 | `VERIFIED` | DPAPI storage, key rotation, license allowlist documented |
| `REQ-A1-11` | Addon 1 §J (L409-419) | Delivery, release & upgrade addenda (semantic versioning, schema versioning, uninstaller) | `24_RELEASE_AND_VERSIONING_RUNBOOK.md` §2, §4; `15` §7 | `VERIFIED` | App and schema versioning, migration rules defined |
| `REQ-A1-12` | Addon 1 §K (L420-429) | Client enablement (docs 22/23 task structure, training outline) | `22_END_USER_GUIDE.md` §3; `23` §5 | `VERIFIED` | Task-based guide and consultant training outline written |
| `REQ-A1-13` | Addon 1 §L (L430-447) | NFR addenda (explicit numbers for throughput, latency, package size) | `14_TESTING_QA_PLAN.md` §3 (NFR-001–016) | `VERIFIED` | 16 canonical NFRs defined with quantitative bars |
| `REQ-A1-14` | Addon 1 §M (L448-458) | Session protocol addenda (SESSION_LOG format, CHANGELOG doc-first rule) | `19_VIBE_CODING_PLAYBOOK.md` §3; `SESSION_LOG.md` | `VERIFIED` | Implemented and maintained |
| `REQ-A1-15` | Addon 1 §N (L459-464) | Explicitly parked backlog (BL-001 to BL-024 recorded with reasons) | `01_PRD.md` §5; `27_BACKLOG.md` §3 | `VERIFIED` | 24 parked items seeded with trigger conditions |
| `REQ-A1-16` | Addon 1 §O (L465-481) | Combined Phase 0 Quality Gate (12 delta checks) | `00_INDEX.md` §9 (`GATE-02`); `14` §15 | `VERIFIED` | Quality Gate 2 verified 12/12 green (tabletop walkthrough, negative corpus, repo structure complete) |
| `REQ-A1-17` | Addon 1 §P (L482-493) | Updated immediate next actions (superseded by Addon 2) | `docs/CHANGELOG.md` | `VERIFIED` | Tracked in project history |

---

## 3. Addon 2 Requirements Inventory

| Req ID | Contract Source | Requirement Description | Target Deliverable Doc & Section | Audit Status | Evidence / Audit Pointer |
|---|---|---|---|---|---|
| `REQ-A2-01` | Addon 2 §A (L499-507) | Addon 2 integration discipline & quality gate enforcement | `00_INDEX.md` §4 | `VERIFIED` | Addon 2 incorporated into Coverage Matrix |
| `REQ-A2-02` | Addon 2 §B.1 (L510-515) | Headless engine boundary; all money logic in engine; CLI with exit codes | `09_TECHNICAL_ARCHITECTURE.md` §3 (ADR-002), §4 | `VERIFIED` | Headless boundary and CLI commands/exit codes specified |
| `REQ-A2-03` | Addon 2 §B.2 (L516-523) | API contract (new document `26_API_CONTRACT.md`); OpenAPI source of truth, error envelope, pagination | `26_API_CONTRACT.md` | `VERIFIED` | 95 endpoints, envelope schema, pagination, error catalogue |
| `REQ-A2-04` | Addon 2 §B.3 (L524-528) | Data-volume rule (browser never sees raw firehose; engine paginates/aggregates) | `09_TECHNICAL_ARCHITECTURE.md` §10; `26` §3 | `VERIFIED` | Page size limits and windowed queries specified |
| `REQ-A2-05` | Addon 2 §B.4 (L529-534) | Configuration layering (defaults -> project settings -> user settings) | `09_TECHNICAL_ARCHITECTURE.md` §8 | `VERIFIED` | Precedence hierarchy documented |
| `REQ-A2-06` | Addon 2 §B.5 (L535-546) | ADR-002: Pin remaining toolchain (Pydantic v2, Ruff, Pytest, Playwright, Tailwind, Lucide, openpyxl, python-pptx) | `09_TECHNICAL_ARCHITECTURE.md` §3.3 | `VERIFIED` | ADR-002 formally pins exact toolchain |
| `REQ-A2-07` | Addon 2 §B.6 (L547-552) | One-command scripts (`scripts/dev`, `scripts/test`, `scripts/build`, `scripts/check`) | `09_TECHNICAL_ARCHITECTURE.md` §15; `scripts/` | `VERIFIED` | `scripts/` directory created with `.gitkeep`; script specifications locked in `09` §15 |
| `REQ-A2-08` | Addon 2 §B.7 (L553-559) | Recompute & invalidation semantics (dirty marking, cascade rules) | `09_TECHNICAL_ARCHITECTURE.md` §9 | `VERIFIED` | Invalidation graph and dirty state rules defined |
| `REQ-A2-09` | Addon 2 §C (L560-591) | Document additions across docs 01, 02, 05, 08, 09, 10, 12, 14, 16, 17, 18, 19, 20 | Owning docs | `VERIFIED` | Additions integrated in respective files |
| `REQ-A2-10` | Addon 2 §D (L592-610) | Functional precision (exception identity/re-run semantics, drill-down breadcrumbs, report versioning) | `02_FUNCTIONAL_SPEC.md` §4–§7 | `VERIFIED` | Identity preservation, breadcrumb navigation specified |
| `REQ-A2-11` | Addon 2 §E (L611-621) | UI/UX & brand addenda (typography, tokens, WCAG AA, dark mode parked) | `08_UI_UX_SPEC.md` §10, §11 | `VERIFIED` | Design tokens, WCAG AA contrast rules defined |
| `REQ-A2-12` | Addon 2 §F (L622-632) | Testing, CI & quality bars (>=90% engine coverage, Playwright golden path) | `14_TESTING_QA_PLAN.md` §13 | `VERIFIED` | Coverage bars and Playwright tests catalogued |
| `REQ-A2-13` | Addon 2 §G (L633-641) | AI addenda (usage log `FactAIUsage`, draft provenance, number-mismatch stance: strip and flag) | `10_AI_INTEGRATION_SPEC.md` §8.2, §9.3, §12 | `VERIFIED` | Strip-and-flag policy and usage logging specified |
| `REQ-A2-14` | Addon 2 §H (L642-650) | Process & governance (conventional commits, ADR process, blocking question format) | `17_CODING_STANDARDS.md` §10; `18` §4.3; `19` §7 | `VERIFIED` | Conventional Commits, ADR-000 template, question format |
| `REQ-A2-15` | Addon 2 §I (L651-667) | Phase 0 quality gate deltas (12 checks) | `00_INDEX.md` §9 (`GATE-03`); `14` §15 | `VERIFIED` | Quality Gate 3 verified 12/12 green (95 API routes frozen, `scripts/` active, matrix integrated) |
| `REQ-A2-16` | Addon 2 §J (L668-679) | Updated immediate next actions (superseded by Addon 3) | `docs/CHANGELOG.md` | `VERIFIED` | Tracked in project history |

---

## 4. Addon 3 Requirements Inventory

| Req ID | Contract Source | Requirement Description | Target Deliverable Doc & Section | Audit Status | Evidence / Audit Pointer |
|---|---|---|---|---|---|
| `REQ-A3-01` | Addon 3 §A (L685-693) | Addon 3 integration discipline & quality gate enforcement | `00_INDEX.md` §4 | `VERIFIED` | Addon 3 incorporated into Coverage Matrix |
| `REQ-A3-02` | Addon 3 §B.1 (L696-706) | New Phase 0 docs: `27_BACKLOG.md`, `28_ACCEPTANCE_UAT_AND_GO_LIVE.md` | `docs/` (`27`, `28`) | `VERIFIED` | Docs 27 and 28 created and elaborated |
| `REQ-A3-03` | Addon 3 §B.2 (L707-729) | Required additions to docs 01, 02, 03, 05, 06, 08, 09, 10, 11, 12, 14, 16, 18, 19 | Owning docs | `VERIFIED` | Additions integrated in respective files |
| `REQ-A3-04` | Addon 3 §C (L730-746) | Feature precision part 2 (AI mapping review queue, commentary workflow, pack issuance register, data-quality score) | `02_FUNCTIONAL_SPEC.md` §5, §8, §10; `10` §13 | `VERIFIED` | FR-IMP-008, FR-BVA-012, FR-REP-005 specified |
| `REQ-A3-05` | Addon 3 §D (L747-755) | AI feature depth: four full prompt texts with schemas and sample-data worked examples | `10_AI_INTEGRATION_SPEC.md` §5.1–§5.4 | `GAP` | Texts and schemas present, but contract L749/L807 require worked example **input/output** on sample data: P2/P3/P4 are output-only (`10:487`, `10:634`, `10:747` — no input payload anywhere in §5); P1's input (`10:323`–`326`) is internally impossible — YTD actual ₹61,80,000 < Sep MTD ₹1,05,40,000 (both measures) — and `10:336` driver cites prior-month budget data the payload lacks (`F-024`, `F-028`); `14:729` `GATE-04-03` ✅ is false |
| `REQ-A3-06` | Addon 3 §E (L756-764) | Decisions that must be settled (success metrics, IP/licensing, forced in/out list, support/warranty) | `01_PRD.md` §5, §15, §16; `18` §5 | `VERIFIED` | Settled and logged in PRD and DEC register |
| `REQ-A3-07` | Addon 3 §F (L765-774) | Charts inventory (12), centralized conditional formatting (12), output conventions, negative file corpus | `08_UI_UX_SPEC.md` §5, §6; `14` §6; `sample-data/malformed/` | `VERIFIED` | Charts & CF rules in `08`; `sample-data/malformed/` with 16 negative test corpus files generated on disk |
| `REQ-A3-08` | Addon 3 §G (L775-784) | Acceptance, UAT & go-live (project DoD, UAT mechanics, defect severities S1–S4, 22-item go-live checklist) | `28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §2, §5, §6 | `GAP` | DoD, S1–S4, 6 UAT scripts and the 22-item checklist are present, but the mandated UAT entry criterion "entry = features demoed" (contract L778, required present by L815) is missing from `28` §5 (`28:142`–`173`; §5.1 table has no entry row; word "entry" occurs only at `28:81`, `:82`, `:239`, `:241`, all unrelated); additionally `28:46` cites a non-existent §5.5 exit record (§5 ends at §5.3) — `F-025` |
| `REQ-A3-09` | Addon 3 §H (L785-792) | Backlog governance (entry schema, 34 seeded items, review ritual at every gate) | `27_BACKLOG.md` §2, §3, §4 | `VERIFIED` | 34 items seeded with trigger conditions |
| `REQ-A3-10` | Addon 3 §I (L793-802) | Process & quality deltas (exception perf NFR, ADR-000 index, local crash dumps, prompt-edit process) | `09_TECHNICAL_ARCHITECTURE.md` §3.1, §6; `10` §4.2; `14` §3 | `VERIFIED` | ADR-000 index, local dumps, prompt edit discipline documented |
| `REQ-A3-11` | Addon 3 §J (L803-819) | Phase 0 quality gate deltas (12 checks) | `00_INDEX.md` §9 (`GATE-04`); `14` §15 | `GAP` | Wave-5 independent gate run: 10/12 — A3J-3 (`GATE-04-03`, contract L807: prompt worked-example inputs missing, `F-024`) and A3J-11 (`GATE-04-11`, contract L815: UAT entry criterion missing, `F-025`) fail; `14:729` and `14:737` ✅ are false |
| `REQ-A3-12` | Addon 3 §K (L820-833) | Updated immediate next actions (superseded by Addon 4) | `docs/CHANGELOG.md` | `VERIFIED` | Tracked in project history |

---

## 5. Addon 4 Requirements Inventory

| Req ID | Contract Source | Requirement Description | Target Deliverable Doc & Section | Audit Status | Evidence / Audit Pointer |
|---|---|---|---|---|---|
| `REQ-A4-01` | Addon 4 §A (L839-847) | Addon 4 integration discipline & quality gate enforcement | `00_INDEX.md` §4 | `VERIFIED` | Addon 4 incorporated into Coverage Matrix |
| `REQ-A4-02` | Addon 4 §B.1 (L848-855) | Standard doc header present on every doc; TL;DR <= 15 lines | All docs `00`–`29` | `VERIFIED` | All 31 docs (`00`–`30`) + `PHASE0_SUMMARY.md` verified with TL;DR strictly ≤ 6 lines (limit ≤ 15) |
| `REQ-A4-03` | Addon 4 §B.2-B.5 (L856-861) | Session reading plan, quote-before-code, decisions accumulate forward, paraphrase ban | `00_INDEX.md` §2.2; `19_VIBE_CODING_PLAYBOOK.md` §3.2, §3.3 | `VERIFIED` | Session reading order and quoting rules established |
| `REQ-A4-04` | Addon 4 §C (L862-905) | Source-of-Truth Matrix in `00_INDEX.md`; one owner per fact; zero duplication; conflict rule | `00_INDEX.md` §5, §6.2 | `VERIFIED` | 29-row matrix and conflict-resolution precedence defined |
| `REQ-A4-05` | Addon 4 §D (L906-915) | FR prioritization (P0/P1/P2), never-cut list (9 items), phase gate rule, cut process | `02_FUNCTIONAL_SPEC.md` §3; `16_ROADMAP_PHASES.md` §9 | `VERIFIED` | All FRs prioritized; 9 never-cut items aligned |
| `REQ-A4-06` | Addon 4 §E.1 (L918-928) | New doc `29_CLIENT_REQUIREMENTS_PACK.md`: plain language, decisions with recommendations, sign-off block | `29_CLIENT_REQUIREMENTS_PACK.md` | `VERIFIED` | Jargon-free pack with 17 decisions and sign-off block |
| `REQ-A4-07` | Addon 4 §E.2 (L929-934) | Approval recording mechanics (CHANGELOG + SESSION_LOG + PRD sign-off block) | `19_VIBE_CODING_PLAYBOOK.md` §6.1; `CHANGELOG.md` | `VERIFIED` | Protocol established in playbook |
| `REQ-A4-08` | Addon 4 §E.3 (L935-940) | Post-approval change impact rule (impact note before code; S/M/L sizing) | `19_VIBE_CODING_PLAYBOOK.md` §5.3; `29` §15 | `VERIFIED` | S/M/L impact assessment required before edits |
| `REQ-A4-09` | Addon 4 §F (L941-949) | Real-data pilot gate between final build and UAT; tie-out worksheet, 4-class taxonomy | `28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §4 | `VERIFIED` | Preconditions, classification log, tie-out worksheet specified |
| `REQ-A4-10` | Addon 4 §G.1 (L952-958) | Numerical tolerance policy (no binary float, minor units, zero balance tolerance, sum-of-rounded footnote) | `05_CALCULATION_SPEC.md` §6.2, §13 | `VERIFIED` | Exact Decimal rules and tolerance bindings documented |
| `REQ-A4-11` | Addon 4 §G.2 (L959-978) | Edge-case data matrix (13 rows with canonical behavior and error message IDs) | `02_FUNCTIONAL_SPEC.md` §16; `14_TESTING_QA_PLAN.md` §5.2 | `CONTRADICTION` | The two mandated matrices disagree on message IDs: `02` §16 (13 rows `E1`–`E13`, `02:1258`–`1270`) vs `14` §6.2 (16 rows, `14:313`–`328`) — rows 1/2/4/11/13 carry different slugs, rows 14–16 have no `02` counterpart, and 8 slugs used in `14` (`import.budgetCoverageGap`, `import.mappingIncomplete`, `import.parenthesesUnresolved`, `import.numberUnparsed`, `import.signRuleApplied`, `import.encryptedFile`, `import.fileLocked`, `import.formulaNoCachedValue`) exist nowhere in `02`; contract L1014 requires the matrix "with message IDs" in both docs — `14:753` `GATE-05-10` ✅ is false (`F-022`) |
| `REQ-A4-12` | Addon 4 §H (L979-986) | Sample-data integrity: watermark, project_type flag, no interleave with real data, non-delivery rule | `14_TESTING_QA_PLAN.md` §4; `16` §10.3 | `GAP` | Spec rules defined, but the generated corpus violates contract L981/L1015/L1029: `sample-data/expected_exceptions.csv` has no `Watermark` column and no watermark string anywhere; the project-type flag exists only in `d365_gl_actuals.csv` (column `ProjectType`, values `sample`) and is absent from `bank_ledger_actuals.csv`, `budget_fy26.csv`, `payroll_procurement_actuals.csv` (no CSV uses the literal name `project_type`) — 1 of 5 CSVs carries it (`F-034`; Wave-4 "present in all CSVs" log claim corrected per `F-033`) |
| `REQ-A4-13` | Addon 4 §I (L987-995) | Engineering discipline deltas: spike policy, fresh-clone bootstrap test, code-health guardrails, storage growth math | `09_TECHNICAL_ARCHITECTURE.md` §5.2, §14; `14` §10; `17` §11 | `VERIFIED` | Spike rules, fresh-clone test, storage math defined |
| `REQ-A4-14` | Addon 4 §J (L996-1002) | Security & config deltas: AI key rotation procedure, keyless mode default | `13_SECURITY_PRIVACY.md` §5.3; `10_AI_INTEGRATION_SPEC.md` §2.1 | `VERIFIED` | Rotation steps and keyless default specified |
| `REQ-A4-15` | Addon 4 §K (L1003-1020) | Phase 0 quality gate deltas (13 checks) | `00_INDEX.md` §9 (`GATE-05`); `14` §15 | `GAP` | Wave-5 independent gate run: 12/13 — K10 (`GATE-05-10`, contract L1014) fails: `02` §16 vs `14` §6.2 message-ID contradictions (`F-022`); `14:753` ✅ is false |
| `REQ-A4-16` | Addon 4 §L (L1021-1035) | Phase 0 completion workflow: repo skeleton, docs 00–29, sample-data build, all 5 gates green, approval before code | `PHASE0_SUMMARY.md`; `00_INDEX.md` | `GAP` | Artifacts exist (skeleton, 31 docs, sample data) but the green claim is false: Wave-5 independent run = 62/66 with 3 of 6 gates FAIL — `GATE-01` K2 (`F-023`), `GATE-04` A3J-3 + A3J-11 (`F-024`, `F-025`), `GATE-05` K10 (`F-022`); `PHASE0_SUMMARY:108` "66 ✅ / 0 ⬜ — 100% PASS" and `PHASE0_SUMMARY:12` readiness overstated (`F-029`), and the page carries no `F-015` Addon-5-source caveat |

---

## 6. Addon 5 Requirements Inventory (Audit Prompt References — PROVISIONAL, contract text pending `F-015`)

> Wave 4 note: the Addon 5 contract text is absent from the workspace (only audit-prompt §8 references exist). Rows below are traced against those references as a provisional stand-in and renumbered to provisional `GATE-05B` (`GATE-06` is the packaging spike). Final verification awaits the owner supplying Addon 5 or rescinding it. `REQ-A5-01`/`04`/`06`/`07`/`08` therefore cannot be `VERIFIED` against a contract source.

| Req ID | Contract Source | Requirement Description | Target Deliverable Doc & Section | Audit Status | Evidence / Audit Pointer |
|---|---|---|---|---|---|
| `REQ-A5-01` | Addon 5 Contract (missing — provisional) | Contract Document #6 delivery and workspace presence | `project prompt/` | `PENDING-ADDON-5` | Addon 5 text absent; Doc 30 + provisional `GATE-05B` + §A.4 notice built from audit-prompt refs only (`F-015` escalated) |
| `REQ-A5-02` | Addon 5 (Audit §8.1, provisional) | Document `30_DOCUMENTATION_SET_REVIEW_GUIDE.md` exists, headered, TL;DR <= 15 lines | `docs/30_...` | `VERIFIED` | `docs/30_DOCUMENTATION_SET_REVIEW_GUIDE.md` authored (305 lines, TL;DR: 6 lines) |
| `REQ-A5-03` | Addon 5 (Audit §8.15, provisional) | Doc 30 contents: session-report format, 5-minute checklist, evidence matrix, red-flag list with response ladder, Phase 0 review guide, spot-check sampling, stuck options, oracle procedure | `docs/30_...` | `VERIFIED` | All required sections fully articulated in `docs/30_DOCUMENTATION_SET_REVIEW_GUIDE.md` §1–§8 |
| `REQ-A5-04` | Addon 5 (Audit §6-A5, provisional) | Provisional Phase-0 Addon 5 checklist (`GATE-05B`, 8 checks) integrated and independently verified | `00_INDEX.md` §9; `14_TESTING_QA_PLAN.md` §15.6 | `VERIFIED` | Provisional `GATE-05B` (8 checks) in `14_TESTING_QA_PLAN.md` §15.6 and `00_INDEX.md` §9; verified 8/8 green; number provisional pending Addon 5 source |
| `REQ-A5-05` | Addon 5 (Audit §8.18, provisional) | Divergence notice (Addon 5 §A.4) recorded in `00_INDEX.md` and `19_VIBE_CODING_PLAYBOOK.md` | `00_INDEX.md`, `19_VIBE_CODING_PLAYBOOK.md` | `VERIFIED` | Canonical Divergence Notice integrated into `19_VIBE_CODING_PLAYBOOK.md` §5.5 and `00_INDEX.md` §6.3 |
| `REQ-A5-06` | Addon 5 (Audit §4, §8.1, provisional) | `evidence/` directory live with evidence conventions | `evidence/` | `VERIFIED` | `evidence/` live with Wave 4 Level 2/3 logs (`evidence/runs/recompute_wave4.log`, `evidence/runs/sample_data_inventory_wave4.log`, `evidence/gates/gate_counts_wave4.log`) |
| `REQ-A5-07` | Addon 5 (Audit §2.2, provisional) | Coverage Matrix covers all six contract documents with all rows verified | `00_INDEX.md` §4 | `GAP` | All 6 contract docs covered and every row `INTEGRATED`, but the count claim is false: actual 86 data rows (15+17+17+17+12+8) — `00:109` claims "85 expanded rows" and `00:136` §4.2 header claims "16 rows" while the table holds 17 (`00:140`–`156`, `A1-C` split into `C.1`/`C.2`); Addon 2 §A.3 gate rule cannot be checked against a false denominator (`F-027`, reopens `F-016`) |
| `REQ-A5-08` | Addon 5 (Audit §6-A6) | Author claims & evidence audit: every 'done/green/integrated' claim backed by existing artifacts | `SESSION_LOG.md`; `CHANGELOG.md` | `VERIFIED` | Session 002 volumes/names corrected by Session 003 supersession note (Wave 4, `F-014`); `CHANGELOG.md` Wave 4 block; `evidence/` holds 3 real Wave 4 logs |

---

## Wave 5 Status Changes

| # | Req ID | Old → New | One-line rationale | Finding |
|---|---|---|---|---|
| 1 | `REQ-KCK-11` | `VERIFIED` → `GAP` | Kickoff quality gate independently re-run at 8/9; K2 "each forecast method" has no worked example for locked actuals / 3-month average / manual override | `F-023` |
| 2 | `REQ-KCK-15` | `VERIFIED` → `CONTRADICTION` | Canonical planted case F13a carries two different rule IDs across `05:524` (`EXC-010`) and owner `06:738` (`EXC-018`) — caveat added to evidence as instructed | `F-020` |
| 3 | `REQ-A3-05` | `VERIFIED` → `GAP` | Contract L749/L807 demand worked-example input/output; P2–P4 are output-only and P1's input is arithmetically impossible | `F-024`, `F-028` |
| 4 | `REQ-A3-08` | `VERIFIED` → `GAP` | UAT entry criterion ("entry = features demoed") absent from `28` §5; `28:46` cites non-existent §5.5 | `F-025` |
| 5 | `REQ-A3-11` | `VERIFIED` → `GAP` | Addon 3 gate independently re-run at 10/12 (A3J-3 prompt inputs, A3J-11 UAT entry) | `F-024`, `F-025` |
| 6 | `REQ-A4-11` | `VERIFIED` → `CONTRADICTION` | `02` §16 (13 rows) and `14` §6.2 (16 rows) contradict on message IDs; 8 `14`-slugs absent from `02`; `GATE-05-10` ✅ false | `F-022` |
| 7 | `REQ-A4-12` | `VERIFIED` → `GAP` | Watermark missing from `expected_exceptions.csv`; `ProjectType` flag present in only 1 of 5 CSVs vs contract L981/L1015/L1029 | `F-034` |
| 8 | `REQ-A4-15` | `VERIFIED` → `GAP` | Addon 4 gate independently re-run at 12/13 (K10 fails on the same matrix contradictions) | `F-022` |
| 9 | `REQ-A4-16` | `VERIFIED` → `GAP` | "All 6 gates green" / "66 ✅ — 100% PASS" is false: 62/66, 3 of 6 gates FAIL, no `F-015` caveat on the approval page | `F-029` |
| 10 | `REQ-A5-07` | `VERIFIED` → `GAP` | Coverage Matrix count claim 85 is wrong (actual 86; §4.2 header 16 vs 17 rows) — gate denominator false | `F-027` (reopens `F-016`) |

**Considered, deliberately NOT changed (for the lead's record):**

- `REQ-A1-16` (GATE-02) — unchanged. GATE-02 **passes literal 12/12**: contract L474 requires only that
  the injection *test case* exists in `14` (it does, `14:700`). `F-026`'s fixture-existence claims
  (`02:1012`, `10:815`, `13:431`, `13:527`, `14:525`) are recorded as a BLOCKER finding and the
  strict-vs-literal reading is escalated to the owner; if the owner adopts the strict reading,
  `GATE-02-08` flips and this row becomes `GAP`.
- `REQ-A2-15` (GATE-03) — unchanged. Wave-5 verdict: PASS 12/12; the matrix row-count defect is
  charged against `REQ-A5-07` / `F-027`, not against GATE-03.
- `REQ-A5-04` (provisional `GATE-05B` 8/8) — unchanged. No `GATE-05B` check failed in Wave 5; the
  `F-015` provisional-source caveat already sits in the §6 section preamble.
- **Flagged for lead decision (not drafted):** `REQ-KCK-14` evidence says "Formally specified with
  formulas and golden fixtures" while two open BLOCKERs sit in those very fixtures (`05:524` rule-ID
  → `F-020`; `05:419` 6dp truncation → `F-021`). Consider the same caveat treatment once the lead
  rules on A2.

> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** the phase model and the **next open item** pointer (Kickoff §14.1), phase
> deliverables and Definition of Done per phase (Kickoff §5), the packaging spike that runs first after
> approval (Addon 4 §L.13), the phase-gate contract and gate IDs beyond the Phase-0 checklists (`14`
> owns the Phase-0 checklists: `GATE-01`…`05` + provisional `GATE-05B`), the phase-level cut-line rule and estimates (Addon 4 §D.2/§D.5), the release
> cadence (Addon 1 §C.2), and the per-phase gate-artefact list (Addon 1 §O, Addon 2 §F.2, Addon 3 §G.6/§K)
> **TL;DR (≤ 15 lines):**
> - **Phase-gated delivery:** Six build phases following Phase 0: Packaging Spike → Core Engine → BvA → Exceptions → Forecast → Packs → AI.
> - **Strict gate rules:** Every phase requires green P0 FRs, test evidence, sample data demo, and recorded client/owner approval.
> - **The Never-Cut List:** Exact money math, atomic imports, auditability, offline isolation, and installer cannot be descoped.
> - **Effort estimates:** 96 ideal engineering days baseline with explicit variance tracking and re-estimation triggers.
> - **No silent scope creep:** Unapproved additions routed to backlog; deferrals require impact notes and formal waiver.

# 16 — Roadmap & Phase Plan

## 1. Purpose, ownership and how this document is used

### 1.1 What this document owns

| Fact | Owner |
|---|---|
| Phase list, phase deliverables, Definition of Done per phase, phase ordering | **`16` (this document)** |
| The **next open item** — the single work item the next session starts from | **`16`** |
| The packaging spike's scope, timebox and exit evidence | **`16`**, with `15` §3 and `09` §15.4 |
| Phase-gate IDs `GATE-06`…`GATE-12` and the universal gate contract | **`16`**; the Phase-0 checklists are `14` §15 |
| Ideal-effort estimates per phase and per P0 epic; re-estimation and variance rules | **`16`** (Addon 4 §D.5) |
| Release cadence at phase level (when a client-visible build exists) | **`16`**; mechanics (tags, notes, publication) belong to `24` |
| The `GATE-01`…`GATE-05` check texts, the test catalogue, NFRs and coverage bars | `14` |
| Build → installer → clean-Windows validation steps | `15` |
| Session protocol, DoD enforcement, approval recording, quoting rules | `19` |
| FR priorities and the per-FR cut policy text | `02` §3 |
| FR → spec → screen → API → test traceability | `20` |
| UAT, pilot and go-live mechanics (`GATE-13`…`GATE-15`) | `28` |
| Release checklist, semver mechanics, upgrade fixture, distribution | `24` |
| Backlog entries produced by cuts and deferrals | `27` |

### 1.2 How to use it

1. **Every session starts here last.** The mandatory order is `00_INDEX` (incl. the Coverage Matrix) →
   `CHANGELOG` entries since the last session → `SESSION_LOG` tail → **the next open item in §1.3** →
   only the docs that item names (Addon 4 §B.2). No other reading, no code.
2. **One next open item at a time.** §1.3 names exactly one; when it is closed, it is replaced in the same
   commit as the work that closed it. Two open items means the log is wrong.
3. **The item is a pointer, not a plan.** Detail lives in the owning document it names (this is the
   single-source rule; the roadmap never restates a formula, threshold or layout).
4. **A gate is passed only by its evidence pack** (§5.2), approved and recorded (`19`, Addon 4 §E.2).
5. **Estimates are transparency, not promises.** They are re-estimated at every gate and reported with
   variance; a silent slip is a protocol violation (Addon 4 §D.5).

### 1.3 The next open item (live pointer)

| Field | Value |
|---|---|
| Item | **Phase 1 — Import & Validation (`GATE-07`)** — Implement ingestion pipeline for D365 and two custom system shapes: file pre-scan, profile mapping, 32 validation checks, staging quarantine, atomic commit, and import batch history (`FR-IMP-001` through `FR-IMP-031`). |
| Why now | Packaging spike (`GATE-06`, `SPK-01`..`SPK-08`) verified green: PyInstaller onedir binary (310.2 MB ≤ 500 MB budget), React UI, and standalone portable package generated with SHA-256 manifest. |
| Definition of done for this item | Engine import parser, mapping engine, all 32 validation checks implemented and tested against `sample-data/malformed/` negative corpus and good GL files; atomic DuckDB commits; UI import wizard and check report screens active; all P0 FRs passing. |
| Next item after this one | Phase 2: BvA Variance & Drilldown (`GATE-08`, 19 FRs: lowest shared grain variance, waterfall bridge, and transaction drilldown). |
| Next after that | Phase 3: Exception Engine & Register (`GATE-09`, 24 rules). |
| Blocking | None. |

> This table is the session-start pointer. `00_INDEX` §10 and the `SESSION_LOG` "Next step" must agree with
> it; if they disagree, this table wins and the difference is corrected in the same commit.

## 2. The phase model

### 2.1 Phases, goals and gates

| Phase | ID | Goal (one line) | Exit gate | Gate owner |
|---|---|---|---|---|
| **Phase 0 — Documentation** | `P0` | The complete Phase 0 documentation set; no product code | `GATE-01`…`GATE-05` + provisional `GATE-05B` (66 checks) | `14` §15, `00_INDEX` §9 |
| **Packaging spike** | `P-S` | Prove build → installer → installed launch on real Windows 11 | `GATE-06` | this document §4, `15` §3/§5 |
| **Phase 1 — Import & validation** | `P1` | Take the client's messy files to a validated, reconciled, committed dataset | `GATE-07` | this document §6.1 |
| **Phase 2 — BvA & drill-down** | `P2` | Answer "why is this number different?" down to the transaction | `GATE-08` | §6.2 |
| **Phase 3 — Exception engine** | `P3` | Surface what needs attention, with owners, SLAs and evidence | `GATE-09` | §6.3 |
| **Phase 4 — Forecast** | `P4` | Rolling forecast with scenarios and accuracy feedback | `GATE-10` | §6.4 |
| **Phase 5 — Excel + PowerPoint packs** | `P5` | One-click, editable, client-ready month-end pack | `GATE-11` | §6.5 |
| **Phase 6 — AI & polish** | `P6` | Optional AI assistance, accessibility, performance, hardening | `GATE-12` | §6.6 |
| **Real-data pilot** | `P-RDP` | One sanitized real month end-to-end (no sample data) | `GATE-13` | `28` (Addon 4 §F) |
| **UAT** | `P-UAT` | The client's analyst runs their own month end | `GATE-14` | `28` (Addon 3 §G) |
| **Go-live** | `P-GL` | Install, train, hand over, support live | `GATE-15` | `28`, `23` |

**Rule:** gate numbers are allocated once and never reused; `GATE-01`…`GATE-05` plus provisional `GATE-05B` are the Phase-0 checklists
defined by `14` §15, `GATE-06`…`GATE-12` are defined here, and `GATE-13`…`GATE-15` are reserved to
`28` with the names above.

### 2.2 Scope → phase mapping (from `01` §18)

| Phase | Scope delivered | FRs | Families touched |
|---|---|---|---|
| 1 | Import pipeline, mapping, validation, batches, project/period setup, storage health, onboarding | 60 | `IMP` 29, `PRJ` 10, `XC` 8, `SET` 7, `ONB` 6 |
| 2 | BvA analysis, KPI library, rollups, drill-to-transaction, search, commentary workflow | 19 | `BVA` 15, `IMP` 1, `SET` 1, `ONB` 1, `XC` 1 |
| 3 | Exception engine and register: 24 rules, workflow, aging, effectiveness | 25 | `EXC` 20, `SET` 3, `PRJ` 2 |
| 4 | Rolling forecast: four methods, scenarios, versions, accuracy | 10 | `FC` 9, `BVA` 1 |
| 5 | Excel pack (8 sheet contracts + evidence bundle) and the six-slide editable deck | 21 | `XL` 9, `PPT` 7, `XC` 4, `SET` 1 |
| 6 | AI commentary/mapping assistance, accessibility, performance, hardening and polish | 21 | `AI` 14, `XC` 3, `PPT` 2, `IMP` 1, `ONB` 1 |
| | **Total** | **156** | 11 families |

**Priority split per phase** (from `02` §2/§3 — the phase gate closes on P0 only; P1/P2 gaps are listed with
an explicit decision):

| Phase | P0 | P1 | P2 | Total |
|---|---|---|---|---|
| 1 | 52 | 8 | 0 | 60 |
| 2 | 14 | 5 | 0 | 19 |
| 3 | 16 | 8 | 1 | 25 |
| 4 | 4 | 5 | 1 | 10 |
| 5 | 13 | 7 | 1 | 21 |
| 6 | 11 | 9 | 1 | 21 |
| **Total** | **110** | **42** | **4** | **156** |

**First-run/onboarding is progressive:** `ONB` FRs land in Phases 1, 2 and 6, and the guides (`22`) plus
the tour are complete before UAT (`01` §18).

**Sample data is a Phase 0 deliverable, not a Phase 1 one** (Addon 4 §L.7): the generator, two non-D365
export shapes, the input `.xlsx` templates, ~40 planted exceptions with `expected_exceptions.csv`, the
`malformed/` corpus and the `--scale 250000` mode must exist before Phase 1 code needs them.

## 3. Phase 0 completion plan (what remains before the six gates can run)

### 3.1 The remaining documents, in order

| # | Document | Primary obligations it closes |
|---|---|---|
| 16 | `16_ROADMAP_PHASES.md` | This document (already in place) |
| 17 | `17_CODING_STANDARDS.md` | Repo layout, naming, commits, branching, engine boundary, code health, `scripts/check` implementation (`02` §3.4, `13` §12, `14` §13, Addon 2 §F) |
| 18 | `18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md` | Glossary, assumptions, the `OQ-` registry, the **Decided** log (`DEC-*`) — absorbs `01` §21 |
| 19 | `19_VIBE_CODING_PLAYBOOK.md` | Session protocol, principles P1–P20, quote-before-code, gates and approvals, DoD enforcement |
| 20 | `20_REQUIREMENTS_TRACEABILITY.md` | The FR → spec → screen → API → test chain for all 156 FRs |
| 21 | `21_CLIENT_ONBOARDING_QUESTIONNAIRE.md` | Every question with its default (Addon 1 §C.1/§D) |
| 22 | `22_END_USER_GUIDE.md` | Task-structured guide; single-sourced with in-app help (`FR-ONB-007`) |
| 23 | `23_CONSULTANT_HANDOVER_AND_SUPPORT.md` | Rebuild, config/branding/prompt editing, dependency updates, diagnostics, escalation |
| 24 | `24_RELEASE_AND_VERSIONING_RUNBOOK.md` | Semver, tags, release checklist, upgrade fixture, distribution + checksum |
| 25 | `25_RISK_REGISTER.md` | Risks with likelihood/impact/mitigation/owner, reviewed at every gate |
| 26 | `26_API_CONTRACT.md` | OpenAPI-as-source-of-truth, every endpoint, the error catalog |
| 27 | `27_BACKLOG.md` | Parked items with triggers; entry schema; reviewed at gates |
| 28 | `28_ACCEPTANCE_UAT_AND_GO_LIVE.md` | Project DoD, the real-data pilot, UAT, defect workflow, `GATE-13`…`15` |
| 29 | `29_CLIENT_REQUIREMENTS_PACK.md` | The plain-language client pack with the sign-off block |
| — | `PHASE0_SUMMARY.md` | Product paragraph, key decisions, top risks, open questions, what is next |

### 3.2 Phase 0 completion steps (Addon 4 §L)

| Step | Work | Evidence |
|---|---|---|
| 1 | Repo skeleton + README | Done (Session 001) |
| 2 | Docs `00`–`20` | `CHANGELOG` + `SESSION_LOG` rows per doc |
| 3 | Addon 1: docs `21`–`25` + its in-doc additions | Coverage-matrix `A1-*` rows integrated |
| 4 | Addon 2: doc `26` + `ADR-002` + its additions | `A2-*` rows integrated |
| 5 | Addon 3: docs `27`–`28`, the four prompt texts, chart inventory, negative corpus spec | `A3-*` rows integrated |
| 6 | Addon 4: doc `29`, Source-of-Truth Matrix, doc headers, FR priorities, tolerance/edge matrices | `A4-*` rows integrated |
| 7 | Build `sample-data/` per `14` §16 | Corpus + fixtures + `--scale` run |
| 8 | Refresh the **Addon Coverage Matrix** (all five documents) | `00_INDEX` §4 all `INTEGRATED` |
| 9 | Self-audit against all six gates; fix every gap; run the link-check | `14` §15 evidence pack |
| 10 | Tabletop month-end walkthrough (Addon 1 §P20) and the cold-start client pass (Addon 4 §L.10) | Walkthrough notes in `SESSION_LOG` |
| 11 | `PHASE0_SUMMARY.md` + `SESSION_LOG` entry | The summary document |
| 12 | **STOP. Present `PHASE0_SUMMARY` + doc `29` and wait for recorded approval. No product code.** | Approval recorded in `CHANGELOG` + `SESSION_LOG` (`19`) |

### 3.3 What "Phase 0 done" means (the only definition that counts)

1. All 31 specification documents (`00`–`30`) exist, each with the standard header and a TL;DR ≤ 15 lines. The two process files (`CHANGELOG`, `SESSION_LOG`) follow their own simpler header convention.
2. Every FR is numbered, prioritised, testable and traced (doc `20`); zero blocking `TBD`s remain.
3. The six Phase-0 checklists (`GATE-01`…`GATE-05` + provisional `GATE-05B`, 66 checks) are green with evidence, including the link-check.
4. The Coverage Matrix shows every spec section integrated (no `PENDING`, no `IN PROGRESS`).
5. The sample-data corpus and its fixtures exist and the planted-exception expectations are frozen.
6. `PHASE0_SUMMARY.md` is written and the set has been presented for approval.
**Until all six hold, no product code is written** (Addon 4 §L.12).

## 4. The packaging spike (`GATE-06`, first work after approval)

**Why it is first:** the riskiest integration in the product is not an algorithm — it is a PyInstaller
build inside an Inno Setup installer launched on a stranger's Windows 11 with SmartScreen in the way
(Addon 1 §G.3, Addon 4 §L.13). If that path is broken, everything else is a demo, not a product.

| Aspect | Rule |
|---|---|
| Purpose | Prove the *delivery* path end-to-end before any product feature is written: hello-world → `scripts/build` → PyInstaller `onedir` → Inno Setup → installed launch on real Windows 11, exercising the SmartScreen path |
| Timebox | **Two half-day spikes** (build path; install/SmartScreen path). The spike policy (`09` §15.1) normally caps a spike at half a day; this one is split rather than extended, and both halves must end with a written outcome |
| Scope | No product features. A window that says hello, reads its version from the same source as the installer, and writes nothing outside its data directory. The UI shell must be the real shell (WebView2) — not a mock |
| Evidence | The installer + SHA-256, the `scripts/build` transcript, the signing state, screenshots of the install (incl. SmartScreen if it appears), the installed launch, About/version match, and the uninstall |
| Exit criteria | The installed build launches on a clean Windows 11 machine, the version matches the artefact name and About, the SmartScreen experience matches `15` §8.3 (or differs and `15` is corrected), and uninstall leaves no leftovers outside the profile |
| Outcomes to record | A `CHANGELOG`/`SESSION_LOG` entry; `ADR-005` confirmed (or superseded); `15` §3/§4/§5 corrected if reality differed; any blocker becomes the first Phase 1 item or a `27` backlog entry with a trigger |
| Failure rule | If the path cannot be made to work as specified, **stop and escalate** — do not start Phase 1 on top of an unproven installer. The fallback options (portable zip, browser fallback, signing certificate) are decided here, not later |
| Gate | `GATE-06` — checked against the table above; recorded by the same approval convention as every gate (`19`) |
| Not in scope | Auto-update, MSIX/Store packaging, per-machine installs, signing-certificate purchase (the decision is recorded, not executed) |

**Why the spike is not "Phase 0.5" in the document sense:** it produces code, so it cannot start before
approval; and it produces no client feature, so it must not grow into Phase 1. Its only deliverable is
proof plus corrected docs.

## 5. The universal gate contract (applies to `GATE-06`…`GATE-12`)

### 5.1 What every gate requires

| # | Requirement | Evidence | Owner |
|---|---|---|---|
| 1 | Full `scripts/check` green (format, lint, types, import boundary, all test levels, coverage, UI checks, secret/licence scans, docs link-check) | The transcript, attached | `17`, `14` §13.1 |
| 2 | Coverage bars met (`app/engine` ≥ 90 %, `app` ≥ 75 %); a drop > 2 points explained | `coverage.xml` | `14` §13.2 |
| 3 | The phase's NFRs measured against **committed baselines**; nothing > 20 % regressed | `perf.json` + baseline diff | `14` §8 |
| 4 | The acceptance harness's bars where the phase raises exceptions (recall ≥ 90 %, zero control raises, 18/18 High) | `acceptance_report.json` | `14` §5, `06` §8.3 |
| 5 | Cross-artifact equality: engine JSON = UI = Excel = deck = CSV, zero tolerance | The harness report | `14` §7, `NFR-015` |
| 6 | The phase's Windows-environment checks run on the real machine, with the `15` §5 protocol items that apply | Signed checklist + screenshots | `15` §5 |
| 7 | Every new/changed FR is reflected in `20` (chain filled) and the FR is demoable | `20` rows | `20` |
| 8 | Addon Coverage Matrix rows for the phase are integrated | `00_INDEX` §4 | `00` |
| 9 | `CHANGELOG` entry (what changed, why) and `SESSION_LOG` entry (test results, next item) | Both files | `19` |
| 10 | `27` backlog updated (new deferrals) and `18`'s Decided log updated (new decisions) | Both files | `27`, `18` |
| 11 | A **3–5 minute demo script** that runs on sample data with expected results, rehearsed | Recorded in `SESSION_LOG` | `16` §11, Addon 3 §K.4 |
| 12 | No silent scope change: P1/P2 gaps are listed with a finish-or-defer decision (`02` §3.2) | Gate checklist | `16` §9 |
| 13 | All P0 FRs of the phase green, including error/empty/loading states | Traceability + tests | `02` §3.2 |
| 14 | Docs affected by the phase are updated in the same gate (never "docs later") | `CHANGELOG` rows per doc | `19` |

**The gate is a conversation with evidence, not a green light on a feeling.** Every item above is
either evidenced or the gate does not pass.

### 5.2 The phase evidence pack

| Artefact | Format | Where it lives |
|---|---|---|
| Gate checklist (this document's §5.1 items, ticked per phase) | Markdown in the phase folder under `docs/evidence/phase-<n>/` | Repo (documents, no binaries) |
| Test and coverage transcripts | The raw `scripts/check` output + `coverage.xml` | Attached to the gate record, not committed |
| Performance report | `perf.json` + the baseline diff | `tests/perf/baselines/` for the baseline, the run report attached |
| Acceptance harness report | `acceptance_report.json` | Attached |
| Cross-artifact report | The harness's diff output | Attached |
| Windows validation checklist | Signed checklist + screenshots (`15` §5.3) | Attached |
| Demo script + result | `SESSION_LOG` entry | Repo |
| Coverage-matrix snapshot | `00_INDEX` §4 rows for the phase | Repo |
| Approval | `Phase <n> gate APPROVED — <who> — <date>` in `CHANGELOG` **and** `SESSION_LOG` | Repo |

### 5.3 Approval, waivers and re-entry

| Situation | Rule |
|---|---|
| Passing | The owner records the approval line in `CHANGELOG` + `SESSION_LOG`; this document's next open item is updated in the same commit |
| Failing | Written gap list with owners and dates; the next open item becomes the first gap; nothing downstream starts |
| Waiving a non-P0 item | Allowed only with the owner's explicit approval, a `27` entry with a trigger, and a note in the gate checklist. **Never-cut items cannot be waived** (`02` §3.3) |
| Late discovery (a defect in a passed phase) | It becomes a P0 item of the current phase if it violates a never-cut rule or an FR's acceptance; otherwise a `27` entry with severity |
| Re-opening a gate | A material change after approval re-opens it (Addon 4 §E.3: impact note first — affected FRs, docs, tests, size S/M/L — then the change) |
| Partial phase delivery | Not a gate. A phase closes whole; partial work stays in `SESSION_LOG`, never in the release history |
| Approval by silence | Never. No reply is not an approval |

### 5.4 What a gate is not

- Not a demo day: the demo is item 11 of fourteen, not the acceptance criterion.
- Not a code freeze by itself: the freeze is the release candidate, and `24` owns the tagging.
- Not a place to re-negotiate scope: scope changes go through `02` §3.4 (proposal → approval → `27`).
- Not a substitute for the six Phase-0 checklists: `GATE-01`…`GATE-05` + provisional `GATE-05B` are about the *specification*; the
  build gates are about the *product*. Both exist; neither replaces the other.

## 6. Per-phase plans

Each phase below carries: goal and gate · deliverables · dependencies · Definition of Done ·
demo outline · principal risks · estimate. The universal contract (§5.1) applies to every one of them
without repetition.

### 6.1 Phase 1 — Import & validation (`GATE-07`)

**Goal:** take the client's real, messy files (D365-style export + two other systems) to a validated,
reconciled, atomically committed dataset — with the project, periods and storage in place.

| Deliverable | Detail | Owner doc |
|---|---|---|
| Import wizard (7 steps, resumable) | Source type, file, mapping, preview, validation, commit, report | `04` |
| Mapping profiles | Fingerprint auto-match, versions, mid-year changes, import/export | `04`, `FR-IMP-005` |
| 32 validation checks (`IMP-001`…`032`) | Reject vs quarantine per the documented rule, plain-language messages | `04` §10 |
| Batch lifecycle | Staging → committed → voided; re-import guard; incremental loads; duplicate keys | `03` §5.7, `04` |
| Validation report + reconciliation | Per-check counts, first-N offending rows, control totals | `04` |
| Project/period/storage | New-project and new-period wizards, backup/restore, storage health, archive-and-delete | `FR-PRJ-*`, `FR-SET-001` |
| Onboarding | Sample project, blank templates, last-project reopen, help panel | `FR-ONB-001`…`006` |
| Data-quality score | The engine-computed score with its inputs visible and never masking a failure | `CALC-050`, `FR-IMP-022` |

| Dependency | Why |
|---|---|
| `sample-data/` corpus | Nothing is testable with real files before it exists (Phase 0 step 7) |
| Packaging spike passed | An unproven installer must not carry a year of feature work |
| `26` (API contract) | Import endpoints and their errors are part of the contract |
| `17` (standards) + `19` (protocol) | The engine boundary and the DoD are enforced from the first commit |

**Definition of Done (phase-specific, on top of §5.1):**

1. Every import path in `04` §2–§3 runs on the corpus: Excel, CSV, the three system shapes, the malformed set.
2. Atomicity is demonstrated: a mid-import kill leaves no partial batch (`TST-IMP-*`, fault injection).
3. All 32 checks fire on their planted cases (`14` §6.3), each with its documented message.
4. Re-running the same file is refused or reconciled exactly as specified (idempotency test).
5. Void and re-import preserve history, and the audit trail records both (`SEC-048`).
6. A fresh clone + `scripts/bootstrap` + `scripts/check` passes on a clean machine (`GATE-05-12`).
7. The Phase-0 gates remain green — no regression in the earlier evidence.

**Demo outline (3–5 min):** open the sample project → import a malformed file and show its named error →
import the good GL file through validation → show the validation report and control-total reconciliation →
open Import History and void/re-import → open storage health. *(6 steps, all on sample data.)*

**Risks → contingencies**

| Risk | Trigger | Contingency |
|---|---|---|
| Real client files differ from the spec'd shapes | Pilot (Addon 4 §F) | The two non-D365 shapes prove mapping flexibility; a new shape is a mapping profile, not code, unless a new control-total rule is required |
| Import performance misses `NFR-002` | Baseline run | Profile first (Polars lazy paths, partition by month); do not trade the 60 s target for correctness — correctness is never-cut |
| A validation check is ambiguous | Test-writing | The rule is fixed in `04` (with its message) before code; ambiguity is a spec defect |

**Estimate:** **24 ideal days** (§7).

### 6.2 Phase 2 — BvA & drill-down (`GATE-08`)

**Goal:** answer "why is this number different?" from a headline down to the transaction, with the KPI
library and rollups consistent at every grain.

| Deliverable | Detail | Owner doc |
|---|---|---|
| BvA engine | MTD/YTD/PY/TTM windows, variance, %, pp, favour*ability* | `05` |
| KPI library | `KPI-001`…`006` with divide-by-zero and negative-budget handling | `05` §5 |
| Drill-to-transaction | Hierarchy → period → transaction, ≤ 5 minutes, every level reconciling to its parent | `FR-BVA-*` |
| Rollups and grain invariants | Any slice sums to its parent; the sum-of-rounded rule | `05` §6.2, §7 |
| Search and comparability | Cross-entity/vendor/cost-centre search; the comparability guard on every comparison | `FR-BVA-012`, `FR-BVA-013` |
| Stale-data semantics | Mapping/threshold/master-data changes mark derived results stale, never silently outdated | `FR-SET-010` |
| Dashboard and states | Home KPIs, charts `CHT-*`, the state matrix, conditional formatting, empty/loading/error states | `08` §5, §9, §13–§14, §17; `FR-BVA-016` |

**Definition of Done:** every figure on every screen traces to a `CALC-*`/`KPI-*` ID; the 14 golden
fixtures pass; the drill from any dashboard figure reaches the transactions that compose it; the UI is
responsive during long queries (`NFR-016`); a stale indicator appears when mappings/thresholds change.

**Demo outline:** Home dashboard → click a material adverse variance → bridge → drill to transaction detail →
show the transaction's source batch and audit row → run a search → show the forecast placeholder state.
*(6 steps.)*

**Risks:** query performance on 250k rows (mitigate: server-side aggregation in DuckDB, virtualised grids
— `09` §12, `14` §12.2); "% vs pp" confusion (mitigate: one formula owner, `05` §4/§6, and the display contract in
`08` §15).

**Estimate:** **14 ideal days.**

### 6.3 Phase 3 — Exception engine & register (`GATE-09`)

**Goal:** surface what needs attention with owners, SLAs, aging and evidence — and prove the engine's
precision on planted data.

| Deliverable | Detail | Owner doc |
|---|---|---|
| Rule engine | Identity/re-run semantics, effective thresholds, strictness tiers, degradation, dependencies | `06` §2 |
| 24 rules (`EXC-001`…`024`) | Each with logic, threshold, severity, owner, false-positive mitigation | `06` §4 |
| Register & workflow | Bulk actions, statuses, comments, owner auto-assign, aging/SLAs, evidence links | `06`, `08` §10 |
| Effectiveness analytics | Precision/recall feedback, tuning log | `06` §9 |
| Cross-batch duplicates + tie-outs | The v1 file-level control-total rule family | `06` |
| Alert surfacing | Home counts, badges, non-colour signals (`P19`) | `08` §5, §10 |

**Definition of Done:** the acceptance harness passes its bars on the planted corpus (recall ≥ 90 %,
**zero control raises**, 18/18 High); `TST-RUL-01…24` all exist and map one-to-one to `EXC-001…024`; rule
re-runs are identity-stable (worked scenario in `06`); every rule's message obeys `08` §16 wording rules.

**Demo outline:** Home exception counts → register filtered to High/aging → open one exception with its
evidence and owner → bulk-assign/comment → show the rule that raised it and its threshold → effectiveness
view. *(6 steps.)*

**Risks:** false positives erode trust (mitigate: the 8 precision controls are part of acceptance, not
optional); slow rule runs at volume (mitigate: `NFR-007` ≤ 60 s, measured each gate).

**Estimate:** **18 ideal days.**

### 6.4 Phase 4 — Forecast (`GATE-10`)

**Goal:** a rolling forecast with four transparent methods, scenarios, versioning and accuracy feedback.

| Deliverable | Detail | Owner doc |
|---|---|---|
| Four methods | Run-rate, prior-year, budget, driver-based — each with eligibility guards | `07` §4, `05` §9 |
| Method resolver | Explainable choice, override with reason, guidance copy | `07` §5 |
| Scenarios & versions | Draft → reviewed → locked; accuracy report per version | `07` §6–§8 |
| Accuracy feedback | Closed-period accuracy feeding method-choice guidance | `07` §8 |
| Forecast UI | Forecast screen, scenario compare, override flow, `CHT-*` charts | `08` §10 |

**Definition of Done:** every method's arithmetic reproduces the `05` fixtures; eligibility guards refuse
ineligible combinations with the documented message; a locked version is immutable; accuracy metrics
recompute from closed periods only; scenario compare is available at the same grain as BvA.

**Demo outline:** open forecast → show method choice and why → switch scenario → override one driver with a
reason → lock the version → show the accuracy report from a closed period. *(6 steps.)*

**Risks:** forecast credibility (mitigate: transparency of method and inputs; AI never computes or
overrides — `10`); state divergence between scenario and base (mitigate: one resolver, tested).

**Estimate:** **10 ideal days.**

### 6.5 Phase 5 — Excel & PowerPoint packs (`GATE-11`)

**Goal:** one-click, editable, client-ready month-end packs that tie out to the screen and to each other.

| Deliverable | Detail | Owner doc |
|---|---|---|
| Excel pack | 8 sheet contracts, zero formulas, the 30-field stamp, 15 number formats, watermarking, lossless split at the row cap | `11` |
| Evidence bundle | Workbook + zip with hashed manifest | `11` §6 |
| Export-what-you-see + CSV | With the sidecar stamp | `11` §7 |
| Deck | Six slides (`PPT-001`…`006`), native charts, editable placeholders, char budgets, base-deck mode | `12` |
| Owner distribution | The plain-text distribution note and per-owner splits | `11` §8 |
| House-style matching | Matchable vs refused inputs, profile JSON | `11` §9, `12` §6 |
| Commentary and issuance | Draft → edit → lock on issuance; the pack issuance register | `FR-XC-001`…`003`, `08` §11 |

**Definition of Done:** `NFR-009` met on the 250k fixture (≤ 120 s) and `NFR-004` for the deck (≤ 15 s);
a zero-formula audit passes on every sheet; opening every artefact in Office produces no repair prompt
(`TST-WIN-10`); the **cross-artifact equality test** passes (engine = UI = Excel = deck = CSV); sample
projects carry the watermark into every artefact (`FR-XC-013`).

**Demo outline:** generate the pack from the sample project → open the workbook and show a drill row →
show the stamp and the no-formula state → generate the deck and show an editable placeholder → show the
cross-artifact ties (one number followed across all three surfaces). *(5 steps.)*

**Risks:** client's existing format differs (contract: refusal beats mangling); large-pack performance
(mitigate: streaming writes, measured against the baseline); Office quirks in the opened artefacts
(the `TST-WIN-10` run is part of the gate, not post-release QA).

**Estimate:** **16 ideal days.**

### 6.6 Phase 6 — AI & polish (`GATE-12`)

**Goal:** optional AI assistance that never computes, decides, applies or sends — plus the accessibility,
performance and hardening work that makes the product feel finished.

| Deliverable | Detail | Owner doc |
|---|---|---|
| AI features | Variance commentary, mapping suggestions, exception summaries — strict JSON, one retry, rule-based fallback | `10` |
| Key & provider flow | Keyless default, DPAPI storage, redaction preview, caps, usage log | `10`, `13` §5 |
| Mapping review queue | Confidence-ranked suggestions with a human decision | `10` §13 |
| Accessibility & wording | WCAG AA, contrast, non-colour signals, the message-catalog audit | `08` §16, §18–§19; `TST-SEC-19` |
| Performance & hardening | Final NFR sweep, crash recovery, log rotation, fault injection, storage math | `09` §14, `14` §8, §11–§13 |
| Documentation set | `22` completed screen-by-screen, `23` handover, `24` checklist rehearsed | `22`–`24` |

**Definition of Done:** with AI off (default) every feature works end to end offline; with AI on, every
output is schema-validated, labelled as a draft, and never authoritative; the key is never displayed or
logged (`SEC-010`); all accessibility checks pass; every NFR in `09` §14 is green with evidence; no known
S1/S2 defect is open.

**Demo outline:** show AI off and the full flow still working → enable AI with a key → produce a commentary
draft → show the provenance label and the number-mismatch strip → disable AI and show the rule-based
fallback. *(5 steps.)*

**Risks:** AI output quality/variability (mitigate: strict schema + fallback + human review; no number is
ever produced by AI); scope creep in "polish" (mitigate: `27` backlog with triggers; polish items are
ranked, not accumulated).

**Estimate:** **14 ideal days.**

## 7. Estimates, re-estimation and variance

### 7.1 Method and assumptions

| Aspect | Rule |
|---|---|
| Unit | **Ideal developer-days** for one senior engineer with AI assistance — no meetings, no waiting, no context loss |
| What is included | Spec reading, code, tests, the phase's docs updates, the demo script, the gate run |
| What is excluded | Calendar waits (client data, questionnaire answers, branding assets, UAT scheduling), procurement (signing certificate), and the phases' contingency |
| Sizing anchors | Phase 1's import pipeline (the largest, most detail-heavy phase) = 24 ideal days; a single exception rule with its tests ≈ 0.5 day (24 rules ≈ 12 days) |
| Confidence | ± 30 % at this level of specification; the range narrows at each gate as the fixtures mature |
| Re-estimation | At **every** gate, before the approval line is recorded: actual vs estimate, and the new estimate for the remaining phases |
| Variance rule | **> 50 % variance on a phase is reported immediately** (Addon 4 §D.5) with cause and options — not discovered at the gate |
| No silent slippage | A slipped phase is named in `SESSION_LOG`; a slipped gate is named in `CHANGELOG` |

### 7.2 Per-phase estimates and per-P0-epic detail

| Phase | Ideal days | P0 epics inside the phase | Epic estimate |
|---|---|---|---|
| Packaging spike | **1** (two half-days) | Build path; install/SmartScreen path | 0.5 + 0.5 |
| 1 — Import & validation | **24** | E1.1 Import pipeline, wizard, mapping profiles | 10 |
| | | E1.2 Validation catalogue (`IMP-001`…`032`) + reports + reconciliation | 7 |
| | | E1.3 Project/period/storage + onboarding + backup/restore | 7 |
| 2 — BvA & drill-down | **14** | E2.1 BvA engine + KPI library + rollups | 8 |
| | | E2.2 Drill-to-transaction + search + dashboard states | 6 |
| 3 — Exception engine | **18** | E3.1 Rule engine + 24 rules + re-run identity | 10 |
| | | E3.2 Register, workflow, aging/SLAs, effectiveness | 8 |
| 4 — Forecast | **10** | E4.1 Methods + resolver + scenarios + accuracy | 10 |
| 5 — Packs | **16** | E5.1 Excel pack + evidence bundle + CSV | 8 |
| | | E5.2 Deck + house style + cross-artifact ties | 8 |
| 6 — AI & polish | **14** | E6.1 AI features + key/provider + review queue | 6 |
| | | E6.2 Accessibility, wording, performance, hardening, docs | 8 |
| **Build total (Phases 1–6)** | **96** | 12 P0 epics | 96 |
| Real-data pilot | **2** | Tie-out worksheet, classification log | — |
| UAT support | **3** | Defect turnaround, fixes, re-test (`28`) | — |
| Go-live | **1** | Install, train, handover, watch | — |

**Phase 0 remainder (context, owned by §3):** the remaining documents + the `sample-data/` build step +
the two audit passes ≈ **10–14 ideal days** of documentation and fixture work, already in progress.

### 7.3 What the numbers mean and do not mean

1. They are **planning aids**, not commitments: the elapsed project will be longer because the client is
   a partner with a day job (questionnaire answers, file access, UAT scheduling).
2. They are **per phase**, and a phase gate is not partial — an estimate that assumes slicing a phase is
   an estimate that assumes the gate will fail.
3. They **exclude** the never-cut list's extra cost: if a never-cut property is at risk, the phase grows
   rather than the property shrinking.
4. They are **reported, not defended**: the number that matters at a gate is the variance, its cause, and
   the corrected plan.

## 8. Release cadence

### 8.1 When a build exists

| Moment | What exists | Who sees it |
|---|---|---|
| Packaging spike | A hello-world installer | The project owner |
| Each build gate | An internal, installable build of the phase's scope (a release candidate when the gate is green) | The project owner; the client at the phase demo |
| Pilot | The first build run on a sanitized real month | The project owner + the client's analyst |
| UAT | The UAT build (feature-complete for v1) | The client's UAT participants |
| Go-live | The released installer + checksums | The client |

### 8.2 Cadence rules

| Rule | Detail |
|---|---|
| Gate-based, not calendar-based | Builds become client-visible **at gates**; there is no release train between gates |
| One release candidate per gate | Tagged per `24` (semver, tags, notes); the previous installer stays available for rollback (`15` §7.3, `28`) |
| Patch releases | Only for a **P0 defect** in a released build; they re-run the affected phase's gate checklist items, not the whole phase |
| No feature releases mid-phase | A half-phase build is a demo, not a release; it is never distributed to the client as a version |
| Hotfix content | The smallest change that removes the P0 defect + its test; no drive-by improvements |
| Version bumps | `MAJOR` on a breaking data/format change, `MINOR` at a gate with new scope, `PATCH` for fixes (`24` owns the mechanics) |
| Docs version | Bumped at gates alongside the app version; the Phase-0 set stays `0.1.0` until approved |
| Distribution | Secure channel + published SHA-256 (`15` §8/§10); never "here is an exe" |

### 8.3 Freeze windows

| Window | Freeze |
|---|---|
| Gate run | Only test fixes; the checklist runs on the frozen commit |
| Pilot week | No feature work; only defects found by the pilot (classified per `28`) |
| UAT period | Only UAT defects; every fix re-runs its test + the affected gate item |
| Go-live week | Only go-live blockers; nothing else ships |

## 9. Cut-line policy at phase level

`02` §3 owns the definitions and the per-FR text; this section is the phase-gate application of it.

### 9.1 The rule at a gate

1. **All P0 FRs of the phase are green** — no exceptions, no partial credits (`02` §3.2).
2. **P1 gaps** are listed explicitly with a finish-or-defer decision recorded in the gate checklist and
   `SESSION_LOG`; a deferral gets a `27` entry with a trigger.
3. **P2 gaps** are deferred by default if the phase is at risk; the same recording rules apply.
4. A phase that cannot close its P0 work **fails the gate** and the next open item becomes the gap list.

### 9.2 The never-cut list (verbatim from `02` §3.3 — never deferred, descoped or "simplified")

Exact money maths (Decimal/minor units) · atomic all-or-nothing imports · versioned audit of edits ·
offline/local-only data behaviour · the Windows installer and real-Windows validation · the advisory
disclaimer · backup/restore · golden tests · the cross-artifact consistency test.

**Why these nine:** each one is either the reason the client trusts the product (money, audit, disclaimer),
the reason it survives a bad day (atomicity, backup, offline), or the reason we know it still works
(golden tests, cross-artifact test, real-Windows validation). Every other line can be cut with approval;
these cannot.

### 9.3 Cut process (outside the never-cut list)

1. A written proposal: what is cut, the impact on FRs/docs/tests, and the size (`S`/`M`/`L`).
2. The project owner's explicit approval (Addon 4 §D.4).
3. A `27_BACKLOG.md` entry with a trigger condition (what makes it come back).
4. The `CHANGELOG` and the gate checklist record the decision.

**Silent under-delivery is a protocol violation — and so is building P2 work while P0 work is open**
(`02` §3.4).

## 10. Client-visible checkpoints

Nothing here is a release; these are the moments the client sees progress without preparation.

| After | The client sees | How |
|---|---|---|
| Packaging spike | A real installer, on a real Windows 11 machine | A 5-minute live run or a recording |
| Phase 1 gate | Their file shape importing, validating and reconciling on sample data | The demo script (§11) |
| Phase 2 gate | A variance explained from headline to transaction | Demo |
| Phase 3 gate | Their exceptions surfaced with owners and SLAs | Demo |
| Phase 4 gate | A forecast with its method visible and an accuracy report | Demo |
| Phase 5 gate | The Excel pack and the deck, opened live in Office | Demo |
| Phase 6 gate | The AI draft with provenance and the offline guarantee | Demo |
| Pilot | Their own sanitized month | Joint session |
| UAT | The product, in their hands | `28` |

**Rule:** the client's view is only ever the *installed* product (or a recorded run of it). A developer
session, a terminal, or a dev build is never a checkpoint.

## 11. Demo scripts and the walkthrough

### 11.1 The demo-script rule (Addon 3 §K.4)

Every phase ends with a **3–5 minute scripted run on sample data**: numbered steps, the expected result
per step, and no live improvisation. The script is written at the **start** of the phase (so the phase is
built to be demonstrable), rehearsed before the gate, and recorded in `SESSION_LOG` with the gate.

### 11.2 The two walkthroughs that close Phase 0 (Addon 1 §P20, Addon 4 §L.10)

| Walkthrough | What it is | Pass condition |
|---|---|---|
| Tabletop month-end | The team walks the whole month end on paper/screen: import → validate → BvA → exceptions → forecast → packs → issuance, naming every screen and every failure it would hit | Every step has a screen, an FR and a test; every gap found becomes a doc fix before the gate |
| Cold-start client | A person with no context, on a fresh machine, with the sample project only: install → first run → tour → one task per phase area | They complete the guided path without asking for help; questions they asked become doc/help fixes |

Both walks are **Phase-0 evidence** and both must be repeated at the pilot with real data (`28`).

### 11.3 What each demo must never do

- Never use real client data (the pilot is the only real-data moment, and it is governed by `28`).
- Never show a feature that is not behind a passing test.
- Never rely on the Internet (the offline guarantee is part of the story, `NFR-008`).
- Never skip the failure path: at least one step shows a named error and its recovery.

## 12. Roadmap risks and contingencies

| # | Risk | Trigger | Contingency | Owner |
|---|---|---|---|---|
| 1 | Client data/shape availability slips | Phase 1 start | Sample data is already the testbed; the pilot shape is added as a mapping profile without code change | project owner |
| 2 | SmartScreen/Defender blocks the installer | Spike or first client install | The mitigation ladder (`15` §8.2): package to the rules; signing certificate decision at go-live | project owner |
| 3 | Import performance misses `NFR-002` | First baseline run | Profile the pipeline (lazy frames, partitioning, column pruning) before touching correctness | engineering |
| 4 | Rule precision disappoints (false positives) | Acceptance harness | Tune thresholds **in `06` first** (spec → config defaults → tests); never hide a rule to pass | engineering |
| 5 | AI output quality or latency varies | Phase 6 | Strict schema + one retry + rule-based fallback; AI never computes numbers | engineering |
| 6 | Scope pressure at a gate | Any gate | The cut-line policy (§9) with the never-cut list; the backlog records what returns | project owner |
| 7 | Coverage or perf regression | Any gate | The blocking rules in `14` §8.3/§13.2; a waiver requires explicit approval | engineering |
| 8 | A doc contradiction is found late | Any session | Fix the owning doc + `CHANGELOG` in the same pass; the conflict rule is in `00_INDEX` §6 | doc owner |
| 9 | Key-person dependency | Any phase | The handover doc (`23`) is written from Phase 1 onward, not at the end; demo scripts double as knowledge transfer | project owner |
| 10 | UAT participants unavailable | Pre-UAT | The UAT plan (`28`) lists participants and a fallback week; the scripts (`TST-UAT-*`) are runnable by one person | project owner |

> These ten rows are operationalised as risk rows in `25_RISK_REGISTER.md` §2 (row order → rows 1–10 →
> `RISK-002`, `RISK-003`, `RISK-006`, `RISK-004`, `RISK-010`, `RISK-007`, `RISK-013`, `RISK-014`, `RISK-011`,
> `RISK-012`); this table keeps the roadmap contingency view and `25` is the operational detail.

## 13. Open items, deferrals and assumptions

| Item | Status |
|---|---|
| Dates and calendar targets | **Deliberately not set here** — this document commits to *order and gates*, not dates (the estimates in §7.1 are ideal days) |
| Signing-certificate decision | Client decision at go-live planning (`ADR-003` step 5, `Q-015`/`OQ-012`) |
| AI model/provider specifics | Keyless default; the provider is configured per client (`10`, `Q-*` in `21`) |
| Per-machine installer, MSIX, auto-update | Parked (`27`, Addon 1 §N) |
| Backlog items returning at a trigger | `27` owns the register; §9.3 is the only way back in |
| Coverage-matrix rows still `IN PROGRESS` | Closed by `18`–`29` in Phase 0 (§3) |

**Assumptions.** (a) One senior engineer builds the product with AI assistance; (b) the client's analyst is
available for the pilot and UAT as planned; (c) the reference machine is available for baselines; (d) the
Windows validation protocol (`15` §5) is runnable at every gate; (e) no security or compliance requirement
outside `13` emerges. Any of these failing changes the plan, not the standards.

## 14. Change control and cross-document obligations

### 14.1 Obligations this document places elsewhere

| Obligation | Owner |
|---|---|
| Gate checklists `GATE-01`…`GATE-05` unchanged in substance; gate texts single-sourced there | `14` §15, `00_INDEX` §9 |
| Every build gate's Windows evidence uses the `15` §5 protocol; `15` §5.3 maps the `TST-WIN-*` suite | `15` |
| The build steps, artefact names and version stamping that the spike exercises | `15` §2–§4, `09` §15.4 |
| `scripts/check` composition, coverage bars and CI rules implemented exactly | `17`, `14` §13 |
| The `20` traceability chain is the source of the gate's FR evidence (item 7, §5.1) | `20` |
| `27` receives every deferral with a trigger; `18` receives every decision | `27`, `18` |
| Release tagging, notes and publication mechanics for §8 | `24` |
| `GATE-13`…`GATE-15` mechanics, the pilot, UAT and go-live | `28` |
| Demo scripts recorded per phase; DoD enforcement and approval recording | `19` |
| The next open item stays in step with `00_INDEX` §10 and `SESSION_LOG` | `00`, `SESSION_LOG` |

### 14.2 Changes to this document

| Change | Requires |
|---|---|
| A phase's scope, order or gate ID | The project owner's approval; `02`/`20` updated in the same pass; `CHANGELOG` entry |
| An estimate change | A gate re-estimation, or an immediate variance report (> 50 %); recorded in `CHANGELOG` |
| A new gate | A number allocated here, `00_INDEX` §8/§9 updated, the check owner named |
| The next open item | Changed only with the work that closes the previous item, in the same commit |
| The universal gate contract (§5.1) | A `14` §17.2 change or an explicit owner decision; the six Phase-0 checklist texts stay authoritative in `14` |
| A cadence change | Recorded here first, then reflected in `24` (mechanics) and `19` (session protocol) |

**Frozen constants owned by this document:** the phase list and their gate IDs (§2.1) · the scope→phase
mapping and priority split (§2.2) · the Phase-0 completion steps (§3.2) · the packaging spike's contract
(§4) · the 14-item universal gate contract (§5.1) and the evidence pack (§5.2) · the estimates and the
variance rule (§7) · the cadence rules and freeze windows (§8) · the never-cut list application and cut
process (§9) · the demo-script rule (§11.1) · the two Phase-0 walkthroughs (§11.2).



> **Status:** Draft v0.2 — **ready for owner presentation; not approved**
> **Last updated:** 2026-10-02
> **Owning FRs/areas:** the one-page Phase 0 close-out summary (Kickoff §5; Addon 1 §P.7, Addon 2 §H.4,
> Addon 3 §K.10, Addon 4 §L.11 and Addon 5 §N): product, documentation locks, key decisions, risks,
> open questions, gate evidence and the exact meaning of approval. Approval is recorded in `CHANGELOG.md`
> and `SESSION_LOG.md` (Addon 4 §E.2).
> **TL;DR (≤ 15 lines):**
> - **Phase 0 specification:** 31 numbered documents (`00`–`30`) define architecture, rules, UX and QA; no product code exists.
> - **Official contract:** Addon 5 is anchored locally at `project prompt/ADDON_5_OWNER_CONTROL_EVIDENCE_DATA_EGRESS_EXTENSION.md` (SHA-256 `cfbb69411d586194d2ad8ef6034a74e19bcb0ae976b466485adda75a97372b11`).
> - **Documentary gates:** the six-source re-audit passed **70/70** rows (9+12+12+12+13+12); report, link check, synthetic regeneration, oracle validation and tabletops are in `evidence/2026-10-02-phase0-re-audit/`.
> - **Scope boundary:** this is evidence that the Phase 0 documentation is ready to present, not an installer/build/pilot/UAT/go-live claim.
> - **Data boundary:** development and evidence use synthetic data only; real pilot work is isolated locally and never enters this repo, agent or cloud service.
> - **Decision still required:** the owner must approve or reject the presented set in writing. Until then packaging and product code are prohibited.

# PHASE 0 SUMMARY — for approval

## 1. The product, in one paragraph

**FP&A Month-End Copilot** is an offline Windows desktop application for a finance team's month-end
review. The analyst drops in three files — a D365-style general-ledger export and two other system
exports, all messy, all real — and the app validates them, refuses anything it cannot trust, and turns the
month into a budget-vs-actual view with drill-through to the transaction and the source row. It then
applies a catalogue of **24 written exception rules** (the kind a reviewer looks for by hand), tracks each
finding through owner, status and age, refreshes a rolling forecast with the method and the reasons
recorded, and generates the month's **Excel pack and PowerPoint deck** from the same numbers — in the
client's house style, with a version and a recipient list. Everything runs on one machine, offline, in
`%LOCALAPPDATA%`; nothing is uploaded, no server is involved, and no accounting record is ever touched. AI
is **optional and off by default**: when enabled it writes **draft** commentary from figures the engine has
already calculated, and a person approves every word. Money is calculated exactly (Decimal, no floating
point), imports are atomic (all or nothing), packs are versioned and immutable once issued, and every
screen, workbook and slide reads the same engine output.

## 2. What Phase 0 produced

| Group | Documents | What it locks |
|---|---|---|
| Core specification | `00`–`20` | Scope and personas; 156 FRs with priorities and acceptance criteria; data model; import rules and 32 validation checks; calculation formulas and tolerances; exception rules; forecast methods; screens, charts and wording; architecture and ADRs; AI policy and prompts; Excel and PowerPoint contracts; security; tests and quality bars; packaging; roadmap and gates; coding standards; decisions and open questions; process rules; traceability |
| Onboarding & handover | `21`–`25` | The 21-question client questionnaire with defaults; the end-user guide (43 screens, 21 tasks); consultant handover and support; the release runbook; the risk register (36 risks) |
| Interface & governance | `26`–`27` | The frozen API contract (95 routes, envelope, error catalogue, contract tests); the backlog register (35 items with promotion triggers) |
| Acceptance | `28` | The project DoD, `S1`–`S4` defect workflow, isolated-local real-data pilot, UAT with six scripts, the **23-item** go-live checklist and sign-off template |
| Client-facing | `29` | The plain-language requirements pack with the 17 decisions and the sign-off block |
| Owner control & verification | `30` | Owner operating handbook: cadence, session-report standard, evidence/review, red flags, sampling, stuck escalation and independent oracle |
| Memory & control | `CHANGELOG`, `SESSION_LOG`, this file | Every change with its reason; the session bridge; the approval record |

**Frozen by this set** (cite the owning doc, never a copy): 156 FRs in 11 families (P0 110 · P1 39 · P2 7) ·
43 screens · 12 charts · 24 exception rules · 8 Excel sheets · 6 slides · 3 source-system shapes (D365-style + two others) ·
32 import checks · 59 import messages · 95 API routes · 11 error families · 35 backlog items · 36 risks ·
20 live open questions with labelled/proposed defaults · 10 ADRs · 40 decisions · 292 test slots in 16 families (206 owned by the doc set, 86 reserved for later phases) ·
9 never-cut items.

## 3. Key decisions (each with its reasoning in the owning doc)

| # | Decision | Where | Why it matters |
|---|---|---|---|
| 1 | **Stack**: Python 3.12 + FastAPI + DuckDB + Polars + openpyxl + python-pptx; React + TypeScript + Vite; pywebview; PyInstaller + Inno Setup | `09` `ADR-001` | Headless, testable engine first; no exotic runtime on the client's machine |
| 2 | **Engine boundary**: all money/business logic in a headless engine; API/UI/CLI are thin shells, enforced by import-linter | `09` `ADR-002` | The numbers can be tested without the UI; the UI cannot invent a figure |
| 3 | **Ship unsigned in v1** with a documented SmartScreen ladder (hash + walkthrough + submission), certificate optional later | `09` `ADR-003` | Installs today without a purchase; the risk is mitigated in writing, not hidden |
| 4 | **Storage** in `%LOCALAPPDATA%`, never a synced folder | `09` `ADR-004` | OneDrive/SharePoint corrupts live databases; snapshots are the supported pattern |
| 5 | **Installer** per-user, no admin, onedir payload + portable zip fallback | `09` `ADR-005` | A finance laptop with no IT involvement can still install it |
| 6 | **One writer, one worker thread**; long jobs are queued, cancellable, resumable | `09` `ADR-006` | No race conditions on the client's data; progress is honest |
| 7 | **Hand-written SQL**, no ORM; DuckDB for analysis, SQLite for workflow state | `09` `ADR-007` | Performance and predictability at 250k rows |
| 8 | **Forward-only migrations with a mandatory pre-migration backup** | `09` `ADR-008` | Upgrade safety; rollback is a restore, never a reverse migration |
| 9 | **Loopback API** with a random port and a per-launch token; the UI is served as static assets by the same process | `09` `ADR-009` | No port is assumed, no local service is left open, no CORS surface |
| 10 | **Any OpenAI-compatible HTTP endpoint**, no vendor SDK; key protected by DPAPI, never backed up or logged | `09`/`13` `ADR-010` | The client owns the AI contract; turning AI off leaves nothing broken |
| 11 | **Money is exact**: Decimal only, no epsilon, quantise at the documented boundary, one rounding policy | `05` §1 and §13 | The class of bug that destroys trust in a finance tool is designed out |
| 12 | **Materiality**: `max(₹5,00,000, 2 % × \|budget\|)` as the default threshold, client-editable | `05` §11 | Rules start where a finance team's attention starts, and they can change it |
| 13 | **Cross-artifact equality**: app = Excel = deck = CSV, zero tolerance, tested | `14` §7, `NFR-015` | "The slide says something else" is the fastest way to lose a client |
| 14 | **Quality bars**: engine coverage ≥ 90 %, app ≥ 75 %; recall ≥ 90 % of 32 planted exceptions with zero control raises | `14` §13.2, §5 | Quality is measured, not asserted |
| 15 | **Performance envelope**: 10 s cold start · 250k rows/100 MB ≤ 60 s · ≤ 2 s UI · pack ≤ 120 s · NFR-006: Installer ≤ 500 MB; NFR-005: Peak memory ≤ 1.5 GB | `14` §8, `NFR-001`…`016` | The tool must be usable on the client's actual machine |
| 16 | **Nine never-cut items** (exact money, atomic imports, audit versioning, local-only, installer + real-Windows validation, disclaimer, backup/restore, golden tests, cross-artifact equality) | `02` §3.3 | Scope can move; these cannot |
| 17 | **Docs-first, quote-before-code**: no code before recorded approval; every change updates its owning doc first | `19` §2 | The reason this phase exists |
| 18 | **Deferrals live in one place** with a trigger that would promote them | `27` §4 | A "later" without a trigger is a lost requirement |
| 19 | **Sample data is never delivered to the client**, and never mixed with real data | `13`/`14` §16 | Contamination safety; go-live checks it explicitly |
| 20 | **No activation, expiry, licence key or usage-control mechanism in v1**; any future control needs explicit owner-approved PRD scope and `BL-037` | `01` §16, `18` `DEC-040`, `27` `BL-037` | Protects the offline/perpetual v1 boundary from commercial-scope drift |

## 4. Top risks (full register: `25`; scores are impact × likelihood, 1–5)

| Risk | Why it would hurt | Mitigation in force |
|---|---|---|
| **Messy real files break the importer** (`RISK-001`, 20) | Nothing else matters if month one does not load | 32 validation checks, quarantine rather than silent repair, mapping profiles, a malformed-file corpus, and the pilot month before go-live |
| **The isolated-local sanitized real month is not scheduled** (`RISK-002`, 20) | The pilot, UAT and trust all depend on it (`OQ-014`) | Named as a schedule dependency; a fallback (UAT on sample data with a written limitation) and a metadata-only early ask in `29` §7 — never an upload request |
| **Unsigned installer blocked** (`RISK-003`, 20) | The client cannot install | SmartScreen ladder, hash verification, portable-zip fallback, and a certificate decision (`OQ-012`) |
| **Rule precision disappoints** (`RISK-004`, 20) | Too many false positives and the register is ignored | Recall ≥ 90 % with zero control raises, effective-threshold traceability, suppression, effectiveness analytics |
| **App numbers differ from the client's manual pack** (`RISK-005`, 16) | Trust collapses at the first tie-out | Tie-out worksheet, four-class difference taxonomy, drill-through to the source row, frozen mapping profiles |
| **Real volumes exceed the envelope** (`RISK-006`, 16) | The tool becomes unusable in month two | local regenerated 250k-row performance work with recorded baselines and a > 20 % regression gate |
| **Scope pressure pushes P1/P2 into P0 time** (`RISK-007`, 16) | A gate slips or quality drops | The cut-line process, the never-cut list, and every deferral with a trigger (`27`) |
| **Windows-only evidence gap** (`RISK-008`, 12) | It works on the dev machine and fails on the client's | Real-Windows checks at every gate, with screenshots and run sheets |

## 5. Open questions and the answers that matter most

| Question / control | Owner | Current position | When it is needed |
|---|---|---|---|
| **`OQ-014`** — when can one sanitized real month be made available locally? | Client | **None — no default.** The pilot cannot run without it; it is a schedule dependency, not a reason to use real data in development or transmit it through a cloud/repository channel. | Before the isolated local pilot (`GATE-13`) |
| **`OQ-016`** — support/warranty terms after go-live | Project owner | Consultant-first support is only a planning default; owner-approved client response targets are required before go-live. | Before go-live |
| **`OQ-017`** — approved installer delivery channel | Project owner | Secure link + published SHA-256 is a labelled default. | Before the pilot/delivery |
| **`OQ-023`** — final default-sweep deadline `N` | Project owner | Addon 5 leaves `N` unspecified. **10 business days is proposed only**; the owner must decide the number and business/calendar-day basis. | Before scheduling the final go-live sweep |
| **`OQ-012`** — code-signing certificate budget | Project owner | Not purchased; the documented SmartScreen mitigation ladder applies. | Before packaging-spike install validation |
| Other questions | Client / owner | 15 further live questions (`OQ-001`…`017`, `OQ-021`/`022`, excluding reserved/retired IDs) have labelled defaults; defaults never become client facts silently. | At their named phase/gate |
| **Synthetic sample-data control** | Engineering | Generator/instructions are versioned; outputs are ignored and regenerated locally. The dated regeneration evidence confirms 40 finance plantings plus `INJ-01`, three templates and 16 malformed cases. | Whenever a test/demo needs synthetic data |

## 6. Gate snapshot

| Gate | Checks | Pass | Fail | Current status |
|---|---:|---:|---:|---|
| `GATE-01` Kickoff | 9 | 9 | 0 | PASS — documentary re-audit |
| `GATE-02` Addon 1 §O | 12 | 12 | 0 | PASS — documentary re-audit |
| `GATE-03` Addon 2 §I | 12 | 12 | 0 | PASS — documentary re-audit |
| `GATE-04` Addon 3 §J | 12 | 12 | 0 | PASS — documentary re-audit |
| `GATE-05` Addon 4 §K | 13 | 13 | 0 | PASS — documentary re-audit |
| `GATE-05B` official Addon 5 §M | 12 | 12 | 0 | PASS — documentary re-audit |
| **Total** | **70** | **70** | **0** | **Phase 0 documents ready to present — owner approval pending** |

**Evidence:** `evidence/2026-10-02-phase0-re-audit/phase0_reaudit_report.md` (70 rows),
`command.txt` (exit 0/link check/client-egress-copy safeguard), `tabletop_walkthroughs.md`, `sample_data_regeneration.md` and
`oracle_workbook_validation.md`. The audit verifies the written Phase 0 specification and safe fixtures.
It does **not** claim an executable product, installer, Windows validation, client pilot, UAT or go-live.

## 7. What approval means

1. **It is recorded, dated and scoped** — `Phase 0 APPROVED — <who> — <date>` in `CHANGELOG.md` and
   `SESSION_LOG.md` (Addon 4 §E.2). It applies to the state presented here.
2. **It releases the packaging spike first** (two half-days: hello-world → PyInstaller → Inno Setup →
   installed launch on real Windows 11 through the SmartScreen path). If that path cannot be made to work,
   the project stops and escalates rather than building features on an unproven installer.
3. **It permits Phase 1 only after the spike outcome is recorded.** Later phases remain individually gated
   (`16`); import & validation does not grant permission to skip directly to forecasting, packs or AI.
4. **It does not freeze the spec forever.** Any material change afterwards gets an **impact note** first
   (affected FRs, docs, tests, size S/M/L), and the gate is re-opened rather than edited quietly.
5. **No product code exists yet.** The repository contains documentation, the skeleton and `.gitkeep`
   files; nothing has been built, installed or shipped.

## 8. What happens next

| When | What |
|---|---|
| On approval | Record the approval in both process logs; then start only the packaging spike. The synthetic generator is available for local regeneration — its outputs are not a delivered corpus. |
| Packaging spike | `GATE-06`: hello-world → build → installer → clean Windows 11 launch/SmartScreen evidence; correct `15` if reality differs. |
| After a recorded spike outcome | Begin Phase 1 (import & validation) only if the spike exit criteria are met; run the mapping walkthrough with synthetic files. |
| Before UAT | The isolated local pilot month (`GATE-13`) with tie-out, local oracle metadata and signed classification log. |
| Before go-live | UAT (`GATE-14`, ≤ 5 business days, six scripts), training (`22` §10), then the **23-item** go-live checklist (`GATE-15`), including owner-approved `OQ-023` deadline. |
| After go-live | Two month-ends of hypercare, first accuracy review, and support/issue → release or request → `27` backlog loop before any enhancement code. |

## 9. The approval ask

Reply with the line below (add any condition you want recorded):

```
Phase 0 APPROVED — <your name> — <date>
Conditions / notes: <optional>
```

Or reply with the section numbers you want changed; each one is fixed, re-audited and re-presented before
approval. **No product code will be written until this line is recorded.**

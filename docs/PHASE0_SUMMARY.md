> **Status:** Draft v0.1 (the approval artefact)
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** the one-page Phase 0 close-out summary (Kickoff §5; Addon 1 §P.7, Addon 2 §H.4,
> Addon 3 §K.10, Addon 4 §L.11): the product, what the documentation set locks, the key decisions, the top
> risks, the open questions, the gate snapshot and what approval means. Approval is recorded in
> `CHANGELOG.md` and `SESSION_LOG.md` (Addon 4 §E.2).
> **TL;DR (≤ 15 lines):**
> - **Phase 0 is complete on paper**: 30 documents (`00`–`29`) + `CHANGELOG` + `SESSION_LOG`, written
>   docs-first, with no product code.
> - **The product**: an offline Windows month-end copilot that turns three messy exports into a
>   budget-vs-actual review with drill-through, a triaged exception register, a rolling forecast and an
>   Excel + PowerPoint pack — on one machine, with money handled exactly.
> - **The spec is closed and consistent**: 156 requirements, 43 screens, 24 exception rules, 95 API routes,
>   11 error families, 34 backlog items, 36 risks, 292 test slots — each fact with one owning document.
> - **Decisions are recorded, not remembered**: 10 architecture decisions and 37 product decisions live in
>   `09`/`18`, with the reasoning and the alternatives.
> - **Nothing is deferred silently**: every cut is a `27` backlog item with the trigger that would bring it
>   back; the nine never-cut items are enforced at every gate.
> - **The acceptance path exists end to end**: project DoD, `S1`–`S4` defect workflow, the real-data pilot
>   (`GATE-13`), UAT (`GATE-14`) and the 22-item go-live checklist (`GATE-15`).
> - **The client-facing pack is ready to send** (`29`): plain language, decisions with recommendations, and
>   the sign-off block.
> - **The link-check is clean**: every cross-reference resolves, every table is well-formed, every ID
>   matches a registered namespace.
> - **Gate snapshot: 55 of 58 checks green.** The three open ones are named below and none blocks approval.
> - **One deliberate scope deferral**: the `sample-data/` fixture build (generator, `.xlsx` templates,
>   40 plantings, malformed corpus, 250k-row mode) — a build step, not documentation; needs your go-ahead.
> - **Two answers would remove the last placeholders**: the support/warranty terms (`OQ-016`) and the
>   delivery channel (`OQ-017`); the pilot month (`OQ-014`) is the project's main schedule dependency.
> - **Nothing here is a financial opinion**: the advisory disclaimer is in the app, the packs and `29` §13.
> - **Approval is a checkpoint, not a launch**: it releases the packaging spike first (proving the installer
>   path), then the six build phases — no code has been written before it.
> - **Approval is recorded, dated and scoped** to the state presented here; later material changes come back
>   to you with an impact note before any work starts.
> - **To approve, reply with the line in §9**; to change anything, say which section and it is fixed first.

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
| Interface & governance | `26`–`27` | The frozen API contract (95 routes, envelope, error catalogue, contract tests); the backlog register (34 items with promotion triggers) |
| Acceptance | `28` | The project DoD, `S1`–`S4` defect workflow, the real-data pilot, UAT with six scripts, the go-live checklist and the sign-off template |
| Client-facing | `29` | The plain-language requirements pack with the 17 decisions and the sign-off block |
| Memory & control | `CHANGELOG`, `SESSION_LOG`, this file | Every change with its reason; the session bridge; the approval record |

**Frozen by this set** (cite the owning doc, never a copy): 156 FRs in 11 families (P0 110 · P1 39 · P2 7) ·
43 screens · 12 charts · 24 exception rules · 8 Excel sheets · 6 slides · 3 source-system shapes (D365-style + two others) ·
32 import checks · 59 import messages · 95 API routes · 11 error families · 34 backlog items · 36 risks ·
19 open questions with labelled defaults · 10 ADRs · 37 decisions · 292 test slots in 16 families (206 owned by the doc set, 86 reserved for later phases) ·
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
| 11 | **Money is exact**: Decimal only, no epsilon, quantise at the documented boundary, one rounding policy | `05` §6 | The class of bug that destroys trust in a finance tool is designed out |
| 12 | **Materiality**: `max(₹5,00,000, 2 % × \|budget\|)` as the default threshold, client-editable | `05` §11 | Rules start where a finance team's attention starts, and they can change it |
| 13 | **Cross-artifact equality**: app = Excel = deck = CSV, zero tolerance, tested | `14` §7, `NFR-015` | "The slide says something else" is the fastest way to lose a client |
| 14 | **Quality bars**: engine coverage ≥ 90 %, app ≥ 75 %; recall ≥ 90 % of 32 planted exceptions with zero control raises | `14` §13.2, §5 | Quality is measured, not asserted |
| 15 | **Performance envelope**: 10 s cold start · 250k rows/100 MB ≤ 60 s · ≤ 2 s UI · pack ≤ 120 s · ≤ 1.5 GB install | `14` §8, `NFR-001`…`016` | The tool must be usable on the client's actual machine |
| 16 | **Nine never-cut items** (exact money, atomic imports, audit versioning, local-only, installer + real-Windows validation, disclaimer, backup/restore, golden tests, cross-artifact equality) | `02` §3.3 | Scope can move; these cannot |
| 17 | **Docs-first, quote-before-code**: no code before recorded approval; every change updates its owning doc first | `19` §2 | The reason this phase exists |
| 18 | **Deferrals live in one place** with a trigger that would promote them | `27` §4 | A "later" without a trigger is a lost requirement |
| 19 | **Sample data is never delivered to the client**, and never mixed with real data | `13`/`14` §16 | Contamination safety; go-live checks it explicitly |

## 4. Top risks (full register: `25`; scores are impact × likelihood, 1–5)

| Risk | Why it would hurt | Mitigation in force |
|---|---|---|
| **Messy real files break the importer** (`RISK-001`, 20) | Nothing else matters if month one does not load | 32 validation checks, quarantine rather than silent repair, mapping profiles, a malformed-file corpus, and the pilot month before go-live |
| **The sanitized real month never arrives** (`RISK-002`, 20) | The pilot, UAT and trust all depend on it (`OQ-014`) | Named as a schedule dependency; a fallback (UAT on sample data with a written limitation) and an early ask in `29` §7 |
| **Unsigned installer blocked** (`RISK-003`, 20) | The client cannot install | SmartScreen ladder, hash verification, portable-zip fallback, and a certificate decision (`OQ-012`) |
| **Rule precision disappoints** (`RISK-004`, 20) | Too many false positives and the register is ignored | Recall ≥ 90 % with zero control raises, effective-threshold traceability, suppression, effectiveness analytics |
| **App numbers differ from the client's manual pack** (`RISK-005`, 16) | Trust collapses at the first tie-out | Tie-out worksheet, four-class difference taxonomy, drill-through to the source row, frozen mapping profiles |
| **Real volumes exceed the envelope** (`RISK-006`, 16) | The tool becomes unusable in month two | 250k-row performance work with committed baselines and a > 20 % regression gate |
| **Scope pressure pushes P1/P2 into P0 time** (`RISK-007`, 16) | A gate slips or quality drops | The cut-line process, the never-cut list, and every deferral with a trigger (`27`) |
| **Windows-only evidence gap** (`RISK-008`, 12) | It works on the dev machine and fails on the client's | Real-Windows checks at every gate, with screenshots and run sheets |

## 5. Open questions and the three answers that matter most

| Question | Owner | Default in force | When it is needed |
|---|---|---|---|
| **`OQ-014`** — when will one sanitized real month arrive? | Client | **None — this one has no default** | Before the pilot (`GATE-13`); the biggest schedule dependency |
| **`OQ-016`** — support/warranty terms after go-live | You (project owner) | Consultant-first support with the `23` §10 response targets as labelled defaults | Before go-live; `28` §3.1 marks the placeholder |
| **`OQ-017`** — the approved installer delivery channel | You | Secure link + published SHA-256 | Before the pilot; sized for a ~500 MB file plus its hash |
| `OQ-012` — code-signing certificate budget | You | Not purchased; mitigation ladder applies | Before the packaging spike's install step |
| 15 further design/data questions (`OQ-001`…`OQ-013`, `OQ-015`, `OQ-021`/`022`) | Client | Each has a labelled default, so no work is blocked | Answered through `21`/`29` §7 as the build reaches each area |
| **Scope question for this session** — build `sample-data/` now, or after approval? | You | Not built (this session was documentation-only) | Before `GATE-04-02`/`-07` can close |

## 6. Gate snapshot

| Gate | Checks | Status |
|---|---|---|
| `GATE-01` Kickoff | 9 | **8 ✅ / 1 ⬜** — open: `GATE-01-06` (the step-by-step installer script is proven by the packaging spike, which is deliberately post-approval) |
| `GATE-02` Addon 1 | 12 | **12 ✅** — the tabletop walkthrough is executed and recorded in `SESSION_LOG` |
| `GATE-03` Addon 2 | 12 | **12 ✅** |
| `GATE-04` Addon 3 | 12 | **10 ✅ / 2 ⬜** — open: `GATE-04-02` (Addon 3 matrix rows all integrated except `A3-F`), `GATE-04-07` (the `sample-data/malformed/` corpus) |
| `GATE-05` Addon 4 | 13 | **13 ✅** |
| **Total** | **58** | **55 ✅ / 3 ⬜** (`14` §15) |

The self-audit and link-check ran in this pass: every citation resolves, every table is well-formed, every
ID token matches a registered namespace, and the two remaining documentation-shaped risks are the corpus
above plus the installer script. Both are execution items, not specification gaps.

## 7. What approval means

1. **It is recorded, dated and scoped** — `Phase 0 APPROVED — <who> — <date>` in `CHANGELOG.md` and
   `SESSION_LOG.md` (Addon 4 §E.2). It applies to the state presented here.
2. **It releases the packaging spike first** (two half-days: hello-world → PyInstaller → Inno Setup →
   installed launch on real Windows 11 through the SmartScreen path). If that path cannot be made to work,
   the project stops and escalates rather than building features on an unproven installer.
3. **It releases Phases 1–6** after the spike (`16` §6): import & validation, BvA & drill-down, exceptions,
   forecast, packs, then AI and polish — with your answers to §5 arriving as the build reaches each area.
4. **It does not freeze the spec forever.** Any material change afterwards gets an **impact note** first
   (affected FRs, docs, tests, size S/M/L), and the gate is re-opened rather than edited quietly.
5. **No product code exists yet.** The repository contains documentation, the skeleton and `.gitkeep`
   files; nothing has been built, installed or shipped.

## 8. What happens next

| When | What |
|---|---|
| On approval | Record the approval; then answer §5's first three rows in parallel with the packaging spike |
| Week 1 | Packaging spike (`GATE-06`) → corrected `15` if reality differed |
| After the spike | Phase 1 (import & validation) begins, with your mapping walkthrough and the sample files from `29` §8 |
| Before UAT | The pilot month (`GATE-13`) with the tie-out worksheet and the signed classification log |
| Before go-live | UAT (`GATE-14`, ≤ 5 business days, six scripts), training (`22` §10), then the 22-item go-live checklist (`GATE-15`) |
| After go-live | Two month-ends of hypercare, the first accuracy review, and the feedback intake that turns requests into `27` items before any code |

## 9. The approval ask

Reply with the line below (add any condition you want recorded):

```
Phase 0 APPROVED — <your name> — <date>
Conditions / notes: <optional>
```

Or reply with the section numbers you want changed; each one is fixed, re-audited and re-presented before
approval. **No product code will be written until this line is recorded.**

# FP&A Month-End Copilot

A **local, offline-first, single-user Windows 11 desktop application** that automates the month-end
FP&A rhythm for a non-technical finance team: import ERP exports (Excel/CSV) → validate → analyse
budget vs actual → surface potential exceptions → refresh the rolling forecast → generate the
management Excel pack and PowerPoint deck.

It replaces a fully manual monthly cycle (Dynamics 365 exports + two other systems, manual variance
investigation, manual PowerPoint building) with a guided, deterministic, auditable workflow that runs
entirely on the user's machine. Optional AI commentary is **off by default** and never computes,
approves, or posts anything.

---

## Current phase: **PHASE 0 — DOCUMENTATION**

**No product code exists and none may be written until Phase 0 passes all five quality gates and the
project owner records explicit approval** (see `docs/19_VIBE_CODING_PLAYBOOK.md`, Addon 4 §E.2).

| | |
|---|---|
| **Phase** | Phase 0 — Documentation set (docs `00`–`29`) |
| **Approval required before** | Any code in `app/`, `ui/`, `tests/`, `packaging/`, `scripts/` |
| **App version (planned)** | 0.1.0 |
| **Docs version** | 0.1.0 (pre-approval working draft) |
| **Last updated** | 2026-10-01 |

---

## How to open the docs

**Start here → [`docs/00_INDEX.md`](docs/00_INDEX.md).**

It contains the document map, the reading order, the **Addon Coverage Matrix** (all 64 sections of the
spec of record), the **Source-of-Truth Matrix** (which doc owns which fact), the ID namespace
registry, and the live quality-gate tracker. Never read the docs in a random order; the reading plan
in `00_INDEX.md` is mandatory.

---

## Repository structure

```
docs/           The Phase 0 documentation set (00_INDEX … 29_CLIENT_REQUIREMENTS_PACK) + CHANGELOG + SESSION_LOG
app/            Python 3.12 backend: headless engine, FastAPI layer, CLI  (Phase 1+, empty until approval)
ui/             React + TypeScript + Vite SPA                                    (Phase 1+, empty until approval)
sample-data/    Fictional generator, input templates, planted exceptions, malformed corpus (Phase 0)
tests/          pytest unit/golden tests, Playwright E2E, contract tests         (Phase 1+, empty until approval)
packaging/      PyInstaller spec + Inno Setup script                             (Phase 1+, empty until approval)
scripts/        dev / check / build / release one-command scripts                (Phase 1+, empty until approval)
```

---

## The spec of record

This project is built strictly spec-first. The contract is the uploaded kickoff prompt **plus four
addons** (stored at the repo root as `FP&A MONTH-END COPILOT — AGENTIC.txt`):

1. **Kickoff prompt** — Sections 1–15 (role, product context, principles, stack/ADR-001, Phase 0 doc
   tree, scope, data model, calculations, exceptions, AI policy, reporting, UX, quality, session
   protocol, next actions).
2. **Addon 1** — Completeness & production readiness (principles P11–P20, docs 21–25, domain
   checklist, ingestion hardening, Windows hardening, financial correctness, security/supply chain,
   release, enablement, NFRs, session addenda, parked backlog, combined gate).
3. **Addon 2** — Architecture, contract & feature precision (headless engine boundary, doc 26,
   ADR-002, data-volume rule, config layering, exception identity/re-run semantics, UI/UX & a11y,
   coverage bars, AI provenance).
4. **Addon 3** — Domain workflows, AI depth & acceptance (docs 27–28, mapping review queue,
   commentary lock, pack issuance register, four full prompt texts, chart inventory, cross-artifact
   consistency, negative corpus, UAT/go-live).
5. **Addon 4** — Spec consumption, prioritisation & real-data acceptance (doc 29, standard doc
   header, quote-before-code, Source-of-Truth Matrix, FR P0/P1/P2 priorities, never-cut list,
   real-data pilot gate, tolerance & edge-case matrices, engineering discipline).

Where the documents overlap, **later addons add requirements and never remove them**.

---

## Non-negotiable rules for anyone (human or AI) working in this repo

1. **Docs before code.** The spec is the source of truth; behaviour changes go into spec + CHANGELOG
   **first**, then code.
2. **Deterministic money math.** `Decimal`/minor units only — binary floats are forbidden in currency
   maths. AI never computes, approves, or posts.
3. **Offline, local-only data.** No cloud storage, no telemetry, no auto-upload. Imported file
   content is treated as hostile input.
4. **Traceability.** Every number is drillable to source transactions and the source file/import
   batch; every FR is traceable to a spec section, screen, API endpoint, and test.
5. **Scope discipline.** If it is not in an approved FR it does not get built; new ideas go to
   `docs/27_BACKLOG.md` or `docs/18_...OPEN_QUESTIONS.md`.
6. **Quality bars are numbers.** Performance, coverage, installer size, start-up time are stated as
   numbers and measured — never assumed.
7. **Spec consumption protocol.** Read `docs/00_INDEX.md` first; quote the FR text before writing
   any code for it; if you cannot cite the FR, you may not build it (Addon 4 §B).

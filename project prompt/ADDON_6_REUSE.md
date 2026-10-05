# ADDON 6 (v2) — REUSE-FIRST BUILD: COPY, SURGICAL EDIT, DOC SYNC

**Version:** v2, 2026-10-05. **Supersedes:** the earlier draft `ADDON_6_REUSE.md` v1 — do not run v1; this file replaces it entirely.
**Status:** Owner-commissioned addon. Additive only — it adds a build method; it removes nothing from the contract.
**Target repo:** `Warzonesiddiki/finalFPA`. **Save this file at** `project prompt/ADDON_6_REUSE.md` and commit it.
**Stack position:** after the kickoff prompt, Addons 1–5, mission brief, quality standard, team-YOLO addon. If anything here appears to conflict with an earlier requirement, BOTH hold: the earlier requirement stays in force, and this addon adds the method. This addon may never override: license law, Tier C rails, or docs 00–31 as spec of record.
**Research basis:** every catalog license below was verified 2026-10-05 against the GitHub license API or the raw LICENSE/pyproject file. Evidence is recorded in `docs/32_REUSE_AND_PROVENANCE.md` when created.

---

## 0. How to read this (binding)

1. Execute this document **literally**. It is written for an agent that does exactly what is written and nothing more. Where it says MUST, you must. Where it says STOP, you stop and write an entry in `docs/18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md` — you do not improvise.
2. Read in this order before touching anything: `docs/00_INDEX.md`, `STATE.md`, this file, `docs/17_CODING_STANDARDS.md`, `docs/09_TECHNICAL_ARCHITECTURE.md` (ADR registry), `docs/18_...` (latest decisions).
3. **Spec of record:** docs 00–31 define WHAT the product does. This addon defines HOW to obtain code faster. Copied code is always subordinate to the spec: if they disagree, you change the CODE, never the spec (spec change = normal change process → docs/18 → owner).
4. Everything here is Tier B (default + log) EXCEPT where Sections 4, 5, or 14 say STOP / Tier C.
5. Report after every adoption: numbers, not adjectives (files copied, lines kept/removed, tests added, coverage %, check result).

## 1. The one rule: reuse before build

Before writing ANY new module (capability-level code, roughly >50 lines, or any new folder under `app/`, `ui/`, `scripts/`), run this decision tree in order — no shortcuts:

```
Q1. Is the capability in the Approved Source Catalog (Section 3)
    with Mode = COPY-EDIT?
      YES → REUSE PATH. Go to S0 (Section 6). Do not write it yourself.
      NO  → Q2. Run Intake (Section 10).
              Intake APPROVES a source → REUSE PATH. Go to S0.
              Intake finds nothing usable → BUILD PATH (normal dev process),
                    AND write a BD row into docs/32 §2 "Build Decisions"
                    so this question is never searched again.
Q2. Already implemented in our repo? → STOP (R12). No second implementation.
```

- Reuse and build are mutually exclusive per capability. Never "build first, look at sources later."
- Worked examples: duplicate-invoice scoring → WS-01 → REUSE. Template-based PPT filling → WS-02 + WS-10 → REUSE. Overflow-safe layout → WS-03 → REUSE. Double-entry GL corpus generator → catalog has no COPY source → Intake → expected outcome BUILD → BD row (golden invariants from WS-11 apply).

## 2. Vocabulary (exact meanings — use these words precisely)

| Term | Exact meaning |
|---|---|
| **SOURCE REPO / UPSTREAM** | A public GitHub repository we may take code or ideas from. |
| **Mode: COPY-EDIT** | Copy listed files, edit surgically, ship them in our binary. Requires PASS on gate 4A. |
| **Mode: GOLDEN REFERENCE** | READ it; encode its expected behaviors as our spec/tests. **Zero code copied.** No license gate needed. |
| **Mode: PATTERN-LIFT** | Re-implement an idea from its README/docs in our own code from scratch. **Zero code copied.** |
| **Mode: DEV-ONLY TOOL** | A tool used during development/tests only (never in the shipped installer's runtime). License rule = 4B. |
| **STAGING** | `vendor/_staging/<WS-ID>/` — the only place copied files may be edited before they earn a place in `app/`. |
| **PROVENANCE ROW** | A row in `docs/32_REUSE_AND_PROVENANCE.md` §1 recording where code came from. |
| **ADP-nnn** | Provenance ID, one per adoption (ADP-001, ADP-002, …). Cited in file headers, ADR, CHANGELOG. |
| **BD row** | Build Decision row (docs/32 §2): "we searched, found nothing, built it ourselves." |

## 3. Approved Source Catalog

Licenses verified 2026-10-05 (GitHub license API / raw LICENSE / pyproject). **You still re-run gate 4A at fetch time** — licenses can change. The live catalog is `docs/32_REUSE_AND_PROVENANCE.md` §1; additions go there via Section 10.

| ID | Upstream | Mode | Take EXACTLY these files | Target | NEVER take | License (evidence) |
|---|---|---|---|---|---|---|
| WS-01 | `github.com/ricothanfx/invoice-dedupe` | COPY-EDIT | from `src/invoice_dedupe/`: normalization, blocking, weighted-scoring modules only (≤6 files; exact list after clone) | `app/engine/dedupe/` | `app.py`, `webapp/`, `vercel*`, `AGENTS.md`, CI, CLI, anything Postgres/PDF | **MIT** — `pyproject.toml` line `license = { text = "MIT" }` (no LICENSE file; record that line as evidence) |
| WS-02 | `github.com/m3dev/pptx-template` | COPY-EDIT | `pptx_template/` package (template + model fill engine) | `app/engine/pptx_fill/` (must conform doc 12 §3.6 + `ppt_spec.py`) | CLI, examples, docs images, `.eggs/`, workflows | **Apache-2.0** — LICENSE file present |
| WS-03 | `github.com/Whatsonyourmind/deckforge` | COPY-EDIT | overflow handler only (font-shrink → reflow → slide-split logic; ≤4 files) | `app/engine/pptx_fill/layout.py` | dashboard/UI, app shell, configs | **MIT** — LICENSE file (© 2026 Luka Stajic…) |
| WS-10 | `github.com/keithmcnulty/ppt-generation` | COPY-EDIT | the edit_pres-style fill helpers (placeholder, `chart.replace_data`, table-cell fill) | `app/engine/pptx_fill/patterns.py` | R wrappers, tutorial prose, sample data | **CC0-1.0** — LICENSE file (attribute anyway) |
| WS-05 | `github.com/dev-belly/AuditLens` | COPY-EDIT (optional) | Benford + explainable-scoring functions only, IF doc 06 needs them implemented | `app/engine/audit_stats/` | web UI, dashboards, demo data | **MIT** — LICENSE file (© 2026 AuditLens contributors) |
| WS-11 | `github.com/dev-belly/LedgerX` + `github.com/bababadr06-dot/ledgerlens` | GOLDEN REFERENCE | nothing; extract invariants: every entry sums to zero, per-entity/per-period balance, exact-integer/Decimal units, replay verification | corpus-rebuild tests (`tests/`) | **all code — no license** | NO LICENSE (404 on API) → L2 applies |
| WS-04 | `github.com/LAKSHYA-NIGAM/Journal-Entry-Audit-Analytics-Platform` | GOLDEN REFERENCE | nothing; expected behaviors of its control rules (near-threshold band, weighted risk tiers) | doc 06 change proposals + tests where 06 already rules | all code (SQL ≠ our stack) | not needed (no code) |
| WS-06 | `github.com/KushPatel29/gl-reconciliation-dashboard` | PATTERN-LIFT | nothing; patterns: exception ageing, owner SLA, close certification, evidence manifest | `docs/27_BACKLOG.md` rows + UI patterns | all code until 4A PASS | unverified → code copy forbidden by default |
| WS-07 | `github.com/Vanithanallamothu/journal-entry-sentinel` | PATTERN-LIFT | nothing; perf shape (DuckDB, 1M journals / 7 rules / 13 s) as budget evidence | `tests/perf/` budgets | all code | not needed (no code) |
| WS-08 | `github.com/scanny/python-pptx` | DEPENDENCY | pip dependency only (already in pyproject) | declared dependency | vendored source | MIT |
| WS-09 | `github.com/anthropics/financial-services` | GOLDEN REFERENCE | nothing; prompt/handoff-allowlist patterns | doc 10 via change process | all code | not needed (no code) |
| WS-12 | `github.com/Valdecy/Forecasting-01-Moving_Averages` | GOLDEN REFERENCE | nothing; cross-check of MA/EWMA formula shapes vs doc 07 | none (doc 07 is authority) | all code — no license | NO LICENSE → L2 applies |
| DT-01 | `github.com/raimon49/pip-licenses` | DEV-ONLY TOOL | installed in `dev` extras only; used by gate 4B | `scripts/license_gate.py` calls it | runtime deps | **MIT** — LICENSE file |
| DT-02 | `github.com/joke2k/faker` | DEV-ONLY TOOL | `dev` extras only; sample-data/corpus generator names | `sample-data/` generator | runtime deps | **MIT** — LICENSE.txt |
| DT-03 | `github.com/HypothesisWorks/hypothesis` | DEV-ONLY TOOL | `dev` extras only; property tests for import validators | `tests/` | runtime deps | **MPL-2.0** — LICENSE.txt; dev-only ⇒ 4B, never shipped |
| **WS-X** | `fschaeck/python-pptx-text-replacer` (**GPL-3.0**), `frappe/erpnext` (**GPL**), any GPL/AGPL/SSPL/BUSL/source-available repo, any repo with NO license, `Warzonesiddiki/fpa`, `Warzonesiddiki/fp-A-betterversion`, any SaaS/cloud/telemetry SDK | **NEVER** | nothing | — | everything | FORBIDDEN — do not even shortlist |

If a take-list proves wrong after cloning (listed file missing, logic lives elsewhere): **STOP** → docs/18 entry proposing the amended take-list → proceed after ruling. Do not improvise extra copies.

## 4. License gates — TWO gates, never confused

### 4A. Source gate — before ANY file is copied

Run inside `vendor/_upstream/<WS-ID>/`:

```bash
ls LICENSE* COPYING* NOTICE* 2>/dev/null
grep -ri "license" pyproject.toml package.json setup.cfg 2>/dev/null
```

| Result | Action |
|---|---|
| MIT, Apache-2.0, BSD-2/3-Clause, ISC, Unlicense, CC0, CC-BY | **GO** → record in docs/32 → Section 5 |
| GPL (any version), AGPL, LGPL, SSPL, BUSL, MPL (shipped code), "source-available", or **no license found anywhere** | **STOP** → Tier C → docs/18 → owner ruling. Default: do NOT copy. GOLDEN/PATTERN modes still allowed |
| Unclear after reading the file(s) | **STOP** (same) |

On GO: (1) Apache-2.0 → full LICENSE text into `THIRD_PARTY_NOTICES.md` + per-file notice `Modified from <repo> — Apache-2.0 — see THIRD_PARTY_NOTICES.md` + notices file ships in installer payload (note in `docs/15`); (2) MIT/CC0 → reproduce copyright notice in `THIRD_PARTY_NOTICES.md`; (3) license snippet + `git rev-parse HEAD` into the docs/32 row.
**Copying before gate PASS = S1 defect. Faked evidence = stop-work (evidence protocol).**

### 4B. Dependency gate — before shipping (runtime vs dev)

- **Runtime dependencies** (`[project] dependencies`): permissive only (same GO list as 4A minus CC0/BY content licenses). New runtime dep requires ADR line + docs/18 DEC in the same session (R9), then `pip-licenses --fail-on="GPL,AGPL,SSPL"` style check must pass.
- **Dev dependencies** (`[project.optional-dependencies] dev`): any recognized OSS license (incl. MPL-2.0) is allowed — dev tools are never in the installer payload. Still never GPL/AGPL (belt and braces).
- A dev-only package appearing in runtime dependencies = defect. A runtime package without a 4A-GO license = STOP.

## 5. Hard rails — violating any rail ends the task, not just the step

- **R1 — Spec wins.** Copied code adapts to docs 00–31. Never edit a spec doc to accommodate copied code.
- **R2 — Gate 4A first**, every time, even for catalog members.
- **R3 — Upstream never committed.** `vendor/_upstream/` in `.gitignore` (verify before cloning). Only staged, edited, provenance-recorded files land in `app/`.
- **R4 — Staging first.** Copies go to `vendor/_staging/<WS-ID>/`, never directly into `app/`.
- **R5 — Records before code lands.** docs/32 row + ADR + THIRD_PARTY_NOTICES entry exist before the first commit containing the code.
- **R6 — Tests travel with code.** Every adopted module lands with tests: adapt upstream test files (rewrite to our spec, provenance noted) and/or write new spec-derived ones. New `app/engine` code ≥90% coverage (D-15).
- **R7 — Never delete or weaken a test.** Upstream expectation contradicting our spec → upstream test is wrong: rewrite to spec, note divergence in the provenance row.
- **R8 — Decimal money.** `float` on a money path in copied code → convert per doc 05 or reject the file.
- **R9 — New runtime dependency = ADR line + docs/18 DEC, same session**, added to `pyproject.toml` in the same commit. Never a silent pip install.
- **R10 — Offline:** strip network calls, telemetry, analytics, remote fonts/CDN from anything copied.
- **R11 — Our IDs rule.** Foreign IDs map to ours (`EXC-xxx`, `IMP-xxx`, `FR-xxx`, `DEF-xxx`, `ADP-xxx`); mapping in the provenance row. Never introduce upstream IDs into our registers; never renumber ours.
- **R12 — One implementation per capability.** Adoption REPLACES existing partial logic behind the same interface, with regression tests proving spec cases still pass. Two live implementations = defect.
- **R13 — No wholesale forks.** Modules only, ≤10 files per adoption, never an entire repo.
- **R14 — Single writer.** You touch exactly the take-list + target paths + doc-sync files (Section 8). Else → Lead/Task Card.
- **L1 — GPL in ANY version** (GPL-2.0, GPL-3.0, AGPL, LGPL as shipped code) in the binary = forbidden. No "GPL is okay because…" — it is not.
- **L2 — No license = no code.** Repos without a license: zero lines copied, ever. Invariants/behaviors are extracted and **rewritten in our own code and words**.
- **L3 — No prose copying.** Never copy upstream README/docs text into our docs. Golden reference = read → re-express as our spec/tests in our own words.

## 6. The procedure — S0 to S10, in order

**S0 — Preflight reads** (Section 0.2). Grep `app/` for the capability. Already implemented → STOP (R12).

**S1 — Route:** catalog COPY-EDIT → reuse; else Intake (Section 10); else BUILD path + BD row.

**S2 — Fetch pinned upstream:**

```bash
mkdir -p vendor/_upstream vendor/_staging
# verify vendor/_upstream is in .gitignore first (R3)
git clone --depth 1 <UPSTREAM_URL> vendor/_upstream/<WS-ID>
git -C vendor/_upstream/<WS-ID> rev-parse HEAD    # this SHA goes in docs/32
```

**S3 — Gate 4A.** GO or STOP. No third option.

**S4 — Copy the take-list only** into `vendor/_staging/<WS-ID>/`. Listed file missing or logic elsewhere → STOP → docs/18.

**S5 — Records BEFORE editing code** (R5):
1. `docs/32_REUSE_AND_PROVENANCE.md` (create if absent — this addon authorizes it). §1 fields: `ADP-nnn | date | WS-ID | upstream URL | SHA | license+evidence | files copied | mode | target paths | FRs/rules served | divergence notes | author`. §2: `BD-nnn | capability | FR/spec quote | sources searched | why none fit | chosen approach`.
2. `THIRD_PARTY_NOTICES.md` (create if absent — authorized) with the 4A obligations.
3. ADR in `docs/09` registry: **verify** the next free number (registry ends ADR-010 → expect ADR-011; never renumber). Content: context, options (incl. "build ourselves"), decision = adopt WS-ID as ADP-nnn, consequences (deps, license, maintenance).

**S6 — Surgical edit in staging** per Section 7 (E1–E12), **including adapting upstream tests if any exist** (R6).

**S7 — Land + verify:**
1. Move edited files to target paths; wire imports.
2. `python -m pytest -m "not perf" -q` then `python scripts/check.py` — format, lint, type, tests, **license gate** all green.
3. Coverage of new/changed `app/engine` modules ≥90% (capture output).
4. Failure → fix loop max 2 attempts → stuck protocol (Section 14).

**S8 — Doc-sync sweep** per Section 8 table, same change.

**S9 — Evidence:** `evidence/<YYYY-MM-DD>-<WS-ID>-reuse/` with SHA-256 manifest of: provenance row, ADR, `scripts/check.py` output, upstream SHA, license snippet:

```bash
sha256sum evidence/<date>-<WS-ID>-reuse/* > evidence/<date>-<WS-ID>-reuse/SHA256SUMS
```

**S10 — Commit + report.** Commit message template:

```
reuse(ADP-nnn): adopt <capability> from <repo>@<sha> (<license>) — surgical edit

- files: <n> copied, <n> edited, <n> rejected
- target: <paths>
- serves: <FR/EXC/IMP ids>
- tests: <added/adapted n>, coverage <n>% over new code
- records: docs/32 ADP-nnn, ADR-0xx, THIRD_PARTY_NOTICES
- check: green (paste the one-line result incl. license gate)
```

Update `STATE.md` task line. Report with numbers.

## 7. Surgical-edit checklist (E1–E13) — run against every staged file

- **E1** Delete everything not on the take-list (demos, `__main__`, runners, scratch).
- **E2** Imports → `app.engine...` layout; no `sys.path` hacks.
- **E3** Storage: upstream DB/SQL/file writes become pure functions returning dataclasses; OUR caller persists (DuckDB). No psycopg/sqlite/etc. leaking in.
- **E4** Money → `Decimal`, quantized per doc 05; grep `float` on money paths (R8).
- **E5** Errors → our envelope + `ERR-*` codes; API-visible changes need the doc 26 amendment process first.
- **E6** Our logger only; no `print`, no telemetry, no outbound URLs (R10).
- **E7** Thresholds → settings-driven; **default behavior = adopted behavior unless doc 06 says otherwise; doc 06 always wins.**
- **E8** Header on every adapted file: `Adapted from <repo> @ <sha> (<license>) — ADP-nnn — modified; see docs/32`.
- **E9** Dependencies: only pre-existing pyproject deps, or R9 completed.
- **E10** No dead code: no test needs it and no FR serves it → it doesn't land.
- **E11** `ruff` + `mypy` clean per `scripts/check.py`.
- **E12** Hidden coupling (network, auth, external DB, exotic deps) → STOP → re-run Section 10 on the amended take-list.
- **E13** Upstream tests adapted or new tests written for every public function that lands (R6).

## 8. Doc-sync table — every adoption, every time (append-only; never renumber; never delete)

| # | File | What to write | When |
|---|---|---|---|
| 1 | `docs/32_REUSE_AND_PROVENANCE.md` | ADP row (+ BD row on build path) | before code lands |
| 2 | `THIRD_PARTY_NOTICES.md` | license text / attribution | before code lands |
| 3 | `docs/09` ADR registry | new ADR | before code lands |
| 4 | `docs/18_...` | first entry: "Addon 6 v2 assigned 2026-10-05, SHA-256 of `project prompt/ADDON_6_REUSE.md` = …"; then one DEC per adoption/intake/BD/new dep | same session |
| 5 | `docs/CHANGELOG.md` | dated entry: what adopted, what changed, why | every commit landing code |
| 6 | `docs/00_INDEX.md` | registry rows for new ADP/ADR/BD IDs; pointer to docs/32 | every adoption |
| 7 | `docs/20_REQUIREMENTS_TRACEABILITY.md` | row if adoption newly satisfies an FR | if FRs affected |
| 8 | `docs/14_TESTING_QA_PLAN.md` + coverage evidence | regenerate coverage for touched modules | every adoption |
| 9 | `docs/27_BACKLOG.md` | close/annotate item if fulfilled | if applicable |
| 10 | `docs/15_PACKAGING_DEPLOYMENT_RUNBOOK.md` | notices file in payload; dev-only deps excluded from payload | first adoption + first new dep |
| 11 | `README.md` §2 | only if user-facing behavior changed | if applicable |

Corrections = new dated lines below the old one. If adoption changes observable behavior vs. spec → spec change via docs/18 + owner FIRST (R1), then code.

## 9. Pre-approved work cards (first wave — no new approval needed)

- **WC-1 — WS-01 dedupe → `app/engine/dedupe/`.** DONE WHEN: normalizer + blocker + weighted scorer behind our interface; doc-06 duplicate rule(s) evaluate through it; doc-06 cases pass; R12 replacement with regression tests; coverage ≥90%; upstream tests adapted; rapidfuzz (if used) via R9; ADP + ADR + notices + green check.
- **WC-2 — WS-02 + WS-10 (+ WS-03 overflow) template fill → `app/engine/pptx_fill/` (fixes DEF-018, S1).** DONE WHEN: `ppt_pack.py` copies the 7-layout template and fills by shape name per doc 12 §3.6; `ERR-EXP-014` family exists in `app/engine/errors.py`; `ppt_spec.py` exists as canonical shape order; no slide built from scratch; WS-10 patterns for chart/table fills; WS-03 overflow logic behind a flag until doc 12 amendment if needed; doc-12 conformance tests pass. Divergence recorded in ADP rows.
- **WC-3 — WS-05 AuditLens (optional) → `app/engine/audit_stats/`.** ONLY if doc 06 demands Benford/scoring we don't have; else golden. DONE WHEN: doc 06 cases pass, coverage ≥90%, provenance complete.
- **WC-4 — WS-04/WS-06/WS-07 extraction.** Expected behaviors → tests where doc 06 already rules; ageing/SLA patterns → doc 27 backlog rows; perf numbers → `tests/perf/`. Zero code copied.
- **WC-5 — GL corpus generator rebuild: BUILD path.** Run Intake once (expect: nothing copyable — WS-11/LedgerX+ledgerlens have no license → L2). Write BD row. Build per docs 03/04/05 double-entry rules; encode WS-11 invariants as tests (sum-to-zero per entry, per-entity/per-period balance, 1999 = 0.00, replay verification); DT-02 faker (dev-only) allowed for names via R9. Oracle stays `scripts/verify_trial_balance.py`. Unbalanced result must surface BLOCKED, never a pass.
- **WC-6 — README §2 truth fix.** Align with STATE.md (pilot-blocked; version 0.1.0 per pyproject; harness + corpus in flight).

Order: **WC-6 first (minutes), then WC-2 (S1), then WC-1.** WC-5 may run in parallel as a separate single-writer track. One adoption fully through S0–S10 before the next starts.

## 10. Intake — sources NOT in the catalog (6-field form)

Search, shortlist ≤3 candidates, write ONE docs/18 entry with exactly:

1. **URL + capability** (which FR/spec quote it serves);
2. **License evidence** (file + text, gate 4A);
3. **Proposed take-list** (≤10 exact paths);
4. **Proposed mode** (COPY-EDIT / GOLDEN / PATTERN-LIFT / DEV-ONLY);
5. **Risks** (deps, network, ID collisions, R12 overlap);
6. **Tier asked for.**

Rules: license GO + ≤2 modules + no spec change + no API change → **Tier B: proceed same session, log DEC**. Anything else → **Tier C: STOP for owner.** No-license repos may only be approved as GOLDEN/PATTERN (L2). Never intake inside another task's single-writer boundary.

## 11. Machine gate — `scripts/license_gate.py`, wired into `scripts/check.py`

A dumb agent cannot skip a rail if CI fails. Create this script (this addon authorizes it) with exactly these checks; exit code 1 on any violation, print every violation:

```
CHECK 1 — Provenance completeness:
  For every file under app/ containing the string "Adapted from":
    its ADP id must appear in docs/32_REUSE_AND_PROVENANCE.md §1
    AND in THIRD_PARTY_NOTICES.md.
CHECK 2 — Forbidden licenses in shipped code:
  Scan app/, ui/, packaging/ for license names: GPL, AGPL, LGPL, SSPL, BUSL,
  "source-available" (word-boundary match) → FAIL if found in code/comments
  except inside THIRD_PARTY_NOTICES.md (which may cite them as refusals).
CHECK 3 — Upstream hygiene:
  vendor/_upstream/ must be listed in .gitignore and must not exist in git ls-files.
CHECK 4 — Dependency split:
  Every package in [project] dependencies passes the 4A GO list;
  DT-* tools (pip-licenses, faker, hypothesis) must appear only under dev extras.
CHECK 5 — Header format:
  Every "Adapted from" header parses as:
  Adapted from <url-ish> @ <7-40 hex> (<license>) — ADP-nnn — …
  Malformed header → FAIL.
```

Wire: `scripts/check.py` runs `python scripts/license_gate.py` as its final step; output pasted into evidence (S9). The gate is part of DoD.

## 12. Definition of Done (paste this as your claim; every box must be literally true)

```
[ ] S0–S10 completed in order; docs/32 ADP row has upstream SHA + license evidence
[ ] Gate 4A PASS recorded (or mode = GOLDEN/PATTERN with zero code copied)
[ ] vendor/_upstream/ gitignored; no upstream repo/CI/config committed
[ ] Only take-list files staged; every adapted file has the ADP header (E8), parseable (CHECK 5)
[ ] E1–E13 passed per file (state yes/no per item)
[ ] Upstream tests adapted and/or new tests written (count) — zero tests deleted/weakened
[ ] Money paths: zero float (grep evidence); no network/telemetry (grep evidence)
[ ] Coverage of new app/engine code ≥90% (paste number)
[ ] python scripts/check.py green INCLUDING license_gate (paste one-liner)
[ ] R12: no duplicate implementation (name the interface replaced/confirmed)
[ ] New deps (if any): ADR line + docs/18 DEC + pyproject same commit; runtime vs dev correct
[ ] Doc-sync Section 8 rows 1–11 done or explicitly N/A
[ ] ADR number verified, not assumed; no existing ID renumbered
[ ] THIRD_PARTY_NOTICES updated; docs/15 payload note (first adoption/dep)
[ ] evidence/<date>-<WS-ID>-reuse/ exists with SHA256SUMS
[ ] STATE.md + report updated with numbers, not adjectives
```

## 13. Anti-patterns — dumb-agent traps. Catching yourself in one: STOP, undo, log

- **T1** Copying a whole repo "to sort it out later" (R13).
- **T2** Editing a spec doc so copied code passes (R1 — forbidden).
- **T3** Skipping gate 4A because the catalog says GO (R2 — verify every time).
- **T4** Committing `vendor/_upstream/` (R3).
- **T5** `cp` straight into `app/` (R4).
- **T6** Claiming DONE with "tests pass" but no coverage number, no check output, no ADP row.
- **T7** Asserting upstream behavior that contradicts docs 00–31 (R7).
- **T8** Second implementation next to existing logic (R12).
- **T9** Silent `pip install` (R9); or putting a dev tool into runtime dependencies (4B).
- **T10** Pasting upstream code from memory — every landed line traces to a pinned SHA in docs/32; untraceable → remove.
- **T11** Renumbering IDs to "avoid collisions" — map, never renumber (R11).
- **T12** Deleting an upstream test instead of adapting it (R7).
- **T13** Reporting "feature complete / 100% / verified" without the number (see Session-010 history).
- **T14** Parallel adoptions in the same files (R14).
- **T15** Copying upstream README/docs prose into ours (L3).
- **T16** Upgrading a GOLDEN/PATTERN repo to COPY-EDIT on your own because "the license looked fine" (only Section 10 + docs/18 DEC changes mode).

## 14. Escalation, stuck protocol, YOLO

- **STOP / Tier C:** license not on the GO list (incl. no license anywhere); spec change needed; API contract change; take-list >10 files; any GPL-family contact with shipped code; ambiguity where a wrong guess wastes money, data, or client trust.
- **Tier B (default + log):** everything else here — proceed, DEC same session.
- **Stuck:** 2 failed attempts → rollback to last green → escalation packet with exactly 3 options + recommended default. Never idle, never half-land.
- Opening the report is a notification, not a permission request (Tier B); Tier C waits.
- `LEVEL: 1` in STATE.md overrides all of the above.

## 15. First six actions, right now

1. Save/commit this file at `project prompt/ADDON_6_REUSE.md`; `sha256sum` it; write the docs/18 DEC with that hash (Section 8 row 4).
2. Create `docs/32_REUSE_AND_PROVENANCE.md` (§1 empty adoptions, §2 empty build decisions), `THIRD_PARTY_NOTICES.md` skeleton; add `vendor/_upstream/` to `.gitignore`.
3. Write `scripts/license_gate.py` per Section 11; wire into `scripts/check.py`; run it — must pass on the current tree (no "Adapted from" yet → checks 2–4 must still pass).
4. **WC-6:** correct `README.md` §2 to match `STATE.md` reality.
5. **WC-2:** S0→S10 with WS-02 (+ WS-10 patterns, WS-03 behind flag) — the DEF-018 S1 defect.
6. After WC-2 green: **WC-1** (WS-01). Then report both with numbers. WC-5 (corpus) runs as its own parallel BUILD track with its BD row.

**End of Addon 6 v2.**

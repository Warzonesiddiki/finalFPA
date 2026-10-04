# ADDON 6 — REUSE-FIRST BUILD: COPY, SURGICAL EDIT, DOC SYNC

**Status:** Owner-commissioned addon, 2026-10-05. Additive only — it adds a build method, it removes nothing from the contract.
**Target repo:** `Warzonesiddiki/finalFPA`. **Save this file at** `project prompt/ADDON_6_REUSE.md` and commit it.
**Stack position:** after the kickoff prompt, Addons 1–5, mission brief, quality standard, team-YOLO addon. When anything here appears to conflict with an earlier requirement, BOTH hold: the earlier requirement stays in force, and this addon supplies the additional method. The only thing this addon may never override: license law, Tier C rails, and docs 00–31 as spec of record.

---

## 0. How to read this (binding)

1. Execute this document **literally**. It is written for an agent that does exactly what is written and nothing more. Where it says MUST, you must. Where it says STOP, you stop and write an entry in `docs/18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md` — you do not improvise.
2. Read in this order before touching anything: `docs/00_INDEX.md`, `STATE.md`, this file, `docs/17_CODING_STANDARDS.md`, `docs/09_TECHNICAL_ARCHITECTURE.md` (ADR registry), `docs/18_...` (latest decisions).
3. **Spec of record:** docs 00–31 define WHAT the product does. This addon defines HOW to obtain code faster. Copied code is always subordinate to the spec: if they disagree, you change the CODE, never the spec (changing spec = normal change process → docs/18 → owner).
4. Everything in this addon is Tier B (default + log) EXCEPT where Section 4, 5, or 13 says STOP / Tier C.
5. Report format after every adoption: numbers, not adjectives (files copied, lines kept/removed, tests added, coverage %, check result).

## 1. The one rule: reuse before build

Before writing ANY new module (capability-level code, roughly >50 lines, or any new folder under `app/`, `ui/`, `scripts/`), run this decision tree — in order, no shortcuts:

```
Q1. Is the capability in the Approved Source Catalog (Section 3)?
      YES → REUSE PATH. Go to S0 (Section 6). Do not write it yourself.
      NO  → Q2. Run the Intake procedure (Section 10).
              Intake APPROVES a source → REUSE PATH. Go to S0.
              Intake finds nothing usable → BUILD PATH (normal dev process),
                    AND write one row into docs/32 §2 "Build Decisions"
                    so this question is never searched again.
Q2. Are you already mid-file on the same capability? → follow single-writer
    rules (team addon); never create a second implementation (Rail R12).
```

- Reuse and build are mutually exclusive per capability. Never "build first, look at sources later."
- Worked examples: duplicate-invoice scoring → catalog WS-01 → REUSE. Template-based PPT filling → catalog WS-02 → REUSE. Double-entry GL generator (corpus option B) → no catalog entry → Intake → almost certainly BUILD → log the Build Decision row.

## 2. Vocabulary (exact meanings — use these words precisely)

| Term | Exact meaning |
|---|---|
| **SOURCE REPO / UPSTREAM** | A public GitHub repository we may take code or ideas from. |
| **Mode: COPY-EDIT** | We copy listed files, edit them surgically, ship them in our binary. Requires a PASS license gate (Section 4). |
| **Mode: GOLDEN REFERENCE** | We READ it and encode its expected behaviors as our spec/tests. **Zero code copied.** No license gate needed (no code lands). |
| **Mode: PATTERN-LIFT** | We re-implement an idea from its README/docs in our own code from scratch. **Zero code copied.** |
| **STAGING** | `vendor/_staging/<WS-ID>/` — the only place copied files may be edited before they earn a place in `app/`. |
| **PROVENANCE ROW** | A row in `docs/32_REUSE_AND_PROVENANCE.md` §1 recording where code came from. |
| **ADP-nnn** | Provenance ID, one per adoption (ADP-001, ADP-002, …). Cited in file headers, ADR, CHANGELOG. |
| **BUILD DECISION** | A row in docs/32 §2 recording "we searched, found nothing, built it ourselves." |

## 3. Approved Source Catalog (starter set; the live catalog is `docs/32_REUSE_AND_PROVENANCE.md` §1)

License column as verified on 2026-10-05. **You still re-run Section 4 at fetch time** — licenses can change.

| ID | Upstream | Mode | Take EXACTLY these files | Target in our repo | NEVER take | License (verify again) |
|---|---|---|---|---|---|---|
| WS-01 | `github.com/ricothanfx/invoice-dedupe` | COPY-EDIT | from `src/invoice_dedupe/`: the normalization, blocking, and weighted-scoring modules only (identify exact filenames after clone; expected ≤6 files) | `app/engine/dedupe/` | `app.py`, `webapp/`, `vercel.json`, `vercelignore`, `AGENTS.md`, CI files, CLI entrypoint, anything Postgres | **MIT** declared in `pyproject.toml` (`license = { text = "MIT" }`); no LICENSE file → GO with attribution, record the pyproject line as evidence |
| WS-02 | `github.com/m3dev/pptx-template` | COPY-EDIT | `pptx_template/` package (the template+model fill engine) | `app/engine/pptx_fill/` (must conform to doc 12 §3.6 and `ppt_spec.py`) | CLI, examples, docs images, `.eggs/`, workflows | **Apache-2.0** (`LICENSE` file present) → GO with Section 4 obligations |
| WS-03 | `github.com/Whatsonyourmind/deckforge` | PATTERN-LIFT until license proven | nothing (re-implement overflow idea: font shrink → reflow → slide split) | `app/engine/pptx_fill/layout.py` if/when built | all code until §4 PASS | UNVERIFIED → code copy forbidden by default |
| WS-04 | `github.com/LAKSHYA-NIGAM/Journal-Entry-Audit-Analytics-Platform` | GOLDEN REFERENCE | nothing; extract expected behaviors of its control rules (incl. near-threshold band, weighted risk tiers) as candidate expectations | `tests/` expectations where doc 06 already covers the rule; doc-06 amendments via change process only | all code (SQL stack ≠ ours) | not needed (no code) |
| WS-05 | `github.com/dev-belly/AuditLens` | GOLDEN REFERENCE | nothing; methodology (Benford, explainable 0–100 scoring) informs doc 06 proposals | change-process proposals only | all code | not needed (no code) |
| WS-06 | `github.com/KushPatel29/gl-reconciliation-dashboard` | PATTERN-LIFT | nothing; patterns: exception ageing, owner SLA, close certification, evidence manifest | `docs/27_BACKLOG.md` items + UI patterns | all code until §4 PASS | UNVERIFIED |
| WS-07 | `github.com/Vanithanallamothu/journal-entry-sentinel` | PATTERN-LIFT | nothing; perf shape only (DuckDB, 1M journals / 7 rules / 13 s) as budget evidence | `tests/perf/` budgets | all code | not needed (no code) |
| WS-08 | `github.com/scanny/python-pptx` | DEPENDENCY | pip dependency only (already in pyproject) | declared dependency | vendored source | MIT — already compliant |
| WS-09 | `github.com/anthropics/financial-services` | GOLDEN REFERENCE | nothing; prompt/handoff-allowlist patterns for doc 10 prompt texts | doc 10 via change process | all code | not needed (no code) |
| WS-X | `frappe/erpnext`, any GPL/AGPL/SSPL/BUSL/source-available repo, `Warzonesiddiki/fpa`, `Warzonesiddiki/fp-A-betterversion`, any SaaS/cloud/telemetry SDK | **NEVER** | nothing | — | everything | FORBIDDEN — do not even shortlist |

If a take-list proves too small or wrong after you clone (e.g., the real logic lives in a file not listed): **STOP** → docs/18 entry proposing the amended take-list → proceed after the ruling. Do not improvise extra copies.

## 4. License gate (run before ANY file is copied)

Run inside `vendor/_upstream/<WS-ID>/`:

```bash
ls LICENSE* COPYING* NOTICE* 2>/dev/null
grep -ri "license" pyproject.toml package.json setup.cfg 2>/dev/null
```

Decision matrix — one line, no judgment calls:

| Result | Action |
|---|---|
| MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, Unlicense | **GO** → record in docs/32, then Section 5 |
| GPL, AGPL, LGPL, SSPL, BUSL, MPL, "source-available", dual-source-without-permissive-option, or **no license found anywhere** | **STOP** → Tier C → docs/18 → owner ruling. Default until ruled: do NOT copy. May still be GOLDEN REFERENCE / PATTERN-LIFT |
| Unclear after reading the file(s) | **STOP** (same as above) |

Extra obligations on GO:
- **Apache-2.0:** copy the LICENSE text into `THIRD_PARTY_NOTICES.md` (create at repo root — this addon authorizes that file); every modified file carries a prominent one-line notice `Modified from <repo> — Apache-2.0 — see THIRD_PARTY_NOTICES.md`; the notices file must ship in the installer payload (note it in `docs/15_PACKAGING_DEPLOYMENT_RUNBOOK.md`).
- **MIT:** reproduce the copyright notice in `THIRD_PARTY_NOTICES.md`.
- Evidence: paste the license snippet + `git rev-parse HEAD` of the clone into the docs/32 row.
- **Copying code before the gate passes = S1 defect. Faked or copied-from-memory evidence = stop-work (evidence protocol).**

## 5. Hard rails (R1–R14) — violating any rail ends the task, not just the step

- **R1 — Spec wins.** Copied code adapts to docs 00–31. You never edit a spec doc to accommodate copied code.
- **R2 — License gate first** (Section 4), every time, even for catalog members.
- **R3 — Upstream never committed.** `vendor/_upstream/` goes in `.gitignore` (verify it is there before cloning). Only staged, edited, provenance-recorded files ever land in `app/`.
- **R4 — Staging first.** `cp` goes to `vendor/_staging/<WS-ID>/`, never directly into `app/`.
- **R5 — Records before code lands.** docs/32 row + ADR + THIRD_PARTY_NOTICES entry exist before the first commit that contains the code.
- **R6 — Tests travel with code.** Every adopted module lands with tests (adapted upstream tests or new spec-derived ones). New `app/engine` code ≥90% coverage (D-15).
- **R7 — Never delete or weaken a test.** If an upstream expectation contradicts our spec, the upstream test is wrong: rewrite it to the spec and note the divergence in the provenance row.
- **R8 — Decimal money.** Any `float` on a money path in copied code → convert to `Decimal` per doc 05 or reject the file.
- **R9 — New dependencies need an ADR line + docs/18 entry in the same session** (e.g., `rapidfuzz` if WS-01 scoring needs it: Tier B default+log, add to `pyproject.toml` in the same commit, never a silent pip install).
- **R10 — Offline:** strip network calls, telemetry, analytics, remote fonts/CDN references from anything copied. Local-only, always.
- **R11 — Our IDs rule.** Foreign IDs map to ours (`EXC-xxx`, `IMP-xxx`, `FR-xxx`, `DEF-xxx`, `ADP-xxx`); the mapping goes in the provenance row. Never introduce upstream IDs into our registers.
- **R12 — One implementation per capability.** If we already have partial logic for the capability (e.g., existing duplicate checks), the adoption REPLACES it behind the same interface, with regression tests proving spec cases still pass. Two live implementations = defect.
- **R13 — No wholesale forks.** Option B-lite stands: modules only, ≤~10 files per adoption, never an entire repo.
- **R14 — Single writer.** The files you may touch are exactly the take-list + target paths + doc-sync files (Section 8). Anything else → coordinate via the Lead / Task Card, do not touch.

## 6. The procedure — S0 to S10, in order

**S0 — Preflight reads** (Section 0.2 list). Confirm the capability is not already implemented (grep `app/` for it). Already implemented → STOP, this is R12 territory.

**S1 — Route the task:** catalog member → reuse; else Intake (Section 10); else BUILD path + Build Decision row.

**S2 — Fetch pinned upstream:**

```bash
mkdir -p vendor/_upstream vendor/_staging
# verify vendor/_upstream is in .gitignore first (R3)
git clone --depth 1 <UPSTREAM_URL> vendor/_upstream/<WS-ID>
git -C vendor/_upstream/<WS-ID> rev-parse HEAD    # this SHA goes in docs/32
```

**S3 — License gate** (Section 4). GO or STOP. No third option.

**S4 — Copy the take-list only** into `vendor/_staging/<WS-ID>/`. If a listed file doesn't exist, or the logic obviously lives elsewhere → STOP → docs/18 (Section 3 rule).

**S5 — Write the records BEFORE editing code** (R5):
1. `docs/32_REUSE_AND_PROVENANCE.md` — create it if absent (this addon authorizes it). §1 table, one row, fields: `ADP-nnn | date | WS-ID | upstream URL | SHA | license+evidence | files copied | mode | target paths | FRs/rules served | divergence notes | author`. §2 table: Build Decisions (`BD-nnn | capability | FR/spec quote | sources searched | why none fit | chosen approach`).
2. `THIRD_PARTY_NOTICES.md` — add the license/attribution entry (Section 4).
3. ADR in `docs/09_TECHNICAL_ARCHITECTURE.md` registry: verify the next free number (registry currently ends ADR-010 → expect **ADR-011**; never renumber existing ADRs). ADR content: context, options considered (incl. "build it ourselves"), decision = adopt WS-ID as ADP-nnn, consequences (deps, license, maintenance).

**S6 — Surgical edit in staging** using the checklist Section 7 (E1–E12).

**S7 — Land + verify:**
1. Move edited files to their target paths; wire imports to our layout.
2. `python -m pytest -m "not perf" -q` then `python scripts/check.py` — format, lint, type, tests all green.
3. Coverage for new/changed `app/engine` modules ≥90% (run the coverage command in `scripts/check.py`, capture output).
4. Failure → fix loop, maximum 2 attempts → then stuck protocol (Section 13).

**S8 — Doc-sync sweep** using the table in Section 8. Every row that applies, done in the same change.

**S9 — Evidence:** create `evidence/<YYYY-MM-DD>-<WS-ID>-reuse/` containing: SHA-256 manifest, copy of the docs/32 row, ADR text, `scripts/check.py` output, upstream SHA, license snippet. Hash with:

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
- check: green (paste the one-line summary)
```

Update `STATE.md` task line. Report with numbers (quality standard), not adjectives.

## 7. Surgical-edit checklist (E1–E12) — run against every staged file

- **E1** Delete everything not on the take-list (demos, `__main__`, sample runners, scratch).
- **E2** Rewrite imports to `app.engine...` layout; no `sys.path` hacks.
- **E3** Storage: upstream DB/SQL/file writes become pure functions returning dataclasses; OUR caller persists (DuckDB store). No psycopg/sqlite/whatever leaking in.
- **E4** Money → `Decimal`, quantized per doc 05; grep for `float` on money paths (R8).
- **E5** Errors → our error envelope and `ERR-*` codes; if the code is API-visible, doc 26 needs its amendment process before it ships.
- **E6** Our logger only; no `print`, no telemetry, no outbound URLs (R10).
- **E7** Thresholds/constants → settings-driven, but **default behavior = adopted behavior unless doc 06 says otherwise; doc 06 always wins.**
- **E8** File header on every adapted file: `Adapted from <repo> @ <sha> (<license>) — ADP-nnn — modified; see docs/32`.
- **E9** Dependencies: only what pyproject already has, or R9 process completed.
- **E10** No dead code: if a test doesn't need it and no FR serves it, it doesn't land.
- **E11** `ruff` + `mypy` clean per `scripts/check.py`.
- **E12** Hidden coupling discovered (network, auth, external DB, exotic deps) → STOP → re-run Section 10 on the amended take-list.

## 8. Doc-sync table — every adoption, every time (append-only; never renumber; never delete)

| # | File | What to write | When |
|---|---|---|---|
| 1 | `docs/32_REUSE_AND_PROVENANCE.md` | ADP row (+ BD row on build path) | before code lands |
| 2 | `THIRD_PARTY_NOTICES.md` | license text / attribution | before code lands |
| 3 | `docs/09_...` ADR registry | new ADR | before code lands |
| 4 | `docs/18_...` | DEC entry: "Addon 6 assigned 2026-10-05, SHA-256 of `project prompt/ADDON_6_REUSE.md` = …" (first entry), then one DEC per adoption/intake/build decision | same session |
| 5 | `docs/CHANGELOG.md` | dated entry: what adopted, what changed, why | every commit that lands code |
| 6 | `docs/00_INDEX.md` | registry rows for new ADP/ADR/BD IDs; pointer to docs/32 | every adoption |
| 7 | `docs/20_REQUIREMENTS_TRACEABILITY.md` | row if adoption newly satisfies an FR | if FRs affected |
| 8 | `docs/14_TESTING_QA_PLAN.md` + coverage evidence | regenerate coverage evidence for touched modules | every adoption (D-15) |
| 9 | `docs/27_BACKLOG.md` | close/annotate item if adoption fulfills it | if applicable |
| 10 | `docs/15_PACKAGING_DEPLOYMENT_RUNBOOK.md` | notices file included in payload | first adoption only |
| 11 | `README.md` §2 | only if user-facing behavior changed | if applicable |

Rules: corrections = new dated lines below the old one, never in-place rewrites of history. If adoption changes observable behavior vs. spec → spec change via docs/18 + owner FIRST (R1), then code.

## 9. Pre-approved work cards (first wave — no new approval needed)

- **WC-1 — WS-01 dedupe → `app/engine/dedupe/`.** DONE WHEN: normalizer + blocker + weighted scorer sit behind our interface; the doc-06 duplicate rule(s) evaluate through it; doc-06 spec cases pass; R12 replacement done with regression tests; coverage ≥90%; ADP + ADR + notices + check green. Dependencies (`rapidfuzz`) only via R9.
- **WC-2 — WS-02 template fill → `app/engine/pptx_fill/` (fixes DEF-018, S1).** DONE WHEN: `ppt_pack.py` copies the 7-layout template and fills by shape name per doc 12 §3.6; `ERR-EXP-014` and the `ERR-EXP-*` family exist in `app/engine/errors.py`; `ppt_spec.py` exists and is the canonical shape order; no slide is built from scratch; doc-12 conformance tests pass. If upstream cannot express name-based resolution → keep only what fits, PATTERN-LIFT the rest, record divergence in the ADP row.
- **WC-3 — WS-04/05 golden extraction.** Write expected behaviors as test cases ONLY where doc 06 already specifies the rule; propose additions via change process. Zero code copied.
- **WC-4 — WS-07 perf budgets** → `tests/perf/` numbers justified by its measurements. Zero code copied.
- **WC-5 — GL generator rebuild (corpus option B):** run Intake once (Section 10); expected outcome = BUILD path → BD row → normal build under the existing fix-crew process. Reuse does not shortcut the double-entry correctness rules of docs 03/04/05.

Order: **WC-2 first (S1 defect), then WC-1.** One adoption fully through S0–S10 before the next begins (serial until proven stable).

## 10. Intake — sources NOT in the catalog (6-field form)

Search, shortlist ≤3 candidates, then write ONE docs/18 entry containing exactly these six fields:

1. **URL + capability** (which FR/spec quote it serves);
2. **License evidence** (file + text, per Section 4);
3. **Proposed take-list** (≤10 files, exact paths);
4. **Proposed mode** (COPY-EDIT / GOLDEN / PATTERN-LIFT);
5. **Risks** (new deps, network, ID collisions, R12 overlap with existing code);
6. **Tier asked for.**

Tier rules: license GO + ≤2 modules + no spec change + no API change → **Tier B: proceed same session, log DEC**. Anything else → **Tier C: STOP for owner.** Intake never runs inside another task's single-writer boundary.

## 11. Definition of Done (paste this as your claim; every box must be literally true)

```
[ ] S0–S10 completed in order; docs/32 ADP row exists with upstream SHA + license evidence
[ ] License gate PASS recorded (or mode = GOLDEN/PATTERN-LIFT with zero code copied)
[ ] vendor/_upstream/ is gitignored; no upstream repo/CI/config committed
[ ] Only take-list files staged; every adapted file has the ADP header line (E8)
[ ] E1–E12 checklist passed per file (state: yes/no per item)
[ ] Money paths: zero float (grep evidence)
[ ] No network/telemetry in landed code (grep evidence)
[ ] Tests: added/adapted = N; all green; zero existing tests deleted or weakened
[ ] Coverage of new app/engine code ≥90% (paste number)
[ ] python scripts/check.py green (paste one-line result)
[ ] R12: no duplicate implementation (name the interface you replaced/confirmed)
[ ] Doc-sync table Section 8: rows 1–11 each done or explicitly N/A
[ ] ADR number verified, not assumed; no existing ID renumbered
[ ] THIRD_PARTY_NOTICES updated; payload note in docs/15 (first adoption)
[ ] evidence/<date>-<WS-ID>-reuse/ exists with SHA256SUMS
[ ] STATE.md + report updated with numbers, not adjectives
```

## 12. Anti-patterns — dumb-agent traps. Catching yourself in one: STOP, undo, log

- **T1** Copying a whole repo "to sort it out later" (R13).
- **T2** Editing a spec doc so the copied code passes (R1 — forbidden).
- **T3** Skipping the license gate because the catalog already says GO (R2 — verify every time).
- **T4** Committing `vendor/_upstream/` (R3).
- **T5** `cp` straight into `app/` (R4).
- **T6** Claiming DONE with "tests pass" but no coverage number, no check output, no ADP row.
- **T7** Writing a test that asserts upstream behavior contradicting docs 00–31 (R7 — spec wins).
- **T8** Second implementation next to existing logic (R12).
- **T9** Silent `pip install` of upstream dependencies (R9).
- **T10** Pasting upstream code from memory instead of cloning it — every landed line must trace to a pinned SHA in docs/32; untraceable code = remove it.
- **T11** Renumbering our `EXC-xxx`/`IMP-xxx`/`FR-xxx` or upstream IDs to "avoid collisions" — map, never renumber (R11).
- **T12** Deleting an upstream test instead of adapting it (R7).
- **T13** Reporting "feature complete / 100% / verified" without the number behind it (quality standard; see DEF/Session-010 history).
- **T14** Starting WC-2 and WC-1 in parallel in the same files (single-writer R14; Lead partitions, you don't self-partition).

## 13. Escalation, stuck protocol, YOLO

- **STOP/Tier C (owner):** license not on the GO list; spec change needed; API contract change; take-list beyond 10 files; wholesale-fork temptation; any ambiguity where the wrong guess wastes money, data, or client trust.
- **Tier B (default + log):** everything else this addon covers — proceed, write the DEC the same session.
- **Stuck:** 2 failed attempts → rollback to last green → post an escalation packet with exactly 3 options + a recommended default (never idle, never half-land).
- **Opening the report is a notification, not a permission request** for Tier B items; Tier C waits.
- `LEVEL: 1` in STATE.md overrides all of the above → supervised mode.

## 14. First five actions, right now

1. Save/commit this file at `project prompt/ADDON_6_REUSE.md`; compute `sha256sum` of it; write the docs/18 DEC entry with that hash (Section 8 row 4).
2. Create `docs/32_REUSE_AND_PROVENANCE.md` (§1 Adoptions table empty, §2 Build Decisions empty), `THIRD_PARTY_NOTICES.md` skeleton; add `vendor/_upstream/` to `.gitignore`.
3. Correct `README.md` §2 to match `STATE.md` reality (pilot-blocked; version per `pyproject.toml` 0.1.0; acceptance harness + corpus rebuild in flight) — truthfulness defect, same session.
4. Start **WC-2** (DEF-018, S1): S0 → S10 with WS-02 exactly as specified.
5. After WC-2 lands green: **WC-1** (WS-01). Then report both with numbers.

**End of Addon 6.**

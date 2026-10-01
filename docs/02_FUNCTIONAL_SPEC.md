> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** every functional requirement (`FR-nnn`), its priority, inputs, outputs, edge cases and acceptance criteria
> **TL;DR (≤ 15 lines):** This document is the single source of truth for feature behaviour. Every
> capability is an `FR-nnn` with a priority (P0 phase-gating, P1 should-ship, P2 could-ship), a phase, its
> inputs/outputs, edge cases, and testable acceptance criteria. Eleven families: ONB onboarding, PRJ
> project/period lifecycle, IMP import & validation, BVA budget-vs-actual analysis, EXC exception engine,
> FC forecast, XL Excel pack, PPT PowerPoint pack, AI commentary, SET settings/master data, XC
> cross-cutting. §3 defines the priority and cut-line policy; §16 is the mandated edge-case matrix. If a
> behaviour is not in this document, it does not get built (P6, Addon 4 §B.3).

---

# 02 — FUNCTIONAL SPECIFICATION

## 1. Purpose, scope and conventions

This document owns **feature behaviour**: what the product does, for every in-scope capability. It does
not own formulas (`05`), exception logic (`06`), forecast logic (`07`), screen layouts (`08`), table
structures (`03`), import mechanics (`04` on file quirks/profiles), API shapes (`26`), or tests (`14`).

**Conventions used in every FR block:**

| Field | Meaning |
|---|---|
| `FR-<FAMILY>-nnn` | Permanent, append-only requirement ID (see `00_INDEX.md` §8) |
| `P0 / P1 / P2` | Priority (see §3). P0 gates its phase; P1 should ship; P2 could ship |
| `Phase n` | The roadmap phase in which the FR must be complete (`16`) |
| **Behaviour** | What happens, stated so a developer cannot improvise |
| **Inputs / Outputs** | Data entering and leaving the feature |
| **Edge cases** | Explicit, non-default conditions (canonical matrix in §16) |
| **Acceptance criteria** | Verifiable statements; each maps to at least one `TST-nnn` in `14` and a row in `20` |

**Cross-reference rules:** screen IDs (`SCR-nnn`), API endpoints (`API-nnn`), test IDs (`TST-nnn`) and
numeric error codes (`ERR-<FAM>-nnn`) are assigned by their owning docs (`08`, `26`, `14`) and joined to
FRs in `20_REQUIREMENTS_TRACEABILITY.md`. This document refers to screens by name and to user-facing
messages by **stable message slug** (e.g. `import.noDataRows`), which `26` maps to numeric codes.
Numeric thresholds that are calculation parameters live in `05`/`06`; this document references them.

**Wording rules (P8):** the product never says "error", "wrong entry", or "confirmed" about data it
flags. Canonical phrasing: *"Potential exception — requires accounting review."* Any deviation is a
defect. All user-facing copy rules are owned by `08`.

## 2. FR families

| Family | Scope | Phases | Count |
|---|---|---|---|
| `FR-ONB` | Onboarding, first-run, help, sample project | 1–6 | 8 |
| `FR-PRJ` | Projects, periods, snapshots, backup/restore, storage health | 1–6 | 12 |
| `FR-IMP` | Import, mapping, profiles, validation, batches, quarantine | 1 | 31 |
| `FR-BVA` | Budget vs actual analysis, drill-down, KPIs, rollups, search | 2 | 16 |
| `FR-EXC` | Exception engine, register, workflow, analytics, evidence | 3 | 20 |
| `FR-FC` | Rolling forecast, scenarios, accuracy | 4 | 9 |
| `FR-XL` | Excel pack | 5 | 9 |
| `FR-PPT` | PowerPoint pack | 5 | 9 |
| `FR-AI` | Optional AI commentary and mapping suggestions | 6 | 14 |
| `FR-SET` | Settings, master data, display locale, version history | 1–6 | 12 |
| `FR-XC` | Cross-cutting: commentary, issuance, diagnostics, errors, a11y | 1–6 | 16 |

156 FRs total. The traceability index (status per FR) is owned by `20`.

## 3. Priority and cut-line policy (Addon 4 §D)

### 3.1 Priority definitions

| Priority | Meaning | Consequence of a gap |
|---|---|---|
| **P0** | The phase cannot close without it | Phase gate fails; release blocked |
| **P1** | Should ship in its phase | Gap listed explicitly with a finish-or-defer decision at the gate |
| **P2** | Could ship; first candidate for the cut line | Deferred by default if the phase is at risk |

### 3.2 Phase gate rule

All P0 FRs of the phase must be green (spec → tests → works on sample data → error/empty states →
traceability → changelog → demoable). P1/P2 gaps are listed with an explicit decision.

### 3.3 Never-cut list (may never be deferred, descoped or "simplified")

Exact money maths (Decimal/minor units) · atomic all-or-nothing imports · versioned audit of edits ·
offline/local-only data behaviour · the Windows installer and real-Windows validation · the advisory
disclaimer · backup/restore · golden tests · the cross-artifact consistency test.

### 3.4 Cut process

Any cut outside the never-cut list requires (a) a written proposal with impact and size, (b) the project
owner's explicit approval, (c) a `27_BACKLOG.md` entry with a trigger condition. Silent under-delivery is
a protocol violation — as is building P2 work while P0 work is open.

### 3.5 Definition of Done (per FR)

Spec updated → tests written → works on the sample project → error/empty/loading states handled →
`20` traceability updated → `CHANGELOG` entry → demo recipe recorded in `SESSION_LOG` (Addon 2 §F.5,
Addon 3 §I.5).

## 4. `FR-ONB` — Onboarding, first-run and help (8 FRs)

**FR-ONB-001 · P0 · Phase 1 — First run opens the sample project**
- **Behaviour:** On first launch after install, the app creates/copies the bundled sample project into
  the local data directory, opens it, and lands on Home with the sample banner visible. No wizard, no
  account setup, no file dialog stands between install and first value.
- **Inputs → Outputs:** bundled `sample-data/` seed → a project folder + an open Home screen.
- **Edge cases:** sample seed missing/corrupt (Phase-6 evidential check: rebuild the seed and log;
  never show a blank app); second launch opens the last project (FR-ONB-006); the client deletes the
  sample project (it is re-creatable from Settings → "Restore sample project").
- **Acceptance:** on a clean install, the app is interactive on the sample project with no user input
  beyond launching it, and cold start meets `NFR-001`.

**FR-ONB-002 · P2 · Phase 6 — Guided first-run tour**
- **Behaviour:** A dismissible, skippable overlay tour of 6 steps (Home → Import → Check → Analyze →
  Exceptions → Reports) with one sentence per step and a "don't show again" switch.
- **Edge cases:** tour interrupted by a crash/restart → resumes at the recorded step (wizard state is
  persisted); tour disabled → never reappears.
- **Acceptance:** tour completes on the sample project without blocking any workflow; dismissal persists
  across restarts.

**FR-ONB-003 · P0 · Phase 1 — "Load your own data" is always one action away**
- **Behaviour:** A persistent primary action on Home (and in Import) opens the file picker; it is never
  hidden behind a menu, and it is present whether a project is open or not (creating one if needed).
- **Acceptance:** from any screen, ≤ 2 clicks reach the file picker.

**FR-ONB-004 · P1 · Phase 1 — Help panel with contextual help**
- **Behaviour:** A right-side help panel available on every screen, showing the topic for the current
  screen/step; wizard steps carry an inline "What is this?" expander. Copy is task language, not
  technical language.
- **Edge cases:** help content missing for a screen → panel shows the workflow-level topic, never an
  empty panel.
- **Acceptance:** every screen in the inventory has a help topic; help text matches doc `22` verbatim
  (single source).

**FR-ONB-005 · P0 · Phase 1 — Blank templates downloadable from inside the app**
- **Behaviour:** Import/Home expose "Download blank template" for: actuals, budget, forecast,
  master data (vendor categories, recurring costs, approval thresholds). Files are written where the
  user chooses and match the shipped `.xlsx` templates exactly (including the template version stamp).
- **Acceptance:** the downloaded file opens in Excel without repair prompts and imports successfully
  after being filled with a minimal valid dataset.

**FR-ONB-006 · P0 · Phase 1 — Reopen last project and autosave**
- **Behaviour:** The app records the last opened project and reopens it on launch; all editable forms
  auto-save with a visible "Saved" state. Closing the app without saving a form is not possible
  (autosave on change, debounced).
- **Edge cases:** last project folder moved/deleted → Home shows the project as missing with "Locate…"
  and "Remove from recents" actions; never a crash or an empty window.
- **Acceptance:** kill the process mid-edit and relaunch → the last committed edit is present, and any
  uncommitted job is reported as recoverable or cancelled (no half-state).

**FR-ONB-007 · P1 · Phase 2 — Help text is single-sourced with the user guide**
- **Behaviour:** In-app help and `22_END_USER_GUIDE.md` render from the same content source, keyed by
  `SCR-nnn`; a wording change lands in one place.
- **Acceptance:** a doc-hygiene test detects divergence between the help source and doc `22` sections.

**FR-ONB-008 · P0 · Phase 1 — Sample data is unmistakable and cannot contaminate client data**
- **Behaviour:** Sample projects carry `project_type: sample`, a persistent in-app "SAMPLE DATA" banner,
  and a watermark on every generated Excel/PPT output. Imports into a sample project are refused with a
  message unless the user explicitly converts the project to a normal project (loud, typed
  confirmation, irreversible, audit-logged). Sample projects are excluded from the deliverables sent to
  the client.
- **Acceptance:** no exported artefact from a sample project lacks the watermark; the go-live checklist
  verifies no sample files are present on the client machine.

## 5. `FR-PRJ` — Projects, periods, storage and lifecycle (12 FRs)

**FR-PRJ-001 · P0 · Phase 1 — Home screen**
- **Behaviour:** Home shows: open/recent project, current period with status (Open/Closed), last import
  summary (file, batch, rows, balance result, when), a KPI strip for the current period, quick actions
  (Import / Check / Analyze / Generate pack), and health warnings (failed checks, stale derived results,
  low storage, pending quarantine rows).
- **Edge cases:** no project open (offer sample, create, or open recent); zero periods yet (quick action
  = New Period wizard); stale results (banner with "Re-run required").
- **Acceptance:** every warning shown on Home links to the screen that resolves it.

**FR-PRJ-002 · P0 · Phase 1 — Create project**
- **Behaviour:** Name, fiscal calendar (year start, period codes), reporting currency, unit scale,
  optional entity list, optional branding overrides. Creates the project folder, schema, and an empty
  Open period; refuses to create inside a detected syncing folder (warns and offers the default
  `%LOCALAPPDATA%` path).
- **Acceptance:** a new project is importable-to immediately and reopens correctly after restart.

**FR-PRJ-003 · P0 · Phase 1 — Open and manage recent projects**
- **Behaviour:** Recent-projects list with path, last opened, last period, and status; actions: open,
  reveal in Explorer, back up, remove from recents (list only), delete (typed confirmation).
- **Edge cases:** missing folder, read-only folder, path over 260 characters (long-path support), path
  containing Unicode.
- **Acceptance:** every error state names the folder and the next action.

**FR-PRJ-004 · P0 · Phase 1 — New Period wizard**
- **Behaviour:** "Start <month> close" opens the period, lists expected sources for that period
  (actuals from each system, budget if not yet loaded, master data), shows what is missing, and carries
  forward **mappings, thresholds, master data and assumptions — never numbers**.
- **Edge cases:** starting a period out of order (warn, require confirmation); starting a period already
  existing (offer to switch to it); no budget loaded (allow, flag, and disable variance rules with a
  notice per §16).
- **Acceptance:** the wizard never copies prior-period figures; a carried-forward mapping is identical
  in version and content to the one it came from.

**FR-PRJ-005 · P0 · Phase 1 — Period status: Open / Closed, with audited reopen**
- **Behaviour:** Closing a period locks its actuals (no import/void/re-import changes the closed
  numbers) and prompts a backup reminder. Reopening requires an explicit warned action with a typed
  confirmation of the period code and is audit-logged; after reopen, derived results are marked stale.
- **Edge cases:** reopen with an issued pack → warning states that the issued pack's snapshot is
  unaffected and a re-issue will be required for any changed number.
- **Acceptance:** a void attempt on a closed period is blocked with a message offering "Reopen period".

**FR-PRJ-006 · P0 · Phase 1 — Single instance per project**
- **Behaviour:** A named mutex per project; a second launch on the same project shows a friendly
  "This project is already open in another window" with "Switch to it" (where possible) or "Close".
- **Acceptance:** no database locking error is ever shown to the user; the second instance exits
  cleanly.

**FR-PRJ-007 · P0 · Phase 1 — Schema version check and migration on open**
- **Behaviour:** On open, the project's stored schema version is compared with the app's; older →
  mandatory backup prompt, then a documented migration with a progress indicator and a written result;
  newer → refuse to open with a "this project needs a newer app version" message.
- **Edge cases:** migration failure → project untouched, backup retained, diagnostics offered.
- **Acceptance:** upgrade-over-previous-version is exercised in `14` with a real prior-version fixture.

**FR-PRJ-008 · P0 · Phase 1 — Back up a project to a zip**
- **Behaviour:** One action produces a timestamped zip of the project folder (databases, archives,
  settings, mappings, master data) containing **no secrets** (AI keys are machine-level, `09`/`13`), plus
  a manifest with versions.
- **Acceptance:** a backup taken before a destructive operation restores to a byte-equivalent working
  state (verified by the recovery drill in `14`).

**FR-PRJ-009 · P0 · Phase 1 — Restore a project from a zip**
- **Behaviour:** Choose a zip → validate manifest and versions → restore to a chosen (empty) folder →
  open or add to recents. Restoring over an existing project requires a typed confirmation.
- **Edge cases:** zip from a newer app/schema version (refuse with guidance); corrupt/partial zip
  (refuse, nothing written).
- **Acceptance:** restore on a clean machine reproduces the project exactly (drill in `14`).

**FR-PRJ-010 · P1 · Phase 3 — Period-close snapshot**
- **Behaviour:** Closing a period stores an immutable snapshot of the numbers behind any issued pack
  (per pack version), so a later re-import or re-run cannot rewrite history behind an already-sent deck.
  Snapshots are readable (Compare view) but never editable.
- **Acceptance:** after issuing a pack, re-importing different numbers for the same period leaves the
  snapshot unchanged and the difference visible.

**FR-PRJ-011 · P1 · Phase 3 — Storage health and archive-and-delete**
- **Behaviour:** Settings/About show storage used by the project with a breakdown (databases, raw
  archives, exports); a configurable low-storage warning appears on Home; "Archive and delete" exports
  raw archives to a zip (user-chosen location) and then deletes them after a typed confirmation.
- **Edge cases:** deletion with the project open in another window (blocked by FR-PRJ-006); deletion
  failure mid-way (partial state reported explicitly, never silently).
- **Acceptance:** after archive-and-delete, all reports still work; only raw-file evidence is gone, and
  the UI says so.

**FR-PRJ-012 · P1 · Phase 1 — Delete project with typed confirmation**
- **Behaviour:** Deleting a project requires typing the project name, states exactly what will be
  deleted (folder path, size, batch count), and logs the action.
- **Acceptance:** no project deletion is possible with a single unconfirmed click.

## 6. `FR-IMP` — Import, mapping, validation and batches (31 FRs)

**FR-IMP-001 · P0 · Phase 1 — Import entry: drag-and-drop and file picker**
- **Behaviour:** Files can be dropped anywhere on the Import screen (with a visible drop zone and
  drag-over state) or chosen via a file picker. Both paths converge on the same pipeline.
- **Edge cases:** unsupported extension; zero-byte file; a folder dropped; multiple files dropped at
  once (queued sequentially with per-file status).
- **Acceptance:** each rejection names the file and the reason, and nothing is partially loaded.

**FR-IMP-002 · P0 · Phase 1 — Source type and file fingerprint**
- **Behaviour:** The user picks the source type (D365-style GL actuals, payroll summary,
  procurement/bank ledger, budget, forecast, master data) or accepts a suggested one; the app computes a
  SHA-256 fingerprint of the file and records it before any parsing.
- **Edge cases:** same file already imported (FR-IMP-019); fingerprint matches but file modified
  (treated as a different file, with a warning naming the earlier import).
- **Acceptance:** the fingerprint is stored with the batch and shown in Import History.

**FR-IMP-003 · P0 · Phase 1 — Pre-scan with estimate and limits**
- **Behaviour:** Before parsing, the app reports file size, sheet count, estimated row count and
  estimated import duration; if limits (`NFR` import size/rows) would be exceeded, the user must confirm
  explicitly or cancel, and the limit check result is recorded in the batch.
- **Edge cases:** estimate cannot be produced (protected/encrypted workbook) → reject with a named
  reason.
- **Acceptance:** no import starts without a completed pre-scan; the estimate is shown with its basis.

**FR-IMP-004 · P0 · Phase 1 — Column mapping with preview**
- **Behaviour:** The mapping screen shows the first N rows (default 20) of the chosen sheet with
  detected types and sample values per column, and lets the user map each source column to a canonical
  field, mark it ignored, or set a per-column override (format, scale, sign convention). Required
  canonical fields are listed with a live "still unmapped" indicator.
- **Edge cases:** duplicate source headers; unlabelled columns; more columns than the screen can show
  (scrollable, with a column summary); mapping changed after a preview (re-preview required).
- **Acceptance:** the import cannot proceed while a required canonical field is unmapped.

**FR-IMP-005 · P0 · Phase 1 — Saved mapping profiles**
- **Behaviour:** Mapping sets can be saved as named, versioned profiles (source type, sheet selector,
  header row, column map, per-column overrides, date/number rules). A D365-style profile ships with the
  app. Profiles are editable, clonable, exportable/importable (JSON), and versioned with history and
  revert.
- **Edge cases:** profile applied to a file missing a mapped column → the mapping screen opens with the
  missing column flagged, never a silent best-guess.
- **Acceptance:** importing the same file shape next month requires no re-mapping.

**FR-IMP-006 · P1 · Phase 1 — Header-fingerprint profile auto-suggest**
- **Behaviour:** When a dropped file's header set matches a saved profile at or above the configured
  similarity threshold, that profile is pre-selected (with a confidence note and the option to change).
  Below the threshold, no suggestion is made.
- **Acceptance:** the threshold is a documented setting and the suggestion is always overridable.

**FR-IMP-007 · P1 · Phase 1 — Template version stamp and outdated-template warning**
- **Behaviour:** App-downloaded templates carry a version stamp; importing a file built from an older
  template warns with the differences and requires confirmation to continue.
- **Acceptance:** current-template files import with no warning; stale-template files always warn.

**FR-IMP-008 · P1 · Phase 6 — AI mapping review queue**
- **Behaviour:** When a file has unmapped columns and AI is enabled, AI may *propose* mappings; each
  suggestion shows source column, target field, confidence, and evidence (examples of previously
  accepted rows). States: `suggested → accepted | edited | rejected`, with bulk accept/edit and audit
  trail. Suggestions are **never auto-applied in the same run**; accepted mappings apply to future
  imports. With AI disabled, the queue shows rule-based suggestions only.
- **Edge cases:** AI returns a target field that does not exist (rejected and logged as a malformed
  response, FR-AI-006); the same column suggested twice (deduplicated).
- **Acceptance:** a suggestion accepted during import N is applied automatically in import N+1 and
  appears in the mapping profile history.

**FR-IMP-009 · P0 · Phase 1 — Excel structure quirks are handled or explicitly rejected**
- **Behaviour:** Handle, or reject with a message naming the sheet and cell/row, each of: banner/title
  rows above the header; merged cells in the header; multi-row headers; embedded `Total`/`Subtotal`
  rows in data; blank trailing rows/columns; hidden sheets; multiple sheets (profile selects the sheet);
  protected sheets; formula-only cells (cached values read via `data_only`); error cells (`#REF!`,
  `#DIV/0!`) reported per row and quarantined.
- **Acceptance:** every quirk in the negative corpus (`sample-data/malformed/`, `14` §F.5) produces its
  specific message and never a stack trace.

**FR-IMP-010 · P0 · Phase 1 — CSV handling**
- **Behaviour:** Detect and handle UTF-8 BOM, UTF-8 without BOM, Windows-1252 (with accented text),
  and delimiters comma/semicolon/tab/pipe; the detected delimiter and encoding are shown for
  confirmation before parsing; quoted fields containing delimiters or newlines are parsed correctly.
- **Edge cases:** detection confidence low → force explicit user choice; a single-column file (no
  delimiter) → offered as a "single column" parse.
- **Acceptance:** the encoding/delimiter matrix in `14` passes with correct accented characters and no
  row shifting.

**FR-IMP-011 · P0 · Phase 1 — Value parsing rules per profile**
- **Behaviour:** Per-profile (not per-file) documented rules for: dates (ISO, `dd-mm-yyyy`,
  `mm/dd/yyyy`, Excel serials, date-times, ambiguous formats requiring explicit confirmation);
  numbers (thousands separators, accounting parentheses for negatives, currency symbols, trailing
  `Cr`/`Dr`, text-formatted numbers); fiscal period text (`FY26-P09`); dimension strings
  (`Dept=100|CC=200`) split by a documented parsing rule.
- **Edge cases:** ambiguous date where both interpretations are valid → never guessed silently; the
  user confirms once and the choice is saved to the profile; unparseable value → quarantine with row
  reference (FR-IMP-013).
- **Acceptance:** every parse rule has a worked case in `14`; a changed rule creates a new profile
  version (FR-IMP-026).

**FR-IMP-012 · P0 · Phase 1 — Formula and error-cell policy**
- **Behaviour:** Only cached values are read (`data_only`); a formula cell with no cached value is
  reported as unmapped/unusable for that row; error cells are counted per column and quarantined with
  row references. Policy is stated in the validation report, not implied.
- **Acceptance:** a workbook of formulas saved by Excel imports identically to its value-only twin.

**FR-IMP-013 · P0 · Phase 1 — Row-level validation and quarantine**
- **Behaviour:** Row-level failures are **quarantined**, never dropped: they are written to a review
  sheet attached to the batch (with the original row number, the failing field, the reason and the raw
  values), counted in the validation report, and reviewable in the UI where the user can fix-and-retry
  or accept the remainder. Counts of loaded/quarantined/rejected are always shown together.
- **Edge cases:** 100% of rows failing a check → the import is rejected at file level (FR-IMP-014) with
  a pointer to the check.
- **Acceptance:** the loaded + quarantined + rejected count equals the source row count for every
  import, and the equation is shown in the validation report.

**FR-IMP-014 · P0 · Phase 1 — File-level rejection conditions**
- **Behaviour:** The whole file is rejected (nothing committed) for: unreadable/encrypted file; no
  detectable header; missing required columns after mapping; debit ≠ credit beyond tolerance; duplicate
  column headers that the profile has not renamed; ≥ 90% of rows unmapped; zero data rows (default
  reject, with an explicit "accept as zero-activity period" confirmation path).
- **Acceptance:** every rejection message names the failing check, the offending sheet/row/column, and
  the next action.

**FR-IMP-015 · P0 · Phase 1 — Debit = credit balance check**
- **Behaviour:** Per file, per entity, per period (and overall), sum(debit) must equal sum(credit) at
  minor-unit precision; the documented tolerance (default: exact; a configured tolerance is allowed only
  if recorded in the project settings) and the result per grouping are shown in the validation report.
- **Acceptance:** a file whose debit ≠ credit cannot be committed; the report shows the imbalance amount
  and the top contributing rows.

**FR-IMP-016 · P1 · Phase 1 — Control-total reconciliation**
- **Behaviour:** When the actuals template's optional control-totals block is present, the validation
  report compares file totals vs loaded totals vs client-provided control totals, and shows variances.
  A variance beyond tolerance fails the import or requires an explicit, recorded acceptance.
- **Acceptance:** the decision (fail vs accept-with-record) is documented in `04` and exercised in `14`.

**FR-IMP-017 · P0 · Phase 1 — Duplicate candidate detection at import**
- **Behaviour:** Within a file, candidate duplicates (documented key: vendor/document number + date +
  amount, plus voucher + line where available) are counted, sampled, and listed in the validation
  report; they are not auto-deleted.
- **Acceptance:** the planted duplicate set in the sample data is detected with zero false negatives
  recorded in `expected_exceptions.csv`.

**FR-IMP-018 · P0 · Phase 1 — Cross-batch duplicate detection**
- **Behaviour:** On import of a new batch, previously imported rows are checked against the incoming
  set on the documented dedup keys; overlaps produce a pre-commit report ("N rows already loaded from
  batch <id> on <date>") with options: skip overlapping rows, import anyway (recorded decision), or
  cancel. Overlaps are never silently double-counted.
- **Acceptance:** re-importing last month's file yields a full-overlap report and no double-counting in
  any BvA total.

**FR-IMP-019 · P0 · Phase 1 — Re-import guard**
- **Behaviour:** An identical SHA-256 checksum is blocked with "already imported on <date> as batch
  <id>". A different checksum with overlapping vouchers triggers the FR-IMP-018 report before commit.
- **Acceptance:** both paths produce the exact documented messages and neither commits silently.

**FR-IMP-020 · P0 · Phase 1 — Atomic staged commit**
- **Behaviour:** Rows are staged, fully validated, and only then committed in a single transaction;
  crash, cancel, power loss, or a bad file never leaves half-loaded data. Interrupted staging areas are
  detected on next launch and offered for discard or resume; the app states clearly that no batch was
  committed.
- **Acceptance:** the crash-during-import test in `14` leaves the project with either 0% or 100% of the
  batch, never a partial load.

**FR-IMP-021 · P0 · Phase 1 — Validation report**
- **Behaviour:** Each import produces a saved report with: pass/fail per check, counts
  (loaded/quarantined/rejected), first N offending rows with sheet/row references, balance results,
  control-total variances, check timings, and the batch identity. It is viewable in-app and exportable
  (Excel/CSV), and is retained with the batch.
- **Acceptance:** every validation check in `04` appears in the report with an explicit result, even
  when it was skipped (skipped checks are shown as skipped with a reason).

**FR-IMP-022 · P1 · Phase 1 — Data-quality score**
- **Behaviour:** A composite 0–100 score per batch from weighted validation checks (weights and formula
  owned by `05`), always displayed **alongside** the individual failed checks so a single score can
  never mask a failure; the per-check breakdown is one click away.
- **Acceptance:** a batch with any failed check cannot display a perfect score; the score decomposes
  exactly to its weighted components.

**FR-IMP-023 · P0 · Phase 1 — Import history**
- **Behaviour:** A list of every batch: file name, source type, checksum, row counts, balance result,
  data-quality score, status (staged / committed / voided / rejected), who/when, and a link to the
  validation report and the archived raw file.
- **Acceptance:** no import action can occur without a corresponding history row.

**FR-IMP-024 · P0 · Phase 1 — Void or reverse a batch**
- **Behaviour:** Voiding removes exactly one batch's contribution from the analytic model
  (all-or-nothing), leaves other batches untouched, is audited, marks dependent derived results stale,
  and is blocked for closed periods (FR-PRJ-005).
- **Edge cases:** voiding a batch referenced by an issued pack snapshot → allowed, with a warning that
  the snapshot remains unchanged and the next pack will differ.
- **Acceptance:** after a void, every BvA total equals a fresh import of the remaining batches.

**FR-IMP-025 · P0 · Phase 1 — Immutable raw-file archive with checksum**
- **Behaviour:** The original file is copied into the project's archive folder, read-only, named by
  timestamp + source type + checksum prefix; the checksum and path are recorded in the batch record.
  Every fact row links to its batch, and every batch to its archive file.
- **Acceptance:** drilling any number to "source file" opens/reveals the archived original (or its
  recorded copy), even after the original download is deleted from the Downloads folder.

**FR-IMP-026 · P0 · Phase 1 — Incremental monthly load and mid-year profile versioning**
- **Behaviour:** Loading a new period is additive; previously loaded periods are not reloaded unless
  the user explicitly voids/re-imports. When a source system changes columns mid-year, the profile is
  versioned (new version with an effective-from period), old batches keep the version they were loaded
  with, and the import shows which version is being applied.
- **Acceptance:** two batches loaded with different profile versions both reconcile, and history shows
  which version each used.

**FR-IMP-027 · P0 · Phase 1 — Budget and forecast file validation**
- **Behaviour:** Budget/forecast imports are validated for: duplicate lines on the key; negative amounts
  (allowed/failed per documented rule); coverage matrix (which entity × account × period cells are
  missing, as a percentage, listable); sum-vs-approved-total check when a total is provided; unmapped
  accounts. Results appear in the standard validation report.
- **Acceptance:** a budget with a deliberate gap and a deliberate duplicate reports both, with the
  coverage percentage stated.

**FR-IMP-028 · P1 · Phase 1 — Budget re-import replaces a version atomically**
- **Behaviour:** Re-importing a budget for the same version replaces the previous version's lines in a
  single transaction — never a silent merge. Before commit, a diff summary (old vs new totals by
  entity/period with deltas and the count of changed lines) is shown and must be acknowledged.
- **Acceptance:** after re-import, no orphan lines from the previous version exist, and the diff summary
  is stored with the batch.

**FR-IMP-029 · P1 · Phase 2 — Master-data imports**
- **Behaviour:** Optional import of vendor master/categories, recurring-cost list, and approval
  thresholds, with the same validation/report/archive treatment. Master data is versioned and
  revertable.
- **Edge cases:** master data absent → dependent exception rules auto-disable with a visible notice
  (never false positives).
- **Acceptance:** importing a recurring-cost list enables the "missing recurring cost" rule; removing it
  disables the rule with a notice.

**FR-IMP-030 · P0 · Phase 1 — Long-running import UX**
- **Behaviour:** Import shows stage-by-stage progress (pre-scan → parse → validate → stage → commit)
  with percentage, an ETA based on observed throughput, and a working Cancel at every stage. The UI
  remains responsive throughout (no freeze, no modal block).
- **Edge cases:** cancel during commit → the transaction rolls back and the batch is reported as
  cancelled (never partial); sleep/standby mid-import → resume or fail cleanly with recovery on next
  launch (A1 §G.4).
- **Acceptance:** a 250k-row import reports progress at least every 2 seconds and meets `NFR-002`.

**FR-IMP-031 · P1 · Phase 1 — Sample-project import guard**
- **Behaviour:** Importing into a sample project is refused with a message offering (a) import into a
  new/existing normal project, or (b) convert this project to a normal project (typed confirmation,
  irreversible, audit-logged).
- **Acceptance:** no client data can enter a sample project without the explicit conversion action.

## 7. `FR-BVA` — Budget vs actual analysis (16 FRs)

All BVA screens operate on a shared, always-visible **filter context** (period window, entity/entities,
account range, cost centre/department, project, vendor, statement-line type). Formulas — variance,
variance %, favour*ability*, zero-budget handling, rounding — are owned by `05`; this section specifies
behaviour only.

**FR-BVA-001 · P0 · Phase 2 — BvA matrix at the lowest shared grain**
- **Behaviour:** The primary matrix shows Actual, Budget, Variance (amount and %), and favour*ability*
  at the **lowest grain where both sides exist** (typically period × entity × cost centre × GL
  account). Rows and columns are expandable across the account hierarchy and cost-centre tree; every
  cell is drillable.
- **Edge cases:** budget exists only at GL/month level while actuals are transaction-level → the UI must
  not imply transaction-level budget matching (FR-BVA-013); a cell with budget but no actual shows
  explicitly as "no actuals loaded", not as zero.
- **Acceptance:** every matrix total equals the sum of its drilled rows exactly (no rounding drift, per
  `05` §rounding).

**FR-BVA-002 · P0 · Phase 2 — Period windows: MTD, YTD, PY MTD, PY YTD, TTM**
- **Behaviour:** One window selector switches all analysis between MTD, YTD, PY MTD, PY YTD and TTM
  (trailing 12 periods, where data exists). The active window and its exact date range are always
  visible on screen and in every export header.
- **Edge cases:** no prior-year data → PY options are hidden with an explanatory tooltip (never a blank
  chart); TTM with fewer than 12 loaded periods → shown with the actual number of periods, labelled
  "TTM (7 of 12 periods)".
- **Acceptance:** no screen or export ever shows a period total without naming its window.

**FR-BVA-003 · P0 · Phase 2 — Variance, variance % and favour*ability***
- **Behaviour:** Variance = Actual − Budget (canonical sign convention, `05`); variance % computed per
  the documented zero-budget rule; favour*ability* is direction-aware by statement-line type
  (revenue/expense/memo). Favour*ability* is shown as colour **plus** a `+`/`−`-style sign or a
  `Fav`/`Adv` label so it survives black-and-white printing and colour blindness.
- **Edge cases:** budget = 0 with actual ≠ 0 → `n/a` per `05`, never `inf`; both zero → blank/dash;
  memo/balance-sheet lines → favour*ability* neutral (defined in `05`).
- **Acceptance:** the golden test for each case in `05` §worked examples passes through the UI path.

**FR-BVA-004 · P0 · Phase 2 — Drill-down to transactions with source-file evidence**
- **Behaviour:** Every displayed figure (cell, bar, KPI, exception subject) opens a transaction detail
  list filtered to exactly that figure's rows, showing the source fields, the import batch, and the
  source file (name + checksum, with "reveal archived file"). Drill-down is available at every
  aggregation level down to a single voucher line.
- **Edge cases:** a figure computed from forecast rows (no transactions) → the drill panel states
  "forecast row — method <name>, generated <date>" instead of an empty table; a figure from a closed
  period → shows the snapshot reference.
- **Acceptance:** the sum of drilled rows equals the drilled figure exactly, for every drill entry
  point, in the acceptance test suite.

**FR-BVA-005 · P0 · Phase 2 — BvA bridge/waterfall chart**
- **Behaviour:** A waterfall from Budget to Actual showing the contribution of the top N variance
  drivers (configurable, default 8) plus an "Other" bar, with positive/negative/favourable/unfavourable
  encoding that is not colour-only, and a table view beneath (every chart has a table view).
- **Edge cases:** more drivers than N (grouped into "Other" with a drill-through to the full list);
  zero-variance drivers (excluded, with a note).
- **Acceptance:** the waterfall's start, end and bar sum reconcile exactly to the BvA totals in the
  matrix.

**FR-BVA-006 · P0 · Phase 2 — Trend charts**
- **Behaviour:** Multi-period trends for actual vs budget vs prior year (lines) and variance (bars),
  with the period window and scale label ("₹ in thousands/lakhs") always shown; tooltips expose exact
  values.
- **Edge cases:** sparse periods (gaps shown as gaps, never interpolated silently); a single loaded
  period (chart renders a single point with a note, not an empty axes frame).
- **Acceptance:** chart values equal the corresponding table values for the same filter state.

**FR-BVA-007 · P0 · Phase 2 — Top-N variance views**
- **Behaviour:** Ranked lists of adverse and favourable variances by amount and by %, by account, cost
  centre, vendor and entity, with N configurable and each row drillable.
- **Acceptance:** ranking ties are broken deterministically (documented tie-break), so two runs produce
  identical order.

**FR-BVA-008 · P1 · Phase 4 — Three-way view and forecast accuracy columns**
- **Behaviour:** Actual vs Budget vs Forecast in one view; for closed periods, Forecast vs Actual
  columns with signed error; forecast accuracy metrics displayed per period and per account group
  (formulas in `05`/`07`). Feeds commentary (FR-XC-001).
- **Edge cases:** no forecast version generated for a period → column shows "not generated" with a CTA.
- **Acceptance:** signed-error arithmetic reproduces the `05` worked examples exactly.

**FR-BVA-009 · P1 · Phase 2 — Hierarchy rollups with tie-to-children guarantee**
- **Behaviour:** Expand/collapse across the COA parent levels and the cost-centre/department tree; a
  parent value always equals the exact sum of its visible children (a tested invariant).
- **Edge cases:** an account assigned to a parent but no child (shown as a direct child row);
  unassigned accounts (grouped under a visible "Unmapped" node, never silently dropped).
- **Acceptance:** an automated invariant test over the full sample dataset finds zero violations.

**FR-BVA-010 · P1 · Phase 2 — KPI/ratio library**
- **Behaviour:** KPI cards (gross margin %, Opex %, Opex-to-revenue, budget-burn %, plus the enabled
  subset of the catalogue in `05`) with current value, budget/target comparison, trend sparkline, and
  drill-through to contributing accounts. Each KPI's formula and divide-by-zero behaviour are owned by
  `05`.
- **Edge cases:** denominator zero → `n/a` (never `inf` or a crash); KPI requiring absent data (e.g.
  headcount — parked, `BL-016`) is not shown at all.
- **Acceptance:** every displayed KPI matches its `05` definition on the golden dataset.

**FR-BVA-011 · P0 · Phase 2 — Export what you see**
- **Behaviour:** Every table view and chart's table view exports exactly the current filter, sort and
  visible columns to Excel/CSV, with the filter context, generation timestamp and source batch IDs in
  the header block.
- **Acceptance:** a cross-artifact consistency test (Addon 3 §F.4) parses the export and asserts equality
  with the on-screen values.

**FR-BVA-012 · P1 · Phase 2 — Search**
- **Behaviour:** One search box finds vouchers, vendors, descriptions and accounts across loaded
  periods; results are grouped by type with counts, show the source batch per row, and land in a
  pre-filtered transaction list. Performance target is owned by `14`.
- **Edge cases:** searches on a partially loaded project state which periods were searched.
- **Acceptance:** a known voucher from the sample data is found in ≤ 2 interactions.

**FR-BVA-013 · P0 · Phase 2 — Comparability guard**
- **Behaviour:** The UI never displays a BvA figure where the two sides are not at the same grain; it
  states the grain of the comparison on screen ("Budget available at: month × account") and in exports.
  Where budget is coarser, actuals are rolled up to the budget grain for comparison and the fact is
  disclosed.
- **Acceptance:** the acceptance suite includes a coarse-budget scenario with no misrepresenting screen.

**FR-BVA-014 · P0 · Phase 2 — Grouped entity totals are labelled as simple sums**
- **Behaviour:** Any consolidated total across entities carries a visible label "Simple sum — no
  eliminations" (PRD §8) in the UI, Excel and PPT.
- **Acceptance:** the label appears wherever entity aggregation occurs; a test asserts its presence.

**FR-BVA-015 · P0 · Phase 2 — Shared filter context**
- **Behaviour:** Filters persist across Analyze screens while the user navigates, are always visible in
  a filter bar, are resettable in one action, and are recorded into every export and commentary draft.
  Filters cannot produce an invalid state (e.g. no periods selected).
- **Acceptance:** navigating between matrix, bridge, trends and drill preserves the context exactly.

**FR-BVA-016 · P0 · Phase 2 — Empty, loading and error states**
- **Behaviour:** Explicit states for: no budget loaded (empty state + "Import budget" CTA; variance
  rules disabled with a notice; never variance = 0); no prior year (PY hidden with a note); first-ever
  period (PY/TTM hidden, run-rate forecasts disabled with an explanatory hint — never a crash or a
  blank chart); no actuals for the selected filter (explicit empty state, not zeros); loading
  (skeletons, never a frozen grid); error (plain-language message + hint per FR-XC-006).
- **Acceptance:** every state above is exercised by a test on the sample project and matches §16.

## 8. `FR-EXC` — Exception engine and register (20 FRs)

Rule logic, thresholds, severities and sample cases are owned by `06_EXCEPTION_RULES_CATALOG.md`; this
section specifies engine and workflow behaviour.

**FR-EXC-001 · P0 · Phase 3 — Rule run**
- **Behaviour:** The engine runs the enabled rule set over the loaded data (optionally scoped to a
  period), with progress, cancel, and a run summary (rules run, exceptions raised, superseded,
  unchanged, skipped-with-reason). Runs are deterministic: identical data + settings + rule version
  produce identical results.
- **Edge cases:** no actuals loaded (run blocked with a CTA); stale derived state after mapping changes
  (run prompts for the required re-run).
- **Acceptance:** two consecutive runs on unchanged data produce byte-identical exception sets.

**FR-EXC-002 · P0 · Phase 3 — Exception register**
- **Behaviour:** A sortable, filterable register showing: rule ID and name (with severity), period,
  entity, subject (account/cost centre/vendor/voucher), amount at risk, owner, status, days open,
  first-seen and last-seen dates, evidence link, and notes count. Filters include severity, status,
  owner, rule, entity, period and aging bucket.
- **Acceptance:** every raised exception is visible in the register with a working drill path to its
  subject rows; counts on screen equal exported counts.

**FR-EXC-003 · P0 · Phase 3 — Deterministic evaluation only**
- **Behaviour:** All rule evaluation is deterministic code. AI may group, summarise or draft text about
  exceptions (FR-AI-004) but may never raise, lower, close, or alter an exception.
- **Acceptance:** disabling AI leaves the exception set identical.

**FR-EXC-004 · P0 · Phase 3 — Stable exception identity**
- **Behaviour:** Identity = `rule_id + subject_key` (the subject key is defined per rule in `06`).
  Re-running after mapping/threshold changes updates the same exception, never creates a duplicate.
- **Acceptance:** the worked scenario in Addon 2 §D.1 (raise → tune threshold → re-run → status
  preserved) passes as a golden test.

**FR-EXC-005 · P0 · Phase 3 — Re-run preserves workflow state**
- **Behaviour:** Re-running never wipes workflow state: open stays open, closed stays closed. A
  previously closed exception that is flagged again receives a visible **"flagged again"** badge and
  remains closed until a human reopens it. Full history is retained per key.
- **Acceptance:** the above scenario (closed → re-flagged) shows the badge, keeps status Closed, and
  records the re-flag event in history.

**FR-EXC-006 · P0 · Phase 3 — Status workflow**
- **Behaviour:** Lifecycle `Open → In Review → Explained → Corrected → Closed`, plus explicit `Reopened`
  (with reason) and `Not applicable` (with reason) paths. Status changes are timestamped, attributed to
  the session user, and audit-logged. Closed is human-only; nothing auto-closes.
- **Edge cases:** "Corrected" requires a note (what was changed and when) — enforced by the UI.
- **Acceptance:** every transition is reversible only through a recorded action; no silent status
  change exists in the audit log.

**FR-EXC-007 · P0 · Phase 3 — Owner assignment**
- **Behaviour:** Owners are auto-assigned from the cost-centre/account-to-owner mapping (master data),
  with manual override always available. Assignments are visible in the register, in the owner-wise
  export (FR-EXC-017) and in the evidence bundle.
- **Edge cases:** no mapping for a subject → owner shows "Unassigned" and appears in a dedicated filter
  so nothing is lost.
- **Acceptance:** bulk owner change (FR-EXC-010) writes one audit entry per affected exception.

**FR-EXC-008 · P0 · Phase 3 — Notes with history**
- **Behaviour:** Free-text notes per exception with author and timestamp, append-only history, and a
  visible edit trail. Notes never overwrite previous text silently.
- **Acceptance:** a note edited twice shows all three versions in order.

**FR-EXC-009 · P1 · Phase 3 — Aging and overdue**
- **Behaviour:** Days-open per exception, aging buckets `0–7 / 8–30 / 31+`, and an overdue highlight
  driven by a configurable per-severity target (defaults in `06`).
- **Acceptance:** aging is computed from `first_seen` in period terms (not wall-clock alone) and matches
  the exported value.

**FR-EXC-010 · P1 · Phase 3 — Bulk operations**
- **Behaviour:** Multi-select supports bulk status change and bulk owner assignment, with a
  confirmation showing the count and the target state, and one audit entry per affected item.
- **Edge cases:** mixed selection where a transition is invalid for some items (the invalid subset is
  listed and skipped, not silently included).
- **Acceptance:** a bulk operation on 20 exceptions produces exactly 20 audit entries.

**FR-EXC-011 · P0 · Phase 3 — Severity**
- **Behaviour:** High / Medium / Low with badges that carry text (not colour alone), sortable and
  filterable; severity defaults come from `06` and per-rule overrides are possible.
- **Acceptance:** severity appears identically in the register, exports and evidence bundles.

**FR-EXC-012 · P0 · Phase 3 — Per-project rule configuration**
- **Behaviour:** Each rule can be enabled/disabled per project and its thresholds edited (with the
  default shown and a "reset to default" action); changes are versioned with history and revert, and
  mark derived results stale.
- **Acceptance:** disabling a rule removes its exceptions on the next run and records the configuration
  change in the audit log.

**FR-EXC-013 · P1 · Phase 3 — Global materiality**
- **Behaviour:** A global materiality setting (percentage of budget and/or absolute floor) feeds the
  default thresholds of amount-based rules; a per-rule override always wins. The effective value used
  for every raise is recorded on the exception.
- **Acceptance:** changing global materiality alters only the rules without overrides, and each new
  exception states the effective threshold.

**FR-EXC-014 · P0 · Phase 3 — Master-data dependencies degrade gracefully**
- **Behaviour:** Rules that need master data (recurring-cost list, approval thresholds, vendor
  categories, prior-period baselines, owner mapping) auto-disable with a visible notice when the data
  is absent — never a false positive and never a silent skip. The notice links to the master-data screen.
- **Acceptance:** with master data removed, the affected rules do not run and are listed as
  "disabled — missing input".

**FR-EXC-015 · P1 · Phase 3 — Rule effectiveness analytics**
- **Behaviour:** Per rule: times raised, share closed as explained, average days to close, last
  threshold tuning, and false-positive feedback captured from closures marked "not applicable".
- **Acceptance:** the dashboard reconciles with the register history for the same period.

**FR-EXC-016 · P1 · Phase 3 — Evidence bundle**
- **Behaviour:** One action per exception produces a workbook (or zip) containing: the subject rows, the
  relevant validation report, the mapping profile version applied, the effective thresholds, the audit
  trail, and a header stating the rule, the period, and the disclaimer. Ready to send to an accounting
  team without further assembly.
- **Acceptance:** the bundle opens, names its sources, and its row totals reconcile to the exception's
  subject rows.

**FR-EXC-017 · P1 · Phase 3 — Owner-wise distribution**
- **Behaviour:** Export the register grouped per accounting owner (Excel/CSV) plus a copyable
  plain-text summary suitable for pasting into Teams/email, listing per-owner counts by severity and the
  most material items.
- **Acceptance:** the plain-text summary contains no colour or formatting dependencies and matches the
  exported counts.

**FR-EXC-018 · P0 · Phase 3 — Register export**
- **Behaviour:** Full register export to Excel with the specified layout (`11`), current filters
  applied and stated, plus an unfiltered "all exceptions" sheet.
- **Acceptance:** export row count equals register row count for the same filter.

**FR-EXC-019 · P0 · Phase 3 — Canonical wording**
- **Behaviour:** Everywhere an exception is presented: *"Potential exception — requires accounting
  review."* Never "error", "mistake", "wrong entry", or a definitive claim. Rule names describe the
  pattern, not a verdict (e.g. "Possible duplicate invoice", not "Duplicate invoice").
- **Acceptance:** a wording lint over UI strings, exports and PPT text finds no forbidden phrasing.

**FR-EXC-020 · P0 · Phase 3 — Rule-run performance**
- **Behaviour:** A full rule run over 250k rows completes within `NFR-009` (≤ 60 s), measured by the
  perf script and re-baselined at every gate.
- **Acceptance:** the perf test passes with the recorded baseline.

## 9. `FR-FC` — Rolling forecast (9 FRs)

Forecast mathematics, method definitions and worked examples are owned by `07`.

**FR-FC-001 · P0 · Phase 4 — Locked actuals, forecasted remainder**
- **Behaviour:** Closed periods are locked to actuals; forecast methods apply only to open/remaining
  periods of the fiscal year. The forecast view always shows which periods are actual, which are
  forecast, and the boundary date.
- **Acceptance:** no forecast value can overwrite or blend into a closed period's actuals.

**FR-FC-002 · P0 · Phase 4 — Four deterministic methods**
- **Behaviour:** Methods: (a) remaining-budget spread, (b) run-rate (average of the last N actual
  months, N configurable, default 3), (c) 3-month average, (d) manual override. A method can be set
  globally, per account group, and per line; the most specific setting wins. Each line records the
  method actually used.
- **Edge cases:** insufficient actual months (e.g. first period) → method disabled with an explanatory
  hint, and the line requires a manual override or another method; N > available months → clamped with
  a visible notice.
- **Acceptance:** every method reproduces its `07` worked example exactly, including rounding.

**FR-FC-003 · P1 · Phase 4 — Scenarios**
- **Behaviour:** Base / Best / Worst scenarios, each a named forecast version with its own assumptions
  (adjustment percentages per driver or per account group, or per-line overrides). Scenarios are
  comparable side by side and in the deck (`12`).
- **Edge cases:** a scenario without overrides equals Base by construction and is labelled as such.
- **Acceptance:** switching scenario changes only forecast values, never actuals or budget.

**FR-FC-004 · P0 · Phase 4 — Forecast provenance**
- **Behaviour:** Every forecast row carries method, scenario/version, "generated at" timestamp, the
  generating user, and the driver reference (e.g. which actual months were averaged). A number can be
  explained months later from the row itself.
- **Acceptance:** any forecast figure can be traced in ≤ 2 clicks to its method, inputs and generation
  time.

**FR-FC-005 · P0 · Phase 4 — Actuals are never overwritten**
- **Behaviour:** Forecasts live in their own fact table and version; regenerating or deleting a forecast
  never touches actuals or budget.
- **Acceptance:** a storage-level test asserts forecast writes cannot modify actual rows.

**FR-FC-006 · P1 · Phase 4 — Manual override with audit**
- **Behaviour:** Any line can be overridden with a value and a mandatory reason; overrides are listed in
  a filterable "overrides" view, are versioned, and are highlighted in exports.
- **Acceptance:** an overridden line reports method = "manual override" plus its reason.

**FR-FC-007 · P1 · Phase 4 — Forecast accuracy report**
- **Behaviour:** For closed periods, compare forecast vs actual with error, absolute error, signed bias
  and MAPE-lite metrics (formulas in `05`/`07`), by period, entity, account group and method. Feeds
  method-choice guidance (FR-FC-008) and commentary (FR-XC-001).
- **Edge cases:** actual = 0 → metric renders `n/a` per the divide-by-zero rule, never `inf`.
- **Acceptance:** metrics reproduce the `05` worked examples on the golden dataset.

**FR-FC-008 · P2 · Phase 4 — Method-choice guidance**
- **Behaviour:** A non-blocking suggestion panel showing which method has historically been most
  accurate per account group, with a one-click "apply suggestion to these lines".
- **Acceptance:** guidance never changes a forecast without an explicit user action.

**FR-FC-009 · P1 · Phase 4 — Forecast versions and comparison**
- **Behaviour:** Forecasts are versioned (generate → compare → lock). A locked version is read-only and
  referenced by issued packs; a new generation creates a new version. Comparison view: forecast vs
  budget vs actual for the same filter context.
- **Acceptance:** an issued pack always references a locked version, and later generations do not alter
  it.

## 10. `FR-XL` — Excel output pack (9 FRs)

Sheet-by-sheet layouts, number formats, conditional formatting, widths, freeze panes, autofilters and
print setup are owned by `11_EXCEL_OUTPUT_SPEC.md`. This section specifies behaviour.

**FR-XL-001 · P0 · Phase 5 — Generate the Excel pack**
- **Behaviour:** Generates one workbook from the current filter context containing: BvA summary,
  transaction detail (drill of the summary), exception register, forecast summary, import
  reconciliation, and audit-trail sheet. The sheet set matches `11` exactly, and any sheet omitted is
  omitted for a stated, documented reason (e.g. no forecast version generated).
- **Acceptance:** the generated workbook opens in Excel with no repair prompt and every sheet matches
  its `11` layout contract.

**FR-XL-002 · P0 · Phase 5 — Format compliance**
- **Behaviour:** All specified formatting is applied: header styles, number formats (₹, 2 dp; % 1 dp;
  negatives in parentheses), centralised conditional formatting (favourability, severity, variance
  thresholds) from the single rule set in `08`, frozen panes, autofilters, column widths, tab colours,
  print areas and a footer carrying the disclaimer.
- **Acceptance:** a structural test (`14`) asserts formats, frozen panes, filters and the footer on the
  golden output.

**FR-XL-003 · P0 · Phase 5 — Refreshable from the project**
- **Behaviour:** Each pack records its filter context, pack version and source batch IDs; a "Refresh
  this pack" action re-generates the same workbook from current data and states exactly what changed
  (period, batch IDs, row counts, values-changed count).
- **Acceptance:** refreshing a pack after a data change produces a workbook whose values match the
  current engine values, with the change summary attached.

**FR-XL-004 · P0 · Phase 5 — File naming and collision policy**
- **Behaviour:** File names follow `<Project>_<Entity>_<Period>_<Pack>_<vN>.xlsx`. If a file exists at
  the target path, the user is prompted to overwrite or keep both (next `vN`); there is never a silent
  overwrite and never a silent overwrite-by-rename.
- **Acceptance:** the naming convention and the collision prompt are both covered by tests.

**FR-XL-005 · P0 · Phase 5 — Sheet row caps**
- **Behaviour:** Detail sheets respect Excel's 1,048,576-row limit: the export either filters the detail
  (with the applied filter stated in the sheet header) or splits across numbered sheets, and it states
  counts exported vs total. Exceeding the cap never produces a truncated sheet without notice.
- **Acceptance:** an export of a >1M-row detail set is either explicitly filtered or split, with the
  counts and the rule stated on the sheet.

**FR-XL-006 · P0 · Phase 5 — Stamping**
- **Behaviour:** Every exported workbook is stamped with generation timestamp, project and filter
  context, pack version (or "unissued draft"), source import batch IDs, app version and schema version,
  and the short-form disclaimer on every sheet footer.
- **Acceptance:** the stamp is present and machine-readable (a dedicated header block) for the
  cross-artifact consistency test.

**FR-XL-007 · P1 · Phase 5 — Evidence bundle workbook layout**
- **Behaviour:** The evidence bundle (FR-EXC-016) uses its own specified layout with subject rows, the
  rule definition and effective threshold, the validation report extract, mapping version, and audit
  trail.
- **Acceptance:** the bundle's totals reconcile to the exception's subject rows.

**FR-XL-008 · P0 · Phase 5 — Cross-artifact consistency**
- **Behaviour:** For a fixed filter state, numbers in the Excel pack equal the values rendered in the UI
  and the PPT deck, exactly, at display precision (Addon 3 §F.4). Formatting conventions are identical
  across app, Excel and PPT.
- **Acceptance:** the cross-artifact consistency test parses the workbook and asserts equality.

**FR-XL-009 · P2 · Phase 5 — Print/PDF readiness**
- **Behaviour:** Every sheet has a defined print area, orientation, fit-to-width, repeating header row
  and footer; "Export to PDF" uses those settings.
- **Acceptance:** a printed/PDF pack is legible in black and white (P19) with no truncated columns.

## 11. `FR-PPT` — PowerPoint management pack (9 FRs)

Slide-by-slide structure, placeholder geometry, fonts, colours and character budgets are owned by
`12_POWERPOINT_OUTPUT_SPEC.md`.

**FR-PPT-001 · P0 · Phase 5 — Generate the six-slide deck**
- **Behaviour:** Exactly the six slides specified in `12`: cover + period + source files; executive KPIs;
  BvA bridge/waterfall; top variances with drivers (+ AI draft commentary when enabled and approved);
  exceptions and control risks; forecast and outlook. Content is driven by the current filter context.
- **Acceptance:** the generated deck contains exactly the specified slides and placeholders, and every
  chart/table is native.

**FR-PPT-002 · P0 · Phase 5 — Native, editable output**
- **Behaviour:** All text is in text frames, all tables are PowerPoint tables, all charts are native
  PowerPoint charts (via `python-pptx`). No screenshots, no images of tables, no embedded ECharts
  renders.
- **Acceptance:** a structural test opens the deck and asserts the type of every shape; a human can edit
  every value in PowerPoint.

**FR-PPT-003 · P0 · Phase 5 — Generation performance and UX**
- **Behaviour:** Deck generation completes within `NFR-004` (≤ 15 s) with a progress indicator and a
  working Cancel; the UI remains responsive.
- **Acceptance:** the perf test passes; cancelling mid-generation leaves no partial file at the target
  path.

**FR-PPT-004 · P0 · Phase 5 — Text fitting**
- **Behaviour:** Every placeholder has a character budget (`12`); long text is trimmed by a documented
  priority order with ellipsis, and never overflows its frame or overlaps another element. Trimmed text
  is retrievable from the source (the UI shows the full text; the Excel pack contains it in full).
- **Acceptance:** the long-commentary fixture renders within frames with no overlap (structural test in
  `14`).

**FR-PPT-005 · P2 · Phase 6 — Client base deck and house style**
- **Behaviour:** Optionally load a client-supplied `.pptx` as the base; the app replaces text/table
  placeholders in the client's layouts and matches their fonts/colours. Missing placeholders are
  reported (with the option to fall back to the built-in deck) instead of producing a broken slide.
- **Acceptance:** with a supplied base deck, the output uses the client's masters and reports any
  placeholder mismatch explicitly.

**FR-PPT-006 · P1 · Phase 5 — Branding**
- **Behaviour:** The configured logo file and two brand colours are applied to the specified
  placeholders/series; branding is configurable in Settings and defaults to the PRD placeholders.
- **Acceptance:** changing the brand colours in Settings changes the deck on the next generation with no
  code change.

**FR-PPT-007 · P1 · Phase 5 — Deterministic element ordering**
- **Behaviour:** Shapes are added in a documented, stable order so regenerating the same deck produces
  the same element order (z-order and XML order), keeping diffs and reviews sane.
- **Acceptance:** generating twice from the same context produces structurally identical decks
  (modulo timestamp fields).

**FR-PPT-008 · P1 · Phase 6 — AI commentary in the deck**
- **Behaviour:** AI draft commentary enters a slide only after the user explicitly approves that draft
  (FR-XC-001); it is labelled as an AI draft in the speaker notes and in the slide text per `12`; an
  unapproved draft is never used.
- **Acceptance:** with AI enabled but no approval, the deck contains no AI text.

**FR-PPT-009 · P0 · Phase 5 — Stamping and disclaimer**
- **Behaviour:** Cover and/or footer show period, project, pack version, generation timestamp, source
  batch IDs, and the short-form disclaimer; the full disclaimer is reachable from the back slide.
- **Acceptance:** the stamp and disclaimer assertions are part of the structural test.

## 12. `FR-AI` — Optional AI commentary and suggestions (14 FRs)

Provider configuration, prompt templates, schemas, redaction rules, caps and provenance are owned by
`10_AI_INTEGRATION_SPEC.md`. Every AI feature is optional, off by default, and never on the money path.

**FR-AI-001 · P0 · Phase 6 — Optional, off by default, keyless-capable**
- **Behaviour:** AI is disabled until a key is configured. With no key, every AI surface still works
  using the deterministic rule-based narrative generated from the same driver data (FR-AI-013).
- **Acceptance:** a full sample-project walkthrough passes with AI never enabled.

**FR-AI-002 · P0 · Phase 6 — Bring-your-own-key configuration**
- **Behaviour:** Settings accepts an Azure OpenAI endpoint/key/deployment (preferred) or an
  OpenAI-compatible base URL/key/model. The key is stored via Windows DPAPI/Credential Manager
  (`13`), never in a project file, never in the repo, never in plain text. A "Test connection" action
  reports success/failure with a plain-language hint.
- **Acceptance:** the key never appears in any project backup, log, diagnostics bundle, or exported file.

**FR-AI-003 · P1 · Phase 6 — Key rotation and revocation**
- **Behaviour:** Replacing the key purges the old value from config and memory, is audit-logged without
  key material, and requires no restart. Revocation steps are documented for the client (`23`).
- **Acceptance:** after rotation, the old key fails and the new one works; logs contain no key material.

**FR-AI-004 · P1 · Phase 6 — Four AI features**
- **Behaviour:** (a) variance commentary draft, (b) mapping suggestion with evidence, (c) exception
  grouping/summary for the period, (d) follow-up message draft for an accounting owner. Each has a
  versioned prompt template (`PROMPT-01…04`, full texts in `10`), a defined input set, a JSON output
  schema, and a worked example on sample data.
- **Acceptance:** each feature produces schema-valid output on the sample project and links to evidence
  rows.

**FR-AI-005 · P0 · Phase 6 — Evidence linkage and confidence**
- **Behaviour:** Every AI output lists the evidence it used (exception IDs, transaction/voucher
  references, aggregation scope) and a confidence indicator; the UI links each claim to the underlying
  rows.
- **Acceptance:** an AI claim with no matching engine evidence cannot be displayed as-is (FR-AI-010).

**FR-AI-006 · P0 · Phase 6 — Strict schema validation**
- **Behaviour:** Responses must validate against the documented JSON schema. On schema failure,
  truncation, timeout, or refusal, the feature falls back with a clear message and logs the failure
  (without client data beyond what was sent).
- **Acceptance:** a malformed-response fixture triggers the fallback path, never a crash or raw JSON
  shown to the user.

**FR-AI-007 · P0 · Phase 6 — Redaction and minimum data**
- **Behaviour:** Vendor names/IDs are masked per the configurable redaction setting before any call; only
  the minimum filtered rows needed for the task are included; full raw tables are never sent. The exact
  payload composition rules are owned by `10`.
- **Acceptance:** a payload-inspection test asserts masked fields and the row-count cap for every
  feature.

**FR-AI-008 · P0 · Phase 6 — Prompt-injection defence**
- **Behaviour:** Imported text is treated as hostile data: wrapped in delimited data blocks, system
  prompt states that content inside data must never be obeyed, HTML/control characters stripped, field
  lengths capped. A planted malicious description in the sample data must not alter behaviour.
- **Acceptance:** the injection test case in `14` passes (no instruction following, no data exfiltration
  attempt).

**FR-AI-009 · P0 · Phase 6 — Caps, usage log and caching**
- **Behaviour:** Configurable per-call and monthly token/cost caps (hard stop with a clear message),
  a local usage log (timestamp, model, prompt version, input rows, tokens in/out, estimated cost)
  visible in Settings, and caching to avoid duplicate calls for identical inputs.
- **Acceptance:** exceeding the cap blocks further calls with a message; the usage log reconciles with
  the number of calls made.

**FR-AI-010 · P0 · Phase 6 — Number-mismatch policy**
- **Behaviour:** A mismatch check runs on every AI text: any number in the text that does not match an
  engine value for the same context is stripped or the text is flagged for review (single documented
  stance in `10`). AI text can never introduce a number the engine did not compute.
- **Acceptance:** a fixture with an invented number is stripped/flagged, never displayed as fact.

**FR-AI-011 · P1 · Phase 6 — Draft provenance and history**
- **Behaviour:** Every draft is stamped with model, prompt-template version, timestamp and inputs;
  regeneration creates a new draft while previous drafts remain in history; editing a prompt template
  never mutates existing drafts; the user chooses which draft is used.
- **Acceptance:** draft history is visible and immutable; the PPT uses only the approved draft.

**FR-AI-012 · P0 · Phase 6 — Labelling**
- **Behaviour:** All AI text is prefixed/labelled **"AI draft — review before use."** in the UI, the
  Excel pack and the deck, and is visually distinguishable without relying on colour alone.
- **Acceptance:** a lint/structural test asserts the label wherever AI text appears.

**FR-AI-013 · P0 · Phase 6 — Offline/keyless fallback narrative**
- **Behaviour:** With no key (or AI disabled), the same commentary surfaces are produced by
  deterministic templates over the same driver data (top variances, largest exceptions, forecast
  movement), clearly labelled as rule-based rather than AI.
- **Acceptance:** the offline walkthrough produces a usable, correctly labelled narrative for the sample
  month.

**FR-AI-014 · P0 · Phase 6 — Data boundary and model pinning**
- **Behaviour:** No data leaves the machine except to the configured endpoint, and only when the user
  triggers an AI action. The default model is pinned; if a pinned model is retired, the app shows a
  clear notice and follows the documented fallback order (never a silent model switch that changes
  output character). A data-residency statement is shown in Settings.
- **Acceptance:** with AI disabled, network monitoring during the offline walkthrough shows zero
  outbound calls.

## 13. `FR-SET` — Settings, master data and display (12 FRs)

**FR-SET-001 · P0 · Phase 1 — Settings screen sections**
- **Behaviour:** One Settings screen with sections: Data & storage, Mappings, Master data, Thresholds &
  rules, Display & locale, Branding, AI, Backups, About/Diagnostics. Machine-level settings (AI key,
  theme, data directory, telemetry = off) are separated from project-level settings (fiscal calendar,
  currency/units, mappings, thresholds, master data, branding, rule enablement) per the configuration
  layering in `09`.
- **Acceptance:** the layering is visible in the UI (machine vs project), and project settings travel
  with a project backup while secrets never do.

**FR-SET-002 · P0 · Phase 1 — Mapping management**
- **Behaviour:** Create, edit, clone, rename, export/import and version mapping profiles; each profile
  keeps full history with timestamp and old→new values and supports revert. Profiles show which batches
  used which version.
- **Acceptance:** reverting a profile restores the previous mapping exactly and marks derived results
  stale.

**FR-SET-003 · P0 · Phase 3 — Master data screens**
- **Behaviour:** Editable, versioned, revertable tables for vendor categories, recurring-cost list,
  approval thresholds, and owner assignments (cost centre/account → owner). Import/export supported;
  every change is timestamped with old→new values.
- **Acceptance:** disabling a master-data-dependent rule is automatic when its table is empty
  (FR-EXC-014).

**FR-SET-004 · P0 · Phase 3 — Rule configuration**
- **Behaviour:** Per-rule enable/disable and threshold editing, with defaults shown, reset-to-default,
  and history. Changing a threshold records the change and marks derived results stale.
- **Acceptance:** the stale banner appears after a rule change and clears after a re-run.

**FR-SET-005 · P0 · Phase 1 — Fiscal calendar configuration**
- **Behaviour:** Year start, period codes/labels and period count (12 or 4-4-5) are configured per
  project; all period logic derives from this calendar (no hardcoded calendar months anywhere).
- **Edge cases:** changing the calendar after data is loaded requires a validated remap with a preview
  of affected periods and a warning; it is never silent.
- **Acceptance:** the fiscal-calendar tests in `05` pass with a non-January year start.

**FR-SET-006 · P0 · Phase 1 — Currency and unit display**
- **Behaviour:** Reporting currency symbol, unit scale (`₹` whole, thousands, lakhs), digit grouping
  (Indian lakh/crore vs international), decimal places, and negatives-in-parentheses toggle — all per
  project.
- **Acceptance:** `₹ 1,23,456` and `₹ 123,456` both render correctly per the setting and match exports.

**FR-SET-007 · P0 · Phase 1 — Uniform display locale**
- **Behaviour:** The display settings apply identically to the app, the Excel pack and the PPT deck
  (date format default `dd-mm-yyyy`), enforced by the cross-artifact consistency test.
- **Acceptance:** a locale change is reflected in all three artefacts for the same filter state.

**FR-SET-008 · P1 · Phase 5 — Branding settings**
- **Behaviour:** Product name override, logo file, and two brand colours; changing them affects the deck,
  the Excel header block and the app header on next render, with a contrast check (WCAG AA) and a
  documented fallback variant when a colour fails.
- **Acceptance:** branding changes never require a code change or a reinstall.

**FR-SET-009 · P0 · Phase 1 — Storage locations and sync detection**
- **Behaviour:** Project storage defaults to `%LOCALAPPDATA%\FP&A Month-End Copilot\`; the app detects
  when a chosen path is inside a known syncing folder (OneDrive/Known Folder Move) and warns about
  lock/performance risks with a "use the default instead" action. Export paths may default to Documents
  but carry the same warning when synced.
- **Acceptance:** the OneDrive-path test in `14` produces the warning and the app still functions.

**FR-SET-010 · P0 · Phase 2 — Stale-derived indicator**
- **Behaviour:** Any change to mappings, thresholds, master data, or loaded data marks derived results
  (aggregates, BvA, exceptions, forecasts) stale and raises a visible "Re-run required" banner that
  names what changed and which results are affected. Stale numbers are never presented as current.
- **Acceptance:** the stale-indicator test in `14` passes for each change type.

**FR-SET-011 · P0 · Phase 1 — Version history and revert**
- **Behaviour:** Every user-editable artefact (mappings, thresholds, master data, forecast assumptions,
  prompt templates, branding) keeps history with timestamp and old→new value and supports revert, with
  the reverted state itself recorded as a new version.
- **Acceptance:** the version-history test covers each artefact type; reverting is always possible from
  the UI.

**FR-SET-012 · P2 · Phase 3 — Audit log viewer**
- **Behaviour:** A filterable local audit log (action, object, timestamp, before→after, session) with
  export; retention configurable. Never contains secrets, amounts or vendor names in log text.
- **Acceptance:** the log policy test in `14` asserts no amounts/vendor names appear in log files.

## 14. `FR-XC` — Cross-cutting behaviour (16 FRs)

**FR-XC-001 · P1 · Phase 5 — Commentary workflow**
- **Behaviour:** Two levels — per-variance-line commentary and a per-period executive narrative (used on
  the deck's executive slide). Text can be typed by the user, drafted by AI, or generated by the
  rule-based fallback; every save creates a version (author, timestamp, old→new). Drafts can be edited
  freely before inclusion.
- **Acceptance:** every commentary change is versioned and attributable; the current text is what the
  pack uses.

**FR-XC-002 · P0 · Phase 5 — Commentary locks on issuance**
- **Behaviour:** Issuing a pack freezes the snapshots and locks the commentary included in it; any
  post-issue edit requires a re-issue (new pack version). Locked text is read-only in the UI with a
  "create a new version to edit" action.
- **Acceptance:** the issue → lock → edit-blocked → re-issue flow passes as a test.

**FR-XC-003 · P1 · Phase 5 — Pack issuance register**
- **Behaviour:** "Issue pack" increments the pack version, records issue date, recipients (typed list)
  and the frozen snapshot reference, and marks the pack immutable. The register lists every issued
  version per period with its files, snapshot, and status; exports carry the pack version.
- **Acceptance:** issued packs cannot be mutated; the register reconciles with the exported files.

**FR-XC-004 · P0 · Phase 1 — About / Diagnostics screen**
- **Behaviour:** Shows app version, build date, schema version, data folder (with a reveal action),
  storage used, last diagnostics export, and actions: "Export diagnostics zip", "Check for updates"
  (manual: shows the latest known version and a link; no auto-update), "Restore sample project", and the
  full advisory disclaimer.
- **Acceptance:** the screen answers "which version, where is my data, how do I get help" without
  leaving the app.

**FR-XC-005 · P0 · Phase 1 — Diagnostics bundle with redaction**
- **Behaviour:** The diagnostics zip contains metadata only by default (versions, config minus secrets,
  log tail, column headers, row counts, timing summaries). Financial values or data rows are included
  only after an explicit, labelled opt-in, with the consequence stated before export. Bundle size cap is
  `NFR-010`. Contents are listed in the UI and documented in `23`.
- **Acceptance:** a default bundle contains no amounts or vendor names (asserted by test).

**FR-XC-006 · P0 · Phase 1 — Global error handling**
- **Behaviour:** A global handler catches every unhandled error and shows a plain-language dialog:
  what happened, what was **not** lost (be explicit), one recommended action, and a "Copy details"
  button. Raw tracebacks never reach the UI; they are written to the log for support.
- **Acceptance:** the fault-injection tests in `14` produce readable dialogs, never tracebacks.

**FR-XC-007 · P0 · Phase 1 — Logging policy**
- **Behaviour:** Logs are written under `%APPDATA%`, rotate at the documented size/age limits
  (`NFR-011`), and contain no secrets, no financial amounts and no vendor names in normal operation.
  Log level is configurable for support.
- **Acceptance:** the log-content test asserts the exclusions.

**FR-XC-008 · P0 · Phase 1 — Crash recovery and job resumption**
- **Behaviour:** After a crash, the next launch reports what was interrupted with each job's state and a
  safe choice (resume/discard). Staged-but-uncommitted imports are detectable and cleanable. Derived
  results are recomputed or marked stale; the app never opens in a partially-broken state.
- **Acceptance:** crash-during-import and crash-during-export tests recover cleanly with no partial data.

**FR-XC-009 · P0 · Phase 1 — Offline guarantee**
- **Behaviour:** All features except the explicitly-marked AI action operate with the network disabled.
  No background network calls, no telemetry, no update checks without a user action.
- **Acceptance:** the offline walkthrough (`NFR-008`) passes with the network off and outbound traffic
  monitored.

**FR-XC-010 · P0 · Phase 2 — Data-volume rule**
- **Behaviour:** Aggregation, filtering, sorting and pagination happen server-side; the UI receives at
  most one page (default 100–200 rows) or one aggregation result set. All grids are virtualised;
  drill-through paginates. No view loads a full 250k-row dataset into the browser.
- **Acceptance:** the scaled-dataset perf test (`--scale 250000`) shows the documented payload sizes and
  meets `NFR-003`.

**FR-XC-011 · P0 · Phase 1 — Accessibility baseline**
- **Behaviour:** Full keyboard navigation on critical flows, visible focus states, ARIA labels on
  controls, WCAG AA contrast (4.5:1) in the default theme, no colour-only signals, charts expose exact
  values via tooltips, and every chart has a table view.
- **Acceptance:** the accessibility checklist in `14` passes on the critical flows.

**FR-XC-012 · P0 · Phase 1 — Error message catalog compliance**
- **Behaviour:** Every error code in `26` maps to a user-facing message plus a plain-language hint, and
  every UI error path uses a catalog entry. No exception message, stack fragment or SQL error is ever
  shown.
- **Acceptance:** a test asserts that every catalog entry has message + hint, and a UI lint asserts no
  raw exception text is rendered.

**FR-XC-013 · P1 · Phase 5 — Sample-data non-delivery guarantee**
- **Behaviour:** Sample-data files are never included in any deliverable sent to the client; the go-live
  checklist includes a verification item, and exports from sample projects carry the sample watermark
  (FR-ONB-008).
- **Acceptance:** the go-live checklist item is evidenced.

**FR-XC-014 · P1 · Phase 6 — Client support flow**
- **Behaviour:** In-app guidance on how to get help: what the diagnostics zip contains, how to send it
  safely, what to try first, and the confidentiality note. Mirrors `23`.
- **Acceptance:** the flow is reachable from the error dialog and About screen in ≤ 2 clicks.

**FR-XC-015 · P2 · Phase 6 — Manual update check**
- **Behaviour:** "Check for updates" contacts the documented update channel (configurable; disabled by
  default), shows the latest version and release notes link, and never downloads or installs anything
  automatically.
- **Acceptance:** with the check disabled, no outbound call occurs; with it enabled, only the version
  metadata request is made.

**FR-XC-016 · P2 · Phase 6 — Local performance instrumentation**
- **Behaviour:** Job timings (import, rule run, exports, cold start) are recorded locally and surfaced
  in Diagnostics, so `NFR` targets can be verified on the client's machine without developer tools.
- **Acceptance:** the Diagnostics screen shows the last run of each instrumented job with its duration
  and the NFR it maps to.

## 15. Screen touchpoints (informative)

Screen IDs are assigned in `08`; the traceability join is in `20`. Feature-to-screen coverage must be
100%: every FR above touches at least one screen, and every screen in the `08` inventory exists to
serve at least one FR. Screens referenced by name in this document: Home, Import (drop/mapping/
pre-scan/preview), Check/Validation report, Import History, Analyze (matrix, bridge, trends, top-N,
three-way, KPIs, drill-through), Exceptions register + detail, Forecast workspace, Reports/Generate
pack, Pack issuance register, Commentary editor, Settings (all sections), Master Data, Backup/Restore,
About/Diagnostics, Error dialog, Help panel.

## 16. Edge-case matrix (Addon 4 §G.2 — canonical behaviour + message slug)

Numeric error codes are assigned in `26` (families `ERR-IMP`, `ERR-VAL`, `ERR-BVA`, `ERR-FC`, …); the
**slug below is the stable join key** used by `26`, `08` and `14`. Tests for every row live in `14`.

| # | Input condition | Required behaviour | Message slug |
|---|---|---|---|
| E1 | First-ever period (no prior periods, no PY) | BvA works; PY/TTM views hidden with a tooltip; run-rate and average-based forecast methods disabled with an explanatory hint — never a crash or a blank chart | `bva.firstPeriod`, `fc.insufficientHistory` |
| E2 | No budget loaded | BvA screen shows an explicit empty state + "Import budget" CTA; amount-based variance rules disable with a visible notice; never variance = 0 masquerading as a real comparison | `bva.noBudget` |
| E3 | Header-only actuals file (0 data rows) | Default: reject the file, naming the reason; an explicit "accept as zero-activity period" confirmation path exists and is recorded on the batch | `import.noDataRows` |
| E4 | Rows with zero amounts | Kept and visible in drill-down; excluded from outlier/spike-type rules; counted in the validation report | `import.zeroAmountRows` |
| E5 | Future-dated transactions | Loaded according to the posting-date period rule (`05`); the cut-off exception rule flags them | `exc.futureDated` |
| E6 | Dates outside the configured fiscal year | Quarantined with a message naming the row and the date — never silently assigned to a wrong period | `import.dateOutsideFiscalYear` |
| E7 | Duplicate column headers in the source | Import blocked until the profile renames/ignores the conflicting columns | `import.duplicateHeaders` |
| E8 | ≥ 90% of rows unmapped after mapping | Import blocked with a mapping CTA and the count of unmapped rows | `import.unmappedThreshold` |
| E9 | Budget imported mid-period or after actuals | Allowed at any time; derived results marked stale with the "Re-run required" banner (FR-SET-010) | `set.staleDerived` |
| E10 | Mixed-currency rows in a single-currency project | Quarantine the rows with a message naming the currencies found; default stance is documented in `04` | `import.mixedCurrency` |
| E11 | Amount exceeding display precision (e.g. > 2 dp) | Rounded for display per the tolerance policy (`05`); never truncated silently; stored value retains full precision | `calc.displayRounding` |
| E12 | Single-row / tiny files | Fully supported with no size assumption; all validation and reporting paths behave normally | — |
| E13 | Amounts as parentheses / `Cr`/`Dr` suffixes / text-formatted numbers | Handled per the per-profile parsing rules (`04`); on ambiguity, the user confirms once and the choice is saved to the profile | `import.ambiguousValue` |

## 17. Traceability and change control for this document

- Every FR is mirrored in `20_REQUIREMENTS_TRACEABILITY.md` with: priority, phase, spec section, screen
  ID, API endpoint, test IDs, and status. An FR without at least one test cannot be marked complete.
- New requirements are appended as `FR-<FAMILY>-nnn` (never renumbered) with a `CHANGELOG` entry; a new
  family requires an update to §2 and to `00_INDEX.md` §8 first.
- Behaviour changes follow the change-impact rule (Addon 4 §E.3): impact note first (affected FRs, docs,
  tests, size), then the doc change, then the code.


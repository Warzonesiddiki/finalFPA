> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** `FR-ONB-*`, `FR-PRJ-*`, `FR-IMP-*` (screens), `FR-BVA-*`, `FR-EXC-*`, `FR-FC-*`, `FR-XL-*`, `FR-PPT-*`, `FR-AI-*`, `FR-SET-*`, `FR-XC-*`; screens (`SCR-nnn`), charts (`CHT-nnn`), formatting rules, wording rules, states, accessibility
> **TL;DR (≤ 15 lines):** This document owns every screen and every visual rule. §4 is the screen
> inventory (43 stable `SCR-` IDs with purpose, linked FRs and states); §5–§10 specify the screens
> screen-by-screen (Home, project/wizard, import, Check, Analyze, Exceptions, Forecast, Reports/issuance,
> Settings/master data, global components) with ASCII wireframes. §11 is the chart inventory (12 `CHT-`
> charts with type, grain, drill target and empty state); §12 is the single centralized conditional-format
> rule set shared by app, Excel and PPT; §13 is the display-formatting contract; §14 is the message-catalog
> wording rule; §15 is the per-screen state matrix; §16 is the accessibility baseline; §17 the design
> system and tokens. Colour is **never** the only signal (P19), no screen ever shows a raw exception, and
> no number is shown that cannot be drilled.

---

# 08 — UI/UX SPECIFICATION

## 1. Purpose and ownership boundary

| Concern | Owner |
|---|---|
| Screens, layout, components, copy, states, charts, formatting rules, accessibility | **`08` (this document)** |
| Feature behaviour (what a screen does) | `02` |
| Numbers shown on screens | `05` (formulas), `06` (rule text), `07` (forecast) |
| Table/field structure | `03` |
| Branding asset values (logo file, brand colours) | `01` §17 (defaults) + Settings (`FR-SET-008`) |
| Theme token *values* | `ui/theme/tokens.ts`, generated against this document |
| Error-code numbering | `26` (families and ranges) |

**Binding rules for any UI work:**

1. **No hardcoded hex values in components.** All colour, spacing and type values come from tokens
   (`ui/theme/tokens.ts`), lint-enforced (A2 §E).
2. **Every screen has an ID** (`SCR-nnn`) referenced by FRs, API endpoints and tests.
3. **Every chart has a table view** — no chart is the only way to read a number.
4. **Every error has a catalog entry** (message + hint); no raw exception text ever reaches the UI.
5. **Every destructive action requires typed confirmation** naming the object (`FR-PRJ-012`).
6. **Never colour-only** (P19): colour is always paired with a sign, label, icon or text.

## 2. Users of this document

| Reader | What they need from it |
|---|---|
| Front-end implementer | Screen inventory, layout, components, tokens, states |
| Back-end implementer | What each screen consumes (`API-nnn` in `26`), payload shapes (`03`) |
| Test author | Screen IDs for Playwright/component tests, the state matrix (§15) |
| The client-facing writer | The copy rules (§14) and the user guide mapping (`22`) |
| Reviewer (non-technical) | The wireframes, to confirm the workflow matches their month-end |

## 3. Information architecture and navigation

### 3.1 Left-nav workflow (guided, ordered by the monthly rhythm)

```
┌──────────────────────┐
│  FP&A Month-End      │   ← product name (branding-configurable)
│  Copilot             │
├──────────────────────┤
│  ⌂  Home             │   SCR-001  period status, health, quick actions
│  ⬇  Import           │   SCR-005…  file in, validation, history
│  ✓  Check            │   SCR-014  data-quality score + failed checks
│  ▤  Analyze          │   SCR-015… BvA, bridge, trends, top-N, KPIs, drill
│  ⚠  Exceptions       │   SCR-023… register, detail, effectiveness
│  ↗  Forecast         │   SCR-027… workspace, comparison, accuracy
│  ▣  Reports          │   SCR-029… generate, issuance register, commentary
│  ⚙  Settings         │   SCR-032… storage, mappings, master data, rules, display,
│                      │            branding, AI, backups, about
├──────────────────────┤
│  [?] Help panel      │   SCR-042  contextual, single-sourced with doc 22
│  ⓘ  Period FY26-P09  │   always-visible current period + Open/Closed chip
│  ●  Last import …    │   always-visible last-import summary chip
└──────────────────────┘
```

| Navigation rule | Detail |
|---|---|
| Order is fixed | Home → Import → Check → Analyze → Exceptions → Forecast → Reports → Settings; it mirrors the month-end rhythm (`01` §4.1) and is never re-ordered |
| Badges | Import shows a quarantine count badge; Check shows a failed-check count; Exceptions shows open/overdue counts; Reports shows "pack not yet issued" for the current period |
| Never dead-end | Every screen offers a next step; a screen with no data explains how to get data and links there |
| Deep links | Any figure, exception or KPI can be linked to a URL fragment for support conversations (`/analyze?ctx=…`), read-only for pasted links |
| Persistence | The last screen per project is restored on reopen; wizard state is persisted separately (`FR-ONB-006`) |

### 3.2 Screen-flow for the monthly cycle (the spine)

```
Home ──► [New Period wizard] ──► Import (× N files) ──► Check ──► Analyze ──► Exceptions
  ▲                                                                              │
  │                                                                              ▼
  └────────────── Reports (generate → review → issue) ◄────────── Forecast workspace
                                   │
                                   ▼
                        Settings / Master data (as needed)
```

### 3.3 Global shell

| Element | Behaviour |
|---|---|
| Header | Product name · project name · current period + status chip · global search (`FR-BVA-012`) · help · Settings |
| Filter bar | Present on all Analyze/Exceptions/Forecast screens; the active filter context is always visible and one click from reset (`FR-BVA-015`); it is captured into every export and commentary draft |
| Stale banner | Full-width amber banner when derived results predate a mapping/threshold/master-data change: *"Results may be out of date — <what changed>. Re-run required."* with a Re-run action (`FR-SET-010`) |
| Job drawer | Bottom-right, collapsed by default: running jobs with progress %, ETA and Cancel; expands to show history (`FR-IMP-030`) |
| Sample banner | Full-width, unmistakable, on every screen when `project_type = sample` (`FR-ONB-008`) |
| Toasts | Transient confirmations ("Import committed"), never used for errors that need action |

## 4. Screen inventory (43 screens)

Every entry lists the screen's purpose, the FRs it serves, and its dominant states (§15 for the full matrix).
"Consumer of" = the API endpoints it calls (defined in `26`).

| ID | Screen | Purpose | FRs | Key states |
|---|---|---|---|---|
| `SCR-001` | Home | Period status, health, KPIs, quick actions | `FR-PRJ-001`, `FR-ONB-003` | first-run, no project, empty period, warnings, normal |
| `SCR-002` | Project launcher (modal) | Open recent / create / restore | `FR-PRJ-003`, `FR-PRJ-002`, `FR-PRJ-009` | empty recents, missing folder, read-only |
| `SCR-003` | New Project wizard | Create project + fiscal calendar + currency + locale | `FR-PRJ-002`, `FR-SET-005`, `FR-SET-006` | validation errors, synced-path warning |
| `SCR-004` | New Period wizard | Open a period, show missing sources, carry forward config | `FR-PRJ-004` | out-of-order warning, already-exists, no budget |
| `SCR-005` | Import — 1 Choose file | Drag-and-drop + picker + source type | `FR-IMP-001`, `FR-IMP-002` | dragging, unsupported file, multi-file queue |
| `SCR-006` | Import — 2 Pre-scan | Size/rows/duration estimate + limits | `FR-IMP-003` | over-limit confirmation, encrypted, cannot-estimate |
| `SCR-007` | Import — 3 Sheet & header | Sheet picker, header row selection, preview | `FR-IMP-009` | no header, multi-row header, hidden sheets |
| `SCR-008` | Import — 4 Map columns | Column mapping, overrides, profile auto-match, suggestions | `FR-IMP-004`…`FR-IMP-008` | unmapped required field, duplicate headers, AI suggestions |
| `SCR-009` | Import — 5 Validate | Progress, per-check results, offenders | `FR-IMP-021`, `FR-IMP-030` | running, cancelled, file-level rejection |
| `SCR-010` | Import — 6 Commit & confirm | Summary, score, next actions | `FR-IMP-020`, `FR-IMP-022` | success, quarantine pending, conflict (duplicates) |
| `SCR-011` | Import History | All batches with status and evidence | `FR-IMP-023`, `FR-IMP-024` | empty, voided present, closed-period block |
| `SCR-012` | Batch detail / validation report | Nine-part report (per `04` §17) | `FR-IMP-021` | rejected, cancelled, skipped checks |
| `SCR-013` | Quarantine review | Resolve row-level failures | `FR-IMP-013` | empty, resolved, bulk resolve |
| `SCR-014` | Check | Data-quality score + failed checks + coverage | `FR-IMP-022`, `FR-EXC-014` | perfect, failing, missing master data |
| `SCR-015` | Analyze — BvA matrix | The primary comparison grid | `FR-BVA-001`…`FR-BVA-003`, `FR-BVA-009`, `FR-BVA-013` | no budget, empty period, coarse-budget disclosure |
| `SCR-016` | Analyze — Bridge | Waterfall from budget to actual | `FR-BVA-005` | all-zero variance, >N drivers |
| `SCR-017` | Analyze — Trends | Multi-period lines and variance bars | `FR-BVA-006` | single period, sparse gaps |
| `SCR-018` | Analyze — Top-N | Ranked adverse/favourable variances | `FR-BVA-007` | ties, empty |
| `SCR-019` | Analyze — Three-way | Actual vs Budget vs Forecast + accuracy | `FR-BVA-008` | no forecast generated, closed periods only |
| `SCR-020` | Analyze — KPIs | KPI cards + trend + drill | `FR-BVA-010` | `n/a` denominators, no targets |
| `SCR-021` | Drill-through | Transaction detail for any figure | `FR-BVA-004` | forecast-sourced figure, snapshot figure |
| `SCR-022` | Search | Vouchers, vendors, accounts, descriptions | `FR-BVA-012` | no results, partial periods loaded |
| `SCR-023` | Exceptions register | Triage, filter, bulk act, export | `FR-EXC-002`…`FR-EXC-014` | all rules disabled, empty, overdue present |
| `SCR-024` | Exception detail | Evidence, workflow, notes, history | `FR-EXC-006`…`FR-EXC-009`, `FR-EXC-016` | no evidence rows, closed, flagged again |
| `SCR-025` | Evidence bundle export (modal) | Assemble the workbook/zip | `FR-EXC-016` | large bundle warning |
| `SCR-026` | Rule effectiveness | Per-rule stats + review recommendations | `FR-EXC-015` | insufficient history |
| `SCR-027` | Forecast workspace | Methods, overrides, scenarios, guidance | `FR-FC-002`…`FR-FC-006`, `FR-FC-009` | ineligible methods, no budget, not generated |
| `SCR-028` | Forecast comparison & accuracy | Scenarios side by side + accuracy report | `FR-FC-003`, `FR-FC-007` | no closed periods, draft-only basis |
| `SCR-029` | Reports — Generate pack | Choose artifacts, filters, scenario, commentary | `FR-XL-001`, `FR-PPT-001`, `FR-XC-001` | no forecast, no exceptions, long generation |
| `SCR-030` | Pack issuance register | Issue, version, recipients, immutability | `FR-XC-002`, `FR-XC-003`, `FR-PRJ-010` | not issued, issued, re-issue required |
| `SCR-031` | Commentary editor | Per-line and executive narrative with versions | `FR-XC-001`, `FR-AI-004`, `FR-AI-011` | AI disabled (rule-based), locked by issue |
| `SCR-032` | Settings — Data & storage | Data folder, storage used, health, archive-and-delete | `FR-SET-001`, `FR-SET-009`, `FR-PRJ-011` | synced path, low storage |
| `SCR-033` | Settings — Mappings | Profiles, versions, history, revert, import/export | `FR-SET-002`, `FR-IMP-005`, `FR-IMP-026` | no profiles, mid-year version present |
| `SCR-034` | Settings — Master data | Vendor categories, recurring costs, thresholds, owners | `FR-SET-003`, `FR-EXC-014` | empty (rules disabled), imported |
| `SCR-035` | Settings — Thresholds & rules | Per-rule enable/threshold/severity, materiality | `FR-EXC-012`, `FR-EXC-013`, `FR-SET-004` | defaults vs overridden |
| `SCR-036` | Settings — Display & locale | Currency, scale, grouping, dates, decimals, negatives | `FR-SET-006`, `FR-SET-007` | — |
| `SCR-037` | Settings — Branding | Name, logo, two brand colours, contrast check | `FR-SET-008` | contrast failure variant |
| `SCR-038` | Settings — AI | Provider, key, model, redaction, caps, usage log | `FR-AI-001`…`FR-AI-003`, `FR-AI-009`, `FR-AI-014` | keyless (default), cap reached, model retired |
| `SCR-039` | Backup & restore | Zip backup, restore, drill | `FR-PRJ-008`, `FR-PRJ-009` | in progress, invalid zip, newer version |
| `SCR-040` | About / Diagnostics | Version, data folder, storage, diagnostics zip, disclaimer | `FR-XC-004`, `FR-XC-005`, `FR-XC-016` | redaction opt-in |
| `SCR-041` | Error dialog (global) | What happened, what was not lost, one action | `FR-XC-006`, `FR-XC-012` | informational, recoverable, fatal |
| `SCR-042` | Help panel (global overlay) | Contextual help, single-sourced with doc `22` | `FR-ONB-004`, `FR-ONB-007` | no topic → workflow topic |
| `SCR-043` | First-run tour overlay | Six-step guided tour | `FR-ONB-002` | resumed mid-tour, dismissed |

**Coverage check:** every FR family maps to at least one screen; every screen serves at least one FR
(verified in `20_REQUIREMENTS_TRACEABILITY.md`).

## 5. Home (`SCR-001`)

### 5.1 Purpose

Answer three questions in one screen, in a non-technical user's words: *Where am I in the close? What
needs my attention? What do I do next?*

### 5.2 Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ⚠ SAMPLE DATA — this project contains fictional data for demonstration only.   [Learn more]│
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ Home                                   FY26-P09 · September 2026        [ OPEN ]  [Close ▸]│
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─ Needs your attention ──────────────────────────┐  ┌─ This month at a glance ────────┐│
│  │ ⚠ 8 quarantined rows (batch 42)     [Review ▸]  │  │ Revenue   ₹1,08,00,000  ↑ 8.0%  ││
│  │ ⚠ 3 checks failed (batch 42)        [Open Check]│  │ Opex      ₹ 35,50,000   ↓ 6.6%  ││
│  │ ⚠ Results may be out of date        [Re-run ▸]  │  │ Gross %   40.0%         ▲ 1.5pp ││
│  │ ⚠ 14 exceptions open (2 overdue)    [Review ▸]  │  │ Net       ₹ 24,00,000   ↑ 5.2%  ││
│  │ ✓ Budget loaded, balances          —            │  │ Budget burn 25.8%       on plan ││
│  └─────────────────────────────────────────────────┘  └─────────────────────────────────┘│
│                                                                                          │
│  ┌─ Continue the close ────────────────────────────────────────────────────────────────┐ │
│  │  1  Import this month's files            ✗ not yet   [ Import ▸ ]                    │ │
│  │  2  Check the data                        ✓ done     [ View ]     score 95/100       │ │
│  │  3  Analyse variances                     ○ open     [ Analyze ▸ ]                   │ │
│  │  4  Review exceptions                     ○ open     [ Exceptions ▸ ]                │ │
│  │  5  Refresh the forecast                  ✗ not yet  [ Forecast ▸ ]                  │ │
│  │  6  Generate and issue the pack           ✗ not yet  [ Reports ▸ ]                   │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  ┌─ Recent activity ───────────────────────────────┐  ┌─ Health ────────────────────────┐│
│  │ 03-Oct 14:22  Imported GL_Sep26.xlsx (184,494)  │  │ Storage used      420 MB of 40GB││
│  │ 03-Oct 14:31  Imported payroll_sep.csv (1,204)  │  │ Last rule run     03-Oct 14:35  ││
│  │ 02-Oct 09:10  Closed period FY26-P08            │  │ Schema version    1             ││
│  └─────────────────────────────────────────────────┘  └─────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Behaviour

| Element | Rule |
|---|---|
| Period header | Current period, label, status chip; `Close ▸` opens the close confirmation (typed period code, backup reminder, snapshot + lock) |
| Needs your attention | Ordered by severity; each item links **directly to the screen that resolves it** (`FR-PRJ-001`); an empty list shows a calm "Nothing needs attention" state — not an empty box |
| KPI strip | Current period's KPIs from `KPI-001`…`KPI-005` (`05` §5.2); every card is drillable; `n/a` renders as `n/a` (never `0%` or `∞`) |
| Continue the close | The six-step checklist mirrors the monthly rhythm; a completed step shows a check and a "View" link, never a dead end |
| Recent activity | Last ten audit-visible events (imports, closures, voids, issues) — text only, no amounts or vendor names in the feed (log policy, `13`) |
| Health | Storage used, last rule run, schema version, last backup age |
| First-run variant | Replaces the checklist with the sample-project explanation and a single primary action: *"Explore the sample project"* |

## 6. Project and period wizards (`SCR-002`–`SCR-004`)

### 6.1 Project launcher (`SCR-002`)

| Element | Behaviour |
|---|---|
| Recent projects | Cards with name, path, last opened, last period, status; actions: Open · Reveal in Explorer · Back up · Remove from recents · Delete |
| Missing folder | Card renders greyed with *"Folder not found"* plus "Locate…" and "Remove from recents" — never a silent failure |
| Primary actions | "Open a project", "Create a new project", "Restore from backup" |

### 6.2 New Project wizard (`SCR-003`)

Step 1 of 4, with persisted state and inline validation.

| Step | Fields | Validation |
|---|---|---|
| 1. Basics | Project name, client/entity description, storage folder (default `%LOCALAPPDATA%\FP&A Month-End Copilot\Projects\<name>`) | Name required; folder must be empty or new; **synced-folder warning** with a "use the default location" action (`FR-SET-009`) |
| 2. Fiscal calendar | Year start month, period count (12 or 4-4-5), period label format | Preview of the generated period list (`FY26-P01 … P12` with dates) for confirmation |
| 3. Reporting | Currency, symbol, unit scale, digit grouping, date format, decimals, negatives-in-parentheses | Live number preview rendering both grouping styles |
| 4. Entities | Optional entity list (code + name + currency) — skippable, importable later | Duplicate codes blocked |

Completion shows a summary and two actions: **"Import your first file"** and **"Explore with the sample
project"**.

### 6.3 New Period wizard (`SCR-004`)

| Step | Content |
|---|---|
| 1. Period | Proposed next period (or a picker); warns if starting out of order ("You are opening FY26-P09 while FY26-P08 is still open") |
| 2. Expected sources | Checklist of sources for the month (D365 GL · payroll · procurement · budget if not yet loaded · master data) with a status per source and what is missing |
| 3. Carry forward | Explicit statement of what carries forward — **mappings, thresholds, master data, forecast method choices; never numbers** — with the profile versions being carried |
| 4. Confirm | Summary; the period opens as `Open`; the Home checklist resets for the new period |

## 7. Import screens (`SCR-005`–`SCR-013`)

### 7.1 Step 1 — Choose file (`SCR-005`)

```
┌───────────────────────────────────────────────────────────────────────────────┐
│  Import ▸ 1 Choose file                                       Step 1 of 6    │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│      ┌──────────────────────────────────────────────────────────────┐         │
│      │         Drag this month's export here, or  [ Choose a file ]  │         │
│      │         .xlsx  .xlsm  .csv        Multiple files supported    │         │
│      └──────────────────────────────────────────────────────────────┘         │
│                                                                               │
│   Source type:  ⦿ Dynamics 365 GL export   ○ Payroll summary                  │
│                 ○ Procurement / bank ledger  ○ Budget   ○ Master data          │
│                 Detected from the file name — change it if wrong  ⓘ            │
│                                                                               │
│   Don't have the file yet?  [ Download a blank template ▾ ]                    │
│   Not sure which type you need?  [ What am I importing? ]                      │
└───────────────────────────────────────────────────────────────────────────────┘
```

| Rule | Detail |
|---|---|
| Drop zone | Whole panel is a drop target with a visible drag-over state (`FR-IMP-001`) |
| Multi-file | Files queue and process sequentially with per-file status rows; the user can cancel the queue between files |
| Rejections | Named immediately under the drop zone with the reason and the next action (`04` §19) |
| Already imported | If the checksum matches a committed batch, the file is shown as *"Already imported on 14-Sep-2026 (batch 37)"* with "View that import" / "Import a corrected file" |
| Next | Enabled once a file and a source type are present |

### 7.2 Step 2 — Pre-scan (`SCR-006`)

Shows: file name and size · sheet count and names · estimated data rows · estimated duration · detected
encoding/delimiter for CSV (with a "change" affordance, never guessed silently — `04` §9 C5) · limit check
result.

Over-limit variant: an amber block stating the limit, the measured value, and the consequence (slower
import, higher memory), requiring an explicit **"Import anyway"** checkbox before Next enables. The
decision is recorded on the batch.

### 7.3 Step 3 — Sheet and header (`SCR-007`)

A parsed grid preview with the header row highlighted; the user can pick another sheet, drag the header
row, and declare additional header rows. The chosen sheet name is displayed and recorded. Hidden sheets
are listed as skipped. If the file is protected-but-readable, a note appears.

### 7.4 Step 4 — Map columns (`SCR-008`)

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  Import ▸ 4 Map columns                                    Step 4 of 6   [Cancel]     │
├───────────────────────────────────────────────────────────────────────────────────────┤
│  Profile applied: D365 GL export (Sep-26 shape) v3 · matched on headers (92%)  [Change]│
│                                                                                        │
│  Source column            Sample values (first 3)         Maps to              Override│
│  ─────────────────────────────────────────────────────────────────────────────────────│
│  Company                  IN01 · IN01 · IN02              Company code       ▾   ⚙    │
│  Ledger account           5200-10 · 5200-10 · 4110-00     GL account         ▾   ⚙    │
│  Posting date             14-09-2026 · 14-09-2026 …      Posting date       ▾   ⚙    │
│  Fiscal period            FY26-P09 · FY26-P09 · …        Fiscal period      ▾   ⚙    │
│  Voucher                  VCH-2026-0912-004 · …          Voucher number     ▾   ⚙    │
│  Line                     1 · 2 · 3                       Line number        ▾   ⚙    │
│  Debit                    45,000.00 · 0.00 · 12,500.00    Debit              ▾   ⚙    │
│  Credit                   0.00 · 45,000.00 · 0.00         Credit             ▾   ⚙    │
│  Department               Dept=100 | CC=200 · …          (dimension string) ▾   ⚙    │
│  Notes                    "Repairs - plant" · …           Description        ▾   ⚙    │
│  (unmapped)               —                               Ignore             ▾   ⚙    │
│                                                                                        │
│  ⓘ 1 required field still unmapped: Cost centre        [ Suggest with AI ▸ ] (if enabled)│
│  ⓘ AI suggested 2 mappings — review them               [ Review suggestions ▸ ]          │
│                                                                                        │
│                                        [ Back ]   [ Save as profile ]   [ Validate ▸ ] │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

| Rule | Detail |
|---|---|
| Sample values | First 3 distinct non-empty values per column, truncated to 24 characters with a tooltip showing the full value |
| Required indicator | The unmapped-required line is sticky above the footer and blocks Next until resolved |
| Overrides | The per-column gear opens format/scale/sign overrides scoped to this profile version |
| AI suggestions | Only when AI is enabled; **never auto-applied in the same run**; the review queue shows confidence and evidence examples (`FR-IMP-008`) |
| Profile save | Saving prompts for a name and a change note; saving an existing profile creates a new version (`FR-IMP-005`, `FR-IMP-026`) |
| Date/number ambiguity | If `IMP-015` fires, a blocking question appears here with examples and a one-time choice saved to the profile version |

### 7.5 Step 5 — Validate (`SCR-009`)

Live progress with stage list (pre-scan → parse → validate → stage → commit), percentage, ETA, elapsed
time and a working Cancel. Results render incrementally grouped by severity: **Errors (block the file)** ·
**Rows needing attention (quarantined)** · **Warnings** · **Checks skipped (with reasons)**. Each group
shows counts and the first offenders with sheet/row/cell references; the full detail is in `SCR-012`.

### 7.6 Step 6 — Commit & confirm (`SCR-010`)

```
┌───────────────────────────────────────────────────────────────────────────────┐
│  Import ▸ 6 Done                                              Step 6 of 6    │
├───────────────────────────────────────────────────────────────────────────────┤
│  ✓ Imported GL_Sep26.xlsx                                                     │
│                                                                               │
│  184,494 rows loaded    8 rows need attention   0 rows rejected               │
│  184,502 source rows = 184,494 + 8 + 0   ✓ reconciles                         │
│                                                                               │
│  Data quality  95 / 100     3 checks failed ▸     [ View full report ]        │
│  Balance       ✓ debits = credits (₹1,84,50,200.00)                           │
│  Batch 42 · archived as 20261003-1422_actuals_d365_a41d2c7f.xlsx              │
│                                                                               │
│  Next:  [ Review the 8 rows ]   [ Open Check ]   [ Import another file ]       │
└───────────────────────────────────────────────────────────────────────────────┘
```

If quarantined rows remain, the primary action is **"Review the N rows"** — the workflow never implies
success while rows are unresolved.

### 7.7 Import History (`SCR-011`) and Batch detail (`SCR-012`)

History table columns: file name · source type · checksum (short, tooltip full) · rows (source/loaded/
quarantined) · balance · score · status chip · period · imported by/at · actions (View report · Reveal
archive · Void). Filters: source type, period, status, date range. Void is disabled (with the reason shown)
for a closed period, pointing to Reopen.

Batch detail is the nine-part validation report of `04` §17 in a tabbed layout (Summary · Checks · Rows ·
Balance · Duplicates · Ignored content · Score · Next actions), exportable as Excel/CSV.

### 7.8 Quarantine review (`SCR-013`)

A table of quarantined rows with raw values, reason, and source reference; actions per row: **Fix values
and re-import**, **Import as-is** (records a decision), **Discard** (records a decision and a reason).
Bulk actions require a confirmation naming the count. Nothing here is ever deleted silently, and the batch
report keeps the history of each decision.

## 8. Check (`SCR-014`)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  Check · FY26-P09                                                   [ Export report ]│
├──────────────────────────────────────────────────────────────────────────────────────┤
│   Data quality   95 / 100     (weights v1 · 32 of 32 checks ran)                      │
│   ██████████████████████░░░░                                                                 │
│   ⓘ A score never replaces the checks below — every failure is listed.                │
│                                                                                       │
│   Failed / warning checks (3)                          Passed (27)   Skipped (2) ▾    │
│   ────────────────────────────────────────────────────────────────────────────────────│
│   High    IMP-014  Date values parsed            8 rows quarantined  [ 8 rows ▸ ]     │
│   Low     IMP-021  Zero-amount rows noted       12 rows flagged      [ 12 rows ▸ ]    │
│   Medium  IMP-011  Unmapped-row share           3.2% (limit 10%)     [ details ▸ ]    │
│                                                                                       │
│   Budget coverage   89%   · 4 pairs missing periods      [ View gaps ▸ ]              │
│   Master data       ✓ recurring costs (12) · ✓ thresholds (3) · ✗ vendor categories    │
│                     ⓘ 1 rule disabled: EXC-014 needs vendor categories  [ Fix ▸ ]     │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

Rules: the score is **always** accompanied by the failed-check list (C.5, `FR-IMP-022`); clicking a check
opens its offenders; disabled rules are listed with the fix link (`FR-EXC-014`); skipped checks state
their reason.

## 9. Analyze (`SCR-015`–`SCR-022`)

### 9.1 Shared frame

All Analyze screens share: the filter bar (§3.3), a window selector (MTD · YTD · PY MTD · PY YTD · TTM)
that is **always visible**, a grain disclosure line, and "Export what you see" (`FR-BVA-011`).

**Grain disclosure (mandatory):** a persistent line under the filter bar, e.g. *"Comparing at: month ×
account × cost centre · Budget available at: month × account"* (`FR-BVA-013`).

### 9.2 BvA matrix (`SCR-015`)

```
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│ Analyze · Budget vs Actual        Window: [ MTD (Sep-26) ▾ ]      [ Export what you see ]  │
│ Filters: Entity=All · Period=FY26-P09 · CC=All · Account=All                    [ Reset ]  │
│ Comparing at: month × account × cost centre · Budget available at: month × account          │
├────────────────────────────────────────────────────────────────────────────────────────────┤
│ Account                          Actual         Budget        Variance      Var %   Fav?  │
│ ▼ 4000 Revenue                1,08,00,000.00  1,00,00,000.00  +8,00,000.00   +8.0%  Fav ▲  │
│    4000-10 Domestic           84,00,000.00    78,00,000.00    +6,00,000.00   +7.7%  Fav ▲  │
│    4000-20 Export             24,00,000.00    22,00,000.00    +2,00,000.00   +9.1%  Fav ▲  │
│ ▶ 5200 Repairs                 3,55,000.00     3,80,000.00    −25,000.00     −6.6%  Fav ▲  │
│ ▶ 5300 Materials               6,18,000.00     5,40,000.00    +78,000.00    +14.4%  Adv ▼  │
│ ▶ 5400 Utilities               2,12,000.00     2,10,000.00    +2,000.00      +1.0%  Adv ▼  │
│ ▶ 5600 Contractors             9,60,000.00     8,20,000.00    +1,40,000.00   +17.1% Adv ▼  │
│ ▶ 1999 Suspense (tagged)          —              —              —            —      —     │
│ Totals (11 accounts)          1,66,45,000.00  1,57,70,000.00  +8,75,000.00                │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

| Rule | Detail |
|---|---|
| Row semantics | Hierarchy rows expand/collapse; parent = exact sum of children (`FR-BVA-009`); every cell is clickable and drills to `SCR-021` |
| Favour*ability* | Always a sign **and** a text label (`Fav ▲` / `Adv ▼` / `—`); never colour alone |
| Zero-budget cells | `—` (nothing to compare) or `n/a` (undefined percentage) per `05` §4.2 — never `0%`, never `∞` |
| Coarse budget | If budget exists at a coarser grain, the comparison rolls actuals up and **says so** in the disclosure line; no transaction-level budget is ever implied |
| Virtualisation | Rows are virtualised; only visible rows are rendered (`FR-XC-010`); pagination on drill lists |
| Export | Produces exactly the visible filter, sort and columns, with the header block and the grain disclosure |

### 9.3 Bridge (`SCR-016`), Trends (`SCR-017`), Top-N (`SCR-018`), Three-way (`SCR-019`), KPIs (`SCR-020`)

| Screen | Spec |
|---|---|
| Bridge | Waterfall from Budget → drivers (top N, default 8) → "Other" → Actual; bars labelled with value and direction; table view beneath showing each driver's amount, account and drill link; reconciles exactly to the matrix totals (`FR-BVA-005`) |
| Trends | Actual / Budget / PY lines plus variance bars by period; gaps shown as gaps (never interpolated); single-period state renders one point with a note rather than empty axes |
| Top-N | Two ranked lists (adverse, favourable) with a toggle for by-amount / by-%; deterministic tie-breaks; each row drills; N configurable (default 10) |
| Three-way | Actual / Budget / Forecast columns plus, for closed periods, Forecast · Actual · Signed error; "not generated" state with a CTA when no locked version exists |
| KPIs | Cards with value, comparator, delta (with unit: % or pp), sparkline, and drill-through; `n/a` states; a "no targets configured" state explains how to set them |

### 9.4 Drill-through (`SCR-021`)

| Element | Rule |
|---|---|
| Header | The number being explained, in one line: *"Repairs and maintenance · Sep-26 · ₹3,55,000.00 · 34 rows"* |
| Table | Transaction rows (date, voucher, account, cost centre, vendor, description, debit, credit, net, source batch) with sort and pagination |
| Sum reconciliation | A pinned footer: *"Sum of these rows ₹3,55,000.00 = the figure you drilled ✓"* — the invariant is shown, not assumed (`FR-BVA-004`) |
| Evidence | Per row: source file name, sheet/row reference, and "Reveal archived file"; a batch chip links to `SCR-012` |
| Forecast rows | When the figure is forecast-sourced, there are no transactions: the panel shows method, scenario, version, generation stamp and driver reference instead (`FR-FC-004`) |
| Snapshot figures | When a figure comes from a closed-period snapshot, a chip states the snapshot reference and that live data may differ |

### 9.5 Search (`SCR-022`)

One box in the header; results grouped (Vouchers · Vendors · Accounts · Descriptions) with counts and a
per-row source batch; clicking a result opens a pre-filtered drill list. A note states which periods were
searched when the project is partially loaded.

## 10. Exceptions (`SCR-023`–`SCR-026`) and Forecast (`SCR-027`–`SCR-028`)

### 10.1 Exceptions register (`SCR-023`)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Exceptions · FY26-P09     Filters: Severity=All · Status=Open · Owner=All · Rule=All   [ Run rules ▸ ]│
│ 14 open · 2 overdue · 3 high                      [ Export ▾ ]  [ Copy owner summary ]  [ Bulk ▾ ] │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ☐ Rule                     Subject                          Amount      Sev   Owner   Status   Age  │
│ ☐ Possible duplicate invoice V-00931 · INV-88213          45,000.00    High  Rahul   Open   4d   │
│ ☐ Potential cut-off issue    V-00412 · doc 29-Sep         3,20,000.00  High  Aarti   In rev 6d   │
│ ☐ Round-number manual journal VCH-2026-0929-014           15,00,000.00 Low   Rahul   Open   4d   │
│ ☐ Spike vs trailing average  5600 · CC-140                1,86,000.00  Med   Priya   Open   4d ⚠ │
│   … 10 more rows                                                                                  │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ⓘ "Potential exception — requires accounting review." These are leads, not verdicts.             │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

| Rule | Detail |
|---|---|
| Columns | Rule name (pattern language, never a verdict) · subject (denormalised display) · amount at risk · severity badge (text + icon) · owner · status · age (period-based, `06` §2.5) · overdue marker |
| Filters | Severity, status, owner (including "Unassigned"), rule, entity, period, aging bucket — all combinable, all reflected in exports |
| Bulk | Multi-select → status or owner change; confirmation names the count; one audit entry per item |
| Export | Register export to Excel (`11` layout) + **copyable plain-text owner summary** (`FR-EXC-017`) |
| Empty state | *"No open exceptions — nothing requires review."* plus a link to run rules if the last run is stale |
| Disabled rules | If any rule is disabled, a line states which and why with a "Fix" link (`FR-EXC-014`) |

### 10.2 Exception detail (`SCR-024`)

Three panes: **Evidence** (the linked subject rows with the same reconciliation footer as drill-through,
plus the effective threshold and rule version) · **Workflow** (status stepper, owner, aging, notes thread)
· **History** (append-only event list: raised, flagged again, status changes, owner changes, notes,
evidence exports). Actions: change status (with the required note for `corrected`), change owner, add note,
reopen (reason required), export evidence bundle (`SCR-025`), and jump to the underlying transactions.
A closed-but-flagged-again exception shows the **"Flagged again"** badge prominently with the detection
date and a Reopen action.

### 10.3 Rule effectiveness (`SCR-026`)

A per-rule table with the §`06` §9 metrics (raised, explained/corrected share, `not_applicable` share,
average days, aging profile, repeat rate, last tuning) plus **"review recommended"** flags where
`not_applicable` exceeds explained+corrected for two consecutive periods, each naming its tuning path.

### 10.4 Forecast workspace (`SCR-027`)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Forecast · FY26 (P10–P12 open)      Scenario: [ Base ▾ ]   Last generated: 03-Oct 14:35 by Aarti  │
│ Method defaults: run_rate (N=3)     [ Generate ▸ ]  [ Compare scenarios ]  [ Lock version ▸ ]     │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Account                   Method        P10          P11          P12         FY landing  Override│
│ 4000 Revenue              run_rate      10,31,933.67 10,31,933.67 10,31,933.67 1,40,95,801.00   ⚙  │
│ 5200 Repairs              remaining_b  1,26,666.67  1,26,666.67  1,26,666.67  …                ⚙  │
│ 5450 Project costs        manual ⚑     2,00,000.00  2,00,000.00  2,00,000.00  …         reason  │
│ 5600 Contractors          not forecast  —            —            —           —      ⓘ excluded │
│                                                                                                   │
│ ⓘ Guidance: avg_3m showed smaller error than run_rate for "Revenue" over 3 closed periods.        │
│   [ Apply to these lines ]   [ Show evidence ]          (suggestion only — nothing changes until │
│                                                          you click)                              │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

| Rule | Detail |
|---|---|
| Method visibility | The method used is a column, never hidden in a tooltip; manual overrides carry a flag and their reason is one click away |
| Excluded lines | Shown with the exclusion reason, not omitted silently |
| Eligibility | An ineligible method renders as *"not forecast — needs 3 loaded periods"* with the hint (`07` §4.1) |
| Lock | Locking states what will be frozen (scenario, periods, line count, total) and is irreversible for that version |
| Guidance | Suggestion only, with evidence; applying it writes a versioned configuration change |

### 10.5 Forecast comparison & accuracy (`SCR-028`)

Scenarios side by side (Base/Best/Worst with variance between them and budget as reference — a scenario
with no adjustments is labelled *"identical to Base"*) and the accuracy report for closed periods with
signed error, absolute error, bias and MAPE-lite, including the count of zero-actual periods excluded.

## 11. Reports, issuance and commentary (`SCR-029`–`SCR-031`)

### 11.1 Generate pack (`SCR-029`)

Choose artifacts (Excel pack · PowerPoint deck), the filter context (carried from Analyze), the forecast
scenario (default Base), commentary (per-line and executive narrative), and the output folder. Generation
runs as a background job with progress and Cancel; on completion, a summary states file names, sizes, sheet
counts, slide count, and exactly which filter context and batch IDs were stamped (`FR-XL-006`, `FR-PPT-009`).
Missing inputs are stated, not silently skipped (e.g. *"No locked forecast version — the forecast slide
will be omitted"* with a link to lock one).

### 11.2 Pack issuance register (`SCR-030`)

Issued packs per period with version number, issue date, recipients, snapshot reference, files, and status
(`issued` / `superseded`). **Issue pack** freezes the snapshot, increments the version, records recipients,
and locks the commentary used. A locked commentary field is read-only with a "create a new version to edit"
action; any post-issue change requires a re-issue, which creates a new version and states what changed.

### 11.3 Commentary editor (`SCR-031`)

Two tabs: **Per-line commentary** (one entry per variance line in the current filter, with the line's
numbers pinned above the text) and **Executive narrative** (the deck's executive slide text). Each entry
shows the current version, author, timestamp, and full version history; AI drafts (when enabled) appear as
separate drafts with the label *"AI draft — review before use."*, a confidence indicator and evidence
links, and require explicit approval before entering a pack (`FR-AI-011`, `FR-PPT-008`). With AI disabled,
the **rule-based narrative** generator fills the same surfaces, labelled as rule-based rather than AI.

## 12. Settings, master data and global components (`SCR-032`–`SCR-043`)

| Screen | Spec |
|---|---|
| Data & storage (`SCR-032`) | Data folder with reveal action; storage used breakdown (databases · archives · snapshots · exports); low-storage warning; **archive-and-delete** with typed confirmation; sync-folder warning when the path is inside a syncing folder |
| Mappings (`SCR-033`) | Profile list with source type, current version, batches using it, effective-from period; version history with old→new diff and revert (revert creates a new version); import/export profile JSON; "batches using non-current versions" report |
| Master data (`SCR-034`) | Four tabs (Vendor categories · Recurring costs · Approval thresholds · Owner assignments) with inline edit, import/export, version history and revert; empty-state guidance explaining which rules are disabled while the table is empty |
| Thresholds & rules (`SCR-035`) | Global materiality (`materiality_pct`, `absolute_floor`) + per-rule rows (enable, severity, thresholds, reset-to-default, effective-value preview); changes mark results stale and are versioned |
| Display & locale (`SCR-036`) | Currency symbol, unit scale, digit grouping (Indian/international), decimal places, date format, negatives in parentheses — with a **live preview** rendering the same number in both grouping styles |
| Branding (`SCR-037`) | Product name, logo file, brand colour 1 and 2, with a WCAG AA contrast check and a documented accessible fallback when a supplied colour fails (`01` §17) |
| AI (`SCR-038`) | Off by default; provider (Azure OpenAI preferred / OpenAI-compatible), endpoint, model, key entry with DPAPI storage note, "Test connection", redaction settings, token/cost caps, usage log table, key rotation with purge, data-residency statement, model-deprecation notice area |
| Backup & restore (`SCR-039`) | "Back up now" producing a timestamped zip with a manifest and **no secrets**; restore flow with validation (version compatibility, corrupt zip refusal) and a typed confirmation when overwriting; a recovery drill link |
| About / Diagnostics (`SCR-040`) | Version, build date, schema version, data folder, storage used, last diagnostics export; actions: Export diagnostics zip (with the redaction opt-in and a contents list), Check for updates (manual only), Restore sample project; the **full canonical disclaimer** (`01` §15.1) with a Copy button |
| Error dialog (`SCR-041`) | Anatomy: **what happened** · **what was not lost** · **one recommended action** · "Copy details" · link to help. Never a traceback, never a code as the headline (`FR-XC-006`) |
| Help panel (`SCR-042`) | Contextual topic for the current screen/step, sourced from the same content as `22` (`FR-ONB-007`); falls back to the workflow topic rather than showing nothing |
| First-run tour (`SCR-043`) | Six steps, skippable, resumable after restart, "don't show again" persisted |

## 13. Chart inventory (12 charts)

**Rule (Addon 3 §F.1): adding a chart without an inventory row is a spec violation.** Every chart has a
table view, exposes exact values via tooltips, and carries the non-colour signals of §14.

| ID | Chart | Type | Source / grain | Screen | Drill target | Empty state |
|---|---|---|---|---|---|---|
| `CHT-001` | KPI trend | Line (multi-series, sparkline in cards) | `kpi_daily` aggregate · KPI × period | `SCR-001`, `SCR-020` | KPI definition → contributing accounts (`SCR-021`) | *"Not enough periods yet"* + "Import more data" |
| `CHT-002` | BvA bridge | Waterfall | `bva_drivers` · driver × period | `SCR-016` | Bar → driver rows (`SCR-021`) | *"No variances to bridge in this window"* |
| `CHT-003` | Top adverse variances | Horizontal bars | `bva_topn` · account/CC × period | `SCR-018` | Bar → drill list for that key | *"No adverse variances"* (a positive message, not an error) |
| `CHT-004` | Top favourable variances | Horizontal bars | `bva_topn` · account/CC × period | `SCR-018` | Same | *"No favourable variances"* |
| `CHT-005` | Department / account heat-map | Matrix heatmap | `bva_matrix` · account × cost centre | `SCR-015` (toggle), `SCR-020` | Cell → matrix row + drill | *"No data for this filter"* with a reset action |
| `CHT-006` | Forecast vs actual | Line + points | `forecast_accuracy` · period × scenario | `SCR-028`, `SCR-019` | Point → forecast line detail (`SCR-027`) | *"No locked forecast version yet"* + "Generate" |
| `CHT-007` | Exception Pareto (by rule) | Pareto (bars + cumulative line) | `exception_stats` · rule | `SCR-026` | Bar → filtered register (`SCR-023`) | *"No exceptions raised in this period"* |
| `CHT-008` | Exception severity mix | Stacked bar by period | `exception_stats` · severity × period | `SCR-026` | Segment → filtered register | Same as `CHT-007` |
| `CHT-009` | Period trend (actual vs budget vs PY) | Line + variance bars | `bva_trend` · period | `SCR-017` | Point → matrix for that period | *"Only one period loaded"* (single-point render, not empty axes) |
| `CHT-010` | Exception aging distribution | Bars by bucket (`0–7`, `8–30`, `31+`) | `exception_stats` · bucket × severity | `SCR-023`, `SCR-026` | Bar → filtered register | *"No open exceptions"* |
| `CHT-011` | Forecast accuracy trend | Line (error by period) + zero line | `forecast_accuracy` · period | `SCR-028` | Point → accuracy rows for that period | *"No closed periods with a locked forecast yet"* |
| `CHT-012` | Budget consumption | Bullet chart (YTD vs annual, with target marker) | `budget_consumption` · account group | `SCR-020`, `SCR-019` | Row → YTD drill | *"No budget loaded"* + "Import budget" |

**Chart rules:** charts never re-render on every keystroke (debounced 250 ms); axis labels always include
the unit and scale (`₹ in thousands`, `%`, `pp`); legends are text, not colour swatches alone; large
series are capped with an explicit "showing top N of M" note and a link to the full table.

## 14. Centralized conditional formatting (one rule set, three consumers)

This is the **single** formatting rule set. The app, the Excel pack (`11`) and the PowerPoint deck (`12`)
render from it; per-screen ad-hoc colours are forbidden (Addon 3 §F.2). Token names resolve to
`ui/theme/tokens.ts`; the same semantic tokens are written into the Excel styles and the PPT theme.

| ID | Condition | Colour token | Non-colour signal (mandatory) | Notes |
|---|---|---|---|---|
| `CF-001` | Favourable variance | `semantic.favourable.bg` / `.text` | `Fav ▲` label + sign in the number | Revenue above budget; expense below budget (`05` §4.3) |
| `CF-002` | Unfavourable variance | `semantic.unfavourable.bg` / `.text` | `Adv ▼` label + sign | Never applied to neutral line types |
| `CF-003` | Neutral / not applicable | `semantic.neutral` | `—` for "nothing to compare", `n/a` for undefined % | Two distinct states, never merged |
| `CF-004` | Severity High | `severity.high.bg` | `High` badge text + icon | Applies to exception rows and badges |
| `CF-005` | Severity Medium | `severity.medium.bg` | `Med` text + icon | |
| `CF-006` | Severity Low | `severity.low.bg` | `Low` text + icon | |
| `CF-007` | Variance beyond the materiality threshold | `semantic.threshold.emphasis` (bold + left rule) | Bold text + threshold chip showing the effective threshold | Threshold value always visible on hover / `effective_threshold` chip |
| `CF-008` | Overdue exception | `semantic.warning.bg` | `Overdue Nd` text badge | `N` = days beyond the severity SLA |
| `CF-009` | Stale derived result | `semantic.warning.banner` | Banner text naming what changed | Full-width banner, never a subtle tint |
| `CF-010` | Quarantined / unresolved rows | `semantic.attention` | Count text (`8 rows need attention`) | |
| `CF-011` | Zero-amount row | `semantic.muted` | `0.00` rendered in muted text | Kept and visible, never hidden (`02` E4) |
| `CF-012` | Sample-data artefact | `semantic.sample.watermark` | Diagonal text watermark + banner | Excel sheets, PPT slides, in-app headers |

**Literal values for the Excel consumer:** the v1 ARGB values, the Excel rule types, the fixed rule
order and the mandatory non-colour **signal columns** are specified in `11` §3.7. `ui/theme/tokens.ts`
remains the single source; the export theme is re-derived from it and asserted equal by a test
(`11` §13 `TST-XL-10`), so the workbook cannot drift from the app's semantics.

**Black-and-white print test:** every rule above must remain readable when printed greyscale — the
non-colour signal is what carries the meaning, and a test renders the pack to greyscale and asserts the
labels are present (`NFR` print check, P19).

## 15. Display-formatting contract

Owned here; consumed identically by app, Excel and PPT (enforced by the cross-artifact consistency test,
`14`).

| Element | Rule | Example |
|---|---|---|
| Currency symbol | Project setting; default `₹` | `₹ 1,08,00,000.00` |
| Digit grouping | Indian (lakh/crore) default, international optional | `₹ 1,08,00,000.00` vs `₹ 10,800,000.00` |
| Scale | Whole units default; thousands/lakhs optional, **label always shown** | `₹ in lakhs 108.00` |
| Decimals | 2 dp for money; 1 dp for % / pp / ratios | `8.0%`, `+1.5 pp` |
| Negatives | Parentheses default | `(25,000.00)` |
| Dates | `dd-mm-yyyy` default | `14-09-2026` |
| Percentage vs points | Ratios compare in **pp**, money in `%` | `40.0% vs 38.5% = +1.5 pp` |
| Rounding footnote | Shown wherever displayed components may not sum to the displayed total | *"Components may not sum to the total due to rounding."* |
| Entity grouping label | Wherever entities are summed | *"Simple sum — no eliminations"* |
| Empty vs zero | `—` = nothing to compare; `n/a` = undefined; `0.00` = a real zero | Never interchangeable |
| Units in exports | Every sheet/chart states its unit and scale in the header block | — |

## 16. Message catalog and wording rules

### 16.1 The rule

1. **Every error path uses a catalog entry** (`ERR-<FAM>-nnn` in `26`) that pairs a **message** with a
   **hint** (the one next action). A UI path with no catalog entry fails a test (`FR-XC-012`).
2. **No raw exception text, SQL text, stack fragment or file path beyond the project folder** is ever
   rendered. Technical detail goes to the log and to "Copy details".
3. **Codes are never the headline**: `ERR-IMP-004` may appear in the details area, never as the message.
4. Wording lint: banned words in user-facing strings — *error*, *invalid*, *illegal*, *failed to parse*,
   *exception* (except in the sanctioned phrase "Potential exception"), *null*, *undefined*,
   *wrong entry*, *confirmed error*. Permitted framings: *"Potential exception — requires accounting
   review."*, *"needs attention"*, *"couldn't be read"*, *"check"*.
5. **One primary action per message**, with optional secondary links (download template, view report).

### 16.2 Catalog shape (populated in `26`)

| Field | Meaning | Example |
|---|---|---|
| `code` | Stable numeric code | `ERR-IMP-011` |
| `message` | What happened, naming the object | *"Column 'Cost Center' wasn't found in sheet 'GL_Export'."* |
| `hint` | The single next action | *"Map it now, or download the current template."* |
| `severity` | `info` / `attention` / `blocking` | `blocking` |
| `slug` | The stable join key used by `04`/`02` | `import.missingRequiredColumns` |

## 17. Per-screen state matrix

Every screen must define these states. "—" means the state cannot occur for that screen.

| Screen group | Empty | Loading | Error | First-run | Stale-derived | Offline |
|---|---|---|---|---|---|---|
| Home (`SCR-001`) | No project → launcher; no period → New Period CTA | Skeleton cards | Banner + retry, other cards still render | Sample-project explanation replaces the checklist | Banner (`CF-009`) | Fully functional |
| Import (`SCR-005`–`SCR-010`) | Drop zone prompt + template link | Stage progress with % and ETA | Named rejection inline; other files unaffected | Template-first guidance | Stale banner after commit | Fully functional |
| Check (`SCR-014`) | *"Import a file to see checks"* + CTA | Score skeleton | Per-check failure rows, not a page-level error | Sample project shows a passing example | Banner when config changed since last run | Fully functional |
| Analyze (`SCR-015`–`SCR-020`) | No budget → CTA; no actuals → CTA; no PY → PY options hidden with tooltip | Grid/chart skeletons (never a frozen grid) | Inline message + retry for the failing panel only | Sample project only | Banner + "Re-run required" | Fully functional |
| Drill (`SCR-021`) | *"No transactions for this figure"* (forecast figures show method info instead) | Row skeleton | Inline + retry | — | Banner | Fully functional |
| Exceptions (`SCR-023`–`SCR-026`) | No rules run yet → "Run rules"; none raised → calm empty state | Progress for the run | Run failure with the reason and a retry | Sample project shows a populated example | Banner; rules show "last run" date | Fully functional |
| Forecast (`SCR-027`–`SCR-028`) | No budget and no history → both methods ineligible with hints | Generation progress + cancel | Ineligible/blocked explained line by line | Sample project | Banner | Fully functional |
| Reports (`SCR-029`–`SCR-031`) | Nothing to generate → prerequisites explained | Generation progress + cancel | Failure stating what was and was not produced | Sample project | Banner | Excel/PPT generation works offline; only AI drafting needs the network |
| Settings (`SCR-032`–`SCR-040`) | Empty tables with guidance (and the rules they disable) | Skeleton rows | Inline validation | Defaults pre-filled | Version history shown | Fully functional except the AI test connection |
| Error dialog (`SCR-041`) | — | — | Self | — | — | Self |
| Help/tour (`SCR-042`–`SCR-043`) | Fallback to the workflow topic | — | — | Tour auto-starts once | — | Local content only |

**Global rule:** a loading state never blocks navigation; a panel-level error never blanks the screen; and
no job over two seconds runs without a visible progress indicator and a cancel path.

## 18. Accessibility baseline (WCAG AA, Addon 2 §E)

| Requirement | Rule |
|---|---|
| Keyboard | Every critical flow (import, filter, drill, exception workflow, generate) is completable by keyboard alone; logical tab order; Esc closes overlays; Enter activates |
| Focus | Visible focus ring on every interactive element (`focus.ring` token), never removed |
| ARIA | Every control has an accessible name; grids expose row/column headers; charts expose a table alternative and an ARIA description carrying the headline value |
| Contrast | Default theme meets AA (4.5:1) for text and 3:1 for large text/UI; brand colours are checked and substituted with an accessible variant when they fail (`01` §17) |
| Non-colour signals | Mandatory per §14; validated by the greyscale print test |
| Zoom & scaling | Layout correct at 100–150% Windows scaling; minimum supported window 1366×768; no horizontal scrolling on primary screens at 1366 px |
| Motion | No essential information conveyed by animation; respect the OS "reduce motion" setting |
| Screen reader | Key figures (KPI values, variance, exception counts) are text, not canvas-only; charts are accompanied by their table view |
| Language | English (v1); plain-language copy per §16; no unexplained abbreviations in user-facing text (glossary in `18`) |
| Timeouts | None. No session expiry, no idle logout (single-user local app) |

## 19. Design system and tokens

### 19.1 Layout grid and spacing

| Token | Value | Use |
|---|---|---|
| `space.1`…`space.8` | 4, 8, 12, 16, 24, 32, 48, 64 px | All padding/margins; no arbitrary pixel values |
| `radius.sm/md/lg` | 4 / 8 / 12 px | Buttons and inputs / cards / dialogs |
| `layout.minWidth` | 1366 px | Minimum supported window |
| `layout.navWidth` | 240 px (collapsible to a 64 px icon rail) | Left navigation |
| `layout.filterBar` | 56 px | Sticky filter bar height |
| `layout.rowHeight` | 40 px (comfortable) / 32 px (compact toggle) | Grid density is user-switchable |

### 19.2 Type scale

| Token | Size / weight | Use |
|---|---|---|
| `type.display` | 28 px / 600 | KPI values on Home |
| `type.h1` | 20 px / 600 | Screen titles |
| `type.h2` | 16 px / 600 | Section headers, card titles |
| `type.body` | 14 px / 400 | Default text and grid cells |
| `type.small` | 12 px / 400 | Metadata, hints, footnotes |
| `type.mono` | 13 px / 400 tabular figures | Numeric columns (tabular numerals mandatory so digits align) |

**Numeric typography rule:** all figure columns use tabular numerals and right alignment; negative values
keep the parenthesis/minus convention of §15 and never rely on colour.

### 19.3 Colour roles (semantic, not literal)

| Token | Role |
|---|---|
| `semantic.favourable` | Good-news encoding (always paired with a label) |
| `semantic.unfavourable` | Bad-news encoding (always paired with a label) |
| `semantic.neutral` | Not applicable / nothing to compare |
| `semantic.warning` | Stale data, overdue, quarantine, sync warnings |
| `semantic.danger` | Blocking errors only (file rejected, integrity failure) |
| `semantic.attention` | "Needs your attention" items that are not errors |
| `brand.primary`, `brand.secondary` | From Settings; may not be used for meaning-bearing colour |
| `surface.*`, `text.*`, `border.*`, `focus.ring` | Structure and interaction |

Components consume **roles**, never hex values; `ui/theme/tokens.ts` maps roles to values and is validated
by a contrast test in `scripts/check`.

### 19.4 Component inventory (minimum set)

Buttons (primary/secondary/ghost/danger) · inline link buttons · segmented control (window/scenario
switchers) · chips (period, status, batch, snapshot, grain) · badges (severity, favourability, overdue) ·
data grid (virtualised, sortable, filterable, column chooser, density toggle) · KPI card · chart card with
a table-view toggle · wizard stepper · progress bar with ETA and cancel · job drawer · filter bar · search
box with grouped results · modal with a typed-confirmation variant · toast · banner (stale/warning/sample) ·
inline validation message · tooltip (must never be the only source of a number) · empty-state block ·
skeleton loaders · tabs · accordion (hierarchy rows) · help panel · version-history panel with diff.

**Component rules:** no component defines its own colour; every component ships with the states in §17;
every interactive component has a keyboard path and an ARIA name; destructive variants are visually
distinct (danger token) and always require confirmation.

## 20. Screen-to-document traceability

| Screen group | Owns behaviour in | Numbers from | Wording rules |
|---|---|---|---|
| Home, wizards | `02` (`FR-PRJ-*`, `FR-ONB-*`) | `05` (KPIs) | §16 |
| Import family | `02` (`FR-IMP-*`), `04` (mechanisms, copy) | `05` (score) | `04` §19, §16 |
| Check | `02`, `04` | `05` (`CALC-050`) | §16 |
| Analyze family | `02` (`FR-BVA-*`) | `05` (`CALC-010`…`CALC-042`, `KPI-*`) | §16 |
| Exceptions family | `02` (`FR-EXC-*`), `06` (rule text) | `06` §4, `05` (materiality) | `06` §1.1, §16 |
| Forecast family | `02` (`FR-FC-*`), `07` | `05` (`CALC-060`…`CALC-069`) | §16 |
| Reports / issuance / commentary | `02` (`FR-XL`/`FR-PPT`/`FR-AI`/`FR-XC-*`), `11`, `12`, `10` | `05` | §16, `10` §labelling |
| Settings / master data | `02` (`FR-SET-*`) | — | §16 |

## 21. Change control

1. A new screen requires: an inventory row (§4), a state entry (§17), an FR link, a help topic (`22`) and
   a test ID (`14`). Without all five it is not added.
2. A new chart requires an inventory row (§13) with type, grain, screen, drill target and empty state —
   **adding a chart without a row is a spec violation**.
3. A formatting change lands in §14 first (the single rule set), then in the app, Excel and PPT together —
   never in one consumer alone.
4. A wording change lands in the catalog (`26`) and in `22` simultaneously (`FR-ONB-007`); the help panel
   and the guide can never diverge.
5. Accessibility regressions block a phase gate (`14` checklist).


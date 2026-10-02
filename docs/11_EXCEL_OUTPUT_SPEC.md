> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** `FR-XL-001`…`FR-XL-009` (Excel pack), `FR-EXC-016` (evidence bundle), `FR-EXC-017` (owner distribution), `FR-EXC-018` (register export), `FR-BVA-011` (export what you see), `FR-XC-003` (pack version stamping), `FR-XC-009` (offline generation); every exported workbook: sheet list, layout, number formats, conditional formatting, freeze/filter/print setup, naming, row caps, consistency
> **TL;DR (≤ 15 lines):** The Excel layer produces **five artefact families** (§2): the month-end pack,
> the per-exception evidence bundle, the exception-register export, the owner-wise distribution, and
> ad-hoc "export what you see" tables (xlsx/csv). §3 is the universal contract — values-only workbooks,
> the stamp block, the header block, filename and collision rules, the number-format dictionary, the
> `CF-`→Excel conditional-formatting mapping with its mandatory non-colour signal column, freeze/filter/
> width rules, and print setup. §4 specifies the pack **sheet by sheet** (`XL-001`…`XL-008`), including
> controls and empty states. §5 owns the 1,048,576-row cap and the split algorithm. §6–§8 cover the
> evidence bundle, ad-hoc exports and the owner distribution (including the exact plain-text summary
> template). §9 house-style matching. §10 print/PDF. §11 the cross-artifact consistency contract that
> binds app, Excel and PPT to the same numbers. §12 failure modes, §13 the 26-item test contract,
> §14 open items, §15 change control. **No formula ever ships in a generated workbook** (§3.2).

---

# 11 — EXCEL OUTPUT SPECIFICATION

## 1. Purpose and ownership boundary

| Concern | Owner |
|---|---|
| Workbook and sheet layout, sheet names/order, header block, column sets, widths, freeze panes, autofilters, tab colours, print/PDF setup | **`11` (this document)** |
| Number-format **semantics** (rounding, signs, `—` vs `n/a`, scaling rules) | `05` (arithmetic) and `08` §15 (display contract) |
| Conditional-formatting **rule definitions** (`CF-001`…`CF-012`) | `08` §14 |
| Which FRs require which export, and export behaviour | `02` (`FR-XL-*`, `FR-EXC-016`…`018`, `FR-BVA-011`) |
| What is exported (filters, batches, grain, tie-out state) | `02`/`04`/`05`/`06`/`07` as fact owners; this document only renders it |
| Filename convention, collision policy, issuance/versioning linkage | **`11`** §3.5/§3.6 with `01` §12 |
| Evidence-bundle contents (which fields, which audit events) | `11` §6 + `06` §2 (thresholds, evidence refs) + `03` §5.2 (the exception record's fields) |
| Deck placeholders and slide geometry | `12` |
| Cross-artifact equality mechanism | **`11`** §11 (the contract), `14` (the test) |
| Test IDs that verify this document | **`11`** §13 (`TST-XL-01`…`TST-XL-26`) |

**The one-sentence rule:** *the workbook is a static, self-describing snapshot of the engine's values at
display precision — never a calculator, never a hidden data source, never a different number from the
screen.*

## 2. The workbook family

Five artefacts are generated. Each has a stable pack token used in the filename (§3.5) and a stable
sheet contract in this document.

| ID | Artefact | Pack token | Trigger | FRs | Format |
|---|---|---|---|---|---|
| `XL-001`…`XL-008` | **Month-end pack** — 8 sheets: Cover · BvA Summary · BvA Bridge · Transaction Detail · Exception Register · Forecast Summary · Import Reconciliation · Audit Trail | `MonthEnd` | Reports → Generate pack (`SCR-029`), CLI `export-xlsx` | `FR-XL-001`…`009`, `FR-XC-003` | `.xlsx` |
| `XL-009` | **Evidence bundle** — one workbook (or zip) per exception | `Evidence-<EXC-nnn>` | Exception detail (`SCR-024`) → Evidence bundle (`SCR-025`) | `FR-EXC-016`, `FR-XL-007` | `.xlsx`, `.zip` when attachments exist |
| `XL-010` | **Ad-hoc table export** — "export what you see" from any table view, and the standalone register export (`FR-EXC-018`) | `<ViewToken>` / `Register` | Any table view; Exceptions register | `FR-BVA-011`, `FR-EXC-018` | `.xlsx` or `.csv` |
| `XL-011` | **Owner-wise exception distribution** — grouped register + plain-text summary | `OwnerDist` | Exceptions register → Export ▾ | `FR-EXC-017` | `.xlsx`, `.csv`, plain text (clipboard + `.txt`) |
| `XL-012` | **Blank input templates** — actuals, budget, forecast, master data (listed here for completeness; layout owned by `04` §11 and `03`) | `Template-<kind>` | Import wizard → "Download blank template" | `FR-IMP-027` | `.xlsx` |

Rules that bind the family:

1. `XL-012` templates are named `<Project>_Template_<kind>_v<N>.xlsx` and are **not** stamped like reports
   (they contain no data, so a generation stamp would be misleading); they carry a "Template — sample
   rows removed before import" note in row 1. Every other family is stamped (§3.3).
2. The four report families are generated **entirely offline** by `app/engine/exports` (`ADR-010`,
   `FR-XC-009`); no generation path requires a network call. AI commentary, when present, is written as
   already-approved text and the workbook states its provenance (§3.3 field `ai_content`).
3. Generation runs through the job queue (`ADR-006`) with progress, ETA and cancel (`FR-XC-008`); a
   cancelled generation writes **no partial file** (temp path, atomic move on success).

## 3. Universal contract (every generated report workbook)

### 3.1 Values only — no formulas

| Rule | Detail |
|---|---|
| No formulas anywhere | Every numeric cell is a value written by the engine. A generated workbook contains **zero** formula cells (except the sanctioned empty-string case: no cell starts with `=` except literal text that is escaped with a leading apostrophe at write time) |
| Why | (a) the cross-artifact equality test (§11) parses values back — formulas read as `None` and would silently break the strongest guard in the project; (b) a client edit to a formula would make the workbook disagree with the engine while looking authoritative; (c) a non-technical user cannot audit a formula |
| Rejected alternative | Writing `SUM()` rows so the client can extend them — rejected: it invites divergence, and any sum the client needs is already a stated control row |
| Consequence | "Refresh this pack" (`FR-XL-003`) **regenerates** the workbook from the project; Excel's F9 changes nothing |
| Enforcement | `TST-XL-03` walks every cell of the generated pack in the golden test and asserts no cell value begins with `=` |

### 3.2 Stamp block (the machine-readable anchor)

The `Cover` sheet carries the canonical stamp. It is a two-column table: **label in column A, value in
column B**, with the section header `Workbook stamp` in row 6 and the 30 fields occupying rows
**7–36**. Each value cell also gets a **defined name** (on `B7:B36`) so tests and downstream tooling
read by name, never by address.

| Row | Label (column A) | Example value (column B) | Defined name |
|---|---|---|---|
| 7 | `Stamp version` | `1` | `Pack_Stamp_Version` |
| 8 | `Generated at` | `2026-10-01 14:22:31` (local, real timestamp format `XLS-FMT-008`) | `Pack_Stamp_GeneratedAt` |
| 9 | `Project` | `Acme Manufacturing` | `Pack_Stamp_Project` |
| 10 | `Entity(ies)` | `IN01, IN02` | `Pack_Stamp_Entities` |
| 11 | `Period(s)` | `FY26-P09` | `Pack_Stamp_Periods` |
| 12 | `Window` | `MTD` (or `YTD`, `PY MTD`, `PY YTD`, `TTM`, `—`) | `Pack_Stamp_Window` |
| 13 | `Scenario` | `Base` | `Pack_Stamp_Scenario` |
| 14 | `Forecast version` | `Base v3 (locked 2026-09-30)` / `none` | `Pack_Stamp_ForecastVersion` |
| 15 | `Budget version` | `FY26-Approved` | `Pack_Stamp_BudgetVersion` |
| 16 | `Filter context (JSON)` | `{"entity":["IN01","IN02"],"period":["FY26-P09"],…}` (single cell, ≤ 500 chars) | `Pack_Stamp_FilterJSON` |
| 17 | `Filter context (human)` | `Entity=IN01, IN02 · Period=FY26-P09 · CC=All · Account=All · Severity=All · Status=Open` | `Pack_Stamp_FilterHuman` |
| 18 | `Grain` | `month × account × cost centre · Budget available at: month × account` | `Pack_Stamp_Grain` |
| 19 | `Source import batch IDs` | `1041, 1042, 1043` | `Pack_Stamp_BatchIDs` |
| 20 | `Source file names` | `D365_GL_Sep26.xlsx; Payroll_Sep26.csv; Procurement_Sep26.xlsx` (≤ 500 chars, then `… (+N more)`) | `Pack_Stamp_SourceFiles` |
| 21 | `Pack version` | `v3 (issued 2026-10-01)` / `unissued draft` | `Pack_Stamp_PackVersion` |
| 22 | `Pack sequence (file vN)` | `3` | `Pack_Stamp_FileVersion` |
| 23 | `App version` | `0.9.0` | `Pack_Stamp_AppVersion` |
| 24 | `Schema version` | `1` | `Pack_Stamp_SchemaVersion` |
| 25 | `Rule set version` | `2026-09-30 (24 rules, 22 enabled)` | `Pack_Stamp_RuleSet` |
| 26 | `Mapping profile versions` | `D365 v4, Payroll v2, Procurement v1` | `Pack_Stamp_Profiles` |
| 27 | `House style profile` | `none` / `Acme-House-2026 v2` | `Pack_Stamp_HouseStyle` |
| 28 | `Units and scale` | `₹ whole units` / `₹ in lakhs` | `Pack_Stamp_Units` |
| 29 | `Digit grouping` | `Indian (lakh/crore)` | `Pack_Stamp_Grouping` |
| 30 | `AI content` | `none` / `draft, approved by <name> at <ts> (PROMPT-01 v1, model <name>)` / `rule-based narrative (no key configured)` | `Pack_Stamp_AIContent` |
| 31 | `Sample data` | `Yes — not client data` / `No` | `Pack_Stamp_SampleData` |
| 32 | `Stale derived results` | `No` / `Yes — thresholds changed 2026-10-01 09:10; re-run required before issue` | `Pack_Stamp_Stale` |
| 33 | `Tie-out state` | `Balanced (debits = credits; variance ₹0.00)` | `Pack_Stamp_TieOut` |
| 34 | `Rounding note` | `Components may not sum to the total due to rounding.` | `Pack_Stamp_RoundingNote` |
| 35 | `Disclaimer (short)` | *(short form from `01` §15.1, verbatim)* | `Pack_Stamp_DisclaimerShort` |
| 36 | `Content hash` | `sha256:9f2c…` (SHA-256 of the engine's pack value payload, computed before write) | `Pack_Stamp_ContentHash` |

Rules:

1. **Every field is always present.** Absent concepts render as `none`, `—` or `0` — never a blank
   stamp cell, never a missing row. A blank value fails `TST-XL-04`.
2. Labels are **exact strings** (case, punctuation). Tests match on the label; the label list is a frozen
   constant in `app/engine/exports/stamps.py`.
3. The JSON filter context is the *same object* the UI sent to the engine, serialised with sorted keys —
   it is the input that makes the pack reproducible (§11).
4. `Content hash` is computed over the ordered value payload (all sheets, all cells, money as quantised
   strings), **excluding** the stamp itself and timestamps. Two packs generated from identical data
   produce the same hash — the basis of the "did anything change?" refresh check (`FR-XL-003`).
5. The `Sample data` stamp field drives the `CF-012` watermark (§3.13) on every sheet; the
   `Stale derived results` field drives the stale banner (`CF-009`) in the header block of every sheet
   (§3.3).

### 3.3 Header block on every sheet

Every sheet (including `Cover`) begins with a four-row human header block so a printed or forwarded
sheet is self-explaining without the Cover. The machine-readable authority stays on `Cover` only —
duplication would create two sources of truth.

```
Row 1  <SHEET TITLE>                                                          <Units: ₹ whole units>
Row 2  <Project> · <Entity(ies)> · <Period(s)> · <Window> · <Scenario>
Row 3  Generated dd-mm-yyyy hh:mm · Pack <vN | unissued draft> · App <version> · Sources: <batch IDs>
Row 4  <sheet-specific note, control statement or omission reason>
Row 5  (spacer — 6 pt row height)
Row 6  TABLE HEADER ROW  ← autofilter starts here; freeze panes from row 7
```

| Element | Rule |
|---|---|
| Row 1 title | Exact sheet title from §4 (`BvA Summary`, `Exception Register`, …), 14 pt bold, brand colour; merged across the table's display width (A:last data column) |
| Row 1 right cell | `Units: ₹ whole units` or `Units: ₹ in lakhs` — **present on every sheet**, right-aligned, bold (Addon 3 §F.3) |
| Row 2 | Context line: project, entities, periods, window, scenario. `—` for concepts that do not apply |
| Row 3 | Generation line: timestamp, pack/file version, app version, source batch IDs (abbreviated with `… (+N)` beyond 5 batches; the full list is on `Cover`) |
| Row 4 | Sheet-specific: the control statement (`Totals tie to the Detail sheet: ₹8,75,000.00 variance`), the applied filter (`Filtered to 250,000 of 1,240,000 rows — split across 5 sheets`), the omission reason (`Forecast Summary omitted: no forecast version generated for FY26-P09`), or the empty-state message |
| Row 5 | Spacer only. Never data |
| Row 6 | Header row: bold, brand fill, white text, wrap on, row height 30, autofilter from A6 |
| Stale banner | When `Pack_Stamp_Stale = Yes`, a full-width row is inserted **above** row 1 (pushing everything down by one) with `CF-009` warning fill: *"Re-run required before issue — <what changed>."* Where present, all fixed addresses shift by one and the freeze row shifts to 8. Tests assert the shift explicitly (`TST-XL-12`) |
| Sample watermark | When `Pack_Stamp_SampleData = Yes`, a rotated `SAMPLE DATA — NOT CLIENT DATA` band occupies rows 2–4 in column A…(merged band, 45° grey 10 pt) in addition to the `CF-012` tint. The header block rows are never hidden by it (band is behind, text remains readable) |

**Freeze behaviour:** freeze panes are set at the cell **below row 6 and right of the identifier
columns** — e.g. `C7` freezes the two identifier columns and rows 1–6. With a stale banner, `C8`.

### 3.4 Filenames, sanitisation, collision policy

**Convention (mandated by the Source-of-Truth Matrix, `00_INDEX` §5):**

```
<Project>_<Entity>_<Period>_<PackToken>_<vN>.<ext>
AcmeManufacturing_IN01_FY26-P09_MonthEnd_v3.xlsx
AcmeManufacturing_IN01_FY26-P09_Evidence-EXC-018_v1.xlsx
AcmeManufacturing_AllEntities_FY26-P09_Register_v2.xlsx
AcmeManufacturing_IN01_FY26-P09_OwnerDist_v1.csv
AcmeManufacturing_IN01_FY26-P09_Drill_v4.xlsx
```

| Token | Rule |
|---|---|
| `<Project>` | Project short name from Settings, spaces removed, camel-case preserved; `[A-Za-z0-9-]` only |
| `<Entity>` | One entity → its code. 2–4 entities → codes joined with `+`, but if that exceeds 24 characters → `MultiEntity`. All / 5+ entities → `AllEntities`. No entity filter → `All` |
| `<Period>` | Single: `FY26-P09`. Range: `FY26-P01-P09`. Through-period: `FY26-YTD-P09`. Trailing twelve: `FY26-TTM-P09`. Multi-year: `FY26-P09_FY27-P02` |
| `<PackToken>` | From §2's table, or the view token for ad-hoc exports (`Drill`, `Matrix`, `Bridge`, `TopN`, `Trends`, `KPIs`, `ThreeWay`, `Search`, `Effectiveness`, `ForecastCompare`, `Accuracy`, `Recon`, `Audit`) |
| `<vN>` | File sequence for that base name, starting at `v1`, monotonic, never reused. Also recorded in the stamp (`Pack_Stamp_FileVersion`) |

**Sanitisation (applied to every token, in order):**

1. Replace Windows-reserved characters `< > : " / \ | ? *` and control characters `0x00–0x1F` with `-`.
2. Collapse runs of `-`; trim leading/trailing `-`, dots and spaces (Windows rejects trailing dot/space).
3. Cap each token at 40 characters (truncate the middle, insert `-`); cap the whole filename at 180
   characters; if the *full path* would exceed 240 characters, shorten `<Project>` (then `<Entity>`) and
   state the shortening on `Cover` row 4. 240 leaves headroom under the 260-character Windows limit and
   under long data folders.
4. Reserved device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1`…`COM9`, `LPT1`…`LPT9`, case-insensitive,
   with or without extension) get a trailing `_` — a project named `CON` must not produce an unwritable
   file.
5. Unicode is allowed in display names but not in filenames: non-ASCII characters are transliterated
   (NFKD, diacritics stripped) then any remainder is `-`. ₹ in the project name is stripped, never written.

**Collision policy (Addon 2 §D.12):**

| Situation | Behaviour |
|---|---|
| Target file does not exist | Write directly (temp file → atomic move) |
| Target file exists | **Modal prompt** (never silent): *"A file named `<name>` already exists in `<folder>`. What would you like to do?"* with buttons **Keep both (recommended)** → writes `_v<N+1>`; **Overwrite** → replaces after moving the existing file to `.recycle/` inside the export folder (recoverable, §12); **Choose another folder**. Default focus = Keep both |
| Target file exists but is **open in Excel** (write-locked) | Overwrite is disabled in the prompt with the reason *"This file is open in Excel. Close it, or keep both."* Keep-both proceeds |
| Folder is read-only / permission denied | Prompt names the folder and offers **Choose another folder**; the export folder default is `%USERPROFILE%\Documents\FP&A Month-End Copilot\Exports\<project>\` |
| Folder is inside a OneDrive/synced path | Warning per `ADR-004` (*"This folder syncs to the cloud. Client data will leave this machine."*) with a **Choose another folder** action; proceeding is allowed but recorded in the audit trail (`export_to_synced_path`) |

**Export folder structure (created on first export):**

```
…\Exports\<project>\
    FY26-P09\                       ← period folder (current filter's primary period)
        AcmeManufacturing_IN01_FY26-P09_MonthEnd_v1.xlsx
        AcmeManufacturing_IN01_FY26-P09_MonthEnd_v1.refresh.json   ← §3.9 when refreshed
        AcmeManufacturing_IN01_FY26-P09_MonthEnd_v1.meta.json      ← CSV sidecar only (never for .xlsx)
    Evidence\
        AcmeManufacturing_IN01_FY26-P09_Evidence-EXC-018_v1.xlsx
    .recycle\                       ← overwritten files, kept 30 days, purged by `doctor`
```

### 3.5 Sheet naming, order, tab colours, workbook properties

| Rule | Detail |
|---|---|
| Sheet names | Exact strings from §4. ≤ 31 characters, no `[ ] : * ? / \`, unique per workbook. Names are **contract**, not cosmetic — tests match them |
| Sheet order | Exactly the order in §2/§4. Omitted sheets are omitted from the workbook (not left empty); the omission reason appears on `Cover` row 4 and in the sheet index |
| Sheet visibility | All sheets `visible`. **Never hidden, never `veryHidden`** — a hidden sheet is how data goes missing in a forwarded pack |
| Tab colours | `Cover` brand slate `1F3A5F` · `BvA Summary` `2E7D32` · `BvA Bridge` `4C8C4A` · `Transaction Detail` `9AA0A6` · `Exception Register` `B7791F` · `Forecast Summary` `1A4FA0` · `Import Reconciliation` `6A5ACD` · `Audit Trail` `5F6368` |
| Gridlines | On for data sheets, off for `Cover` |
| Protection | **None.** No sheet protection, no workbook protection, no password, no macro (`.xlsx`, never `.xlsm`) — the client must be able to filter, sort and copy their own data |
| Workbook properties | `title` = `<Project> — <Period(s)> — <PackName>`, `creator` = `FP&A Month-End Copilot <version>`, `description` = `Pack v<N> · stamp hash <ContentHash>`, `keywords` = `FP&A, month-end, <period>`, `language` = `en-IN` |
| Document links | **No external links, no hyperlinks to the internet.** The only hyperlinks are the internal sheet index on `Cover` (`#SheetName!A1`), capped at 20 |
| Merged cells | **Forbidden in data tables and header rows 2–7** (breaks sorting, filtering and re-import). Permitted only in row 1 and the `Cover` layout blocks. A test asserts no merged range intersects a data table (`TST-XL-06`) |
| Row/column limits respected | Style reuse ≤ 40 distinct cell styles per workbook (§12.3), ≤ 50 conditional-format ranges per sheet, ≤ 65,530 hyperlinks (we use ≤ 20), cell text ≤ 32,767 characters (descriptions are ≤ 500 by `03`) |

### 3.6 Number-format dictionary

Formats are **write-side constants** in `app/engine/exports/formats.py` and are referenced by ID in the
column tables of §4. `m` = money, `p` = percent (stored as a fraction), `pp` = percentage points,
`c` = count/row count, `d` = date, `t` = timestamp, `x` = text/code.

| ID | Name | Format string | Rendered examples | Used for |
|---|---|---|---|---|
| `XLS-FMT-001` | `MONEY_IN` — Indian grouping | `₹ #,##,##,##0.00;(₹ #,##,##,##0.00);₹ 0.00` | `₹ 1,08,00,000.00` · `(₹ 25,000.00)` · `₹ 0.00` | All money when the project grouping is Indian (default) |
| `XLS-FMT-002` | `MONEY_INTL` — international grouping | `₹ #,##0.00;(₹ #,##0.00);₹ 0.00` | `₹ 10,800,000.00` · `(₹ 25,000.00)` | All money when the project grouping is international |
| `XLS-FMT-003` | `MONEY_SCALED` | `#,##0.00;(#,##0.00);0.00` | `108.00` under an `₹ in lakhs` label | Money cells when scale ≠ whole units; **the unit label is mandatory in row 1** |
| `XLS-FMT-004` | `PCT_1DP` | `0.0%;(0.0%);0.0%` | `8.0%` · `(6.6%)` · `0.0%` | Variance %, KPI ratios |
| `XLS-FMT-005` | `PP_1DP` | `+0.0" pp";-0.0" pp";0.0" pp"` | `+1.5 pp` · `-1.5 pp` · `0.0 pp` | Ratio comparisons in percentage points |
| `XLS-FMT-006` | `RATIO_2DP` | `0.00;(0.00);0.00` | `1.25` · `(0.30)` | Multiples, cost-per-head, burn multiple |
| `XLS-FMT-007` | `COUNT_INT` | `#,##0;(#,##0);0` | `1,048,576` · `14` · `0` | Row counts, exception counts, day counts — **international grouping always** (a count is metadata, not money; the rule is stated on `Cover`) |
| `XLS-FMT-008` | `DATE_DMY` | `dd-mm-yyyy` | `14-09-2026` | Real Excel date values (never text) |
| `XLS-FMT-009` | `TS_DMY` | `dd-mm-yyyy hh:mm` | `01-10-2026 14:22` | Stamps, audit timestamps (24-hour, project locale-independent) |
| `XLS-FMT-010` | `TEXT` | `@` | `Possible duplicate invoice` | Free text, wrapped columns |
| `XLS-FMT-011` | `CODE` | `@` | `0400-10` · `CC-140` | **Codes are written as text**, never numbers — a leading zero must never be lost, and Excel must never auto-convert `0400` to `400` |
| `XLS-FMT-012` | `HASH` | `@` | `9f2c…` (short) | SHA-256 fingerprints, printed in a monospaced font |
| `XLS-FMT-013` | `DAYS` | `0" d"` | `4 d` | Age in days |
| `XLS-FMT-014` | `LABEL` | `@` | `Fav ▲` · `n/a` | Signal/flag columns |
| `XLS-FMT-015` | `BPS_1DP` | `+0.0" bp";-0.0" bp";0.0" bp"` | `+15.0 bp` | Reserved: only if a PRD decision introduces basis-point reporting; unused in v1 |

**Format rules:**

1. **Indian grouping is the default** (`XLS-FMT-001`) and is a project setting (`08` §15, `SCR-036`); it
   applies uniformly to app, Excel and PPT.
2. **The grouping pattern is verified, not assumed.** The pattern's group rhythm is `[3, 2, 2, 2]` and
   Excel drops separators for absent digit groups. This behaviour is proven by the boundary matrix in
   §13 (`TST-XL-07`, 14 cases) on the real Windows build; if any case fails to render exactly as
   specified, the fallback is the two-separator pattern `#,##,##0.00` with a `CF`-applied number format
   for values ≥ 10 crore, and the failing contract text is corrected in this document first (never patched
   silently in code).
3. **Percentages are stored as fractions** (`0.0795` renders as `8.0%`), never pre-multiplied with a
   textual `%`. Rounding is display-only (`05` §6.1); the stored value keeps full precision.
4. **Money is written as a number at exactly 2 decimal places** (the engine's stored precision — no
   loss), as `float(Decimal)`. Values are quantised before conversion; the cross-artifact test compares
   at 2 dp.
5. **`—` and `n/a` are text inside numeric columns.** They are the only two non-numeric tokens permitted
   in a numeric column, they are never interchangeable (`08` §14 `CF-003`), and a real zero is always
   `0.00` (or `₹ 0.00`). Consequence, stated for the record: a mixed column cannot be summarised by
   Excel's status bar; the pack's own control rows carry the totals.
6. **Dates are real dates**, formatted `dd-mm-yyyy`. Never text. A text date breaks sorting and the
   cross-artifact test.
7. **Negative percentages use parentheses** (`(6.6%)`), matching money; the minus sign remains the
   unambiguous fallback anywhere formatting is lost (CSV, plain text).
8. **Scaled values always carry the label.** Any sheet/graph with scale ≠ whole units prints
   `₹ in thousands` / `₹ in lakhs` in row 1; a scaled number without the label is a defect
   (`TST-XL-09`).
9. `COUNT_INT` and `XLS-FMT-007` are used for all counts even under Indian grouping — disclosed in the
   `Cover` units block so nobody reads `1,048,576` as a money-style inconsistency.

### 3.7 Conditional formatting — the single rule set, rendered in Excel

`08` §14 defines `CF-001`…`CF-012` once. Excel renders them; **no sheet invents a colour**. Excel cannot
inject text through conditional formatting, so the contract has two halves: the *colour* (a CF rule) and
the *non-colour signal* (a real column value written by the engine). The signal column is mandatory —
it is what survives greyscale printing, colour-blindness and a copy-paste into a plain-text channel.

| CF | Excel rule type | Applied to | Fill | Font | Border | Non-colour signal (a written column value) |
|---|---|---|---|---|---|---|
| `CF-001` Favourable variance | Formula: `=$<signalCol>="Fav ▲"` (or a numeric favourability column `=1`) | Variance and Var % cells of BvA Summary/Bridge; favourable rows on Top-N blocks | `E8F5E9` | `1B5E20` | — | `Fav ▲` in the row's `Signal` column |
| `CF-002` Unfavourable variance | Formula: `=$<signalCol>="Adv ▼"` | Same | `FDECEA` | `B3261E` | — | `Adv ▼` |
| `CF-003` Neutral / not applicable | Cell-is-equal to `"—"` or `"n/a"` | Every numeric column | `F3F4F6` | `6B7280` | — | The text itself (`—` / `n/a`) |
| `CF-004` Severity High | Formula on the severity column = `"High"` | Exception rows (register, bundle, detail-with-exceptions) | `F6D5D3` | `7A1C16` | — | `High` (with the icon glyph column `Severity icon` = `▲`) |
| `CF-005` Severity Medium | `="Med"` | Same | `FDF0D5` | `7A5200` | — | `Med` + `◆` |
| `CF-006` Severity Low | `="Low"` | Same | `E3F1E6` | `1F5C2C` | — | `Low` + `●` |
| `CF-007` Beyond materiality threshold | Formula: `=AND(ISNUMBER($<varCol>),ABS($<varCol>)>=$<thresholdCol>)` | Variance cells | none | bold | thick left, `B7791F` | Bold cell + the `Effective threshold` column on the row carrying the exact threshold text (`materiality 2.0% or ₹500,000`) |
| `CF-008` Overdue exception | Formula: `=$<overdueDaysCol>>0` | Register age cells | `FFF4E5` | `8A5300` | — | `Overdue 12 d` in the `Overdue` column |
| `CF-009` Stale derived result | Static fill on the inserted banner row (§3.3) | Banner row on every sheet | `FFF4E5` | `8A5300` | top+bottom, `B7791F` | Banner text naming what changed |
| `CF-010` Quarantined / unresolved | Formula on `Quarantine` count column `>0` | Import Reconciliation rows | `E8F0FE` | `1A4FA0` | — | `8 rows need attention` text |
| `CF-011` Zero amount | Formula: `=AND(ISNUMBER(x),x=0)` | Money columns | none | `9AA0A6` | — | `₹ 0.00` kept visible; never hidden, never blanked (`02` E4) |
| `CF-012` Sample-data artefact | Static fill + rotated band (§3.3) | Whole used range on every sheet | `FFF9C4` | `6B5B00` | — | Header-band text + `Sample data: Yes` stamp + filename-independent banner |

**CF implementation rules:**

1. Rules are applied to the **exact ranges in §4**, expressed with absolute-free formulas so they work
   under autofilter and row insertion (Excel adjusts relative references).
2. `stopIfTrue = True` on `CF-001`/`CF-002` (favourability wins over the zero rule); severity rules do
   not intersect variance rules in the same range, so no ordering subtleties elsewhere.
3. **Order matters and is fixed**: `CF-004/005/006` (severity) → `CF-008` (overdue) → `CF-001/002`
   (favourability) → `CF-007` (threshold) → `CF-011` (zero) → `CF-003` (neutral text) → `CF-012`.
   Severity is never overridden by favourability.
4. Contrast: every `fill`/`font` pair above is ≥ 4.5:1 (AA) — verified by `TST-XL-11` against the
   contrast formula, with the greyscale test asserting the signal text still distinguishes the states.
5. The colour values above are the **v1 export theme**. A test (`TST-XL-10`) re-derives them from
   `ui/theme/tokens.ts` and asserts equality, so the Excel theme cannot drift from the app theme
   (`08` §19.3: components consume roles, never hex). If the client supplies a house style (§9), only
   *brand* colours may change; every `CF-` colour above is **semantic and non-negotiable**.
6. Greyscale legibility is a release gate: the pack is rendered to PDF and each sheet asserted to still
   show the signal text (`TST-XL-11`).

### 3.8 Freeze panes, autofilters, widths, sorting

| Aspect | Rule |
|---|---|
| Freeze panes | `C7` on every data sheet (freezes identifier columns A–B and the header block + table header). `B7` where a single identifier column suffices (`Audit Trail`). `Cover` has no freeze |
| Autofilter | Enabled on the table header row (row 6) on every data sheet, spanning all data columns and all data rows. Never applied to header block rows |
| Sorting | The engine writes rows in a **deterministic order** per sheet (sort keys in §4). The autofilter lets the user re-sort freely; the *written* order is what tests and diffs rely on |
| Tie-breakers | Every sort ends with a unique key (voucher no → line no, or exception id) so two runs from identical data produce identical files |
| Column widths | Explicit widths per §4 column tables, unit = Excel "characters". Rules: minimum 8, maximum 48 (60 for description columns), never auto-fit (auto-fit is not reproducible and produces absurd widths on long text) |
| Wrap | On for text/description/note columns and header row 6; off elsewhere. Wrapped rows get height 30 (or 45 where the column table says so) |
| Long text | Written in full. The pack **never truncates data** to fit a column — a truncated description would be a data-integrity defect. Users widen the column; the CSV export carries the same full text |
| Numeric alignment | Right, tabular font (Calibri or the house font). Text left. Codes left. Dates centred. Booleans centred |
| Row heights | Header block rows per §3.3; data rows default 15 (single line) / 30 (wrapped). Never set per-row heights from content (unstable file sizes) |
| Banding | Alternating row fill `FAFAFA` on even data rows via a `CF`-free static style per row is forbidden (style explosion, §12.3). Use Excel's native table banding only where a sheet is written as an Excel Table — we do **not** use Excel Tables (`ListObject`) in v1: they conflict with split sheets and re-import. Documented consequence: no native banding; row readability comes from borders and the totals styling |
| Borders | Thin bottom border `E0E0E0` under the header row; thin top border on control/total rows |

### 3.9 Refresh, staleness and the refresh log

| Concept | Contract |
|---|---|
| Refresh trigger | `SCR-029` → "Refresh this pack" on a pack row; CLI `export-xlsx --refresh <file>` |
| Mechanism | The app stores the export context in `FactExport` (`03` §5.7) — filter JSON, pack token, file version, batch IDs, house-style profile, content hash. Refresh reloads that context, regenerates with current data, and writes the next `vN` |
| Change summary | A sidecar `<same-basename>.refresh.json` is written next to the new workbook **only when a refresh produced differences** (never for a first generation) |
| Stale results | If thresholds, master data, mappings or rules changed since the last rule run, the pack is generated **with** the `CF-009` banner and `Pack_Stamp_Stale = Yes`; generation is allowed (the analyst may need the pack now) but the pack cannot be *issued* until the stale state clears (`FR-XC-003` gate) |
| File version vs pack version | `vN` is the file sequence for a base name and equals the pack version when the file is issued (§3.4). The stamp carries both fields explicitly so there is never a second, invisible numbering scheme |

`<basename>.refresh.json` schema (validated on write; read by `SCR-029` to show the change list):

```json
{
  "schema": "fpa.refresh.v1",
  "previous_file": "AcmeManufacturing_IN01_FY26-P09_MonthEnd_v2.xlsx",
  "previous_content_hash": "sha256:6a1f...",
  "new_content_hash": "sha256:9f2c...",
  "regenerated_at": "2026-10-01T14:22:31+05:30",
  "context_changed": false,
  "row_count_delta": { "BvA Summary": 0, "Transaction Detail": 41, "Exception Register": 3 },
  "values_changed": { "cells": 57, "sheets": ["BvA Summary", "Exception Register"] },
  "batch_ids_added": [1044],
  "batch_ids_voided": [],
  "summary_text": "Re-imported batch 1044 (41 rows); 3 exceptions added; 57 values changed in BvA Summary and Exception Register."
}
```

### 3.10 Screen/export parity ("export what you see")

| Rule | Detail |
|---|---|
| Columns | An ad-hoc export (`XL-010`) contains **exactly the columns visible** in the view, in visible order, with the same header labels as the screen |
| Rows | Exactly the filtered, sorted row set the user is looking at. The applied filter is stated in row 2 and row 4 of the header block, and in the Cover stamp for a pack |
| Filters | Multi-select, text search and numeric filters all reflected. The export of a filtered view is **not** expanded to the full dataset unless the user picks "Export all rows" explicitly |
| Sort | The visible sort is preserved in the file; the deterministic tie-break still applies inside ties |
| Hierarchy | A collapsed hierarchy exports its **visible rows only** by default, with the option "Include collapsed rows" (default off), and the export states which was used |
| Unavailable columns | A column the user hid is absent. A column with no data in the current filter is still present (an empty column is information) |
| Register export (`FR-EXC-018`) | Two sheets in one workbook: `Register (filtered)` — the current filter — and `All exceptions` — unfiltered, so nothing is ever invisible by accident. Row counts on both sheets must match the register counts for the same filter (`TST-XL-19`) |

### 3.11 Empty, zero and not-available states inside a workbook

| State | Rendering | Never |
|---|---|---|
| No rows for the filter | The sheet is still written, with the header block, the table header, and **one italic row** in column A: the sheet's empty-state message from `08` §17 (e.g. *"No open exceptions — nothing requires review."*) plus, for the Cover index, the row count `0` | Never omit the sheet silently; never write a sheet with only headers and no explanation; never write an "N/A" table |
| A real zero | `₹ 0.00` / `0.0%` / `0` (with `CF-011`) | Never blank; never `—` |
| Nothing to compare | `—` (with `CF-003`) | Never `0.00` |
| Undefined ratio | `n/a` (with `CF-003`) | Never `0.0%`; never `#DIV/0!` |
| Row excluded by rule | Absent, and the count of excluded rows stated in row 4 where a control total would otherwise not tie | Never silently dropped from a control total |
| Sheet omitted for a stated reason | Not present in the workbook; the reason appears on `Cover` row 4 and in the sheet index (`Sheet omitted — no forecast version`) | Never an empty placeholder sheet |

### 3.12 Locale independence

1. All number formats use explicit separators and explicit currency symbols — the workbook renders
   identically on a Windows machine set to any locale, because nothing depends on the OS list separator
   or the system date format.
2. Values are written as numbers/dates; **no locale-formatted strings** are written except where the
   contract says text (`—`, `n/a`, codes).
3. Dates are written as `datetime.date`/`datetime.datetime` objects with `XLS-FMT-008/009`.
4. The header/footer, the stamp and every user-facing label are English (`08` §18: English v1).
5. The file contains no locale-specific function names (another consequence of having no formulas).

### 3.13 Watermark and sample-data mode

When the project is the sample project (`CF-012`):

1. Every sheet's used range receives the pale `FFF9C4` fill and the rotated band text
   `SAMPLE DATA — NOT CLIENT DATA` (rows 2–4, column A band, grey 10 pt, 45°).
2. Row 1's title is suffixed ` — SAMPLE DATA`.
3. The `Cover` stamp carries `Sample data: Yes — not client data`.
4. A banner row above row 1: *"This workbook was generated from the built-in sample project. It contains no client data."*
5. When the client's own data is loaded, all four signals disappear in the same generation — the mode is
   a property of the project, not a manual switch a user can forget to turn off.

### 3.14 File size, generation time and protection of the contract

| Budget | Value at 250,000 detail rows | Notes |
|---|---|---|
| Month-end pack generation | ≤ 120 s (progress + cancel) | `NFR-009` (`14` §3); the deck is ≤ 15 s (`NFR-004`) |
| Month-end pack file size | ≤ 150 MB typical; hard fail at 300 MB with a stated reason and a "summary only" option | 26 columns × 250k rows of text is the size driver |
| Evidence bundle | ≤ 5 MB typical; warn over 25 MB and offer the zip form | |
| Ad-hoc export | ≤ 20 s for 250k rows | |
| Memory during export | ≤ 1.5 GB total process (`NFR-005`) | Write-only workbook mode, no DataFrame materialisation of the full sheet |

Contract-protecting implementation constraints (the *how*, binding because they protect the *what*):

1. **Write-only mode** (`openpyxl` `Workbook(write_only=True)`) for any sheet over 50,000 rows, with
   styles referenced from a pre-built style cache; freeze panes, autofilter, column widths and page
   setup are set **before** rows are written (write-only workbooks cannot be mutated afterwards).
2. **Style reuse:** a maximum of 40 distinct `NamedStyle`/style objects per workbook, created once. No
   per-cell `Font`/`Fill` construction (this is the classic cause of 100 MB+ workbooks and unusable open
   times; also protects the 65,490 unique-format limit).
3. **Single pass:** values are streamed from DuckDB in the sheet's sort order straight to rows — no
   intermediate full-sheet Python list.
4. **Temp-then-move:** every workbook is written to `<target>.tmp` in the same folder and atomically
   moved on success, then the `FactExport` row is committed. A cancelled or failed export leaves no
   partial file (a leftover `.tmp` is purged by `doctor`).
5. **CSV** is written with `csv.writer` and `newline=""`, `utf-8-sig`, one pass, no pandas.

### 3.15 Cross-document obligations created by this document

| Obligation | Owner |
|---|---|
| `FactExport` table (context, content hash, file names) | `03` §5.7 and the §2.1 grain register — **added in this pass**, so the refresh contract has a real home |
| `ERR-EXP-001`…`ERR-EXP-011` message-catalog entries for every failure in §12 | `26` |
| Test IDs `TST-XL-01`…`TST-XL-26` implemented, plus the greyscale and cross-artifact tests | `14` |
| PPT placeholder values must equal the pack's control-row values | `12` §, §11 here |
| API endpoints for generate/refresh/evidence/register/owner-dist | `26` |
| User-guide instructions for exporting, collision prompts, CSV sidecars | `22` |
| `app/engine/exports/formats.py` constants frozen to §3.6 IDs; theme re-derivation test | `17` (standards), `14` |

## 4. The month-end pack, sheet by sheet

Common to every sheet below: the four-row header block (§3.3), the spacer row 5, the header row 6 with
autofilter, freeze panes at `C7`, deterministic sort, values-only, the tab colour from §3.5, the footer
from §10, and the `CF-` rules from §3.7. Column tables list **every** column in order; the format ID
resolves through §3.6.

### 4.1 `Cover` (`XL-001`)

**Purpose:** make the workbook self-describing — what it is, what data is behind it, what the numbers
tie to, how to read it — for a reader who received only this file.

**Layout (rows):**

| Rows | Content |
|---|---|
| 1–4 | Header block (§3.3). Row 1: `Month-end pack — <Project>` + units label. No stale banner row unless stale |
| 6 | Section header `Workbook stamp` |
| 7–36 | The 30-field stamp table (§3.2): labels in column A, values in column B, defined names on B7:B36 |
| 38 | Section header `Contents` |
| 39 | Table header: `Sheet` · `Rows` · `Included` · `Note` |
| 40–47 | One row per pack sheet in workbook order, column A hyperlinked to `#<SheetName>!A1`. `Included` = `Yes` / `Omitted — <reason>`. `Rows` = data row count written (`0` when empty; `—` when omitted) |
| 49 | Section header `Control totals (read this before quoting a number)` |
| 50 | Table header: `Control` · `Value` · `Source` · `Check` |
| 51–60 | One row per control figure: `Actual (total)`, `Budget (total)`, `Variance (total)`, `Variance % (total)`, `Forecast landing estimate`, `Exceptions — open`, `Exceptions — overdue`, `Exceptions — high severity`, `Import balance variance`, `Data-quality score`. `Source` states the sheet and the control row label it comes from (e.g. `BvA Summary · row "Totals"`). `Check` = `OK` where a control comparison applies, else `—` |
| 62–68 | Section header `How to read this workbook` down to the five bullets in the field guide below |
| 70–73 | Section header `Disclaimer` + the short form verbatim + the pointer to `About → Diagnostics` for the full text (`01` §15.1–§15.2) |

**Field guide (the five bullets, written verbatim into the sheet):**

```
1. Every number in this workbook is a static value from the FP&A Month-End Copilot engine. There are no
   formulas — press F9 and nothing will change. To update the numbers, use "Refresh this pack" in the app.
2. "—" means there was nothing to compare. "n/a" means the percentage is undefined (a zero denominator).
   "₹ 0.00" is a real zero. They are never interchangeable.
3. Green/red shading marks favourable/unfavourable and is always accompanied by a text label
   (Fav ▲ / Adv ▼) in the Signal column, so the meaning survives black-and-white printing.
4. Filters used to build this pack are printed in the stamp above and repeated on every sheet's row 2.
5. This is an advisory analysis pack, not an audited statement. Every figure must be reviewed by a
   qualified accountant before it is used for a business decision, filing or external reporting.
```

Columns: A `Label` (34, text) · B `Value` (78, text/date/number, wrap) · C `Source` (30, text) ·
D `Check` (10, text) · E `Note` (60, text, wrap, optional).
Freeze: none. Autofilter: none. Gridlines: off. Sort: fixed order as above.
Empty/omitted behaviour: `Cover` is **always** present, in every pack, including an empty project (the
control rows then read `0` / `n/a` and `Check` = `—`).
Print: portrait A4, fit to width 1, area `A1:E73`.

**Control-row formula-free checks** (each is a comparison performed by the engine before writing, and the
result is written as text): variance = actual − budget (`CALC-010`); variance % per `CALC-011`;
`Check` = `OK` when the value recomputed from the written sheets equals the value written in the control
row; otherwise `CHECK FAILED — <detail>` and generation raises `ERR-EXP-004` (§12). A generated pack can
therefore never contain a control row that contradicts its own sheets.

### 4.2 `BvA Summary` (`XL-002`)

**Purpose:** the budget-vs-actual matrix the pack exists for (`FR-BVA-001`), at the filter's grain, with
hierarchy, favourability, materiality emphasis, and the approved commentary line where one exists.

**Inclusion:** always present. If the filter returns no rows, the empty-state row is written (§3.11).

**Sort:** hierarchy order (COA sequence, parents before children), then cost-centre code, then account
code. The final `Totals` row is last. `Rank` is computed over non-total rows by `|Variance|` descending.

| # | Header | Type | Format | Width | Notes |
|---|---|---|---|---|---|
| A | `Level` | int | `XLS-FMT-007` | 7 | 0 = company total, 1 = account group, 2 = account, 3+ = sub-account |
| B | `Account code` | text | `XLS-FMT-011` | 12 | Text, never numeric (leading zeros) |
| C | `Account name` | text | `XLS-FMT-010` | 34 | Indented 2 spaces per level; Excel outline grouping also applied |
| D | `Account type` | text | `XLS-FMT-010` | 12 | `revenue` / `expense` / `neutral` — drives `CF-001`/`CF-002` eligibility |
| E | `Cost centre` | text | `XLS-FMT-011` | 14 | `All` when the matrix is not at cost-centre grain |
| F | `Actual` | money | `XLS-FMT-001` | 16 | Window per `Pack_Stamp_Window` (MTD/YTD/PY/TTM) |
| G | `Budget` | money | `XLS-FMT-001` | 16 | Budget version from the stamp |
| H | `Variance` | money | `XLS-FMT-001` | 16 | `CALC-010`; `CF-001`/`CF-002`/`CF-007` apply |
| I | `Var %` | percent | `XLS-FMT-004` | 10 | `CALC-011`; zero-budget → `n/a`, no-budget-row → `—` |
| J | `Signal` | text | `XLS-FMT-014` | 13 | `Fav ▲` / `Adv ▼` / `—` (`CF-001`/`CF-002`/`CF-003`) |
| K | `Effective threshold` | text | `XLS-FMT-010` | 26 | The exact threshold text where `CF-007` fires (e.g. `materiality 2.0% or ₹500,000`), else `—` |
| L | `Rank` | int | `XLS-FMT-007` | 8 | Rank by absolute variance within the sheet (PPT top-N linkage) |
| M | `Rows` | int | `XLS-FMT-007` | 9 | Contributing transaction count — the drill traceability witness (`FR-BVA-004`) |
| N | `Commentary` | text | `XLS-FMT-010` | 48 | Approved commentary line for the row when present (`FR-XC-001`); wrap on, row height 45; provenance per `Pack_Stamp_AIContent`. Empty when none — never placeholder text |

**Hierarchy and controls:**

- Outline grouping: level 1 rows at `outlineLevel = 1`, level 2 at `2`, level 3 at `3`;
  `outlinePr.summaryBelow = False` (the parent row sits above its children, matching `08` §9.2);
  `sheet_view.showOutlineSymbols = True`; **default state: fully expanded** — the pack never hides rows
  on open. Collapsing is a convenience for the reader.
- `Totals (N accounts)` row immediately after the last data row: `F`, `G`, `H` summed over **level-1 rows
  only** (never double-counting children), `I` = total variance % per `CALC-011`, `J` blank, `L`/`M`
  blank, `N` carries the sum-of-rounded footnote when rounding differences exist (`CALC-031`).
- Rollup invariant checked before write: for every parent, `parent = Σ children` exactly (`CALC-042`,
  `FR-BVA-009`); a mismatch raises `ERR-EXP-004` rather than writing a pack that fails its own tie.
- Grouped-entity labelling: where more than one entity is in scope, row 4 and the totals row carry
  *"Simple sum — no eliminations"* (`FR-BVA-014`).
- Grain disclosure: `Pack_Stamp_Grain` and row 2 state the comparison grain and the budget grain
  (`FR-BVA-013`).

**Empty state:** row 7 (first data row) = italic, `—` in all numeric columns, message in column A:
*"No data for this filter."* plus the reset hint from `08` §17; the totals row still prints with
`₹ 0.00`. Row 4 states the filter that produced the empty result.

**Print:** A4 landscape, fit to width 2, print titles rows 1–6 and columns A:B (§10).

### 4.3 `BvA Bridge` (`XL-003`)

**Purpose:** the waterfall *data* behind the bridge chart (`FR-BVA-005`) so a reader can re-derive the
bridge by hand, and so the PPT bridge slide (§`12`) and the workbook cannot disagree.

**Inclusion:** present when the filter resolves to a **single period and a single window**; otherwise
omitted with the reason on `Cover` row 4: *"BvA Bridge omitted — the bridge is a single-period view; the
current filter spans <P1>–<P2>."* Present with the empty-state row when the period has no variance at all.

**Sort:** `Order` ascending, fixed by the engine's bridge builder: opening (budget) → adverse drivers by
absolute amount descending → favourable drivers by absolute amount descending → closing (actual). Ties
broken by driver label, then account code.

| # | Header | Type | Format | Width | Notes |
|---|---|---|---|---|---|
| A | `Order` | int | `XLS-FMT-007` | 6 | 0 = opening, 1…n = driver steps, 99 = closing |
| B | `Step` | text | `XLS-FMT-010` | 14 | `Opening (Budget)`, `Driver`, `Closing (Actual)` |
| C | `Driver` | text | `XLS-FMT-010` | 34 | Account/group label the step belongs to |
| D | `Account code` | text | `XLS-FMT-011` | 12 | Blank on opening/closing rows |
| E | `Direction` | text | `XLS-FMT-014` | 10 | `▲` / `▼` / `—` |
| F | `Amount` | money | `XLS-FMT-001` | 16 | Signed step amount (`CALC-010`) — a favourable expense step is negative |
| G | `Cumulative` | money | `XLS-FMT-001` | 18 | Running total from the opening value |
| H | `Signal` | text | `XLS-FMT-014` | 13 | `Fav ▲` / `Adv ▼` / `—` |
| I | `Effective threshold` | text | `XLS-FMT-010` | 26 | Per §4.2 column K |
| J | `Note` | text | `XLS-FMT-010` | 40 | Driver explanation where the engine has one (e.g. *"includes the ₹5,40,000 repairs variance"*), else empty |

**Controls (three rows after the steps):**

| Control row | Contents |
|---|---|
| `Budget total (opening)` | `G` = opening value; must equal `BvA Summary` budget total for the same filter |
| `Σ drivers` | `F` = sum of steps 1…n |
| `Actual total (closing)` | `G` = closing value; must equal `BvA Summary` actual total |
| `Check` | Text: `Opening + Σ drivers = Closing — OK` or `CHECK FAILED — <detail>`; a mismatch raises `ERR-EXP-004` |

**Empty state:** the opening and closing rows are written with `₹ 0.00` and the driver area carries
*"No variances to bridge in this window."*
**Print:** A4 landscape, fit to width 1, print titles rows 1–6.

### 4.4 `Transaction Detail` (`XL-004`)

**Purpose:** the row-level evidence behind every summary figure (`FR-BVA-004`), exportable to an
accounting team without further assembly; the drill export, the pack's detail sheet, and the basis of the
evidence bundle (`XL-009`) are the **same column contract**.

**Inclusion:** present by default. Omitted only when the user explicitly picks *"Summary pack (no
transaction detail)"* in `SCR-029` — `Cover` row 4 then reads *"Transaction Detail omitted at the user's
request (`summary_only`) — the summary figures are unaffected."*

**Sort:** period, account code, cost-centre code, voucher no, line no, then source row reference. Period
ascending, then the rest ascending. Unique tie-break: voucher no + line no.

| # | Header | Type | Format | Width | Notes |
|---|---|---|---|---|---|
| A | `#` | int | `XLS-FMT-007` | 7 | 1-based within the sheet; continues across split sheets (so row 1 of sheet 3 is `250001`) |
| B | `Entity` | text | `XLS-FMT-011` | 10 | Company/entity code |
| C | `Account code` | text | `XLS-FMT-011` | 12 | |
| D | `Account name` | text | `XLS-FMT-010` | 30 | |
| E | `Cost centre` | text | `XLS-FMT-011` | 12 | Empty when legitimately absent in source (`03` §4.1) |
| F | `Department` | text | `XLS-FMT-010` | 16 | Where reported separately |
| G | `Project` | text | `XLS-FMT-011` | 14 | |
| H | `Vendor` | text | `XLS-FMT-010` | 24 | Display name from master data |
| I | `Vendor code` | text | `XLS-FMT-011` | 12 | |
| J | `Period` | text | `XLS-FMT-011` | 10 | `FY26-P09` (assigned from posting date per `05`) |
| K | `Posting date` | date | `XLS-FMT-008` | 12 | Real date |
| L | `Document date` | date | `XLS-FMT-008` | 12 | Real date; empty when absent |
| M | `Voucher no` | text | `XLS-FMT-011` | 20 | |
| N | `Document no` | text | `XLS-FMT-011` | 18 | |
| O | `Invoice no` | text | `XLS-FMT-011` | 18 | |
| P | `Line` | int | `XLS-FMT-007` | 6 | |
| Q | `Description` | text | `XLS-FMT-010` | 60 | Full text (`≤ 500` chars), wrap on, height 30, **never truncated** |
| R | `Journal category` | text | `XLS-FMT-010` | 13 | `manual` / `auto` / `reclass` / `accrual` / empty |
| S | `Debit` | money | `XLS-FMT-001` | 16 | |
| T | `Credit` | money | `XLS-FMT-001` | 16 | |
| U | `Net` | money | `XLS-FMT-001` | 16 | `debit − credit` (`CALC-007`), signed |
| V | `Dr/Cr` | text | `XLS-FMT-014` | 7 | `Dr` / `Cr` / `—` for zero — the non-colour sign signal |
| W | `Currency` | text | `XLS-FMT-011` | 8 | Single project currency (`01` §6); mixed rows never reach here |
| X | `Source system` | text | `XLS-FMT-010` | 12 | `D365` / `Payroll` / `Procurement` |
| Y | `Source file` | text | `XLS-FMT-010` | 28 | As received |
| Z | `Source row ref` | text | `XLS-FMT-011` | 14 | `Sheet1!A412` / `line 412` — the evidence pointer |
| AA | `Batch ID` | int | `XLS-FMT-007` | 10 | Traceability invariant (`03` §4.1) |
| AB | `Fingerprint` | text | `XLS-FMT-012` | 14 | First 12 hex characters of `row_fingerprint` (the full value is in the database and the audit sheet) |
| AC | `Exception IDs` | text | `XLS-FMT-011` | 24 | Comma-separated `EXC-nnn` raised on this row; empty when none. Omitted (column absent, not blank) when no register is in scope |

**Controls (rows after the last data row):**

| Control row | Contents |
|---|---|
| `Subtotal (this sheet)` | `S`, `T`, `U` sums over this sheet's rows; `A` column shows `Σ of rows shown: N` |
| `Total (all split sheets)` | Present only on split exports: the grand totals across all split sheets, so a page subtotal can never be mistaken for the grand total |
| `Check` | `Σ Debit − Σ Credit = ₹<x> — matches Import Reconciliation variance` or `CHECK FAILED — <detail>` (`CALC-071`); a mismatch raises `ERR-EXP-004` |

Row 4 always states the row accounting: `Rows shown: 250,000 of 1,240,000 · split across 5 sheets` or
`Rows shown: 250,000 of 1,240,000 · filtered to the first N by <sort>` when the user limited the export.

**Empty state:** *"No transactions for this filter."* plus the hint naming the most likely filter to
clear (cost centre → entity → period), from `08` §17.
**Print:** A4 landscape, fit to width 1, print titles rows 1–6; printing is discouraged above 5,000 rows
and the export dialog says so (print the summary, send the workbook).

### 4.5 `Exception Register` (`XL-005`)

**Purpose:** the reviewable exception list with severity, ownership, aging and thresholds — the sheet a
controller actually works from (`06`, `FR-EXC-002`…`FR-EXC-018`).

**Inclusion:** always present in the pack (the empty-state row when nothing is open). In the standalone
register export (`FR-EXC-018`, `XL-010`) the workbook contains **two sheets**: `Register (filtered)` and
`All exceptions`, both using this column contract.

**Sort:** severity (High → Med → Low), then `Amount at risk` descending, then `Rule ID`, then
`Exception ID`. Closed items sit after open ones within the same severity; the deterministic tie-break is
`Exception ID`.

| # | Header | Type | Format | Width | Notes |
|---|---|---|---|---|---|
| A | `Exception ID` | int | `XLS-FMT-007` | 10 | |
| B | `Rule ID` | text | `XLS-FMT-011` | 10 | `EXC-nnn` |
| C | `Rule name` | text | `XLS-FMT-010` | 32 | Pattern language, never a verdict (`FR-EXC-019`) |
| D | `Rule version` | text | `XLS-FMT-011` | 10 | Version that raised it (`03` §5.2) |
| E | `Family` | text | `XLS-FMT-010` | 18 | The `06` §3 family |
| F | `Severity` | text | `XLS-FMT-010` | 9 | `High` / `Med` / `Low` — `CF-004`/`005`/`006` |
| G | `Mark` | text | `XLS-FMT-014` | 7 | `▲` / `◆` / `●` — the greyscale signal |
| H | `Subject` | text | `XLS-FMT-010` | 40 | `subject_display` (denormalised for reports) |
| I | `Subject key` | text | `XLS-FMT-011` | 30 | The rule-specific canonical key |
| J | `Entity` | text | `XLS-FMT-011` | 10 | |
| K | `Account code` | text | `XLS-FMT-011` | 12 | |
| L | `Account name` | text | `XLS-FMT-010` | 28 | |
| M | `Cost centre` | text | `XLS-FMT-011` | 12 | |
| N | `Vendor` | text | `XLS-FMT-010` | 22 | |
| O | `Period` | text | `XLS-FMT-011` | 11 | Current period of the occurrence |
| P | `First seen` | text | `XLS-FMT-011` | 11 | Original period — never overwritten |
| Q | `Amount at risk` | money | `XLS-FMT-001` | 16 | `CF-011` when zero |
| R | `Status` | text | `XLS-FMT-010` | 13 | `open` / `in_review` / `explained` / `corrected` / `closed` / `reopened` / `not_applicable` |
| S | `Owner` | text | `XLS-FMT-010` | 18 | Empty renders as `Unassigned` (a filter state, not a loss) |
| T | `Age (days)` | int | `XLS-FMT-013` | 10 | Period-based aging (`06` §2.5) |
| U | `Overdue` | text | `XLS-FMT-014` | 12 | `Overdue 12 d` / `—` — `CF-008` |
| V | `SLA due` | date | `XLS-FMT-008` | 12 | Severity SLA (7/21/45 days per `06`) |
| W | `Effective threshold` | text | `XLS-FMT-010` | 30 | The threshold actually used when raised (`03` §5.2) |
| X | `Flagged again` | text | `XLS-FMT-010` | 12 | `Yes <dd-mm-yyyy>` / `No` |
| Y | `Notes` | int | `XLS-FMT-007` | 8 | Note count |
| Z | `Last note` | date | `XLS-FMT-008` | 11 | |
| AA | `Evidence refs` | text | `XLS-FMT-010` | 30 | Voucher/row references behind the exception |
| AB | `Raised at` | timestamp | `XLS-FMT-009` | 15 | |
| AC | `Last seen at` | timestamp | `XLS-FMT-009` | 15 | |
| AD | `Closed at` | timestamp | `XLS-FMT-009` | 15 | Empty while open |
| AE | `Run ID` | int | `XLS-FMT-007` | 9 | Rule-run traceability |

Row 4 carries the canonical wording verbatim: *"Potential exception — requires accounting review. These
are leads, not verdicts."* (`FR-EXC-019`), plus the applied filter.

**Controls:**

| Control row | Contents |
|---|---|
| `Counts` | `Total: N · Open: n · Overdue: n · High: n · Unassigned: n` — written as text in the control row (a per-row count column would be meaningless); the same values also appear on `Cover` control rows 55–59 |
| `Σ Amount at risk` | `Q` = sum over shown rows, with the standing caveat in the same row's `Note` cell: *"Indicator only — amounts at risk across different subjects are not additive as a ledger total."* |
| `Rule coverage` | Text: `Rules evaluated: 24 of 24 enabled (rule set 2026-09-30) · Run 118 · Last run 01-10-2026 14:05`; when rules are disabled the line names them and why (`FR-EXC-014`) |

**Empty state:** *"No open exceptions — nothing requires review."* — written as the single italic data
row, with the last rule-run line so a stale run is visible.
**Print:** A4 landscape, fit to width 2, print titles rows 1–6 and columns A:C.

### 4.6 `Forecast Summary` (`XL-006`)

**Purpose:** the rolling-forecast view the deck's outlook slide references: method, scenario, version,
landing estimate, and accuracy for closed periods (`07`, `FR-FC-002`…`FR-FC-008`).

**Inclusion:** present when a forecast version is selected for the filter; **omitted** when none exists,
with the reason on `Cover` row 4: *"Forecast Summary omitted — no forecast version generated for
FY26-P09. Generate a forecast in the Forecast workspace."* In an **issued** pack the referenced version
must be `locked` (`07` §lifecycle); a draft-based pack can be generated but cannot be issued, and row 4
says so: *"Draft forecast v4 — not locked; this pack cannot be issued until the version is locked."*

**Sort:** account group (hierarchy order), then period ascending, then method label. Landing and accuracy
blocks follow the detail rows in fixed order.

| # | Header | Type | Format | Width | Notes |
|---|---|---|---|---|---|
| A | `Level` | int | `XLS-FMT-007` | 7 | As §4.2 |
| B | `Account code` | text | `XLS-FMT-011` | 12 | Blank for group-level rows |
| C | `Account group` | text | `XLS-FMT-010` | 34 | Indented per level; outline grouping as §4.2 |
| D | `Period` | text | `XLS-FMT-011` | 10 | |
| E | `Scenario` | text | `XLS-FMT-010` | 10 | `Base` / `Best` / `Worst` (`07` §scenarios) |
| F | `Method` | text | `XLS-FMT-010` | 20 | `locked_actuals`, `remaining_budget`, `run_rate`, `three_month_avg`, `manual` |
| G | `Method source` | text | `XLS-FMT-010` | 18 | `line pin` / `account group` / `project default` / `override` (resolver, `07` §) |
| H | `Actual` | money | `XLS-FMT-001` | 16 | Closed periods only; empty on forecast periods |
| I | `Budget` | money | `XLS-FMT-001` | 16 | |
| J | `Forecast` | money | `XLS-FMT-001` | 16 | Empty on closed periods (actuals win, never overwritten — `CALC-060`) |
| K | `Variance (F − B)` | money | `XLS-FMT-001` | 16 | `CF-001`/`CF-002` |
| L | `Var %` | percent | `XLS-FMT-004` | 10 | `CALC-011` guards |
| M | `Signal` | text | `XLS-FMT-014` | 13 | `Fav ▲` / `Adv ▼` / `—` |
| N | `Base method` | text | `XLS-FMT-010` | 16 | For adjusted rows: the method the scenario adjustment was applied to (`CALC-065`) |
| O | `Adjustment %` | percent | `XLS-FMT-004` | 12 | Scenario adjustment, `—` when none |
| P | `Override reason` | text | `XLS-FMT-010` | 40 | Present when method = `manual` (`CALC-064` requires it) |
| Q | `Version` | text | `XLS-FMT-011` | 14 | `Base v3 (locked 30-09-2026)` |
| R | `Updated at` | timestamp | `XLS-FMT-009` | 15 | |

**Landing-estimate block** (after the detail rows, section header `Landing estimate`):

| Row | Contents |
|---|---|
| `FY actual YTD` | Sum of actuals across loaded periods per account group, and a total row |
| `Forecast (remaining)` | Sum of forecast rows |
| `Landing estimate (FY)` | YTD + remaining, per group and total |
| `Landing vs annual budget` | Money and % (`CALC-011`) |
| `Status` | `Locked` / `Draft` with the version name |

**Accuracy block** (for closed periods where a locked forecast existed — `07` §accuracy, `CALC-066`…`069`):

| Column set | Contents |
|---|---|
| `Period`, `Account group` | Comparison grain |
| `Signed bias` | `CALC-068` (money, signed; positive = under-forecast) |
| `MAPE-lite` | `CALC-069` (percent, 1 dp) |
| `Periods compared` / `Excluded (zero actual)` | Counts, `XLS-FMT-007` — the exclusions are always shown, never silently dropped |
| `Method guidance` | The non-blocking suggestion text from `FR-FC-008`, only where a suggestion exists; empty otherwise. Never an instruction |

**Controls:** `Totals` row per block; `Check`: Σ landing estimate = FY actual YTD + Σ forecast remaining —
`OK`/`CHECK FAILED`; and when the filter covers one entity and one period, the forecast row for that
period must equal the Forecast Summary KPI the app shows (cross-artifact §11).
**Empty state:** *"No locked forecast version yet."* plus, where relevant, *"Not enough closed periods
yet for accuracy (3 required)."*
**Print:** A4 landscape, fit to width 2, print titles rows 1–6 and columns A:C.

### 4.7 `Import Reconciliation` (`XL-007`)

**Purpose:** prove where the numbers came from and that the load is complete and balanced
(`FR-IMP-*`, `CALC-070`…`072`, Addon 1 `P12`).

**Inclusion:** always present. With no imports, the empty-state row and the instructions text.

**Sort:** `Loaded at` ascending, then `Batch ID`.

| # | Header | Type | Format | Width | Notes |
|---|---|---|---|---|---|
| A | `Batch ID` | int | `XLS-FMT-007` | 10 | |
| B | `Status` | text | `XLS-FMT-010` | 12 | `committed` / `staged` / `voided` |
| C | `Source system` | text | `XLS-FMT-010` | 13 | |
| D | `File name` | text | `XLS-FMT-010` | 30 | As received |
| E | `Sheet` | text | `XLS-FMT-010` | 14 | Sheet/stream imported |
| F | `Checksum (short)` | text | `XLS-FMT-012` | 14 | First 12 hex characters of the file SHA-256 |
| G | `Checksum (full)` | text | `XLS-FMT-012` | 66 | Full hash; **not printed** (outside the print area) |
| H | `Rows read` | int | `XLS-FMT-007` | 10 | |
| I | `Rows committed` | int | `XLS-FMT-007` | 13 | |
| J | `Rows quarantined` | int | `XLS-FMT-007` | 14 | `CF-010` when > 0 |
| K | `Rows rejected` | int | `XLS-FMT-007` | 12 | |
| L | `Debit total` | money | `XLS-FMT-001` | 16 | `CALC-071` |
| M | `Credit total` | money | `XLS-FMT-001` | 16 | |
| N | `Balance variance` | money | `XLS-FMT-001` | 14 | `debit − credit`; should be `₹ 0.00` |
| O | `Control total (source)` | money | `XLS-FMT-001` | 16 | Manually supplied control total (`DEC-020`), empty when none |
| P | `Control variance` | money | `XLS-FMT-001` | 14 | `loaded − supplied` (`CALC-070`) |
| Q | `Balance result` | text | `XLS-FMT-010` | 15 | `Balanced` / `Accepted deviation (reason)` / `Variance` |
| R | `Profile version` | text | `XLS-FMT-011` | 14 | Mapping profile + version actually applied |
| S | `Loaded at` | timestamp | `XLS-FMT-009` | 15 | |
| T | `Loaded by` | text | `XLS-FMT-010` | 14 | Windows user account (`13`) |
| U | `Quarantine ref` | text | `XLS-FMT-011` | 14 | Where the quarantined rows can be reviewed |

**Validation summary block** (section header `Validation checks (latest run)`): columns
`Check ID` (`IMP-nnn`) · `Check` · `Weight` (10/5/2 per `04`) · `Result` (`Pass`/`Fail`/`Warn`) ·
`Rows affected` · `Message` (the plain-language catalog message). All 32 checks are listed every time,
pass or fail — a passing check is evidence, not noise.

**Data-quality score block:** the composite 0–100 (`CALC-050`) with its weighted components, printed
**alongside** the failed checks (Addon 3 §C.5: a single score must never mask a failure), plus the
threshold band text (`Good ≥ 90`, `Review 70–89`, `At risk < 70`).

**Tie-out block** (`FR-IMP-*`, `DEC-022`): rows `Control total (client)` · `Loaded total (engine)` ·
`Variance` · `Decision` (`Balanced` / `Accepted by <name> on <date> — reason: <text>`) · `Evidence`.
The acceptance reason is transcribed from the recorded acceptance, never invented.

**Controls:** totals row over `H`–`P`; `Check`: *"Σ Balance variance across committed batches = ₹0.00"* or
names each accepted deviation by batch; plus `CALC-072`: `Σ (committed + quarantined + rejected) = Σ rows
read` — `OK`/`CHECK FAILED`.
**Empty state:** *"No import batches yet."* plus *"Import your first file from the Import screen."*
**Print:** A4 landscape, fit to width 1, print area excludes column G.

### 4.8 `Audit Trail` (`XL-008`)

**Purpose:** the append-only, human-readable history that makes the pack reproducible and answerable
("who changed this, when, and from what") — the workbook's contribution to `FR-XC-007` and the audit
requirements in Addon 1 `P16`.

**Scope:** events with `occurred_at` between the earliest in-scope batch timestamp and generation time,
restricted to (a) the pack's entities/periods, (b) anything that changes the numbers (thresholds, master
data, mappings, rules, imports, voids), and (c) pack issuance and commentary approval for the same period.

**Sort:** `occurred_at` ascending, then `seq`. Chronological order is the point of an audit trail.

| # | Header | Type | Format | Width | Notes |
|---|---|---|---|---|---|
| A | `Seq` | int | `XLS-FMT-007` | 8 | Stable sequence from the audit store |
| B | `Occurred at` | timestamp | `XLS-FMT-009` | 16 | |
| C | `Actor` | text | `XLS-FMT-010` | 16 | Windows user or `system` |
| D | `Entity type` | text | `XLS-FMT-010` | 18 | `import_batch` / `exception` / `threshold` / `mapping_profile` / `master_data` / `rule_run` / `pack_issue` / `commentary` / `settings` / `backup` |
| E | `Entity ref` | text | `XLS-FMT-011` | 24 | Batch ID, `EXC-018`, profile name, … |
| F | `Event` | text | `XLS-FMT-010` | 24 | `committed`, `voided`, `status_changed`, `threshold_changed`, `version_reverted`, `issued`, `approved`, … |
| G | `Field` | text | `XLS-FMT-010` | 16 | For change events |
| H | `From` | text | `XLS-FMT-010` | 30 | |
| I | `To` | text | `XLS-FMT-010` | 30 | |
| J | `Reason / note` | text | `XLS-FMT-010` | 44 | Verbatim note text where the event carries one; wrap on, height 30 |
| K | `Source` | text | `XLS-FMT-010` | 10 | `ui` / `cli` / `system` |

**Content rules (non-negotiable):**

1. **No AI payloads, no prompts, no secrets.** AI provenance events appear as
   `commentary → approved (PROMPT-01 v1, model <name>)` — never the generated text, never a key
   (`10` §14, `13`).
2. No amounts or vendor names are added by the audit *sheet* beyond what the event itself recorded;
   the sheet mirrors the audit store, it does not enrich it.
3. Events are never edited, hidden or re-ordered. A correction is a new event.
4. The sheet is capped at **200,000 rows**: if the scope exceeds it, the most recent 200,000 are written
   and row 4 states *"Showing the most recent 200,000 of <N> events (from dd-mm-yyyy) — export the full
   audit trail from Settings → Data & storage."* Silent truncation is a defect.
5. Keys, tokens and passwords never appear even if a malformed event tried to record one — the writer
   redacts anything matching the secret patterns in `13` §5.4.

**Controls:** `Events in scope: N · Shown: M · Range: <first> → <last>`. No money totals (an audit sheet
that totalled money would imply a control it does not provide).
**Empty state:** *"No audit events in this period yet."*
**Print:** A4 landscape, fit to width 1, print titles rows 1–6 and column A:B.

## 5. Row caps, splitting and the 16,384-column limit

### 5.1 The cap

| Quantity | Value |
|---|---|
| Excel worksheet limit | 1,048,576 rows × 16,384 columns |
| Reserved by this contract | 6 header rows + 1 spacer after data + up to 4 control rows + 1 buffer = 12 |
| **`XLS_SAFE_MAX_DATA_ROWS`** | **1,048,500** (a frozen constant; the ~64-row margin absorbs future control rows without a layout change) |
| Widest sheet in the pack | `Transaction Detail`, 29 columns (`AC`) — well inside 16,384 |
| Longest cell text | 500 characters (description) — well inside 32,767 |

### 5.2 Splitting algorithm (lossless by default)

1. Count the rows the current filter would write (`N`) **before** writing anything.
2. `N ≤ XLS_SAFE_MAX_DATA_ROWS` → one sheet, base name (e.g. `Transaction Detail`).
3. `N > cap` → `K = ceil(N / cap)` sheets, named `<Base>` then `<Base> 2ofK`, `<Base> 3ofK`, … (the base
   name is short enough to keep every sheet name ≤ 31 characters; if a future base name is longer, the
   suffix truncates the base and the full name is stated in row 1).
4. Every split sheet repeats the complete header block, the table header row, the freeze panes and the
   autofilter, and states its slice in row 4: *"Rows 250,001–500,000 of 1,240,000 · sheet 2 of 5"*.
5. The **written order is identical to the unsplit order** — splitting never re-sorts, so reading sheet
   2 immediately after sheet 1 continues the same sequence, and the `#` column continues incrementing.
6. Per-sheet `Subtotal (this sheet)` controls plus one `Total (all split sheets)` control on every split
   sheet (§4.4) — a page subtotal can never be mistaken for the grand total.
7. The `Cover` contents row states the sheet count: `Transaction Detail · 1,240,000 · Yes — 5 sheets`.
8. Generation time and file size are estimated before writing; the job dialog shows the estimate and the
   cancel button (Kickoff §12.9).

### 5.3 The alternative: an explicit row limit (never silent)

The export dialog offers **"Rows to export"**: `All (split if needed)` — default — or `First N rows`
(user-typed, with the sort order stated so "first" is meaningful). A limited export:
- writes the standard control rows over the rows shown,
- states in row 4: *"Filtered to the first 250,000 of 1,240,000 rows by <sort key>. Remaining rows were
  not exported."*,
- records the limit in the audit trail (`export_row_limited`) and in the CSV sidecar or `FactExport`.

A truncated sheet **without** that statement fails `TST-XL-16` — the single most important rule in this
section.

### 5.4 CSV is never split

CSV exports write all rows in one file (no worksheet limit). The export dialog warns above 500,000 rows
about open time and file size and offers xlsx-with-split as the alternative. CSV never truncates.

## 6. Evidence bundle (`XL-009`)

### 6.1 Trigger, naming, format

| Aspect | Rule |
|---|---|
| Trigger | `SCR-024` Exception detail → **Export evidence bundle** (`SCR-025` modal: options, size estimate, destination) |
| Scope | Exactly one exception (`FR-EXC-016`: "one click per exception") |
| Name | `<Project>_<Entity>_<Period>_Evidence-<EXC-nnn>_<vN>.<ext>` |
| Format | `.xlsx` by default. `.zip` when the user ticks *"Include the source file excerpt"* **and** the archived original exists, or when the subject rows exceed 200,000 (then the workbook is split inside the zip) |
| Destination | The `Evidence\` subfolder (§3.4) |
| Size | Warn above 25 MB; the modal shows the estimated size before writing |

### 6.2 Sheets

| Sheet | Contents |
|---|---|
| `Cover` | Bundle stamp: project · exception ID · rule ID + version · rule name · family · severity · subject (key + display) · period · first seen · status · owner · amount at risk · effective threshold · rule tier (`exact`/`fuzzy`) · source batch IDs · source file names · mapping profile versions · generation timestamp · app/schema version · pack link (`Pack v3`) · disclaimer short form (verbatim) · "What to check" list (below) |
| `Subject Rows` | The transactions behind the exception, using the `Transaction Detail` column contract (§4.4). Totals row `Σ Debit` / `Σ Credit` / `Σ Net` and a reconciliation line: `Σ \|amounts\| = amount at risk (₹x) — OK` or the stated difference with its explanation (e.g. *"amount at risk includes 2 rows outside the current filter: see row 14"*) |
| `Rule & Threshold` | The rule as specified in `06`: ID, name, family, version, severity, owner role, SLA days, dependency list, tier, intent, logic (plain-language restatement, verbatim from `06`), thresholds with the **effective** values for this project, the global materiality defaults (`CALC-080`), and the sample-case note where one exists. This sheet exists so an accounting team can judge the rule without access to the app |
| `Validation Extract` | The `IMP-nnn` checks that touched the subject rows' batches: check ID · name · weight · result · rows affected · message; plus the batch control totals and balance results for those batches, and the data-quality score with its components |
| `Mapping Version` | Profile name · version · effective-from · the applied column mapping rows (source column → target field → transformation note) · a "changed mid-year" flag with the before/after diff when the profile version changed inside the data range |
| `Audit Trail` | The exception's own event history (`raised`, `flagged_again`, `status_changed`, `owner_changed`, `note_added`, `threshold_changed`, `reopened`, `evidence_exported`) plus the import commit/void events of the batches behind the subject rows. Same column contract as §4.8 |

**"What to check" list (written verbatim on the bundle `Cover`):**

```
1. The rule that raised this item, and its threshold — see "Rule & Threshold".
2. The rows it was raised on — see "Subject Rows"; check the voucher/document/invoice numbers in your ledger.
3. Whether the source file loaded completely and balanced — see "Validation Extract".
4. Whether the right mapping version was applied — see "Mapping Version".
5. Who has touched this item and what they decided — see "Audit Trail".
This bundle is an analysis aid. It is not an audit opinion and it does not conclude that the item is an error.
```

### 6.3 Zip layout

```
AcmeManufacturing_IN01_FY26-P09_Evidence-EXC-018_v1.zip
├── AcmeManufacturing_IN01_FY26-P09_Evidence-EXC-018_v1.xlsx     ← the bundle workbook
├── manifest.json                                                ← below
├── README.txt                                                   ← the "what to check" list + disclaimer, plain text
└── source/
    └── D365_GL_Sep26.xlsx                                       ← the archived original, byte-identical, never edited
```

```json
{
  "schema": "fpa.evidence.v1",
  "exception_id": 1043,
  "rule_id": "EXC-018",
  "rule_version": "1.0",
  "subject_key": "5200|CC-100|FY26-P09",
  "period": "FY26-P09",
  "generated_at": "2026-10-01T14:22:31+05:30",
  "files": [
    { "path": "AcmeManufacturing_IN01_FY26-P09_Evidence-EXC-018_v1.xlsx", "sha256": "9f2c...", "bytes": 482113 },
    { "path": "source/D365_GL_Sep26.xlsx", "sha256": "1b77...", "bytes": 8320441, "originated_from_batch": 1041 }
  ],
  "subject_row_count": 12,
  "amount_at_risk": "540000.00",
  "disclaimer": "Potential exceptions only — advisory tool, not professional advice. Review by a qualified accountant required. Figures may be revised."
}
```

Rules: the source excerpt is the **archived original file** (never a re-export, never edited); its SHA-256
in the manifest must equal the archived checksum (a mismatch aborts the bundle with `ERR-EXP-004`); no AI
text, no generated commentary and no secrets are ever included in a bundle; the bundle is stamped as an
unissued artefact (it is correspondence, not a pack).

## 7. Ad-hoc table export (`XL-010`) — "export what you see"

### 7.1 xlsx form

One sheet, named after the view (`Drill`, `Matrix`, `Bridge`, `TopN`, `Trends`, `KPIs`, `ThreeWay`,
`Search`, `Effectiveness`, `ForecastCompare`, `Accuracy`, `Recon`, `Register`). Everything in §3 applies:
header block, header row 6 with autofilter, freeze panes at `C7`, the same column formats and widths as
the pack sheet the view mirrors, the same `CF-` rules, values-only, row 4 stating the applied filter and
the row accounting, and a `Totals` row carrying the view's own totals (only where the view has a
meaningful total). Row cap and splitting exactly as §5.

**Standalone register export** (`FR-EXC-018`) is the one two-sheet exception:
`Register (filtered)` + `All exceptions`, both using the §4.5 column contract; `All exceptions` has no
filter applied and states `Filter: none (all periods loaded)` in row 4. Counts on both sheets must equal
the register counts for the same filter (`TST-XL-19`).

### 7.2 CSV form

| Aspect | Rule |
|---|---|
| Encoding | UTF-8 **with BOM** (`utf-8-sig`) — so double-clicking in Excel renders `₹`-adjacent text, accented names and `—`/`▲` correctly |
| Delimiter | Comma. Never semicolon (a locale-dependent delimiter breaks re-import elsewhere) |
| Line endings | CRLF |
| Quoting | Quote a field when it contains the delimiter, a double quote, CR/LF, or leading/trailing whitespace. Escape an embedded quote by doubling it. Everything else is unquoted |
| Header row | Exactly the visible column labels, in visible order — identical strings to the screen and the xlsx export |
| Numbers | Raw, unformatted: no currency symbol, no thousands separators, `.` decimal, `-` for negative, 2 dp for money, full stored precision for percentages (fractions, e.g. `0.0795`) |
| Dates | `dd-mm-yyyy` text (the project display format) — CSV is a report export; a re-import still asks the user to confirm the date format per `04` |
| Empty vs zero vs not-available | The same three tokens as everywhere else: `—` (nothing to compare), `n/a` (undefined), `0.00` (real zero). Semantics never change between artefacts |
| Long text | Full text, quoted as needed; embedded newlines are preserved inside quotes |
| Row cap | None (§5.4). Warning above 500,000 rows |
| Stamp | **No comment or banner lines inside the CSV** — a leading `#` block would break naive parsers and would mean our own exports could not be re-imported cleanly. The stamp travels in the sidecar (§7.3) and in the export dialog's "Copy stamp" button |
| Encoding declaration | The sidecar names it; the BOM makes Excel agree |

**Why no in-file stamp (decision record):** the alternative — 4 leading `#` comment lines — was rejected
because (a) the spec requires "every table view exports exactly the current filter/sort/columns", and
comment lines violate "exactly"; (b) our own importer (`04`) would have to special-case our own output;
(c) every consumer that reads the file programmatically would need to know about the header block. The
sidecar gives the same information without corrupting the data contract.

### 7.3 Sidecar stamp (`<basename>.csv.meta.json`)

```json
{
  "schema": "fpa.export.v1",
  "file": "AcmeManufacturing_IN01_FY26-P09_Drill_v4.csv",
  "view": "Drill",
  "generated_at": "2026-10-01T14:22:31+05:30",
  "project": "Acme Manufacturing",
  "entities": ["IN01", "IN02"],
  "periods": ["FY26-P09"],
  "window": "MTD",
  "scenario": "Base",
  "filter_json": { "entity": ["IN01", "IN02"], "period": ["FY26-P09"], "cost_center": [], "account": [], "severity": [], "status": ["open"] },
  "filter_human": "Entity=IN01, IN02 · Period=FY26-P09 · CC=All · Account=All · Severity=All · Status=Open",
  "sort": ["account_code asc", "cost_center asc", "voucher_no asc", "line_no asc"],
  "row_count": 1240,
  "row_limit_applied": null,
  "batch_ids": [1041, 1042, 1043],
  "units": "₹ whole units",
  "grouping": "Indian (lakh/crore)",
  "app_version": "0.9.0",
  "schema_version": "1",
  "content_hash": "sha256:9f2c...",
  "disclaimer_short": "Potential exceptions only — advisory tool, not professional advice. Review by a qualified accountant required. Figures may be revised."
}
```

The sidecar is written **after** the CSV is closed successfully; a failure to write it does not delete the
CSV, but reports `ERR-EXP-008` so the user knows the stamp is missing. The export dialog shows the same
JSON in a "Stamp" panel with a **Copy** button, so a stamped summary can be pasted into an email body
without sending a second file.

## 8. Owner-wise exception distribution (`XL-011`)

**Purpose:** hand each accounting owner their list without handing them the whole register
(`FR-EXC-017`), and give the FP&A analyst something that pastes into Teams or an email.

**Workbook** (three sheets):

| Sheet | Contents |
|---|---|
| `By owner` | One row per owner (`Unassigned` included, never dropped): `Owner` · `Open` · `In review` · `Overdue` · `High` · `Med` · `Low` · `Σ Amount at risk` · `Oldest age (days)` · `Most material item` (subject + amount) · `SLA risk` (`Overdue 2 of 4` style text). Sorted by overdue desc, then Σ amount at risk desc, then owner name. Totals row at the bottom |
| `Items` | All in-scope exceptions using the §4.5 column contract, sorted by owner (same order as `By owner`), then severity, then amount desc. Row 4 states the filter and the owner count |
| `Copy for email` | The plain-text summary in column A, one line per row, so it can be selected and copied from the workbook as a fallback if the clipboard path is unavailable |

**Plain-text summary (the exact template — also what the `Copy owner summary` button writes):**

```
FP&A Month-End Copilot — exception summary for review
Project: Acme Manufacturing · Period: FY26-P09 · Generated 01-10-2026 14:22
Potential exceptions only — requires accounting review. These are leads, not verdicts.

OWNER: Rahul Mehta — 4 open, 1 overdue, 1 high
  1. [High] Possible duplicate invoice · V-00931 / INV-88213 · ₹45,000.00 · open 4d · OVERDUE 2d
  2. [Med] Spike vs trailing average · 5600 / CC-140 · ₹1,86,000.00 · open 4d
  3. [Med] Missing recurring cost · Vendor V-2210 / 5300 · ₹72,000.00 · open 6d
  4. [Low] Round-number manual journal · VCH-2026-0929-014 · ₹15,00,000.00 · open 4d
  Amount at risk (indicator): ₹18,03,000.00

OWNER: Unassigned — 2 open, 1 overdue, 1 high
  1. [High] Potential cut-off issue · V-00412 / doc 29-Sep · ₹3,20,000.00 · open 6d · OVERDUE 1d
  2. [Med] Material variance (>threshold) · 5600 / CC-140 · ₹5,40,000.00 · open 4d
  Amount at risk (indicator): ₹8,60,000.00

TOTALS — 6 open, 2 overdue, 2 high of 2 owners shown (plus 1 unassigned group).
Closed in this period: 3 · Not applicable: 1
Full register: AcmeManufacturing_AllEntities_FY26-P09_Register_v2.xlsx
```

**Formatting rules for the text:** plain ASCII-safe where possible but the `₹`/`·` characters are kept
(UTF-8, no BOM for the `.txt`); lines ≤ 100 characters; no tab characters; no colour or markdown; at most
10 items per owner, then `  … 4 more (see the exported register)`; numbering restarts per owner; ordering
is severity, then amount descending, then exception ID; the disclaimer line is always the third line; the
totals section is always present, including zero values (`0 closed`). Counts in the text must equal the
workbook counts exactly (`TST-XL-20`).

**Sizes:** the `.txt` is offered via clipboard first (the common case), with "Save as .txt" second.

## 9. House-style matching (client-supplied report)

The Source-of-Truth Matrix (`00_INDEX` §5) requires the pack to match the client's current report when
they supply one. Matching is **appearance only** — semantics are never negotiable.

### 9.1 What can be matched

| Element | Matchable | Notes |
|---|---|---|
| Brand colours (2) | Yes | Used for the header row fill, title text and tab colours; contrast-checked (`01` §17) with a documented accessible substitute when a supplied colour fails AA |
| Font family and size scale | Yes | One family plus a body/heading size pair; falls back to Calibri 11 where a font is not installed, and the fallback is recorded in the stamp |
| Header text (row 1) | Yes | e.g. *"Acme Manufacturing — Monthly Actuals vs Budget"* replaces the default title |
| Column headers | Yes | Per-column display labels only; **column order can be matched only where the profile maps a house column to an existing contract column** — no contract column can be dropped (the numbers must remain traceable) |
| Column order | Partially | The identifier block (A–E area: level/code/name/type) stays first; the remainder may be reordered per the profile, and the pack records the profile version in the stamp. Reordering is validated against the contract's required columns |
| Number formats | Partially | Only the grouping convention (Indian/international) and decimal places are matchable. The currency symbol, parenthesis negatives, and `—`/`n/a` semantics are fixed by `08` §15 |
| Footer text | Yes | Client wording, with our short disclaimer appended — the disclaimer is never removable |
| Print settings | Yes | Orientation/papersize/margins from the house profile; the required print titles and footer disclaimer stay |
| Logo | Cover only | One image, top-right of `Cover`, width ≤ 240 px equivalent, aspect preserved, inserting never pushes the stamp table (anchor sized to the reserved block) |
| Tab colours | Yes | May be overridden; the default set is a fallback |

### 9.2 What cannot be matched (and why)

| Not matchable | Reason |
|---|---|
| VBA, macros, `.xlsm` | Security and supportability: the app produces `.xlsx` only (`FR-XC-009`, `13`) |
| Pivot tables and pivot caches | Not portable, not testable, and they hide the data contract behind a cache; the same numbers are already delivered as values |
| External links / Power Query | The pack must open offline with no repair prompt; external links are a silent failure mode |
| Merged-cell report layouts | They break sorting, filtering, re-import and the row contract (§3.5) |
| Their conditional-formatting formulas | We map to the `CF-` rule set (one rule set, `08` §14). A colour with no non-colour signal would fail our own accessibility gate |
| Sheet protection / passwords | The client must be able to filter and copy their own data |
| Their charts and shapes | The pack has no charts in v1 (§14 `XL-CHART-DEFER`); charts live in the deck and the app |
| Their formulas | Values-only (§3.2) |

### 9.3 Mechanism and lifecycle

1. **Import:** Settings → Branding → *"Match our current report"* → pick an `.xlsx`. The app reads fonts,
   fills, header text, column labels, number formats, tab colours, print settings. It never copies their
   data, formulas or macros — only style metadata.
2. **Preview and diff:** the import shows what will be taken (table of `element → current → imported`) and
   what is refused (the §9.2 list, with reasons). Nothing is applied without confirmation.
3. **Profile:** saved as a versioned `HouseStyleProfile` (`v1`, `v2`, …), revertable, exportable/importable
   as JSON, and recorded in `Pack_Stamp_HouseStyle`.
4. **Validation:** contrast check on brand colours; missing-font detection; a column-order profile that
   drops a required column is rejected with the reason.
5. **Precedence when rules conflict:** semantics (formats dictionary §3.6, `CF-` §3.7, stamp §3.2,
   disclaimer) **always win**; house style wins over the built-in appearance defaults; anything unspecified
   falls back to the defaults.

```json
{
  "schema": "fpa.housestyle.v1",
  "profile_name": "Acme-House-2026",
  "version": 2,
  "source_file": "Acme_Current_Management_Report.xlsx",
  "imported_at": "2026-10-01T11:04:00+05:30",
  "brand": { "primary": "1F3A5F", "secondary": "B7791F", "contrast_checked": true },
  "fonts": { "family": "Calibri", "body_size": 11, "heading_size": 13, "fallback_used": null },
  "titles": { "pack_title_template": "{project} — {period} — Actuals vs Budget" },
  "column_labels": { "account_name": "Ledger account", "variance": "Variance (Act-Bud)" },
  "column_order": ["level", "account_code", "account_name", "account_type", "actual", "budget", "variance", "variance_pct", "signal"],
  "tab_colours": { "BvA Summary": "2E7D32", "Exception Register": "B7791F" },
  "footer_text": "Acme Manufacturing — internal management reporting",
  "print": { "paper": "A4", "orientation": "landscape", "margins_cm": 1.0 },
  "logo": { "path": "brand/acme-logo.png", "placement": "cover_top_right", "max_width_px": 240 },
  "refused": ["vba", "external_links", "merged_headers", "sheet_protection", "pivot_tables"]
}
```

**Assumption to validate:** that the client's current report is a plain `.xlsx` without protection. If it
is protected or `.xlsm`, the importer explains what it cannot read and offers the manual fallback (enter
brand colours, font and title by hand) — the pack remains deliverable either way (`OQ-021`).

## 10. Print and PDF setup

### 10.1 Global page setup

| Aspect | Rule |
|---|---|
| Paper / orientation | A4 landscape by default; `Cover` A4 portrait; house profile may override (§9) |
| Margins | 1.0 cm all sides; header 0.5 cm, footer 0.5 cm |
| Scaling | `fitToWidth` per sheet (table below), `fitToHeight = 0` (as many pages tall as needed). **No scale-to-one-page for tall sheets** — it makes text unreadable |
| Print titles | Rows 1–6 repeated on every page (header block + table header), plus the identifier columns where the table is wide (`A:B` or `A:C`) |
| Footer (left) | The **short-form disclaimer verbatim** (`01` §15.1) |
| Footer (right) | `&A · Page &P of &N` (sheet name and page numbers) |
| Footer (centre) | Empty |
| Header | Empty — the generated timestamp lives in the header block (rows 1–4), because `&D` in a footer would print the *printing* date, which is a different, misleading fact |
| Ampersands | Any literal `&` in footer/header text is escaped as `&&`; the short form contains none, so the current footers are escape-free — and a test asserts it (§13 `TST-XL-26`) |
| Footer length | Excel limits a header/footer section to 255 characters; the short form is 134 characters, leaving room for `&A · &P of &N`. A test asserts every footer section ≤ 255 |
| Gridlines in print | Off (the table has borders); screen gridlines remain on (§3.5) |
| Black and white | Print colour is left on (`blackAndWhite = False`); the greyscale gate is met by the `CF-` non-colour signals, not by suppressing colour (§3.7) |
| Page breaks | Horizontal break before each control row block; vertical breaks at the print-area boundary. No manual breaks inside data |

### 10.2 Per-sheet print contract

| Sheet | Orientation | fitToWidth | Print area | Titles |
|---|---|---|---|---|
| `Cover` | Portrait | 1 | `A1:E73` | Rows 1–4 |
| `BvA Summary` | Landscape | 2 | `A1:N<last>` | Rows 1–6, cols A:B |
| `BvA Bridge` | Landscape | 1 | `A1:J<last>` | Rows 1–6, cols A:B |
| `Transaction Detail` | Landscape | 1 | `A1:AC<last>` | Rows 1–6, cols A:C |
| `Exception Register` | Landscape | 2 | `A1:AE<last>` | Rows 1–6, cols A:C |
| `Forecast Summary` | Landscape | 2 | `A1:R<last>` | Rows 1–6, cols A:C |
| `Import Reconciliation` | Landscape | 1 | `A1:F<last>` + `H1:U<last>` (excludes the full-checksum column G) | Rows 1–6, cols A:B |
| `Audit Trail` | Landscape | 1 | `A1:K<last>` | Rows 1–6, cols A:B |
| Split sheets | As their base sheet | As base | As base | As base |
| Ad-hoc export | Landscape | 1 | As the source view's contract | Rows 1–6, identifier cols |

### 10.3 PDF — the honest scope statement

`FR-XL-009` says *"'Export to PDF' uses those settings"*. The app does **not** render PDF itself:

| Option | Why not |
|---|---|
| Bundle a headless renderer (LibreOffice) | Adds hundreds of megabytes to a ≤ 500 MB installer (`NFR-006`) and a second engine to support |
| Automate the user's Excel via COM | Requires Excel installed, is brittle across versions, and would need `pywin32` — an additional runtime dependency the architecture avoids (`ADR-001`, `ADR-010` precedent) |
| Hand-rolled xlsx→PDF renderer | Would silently produce a *different* rendering from Excel — exactly the drift the cross-artifact rule exists to prevent |

**Resolution (`DEC-028`, to be recorded in `01` §21):** v1 delivers *print/PDF readiness*, not PDF
rendering: (a) every sheet carries a complete, tested page setup (§10.1/§10.2); (b) the app's action is
**"Open for printing / Save as PDF"**, opening the workbook in the OS default handler with a three-step
inline guide (Print → Microsoft Print to PDF → Save); (c) the greyscale/PDF acceptance test runs in the
real-Windows validation using Excel's print-to-PDF, which is the same renderer the client uses. The
acceptance criterion ("a printed/PDF pack is legible in black and white with no truncated columns") is
satisfied and tested; only the *origin* of the PDF changes. The user guide (`22`) documents the flow.

## 11. Cross-artifact consistency contract

`FR-XL-008` / Addon 3 §F.4 require exact equality between the engine, the screen, the workbook and the
deck for a fixed filter state. This section defines how the equality is *mechanically* checkable.

| Element | Rule |
|---|---|
| Canonical filter state | `Pack_Stamp_FilterJSON` (sorted-key JSON) generated once by the app and reused for the UI render, the Excel pack and the PPT deck. Any artefact rendered from a different filter state is not comparable and the test refuses to compare it |
| Engine authority | The engine's computed values are the authority. A mismatch is fixed in the renderer, **never** by hand-editing a workbook or by relaxing the engine |
| Value precision for comparison | Money: exact equality as `Decimal` at 2 dp. Percentages/pp/ratios: equality of the **formatted display string** (`8.0%`, `+1.5 pp`) because rounding is display-only (`CALC-030`/`031`). Counts: exact integers. Text: exact string equality. Tokens (`—`, `n/a`): exact string equality, position by position |
| Reading the workbook | `openpyxl.load_workbook(..., data_only=True)`; values read from the labelled control rows (§4) and the named stamp cells (§3.2). Tests locate rows by label, not by hard-coded addresses, except the stamp defined names |
| Comparison set (minimum) | Total actual · total budget · total variance · total variance % · headline rate variance · landing estimate · exception counts (open/overdue/high) · Σ amount at risk indicator · import balance variance · data-quality score · units label · grouping style · signal values · `—`/`n/a` pattern · applied filter string |
| Tolerance | **Zero.** One minor unit of difference is a failure (`TST-XL-23`) |
| What is compared across which pair | Excel ↔ engine (values), Excel ↔ PPT (values + labels + units), Excel ↔ UI (the values the API returns for the same filter), PPT ↔ UI (labels). The test enumerates the pairs so a skipped pair fails |
| Failure handling | S1 defect (wrong numbers), logged in `28`'s defect list; release blocked. Rationale: a pack that disagrees with the deck it was issued with destroys trust faster than a missing feature |
| Deck specifics | `12` § owns which PPT placeholder carries which value; every placeholder value must be one of the comparison-set cells above |

## 12. Failure modes, limits and error handling

Every failure uses the `SCR-041` error anatomy (what happened · what was not lost · one next action ·
Copy details) and a catalog entry (`26`), never a traceback (`FR-XC-006`).

| ID | Trigger | Message (headline) | What was not lost | Next action | Technical note |
|---|---|---|---|---|---|
| `ERR-EXP-001` | Target folder not writable | *"The export folder can't be written to — <path>."* | *"Nothing else was affected. No file was created."* | Choose another folder | `PermissionError`; logged with the path only (no data) |
| `ERR-EXP-002` | Target file open in another program | *"<file name> is open in Excel, so it can't be replaced."* | *"Your existing file is untouched."* | Close it, or keep both (next version) | Retry once after 2 s, then prompt |
| `ERR-EXP-003` | Disk full / quota | *"There isn't enough space on <drive> to write this pack (needs about <size>)."* | *"No partial file was left behind."* | Free space, or export a summary-only pack | Temp file removed in `finally`; `.tmp` purged by `doctor` |
| `ERR-EXP-004` | Internal control check failed (rollup, tie-out, checksum of an archived source) | *"The pack was not written: an internal check did not pass (<check name>)."* | *"Your data and every previous pack are unchanged."* | Copy details and report it — this is a defect, not user error | Generation aborts **before** any file write; the failure is logged with the check name and the two values that disagreed |
| `ERR-EXP-005` | Row cap cannot be satisfied (more split sheets than the 31-character sheet-name budget allows, i.e. > 9,999 sheets) | *"This filter needs more than 9,999 sheets."* | *"Nothing was written."* | Narrow the filter, or export CSV | Defensive; unreachable in practice |
| `ERR-EXP-006` | User cancels generation | *"Export cancelled."* (informational, not an error colour) | *"No file was written."* | Try again when ready | Worker thread stops at a row boundary; temp file removed |
| `ERR-EXP-007` | Source data changed during generation (batch committed or voided mid-run) | *"The data changed while the pack was being generated, so it was restarted."* | *"Nothing was written from the inconsistent run."* | Continue (the restart is automatic, once) | Detected by comparing the snapshot token/batch set before and after; a second change fails with `ERR-EXP-004` |
| `ERR-EXP-008` | CSV written but its sidecar stamp failed | *"The export finished, but its stamp file couldn't be saved."* | *"Your CSV is complete and correct."* | Re-save the stamp from the export dialog | The dialog keeps the JSON available for clipboard copy |
| `ERR-EXP-009` | Export folder is inside a cloud-synced path | *"This folder syncs to the cloud."* (warning) | *"Nothing has been uploaded by this app."* | Choose another folder, or continue knowingly | Continuation is audited as `export_to_synced_path` (`ADR-004`) |
| `ERR-EXP-010` | Estimated workbook size > 300 MB | *"This pack is estimated at <size>, above the 300 MB limit."* | *"Nothing was written."* | Export summary-only, or narrow the filter | Estimate from row counts × the measured bytes/row for the sheet |
| `ERR-EXP-011` | Stale derived results in scope | Warning banner in the app and in the pack (`CF-009`) | — | *"Re-run rules / recalculation before issuing this pack."* | Generation is allowed; **issuance is blocked** (`FR-XC-003`) until the stale state clears |

**PowerPoint-generation failures continue the same family.** `ERR-EXP-012`…`ERR-EXP-018` are specified
in `12` §10 (base-deck placeholder mismatch, unmeetable text budget, damaged template, chart-type
fallback, logo, embedded chart data, size guard); the shared conditions above (`ERR-EXP-002`, `003`,
`006`, `007`, `009`) apply to deck generation unchanged.

**Hard-open guarantee:** the limitations in §3.5 (no macros, no external links, no pivot caches, no merged
data cells, ≤ 40 styles, values only, ASCII-safe sheet names) exist so that a generated workbook opens in
Excel, LibreOffice and Google Sheets with **no repair prompt** and no "protected view" surprise. The
real-Windows validation (`14`) opens every generated artefact in a clean VM before release
(`TST-XL-01`).

## 13. Test contract (`TST-XL-01`…`TST-XL-26`)

| ID | Asserts | Fixture | Type |
|---|---|---|---|
| `TST-XL-01` | Every artefact opens with no repair prompt in Excel (real Windows) and round-trips through `openpyxl` | Golden pack, evidence bundle, ad-hoc exports | Manual (VM) + structural |
| `TST-XL-02` | Sheet names, order, visibility (all visible) and tab colours match §3.5/§4 exactly | Golden pack | Structural |
| `TST-XL-03` | Zero formula cells anywhere in any generated artefact | Golden pack | Structural |
| `TST-XL-04` | All 30 stamp fields present, non-blank, correct types; every defined name resolves | Golden pack | Structural |
| `TST-XL-05` | Each sheet's header block rows 1–3 agree with the stamp (project, periods, version, batch IDs, units) | Golden pack | Structural |
| `TST-XL-06` | No merged range intersects a data table; merges only in row 1 / `Cover` blocks | Golden pack | Structural |
| `TST-XL-07` | 14-case number-format boundary matrix renders exactly the specified strings (₹0.00, ₹1.00, ₹999.99, ₹1,000.00, ₹99,999.99, ₹1,00,000.00, ₹99,99,999.99, ₹1,00,00,000.00, ₹99,99,99,999.99, negatives in each band, blank, `—`, `n/a`) | Format fixture | Structural + manual confirm in Excel |
| `TST-XL-08` | Indian vs international grouping switch changes every money cell consistently, including through the scaling modes | Two projects | Structural |
| `TST-XL-09` | Every scaled sheet prints the unit label in row 1; no scaled number appears unlabelled | Scaled fixture | Structural |
| `TST-XL-10` | The Excel export theme equals the colours derived from `ui/theme/tokens.ts` | Theme fixture | Structural |
| `TST-XL-11` | All `CF-` rules present, in the fixed order, on the right ranges; every fired rule has its non-colour signal text; greyscale render still distinguishes states | Golden pack + greyscale PDF | Structural + manual |
| `TST-XL-12` | Stale banner insertion shifts every address/freeze/print-title consistently | Stale fixture | Structural |
| `TST-XL-13` | Freeze panes and autofilter ranges match §4 per sheet | Golden pack | Structural |
| `TST-XL-14` | Column headers, order, format IDs, widths and alignment match §4 per sheet | Golden pack | Structural |
| `TST-XL-15` | Hierarchy rollup invariant: every parent equals the sum of its children, at every level, on `BvA Summary` and `Forecast Summary` | Golden pack | Structural (`CALC-042`) |
| `TST-XL-16` | Row-cap behaviour: no-split under the cap; split naming, slicing statement, continued row numbers, per-sheet subtotal + grand total, **and the explicit "first N of M" statement whenever a limit was applied** | 1.24 M-row fixture | Structural |
| `TST-XL-17` | Filename convention, sanitisation (reserved characters, device names, 240-char path cap, non-ASCII) | Name fixtures | Unit |
| `TST-XL-18` | Collision policy: prompt appears, keep-both increments `vN`, overwrite moves the old file to `.recycle`, locked file disables overwrite | UI test | UI + unit |
| `TST-XL-19` | Register export: two sheets, filtered counts equal the register counts, `All exceptions` is unfiltered | Register fixture | Structural |
| `TST-XL-20` | Owner distribution: workbook counts equal text counts; the text uses the §8 template (line width ≤ 100, no tabs, disclaimer on line 3) and parses back | Register fixture | Structural |
| `TST-XL-21` | Evidence bundle reconciles to the exception's subject rows; the zip manifest hashes match the archived files | `EXC-018` planting | Structural |
| `TST-XL-22` | CSV contract: UTF-8 BOM, comma delimiter, CRLF, quoting rules, raw numbers, token preservation; sidecar validates against the schema | Export fixtures | Unit |
| `TST-XL-23` | Cross-artifact equality for the full comparison set, both pairs, zero tolerance | Fixed filter state | E2E |
| `TST-XL-24` | Performance and size: 250k-row pack ≤ 120 s, ≤ 150 MB; ad-hoc export ≤ 20 s; memory within `NFR-005` | `--scale 250000` | Performance |
| `TST-XL-25` | Failure modes `ERR-EXP-001`…`011`: correct message, no partial file, correct next action; cancel leaves nothing behind | Fault injection | Unit + UI |
| `TST-XL-26` | Every sheet carries the short-form disclaimer in its footer (≤ 255 chars, no unescaped `&`) and the watermark whenever the project is the sample project | Golden pack + sample project | Structural |

## 14. Open items, deferrals and assumptions

| ID | Item | Status |
|---|---|---|
| `XL-CHART-DEFER` | **Charts inside the Excel pack.** Deferred: the pack ships data tables only; visual analysis lives in the app (`08` §13) and the deck (`12`). Reason: native openpyxl charts are hard to verify in the cross-artefact test and add size for little value. To be recorded as `BL-026` in `27_BACKLOG.md` | Deferred (parked) |
| `DEC-028` | **PDF rendering** (§10.3): v1 = print/PDF readiness + "Open for printing / Save as PDF"; no in-app renderer. Must be recorded in `01` §21 | Decision required — drafted here |
| `OQ-021` | Client's current report format: plain `.xlsx`, `.xlsm`, protected, or paper only? Determines the house-style importer's v1 depth | Open question for the client (`21`) |
| `OQ-022` | Preferred pack default: whole units or lakhs? Both are supported; the questionnaire default is whole units | Open question for the client (`21`) |
| Assumption A | Microsoft Excel 2016 or later / Microsoft 365 is the client's reader. The open-pyxl-written feature set is compatible with Excel 2016+, LibreOffice 7+ and Google Sheets | Assumption — validated in the real-Windows validation |
| Assumption B | The client's month-end pack is a single workbook of tens of sheets at most; the 8-sheet contract covers the required content, and additional sheets become backlog items rather than ad-hoc additions | Assumption |
| Assumption C | Amounts stay below ₹99,99,99,999.99 (₹999.99 crore) in any single cell; beyond that the grouping pattern's leading placeholder absorbs digits and grouping degrades (stated, not silently) — the boundary test documents the exact behaviour | Assumption, bounded |
| Note | Commentary is a **column** on `BvA Summary` (N), not an Excel cell comment/note, because comments do not print, do not export, and are easy to lose | Decision recorded here |

## 15. Change control

| Change | Requires |
|---|---|
| Adding, removing or renaming a **sheet** | Update §2/§4, the `Cover` contents table, `00_INDEX` doc map if the FR mapping changes, and `TST-XL-02/05/14`; regenerate the golden pack |
| Adding, removing or reordering a **column** | Update the §4 column table, the print area, the cross-artifact comparison set if the column carries a compared value, and `TST-XL-14`; a column that changes the row cap math updates §5.1 |
| Changing a **number format** | Update §3.6 and the boundary matrix (`TST-XL-07`); a new format ID is added, never renumbered |
| Changing a **conditional-formatting rule** | The rule set is owned by `08` §14 — change it there first, then mirror the Excel rendering in §3.7 and update `TST-XL-11` |
| Changing a **stamp field** | Update §3.2 (and the frozen label list), the undefined-name test, and every downstream consumer (`12`, `14`, `29`); stamp fields are never reused for a different meaning |
| Changing **filenames or collision policy** | Update §3.4 and `22` (user guide) and `24` (release runbook where packs are referenced) |
| Changing the **row-cap or split** behaviour | Update §5 and `TST-XL-16`; the constant `XLS_SAFE_MAX_DATA_ROWS` is frozen in this document, not in code |
| Any change here | Add a `CHANGELOG.md` entry and a `SESSION_LOG.md` row; re-run the structural tests before commit |

**Frozen constants owned by this document:**
`XLS_SAFE_MAX_DATA_ROWS = 1,048,500` · stamp labels and field order (§3.2) · sheet names and order (§4) ·
column headers and format IDs (§4, §3.6) · `CF-` application ranges and order (§3.7) · filename tokens and
sanitisation order (§3.4) · the short-form disclaimer footer (§10.1) · the owner-summary text template
(§8) · the sidecar and profile schemas (§7.3, §9.3).



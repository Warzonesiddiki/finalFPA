> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** `FR-IMP-001`…`FR-IMP-031`, `FR-XL-004` (naming), `FR-SET-002` (mapping management), `FR-SET-009` (storage/sync detection); import behaviour, file quirks, profiles, validation, quarantine rules
> **TL;DR (≤ 15 lines):** This document owns how files get in: the seven-step import wizard, the shipped
> templates and their version stamps, mapping profiles (structure, fingerprint auto-match, immutable
> versions, mid-year source changes), the per-profile value-parsing rules (dates, numbers, Cr/Dr,
> parentheses, fiscal text, dimension strings), the full Excel/CSV hardening list where every quirk is
> either handled or explicitly rejected with named error copy, the **32-check validation catalogue
> (`IMP-001`…`IMP-032`)**, the reject-vs-quarantine rule, balance and control-total reconciliation,
> duplicate detection keys, incremental monthly loading, atomic commit and crash recovery, the
> data-quality score inputs, and the validation report. Nothing is ever silently discarded: loaded +
> quarantined + rejected must always equal the source row count.

---

# 04 — SOURCE MAPPING AND IMPORT SPECIFICATION

## 1. Purpose and scope

This document owns **import behaviour**: what the user does, what the app accepts, what it refuses, what
it quarantines, what it reports, and the exact wording of the messages. It does not own:

- the canonical target tables and columns → `03_DATA_DICTIONARY.md`;
- calculation of the data-quality score → `05_CALCULATION_SPEC.md` (weights and formula);
- the mapping screens' layout and copy → `08_UI_UX_SPEC.md`;
- AI mapping suggestion prompt/schema → `10_AI_INTEGRATION_SPEC.md`;
- error-code numbering → `26_API_CONTRACT.md` (the **message slugs here are the join keys**).

**Governing principle (P13): nothing is silently discarded.** Every source row ends in exactly one of
three states — **loaded**, **quarantined**, or **rejected** — and the three counts must sum to the source
row count, always. That equation is printed on every validation report.

## 2. Source systems and file shapes

### 2.1 What arrives from the client (confirmed vs default)

| Source | Real columns known? | v1 handling |
|---|---|---|
| **D365 GL export** (edition unconfirmed — `Q-002`) | No | A shipped **D365-style GL profile** plus a documented dimension-parsing rule; per-edition profiles are added when the edition is confirmed. The default template mirrors a typical D365 GL export with a fiscal-period text column (`FY26-P09`) and optionally a combined dimension string |
| **System 2 — payroll summary** (`Q-003`) | No | A shipped **payroll-summary shape** (entity, cost centre/department, account, period, amount, employee count none) to prove mapping flexibility |
| **System 3 — procurement / bank ledger** (`Q-003`) | No | A shipped **procurement/bank-ledger shape** (vendor, invoice number, document date, amount, account, cost centre) |
| **Budget** | No | The budget template (`§4`) |
| **Forecast baseline** (optional) | No | The forecast template, imported as method `manual` |
| **Master data** (optional) | No | Vendor categories, recurring costs, approval thresholds, owner assignments |

**Non-negotiable:** the two non-D365 shapes must remain **materially different** from the D365 shape
(different header names, different date formats, one CSV and one XLSX) so that mapping flexibility is
demonstrated, not asserted. The sample dataset ships all four shapes.

### 2.2 Source-type registry

| `source_type` | Expected cadence | Target table(s) | Required mapping fields |
|---|---|---|---|
| `actuals_d365` | Monthly | `FactActual` | company, account, period **or** posting date, voucher, line, debit/credit (or amount) |
| `actuals_payroll` | Monthly | `FactActual` | company, cost centre, account, period **or** posting date, amount, voucher |
| `actuals_procurement` | Monthly | `FactActual` | company, vendor, invoice no, posting date, amount, account, cost centre |
| `budget` | Annually + ad-hoc reforecast | `FactBudget` | budget version, company, account, period, amount |
| `forecast_input` | Optional | `FactForecast` (method `manual`) | company, account, period, amount |
| `vendor_master` | Ad-hoc | `MasterVendorCategory`, `DimVendor` enrichment | vendor code, category |
| `recurring_costs` | Ad-hoc | `MasterRecurringCost` | name, account, cost centre, expected amount, frequency, start period |
| `approval_thresholds` | Ad-hoc | `MasterApprovalThreshold` | scope, amount threshold, effective from |
| `owner_assignments` | Ad-hoc | `MasterOwnerAssignment` | scope, owner name |

## 3. The import wizard (seven steps)

| Step | Screen behaviour | Failure/exit behaviour |
|---|---|---|
| **1. Choose** | Drag-and-drop zone + file picker; source type pre-suggested from the filename/headers and always overridable (FR-IMP-002) | Unsupported/zero-byte file → reject with named reason; folder dropped → explain; multiple files → queued sequentially with per-file status |
| **2. Pre-scan** | Reports file size, sheet list, estimated rows, estimated duration, and the limit check; the user confirms or cancels (FR-IMP-003) | Encrypted/protected workbook → reject with a named reason; limit exceeded → explicit confirmation required, recorded on the batch |
| **3. Sheet & header** | Profile proposes the sheet and header row; the user can pick another sheet and drag the header row. A preview of the parsed table (first 20 rows) is shown before any validation | No header detectable → user must pick the header row; a header-only file → reject with the `import.noDataRows` path (`§10`, E3) |
| **4. Map** | Column-by-column: source column → canonical field, ignore, or per-column override (format, scale, sign). Required fields show a live "still unmapped" indicator. Profile auto-match is pre-applied when the header fingerprint clears the threshold (FR-IMP-006) | Required field unmapped → cannot proceed; AI suggestions (if enabled) appear in the review queue and are **never auto-applied** (FR-IMP-008) |
| **5. Validate** | All 32 checks run with a progress bar and cancel; results are grouped by severity with counts and the first offenders | File-level failure → reject (nothing committed); row-level failures → quarantine (never drop) |
| **6. Commit** | The batch is committed atomically; the report is saved; the raw file is archived with its checksum | Cancel during commit → transaction rolls back, batch recorded as `cancelled`, no partial data |
| **7. Confirm** | Summary: rows loaded/quarantined/rejected, balance result, score, batch ID, where the report is, and what to do next (Fix quarantined rows / Continue to Check) | Quarantine pending items remain visible on Home as a health warning until resolved |

**Resumability:** wizard state is persisted; after an app restart the user is offered "Resume import of
&lt;file&gt;" with the exact step restored. Nothing about an interrupted import is left ambiguous:
the batch either exists as `committed`, or as `staged`/`cancelled`/`rejected` with a stated reason.

**Long-running UX:** progress percentage, ETA based on observed throughput, and a working Cancel at every
stage (FR-IMP-030); the UI never freezes; stage transitions are logged with timings.

## 4. Templates (shipped files, versioned)

### 4.1 Template inventory

| Template | Sheets | Notes |
|---|---|---|
| `TEMPLATE_Actuals_v<N>.xlsx` | `Data` (+ optional `ControlTotals`) | The `ControlTotals` sheet carries the optional client control-totals block (IMP-025) |
| `TEMPLATE_Budget_v<N>.xlsx` | `Data` (+ optional `ApprovedTotal`) | `ApprovedTotal` enables the sum-vs-approved check (IMP-026) |
| `TEMPLATE_Forecast_v<N>.xlsx` | `Data` | Optional manual baseline |
| `TEMPLATE_MasterData_v<N>.xlsx` | `VendorCategories`, `RecurringCosts`, `ApprovalThresholds`, `OwnerAssignments` | One file, four optional sheets |
| `TEMPLATE_D365_Style_GL_v<N>.xlsx` | `GL_Export` | Mirrors the default D365 shape so the client can compare against a real export |

### 4.2 Template versioning rules

1. Every shipped template contains a hidden-safe **version stamp cell** (defined in `08`) and a visible
   "Template version" row in the header block.
2. On import, the detected stamp is compared with the current app's template version:
   - current → no message;
   - older → a warning naming the differences and requiring confirmation to continue (FR-IMP-007);
   - newer than the app → refuse with "this file was built for a newer version of the app".
3. Templates are downloadable in-app (FR-ONB-005) and the downloaded file must be byte-comparable with
   the shipped template for the same version (tested).
4. A template change bumps its version and adds a `CHANGELOG` entry; the old version remains supported for
   import (with the warning) — templates are never silently changed in place.

## 5. Mapping profiles

### 5.1 Profile contents

A profile is the complete, reusable answer to "how do I read this file shape?" — stored as data, never
hardcoded (`03` §5.5):

| Element | Example | Notes |
|---|---|---|
| `name` | `D365 GL export (Sep-26 shape)` | User-facing |
| `source_type` | `actuals_d365` | Must match the batch's source type |
| `header_signature` | SHA-256 over the sorted, normalised header set | Drives FR-IMP-006 auto-match |
| `sheet_selector` | `GL_Export` or `first` | `first` records which sheet was actually used |
| `header_row` | `4` | 1-based; handles banner rows |
| `multi_header_rows` | `[4,5]` | Concatenated with `" / "` when declared |
| `delimiter` / `encoding` | `;` / `cp1252` | CSV only; confirmed at pre-scan |
| `date_rule` | `dd-mm-yyyy` | Documented per-profile rule; ambiguity must be confirmed |
| `number_rule` | `parens_negative` + `strip_currency` | Cr/Dr suffix handling included |
| `column_map` | `Ledger account → account_code` | Plus `__ignored__` entries |
| `transforms` | `{"cost_center_code":{"from":"dimension_string","pattern":"CC=(?P<v>\\d+)"}}` | Dimension-string parsing |

### 5.2 Auto-match (FR-IMP-006)

- Normalisation for fingerprinting: trim, case-fold, collapse whitespace, strip trailing `:`/`*`, and
  remove BOM/zero-width characters.
- Similarity = Jaccard overlap of the normalised header sets. At or above the configured threshold
  (default **0.80**), the profile is pre-selected with a confidence note; below it, no suggestion is made
  (never a wrong guess).
- The user can always choose another profile or map from scratch; the choice is recorded on the batch.

### 5.3 Versioning and mid-year source changes (FR-IMP-026)

1. Profiles are **immutable per version**. Any edit creates a new version with `change_note`,
   `effective_from_period_id`, and full history (revert = create a new version equal to an old one, so the
   change itself is auditable).
2. Each batch records `profile_id` + `profile_version` + `template_version_seen`.
3. When a source system changes columns mid-year, the user edits the profile → new version effective from
   period *P*; earlier batches keep their original version and continue to reconcile.
4. Import History shows which version each batch used; a discrepancy report is available ("batches using
   non-current profile versions").
5. A profile used by a **closed** period's batch cannot be deleted; it can be superseded.

### 5.4 Built-in profiles

Shipped, read-only (clone to edit): `D365 GL (default)`, `Payroll Summary`, `Procurement / Bank Ledger`,
`Budget Template`, `Forecast Template`, `Master Data`. Built-ins are versioned with the app and are
re-seeded (as new clones) on upgrade rather than mutated.

## 6. Canonical field reference (mapping targets)

| Canonical field | Applies to | Required? | Notes |
|---|---|---|---|
| `company_code` | actuals, budget, forecast | Required for actuals/budget | Unmapped → derived from the project's single-entity setting, if configured, with a notice |
| `account_code` | actuals, budget, forecast | Required | Unmapped → `IMP-010` blocks |
| `cost_center_code` | actuals, budget | Optional | Null allowed for e.g. payroll lines |
| `department_code` | actuals | Optional | Mapped to a department node in `DimCostCenter` |
| `project_code` | actuals, budget | Optional | |
| `vendor_code` / `vendor_name` | actuals (procurement), vendor master | Optional | Name alone is accepted; a stable code is preferred |
| `posting_date` | actuals | Required unless `period_code` is mapped | Drives period assignment (`05`) |
| `document_date` | actuals | Optional | Cut-off rule input only |
| `period_code` | actuals, budget, forecast | Alternative to dates | `FY26-P09` parsed to `DimPeriod` |
| `voucher_no` | actuals | Required | Part of the dedup key |
| `document_no`, `invoice_no` | actuals | Optional | Invoice number feeds duplicate/threshold rules |
| `line_no` | actuals | Recommended | Defaults to source row order if absent, with a notice |
| `description` | actuals | Optional | Hostile input: sanitised, capped at 500 chars |
| `debit`, `credit` | actuals | One of them, or `amount` | Sign convention resolved by the profile rule |
| `amount` | budget, forecast, payroll, procurement | Required | Mapped to `debit`/`credit` per the sign rule for actuals |
| `currency_code` | all money sources | Optional | Absent → project currency; a differing value → quarantined (E10) |
| `journal_category` | actuals | Optional | `manual`/`auto`/`reclass`/`accrual`; invalid values → quarantine |
| `budget_version` | budget | Required | Defaults to `FY<yy>-Approved` with a notice if absent |
| `scenario_code` | budget, forecast | Optional | Defaults to `base` with a notice |
| `expected_amount`, `frequency`, `start_period_code` | recurring costs | Required | |
| `amount_threshold`, `scope`, `effective_from` | approval thresholds | Required | |
| `owner_name` | owner assignments | Required | |

**Ignored columns** are recorded explicitly (never implied): the batch stores the list of ignored source
columns so a later review can see exactly what was not loaded.

## 7. Value parsing rules (per profile, never per guess)

### 7.1 Dates

| Rule | Behaviour |
|---|---|
| `iso` | `YYYY-MM-DD` |
| `dd-mm-yyyy` | Day-first (also accepts `/` and `.` separators) |
| `mm-dd-yyyy` | Month-first, only if explicitly configured |
| `excel_serial` | Numeric serial → date using the workbook's epoch convention |
| `datetime` | Datetime → date part, with the time recorded in the validation detail |
| **Ambiguity rule** | If a value parses under both day-first and month-first interpretations **and** the file's values contradict one another, parsing **stops for that column** and the user is asked once, with examples; the choice is saved into the profile version. Values that are unambiguous are never used to justify guessing on ambiguous ones |

### 7.2 Numbers and signs

| Case | Behaviour |
|---|---|
| Thousands separators (`,` ` ` `.`) | Stripped per the profile rule; a decimal comma locale is an explicit setting, never inferred from a single value |
| Currency symbols (`₹`, `$`, `€`) | Stripped |
| Accounting parentheses `(1,200.00)` | Parsed as **negative** when the profile's `number_rule` says so |
| Trailing `Cr` / `Dr` | Interpreted per the profile rule: `Dr` → debit, `Cr` → credit for balance-style exports; for amount-style exports, `Cr` → negative |
| Text-formatted numbers (`"1200"`, `"1,200.00 "`) | Parsed; non-parseable → quarantine (IMP-016) |
| Both `debit` and `credit` populated on one row | Warn (`IMP-022`), load as provided (the model stores both; `net_amount` is derived) |
| Negative where the sign rule forbids it | Warn or quarantine per the documented rule for the source type |
| Scientific notation (`1.2E+05`) | Accepted only when the profile allows it (default: rejected with a message naming the cell) |

### 7.3 Dimension strings (e.g. `Dept=100|CC=200`)

The parsing rule is documented and profile-driven: split on the configured delimiter (`|`, `;`, `,`),
then split each token on the configured separator (`=` or `:`), trim, upper-case the keys, and map known
keys to canonical fields. Unknown keys are collected and reported as a warning listing the distinct
unknown keys (never dropped silently). A token that does not match the pattern → quarantine with the
offending token shown.

### 7.4 Fiscal period text

`FY26-P09` → `DimPeriod` row via `(fiscal_year, period_number)`. Accepted variants (profile-declared):
`FY26-P09`, `2026-P09`, `202609`, `Sep-26`, `09/2026`. A period code that does not exist in the project's
fiscal calendar → quarantine (IMP-018), never a silent fallback to the posting month.

### 7.5 Booleans and enumerations

`TRUE/FALSE`, `Y/N`, `Yes/No`, `1/0` per the profile rule. Enum values (e.g. `journal_category`) are
validated against the allowed list (`03` §1.2); an invalid value → quarantine (never coerced to the
nearest match).

## 8. Excel structure hardening (every quirk: handled or explicitly rejected)

Addon 1 §F requires each quirk below to have a documented handle-or-reject behaviour **with error copy
that names the sheet and the row/cell**. Column "Behaviour" states which of the two it is; the message
slugs resolve to user copy through `26`.

| # | Quirk | Detection | Behaviour | Slug |
|---|---|---|---|---|
| X1 | Title/banner rows above the real header | Candidate header row scoring (density of non-empty, text-like, unique cells) | Profile's `header_row` wins; otherwise the highest-scoring row is proposed and the user confirms visually on the parsed preview | `import.headerRowProposed` |
| X2 | Merged cells above or inside the header | Merge ranges in the header zone | Merged header cells are unmerged in memory and each cell's value is propagated; merged **data** cells are reported and the affected rows are quarantined (a merged data cell cannot be attributed to one row) | `import.mergedDataCells` |
| X3 | Multi-row headers | Profile's `multi_header_rows` | Concatenated with `" / "` (e.g. `Amount / Debit`); if not declared, the user can select additional header rows in the wizard | `import.multiRowHeader` |
| X4 | Embedded `Total` / `Subtotal` rows | Label match in the key column(s) + a numeric row below a blank separator | Excluded from the load and **counted and listed** in the report as "summary rows ignored" — never silently dropped, never loaded as data | `import.totalRowsIgnored` |
| X5 | Blank trailing rows/columns | Trailing empty range detection | Trimmed and counted in the report ("N blank trailing rows trimmed") | `import.blankTailTrimmed` |
| X6 | Fully blank rows inside the data | All-mapped-columns-empty test | Counted as ignored blanks and listed with their row numbers; never quarantined as errors (they carry no data) | `import.blankRowsIgnored` |
| X7 | Hidden sheets | Sheet visibility flag | Hidden sheets are **not** read unless explicitly selected; the report lists them so the user knows they were skipped | `import.hiddenSheetSkipped` |
| X8 | Multiple sheets | Sheet enumeration | The profile's selector decides; with `first`, the chosen sheet name is recorded and displayed; the user can switch before validating | `import.sheetSelected` |
| X9 | Protected sheet (read allowed) | Workbook protection flags | Read succeeds → proceed; the report notes the protection. Read fails → reject with the sheet named and instructions to remove protection | `import.sheetProtected` |
| X10 | Encrypted workbook | Open attempt fails with an encryption error | Reject: "This file is password-protected. Save an unprotected copy and try again." | `import.encryptedFile` |
| X11 | Formula cells | Cell data type | **Cached values only** (`data_only=True`). A formula cell with no cached value → the row is quarantined with the cell reference | `import.formulaNoCachedValue` |
| X12 | Error cells (`#REF!`, `#DIV/0!`, `#N/A`, `#VALUE!`) | Cell value match | Quarantined per row; the report counts them per column with examples. Never loaded as text, never as zero | `import.errorCell` |
| X13 | Dates stored as text | Value parse under the profile's date rule | Parsed per rule; unparseable → quarantine (IMP-014); ambiguous → the ambiguity rule (§7.1) | `import.dateUnparsed` |
| X14 | Dates stored as serials | Numeric in a date-mapped column | Converted with the workbook epoch; the report states the conversion count | `import.serialDatesConverted` |
| X15 | Numbers stored as text | Numeric column with text-like values | Parsed per the number rule; failures quarantine (IMP-016) | `import.numberUnparsed` |
| X16 | Trailing `Cr`/`Dr` | Suffix match | Parsed per the profile's sign rule; the interpreted direction is stated in the report | `import.signRuleApplied` |
| X17 | Currency symbols in numeric cells | Symbol match | Stripped per the number rule | `import.currencySymbolStripped` |
| X18 | Accounting parentheses negatives | Pattern match | Parsed as negative when the rule says so; otherwise quarantine with the raw value shown | `import.parenthesesUnresolved` |
| X19 | Combined dimension string (`Dept=100\|CC=200`) | Column mapped as `dimension_string` | Split per §7.3; unknown keys reported; malformed tokens quarantined | `import.dimensionUnparsed` |
| X20 | Fiscal period as text (`FY26-P09`) | Column mapped as `period_code` | Resolved against `DimPeriod`; unknown → quarantine (IMP-018) | `import.periodNotInCalendar` |
| X21 | Duplicate column headers | Normalised header comparison | **Blocked** until the profile renames or ignores the conflicting columns (never auto-suffixed silently) | `import.duplicateHeaders` |
| X22 | Header-only / no data rows | Data-range emptiness after the header | Rejected by default with the zero-activity override path (§10, E3) | `import.noDataRows` |
| X23 | Excel "table" objects and autofilters over the range | Table metadata | Read normally; filters do not hide rows from the reader, and the report states if rows were filtered in Excel (detected via hidden-row metadata) | `import.rowsHiddenInExcel` |
| X24 | Very wide files (many unmapped columns) | Column count vs mapped count | Proceed; unmapped columns are listed explicitly as ignored (never implied) | `import.ignoredColumns` |
| X25 | File open/locked in Excel | Lock error on open | Retry once, then a message naming the file: "Close the file in Excel and try again." | `import.fileLocked` |
| X26 | File on a OneDrive-synced path | Path inspection | Warn about sync/locking risk with an offer to copy the file into the project archive first (the import always reads a stable copy) | `import.syncedPathWarning` |

## 9. CSV hardening

| # | Case | Behaviour | Slug |
|---|---|---|---|
| C1 | UTF-8 BOM | BOM stripped; encoding recorded | `import.encodingDetected` |
| C2 | UTF-8 without BOM | Detected by validation of the byte stream | `import.encodingDetected` |
| C3 | Windows-1252 with accented characters | Decoded correctly; the detected encoding is shown for confirmation before parsing (never a silent mojibake load) | `import.encodingDetected` |
| C4 | Unknown/other encoding | Reject with the detected byte pattern and instruct the user to re-export as UTF-8 or Windows-1252 | `import.encodingUnsupported` |
| C5 | Delimiters: comma, semicolon, tab, pipe | Auto-detected by field-count consistency across sample lines; **shown for confirmation** before parsing | `import.delimiterDetected` |
| C6 | Ambiguous delimiter (e.g. single column with commas inside quotes) | Force an explicit user choice; offer a "single column" parse | `import.delimiterAmbiguous` |
| C7 | Quoted fields containing delimiters | Parsed correctly (RFC 4180) | — |
| C8 | Quoted fields containing newlines | Parsed correctly; the row's source reference reports the logical row number and the physical line range | `import.multilineField` |
| C9 | Mixed line endings (CRLF/LF/CR) | Normalised; count reported | `import.lineEndingsNormalised` |
| C10 | Ragged rows (fewer/more fields than the header) | Fewer → missing values treated as empty and validated normally; more → extra fields quarantined as a structural warning naming the line | `import.raggedRow` |
| C11 | Trailing delimiter on every line | Detected and ignored; count reported | `import.trailingDelimiter` |
| C12 | Leading/trailing whitespace in headers and values | Trimmed for matching and parsing; original values preserved in quarantine payloads | `import.whitespaceTrimmed` |

## 10. Validation check catalogue (`IMP-001`…`IMP-032`)

Scope: **F** = file-level (failure rejects the file), **R** = row-level (failure quarantines the row),
**W** = warning (records a finding and continues). "On failure" states the enforced behaviour; all
failures appear in the validation report with counts and samples.

| ID | Check | Scope | On failure | Severity | Slug |
|---|---|---|---|---|---|
| `IMP-001` | File readable and format supported | F | Reject | High | `import.unreadableFile` |
| `IMP-002` | File size within the configured limit (`NFR`) | F | Explicit confirmation required, else reject | Medium | `import.fileTooLarge` |
| `IMP-003` | Row count within the configured limit (`NFR`) | F | Explicit confirmation required, else reject | Medium | `import.rowLimitExceeded` |
| `IMP-004` | Header row detected | F | User must pick the header row | High | `import.noHeaderDetected` |
| `IMP-005` | Required columns present after mapping | F | Reject, naming each missing column and the sheet | High | `import.missingRequiredColumns` |
| `IMP-006` | Duplicate column headers resolved | F | Block until renamed or ignored | High | `import.duplicateHeaders` |
| `IMP-007` | Expected sheet present (per profile) | F | User picks a sheet or cancels | High | `import.sheetNotFound` |
| `IMP-008` | Data range not empty | F | Reject (zero-activity override available) | High | `import.noDataRows` |
| `IMP-009` | Workbook not encrypted / not unreadable | F | Reject | High | `import.encryptedFile` |
| `IMP-010` | All required canonical fields mapped | F | Block until mapped | High | `import.mappingIncomplete` |
| `IMP-011` | Unmapped-row share below 90% | F | Reject with a mapping CTA and the unmapped share | High | `import.unmappedThreshold` |
| `IMP-012` | Dimension-string tokens parsed | R | Quarantine the row | Medium | `import.dimensionUnparsed` |
| `IMP-013` | Unknown/unmapped account codes | W | List distinct codes with row counts and a mapping CTA | Medium | `import.unknownAccounts` |
| `IMP-014` | Date values parsed | R | Quarantine the row | High | `import.dateUnparsed` |
| `IMP-015` | Ambiguous date formats confirmed | F | Stop and ask once; save the choice to the profile version | High | `import.ambiguousDate` |
| `IMP-016` | Numeric values parsed | R | Quarantine the row | High | `import.numberUnparsed` |
| `IMP-017` | Sign / `Cr`-`Dr` interpretation applied | R | Warn with the interpreted direction and the rule used | Low | `import.signRuleApplied` |
| `IMP-018` | Period resolved against the fiscal calendar | R | Quarantine the row | High | `import.periodNotInCalendar` |
| `IMP-019` | Dates inside the configured fiscal year | R | Quarantine the row | Medium | `import.dateOutsideFiscalYear` |
| `IMP-020` | Currency matches the project currency | R | Quarantine the row, naming the currencies found | High | `import.mixedCurrency` |
| `IMP-021` | Zero-amount rows noted | R | Keep the row; count and flag it (excluded from outlier rules) | Low | `import.zeroAmountRows` |
| `IMP-022` | Debit and credit not both populated | R | Warn; load as provided | Low | `import.bothDebitCredit` |
| `IMP-023` | Debit = credit within tolerance, per file/entity/period | F | Reject; show the imbalance amount and the top contributing rows | High | `import.balanceMismatch` |
| `IMP-024` | Row-count reconciliation (source = loaded + quarantined + rejected) | F | **Block commit** (internal invariant; a mismatch is a bug, never a user error) | High | `import.countMismatch` |
| `IMP-025` | Control-total variance within tolerance (when provided) | F | Fail the import or require a recorded acceptance (`§12`) | High | `import.controlTotalVariance` |
| `IMP-026` | Budget sum matches the approved total (when provided) | F | Fail or require a recorded acceptance | Medium | `import.approvedTotalVariance` |
| `IMP-027` | Within-file duplicate candidates reported | R | Report only — never auto-delete | Medium | `import.duplicateCandidates` |
| `IMP-028` | Cross-batch duplicate candidates reported | R | Pre-commit report; the user chooses skip / import anyway (recorded) / cancel | Medium | `import.crossBatchDuplicates` |
| `IMP-029` | File checksum not previously committed | F | Block: "already imported on <date> as batch <id>" | High | `import.alreadyImported` |
| `IMP-030` | Inactive cost centre usage noted | R | Warn and list (the exception engine also raises this; no double-reporting in the UI) | Low | `import.inactiveCostCentre` |
| `IMP-031` | Budget coverage matrix reported | F | Report the missing entity × account × period cells as a percentage, listable | Medium | `import.budgetCoverageGap` |
| `IMP-032` | Budget/forecast duplicate lines on the uniqueness key | R | Report; block the commit only when the duplicates conflict (same key, different amount) | Medium | `import.duplicateBudgetLines` |

**Check-skipped rule:** a check that cannot run (e.g. no control-totals block supplied) is recorded as
`skipped` **with a reason**, never silently omitted (FR-IMP-021).

## 11. Reject vs quarantine — the decision rule (fixed, not per-case)

| Level | Definition | Consequence |
|---|---|---|
| **File-level failure (reject)** | The file as a whole cannot be trusted or read: unreadable/encrypted, no header, missing required columns, duplicate headers unresolved, ≥ 90% rows unmapped, debit ≠ credit (journal-style sources; amount-style scope per §12 `DEC-056`), checksum re-import, newer template, empty data range (default) | **Nothing is committed.** The batch is recorded as `rejected` with the failing check, the file is not added to the analytic model, and the report states exactly what to fix |
| **Row-level failure (quarantine)** | A single row cannot be attributed or parsed, but the rest of the file can: unparseable date/number, period outside the calendar, mixed currency, malformed dimension token, error cell | The row is written to `QuarantineRow` with raw values, its source reference, and a reason; it is **visible, countable, exportable and resolvable** (fix-and-reimport, import-as-is with a recorded decision, or discard with a recorded decision) |
| **Warning** | Suspicious but loadable: zero-amount rows, both debit and credit, unknown accounts, inactive cost centres, sign-rule application | Loaded; recorded in the report for review; may also raise an exception via the rule engine (`06`) |

**No third path exists.** "Drop the row and say nothing", "load it anyway and hope" and "silently coerce
the value" are all protocol violations (P13).

## 12. Balance and control-total reconciliation

| Check | Rule |
|---|---|
| **Debit = credit** | Journal-style sources (scope row below, `DEC-056`): computed at minor-unit precision (exact; no epsilon, `05` §13) per file, per entity, per period, and overall. Tolerance may be configured only with a documented reason, and any non-zero tolerance is stated in the report |
| **Scope by source type (`DEC-056`)** | Journal-style sources (`actuals_d365`, budget) are rejected on any imbalance. Amount-style sub-ledger exports (`bank_ledger`, `payroll_procurement` per §2.2) are one-sided by nature; they are validated by **control totals / net-amount reconciliation** with the documented **₹500 tolerance** of `06` §8 instead — within tolerance the file loads and the variance is stated in the report; beyond tolerance it fails with the recorded-acceptance path above. This **scopes** `IMP-023`, it does not exempt any source from a money-integrity gate |
| **Row-count reconciliation** | `source = loaded + quarantined + rejected`, asserted before commit (IMP-024) |
| **Control totals (optional block)** | When the `ControlTotals` sheet is present: compare file totals (as supplied by the client) vs loaded totals vs previous-period totals where useful; report the variance. **Decision `DEC-022`:** a variance beyond tolerance **fails the import by default**; the user may accept it explicitly, and the acceptance is recorded on the batch (who, when, why) — never silent |
| **Approved total (budgets)** | When the `ApprovedTotal` sheet is present: compare the sum of loaded budget lines with the approved figure; report the delta; fail by default with a recorded-acceptance path |
| **No control totals supplied** | The check is `skipped` with the reason "no control-totals block supplied" — never reported as `pass` |

**`ControlTotals` worksheet shape:** row 1 contains `Scope`, `SuppliedTotal`, and optional `Measure` and `Tolerance`; each subsequent non-empty row is one file-level total. `Scope` is a unique stable label used by `EXC-003`. `Measure` is `debit`, `credit`, or `net`; it may be omitted when `Scope` itself is one of those values. The loaded amount is respectively the sum of imported debits, credits, or net amounts. `Tolerance` defaults to `0.00` and cannot be negative. A variance beyond tolerance rejects the batch unless the import request carries `controlTotalAcceptance` with a non-blank `acceptedBy` and a reason of at least 10 characters. Acceptance details are persisted with `IMP-025`; they do not suppress the `EXC-003` finding.

## 13. Duplicate detection

| Level | Key (documented in `03` §6) | Behaviour |
|---|---|---|
| Within a file | `row_fingerprint` (company, voucher, line, posting date, account, debit, credit, cost centre) | Counted, sampled, reported; **not** auto-deleted |
| Cross-batch | (`company_code`, `voucher_no`, `line_no`) **and** (`vendor_code`, `invoice_no`, `posting_date`, `amount`) | Pre-commit report naming the earlier batch and date; user chooses skip / import anyway (recorded) / cancel. Overlapping rows are never double-counted without a recorded decision |
| File level | `file_checksum` (SHA-256) | Hard block with the original import date and batch ID |
| Budget/forecast | uniqueness key from `03` §2.1 | Conflicting duplicates (same key, different amount) block the commit; exact duplicates are reported and de-duplicated with a recorded count |

**Rationale for two cross-batch keys (`DEC-021`):** voucher-based keys catch re-exports of the same
ledger, while invoice-based keys catch duplicate invoices posted under different vouchers. Both are
needed; neither is sufficient. The default action on a detected overlap is **report and ask**
(`DEC-023`) — never auto-skip and never auto-import. The decisions are recorded in `01_PRD.md` §21 and,
canonically, in `18_...OPEN_QUESTIONS.md` §Decided.

## 14. Incremental monthly load rules

1. **Additive by default.** A new period's files are added; previously loaded periods are untouched.
2. **No implicit reload.** Re-importing a period requires the previous batch to be **voided** first
   (FR-IMP-024), which is audited and blocked for closed periods.
3. **Mappings carry forward, numbers never do** (FR-PRJ-004): a New Period wizard copies profiles,
   thresholds and master data, and copies no amounts.
4. **Late-arriving data.** A correction file for an earlier open period is allowed and creates its own
   batch; it changes that period's figures, and any derived results referencing it are marked stale.
5. **Closed periods.** Import/void into a closed period requires an explicit, warned, audited reopen
   (FR-PRJ-005).
6. **Idempotency.** Re-running a failed/cancelled import does not create duplicate facts (enforced by
   `row_fingerprint` + the checksum guard, not by user discipline).

## 15. Atomic commit, cancellation and recovery

| Stage | Storage | Crash/cancel behaviour |
|---|---|---|
| Pre-scan, sheet/header, mapping | Memory only | Nothing written |
| Parse + validate | Rows written to the **staging area** inside the project, tagged to a `staged` batch | On next launch the staged batch is detected and offered: **discard** or **resume**. The UI states clearly that nothing was committed |
| Commit | Single transaction: facts inserted, batch status → `committed`, validation report + checks, archive reference written | Rollback on any error; batch → `rejected`/`cancelled` with the reason |
| Post-commit | Derived results marked stale; Home shows the new batch | A crash after commit but before the UI refresh is harmless: the data is committed and derivations are recomputed or flagged on next launch |

**Sleep/standby mid-import** (A1 §G.4): either the operation completes on resume, or it fails cleanly
with the staged batch recoverable on next launch — never a half-written state, never a hung spinner.

## 16. Data-quality score (inputs only)

The score is a weighted composite of the checks above, computed per batch and displayed **alongside**
the failed checks (never instead of them). The formula, weights and worked example are owned by
`05_CALCULATION_SPEC.md`; this document defines the inputs:

| Input | Source |
|---|---|
| Per-check pass/fail/skip status and `offending_count` | `FactValidationCheck` |
| Per-check `weight` | Seeded per check, editable in Settings, versioned |
| Row-count ratios (`quarantined ÷ source`, `zero-amount ÷ source`, `duplicate candidates ÷ source`) | Batch counters |
| Balance and control-total results | Batch counters |
| Coverage percentage (budgets) | `IMP-031` |

A batch with any failed **High**-severity check can never display a perfect score; the arithmetic
guarantees it (the weights of failed high-severity checks are a fixed, non-zero share).

## 17. Validation report

Contents (saved with the batch, viewable in-app, exportable to Excel/CSV — FR-IMP-021):

1. **Header block:** project, source type, file name, checksum (short), sheet, profile + version,
   template version seen, batch ID, period, who/when, app + schema version.
2. **The reconciliation equation:** source = loaded + quarantined + rejected, with each figure.
3. **Check results table:** every one of the 32 checks with status, severity, offending count, and the
   first N offenders (default 20) showing sheet/row/cell references.
4. **Balance block:** debit, credit, variance, per entity and per period.
5. **Control-total block** (when supplied): supplied vs loaded vs variance and the acceptance record.
6. **Duplicate block:** within-file and cross-batch candidates with samples and the decision taken.
7. **Ignored content list:** ignored columns, skipped sheets, hidden sheets, total/subtotal rows,
   blank rows, trimmed whitespace — each with counts (never implied).
8. **Score block:** the composite score with its weighted components.
9. **Next actions:** a plain-language list ("Fix 8 quarantined rows", "Map 3 unknown accounts",
   "Confirm the date format for this profile").

## 18. Batch lifecycle and void

```
staged ──commit──► committed ──void──► voided
   │                    ▲
   │                    └── (no return to staged; a re-import is a new batch)
   ├──cancel──► cancelled
   └──reject──► rejected
```

| Rule | Detail |
|---|---|
| Void scope | Exactly one batch; other batches' facts are untouched |
| Void preconditions | Period open (else an audited reopen); typed confirmation naming the batch ID and file name |
| Void effects | Facts removed in a single transaction; archive file retained (evidence); validation report retained; dependent derived results marked stale; audit entry written with a mandatory reason |
| Void vs issued packs | Allowed with a warning that the issued pack's snapshot is unchanged and a re-issue will be required for any changed figures (FR-PRJ-010) |
| Deletion | Batches are **never deleted**; voided batches remain visible in Import History for the audit trail |

## 19. Error-copy standards (binding for every message above)

Every message follows the same three-part shape:

> **[What happened]** — *[where, precisely]* — **Next: [one clear action].**

Rules:

1. **Name the object:** the file, sheet, column, row and cell where known. Never "invalid data".
2. **Give one primary next action**, not a menu of five; secondary options (download template, view
   report) are links.
3. **No codes as the primary message.** Error codes (`ERR-IMP-*`) appear in a details/copy area for
   support, never as the headline.
4. **No blame, no jargon:** "The file has 3 rows the app could not read" not "parse exception in
   RowParser".
5. **Never a raw traceback** (FR-XC-006); the log keeps the technical detail.
6. **Numbers are formatted** per the project's display settings (grouping, symbols) even inside errors.

Worked examples:

| Situation | User-facing copy |
|---|---|
| Missing column | *"Column 'Cost Center' wasn't found in sheet 'GL_Export'. Next: map it now, or download the current template."* |
| Balance failure | *"This file's debits (₹ 1,84,50,200.00) don't equal its credits (₹ 1,84,49,850.00) — a difference of ₹ 350.00. Next: check row 412 of 'GL_Export', or ask your ERP team to re-export the period."* |
| Ambiguous dates | *"Rows 12 and 87 could be read as 03-04-2026 (3 April) or 04-03-2026 (4 March). Next: choose the format used by this file — your choice is saved for next month."* |
| Quarantined rows | *"184,494 rows loaded. 8 rows need your attention — they're saved in the quarantine list. Next: review the 8 rows."* |
| Re-import guard | *"This exact file was already imported on 14-Sep-2026 (batch 37). Next: view that import, or import a corrected file."* |
| Mixed currency | *"2 rows are in USD but this project reports in INR. Next: review the 2 quarantined rows, or change the project currency in Settings."* |
| Older template | *"This file was built with template version 2; version 3 is current. The differences are listed in the report. Next: continue, or download the current template."* |

## 20. Mapping to the canonical edge cases (`02` §16)

| Edge case | Import behaviour |
|---|---|
| E3 header-only file | Reject by default; the zero-activity override requires an explicit confirmation naming the period |
| E4 zero-amount rows | Kept, flagged by IMP-021, excluded from outlier rules, visible in drill-down |
| E6 dates outside the fiscal year | Quarantined by IMP-019 with the row and date shown |
| E7 duplicate headers | Blocked by IMP-006 until renamed/ignored |
| E8 ≥ 90% unmapped | Blocked by IMP-011 with the unmapped share and a mapping CTA |
| E10 mixed currency | Quarantined by IMP-020 (default stance; revisitable if `Q-006` confirms multi-currency) |
| E11 display precision | Import stores full declared precision; rounding is a display-time rule (`05`) |
| E12 tiny files | Fully supported; no minimum-size assumption anywhere in the pipeline |
| E13 parentheses / `Cr`-`Dr` / text numbers | Handled by §7.2 rules; ambiguity confirmed once and saved to the profile |
| E1/E2 first period / no budget | Import-side: allowed and recorded; the UI consequences live in `02`/`08` |

## 21. Open items and dependencies

| Item | Status |
|---|---|
| Real column lists for D365 edition, payroll and procurement (`Q-002`, `Q-003`) | Open — defaults shipped; profiles will be tuned on the first real file set |
| Enforced file-size and row limits | Numbers owned by `14` (`NFR-002`); this doc consumes them |
| Control-total default: fail vs accept-with-record | **Decided: fail by default, with a recorded acceptance path** (`DEC-022`) |
| Cross-batch duplicate default action | **Decided: report and ask; never auto-skip or auto-import** (`DEC-023`) |
| Quarantine retention | Kept with the batch for the project's lifetime (evidence); raw archive retention follows `09`/`13` |
| AI mapping suggestions | Behaviour here; prompt, schema and caps in `10`; queue states also referenced in `03` §5.5 |


> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** data model — tables, columns, types, grains, keys, nullability, identities, store placement, example rows; schema versioning
> **TL;DR (≤ 15 lines):** The canonical model is a star schema in two stores: **DuckDB** holds the analytic
> model (immutable facts + slowly-changing dimensions + validation results + derived views); **SQLite**
> holds workflow state (import batches, exception register, master data, mappings, commentary, audit, AI
> drafts, issuance). Every fact row links to `import_batch_id`; every batch links to an immutable archived
> file with a checksum. Money is `DECIMAL(18,2)` at minor-unit precision — **floats are forbidden in
> money paths**; rates `DECIMAL(18,6)`; quantities `DECIMAL(18,3)`. Grains are declared for every table
> (§4) and are enforced by uniqueness constraints. Schema version lives in `SchemaMetadata` and is
> bumped only by a documented migration (`24`). This document is the single owner of table/column facts.

---

# 03 — DATA DICTIONARY

## 1. Scope, conventions and type system

This document owns **structure**: tables, columns, types, nullability, grains, keys, identities and
storage placement. It does not own formulas (`05`), rule logic (`06`), import mechanics and profile
behaviour (`04`), API shapes (`26`) or screen behaviour (`08`).

### 1.1 Naming conventions

| Convention | Rule |
|---|---|
| Table names | `PascalCase`, prefixed by role: `Fact*` (measurable events), `Dim*` (descriptive), `Master*` (editable reference data), `Map*`/`Mapping*` (mapping artefacts), `Fact*Event` (history of a fact), `View*` (derived read-only) |
| Column names | `snake_case`, singular, no abbreviations except the approved list (`id`, `no`, `code`, `amt`, `qty`, `pct`, `ref`, `ts`, `dt`) |
| Primary key | `<table_singular>_id`, `BIGINT`/`INTEGER` surrogate, never reused |
| Business key | `<thing>_code` or the documented natural key, with a `UNIQUE` constraint where required |
| Booleans | `is_*` / `has_*`, `BOOLEAN NOT NULL DEFAULT FALSE` |
| Timestamps | `*_at` (`TIMESTAMP`, local machine time, stored with the app's timezone offset in `SchemaMetadata.timezone`) |
| Dates | `*_date` (`DATE`) |
| Enumerations | `*_code` with the allowed values listed in the column description; stored as short `VARCHAR` (not DB enums, so new values do not need a migration) |
| Reserved audit columns | Every table ends with `created_at`, and mutable tables add `updated_at`, `updated_by` |

### 1.2 Type system and money rules (binding — never-cut list)

| Logical type | Physical type | Rules |
|---|---|---|
| **Money** | `DECIMAL(18,2)` | Minor-unit precision. **`FLOAT`/`DOUBLE`/`REAL` are forbidden in any money path** (schema-level test fails the build if one appears). Internal comparisons use exact equality — no epsilon (Addon 4 §G.1) |
| **Rate / ratio / percentage** | `DECIMAL(18,6)` | Percentages are stored as fractions (0.1234 = 12.34%); display applies 1 dp |
| **Quantity / units / headcount-equivalent (unused in v1)** | `DECIMAL(18,3)` | |
| **Identifier** | `BIGINT` / `INTEGER` | Surrogates for joins; business codes are `VARCHAR` |
| **Text (short)** | `VARCHAR(n)` | Codes ≤ 40, names ≤ 200, references ≤ 260 |
| **Text (long)** | `VARCHAR(2000)` / `TEXT` | Descriptions from source capped at 500 chars after hostile-input sanitisation (`10`, `13`) |
| **JSON blobs** | `JSON` (DuckDB) / `TEXT` with a `CHECK (json_valid(x))` (SQLite) | Used only for heterogeneous payloads (validation samples, prompt inputs, setting values); never for values that need querying by field without an extraction view |
| **Date / time** | `DATE` / `TIMESTAMP` | Dates are calendar dates with no time component; timestamps are local machine time |
| **Boolean** | `BOOLEAN` | Never `0/1` integers in the schema |
| **Enumeration** | `VARCHAR(n)` + documented allowed values + a `CHECK` constraint | Append-only: adding a value is a schema change (`24`) |

### 1.3 Nullability conventions

- `NOT NULL` is the default expectation. A nullable column exists only where the source may legitimately
  omit the value (e.g. `cost_center_id` on a payroll line).
- **Money columns in facts are `NOT NULL DEFAULT 0`**, never null — a missing amount is a validation
  failure at import, not a null in the model.
- Dimensions allow `NULL` parents (`parent_account_id`) and optional descriptive attributes.
- Every fact row requires `import_batch_id NOT NULL` (except forecast rows, which require
  `forecast_version_id NOT NULL`) — the traceability invariant.

### 1.4 Store placement (which database owns which table)

| Store | File (inside the project folder) | Owns | Characteristics |
|---|---|---|---|
| **DuckDB** | `analytics.duckdb` | Analytic model: `FactActual`, `FactBudget`, `FactForecast`, all `Dim*`, `FactValidationCheck`, `FactRuleRun`, quarantine staging, derived `View*` | Read-mostly, rebuildable from archives + configs; optimised for aggregation over 250k+ rows |
| **SQLite** | `state.sqlite` | Workflow state: `FactImportBatch`, `FactException` (+events), `FactPackIssue`, `FactPeriodSnapshot` metadata, `MappingProfile`(+versions), `MappingSuggestion`, `Master*`, configs, `Commentary`(+versions), `AuditLog`, AI usage/drafts, `VersionHistory`, `SchemaMetadata` | Transactional, small row counts, must never be lost; this is the authority for "what the human decided" |
| **Read-only projection** | `analytics.duckdb` → `ViewException` | A projection of the SQLite exception register for reporting joins, refreshed on demand and marked stale when out of date (FR-SET-010) | Never written directly; the register in SQLite is the authority |

**Rule:** a fact row's workflow state (status, owner, notes) lives **only** in SQLite; analytic measures
live **only** in DuckDB. Cross-store reporting uses the projection view plus denormalised display fields
on `FactException` (rule name, severity, period code) so no report needs a cross-store join at query
time.

### 1.5 Primary keys, identity and de-duplication

| Concept | Rule |
|---|---|
| Surrogate keys | Assigned by the loader, monotonic, never reused, never exposed to the user except in exports for support |
| Fact de-duplication | Every fact table carries a deterministic `row_fingerprint` (SHA-256 over the canonical business fields + batch-independent source identity) with a unique constraint per batch scope; the cross-batch duplicate report uses the documented business keys in §7 |
| Exception identity | `identity_hash = SHA-256(rule_id + '|' + subject_key)` — the stable join across re-runs (FR-EXC-004) |
| Mapping identity | `(profile_id, version_no)` — never mutable in place; edits create a new version |
| Idempotency | Re-running any derivation after a failure must produce the same rows, not duplicates (enforced by unique constraints, not by app logic alone) |

## 2. Model overview

```
                       ┌──────────────┐
   SQLite (state)      │ FactImport   │  batches, status, checksums, counts
   ──────────────      │ Batch        │
                       └──────┬───────┘
                              │ import_batch_id (every fact row)
   ┌──────────────────────────┼───────────────────────────────┐
   │  DuckDB (analytics)      ▼                               │
   │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐  │
   │  │ FactActual   │   │ FactBudget   │   │ FactForecast │  │
   │  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘  │
   │         └──────────┬───────┴──────────────────┘          │
   │                    ▼                                     │
   │   DimCompany · DimAccount · DimCostCenter · DimVendor ·   │
   │   DimProject · DimPeriod · DimScenario · DimMethod ·      │
   │   DimMapping · DimRule · DimCurrency                      │
   │                    │                                     │
   │   FactValidationCheck · FactRuleRun · View* (derived)     │
   └────────────────────┼─────────────────────────────────────┘
                        ▼
   SQLite (state)  FactException (+FactExceptionEvent) · FactPackIssue ·
                   FactPeriodSnapshot · Master* · MappingProfile(+Version) ·
                   MappingSuggestion · Commentary(+Version) · AIDraft ·
                   FactAIUsage · RuleConfig · AuditLog · VersionHistory
```

### 2.1 Grain register (the authority on "one row = ?")

| Table | Grain (one row = ?) | Uniqueness |
|---|---|---|
| `DimCompany` | One legal entity / reporting unit | `UNIQUE(company_code)` |
| `DimAccount` | One GL account as posted to | `UNIQUE(account_code)` |
| `DimCostCenter` | One cost centre / department node | `UNIQUE(cost_center_code)` |
| `DimVendor` | One supplier as seen in the source | `UNIQUE(vendor_code)` |
| `DimProject` | One project/tag value seen in the source | `UNIQUE(project_code)` |
| `DimPeriod` | One fiscal period of one fiscal year | `UNIQUE(fiscal_year, period_number)` |
| `DimScenario` | One forecast scenario | `UNIQUE(scenario_code)` |
| `DimMethod` | One forecast method | `UNIQUE(method_code)` |
| `DimCurrency` | One currency known to the project (exactly one active in v1) | `UNIQUE(currency_code)` |
| `DimRule` | One exception rule definition | `UNIQUE(rule_id)` |
| `DimMapping` | One source-column-to-canonical-field mapping in one profile version | `UNIQUE(profile_id, version_no, source_column)` |
| `FactActual` | One posted GL transaction **line** | `UNIQUE(import_batch_id, row_fingerprint)` |
| `FactBudget` | One budget line at version × scenario × period × account × dimensions | `UNIQUE(budget_version, scenario_code, period_id, account_id, company_id, cost_center_id, project_id)` |
| `FactForecast` | One forecast line at version × scenario × method × period × account × dimensions | `UNIQUE(forecast_version_id, period_id, account_id, company_id, cost_center_id, project_id)` |
| `FactForecastVersion` | One generated forecast version for one scenario | `UNIQUE(scenario_id, version_no)` |
| `FactImportBatch` | One import run of one file (or one sheet selection of one file) | `UNIQUE(file_checksum, source_type, sheet_name)` for committed batches (enforced by the re-import guard) |
| `FactValidationCheck` | One validation check result within one batch | `UNIQUE(batch_id, check_code)` |
| `FactRuleRun` | One execution of the rule engine | `UNIQUE(run_id)` |
| `QuarantineRow` | One source row that failed row-level validation | `UNIQUE(batch_id, source_row_ref)` |
| `FactException` | One **unique rule + subject** (stable identity) | `UNIQUE(identity_hash)` |
| `FactExceptionEvent` | One event in an exception's history | `UNIQUE(exception_id, event_seq)` |
| `FactPackIssue` | One issued pack version for one period | `UNIQUE(period_id, pack_version)` |
| `FactPeriodSnapshot` | One immutable snapshot (close or issue) | `UNIQUE(period_id, snapshot_type, pack_version)` |
| `MappingProfile` | One saved mapping profile | `UNIQUE(name, source_type)` |
| `MappingProfileVersion` | One version of a profile | `UNIQUE(profile_id, version_no)` |
| `MappingSuggestion` | One AI/rule suggestion for one source column in one batch | `UNIQUE(batch_id, source_column)` |
| `MasterVendorCategory` | One vendor category | `UNIQUE(category_code)` |
| `MasterRecurringCost` | One expected recurring charge | `UNIQUE(name, vendor_id, account_id, cost_center_id, start_period_id)` |
| `MasterApprovalThreshold` | One threshold rule scope | `UNIQUE(scope, company_id, account_id, cost_center_id, effective_from)` |
| `MasterOwnerAssignment` | One owner mapping at a scope | `UNIQUE(scope, company_id, cost_center_id, account_id)` |
| `RuleConfig` | One rule's configuration in one project | `UNIQUE(rule_id)` |
| `Commentary` | One commentary target (a variance line or the period narrative) | `UNIQUE(period_id, scope_type, subject_key)` |
| `CommentaryVersion` | One version of one commentary target | `UNIQUE(commentary_id, version_no)` |
| `AIDraft` | One generated draft | `UNIQUE(draft_id)` |
| `FactAIUsage` | One AI call | `UNIQUE(usage_id)` |
| `AuditLog` | One user action | `UNIQUE(audit_id)` |
| `VersionHistory` | One change to one versioned artefact | `UNIQUE(artefact_type, artefact_id, version_no)` |
| `FactExport` | One generated export artefact (one file version of one pack token) | `UNIQUE(file_name)` |
| `ProjectSetting` | One project-level configuration key | `UNIQUE(key)` |
| `AppSetting` | One machine-level configuration key | `UNIQUE(key)` |
| `SchemaMetadata` | One row per project (single-row table) | `UNIQUE(project_id)` |

## 3. Dimensions (DuckDB)

`Dim*` tables use a **v1 slow-change strategy**: current-row flags with `valid_from` / `valid_to`, no
historical attribute versions except where explicitly stated. Dimension history beyond this is parked
(`27`); the model is designed so SCD-2 can be added later without changing fact grains.

### 3.1 `DimCompany`

| Column | Type | Null | Description / example |
|---|---|---|---|
| `company_id` | `INTEGER` | PK | Surrogate. `1` |
| `company_code` | `VARCHAR(40)` | No | Source entity code. `IN01` |
| `company_name` | `VARCHAR(200)` | No | `Alpha Industries Pvt Ltd` |
| `entity_type` | `VARCHAR(20)` | No | `legal` \| `division` \| `branch` |
| `parent_company_id` | `INTEGER` | Yes | FK to `DimCompany` for grouped reporting; grouping is a **simple sum, no eliminations** (`01` §8) |
| `currency_code` | `CHAR(3)` | No | Must equal the project currency in v1 (`01` §6.3) |
| `is_active` | `BOOLEAN` | No | Default `TRUE` |
| `source_system` | `VARCHAR(40)` | No | `D365` \| `Payroll` \| `Procurement` |
| `valid_from` / `valid_to` | `DATE` | No / Yes | Open-ended = `NULL` |
| `is_current` | `BOOLEAN` | No | |
| `created_at` | `TIMESTAMP` | No | |

### 3.2 `DimAccount`

| Column | Type | Null | Description / example |
|---|---|---|---|
| `account_id` | `INTEGER` | PK | `4200` |
| `account_code` | `VARCHAR(40)` | No | Source GL account. `5200-10` |
| `account_name` | `VARCHAR(200)` | No | `Repairs and maintenance` |
| `account_type` | `VARCHAR(20)` | No | `asset` \| `liability` \| `equity` \| `revenue` \| `expense` \| `memo` |
| `statement_line` | `VARCHAR(120)` | Yes | P&L line for reporting (`01` §6.3: P&L focus). `Operating expenses` |
| `parent_account_id` | `INTEGER` | Yes | FK to `DimAccount` for hierarchy rollups (FR-BVA-009) |
| `hierarchy_level` | `SMALLINT` | No | 0 = root; used for rollup ordering |
| `is_postable` | `BOOLEAN` | No | Postable accounts accept transactions |
| `favourability_direction` | `VARCHAR(20)` | No | Derived from `account_type`: `higher_is_favourable` (revenue), `lower_is_favourable` (expense), `neutral` (asset/liability/equity/memo) — the canonical direction rule is owned by `05` |
| `is_active` | `BOOLEAN` | No | |
| `valid_from` / `valid_to` / `is_current` | `DATE` / `DATE` / `BOOLEAN` | No / Yes / No | |
| `created_at` | `TIMESTAMP` | No | |

### 3.3 `DimCostCenter`

| Column | Type | Null | Description / example |
|---|---|---|---|
| `cost_center_id` | `INTEGER` | PK | |
| `cost_center_code` | `VARCHAR(40)` | No | `CC-100` |
| `cost_center_name` | `VARCHAR(200)` | No | `Plant maintenance` |
| `parent_cost_center_id` | `INTEGER` | Yes | Tree for expand/collapse rollups |
| `hierarchy_level` | `SMALLINT` | No | |
| `department_name` | `VARCHAR(200)` | Yes | Department grouping used by charts |
| `company_id` | `INTEGER` | No | Owning entity |
| `owner_name` | `VARCHAR(120)` | Yes | Default accounting owner (mirrored from `MasterOwnerAssignment` where present) |
| `is_active` | `BOOLEAN` | No | Inactive usage is an exception rule (`06`) |
| `valid_from` / `valid_to` / `is_current` | as above | | |
| `created_at` | `TIMESTAMP` | No | |

### 3.4 `DimVendor`

| Column | Type | Null | Description / example |
|---|---|---|---|
| `vendor_id` | `INTEGER` | PK | |
| `vendor_code` | `VARCHAR(40)` | No | `V-00931` |
| `vendor_name` | `VARCHAR(200)` | No | `Sunrise Facilities LLP` (masked before AI calls, `10`) |
| `category_id` | `INTEGER` | Yes | FK to `MasterVendorCategory` (optional master data) |
| `is_intercompany` | `BOOLEAN` | No | Default `FALSE` |
| `is_active` | `BOOLEAN` | No | |
| `source` | `VARCHAR(20)` | No | `imported` \| `derived_from_transactions` |
| `valid_from` / `valid_to` / `is_current` | as above | | |
| `created_at` | `TIMESTAMP` | No | |

### 3.5 `DimProject`

| Column | Type | Null | Description / example |
|---|---|---|---|
| `project_id` | `INTEGER` | PK | |
| `project_code` | `VARCHAR(40)` | No | `PRJ-2026-014` |
| `project_name` | `VARCHAR(200)` | No | `Line 3 upgrade` |
| `project_type` | `VARCHAR(20)` | No | `client` \| `internal` \| `capex` \| `other` |
| `company_id` | `INTEGER` | Yes | Owning entity where known |
| `is_active` | `BOOLEAN` | No | |
| `created_at` | `TIMESTAMP` | No | |

### 3.6 `DimPeriod` (fiscal calendar — owned by the project settings, `05` §fiscal calendar)

| Column | Type | Null | Description / example |
|---|---|---|---|
| `period_id` | `INTEGER` | PK | Surrogate, ordered |
| `fiscal_year` | `SMALLINT` | No | `2026` |
| `period_number` | `SMALLINT` | No | `9` (September) |
| `period_code` | `VARCHAR(20)` | No | `FY26-P09` (also accepted as a source text format at import) |
| `period_label` | `VARCHAR(40)` | No | `Sep-26` |
| `start_date` | `DATE` | No | `2026-09-01` |
| `end_date` | `DATE` | No | `2026-09-30` |
| `status` | `VARCHAR(10)` | No | `open` \| `closed` (FR-PRJ-005) |
| `has_actuals` | `BOOLEAN` | No | Set by the loader; drives empty states |
| `has_budget` | `BOOLEAN` | No | |
| `is_forecast_eligible` | `BOOLEAN` | No | `FALSE` for closed periods |
| `closed_at` | `TIMESTAMP` | Yes | |
| `created_at` | `TIMESTAMP` | No | |

**Calendar rules:** all period logic derives from this table; no calendar months are hardcoded anywhere
(`01` §11). A non-January year start or a 4-4-5 arrangement changes only the rows here plus the project
setting that generated them.

### 3.7 `DimScenario`, `DimMethod`, `DimCurrency`, `DimRule`

| Table | Key columns | Notes |
|---|---|---|
| `DimScenario` | `scenario_id`, `scenario_code` (`base`\|`best`\|`worst`), `name`, `description`, `is_default` | Three scenarios in v1 (FR-FC-003) |
| `DimMethod` | `method_id`, `method_code` (`remaining_budget`\|`run_rate`\|`avg_3m`\|`manual`), `name`, `requires_history_months`, `description` | Method mathematics owned by `07` |
| `DimCurrency` | `currency_code`, `symbol`, `decimal_places`, `is_project_currency` | Exactly one active row in v1 (§6.3 of `01`) |
| `DimRule` | `rule_id`, `rule_name`, `rule_family`, `severity_default`, `threshold_default` (JSON), `requires_master_data` (JSON), `subject_key_definition`, `is_enabled_default`, `rule_version`, `description` | Registry mirroring the catalog in `06`; logic is code, configuration is data (`RuleConfig`) |

### 3.8 `DimMapping` (versioned, approval-flagged)

| Column | Type | Null | Description / example |
|---|---|---|---|
| `mapping_id` | `INTEGER` | PK | |
| `profile_id` | `INTEGER` | No | FK to `MappingProfile` (SQLite) |
| `version_no` | `INTEGER` | No | |
| `source_system` | `VARCHAR(40)` | No | `D365` |
| `source_column` | `VARCHAR(200)` | No | `Ledger account` |
| `canonical_field` | `VARCHAR(60)` | No | `account_code` (or `__ignored__`) |
| `transform` | `JSON` | Yes | Per-column overrides: `{"date_rule":"dd-mm-yyyy","sign":"parens_negative","scale":1}` |
| `effective_from_period_id` | `INTEGER` | Yes | Mid-year column changes create a new version (FR-IMP-026) |
| `approved_by` | `VARCHAR(120)` | Yes | Human approval flag |
| `approved_at` | `TIMESTAMP` | Yes | |
| `is_active` | `BOOLEAN` | No | |
| `notes` | `VARCHAR(500)` | Yes | |
| `created_at` | `TIMESTAMP` | No | |

## 4. Fact tables (DuckDB)

### 4.1 `FactActual` — one row per posted GL transaction line

| Column | Type | Null | Description / example |
|---|---|---|---|
| `actual_id` | `BIGINT` | PK | Surrogate, assigned by the loader |
| `import_batch_id` | `BIGINT` | No | FK to `FactImportBatch` — **traceability invariant** |
| `row_fingerprint` | `VARCHAR(64)` | No | SHA-256 of canonical business fields (§7) |
| `company_id` | `INTEGER` | No | FK `DimCompany` |
| `account_id` | `INTEGER` | No | FK `DimAccount` |
| `cost_center_id` | `INTEGER` | Yes | FK `DimCostCenter`; null only when the source legitimately omits it |
| `department_id` | `INTEGER` | Yes | FK `DimCostCenter` (department node) where reported separately |
| `project_id` | `INTEGER` | Yes | FK `DimProject` |
| `vendor_id` | `INTEGER` | Yes | FK `DimVendor` |
| `period_id` | `INTEGER` | No | FK `DimPeriod` — assigned from **posting_date** per the documented rule (`05`) |
| `posting_date` | `DATE` | No | Drives period assignment |
| `document_date` | `DATE` | Yes | Used only by the cut-off exception rule (`06`) |
| `voucher_no` | `VARCHAR(60)` | No | `VCH-2026-0912-004` |
| `document_no` | `VARCHAR(60)` | Yes | Source document reference |
| `invoice_no` | `VARCHAR(60)` | Yes | Used by duplicate-invoice and threshold rules |
| `line_no` | `INTEGER` | No | Source line number within the voucher |
| `description` | `VARCHAR(500)` | Yes | Hostile input: sanitised before logs/AI (`10`, `13`) |
| `debit` | `DECIMAL(18,2)` | No | `NOT NULL DEFAULT 0` |
| `credit` | `DECIMAL(18,2)` | No | `NOT NULL DEFAULT 0` |
| `net_amount` | `DECIMAL(18,2)` | No | Generated as `debit − credit` (canonical sign, `05`) |
| `currency_code` | `CHAR(3)` | No | Must equal the project currency; mixed rows are quarantined (`02` E10) |
| `journal_category` | `VARCHAR(20)` | Yes | `manual` \| `auto` \| `reclass` \| `accrual` — optional via profile (`01` §6.3) |
| `source_system` | `VARCHAR(40)` | No | `D365` \| `Payroll` \| `Procurement` |
| `source_file_name` | `VARCHAR(260)` | No | As received, for evidence display |
| `source_row_ref` | `VARCHAR(80)` | No | `Sheet1!A412` or `line 412` — the row-level evidence pointer |
| `is_zero_amount` | `BOOLEAN` | No | Derived; zero-amount rows are kept but excluded from outlier rules (§02 E4) |
| `created_at` | `TIMESTAMP` | No | |

### 4.2 `FactBudget` — one row per budget line

| Column | Type | Null | Description / example |
|---|---|---|---|
| `budget_id` | `BIGINT` | PK | |
| `import_batch_id` | `BIGINT` | No | FK `FactImportBatch` |
| `budget_version` | `VARCHAR(40)` | No | `FY26-Approved` (v1 = one approved budget + version field, `01` §12 A6) |
| `scenario_code` | `VARCHAR(20)` | No | Usually `base` for budget |
| `company_id` / `account_id` | `INTEGER` | No | FKs |
| `cost_center_id` / `department_id` / `project_id` | `INTEGER` | Yes | Optional dimensions |
| `period_id` | `INTEGER` | No | FK `DimPeriod` |
| `amount` | `DECIMAL(18,2)` | No | Signed per the canonical convention (`05`) |
| `currency_code` | `CHAR(3)` | No | |
| `is_derived_spread` | `BOOLEAN` | No | `TRUE` when the loader spread an annual figure across periods under a documented rule |
| `source_row_ref` | `VARCHAR(80)` | No | |
| `created_at` | `TIMESTAMP` | No | |

### 4.3 `FactForecast` — one row per forecast line

| Column | Type | Null | Description / example |
|---|---|---|---|
| `forecast_id` | `BIGINT` | PK | |
| `forecast_version_id` | `BIGINT` | No | FK `FactForecastVersion` (SQLite) — a locked version is referenced by issued packs |
| `scenario_id` | `INTEGER` | No | FK `DimScenario` |
| `method_id` | `INTEGER` | No | FK `DimMethod` (the method actually used) |
| `company_id` / `account_id` | `INTEGER` | No | FKs |
| `cost_center_id` / `project_id` | `INTEGER` | Yes | |
| `period_id` | `INTEGER` | No | Only forecast-eligible (open) periods |
| `amount` | `DECIMAL(18,2)` | No | |
| `is_manual_override` | `BOOLEAN` | No | |
| `override_reason` | `VARCHAR(500)` | Yes | **Required** when `is_manual_override = TRUE` (FR-FC-006) |
| `driver_ref` | `JSON` | Yes | Which actuals fed the method, e.g. `{"months":["FY26-P07","FY26-P08","FY26-P09"],"avg_basis":"net_amount"}` |
| `generated_at` | `TIMESTAMP` | No | Provenance (FR-FC-004) |
| `generated_by` | `VARCHAR(120)` | No | Session user |
| `created_at` | `TIMESTAMP` | No | |

### 4.4 `FactForecastVersion` (DuckDB) / `ForecastVersion` (SQLite metadata)

| Column | Type | Null | Description |
|---|---|---|---|
| `forecast_version_id` | `BIGINT` | PK | |
| `period_generated_for` | `INTEGER` | No | FK `DimPeriod` (the period whose close triggered the forecast) |
| `scenario_id` | `INTEGER` | No | |
| `version_no` | `INTEGER` | No | Monotonic per scenario |
| `status` | `VARCHAR(20)` | No | `draft` \| `locked` \| `superseded` |
| `locked_at` / `locked_by` | `TIMESTAMP` / `VARCHAR(120)` | Yes | A locked version is read-only (FR-FC-009) |
| `generated_at` / `generated_by` | `TIMESTAMP` / `VARCHAR(120)` | No | |
| `notes` | `VARCHAR(500)` | Yes | |

### 4.5 `QuarantineRow` — row-level failures (never silently dropped)

| Column | Type | Null | Description |
|---|---|---|---|
| `quarantine_id` | `BIGINT` | PK | |
| `import_batch_id` | `BIGINT` | No | FK |
| `target_table` | `VARCHAR(40)` | No | `FactActual` \| `FactBudget` \| `FactForecast` \| master data |
| `source_row_ref` | `VARCHAR(80)` | No | Sheet + row, or CSV line number |
| `reason_code` | `VARCHAR(60)` | No | Stable slug, e.g. `import.dateOutsideFiscalYear` |
| `reason_detail` | `VARCHAR(1000)` | No | Human explanation naming column and value |
| `raw_values` | `JSON` | No | The original row values (hostile input; sanitised on display) |
| `resolution` | `VARCHAR(20)` | No | `pending` \| `imported` \| `discarded` (with a recorded decision) |
| `resolved_at` / `resolved_by` | `TIMESTAMP` / `VARCHAR(120)` | Yes | |
| `created_at` | `TIMESTAMP` | No | |

### 4.6 `FactValidationCheck` — one row per check per batch

| Column | Type | Null | Description |
|---|---|---|---|
| `check_id` | `BIGINT` | PK | |
| `import_batch_id` | `BIGINT` | No | FK |
| `check_code` | `VARCHAR(20)` | No | `IMP-nnn` from `04` |
| `check_name` | `VARCHAR(200)` | No | |
| `status` | `VARCHAR(10)` | No | `pass` \| `fail` \| `warn` \| `skipped` |
| `skip_reason` | `VARCHAR(300)` | Yes | Required when `skipped` (FR-IMP-021) |
| `severity` | `VARCHAR(10)` | No | `high` \| `medium` \| `low` |
| `offending_count` | `INTEGER` | No | `0` when passing |
| `sample_rows` | `JSON` | Yes | First N offenders (default 20) with `source_row_ref` |
| `detail` | `VARCHAR(1000)` | Yes | Totals/variance text |
| `weight` | `DECIMAL(6,4)` | No | Used by the data-quality score (`05`) |
| `duration_ms` | `INTEGER` | No | |
| `created_at` | `TIMESTAMP` | No | |

### 4.7 `FactRuleRun` — one row per engine execution

| Column | Type | Null | Description |
|---|---|---|---|
| `run_id` | `BIGINT` | PK | |
| `period_id` | `INTEGER` | Yes | Null = all periods |
| `started_at` / `finished_at` | `TIMESTAMP` | No | |
| `rules_evaluated` | `INTEGER` | No | |
| `rules_skipped` | `INTEGER` | No | With reasons in `ViewRuleRunSkip` |
| `exceptions_raised` | `INTEGER` | No | New identities only |
| `exceptions_flagged_again` | `INTEGER` | No | Previously closed, re-flagged (§02 FR-EXC-005) |
| `exceptions_unchanged` | `INTEGER` | No | |
| `duration_ms` | `INTEGER` | No | Measured against `NFR-009` |
| `triggered_by` | `VARCHAR(120)` | No | Session user or `system` |
| `engine_version` | `VARCHAR(20)` | No | |
| `data_scope` | `JSON` | No | Batch IDs and period range covered |
| `created_at` | `TIMESTAMP` | No | |

## 5. Workflow state tables (SQLite)

### 5.1 `FactImportBatch` (absorbs the seed's "FactImportAudit" — supersession noted in §9.3)

| Column | Type | Null | Description |
|---|---|---|---|
| `batch_id` | `BIGINT` | PK | |
| `source_type` | `VARCHAR(40)` | No | `actuals_d365` \| `actuals_payroll` \| `actuals_procurement` \| `budget` \| `forecast_input` \| `vendor_master` \| `recurring_costs` \| `approval_thresholds` |
| `source_system` | `VARCHAR(40)` | No | |
| `file_name` | `VARCHAR(260)` | No | Original name as received |
| `archive_path` | `VARCHAR(500)` | No | Immutable archive location (FR-IMP-025) |
| `file_checksum` | `VARCHAR(64)` | No | SHA-256 |
| `file_size_bytes` | `BIGINT` | No | |
| `sheet_name` | `VARCHAR(120)` | Yes | For multi-sheet workbooks |
| `profile_id` / `profile_version` | `INTEGER` | Yes | Mapping profile applied |
| `template_version_seen` | `VARCHAR(20)` | Yes | Outdated-template warning (FR-IMP-007) |
| `row_count_source` | `INTEGER` | No | |
| `row_count_loaded` | `INTEGER` | No | |
| `row_count_quarantined` | `INTEGER` | No | |
| `row_count_rejected` | `INTEGER` | No | File-level rejection = all rows here |
| `balance_result` | `VARCHAR(10)` | No | `pass` \| `fail` |
| `balance_variance` | `DECIMAL(18,2)` | No | `0.00` when balanced |
| `control_total_variance` | `DECIMAL(18,2)` | Yes | Null when no control-totals block was supplied |
| `data_quality_score` | `SMALLINT` | Yes | 0–100 (`05` formula) |
| `status` | `VARCHAR(12)` | No | `staged` \| `committed` \| `voided` \| `rejected` \| `cancelled` |
| `period_id` | `INTEGER` | Yes | Primary period loaded |
| `company_id` | `INTEGER` | Yes | When the file is entity-specific |
| `imported_by` | `VARCHAR(120)` | No | Session user |
| `started_at` / `committed_at` | `TIMESTAMP` | No / Yes | |
| `voided_at` / `void_reason` | `TIMESTAMP` / `VARCHAR(500)` | Yes | Void requires a reason (FR-IMP-024) |
| `app_version` / `schema_version` | `VARCHAR(20)` / `INTEGER` | No | Records the build that loaded it |
| `created_at` | `TIMESTAMP` | No | |

### 5.2 `FactException` (the exception register authority)

| Column | Type | Null | Description |
|---|---|---|---|
| `exception_id` | `BIGINT` | PK | |
| `identity_hash` | `VARCHAR(64)` | No | `SHA-256(rule_id + '|' + subject_key)` — UNIQUE |
| `rule_id` | `VARCHAR(20)` | No | FK `DimRule` |
| `rule_version` | `VARCHAR(20)` | No | The rule version that raised it |
| `subject_key` | `VARCHAR(200)` | No | Rule-specific canonical subject (defined in `06`) |
| `subject_display` | `VARCHAR(300)` | No | Human-readable subject (denormalised for reports) |
| `period_id` | `INTEGER` | No | |
| `company_id` / `account_id` | `INTEGER` | Yes | Denormalised subject dimensions |
| `cost_center_id` / `vendor_id` / `project_id` | `INTEGER` | Yes | |
| `amount_at_risk` | `DECIMAL(18,2)` | No | Sum of the subject rows' absolute amounts where applicable |
| `severity` | `VARCHAR(10)` | No | `high` \| `medium` \| `low` |
| `status` | `VARCHAR(20)` | No | `open` \| `in_review` \| `explained` \| `corrected` \| `closed` \| `reopened` \| `not_applicable` |
| `owner_name` | `VARCHAR(120)` | Yes | Null = "Unassigned" (a filter, not a loss) |
| `first_seen_period_id` | `INTEGER` | No | Original period (never overwritten) |
| `raised_at` | `TIMESTAMP` | No | First raise |
| `last_seen_at` | `TIMESTAMP` | No | Last run that matched it |
| `flagged_again` | `BOOLEAN` | No | Set when a closed exception matches again |
| `flagged_again_at` | `TIMESTAMP` | Yes | |
| `closed_at` | `TIMESTAMP` | Yes | |
| `effective_threshold` | `VARCHAR(120)` | No | The threshold actually used when raised (e.g. `materiality 2.0% or ₹500,000`) |
| `evidence_refs` | `JSON` | Yes | Subject row references (voucher + source_row_ref) for the evidence bundle |
| `last_run_id` | `BIGINT` | No | FK `FactRuleRun` |
| `notes_count` | `INTEGER` | No | Denormalised for the register |
| `last_note_at` | `TIMESTAMP` | Yes | |
| `created_at` / `updated_at` / `updated_by` | `TIMESTAMP` / `TIMESTAMP` / `VARCHAR(120)` | No / No / Yes | |

### 5.3 `FactExceptionEvent` (append-only history)

| Column | Type | Null | Description |
|---|---|---|---|
| `event_id` | `BIGINT` | PK | |
| `exception_id` | `BIGINT` | No | FK |
| `event_seq` | `INTEGER` | No | Monotonic per exception |
| `event_type` | `VARCHAR(30)` | No | `raised` \| `flagged_again` \| `status_changed` \| `owner_changed` \| `note_added` \| `threshold_changed` \| `reopened` \| `evidence_exported` |
| `from_value` / `to_value` | `VARCHAR(500)` | Yes | |
| `note_text` | `VARCHAR(2000)` | Yes | |
| `actor` | `VARCHAR(120)` | No | Session user or `system` |
| `occurred_at` | `TIMESTAMP` | No | |

### 5.4 `FactPackIssue` and `FactPeriodSnapshot`

| `FactPackIssue` column | Type | Null | Description |
|---|---|---|---|
| `issue_id` | `BIGINT` | PK | |
| `period_id` | `INTEGER` | No | |
| `pack_version` | `INTEGER` | No | Monotonic per period |
| `pack_type` | `VARCHAR(10)` | No | `excel` \| `ppt` \| `both` |
| `issued_at` / `issued_by` | `TIMESTAMP` / `VARCHAR(120)` | No | |
| `recipients` | `JSON` | No | Typed list of recipient names/roles |
| `snapshot_id` | `BIGINT` | No | FK `FactPeriodSnapshot` |
| `file_names` | `JSON` | No | The exact files issued |
| `status` | `VARCHAR(12)` | No | `issued` \| `superseded` |
| `notes` | `VARCHAR(500)` | Yes | Re-issue reason |

| `FactPeriodSnapshot` column | Type | Null | Description |
|---|---|---|---|
| `snapshot_id` | `BIGINT` | PK | |
| `period_id` | `INTEGER` | No | |
| `snapshot_type` | `VARCHAR(10)` | No | `close` \| `issue` |
| `pack_version` | `INTEGER` | Yes | Null for a close-type snapshot |
| `created_at` / `created_by` | `TIMESTAMP` / `VARCHAR(120)` | No | |
| `row_counts` | `JSON` | No | Rows per fact table at snapshot time |
| `totals_hash` | `VARCHAR(64)` | No | SHA-256 over the period's aggregated totals — proves immutability |
| `storage_path` | `VARCHAR(500)` | No | Immutable snapshot payload |
| `immutable` | `BOOLEAN` | No | Always `TRUE`; the app refuses writes |

### 5.5 Mapping tables

| `MappingProfile` column | Type | Null | Description |
|---|---|---|---|
| `profile_id` | `INTEGER` | PK | |
| `name` | `VARCHAR(120)` | No | `D365 GL export (Sep-26 shape)` |
| `source_type` | `VARCHAR(40)` | No | Matches `FactImportBatch.source_type` |
| `header_signature` | `VARCHAR(64)` | No | SHA-256 over the sorted, normalised header set |
| `sheet_selector` | `VARCHAR(120)` | Yes | Sheet name or `first` |
| `header_row` | `INTEGER` | No | 1-based row index of the true header |
| `delimiter` / `encoding` | `VARCHAR(10)` / `VARCHAR(20)` | Yes | CSV only |
| `date_rule` / `number_rule` | `VARCHAR(40)` | Yes | Documented per-profile rules |
| `is_builtin` | `BOOLEAN` | No | Shipped profiles are read-only (clone to edit) |
| `created_at` | `TIMESTAMP` | No | |

| `MappingProfileVersion` column | Type | Null | Description |
|---|---|---|---|
| `version_id` | `INTEGER` | PK | |
| `profile_id` / `version_no` | `INTEGER` / `INTEGER` | No | |
| `definition` | `JSON` | No | Full profile snapshot (immune to later edits) |
| `effective_from_period_id` | `INTEGER` | Yes | Mid-year source changes (FR-IMP-026) |
| `change_note` | `VARCHAR(500)` | No | Why the version changed |
| `is_current` | `BOOLEAN` | No | Exactly one per profile |
| `created_at` / `created_by` | `TIMESTAMP` / `VARCHAR(120)` | No | |

| `MappingSuggestion` column | Type | Null | Description |
|---|---|---|---|
| `suggestion_id` | `INTEGER` | PK | |
| `import_batch_id` | `BIGINT` | No | |
| `source_column` | `VARCHAR(200)` | No | |
| `suggested_field` | `VARCHAR(60)` | No | |
| `confidence` | `DECIMAL(5,2)` | No | 0–100 |
| `evidence` | `JSON` | Yes | Previously accepted rows supporting the suggestion |
| `source` | `VARCHAR(10)` | No | `ai` \| `rule` |
| `ai_draft_id` | `BIGINT` | Yes | FK `AIDraft` when AI-generated |
| `state` | `VARCHAR(12)` | No | `suggested` \| `accepted` \| `edited` \| `rejected` |
| `decided_at` / `decided_by` | `TIMESTAMP` / `VARCHAR(120)` | Yes | |
| `created_at` | `TIMESTAMP` | No | |

### 5.6 Master data tables (versioned, revertable — FR-SET-003)

| Table | Columns | Notes |
|---|---|---|
| `MasterVendorCategory` | `category_id` PK, `category_code`, `category_name`, `is_active`, audit columns | Optional; rules degrade when empty (§02 FR-EXC-014) |
| `MasterRecurringCost` | `recurring_id` PK, `name`, `vendor_id` NULL, `account_id`, `cost_center_id` NULL, `expected_amount` `DECIMAL(18,2)`, `frequency` (`monthly`\|`quarterly`\|`annual`), `start_period_id`, `end_period_id` NULL, `tolerance_pct` `DECIMAL(9,6)`, `is_active`, audit columns | Feeds the "missing recurring cost" rule |
| `MasterApprovalThreshold` | `threshold_id` PK, `scope` (`company`\|`account`\|`cost_center`), `company_id` NULL, `account_id` NULL, `cost_center_id` NULL, `amount_threshold` `DECIMAL(18,2)`, `requires_dual_approval` BOOLEAN, `effective_from` DATE, `is_active`, audit columns | Feeds the threshold-crossing rule |
| `MasterOwnerAssignment` | `assignment_id` PK, `scope` (`company`\|`cost_center`\|`account`), `company_id` NULL, `cost_center_id` NULL, `account_id` NULL, `owner_name`, `owner_email` NULL, `priority` INTEGER, `is_active`, audit columns | Drives owner auto-assignment and the owner-wise export |

### 5.7 Configuration, commentary, AI and audit tables

| Table | Key columns | Purpose |
|---|---|---|
| `RuleConfig` | `config_id` PK, `rule_id`, `is_enabled`, `thresholds` JSON, `version_no`, `updated_at`, `updated_by` | Per-project rule enable/thresholds (FR-EXC-012) |
| `Commentary` | `commentary_id` PK, `period_id`, `scope_type` (`line`\|`executive`), `subject_key`, `current_version_no`, `locked_by_issue_id` NULL, `created_at` | One target per variance line or the period narrative (FR-XC-001) |
| `CommentaryVersion` | `version_id` PK, `commentary_id`, `version_no`, `text` `VARCHAR(4000)`, `source` (`user`\|`ai`\|`rule_based`), `ai_draft_id` NULL, `author`, `created_at` | Immutable history; locked when the pack is issued (FR-XC-002) |
| `AIDraft` | `draft_id` PK, `feature_code`, `prompt_version`, `model`, `input_scope` JSON, `output_json` JSON, `evidence_refs` JSON, `confidence`, `number_mismatch_flag` BOOLEAN, `status` (`draft`\|`approved`\|`rejected`\|`superseded`), `approved_at`, `approved_by`, `created_at` | Provenance and approval (FR-AI-011) |
| `FactAIUsage` | `usage_id` PK, `occurred_at`, `feature_code`, `model`, `prompt_version`, `input_row_count`, `tokens_in`, `tokens_out`, `estimated_cost` `DECIMAL(18,6)`, `latency_ms`, `outcome` (`ok`\|`schema_error`\|`timeout`\|`cap_exceeded`\|`refused`) | Usage log and caps (FR-AI-009) |
| `AuditLog` | `audit_id` PK, `occurred_at`, `actor`, `action_code`, `object_type`, `object_id`, `before` JSON, `after` JSON, `session_id`, `app_version` | Local audit trail; **no amounts or vendor names in `action_code`/text fields** (`13`) |
| `VersionHistory` | `history_id` PK, `artefact_type`, `artefact_id`, `version_no`, `changed_at`, `changed_by`, `old_value` JSON, `new_value` JSON, `change_note` | Generic version/revert support (FR-SET-011) |
| `FactExport` | `export_id` PK, `generated_at`, `generated_by`, `pack_token` (`MonthEnd`\|`Register`\|`OwnerDist`\|`Evidence`\|`Drill`\|`Matrix`\|…), `file_version` INTEGER, `file_name`, `file_format` (`xlsx`\|`csv`\|`txt`\|`zip`), `filter_json` JSON, `filter_human`, `period_id` NULL, `pack_issue_id` NULL, `batch_ids` JSON, `content_hash` `VARCHAR(80)`, `row_counts` JSON, `house_style_version` NULL, `row_limit_applied` INTEGER NULL, `refresh_of_export_id` NULL, `outcome` (`written`\|`cancelled`\|`failed`) | **Export register**: the exact context needed to refresh a pack (FR-XL-003), the source of `vN` file numbering and collision decisions (`11` §3.4/§3.9), and the audit link for every generated artefact. SQLite (workflow state, not rebuildable) |
| `ProjectSetting` | `key` PK, `value` JSON, `updated_at`, `updated_by` | Project-level configuration (fiscal calendar, currency, locale, branding, storage) — portable, contains **no secrets** (`09` §config layering) |
| `AppSetting` | `key` PK, `value` (encrypted when sensitive), `updated_at` | **Machine-level** settings: AI provider/model, key (DPAPI-protected, `13`), theme, data directory, telemetry = off |
| `SchemaMetadata` | `project_id` PK, `app_version`, `schema_version`, `created_at`, `migrated_at`, `migration_log` JSON, `timezone`, `project_type` (`normal`\|`sample`) | Single-row table; the anchor for migrations (`24`) and sample-data integrity (`02` §16 H) |

## 6. Business keys and duplicate detection (documented dedup keys)

| Purpose | Key |
|---|---|
| Actuals — exact duplicate (same batch) | `row_fingerprint` = SHA-256(`company_code`, `voucher_no`, `line_no`, `posting_date`, `account_code`, `debit`, `credit`, `cost_center_code`) |
| Actuals — cross-batch duplicate candidate | (`company_code`, `voucher_no`, `line_no`) **and** (`vendor_code`, `invoice_no`, `posting_date`, `amount`) — both reported, neither auto-deleted |
| Budget/forecast line duplicate | (`budget_version`\|`forecast_version_id`, `period_id`, `account_id`, `company_id`, `cost_center_id`, `project_id`) |
| Re-import guard (file level) | `file_checksum` |
| Exception identity | `rule_id + subject_key` |
| Commentary target | (`period_id`, `scope_type`, `subject_key`) |

**Rule:** duplicate candidates are always *reported with counts and samples*, never silently dropped and
never silently merged (P13, FR-IMP-017/018).

## 7. Integrity rules and constraints

| # | Rule | Enforced by |
|---|---|---|
| I1 | Every fact row references an existing `import_batch_id` (or `forecast_version_id` for forecasts) | FK + `NOT NULL` + loader transaction |
| I2 | A batch cannot be committed unless debit = credit within tolerance and row counts reconcile (`source = loaded + quarantined + rejected`) | Loader precondition + validation check `IMP-*` |
| I3 | Money columns are `DECIMAL(18,2)`; no float types anywhere in money paths | Schema test in `scripts/check` (fails the build) |
| I4 | `FactActual.period_id` is derived from `posting_date` per the documented rule; a mismatch with the source fiscal period column is reported, not silently reconciled | Validation check + `05` rule |
| I5 | A closed period's facts are immutable: void/re-import require an audited reopen (FR-PRJ-005) | Loader guard + audit event |
| I6 | Issued packs and close snapshots are immutable; their `totals_hash` never changes | Snapshot writer refuses updates; test asserts |
| I7 | Exception identity is unique; re-runs update, never duplicate | `UNIQUE(identity_hash)` + upsert semantics |
| I8 | Exception workflow state is never overwritten by a rule run | Update statements restricted to raise/flag fields |
| I9 | Mapping profiles are immutable per version; edits create a new version | Insert-only version table |
| I10 | Master data and thresholds are versioned; every change records old→new | `VersionHistory` + triggers in the service layer |
| I11 | Forecast facts can never write to `FactActual` | Separate tables + write-path test |
| I12 | Every dimension referenced by a fact exists (no orphan dimensions); unmapped values are quarantined at import | FK + `IMP-*` checks |
| I13 | Raw archives are read-only after write | File permission + checksum re-verification on open |
| I14 | `ProjectSetting` and backups contain **no secrets**; secrets live only in `AppSetting` | Backup writer test |
| I15 | Reference tables (`DimRule`, `DimMethod`, `DimScenario`) are seeded by the app and versioned with it | Migration + seed script |

## 8. Example rows

**`FactActual` (two rows of the same voucher, showing the traceability fields):**

| actual_id | import_batch_id | company_id | account_id | cost_center_id | period_id | posting_date | voucher_no | line_no | description | debit | credit | net_amount | source_system | source_row_ref |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1048231 | 37 | 1 | 5200 | 12 | 69 | 2026-09-14 | VCH-2026-0912-004 | 1 | `Repairs - plant` | 45000.00 | 0.00 | 45000.00 | D365 | `Sheet1!A412` |
| 1048232 | 37 | 1 | 2100 | 12 | 69 | 2026-09-14 | VCH-2026-0912-004 | 2 | `Repairs - plant (credit)` | 0.00 | 45000.00 | -45000.00 | D365 | `Sheet1!A413` |

**`FactBudget`:**

| budget_id | import_batch_id | budget_version | scenario_code | company_id | account_id | cost_center_id | period_id | amount |
|---|---|---|---|---|---|---|---|---|
| 58120 | 41 | `FY26-Approved` | `base` | 1 | 5200 | 12 | 69 | 38000.00 |

**`FactException`:**

| exception_id | identity_hash (prefix) | rule_id | subject_key | period_id | amount_at_risk | severity | status | owner_name | first_seen_period_id | flagged_again | effective_threshold |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 9021 | `9f2c…` | `EXC-004` | `company=1|vendor=V-00931|invoice=INV-88213|amount=45000.00` | 69 | 45000.00 | high | open | `Rahul` | 69 | FALSE | `materiality 2.0% or ₹500,000` |

**`FactImportBatch`:**

| batch_id | source_type | file_name | file_checksum (prefix) | row_count_source | row_count_loaded | row_count_quarantined | balance_result | data_quality_score | status | period_id |
|---|---|---|---|---|---|---|---|---|---|---|
| 37 | `actuals_d365` | `GL_Sep26.xlsx` | `a41d…` | 184,502 | 184,494 | 8 | pass | 95 | committed | 69 |

*The score in this row is the worked example `F12` of `05_CALCULATION_SPEC.md`: one failed High-severity
check (weight 10) plus one Low-severity warning (weight 0.5 × 2) over a weight total of 238 gives
`100 × (1 − 11/238) = 95.378…` → **95**. Any change to the score formula changes this example too.*

## 9. Notes, supersessions and storage

### 9.1 Storage layout inside a project folder

```
<project>/
  analytics.duckdb          analytic model (§2 store split)
  state.sqlite              workflow state
  archives/                 immutable raw files (read-only), named <yyyymmdd-HHMM>_<source_type>_<checksum8>.<ext>
  snapshots/                immutable close/issue snapshots
  exports/                  generated packs (subject to the collision policy, `11`)
  backup/                   user-requested project zips
  logs/                     local logs (rotation per `NFR-011`)
```

### 9.2 Volume expectations (basis for the storage-growth maths in `09`)

| Scale | Assumption | Resulting size (order of magnitude) |
|---|---|---|
| Typical month | ~180k actual rows, ~12k budget rows | ~35–60 MB/month of DuckDB growth with indexes |
| Peak file | 250k rows / ~100 MB source | Import must stay inside `NFR-002` |
| 3-year projection | 36 months | Documented in `09`; low-storage warning threshold configurable (FR-PRJ-011) |

### 9.3 Supersessions from the seed model (explicit, for the audit trail)

| Seed element | Resolution |
|---|---|
| `FactImportAudit` (file, checksum, counts, timestamp, balance result) | **Absorbed into `FactImportBatch`** (§5.1) plus per-check detail in `FactValidationCheck` (§4.6) — one authority, no duplicate table |
| `FactException` in the analytic model | Lives in **SQLite** (workflow authority) with a read-only DuckDB projection (`ViewException`) for reporting joins |
| `DimMapping` "source→canonical, versioned, approval-flagged" | Split into `MappingProfile` + `MappingProfileVersion` (SQLite, immutable versions) with `DimMapping` (DuckDB) holding the flattened active mapping for join performance |
| Master data (Addon 1 §C.2) | Four `Master*` tables (§5.6), all versioned |

## 10. Schema versioning and migration

| Rule | Detail |
|---|---|
| Version storage | `SchemaMetadata.schema_version` (integer), bumped only by a migration (`24`) |
| Change process | `03` updated **first** → migration script → version bump → backup prompt → tested on a real prior-version project (Addon 1 §M.4) |
| Ad-hoc changes | `ALTER` during feature work is forbidden; no silent schema drift |
| Compatibility | Older app opening a newer project → refuse with guidance; newer app opening an older project → backup prompt, migrate, record in `migration_log` |
| Rollback | Backup retained until the migration is confirmed successful; the rollback stance is documented in `24` |
| Seed data | `DimRule`, `DimMethod`, `DimScenario`, `DimCurrency` are seeded and versioned with the app |

## 11. Deferred model decisions (parked with triggers)

| Item | Status |
|---|---|
| SCD-2 history for dimensions | Parked (`27`); the current `valid_from`/`valid_to`/`is_current` scheme supports later upgrade without changing fact grains |
| Multi-currency FX rate table | Parked; single currency per project in v1 (`01` §6.3) |
| Headcount dimension/measures | Parked (`BL-016`); no columns reserved |
| One-off tagging columns | Parked (`BL-024`); a future `FactActual.is_one_off` + tagging table is the documented promotion path |
| Additional source systems | New `source_type` values are data, not schema changes |


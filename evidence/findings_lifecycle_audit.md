# ENG-03 Finding-Lifecycle Audit and Gap-Fill Report

## 1. Finding Lifecycle Trace (Raise to Sign-Off)

```
[ Exception Evaluator ] ──(raise)──> FactException (status='open', owner auto-assigned)
                                            │
                                            ▼
[ Accounting Owner / Analyst ] ──(update status/owner/note)──> UPDATE FactException
                                            │                 INSERT ExceptionNote
                                            │                 INSERT FactExceptionEvent
                                            ▼
[ Audit / Deck Export ] ◄──(read)── ExceptionDetailView (includes events + notes)
```

### Phase 1: Raise & Auto-Assignment
1. **Rule Evaluation**: `ExceptionsRepository.run_rules(period_code, as_of_date)` runs all catalog evaluators (`EXC-001`..`EXC-024`).
2. **Deduplication & Persistence**: Rule findings are deduplicated by `identity_hash` (`rule_id + subject_key`).
3. **Auto-Assignment**: 6-step resolver assigns initial `owner_name` and `owner_role` based on cost center/department ownership or rule defaults (`Unassigned`). Status defaults to `'open'`.

### Phase 2: Inspection & Detail Retrieval
1. **List Findings**: `GET /api/v1/exceptions` filters by period, severity, status (`open`, `under_review`, `closed`, `not_applicable`), owner, rule ID, aging bucket, or search query `q`.
2. **Detail & History**: `GET /api/v1/exceptions/{exception_id}` returns:
   - Base finding record (`FactException`)
   - Materialized sample rows (`sampleRows`)
   - Linked evidence references (`evidenceRefs`)
   - Append-only notes history (`ExceptionNote`)
   - Audit trail of all state changes (`FactExceptionEvent`)

### Phase 3: Update & Collaboration
1. **Single Update**: `PATCH /api/v1/exceptions/{exception_id}` accepts `status`, `owner`, and `note`:
   - Updates `status` and `updated_at` on `FactException`
   - Records `status_changed` event in `FactExceptionEvent`
   - Updates `owner_name` on `FactException`
   - Records `owner_changed` event in `FactExceptionEvent`
   - Inserts append-only record into `ExceptionNote` and `note_added` event in `FactExceptionEvent`
2. **Bulk Operations**: `POST /api/v1/exceptions/bulk` updates multiple findings atomically with per-item 1:1 audit event logging.

### Phase 4: Sign-Off & Export
1. **Owner Distribution Report**: `GET /api/v1/exceptions/export/owner` produces CSV export and Teams/email summary per owner.
2. **Excel Board Pack**: `export_excel_pack` writes Sheet 5 (`Exception Register`) exporting active findings with severity, owner, amount at risk, and rule description.

## 2. Store Persistence Audit

| Table | Primary Key | Key Columns | Purpose |
|---|---|---|---|
| `FactException` | `exception_id` | `identity_hash`, `rule_id`, `rule_name`, `severity`, `status`, `owner_role`, `owner_name`, `period_code`, `amount_at_risk`, `subject_key`, `created_at`, `updated_at` | Master exception finding record |
| `FactExceptionEvent` | `event_id` | `exception_id`, `event_type` (`status_changed`, `owner_changed`, `note_added`), `from_value`, `to_value`, `note_text`, `actor`, `occurred_at` | Immutable append-only audit trail |
| `ExceptionNote` | `note_id` | `exception_id`, `author`, `note_text`, `created_at` | Collaborative notes history |

## 3. Workflow & UX-12 Compatibility Verification
- **Status Enum**: `open`, `under_review`, `closed`, `not_applicable` supported in DB DDL and API validators.
- **Owner Resolution**: Full 6-step owner resolver present in `app/engine/exceptions/owner_resolver.py`.
- **Audit Logging**: 100% of state changes (status, owner, notes) log immutable events with timestamps and actors.
- **Migration Safety**: SQLite tables use `CREATE TABLE IF NOT EXISTS` with standard DDL migrations.

## 4. Test Verification Transcript
- `pytest tests/integration/test_api.py -k exceptions`: PASSED (1 passed in 3.06s)
- `pytest tests/integration/test_cli_exceptions.py`: PASSED (4 passed)

-- SQLite Workflow State DDL per 03_DATA_DICTIONARY.md

CREATE TABLE IF NOT EXISTS SchemaMetadata (
    project_id TEXT PRIMARY KEY,
    app_version TEXT NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS FactImportBatch (
    batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_checksum TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    sheet_name TEXT NOT NULL,
    profile_id INTEGER NOT NULL DEFAULT 1,
    profile_version INTEGER NOT NULL DEFAULT 1,
    total_source_rows INTEGER NOT NULL,
    loaded_count INTEGER NOT NULL,
    quarantined_count INTEGER NOT NULL,
    rejected_count INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'committed', -- staging, committed, voided, rejected, cancelled
    is_balanced INTEGER NOT NULL DEFAULT 1,
    total_debit TEXT NOT NULL DEFAULT '0.00',
    total_credit TEXT NOT NULL DEFAULT '0.00',
    net_imbalance TEXT NOT NULL DEFAULT '0.00',
    balance_tolerance TEXT NOT NULL DEFAULT '0.00',
    data_quality_score REAL NOT NULL DEFAULT 100.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS FactValidationCheck (
    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_batch_id INTEGER NOT NULL,
    check_code TEXT NOT NULL,
    check_name TEXT NOT NULL,
    status TEXT NOT NULL, -- pass, fail, warn, skipped
    severity TEXT NOT NULL, -- high, medium, low
    offending_count INTEGER NOT NULL DEFAULT 0,
    skip_reason TEXT,
    detail TEXT,
    sample_rows TEXT, -- JSON array
    weight REAL NOT NULL DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(import_batch_id) REFERENCES FactImportBatch(batch_id)
);

CREATE TABLE IF NOT EXISTS QuarantineRow (
    quarantine_id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_batch_id INTEGER NOT NULL,
    target_table TEXT NOT NULL,
    source_row_ref TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    reason_detail TEXT NOT NULL,
    raw_values TEXT NOT NULL, -- JSON
    resolution TEXT NOT NULL DEFAULT 'pending', -- pending, imported, discarded
    resolved_at DATETIME,
    resolved_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(import_batch_id) REFERENCES FactImportBatch(batch_id)
);

CREATE TABLE IF NOT EXISTS FactException (
    exception_id INTEGER PRIMARY KEY AUTOINCREMENT,
    identity_hash TEXT NOT NULL UNIQUE,
    rule_id TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    severity TEXT NOT NULL, -- High, Medium, Low
    status TEXT NOT NULL DEFAULT 'open', -- open, in_review, explained, corrected, closed, reopened, not_applicable
    owner_role TEXT NOT NULL DEFAULT 'senior_accountant',
    owner_name TEXT,
    period_code TEXT,
    period_id INTEGER,
    subject_key TEXT,
    subject_display TEXT,
    subject_entity TEXT,
    subject_account TEXT,
    subject_amount TEXT,
    amount_at_risk TEXT DEFAULT '0.00',
    effective_threshold TEXT,
    evidence_count INTEGER NOT NULL DEFAULT 1,
    evidence_refs TEXT, -- JSON
    sample_rows TEXT, -- JSON
    first_seen_date TEXT,
    last_seen_date TEXT,
    flagged_again INTEGER NOT NULL DEFAULT 0,
    correlation_id TEXT,
    claim_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS FactExceptionEvent (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exception_id INTEGER NOT NULL,
    event_type TEXT NOT NULL, -- raised, flagged_again, status_changed, owner_changed, note_added, threshold_changed, reopened, evidence_exported
    from_value TEXT,
    to_value TEXT,
    note_text TEXT,
    actor TEXT NOT NULL DEFAULT 'session_user',
    occurred_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(exception_id) REFERENCES FactException(exception_id)
);

CREATE TABLE IF NOT EXISTS ExceptionNote (
    note_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exception_id INTEGER NOT NULL,
    author TEXT NOT NULL DEFAULT 'session_user',
    note_text TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(exception_id) REFERENCES FactException(exception_id)
);

CREATE TABLE IF NOT EXISTS MappingProfile (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    header_signature TEXT NOT NULL,
    sheet_selector TEXT,
    header_row INTEGER NOT NULL DEFAULT 1,
    delimiter TEXT DEFAULT ',',
    encoding TEXT DEFAULT 'utf-8',
    date_rule TEXT DEFAULT 'iso',
    number_rule TEXT DEFAULT 'standard',
    is_builtin INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, source_type)
);

CREATE TABLE IF NOT EXISTS MappingProfileVersion (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    version_no INTEGER NOT NULL,
    definition TEXT NOT NULL, -- JSON
    effective_from_period_id INTEGER,
    change_note TEXT NOT NULL,
    is_current INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT NOT NULL DEFAULT 'system',
    FOREIGN KEY(profile_id) REFERENCES MappingProfile(profile_id),
    UNIQUE(profile_id, version_no)
);

CREATE TABLE IF NOT EXISTS DimMapping (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    version_no INTEGER NOT NULL,
    source_system TEXT NOT NULL,
    source_column TEXT NOT NULL,
    canonical_field TEXT NOT NULL,
    transform TEXT, -- JSON
    effective_from_period_id INTEGER,
    approved_by TEXT,
    approved_at DATETIME,
    is_active INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(profile_id) REFERENCES MappingProfile(profile_id),
    UNIQUE(profile_id, version_no, source_column)
);

CREATE TABLE IF NOT EXISTS FactPackIssue (
    issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_id INTEGER NOT NULL,
    pack_version INTEGER NOT NULL,
    pack_type TEXT NOT NULL DEFAULT 'both', -- excel, ppt, both
    issued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    issued_by TEXT NOT NULL DEFAULT 'Aarti',
    recipients TEXT NOT NULL, -- JSON array of strings
    snapshot_id INTEGER,
    file_names TEXT NOT NULL, -- JSON array of filenames
    status TEXT NOT NULL DEFAULT 'issued', -- issued, superseded
    notes TEXT
);

CREATE TABLE IF NOT EXISTS Commentary (
    commentary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_id INTEGER NOT NULL,
    scope_type TEXT NOT NULL, -- line, executive
    subject_key TEXT NOT NULL, -- account_code or 'EXECUTIVE'
    current_version_no INTEGER NOT NULL DEFAULT 1,
    locked_by_issue_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(period_id, scope_type, subject_key)
);

CREATE TABLE IF NOT EXISTS CommentaryVersion (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    commentary_id INTEGER NOT NULL,
    version_no INTEGER NOT NULL,
    text TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'user', -- user, ai, rule_based
    author TEXT NOT NULL DEFAULT 'Aarti',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(commentary_id) REFERENCES Commentary(commentary_id)
);

CREATE TABLE IF NOT EXISTS FactExport (
    export_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pack_token TEXT NOT NULL, -- excel, ppt, both
    pack_version INTEGER NOT NULL DEFAULT 1,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL DEFAULT 0,
    period_code TEXT NOT NULL,
    scenario_id TEXT NOT NULL DEFAULT 'base',
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    generated_by TEXT NOT NULL DEFAULT 'Aarti',
    status TEXT NOT NULL DEFAULT 'ready'
);


-- Mapping review queue per 02_FUNCTIONAL_SPEC.md FR-IMP-008.
-- AI may only PROPOSE: this table records proposals and their human decision.
-- It never applies a mapping - DimMapping remains the single apply point.
CREATE TABLE IF NOT EXISTS MappingSuggestion (
    suggestion_id INTEGER PRIMARY KEY AUTOINCREMENT,
    identity_hash TEXT NOT NULL UNIQUE,
    import_run_id INTEGER NOT NULL,
    source_column TEXT NOT NULL,
    suggested_target_field TEXT NOT NULL,
    resolved_target_field TEXT,
    confidence TEXT NOT NULL,
    origin TEXT NOT NULL DEFAULT 'rule',
    state TEXT NOT NULL DEFAULT 'suggested',
    evidence_examples TEXT, -- JSON array of example rows justifying the proposal
    decided_by TEXT,
    decided_at DATETIME,
    malformed_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mapping_suggestion_run
    ON MappingSuggestion(import_run_id, state);

-- Append-only audit trail for every state change (FR-IMP-008 "audit trail").
CREATE TABLE IF NOT EXISTS MappingSuggestionAudit (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_id INTEGER NOT NULL,
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL, -- accept, edit, reject, bulk_accept, bulk_edit
    detail TEXT, -- JSON: e.g. {"previous_target": "...", "new_target": "..."}
    occurred_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(suggestion_id) REFERENCES MappingSuggestion(suggestion_id)
);

-- Records WHICH accepted suggestions were baked into WHICH mapping profile
-- version, and by which import run. This is the write side of FR-IMP-008
-- ("accepted mappings apply to future imports").
--
-- The UNIQUE(suggestion_id) constraint is what makes application idempotent:
-- re-resolving the profile on a later run finds the suggestion already applied
-- and does not create another version. Without it, every subsequent import
-- would bump the profile version forever.
CREATE TABLE IF NOT EXISTS MappingSuggestionApplication (
    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_id INTEGER NOT NULL,
    profile_id INTEGER NOT NULL,
    version_no INTEGER NOT NULL,
    import_run_id INTEGER NOT NULL,
    source_column TEXT NOT NULL,
    canonical_field TEXT NOT NULL,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(suggestion_id) REFERENCES MappingSuggestion(suggestion_id),
    UNIQUE(suggestion_id)
);

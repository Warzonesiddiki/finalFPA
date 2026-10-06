-- DuckDB Analytic Schema per 03_DATA_DICTIONARY.md

CREATE TABLE IF NOT EXISTS DimCompany (
    company_id INTEGER PRIMARY KEY,
    company_code VARCHAR(40) NOT NULL UNIQUE,
    company_name VARCHAR(200) NOT NULL,
    entity_type VARCHAR(20) NOT NULL DEFAULT 'legal',
    parent_company_id INTEGER,
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    source_system VARCHAR(40) NOT NULL DEFAULT 'D365',
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS DimAccount (
    account_id INTEGER PRIMARY KEY,
    account_code VARCHAR(40) NOT NULL UNIQUE,
    account_name VARCHAR(200) NOT NULL,
    account_type VARCHAR(20) NOT NULL,
    statement_line VARCHAR(120),
    parent_account_id INTEGER,
    hierarchy_level SMALLINT NOT NULL DEFAULT 0,
    is_postable BOOLEAN NOT NULL DEFAULT TRUE,
    favourability_direction VARCHAR(20) NOT NULL DEFAULT 'lower_is_favourable',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS DimCostCenter (
    cost_center_id INTEGER PRIMARY KEY,
    cost_center_code VARCHAR(40) NOT NULL UNIQUE,
    cost_center_name VARCHAR(200) NOT NULL,
    parent_cost_center_id INTEGER,
    hierarchy_level SMALLINT NOT NULL DEFAULT 0,
    department_name VARCHAR(200),
    company_id INTEGER NOT NULL DEFAULT 1,
    owner_name VARCHAR(120),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS MasterApprovalThreshold (
    threshold_id VARCHAR(80) NOT NULL,
    scope VARCHAR(20) NOT NULL CHECK (scope IN ('company', 'account', 'cost_center')),
    company_id INTEGER,
    account_id INTEGER,
    cost_center_id INTEGER,
    amount_threshold DECIMAL(18,2) NOT NULL CHECK (amount_threshold > 0),
    requires_dual_approval BOOLEAN NOT NULL DEFAULT FALSE,
    effective_from DATE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(120) NOT NULL DEFAULT 'system',
    change_note VARCHAR(500) NOT NULL DEFAULT '',
    updated_at TIMESTAMP,
    updated_by VARCHAR(120),
    CHECK (
        (scope = 'company' AND company_id IS NOT NULL AND account_id IS NULL AND cost_center_id IS NULL)
        OR (scope = 'account' AND company_id IS NULL AND account_id IS NOT NULL AND cost_center_id IS NULL)
        OR (scope = 'cost_center' AND company_id IS NULL AND account_id IS NULL AND cost_center_id IS NOT NULL)
    ),
    PRIMARY KEY (threshold_id, effective_from)
);

CREATE INDEX IF NOT EXISTS idx_master_approval_threshold_scope_effective
    ON MasterApprovalThreshold(scope, effective_from, is_active);

CREATE TABLE IF NOT EXISTS DerivedDataState (
    state_id INTEGER PRIMARY KEY CHECK (state_id = 1),
    is_stale BOOLEAN NOT NULL DEFAULT FALSE,
    reason VARCHAR(500),
    generation BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS DimVendor (
    vendor_id INTEGER PRIMARY KEY,
    vendor_code VARCHAR(40) NOT NULL UNIQUE,
    vendor_name VARCHAR(200) NOT NULL,
    category_id INTEGER,
    is_intercompany BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    source VARCHAR(20) NOT NULL DEFAULT 'imported',
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to DATE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS DimProject (
    project_id INTEGER PRIMARY KEY,
    project_code VARCHAR(40) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    project_type VARCHAR(20) NOT NULL DEFAULT 'client',
    company_id INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS DimPeriod (
    period_id INTEGER PRIMARY KEY,
    fiscal_year SMALLINT NOT NULL,
    period_number SMALLINT NOT NULL,
    period_code VARCHAR(20) NOT NULL UNIQUE,
    period_label VARCHAR(40) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(10) NOT NULL DEFAULT 'open',
    has_actuals BOOLEAN NOT NULL DEFAULT FALSE,
    has_budget BOOLEAN NOT NULL DEFAULT FALSE,
    is_forecast_eligible BOOLEAN NOT NULL DEFAULT TRUE,
    closed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS FactActual (
    actual_id BIGINT PRIMARY KEY,
    import_batch_id BIGINT NOT NULL,
    row_fingerprint VARCHAR(64) NOT NULL,
    company_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    cost_center_id INTEGER,
    department_id INTEGER,
    project_id INTEGER,
    vendor_id INTEGER,
    period_id INTEGER NOT NULL,
    posting_date DATE NOT NULL,
    document_date DATE,
    voucher_no VARCHAR(60) NOT NULL,
    document_no VARCHAR(60),
    invoice_no VARCHAR(60),
    line_no INTEGER NOT NULL DEFAULT 1,
    description VARCHAR(500),
    debit DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    credit DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    net_amount DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    journal_category VARCHAR(20),
    source_system VARCHAR(40) NOT NULL DEFAULT 'D365',
    source_file_name VARCHAR(260) NOT NULL,
    source_row_ref VARCHAR(80) NOT NULL,
    is_zero_amount BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS FactBudget (
    budget_id BIGINT PRIMARY KEY,
    import_batch_id BIGINT NOT NULL,
    budget_version VARCHAR(40) NOT NULL DEFAULT 'FY26-Approved',
    scenario_code VARCHAR(20) NOT NULL DEFAULT 'base',
    company_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    cost_center_id INTEGER,
    department_id INTEGER,
    project_id INTEGER,
    period_id INTEGER NOT NULL,
    amount DECIMAL(18,2) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    is_derived_spread BOOLEAN NOT NULL DEFAULT FALSE,
    source_row_ref VARCHAR(80) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS DimMapping (
    mapping_id INTEGER PRIMARY KEY,
    profile_id INTEGER NOT NULL,
    version_no INTEGER NOT NULL,
    source_system VARCHAR(40) NOT NULL,
    source_column VARCHAR(200) NOT NULL,
    canonical_field VARCHAR(60) NOT NULL,
    transform VARCHAR(2000),
    effective_from_period_id INTEGER,
    approved_by VARCHAR(120),
    approved_at TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    notes VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS FactForecast (
    forecast_id BIGINT PRIMARY KEY,
    forecast_version_id VARCHAR(40) NOT NULL,
    scenario_id VARCHAR(20) NOT NULL,
    method_id VARCHAR(40) NOT NULL,
    company_id INTEGER NOT NULL DEFAULT 1,
    account_id INTEGER NOT NULL,
    cost_center_id INTEGER,
    project_id INTEGER,
    period_id INTEGER NOT NULL,
    amount DECIMAL(18,2) NOT NULL,
    is_manual_override BOOLEAN NOT NULL DEFAULT FALSE,
    override_reason VARCHAR(500),
    driver_ref VARCHAR(2000), -- JSON
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    generated_by VARCHAR(120) NOT NULL DEFAULT 'system',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS FactForecastVersion (
    forecast_version_id VARCHAR(40) PRIMARY KEY,
    period_generated_for INTEGER NOT NULL,
    scenario_id VARCHAR(20) NOT NULL,
    version_no INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft', -- draft, locked, superseded
    locked_at TIMESTAMP,
    locked_by VARCHAR(120),
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    generated_by VARCHAR(120) NOT NULL DEFAULT 'system',
    notes VARCHAR(500)
);


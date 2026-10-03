"""Engine imports root package."""

from app.engine.imports.models import (
    PreScanResult,
    ValidationIssue,
    ValidationCheckReport,
    ParsedTransaction,
    ImportBatchResult,
)
from app.engine.imports.profiles import (
    MappingProfile,
    MappingProfileVersion,
    DimMapping,
    BUILTIN_PROFILES,
    match_profile,
    normalize_header,
    compute_header_signature,
)
from app.engine.imports.parser import (
    prescan_file,
    parse_and_validate_csv,
    parse_csv_transactions,
    compute_file_checksum,
)

from app.engine.imports.hardening import (
    HardeningFinding,
    CsvDetectionResult,
    ExcelHardenedData,
    detect_csv_encoding_and_delimiter,
    read_hardened_csv,
    detect_hidden_sheets,
    unmerge_header_cells,
    detect_merged_data_cells,
    verify_cached_formulas,
    trim_trailing_empty,
    concatenate_multi_row_headers,
    is_total_subtotal_row,
    load_hardened_excel_sheet,
)

from app.engine.imports.mapping_suggestions import (
    MappingSuggestion,
    CANONICAL_FIELDS,
    build_suggestion_queue,
    applyable_suggestions,
)

from app.engine.imports.profile_binding import (
    ProfileBindingResult,
    next_import_run_id,
    resolve_base_profile,
    resolve_profile_for_import,
    unmapped_columns_for_headers,
    verify_run_id_prediction,
)

from app.engine.imports.vendor_budget_loader import (
    BudgetCommitBlocked,
    BudgetLoadResult,
    VendorLoadResult,
    commit_budget_csv,
    commit_vendor_csv,
    parse_budget_csv,
    parse_vendor_csv,
)

__all__ = [
    "PreScanResult",
    "ValidationIssue",
    "ValidationCheckReport",
    "ParsedTransaction",
    "ImportBatchResult",
    "MappingProfile",
    "MappingProfileVersion",
    "DimMapping",
    "BUILTIN_PROFILES",
    "match_profile",
    "normalize_header",
    "compute_header_signature",
    "prescan_file",
    "parse_and_validate_csv",
    "parse_csv_transactions",
    "compute_file_checksum",
    "HardeningFinding",
    "CsvDetectionResult",
    "ExcelHardenedData",
    "detect_csv_encoding_and_delimiter",
    "read_hardened_csv",
    "detect_hidden_sheets",
    "unmerge_header_cells",
    "detect_merged_data_cells",
    "verify_cached_formulas",
    "trim_trailing_empty",
    "concatenate_multi_row_headers",
    "is_total_subtotal_row",
    "load_hardened_excel_sheet",
    "MappingSuggestion",
    "CANONICAL_FIELDS",
    "build_suggestion_queue",
    "applyable_suggestions",
    "ProfileBindingResult",
    "next_import_run_id",
    "resolve_base_profile",
    "resolve_profile_for_import",
    "unmapped_columns_for_headers",
    "verify_run_id_prediction",
    "BudgetCommitBlocked",
    "BudgetLoadResult",
    "VendorLoadResult",
    "commit_budget_csv",
    "commit_vendor_csv",
    "parse_budget_csv",
    "parse_vendor_csv",
]

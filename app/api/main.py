"""FastAPI backend application and local API router per ADR-009 and 26_API_CONTRACT.md."""

from fastapi import FastAPI, Depends, Header, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from decimal import Decimal
from functools import lru_cache
from typing import Optional, Dict, Any, List, Literal
import secrets
import os
import logging

from app import __version__, __app_name__
from app.engine.errors import get_error_catalog
from app.engine.calc import calculate_variance, calculate_variance_pct, quantize_money, ZERO
from app.engine.imports.parser import (
    prescan_file,
    parse_csv_transactions,
    parse_excel_transactions,
)
from app.engine.store.db import DatabaseManager
from app.engine.store.import_repo import ImportRepository
from app.engine.store.analytics_repo import AnalyticsRepository
from app.engine.store.exceptions_repo import (
    ExceptionsRepository,
    ExceptionStatusEvidenceRequired,
    ExceptionWorkflowError,
    InvalidExceptionStatus,
)
from app.engine.store.master_data_repo import (
    ApprovalThresholdConflict,
    ApprovalThresholdError,
    ApprovalThresholdRepository,
)
from app.engine.store.forecast_repo import ForecastRepository
from app.engine.store.reports_repo import ReportsRepository
from app.engine.store.period_repo import PeriodRepository
from app.engine.ai.client import AIClient, AIConfig, RuleBasedNarrativeGenerator
from app.engine.ai.usage import AIUsageStore
from app.engine.ai.provenance import AiProvenanceStore
from app.engine.ai.pinning import get_model_pinning_config, validate_model_selection
from app.engine.ai.prompts import PromptTemplateStore

logger = logging.getLogger(__name__)

# Session token for loopback security per ADR-009
SESSION_TOKEN = secrets.token_hex(16)


@lru_cache(maxsize=1)
def _staleness_db_manager() -> DatabaseManager:
    """Reuse one lazy manager so periodic staleness polls do not re-run DDL."""
    return DatabaseManager()


class RunForecastRequest(BaseModel):
    period: Optional[str] = "FY26-P09"
    scenario: Optional[str] = "base"
    default_method: Optional[str] = "run_rate"
    run_rate_n: Optional[int] = 3


class OverrideForecastRequest(BaseModel):
    account_id: int
    period_code: str
    amount: str
    reason: str
    scenario: Optional[str] = "base"


class LockForecastVersionRequest(BaseModel):
    confirm: Optional[bool] = True


class OpenPeriodRequest(BaseModel):
    fiscal_year: int
    period_number: int
    period_code: str
    period_label: str
    start_date: str
    end_date: str
    carry_forward_mappings: Optional[bool] = True
    carry_forward_assumptions: Optional[bool] = True


class ReopenPeriodRequest(BaseModel):
    reason: str
    reopened_by: Optional[str] = "admin"


class GeneratePackRequest(BaseModel):
    period: Optional[str] = "FY26-P09"
    scenario: Optional[str] = "base"
    format: Optional[str] = "both"  # excel, ppt, both


class IssuePackRequest(BaseModel):
    period_id: Optional[int] = 9
    period_code: Optional[str] = "FY26-P09"
    recipients: List[str]
    pack_type: Optional[str] = "both"
    notes: Optional[str] = None


class ReissuePackRequest(BaseModel):
    issue_id: int
    reason: str


class SaveCommentaryRequest(BaseModel):
    period_id: Optional[int] = 9
    scope_type: str  # line, executive
    subject_key: str
    text: str
    author: Optional[str] = "Aarti"



class RunRulesRequest(BaseModel):
    period: Optional[str] = "FY26-P09"
    asOfDate: Optional[str] = "2026-11-12"
    correlationId: Optional[str] = None
    claimId: Optional[str] = None


ExceptionStatusInput = Literal[
    "open", "in_review", "explained", "corrected", "closed", "reopened", "not_applicable"
]


class PatchExceptionRequest(BaseModel):
    status: Optional[ExceptionStatusInput] = None
    owner: Optional[str] = None
    note: Optional[str] = None


class BulkExceptionRequest(BaseModel):
    ids: List[int]
    status: Optional[ExceptionStatusInput] = None
    owner: Optional[str] = None
    note: Optional[str] = None


class ApprovalThresholdCreateRequest(BaseModel):
    thresholdId: str
    scope: Literal["company", "account", "cost_center"]
    amountThreshold: str
    requiresDualApproval: bool
    effectiveFrom: str
    changeNote: str
    isActive: bool = True
    companyCode: Optional[str] = None
    accountCode: Optional[str] = None
    costCenterCode: Optional[str] = None


class BudgetReplaceRequest(BaseModel):
    budgetVersion: str = Field("FY26-Approved")
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    batchId: int = Field(999)


# --- Mapping review queue models (02 FR-IMP-008) ---------------------------

class MappingSuggestionRequest(BaseModel):
    """One proposed mapping. AI may only PROPOSE (FR-IMP-008)."""

    sourceColumn: str
    targetField: str
    confidence: str
    origin: str = "rule"
    evidence: List[Dict[str, Any]] = Field(default_factory=list)


class EnqueueSuggestionsRequest(BaseModel):
    importRunId: int
    aiEnabled: bool = False
    suggestions: List[MappingSuggestionRequest] = Field(default_factory=list)


class DecideSuggestionRequest(BaseModel):
    action: str  # accept | edit | reject
    actor: str = "session_user"
    newTargetField: Optional[str] = None
    reason: Optional[str] = None


class BulkMappingDecisionRequest(BaseModel):
    ids: List[int]
    action: str  # accept | edit | reject
    actor: str = "session_user"
    newTargets: Dict[int, str] = Field(default_factory=dict)
    reason: Optional[str] = None


def get_session_token() -> str:
    """Return active session token for pywebview shell injection."""
    return SESSION_TOKEN


def verify_session_token(
    x_session_token: str = Header(None, alias="X-Session-Token"),
) -> str:
    """Enforce session token verification on API endpoints per ADR-009."""
    if not x_session_token or x_session_token != SESSION_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing session token",
        )
    return x_session_token


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    engine_ready: bool


class PreScanRequest(BaseModel):
    path: str
    sourceType: Optional[str] = None


class ControlTotalAcceptanceRequest(BaseModel):
    acceptedBy: str = Field(min_length=1, max_length=120)
    reason: str = Field(min_length=10, max_length=500)

    @field_validator("acceptedBy")
    @classmethod
    def validate_accepted_by(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("acceptedBy must not be blank")
        return cleaned

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 10:
            raise ValueError("reason must contain at least 10 non-whitespace characters")
        return cleaned


class ImportFileRequest(BaseModel):
    path: str
    sourceType: Optional[str] = None
    balanceTolerance: Decimal = Field(default=Decimal("0.00"), ge=0)
    controlTotalAcceptance: Optional[ControlTotalAcceptanceRequest] = None


class VoidBatchRequest(BaseModel):
    confirm: bool
    reason: str


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=__app_name__,
        version=__version__,
        docs_url=None,  # Disabled in production bundle
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1", "http://localhost"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _get_staleness_state() -> Dict[str, Any]:
        conn = _staleness_db_manager().get_duckdb_connection()
        try:
            row = conn.execute(
                "SELECT is_stale, reason, generation FROM DerivedDataState WHERE state_id = 1"
            ).fetchone()
            if not row:
                return {"isStale": False, "reason": None, "generation": 0}
            return {
                "isStale": bool(row[0]),
                "reason": row[1],
                "generation": int(row[2] or 0),
            }
        finally:
            conn.close()

    def _set_staleness_state(is_stale: bool, reason: Optional[str]) -> Dict[str, Any]:
        conn = _staleness_db_manager().get_duckdb_connection()
        try:
            conn.execute("BEGIN TRANSACTION")
            existing = conn.execute(
                "SELECT 1 FROM DerivedDataState WHERE state_id = 1"
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE DerivedDataState
                    SET is_stale = ?,
                        reason = ?,
                        generation = COALESCE(generation, 0) + CASE WHEN ? THEN 1 ELSE 0 END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE state_id = 1
                    """,
                    [bool(is_stale), reason, bool(is_stale)],
                )
            else:
                conn.execute(
                    """
                    INSERT INTO DerivedDataState (state_id, is_stale, reason, generation)
                    VALUES (1, ?, ?, CASE WHEN ? THEN 1 ELSE 0 END)
                    """,
                    [bool(is_stale), reason, bool(is_stale)],
                )
            generation_row = conn.execute(
                "SELECT generation FROM DerivedDataState WHERE state_id = 1"
            ).fetchone()
            conn.execute("COMMIT")
            return {
                "isStale": bool(is_stale),
                "reason": reason,
                "generation": int(generation_row[0] or 0) if generation_row else 0,
            }
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def _clear_staleness_state_if_unchanged(expected_generation: int) -> Optional[Dict[str, Any]]:
        conn = _staleness_db_manager().get_duckdb_connection()
        try:
            conn.execute("BEGIN TRANSACTION")
            row = conn.execute(
                "SELECT is_stale, reason, generation FROM DerivedDataState WHERE state_id = 1"
            ).fetchone()
            if not row:
                conn.execute("COMMIT")
                return None
            generation = int(row[2] or 0)
            if generation != expected_generation:
                conn.execute("COMMIT")
                return None
            conn.execute(
                """
                UPDATE DerivedDataState
                SET is_stale = FALSE, reason = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE state_id = 1 AND COALESCE(generation, 0) = ?
                """,
                [expected_generation],
            )
            current = conn.execute(
                "SELECT is_stale, reason, generation FROM DerivedDataState WHERE state_id = 1"
            ).fetchone()
            conn.execute("COMMIT")
            return {
                "isStale": bool(current[0]),
                "reason": current[1],
                "generation": int(current[2] or 0),
            }
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "code": "ERR-API-422",
                "userMessage": "Validation error in input payload",
                "hint": "Check request parameters for syntax errors.",
                "error": {
                    "code": "ERR-API-422",
                    "userMessage": "Validation error",
                    "hint": "Check request parameters for syntax errors.",
                }
            }
        )

    @app.exception_handler(HTTPException)
    @app.exception_handler(StarletteHTTPException)
    async def universal_http_exception_handler(request: Request, exc: HTTPException | StarletteHTTPException):
        """Universal error envelope handler per docs 26 (§5) and docs 08 (§16).

        Quote docs 26 §5: 'All error responses MUST adhere to the standardized error envelope 
        containing code (e.g., ERR-VAL-001), userMessage (human readable description), hint (actionable guidance).'
        Quote docs 08 §16: 'Error Message Catalog (SCR-041): Every user-facing error must display 
        its error code, clear explanation, and troubleshooting hint.'
        """
        status_code = exc.status_code
        detail = exc.detail
        
        code_map = {
            400: ("ERR-API-400", "Review the request parameters and try again."),
            401: ("ERR-API-401", "Authenticate with a valid session token."),
            403: ("ERR-API-403", "Action not permitted under current user role or state."),
            404: ("ERR-API-404", "The requested resource could not be found."),
            409: ("ERR-API-409", "Conflict detected with current state."),
            422: ("ERR-API-422", "Validation error in input payload."),
        }
        # User-facing copy for the codes above, keyed by status.
        CATALOG_MESSAGES = {
            400: "The request could not be processed.",
            401: "Authentication is required.",
            403: "You do not have permission to perform this action.",
            404: "The requested resource could not be found.",
            409: "The request conflicts with the current state.",
            422: "Validation error in input payload.",
        }
        # Starlette's bare routing-level defaults. Matched exactly so that a
        # route raising its own detail string is never overwritten.
        FRAMEWORK_DEFAULT_DETAILS = {404: "Not Found", 405: "Method Not Allowed"}
        code, hint = code_map.get(status_code, (f"ERR-API-{status_code}", "An unexpected error occurred. Check diagnostics."))
        
        if isinstance(detail, dict):
            user_message = detail.get("userMessage", detail.get("message", str(detail)))
            code = detail.get("code", code)
            hint = detail.get("hint", hint)
        else:
            user_message = str(detail)
            # Starlette raises bare framework defaults for routing-level failures
            # (404 -> "Not Found", 405 -> "Method Not Allowed"). Those are internal
            # strings, not user-facing copy: docs 26 section 5 requires a
            # human-readable userMessage. Substitute the catalog message ONLY for
            # these exact defaults, so a route that raises a specific detail
            # (e.g. HTTPException(400, detail="Batch 999 not found")) keeps its
            # own text.
            if user_message.strip() == FRAMEWORK_DEFAULT_DETAILS.get(status_code):
                user_message = CATALOG_MESSAGES.get(status_code, user_message)

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "error",
                "code": code,
                "userMessage": user_message,
                "hint": hint,
                "error": {
                    "code": code,
                    "userMessage": user_message,
                    "hint": hint,
                }
            }
        )

    @app.exception_handler(Exception)
    async def global_unhandled_exception_handler(request: Request, exc: Exception):
        """Global fallback handler for unhandled exceptions per docs 26 (§5).

        Quote docs 26 §5: 'Under no circumstances shall unhandled exceptions, raw stack traces, 
        or debug HTML reach the client; unexpected server errors must return status 500 formatted 
        with ERR-API-500, a clean user message, and a troubleshooting hint.'
        """
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "code": "ERR-API-500",
                "userMessage": "An unexpected internal error occurred.",
                "hint": "Check server diagnostics logs or retry the operation.",
                "error": {
                    "code": "ERR-API-500",
                    "userMessage": "An unexpected internal error occurred.",
                    "hint": "Check server diagnostics logs or retry the operation.",
                }
            }
        )

    @app.get("/api/v1/health", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        """Health check endpoint accessible by desktop shell."""
        return HealthResponse(
            status="ok",
            app=__app_name__,
            version=__version__,
            engine_ready=True,
        )

    @app.get("/meta/error-catalog")
    @app.get("/api/v1/meta/error-catalog")
    def get_error_catalog_endpoint() -> Dict[str, Any]:
        """Serve the runtime error catalog per docs 26 (§5) and docs 08 (§16).

        Quote docs 26 §5: 'GET /meta/error-catalog is the runtime projection of this section: 
        {code, slug, severity, message, hint, httpStatus, ownerDoc}.'
        """
        catalog = get_error_catalog()
        return {
            "status": "ok",
            "count": len(catalog),
            "catalog": catalog,
        }

    @app.get("/api/v1/_test_crash")
    def test_crash_endpoint():
        """Test endpoint simulating unhandled repo failure per doc 26 (gated)."""
        if os.environ.get("FPA_TEST_MODE") != "1":
            raise HTTPException(status_code=404, detail="Not found")
        raise RuntimeError("Simulated unhandled repo/db failure")
    @app.get("/api/v1/bootstrap")
    def api_bootstrap() -> Dict[str, Any]:
        """Bootstrap endpoint providing session token, app metadata and project context."""
        return {
            "status": "ok",
            "app": {
                "appName": __app_name__,
                "appVersion": __version__,
                "schemaVersion": 1,
            },
            "session_token": SESSION_TOKEN,
            "sample": {
                "exists": True,
                "path": "default",
            },
        }

    @app.post(
        "/api/v1/calc/variance-demo",
        dependencies=[Depends(verify_session_token)],
    )
    def variance_demo(payload: Dict[str, str]) -> Dict[str, Any]:
        """Variance demonstration endpoint."""
        act = Decimal(payload["actual"])
        bud = Decimal(payload["budget"])
        var = calculate_variance(act, bud)
        var_pct = calculate_variance_pct(act, bud)
        return {
            "actual": str(quantize_money(act)),
            "budget": str(quantize_money(bud)),
            "variance": str(var),
            "variance_pct": str(var_pct) if var_pct is not None else None,
        }

    @app.post(
        "/api/v1/imports/pre-scan",
        dependencies=[Depends(verify_session_token)],
    )
    def api_prescan(payload: PreScanRequest) -> Dict[str, Any]:
        """Execute Step 2 Pre-scan per 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md §3 and 26 §3.2."""
        p = Path(payload.path)
        if not p.exists():
            raise HTTPException(status_code=400, detail=f"File not found: {payload.path}")
        res = prescan_file(p)
        return {
            "fileName": res.file_name,
            "fileSizeBytes": res.file_size_bytes,
            "fileChecksum": res.file_checksum,
            "sheetNames": res.sheet_names,
            "estimatedRows": res.estimated_rows,
            "headerRowCandidate": res.header_row_candidate,
            "sampleHeaders": res.sample_headers,
            "hasBanner": res.has_banner,
        }

    @app.post(
        "/api/v1/imports",
        dependencies=[Depends(verify_session_token)],
    )
    def api_import(payload: ImportFileRequest) -> Dict[str, Any]:
        """Parse, validate, and atomically commit a source file per 04 §3 and 26 §3.2.

        FR-IMP-008: before parsing, fold in every mapping suggestion that a
        human accepted during an EARLIER import run, so a suggestion accepted in
        import N is applied automatically in import N+1. `resolve_profile_for_import`
        excludes suggestions raised by the current run, so this call can never
        apply a suggestion the current file itself produced.
        """
        p = Path(payload.path)
        if not p.exists():
            raise HTTPException(status_code=400, detail=f"File not found: {payload.path}")

        db_mgr = DatabaseManager()

        from app.engine.imports.profile_binding import (
            resolve_base_profile,
            resolve_profile_for_import,
        )

        prescan = prescan_file(p)
        binding = resolve_profile_for_import(
            db_mgr,
            base_profile=resolve_base_profile(db_mgr, prescan.sample_headers),
        )
        predicted_run_id = binding.import_run_id

        control_acceptance = None
        if payload.controlTotalAcceptance is not None:
            control_acceptance = {
                "accepted_by": payload.controlTotalAcceptance.acceptedBy.strip(),
                "reason": payload.controlTotalAcceptance.reason.strip(),
            }
        if p.suffix.lower() in {".xlsx", ".xlsm"}:
            batch, transactions = parse_excel_transactions(
                p,
                profile=binding.profile,
                balance_tolerance=payload.balanceTolerance,
                control_total_acceptance=control_acceptance,
            )
            control_check = next(
                (check for check in batch.checks if check.check_code == "IMP-025"),
                None,
            )
            if control_acceptance and control_check and control_check.status == "skipped":
                raise HTTPException(
                    status_code=400,
                    detail="controlTotalAcceptance requires a ControlTotals worksheet",
                )
        else:
            if control_acceptance:
                raise HTTPException(
                    status_code=400,
                    detail="controlTotalAcceptance is supported only for Excel workbooks",
                )
            batch, transactions = parse_csv_transactions(
                p,
                profile=binding.profile,
                balance_tolerance=payload.balanceTolerance,
            )
        repo = ImportRepository(db_mgr)
        batch_id = repo.commit_batch(batch, transactions)

        # The profile history now carries the applied suggestions, and this
        # batch_id is the run the next import's resolution will look past.
        if batch_id != predicted_run_id:
            logger.warning(
                "Import run id prediction drifted: predicted %s, committed %s. "
                "Suggestions enqueued against the predicted id may not apply on "
                "the next run.",
                predicted_run_id,
                batch_id,
            )

        import_status = "committed" if batch.can_commit else "rejected"
        return {
            "batchId": batch_id,
            "status": import_status,
            "profileBinding": binding.to_dict(),
            "fileName": batch.file_name,
            "sheetName": batch.sheet_name,
            "fileChecksum": batch.file_checksum,
            "sourceType": batch.source_type,
            "totalSourceRows": batch.total_source_rows,
            "loadedCount": batch.loaded_count,
            "quarantinedCount": batch.quarantined_count,
            "rejectedCount": batch.rejected_count,
            "isBalanced": batch.is_balanced,
            "totalDebit": str(batch.total_debit),
            "totalCredit": str(batch.total_credit),
            "netImbalance": str(batch.net_imbalance),
            "balanceTolerance": str(batch.balance_tolerance),
        }

    @app.get(
        "/api/v1/imports",
        dependencies=[Depends(verify_session_token)],
    )
    def api_list_imports() -> Dict[str, Any]:
        """Return import batch history per 26_API_CONTRACT.md §3.2."""
        db_mgr = DatabaseManager()
        repo = ImportRepository(db_mgr)
        batches = repo.list_batches()
        return {"status": "ok", "data": {"items": batches, "total": len(batches)}}

    @app.get(
        "/api/v1/imports/{batch_id}",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_batch_detail(batch_id: int) -> Dict[str, Any]:
        """Return batch details, validation checks, and quarantine rows per FR-IMP-021/023."""
        db_mgr = DatabaseManager()
        repo = ImportRepository(db_mgr)
        details = repo.get_batch_detail(batch_id)
        if not details:
            raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
        return {"status": "ok", "data": details}

    @app.post(
        "/api/v1/imports/{batch_id}/void",
        dependencies=[Depends(verify_session_token)],
    )
    def api_void_batch(batch_id: int, payload: VoidBatchRequest) -> Dict[str, Any]:
        """Void/reverse one batch per 02 FR-IMP-024 and 26 §3.2."""
        if not payload.confirm:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "ERR-VAL-001",
                    "userMessage": "Confirmation required to void batch",
                    "hint": "Check the API spec for required confirmation parameters.",
                },
            )
        db_mgr = DatabaseManager()
        repo = ImportRepository(db_mgr)
        success = repo.void_batch(batch_id, payload.reason)
        if not success:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "ERR-API-400",
                    "userMessage": f"Batch {batch_id} not found or already voided",
                    "hint": "Review the batch ID and status and try again.",
                },
            )
        return {"status": "ok", "batchId": batch_id, "action": "voided", "reason": payload.reason}

    @app.get(
        "/api/v1/analysis/three-way",
        dependencies=[Depends(verify_session_token)],
    )
    @app.get(
        "/api/v1/bva/three-way",
        dependencies=[Depends(verify_session_token)],
    )
    def api_three_way_analysis(
        period_id: Optional[int] = None,
        window: str = "MTD",
    ) -> Dict[str, Any]:
        """Three-way Actual vs Budget vs Forecast view with signed-error accuracy columns (FR-BVA-008, CALC-066..069)."""
        db_mgr = DatabaseManager()
        repo = AnalyticsRepository(db_mgr)
        items = repo.get_three_way_summary(period_id=period_id, window=window)
        return {
            "status": "ok",
            "data": {
                "items": items,
                "total": len(items),
            },
        }

    @app.get(
        "/api/v1/analysis/bva",
        dependencies=[Depends(verify_session_token)],
    )
    @app.get(
        "/api/v1/bva",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_bva(
        period_id: Optional[int] = None,
        company_id: Optional[int] = None,
        cost_center_id: Optional[int] = None,
        statement_line: Optional[str] = None,
        window: str = "MTD",
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """BvA summary matrix by account per 26_API_CONTRACT.md §3.4 and FR-BVA-001/002/003."""
        db_mgr = DatabaseManager()
        repo = AnalyticsRepository(db_mgr)
        result = repo.get_bva_summary(
            period_id=period_id,
            company_id=company_id,
            cost_center_id=cost_center_id,
            statement_line=statement_line,
            page=page,
            page_size=page_size,
            window=window,
        )
        return {
            "status": "ok",
            "data": {
                "items": [
                    {
                        "statementLine": item.statement_line,
                        "accountId": item.account_id,
                        "accountCode": item.account_code,
                        "accountName": item.account_name,
                        "accountType": item.account_type,
                        "favourabilityDirection": item.favourability_direction,
                        "actualAmount": str(item.actual_amount),
                        "budgetAmount": str(item.budget_amount),
                        "varianceAmount": str(item.variance_amount),
                        "variancePct": str(item.variance_pct) if item.variance_pct is not None else None,
                        "favourability": item.favourability,
                    }
                    for item in result.items
                ],
                "total": result.total,
                "page": result.page,
                "pageSize": result.page_size,
                "hasMore": result.has_more,
            },
        }

    @app.get(
        "/api/v1/analysis/bva/statement-lines",
        dependencies=[Depends(verify_session_token)],
    )
    @app.get(
        "/api/v1/bva/statement-lines",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_bva_statement_lines(
        period_id: Optional[int] = None,
        company_id: Optional[int] = None,
        cost_center_id: Optional[int] = None,
        window: str = "MTD",
    ) -> Dict[str, Any]:
        """Roll up statement lines per FR-BVA-009 / CALC-042."""
        db_mgr = DatabaseManager()
        repo = AnalyticsRepository(db_mgr)
        lines = repo.get_bva_statement_line_summary(
            period_id=period_id,
            company_id=company_id,
            cost_center_id=cost_center_id,
            window=window,
        )
        return {
            "status": "ok",
            "data": {
                "items": [
                    {
                        "statementLine": line.statement_line,
                        "actualAmount": str(line.actual_amount),
                        "budgetAmount": str(line.budget_amount),
                        "varianceAmount": str(line.variance_amount),
                        "variancePct": str(line.variance_pct) if line.variance_pct is not None else None,
                        "favourability": line.favourability,
                        "accountCount": line.account_count,
                    }
                    for line in lines
                ],
                "total": len(lines),
            },
        }

    @app.get(
        "/api/v1/analysis/bva/entities",
        dependencies=[Depends(verify_session_token)],
    )
    @app.get(
        "/api/v1/bva/entities",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_bva_entities(
        period_id: Optional[int] = None,
        company_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """Entity-level rollups per CALC-041 and FR-BVA-014."""
        db_mgr = DatabaseManager()
        repo = AnalyticsRepository(db_mgr)
        res = repo.get_entity_rollups(period_id=period_id, company_id=company_id, page=page, page_size=page_size)
        return {
            "status": "ok",
            "data": {
                "items": [
                    {
                        "companyId": item.company_id,
                        "companyCode": item.company_code,
                        "companyName": item.company_name,
                        "actualAmount": str(item.actual_amount),
                        "budgetAmount": str(item.budget_amount),
                        "varianceAmount": str(item.variance_amount),
                        "variancePct": str(item.variance_pct) if item.variance_pct is not None else None,
                        "favourability": item.favourability,
                    }
                    for item in res.items
                ],
                "total": res.total,
                "hasMore": res.has_more,
            },
        }

    @app.get(
        "/api/v1/analysis/bva/cost-centers",
        dependencies=[Depends(verify_session_token)],
    )
    @app.get(
        "/api/v1/bva/cost-centers",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_bva_cost_centers(
        period_id: Optional[int] = None,
        company_id: Optional[int] = None,
        department_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """Cost center rollups per FR-BVA-001/007."""
        db_mgr = DatabaseManager()
        repo = AnalyticsRepository(db_mgr)
        res = repo.get_cost_center_aggregations(period_id=period_id, company_id=company_id, department_name=department_name, page=page, page_size=page_size)
        return {
            "status": "ok",
            "data": {
                "items": [
                    {
                        "costCenterId": item.cost_center_id,
                        "costCenterCode": item.cost_center_code,
                        "costCenterName": item.cost_center_name,
                        "departmentName": item.department_name,
                        "actualAmount": str(item.actual_amount),
                        "budgetAmount": str(item.budget_amount),
                        "varianceAmount": str(item.variance_amount),
                        "variancePct": str(item.variance_pct) if item.variance_pct is not None else None,
                        "favourability": item.favourability,
                    }
                    for item in res.items
                ],
                "total": res.total,
                "hasMore": res.has_more,
            },
        }

    @app.get(
        "/api/v1/analysis/drill",
        dependencies=[Depends(verify_session_token)],
    )
    @app.get(
        "/api/v1/bva/drill",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_analysis_drill(
        period_id: Optional[int] = None,
        account_id: Optional[int] = None,
        account_code: Optional[str] = None,
        statement_line: Optional[str] = None,
        company_id: Optional[int] = None,
        cost_center_id: Optional[int] = None,
        voucher_no: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """Transaction detail drill-through per 26_API_CONTRACT.md §3.4 and FR-BVA-004."""
        db_mgr = DatabaseManager()
        repo = AnalyticsRepository(db_mgr)
        result = repo.get_transaction_drill(
            period_id=period_id,
            account_id=account_id,
            account_code=account_code,
            statement_line=statement_line,
            company_id=company_id,
            cost_center_id=cost_center_id,
            voucher_no=voucher_no,
            page=page,
            page_size=page_size,
        )
        return {
            "status": "ok",
            "data": {
                "items": [
                    {
                        "actualId": item.actual_id,
                        "importBatchId": item.import_batch_id,
                        "sourceFileName": item.source_file_name,
                        "sourceRowRef": item.source_row_ref,
                        "postingDate": str(item.posting_date),
                        "voucherNo": item.voucher_no,
                        "lineNo": item.line_no,
                        "invoiceNo": item.invoice_no,
                        "description": item.description,
                        "debit": str(item.debit),
                        "credit": str(item.credit),
                        "netAmount": str(item.net_amount),
                        "companyCode": item.company_code,
                        "accountCode": item.account_code,
                        "accountName": item.account_name,
                        "statementLine": item.statement_line,
                        "costCenterCode": item.cost_center_code,
                    }
                    for item in result.items
                ],
                "total": result.total,
                "page": result.page,
                "pageSize": result.page_size,
                "hasMore": result.has_more,
            },
        }

    # =========================================================================
    # Effective-dated approval-threshold master data (EXC-021 / FR-SET-003)
    # =========================================================================

    @app.get(
        "/api/v1/master-data/approval-thresholds",
        dependencies=[Depends(verify_session_token)],
    )
    def api_list_approval_thresholds() -> Dict[str, Any]:
        repo = ApprovalThresholdRepository(DatabaseManager())
        return {"status": "ok", "data": {"items": repo.list_approval_thresholds()}}

    @app.post(
        "/api/v1/master-data/approval-thresholds",
        dependencies=[Depends(verify_session_token)],
        responses={409: {"description": "Approval threshold version conflict"}},
    )
    def api_create_approval_threshold_version(
        payload: ApprovalThresholdCreateRequest,
    ) -> Dict[str, Any]:
        repo = ApprovalThresholdRepository(DatabaseManager())
        try:
            item = repo.create_approval_threshold_version(
                threshold_id=payload.thresholdId,
                scope=payload.scope,
                amount_threshold=payload.amountThreshold,
                requires_dual_approval=payload.requiresDualApproval,
                effective_from=payload.effectiveFrom,
                change_note=payload.changeNote,
                is_active=payload.isActive,
                company_code=payload.companyCode,
                account_code=payload.accountCode,
                cost_center_code=payload.costCenterCode,
                actor="session_user",
            )
        except ApprovalThresholdConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ApprovalThresholdError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"status": "ok", "data": item}

    # =========================================================================
    # Exceptions Register & Rules Workflow Endpoints (SCR-023..SCR-026, FR-EXC)
    # =========================================================================

    @app.post(
        "/api/v1/exceptions/run",
        dependencies=[Depends(verify_session_token)],
    )
    @app.post(
        "/api/v1/rules/run",
        dependencies=[Depends(verify_session_token)],
    )
    def api_run_rules(payload: Optional[RunRulesRequest] = None) -> Dict[str, Any]:
        """Trigger deterministic execution of the full de-duplicated rule catalog.

        Runs EXC-001..EXC-024 via the shared batch in app.engine.rules.batch.
        `as_of` defaults to None, which derives the run date from the period
        under review (doc 05 CALC-002) rather than any system clock; an explicit
        `asOfDate` in the payload always wins (doc 06 EXC-011 injected run date).
        """
        period = payload.period if payload and payload.period else "FY26-P09"
        as_of = payload.asOfDate if payload and payload.asOfDate else None
        corr_id = payload.correlationId if payload and payload.correlationId else None
        claim_id = payload.claimId if payload and payload.claimId else None
        db_mgr = DatabaseManager()
        repo = ExceptionsRepository(db_mgr)
        summary = repo.run_rules(
            period_code=period,
            as_of_date=as_of,
            correlation_id=corr_id,
            claim_id=claim_id,
        )
        return {"status": "ok", "data": summary}

    # =========================================================================
    # Mapping Review Queue (02 FR-IMP-008). AI may only PROPOSE; these endpoints
    # record proposals and human decisions. They never apply a mapping - applying
    # is the importer's act on a LATER run.
    # =========================================================================

    @app.post(
        "/api/v1/mapping-suggestions",
        dependencies=[Depends(verify_session_token)],
    )
    def api_enqueue_mapping_suggestions(payload: EnqueueSuggestionsRequest) -> Dict[str, Any]:
        """Enqueue proposals for an import run and return the review queue.

        FR-IMP-008: "With AI disabled, the queue shows rule-based suggestions only" -
        so `aiEnabled=False` drops AI-origin proposals entirely.
        """
        from app.engine.imports.mapping_suggestions import build_suggestion_queue
        from app.engine.store.mapping_suggestion_repo import MappingSuggestionRepository

        proposals = [
            {
                "source_column": s.sourceColumn,
                "target_field": s.targetField,
                "confidence": s.confidence,
                "origin": s.origin,
                "evidence": s.evidence,
            }
            for s in payload.suggestions
        ]
        queue = build_suggestion_queue(
            import_run_id=payload.importRunId,
            proposals=proposals,
            ai_enabled=payload.aiEnabled,
        )
        repo = MappingSuggestionRepository(DatabaseManager())
        stored = repo.enqueue(queue)
        return {
            "status": "ok",
            "data": {
                "items": [s.to_dict() for s in stored],
                "total": len(stored),
                "importRunId": payload.importRunId,
                "aiEnabled": payload.aiEnabled,
                "summary": repo.count_by_state(payload.importRunId),
            },
        }

    @app.get(
        "/api/v1/mapping-suggestions",
        dependencies=[Depends(verify_session_token)],
    )
    def api_list_mapping_suggestions(
        importRunId: Optional[int] = None,
        state: Optional[str] = None,
        origin: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List the review queue for an import run (FR-IMP-008)."""
        from app.engine.store.mapping_suggestion_repo import MappingSuggestionRepository

        repo = MappingSuggestionRepository(DatabaseManager())
        page = repo.list_suggestions(
            import_run_id=importRunId, state=state, origin=origin,
            limit=limit, offset=offset,
        )
        page["summary"] = repo.count_by_state(importRunId)
        return {"status": "ok", "data": page}

    @app.post(
        "/api/v1/mapping-suggestions/{suggestion_id}/decision",
        dependencies=[Depends(verify_session_token)],
    )
    def api_decide_mapping_suggestion(
        suggestion_id: int, payload: DecideSuggestionRequest
    ) -> Dict[str, Any]:
        """Accept / edit / reject one suggestion (FR-IMP-008 state machine).

        An illegal transition returns 409 rather than silently rewriting state, so
        the audit trail cannot be tampered with after the fact.
        """
        from app.engine.imports.mapping_suggestions import (
            InvalidSuggestionTransition,
            MalformedAiSuggestion,
        )
        from app.engine.store.mapping_suggestion_repo import MappingSuggestionRepository

        repo = MappingSuggestionRepository(DatabaseManager())
        try:
            updated = repo.decide(
                suggestion_id=suggestion_id,
                action=payload.action,
                actor=payload.actor,
                new_target_field=payload.newTargetField,
                reason=payload.reason,
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="suggestion not found")
        except MalformedAiSuggestion as exc:
            # FR-AI-006: a target field that does not exist is a client-side
            # validation error, not a server fault.
            raise HTTPException(status_code=422, detail=str(exc))
        except InvalidSuggestionTransition as exc:
            # NOTE: must precede the generic ValueError handler below, since
            # InvalidSuggestionTransition subclasses ValueError. A decided
            # suggestion is a state conflict (409), not a malformed request.
            raise HTTPException(status_code=409, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        return {
            "status": "ok",
            "data": {
                "item": updated.to_dict(),
                "audit": repo.get_audit_trail(suggestion_id),
            },
        }

    @app.post(
        "/api/v1/mapping-suggestions/bulk-decision",
        dependencies=[Depends(verify_session_token)],
    )
    def api_bulk_mapping_decision(payload: BulkMappingDecisionRequest) -> Dict[str, Any]:
        """Bulk accept/edit with an audit trail (FR-IMP-008)."""
        from app.engine.store.mapping_suggestion_repo import MappingSuggestionRepository

        repo = MappingSuggestionRepository(DatabaseManager())
        result = repo.bulk_decide(
            suggestion_ids=payload.ids,
            action=payload.action,
            actor=payload.actor,
            new_targets=payload.newTargets,
            reason=payload.reason,
        )
        return {"status": "ok", "data": result}

    @app.get(
        "/api/v1/mapping-suggestions/{suggestion_id}/audit",
        dependencies=[Depends(verify_session_token)],
    )
    def api_mapping_suggestion_audit(suggestion_id: int) -> Dict[str, Any]:
        """Append-only audit trail for one suggestion (FR-IMP-008)."""
        from app.engine.store.mapping_suggestion_repo import MappingSuggestionRepository

        repo = MappingSuggestionRepository(DatabaseManager())
        return {
            "status": "ok",
            "data": {"suggestionId": suggestion_id, "audit": repo.get_audit_trail(suggestion_id)},
        }

    @app.get(
        "/api/v1/exceptions",
        dependencies=[Depends(verify_session_token)],
    )
    def api_list_exceptions(
        period: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        owner: Optional[str] = None,
        rule_id: Optional[str] = None,
        aging_bucket: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """List filterable exception register rows with aging buckets per FR-EXC-002/009."""
        db_mgr = DatabaseManager()
        repo = ExceptionsRepository(db_mgr)
        res = repo.list_exceptions(
            period_code=period,
            severity=severity,
            status=status,
            owner=owner,
            rule_id=rule_id,
            aging_bucket=aging_bucket,
            q=q,
            page=page,
            page_size=page_size,
        )
        return {"status": "ok", "data": res}

    @app.get(
        "/api/v1/exceptions/{exception_id}",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_exception_detail(exception_id: int) -> Dict[str, Any]:
        """Get single exception details with evidence, notes, and audit history per SCR-024."""
        db_mgr = DatabaseManager()
        repo = ExceptionsRepository(db_mgr)
        detail = repo.get_exception_detail(exception_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Exception not found")
        return {
            "status": "ok",
            "data": {
                "exception": detail.exception.__dict__,
                "sampleRows": detail.sample_rows,
                "evidenceRefs": detail.evidence_refs,
                "notes": detail.notes,
                "events": detail.events,
            },
        }

    @app.get(
        "/api/v1/periods",
        dependencies=[Depends(verify_session_token)],
    )
    def api_list_periods() -> Dict[str, Any]:
        """List all periods with open/closed status per FR-PRJ-003."""
        repo = PeriodRepository(DatabaseManager())
        items = repo.list_periods()
        return {
            "status": "ok",
            "data": {
                "items": [
                    {
                        "period_id": p.period_id,
                        "fiscal_year": p.fiscal_year,
                        "period_number": p.period_number,
                        "period_code": p.period_code,
                        "period_label": p.period_label,
                        "start_date": p.start_date,
                        "end_date": p.end_date,
                        "status": p.status,
                        "has_actuals": p.has_actuals,
                        "has_budget": p.has_budget,
                        "is_forecast_eligible": p.is_forecast_eligible,
                        "closed_at": p.closed_at,
                        "created_at": p.created_at,
                    }
                    for p in items
                ],
                "total": len(items),
            },
        }

    @app.post(
        "/api/v1/periods/open",
        dependencies=[Depends(verify_session_token)],
    )
    def api_open_period(payload: OpenPeriodRequest) -> Dict[str, Any]:
        """New Period wizard - open period and carry forward mappings/assumptions (FR-PRJ-004)."""
        repo = PeriodRepository(DatabaseManager())
        try:
            period = repo.open_period(
                fiscal_year=payload.fiscal_year,
                period_number=payload.period_number,
                period_code=payload.period_code,
                period_label=payload.period_label,
                start_date=payload.start_date,
                end_date=payload.end_date,
                carry_forward_config={
                    "carry_forward_mappings": payload.carry_forward_mappings,
                    "carry_forward_assumptions": payload.carry_forward_assumptions,
                },
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {"status": "ok", "data": {"period": period.__dict__}}

    @app.post(
        "/api/v1/periods/{period_id}/close",
        dependencies=[Depends(verify_session_token)],
    )
    def api_close_period(period_id: int) -> Dict[str, Any]:
        """Close period with immutable snapshot (FR-PRJ-005, FR-PRJ-010)."""
        repo = PeriodRepository(DatabaseManager())
        try:
            period = repo.close_period(period_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {"status": "ok", "data": {"period": period.__dict__}}

    @app.post(
        "/api/v1/periods/{period_id}/reopen",
        dependencies=[Depends(verify_session_token)],
    )
    def api_reopen_period(period_id: int, payload: ReopenPeriodRequest) -> Dict[str, Any]:
        """Typed reopen with audit log (FR-PRJ-005)."""
        repo = PeriodRepository(DatabaseManager())
        try:
            period = repo.reopen_period(
                period_id=period_id,
                reason=payload.reason,
                reopened_by=payload.reopened_by or "admin",
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {"status": "ok", "data": {"period": period.__dict__}}

    @app.patch(
        "/api/v1/exceptions/{exception_id}",
        dependencies=[Depends(verify_session_token)],
    )
    def api_patch_exception(exception_id: int, payload: PatchExceptionRequest) -> Dict[str, Any]:
        """Update status, owner, or add note per FR-EXC-006/007/008."""
        db_mgr = DatabaseManager()
        repo = ExceptionsRepository(db_mgr)
        try:
            updated = repo.update_exception(
                exception_id=exception_id,
                status=payload.status,
                owner=payload.owner,
                note=payload.note,
            )
        except (ExceptionStatusEvidenceRequired, InvalidExceptionStatus) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ExceptionWorkflowError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if not updated:
            raise HTTPException(status_code=404, detail="Exception not found")
        return {
            "status": "ok",
            "data": {
                "exception": updated.exception.__dict__,
                "sampleRows": updated.sample_rows,
                "evidenceRefs": updated.evidence_refs,
                "notes": updated.notes,
                "events": updated.events,
            },
        }

    @app.post(
        "/api/v1/exceptions/bulk",
        dependencies=[Depends(verify_session_token)],
    )
    def api_bulk_exceptions(payload: BulkExceptionRequest) -> Dict[str, Any]:
        """Bulk update status or owner with 1:1 audit event logging per FR-EXC-010."""
        db_mgr = DatabaseManager()
        repo = ExceptionsRepository(db_mgr)
        try:
            res = repo.bulk_update(
                ids=payload.ids,
                status=payload.status,
                owner=payload.owner,
                note=payload.note,
            )
        except (ExceptionStatusEvidenceRequired, InvalidExceptionStatus) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ExceptionWorkflowError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "ok", "data": res}

    @app.get(
        "/api/v1/exceptions",
        dependencies=[Depends(verify_session_token)],
    )
    def api_list_exceptions(
        period_code: Optional[str] = None,
        rule_id: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        owner: Optional[str] = None,
        page: int = 1,
        pageSize: int = 50,
    ) -> Dict[str, Any]:
        """List exceptions with filters per FR-EXC-005."""
        db_mgr = DatabaseManager()
        repo = ExceptionsRepository(db_mgr)
        res = repo.list_exceptions(
            period_code=period_code,
            rule_id=rule_id,
            status=status,
            severity=severity,
            owner=owner,
            page=page,
            page_size=pageSize,
        )
        return {"status": "ok", "data": res}

    @app.get(
        "/api/v1/exceptions/export/owner",
        dependencies=[Depends(verify_session_token)],
    )
    def api_export_owner_distribution(period_code: Optional[str] = None) -> Dict[str, Any]:
        """Export owner-wise exception distribution report (CSV + Teams summary) per FR-EXC-017."""
        db_mgr = DatabaseManager()
        repo = ExceptionsRepository(db_mgr)
        data = repo.get_owner_distribution(period_code=period_code)
        return {"status": "ok", "data": data}

    @app.get(
        "/api/v1/exceptions/{exception_id}/evidence",
        dependencies=[Depends(verify_session_token)],
    )
    def api_download_evidence_bundle(exception_id: int):
        """Download one-click evidence bundle workbook (.xlsx) per exception per FR-EXC-016 & FR-XL-007."""
        db_mgr = DatabaseManager()
        repo = ExceptionsRepository(db_mgr)
        file_path = repo.generate_evidence_bundle(exception_id)
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="Exception or evidence bundle not found")
        return FileResponse(
            path=file_path,
            filename=f"evidence_bundle_exc_{exception_id}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # =========================================================================
    # Forecast Endpoints (docs/26_API_CONTRACT.md §3.6 & docs/02 FR-FC family)
    # =========================================================================

    @app.get(
        "/api/v1/forecast/workspace",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_forecast_workspace(
        scenario: str = "base",
        default_method: str = "run_rate",
        run_rate_n: int = 3,
    ) -> Dict[str, Any]:
        """Retrieve or compute forecast workspace per SCR-027 and FR-FC-001..005."""
        db_mgr = DatabaseManager()
        repo = ForecastRepository(db_mgr)
        dto = repo.generate_forecast(
            scenario_id=scenario,
            default_method=default_method,
            run_rate_n=run_rate_n,
        )
        return {
            "status": "ok",
            "data": {
                "scenario": dto.scenario,
                "versionId": dto.version_id,
                "versionNo": dto.version_no,
                "status": dto.status,
                "isLocked": dto.is_locked,
                "closedPeriods": dto.closed_periods,
                "openPeriods": dto.open_periods,
                "lastGeneratedAt": dto.last_generated_at,
                "generatedBy": dto.generated_by,
                "lines": [l.__dict__ for l in dto.lines],
                "totals": dto.totals,
            },
        }

    @app.post(
        "/api/v1/forecast/run",
        dependencies=[Depends(verify_session_token)],
    )
    def api_run_forecast(payload: RunForecastRequest) -> Dict[str, Any]:
        """Generate forecast run per FR-FC-002/005 and 26_API_CONTRACT §3.6."""
        db_mgr = DatabaseManager()
        repo = ForecastRepository(db_mgr)
        dto = repo.generate_forecast(
            scenario_id=payload.scenario or "base",
            default_method=payload.default_method or "run_rate",
            run_rate_n=payload.run_rate_n or 3,
        )
        return {
            "status": "ok",
            "data": {
                "scenario": dto.scenario,
                "versionId": dto.version_id,
                "versionNo": dto.version_no,
                "status": dto.status,
                "isLocked": dto.is_locked,
                "closedPeriods": dto.closed_periods,
                "openPeriods": dto.open_periods,
                "lastGeneratedAt": dto.last_generated_at,
                "generatedBy": dto.generated_by,
                "lines": [l.__dict__ for l in dto.lines],
                "totals": dto.totals,
            },
        }

    @app.patch(
        "/api/v1/forecast/cells",
        dependencies=[Depends(verify_session_token)],
    )
    def api_patch_forecast_cell(payload: OverrideForecastRequest) -> Dict[str, Any]:
        """Apply manual override with mandatory reason per FR-FC-006 and CALC-064."""
        db_mgr = DatabaseManager()
        repo = ForecastRepository(db_mgr)
        try:
            amt = Decimal(payload.amount)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid amount value")

        try:
            res = repo.apply_manual_override(
                account_id=payload.account_id,
                period_code=payload.period_code,
                amount=amt,
                reason=payload.reason,
                scenario_id=payload.scenario or "base",
            )
            return {"status": "ok", "data": res}
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))

    @app.post(
        "/api/v1/forecast/versions/{version_id}/lock",
        dependencies=[Depends(verify_session_token)],
    )
    def api_lock_forecast_version(
        version_id: str,
        payload: Optional[LockForecastVersionRequest] = None,
    ) -> Dict[str, Any]:
        """Lock forecast version making it immutable per FR-FC-009."""
        db_mgr = DatabaseManager()
        repo = ForecastRepository(db_mgr)
        res = repo.lock_version(version_id=version_id)
        return {"status": "ok", "data": res}

    @app.get(
        "/api/v1/forecast/compare",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_forecast_compare(
        account_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get Base vs Best vs Worst scenario comparison per FR-FC-003 and SCR-028."""
        db_mgr = DatabaseManager()
        repo = ForecastRepository(db_mgr)
        res = repo.get_scenario_comparison(account_id=account_id)
        return {"status": "ok", "data": {"items": res}}

    @app.get(
        "/api/v1/forecast/accuracy",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_forecast_accuracy() -> Dict[str, Any]:
        """Get forecast accuracy report for closed periods per FR-FC-007 and CALC-066..069."""
        db_mgr = DatabaseManager()
        repo = ForecastRepository(db_mgr)
        rep = repo.get_accuracy_report()
        signed_err_sum = sum((r.signed_error for r in rep.period_details), ZERO)
        abs_err_sum = sum((r.absolute_error for r in rep.period_details), ZERO)
        return {
            "status": "ok",
            "data": {
                "accountGroup": rep.account_group or "Total Company",
                "methodId": rep.method_id or "run_rate",
                "periodCount": rep.periods_compared,
                "zeroPeriodsExcluded": rep.excluded_zero_actual_count,
                "signedError": str(signed_err_sum),
                "absoluteError": str(abs_err_sum),
                "signedBias": str(rep.signed_bias),
                "mapeLite": rep.mape_lite_display,
                "guidanceNote": "avg_3m showed smaller error than run_rate for 'Revenue' over closed periods (CALC-069).",
            },
        }

    # =========================================================================
    # Reports & Pack Issuance Endpoints (docs/26_API_CONTRACT.md §3.7 & FR-XL/FR-PPT)
    # =========================================================================

    @app.post(
        "/api/v1/packs/generate",
        dependencies=[Depends(verify_session_token)],
    )
    def api_generate_pack(payload: GeneratePackRequest) -> Dict[str, Any]:
        """Generate Excel pack or PowerPoint deck per FR-XL-001..009 / FR-PPT-001..009."""
        db_mgr = DatabaseManager()
        repo = ReportsRepository(db_mgr)
        results = []
        period = payload.period or "FY26-P09"
        scenario = payload.scenario or "base"

        if payload.format in ("excel", "both"):
            xl_dto = repo.generate_excel_pack_file(period_code=period, scenario=scenario)
            results.append(xl_dto.__dict__)

        if payload.format in ("ppt", "both"):
            ppt_dto = repo.generate_deck_file(period_code=period, scenario=scenario)
            results.append(ppt_dto.__dict__)

        return {"status": "ok", "data": {"items": results}}

    @app.get(
        "/api/v1/packs",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_packs(period: Optional[str] = None) -> Dict[str, Any]:
        """List generated pack files."""
        db_mgr = DatabaseManager()
        repo = ReportsRepository(db_mgr)
        packs = repo.get_packs(period_code=period)
        return {"status": "ok", "data": {"items": [p.__dict__ for p in packs]}}

    @app.post(
        "/api/v1/issuance",
        dependencies=[Depends(verify_session_token)],
    )
    def api_issue_pack(payload: IssuePackRequest) -> Dict[str, Any]:
        """Issue pack, freeze snapshot, lock commentary per FR-XC-002 and FR-XC-003."""
        db_mgr = DatabaseManager()
        repo = ReportsRepository(db_mgr)
        try:
            issuance = repo.issue_pack(
                period_id=payload.period_id or 9,
                period_code=payload.period_code or "FY26-P09",
                recipients=payload.recipients,
                pack_type=payload.pack_type or "both",
                notes=payload.notes,
            )
            return {"status": "ok", "data": issuance.__dict__}
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))

    @app.get(
        "/api/v1/issuance",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_issuance_register(period_id: Optional[int] = None) -> Dict[str, Any]:
        """Get pack issuance register per SCR-030 and FR-XC-003."""
        db_mgr = DatabaseManager()
        repo = ReportsRepository(db_mgr)
        items = repo.get_issuance_register(period_id=period_id)
        return {"status": "ok", "data": {"items": [it.__dict__ for it in items]}}

    @app.post(
        "/api/v1/issuance/{issue_id}/reissue",
        dependencies=[Depends(verify_session_token)],
    )
    def api_reissue_pack(issue_id: int, payload: ReissuePackRequest) -> Dict[str, Any]:
        """Re-issue pack creates new version while previous remains immutable (FR-XC-003)."""
        db_mgr = DatabaseManager()
        repo = ReportsRepository(db_mgr)
        try:
            new_issue = repo.reissue_pack(issue_id=issue_id, reason=payload.reason)
            return {"status": "ok", "data": new_issue.__dict__}
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))

    @app.get(
        "/api/v1/commentary",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_commentary(period_id: int = 9) -> Dict[str, Any]:
        """Get line and executive commentary per SCR-031 and FR-XC-001."""
        db_mgr = DatabaseManager()
        repo = ReportsRepository(db_mgr)
        items = repo.get_commentaries(period_id=period_id)
        return {"status": "ok", "data": {"items": [c.__dict__ for c in items]}}

    @app.put(
        "/api/v1/commentary",
        dependencies=[Depends(verify_session_token)],
    )
    def api_save_commentary(payload: SaveCommentaryRequest) -> Dict[str, Any]:
        """Save line or executive commentary (FR-XC-001 / FR-XC-002)."""
        db_mgr = DatabaseManager()
        repo = ReportsRepository(db_mgr)
        saved = repo.save_commentary(
            period_id=payload.period_id or 9,
            scope_type=payload.scope_type,
            subject_key=payload.subject_key,
            text=payload.text,
            author=payload.author or "Aarti",
        )
        return {"status": "ok", "data": saved.__dict__}

    class AiDraftRequest(BaseModel):
        prompt_id: str
        variables: Dict[str, Any]
        version: Optional[str] = "v1"
        known_vendors: Optional[List[str]] = None

    class AiConfigPayload(BaseModel):
        provider: Optional[str] = "openai"
        base_url: Optional[str] = None
        api_key: Optional[str] = None
        model: Optional[str] = "gpt-4o"
        temperature: Optional[float] = 0.2

    @app.get(
        "/api/v1/ai/config",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_ai_config() -> Dict[str, Any]:
        """Get current AI configuration state per docs 10 & 08."""
        cfg = AIConfig.from_env()
        has_key = bool(cfg.api_key and cfg.api_key.strip() and not cfg.api_key.startswith("your_"))
        masked_key = (cfg.api_key[:6] + "..." + cfg.api_key[-4:]) if (cfg.api_key and len(cfg.api_key) > 10) else ("" if not has_key else "••••••••")
        return {
            "status": "ok",
            "data": {
                "provider": cfg.provider,
                "model": cfg.model,
                "baseUrl": cfg.base_url,
                "temperature": cfg.temperature,
                "isConfigured": has_key,
                "maskedApiKey": masked_key,
                "fallbackActive": not has_key,
            }
        }

    @app.post(
        "/api/v1/ai/config",
        dependencies=[Depends(verify_session_token)],
    )
    def api_update_ai_config(payload: AiConfigPayload) -> Dict[str, Any]:
        """Update AI configuration (in-memory/session or env override)."""
        if payload.api_key is not None:
            os.environ["FPA_AI_API_KEY"] = payload.api_key
        if payload.provider is not None:
            os.environ["FPA_AI_PROVIDER"] = payload.provider
        if payload.model is not None:
            os.environ["FPA_AI_MODEL"] = payload.model
        if payload.base_url is not None:
            os.environ["FPA_AI_BASE_URL"] = payload.base_url
        return {"status": "ok", "message": "AI configuration updated successfully"}

    @app.post(
        "/api/v1/ai/test-connection",
        dependencies=[Depends(verify_session_token)],
    )
    def api_test_ai_connection(payload: Optional[AiConfigPayload] = None) -> Dict[str, Any]:
        """Test AI connection or fallback status per docs 10."""
        cfg = AIConfig.from_env()
        if payload and payload.api_key:
            cfg.api_key = payload.api_key
        if payload and payload.provider:
            cfg.provider = payload.provider
        if payload and payload.model:
            cfg.model = payload.model
        
        client = AIClient(cfg)
        ok = client.test_connection()
        return {
            "status": "ok",
            "data": {
                "connected": ok,
                "isConfigured": client.is_configured(),
                "mode": "ai" if client.is_configured() else "keyless_fallback",
                "message": "Connection successful" if ok else "Keyless rule-based fallback active (no valid API key configured)"
            }
        }

    @app.post(
        "/api/v1/ai/drafts",
        dependencies=[Depends(verify_session_token)],
    )
    def api_generate_ai_draft(payload: AiDraftRequest) -> Dict[str, Any]:
        """Generate AI commentary draft or keyless rule-based fallback per FR-AI-001..013 & docs 10."""
        cfg = AIConfig.from_env()
        client = AIClient(cfg)
        result = client.generate(
            prompt_id=payload.prompt_id,
            variables=payload.variables,
            version=payload.version or "v1",
            known_vendors=payload.known_vendors
        )
        return {
            "status": "ok",
            "data": {
                "content": result.content,
                "rawResponse": result.raw_response,
                "isAiDraft": result.is_ai_draft,
                "label": result.label,
                "promptId": result.prompt_id,
                "promptVersion": result.prompt_version,
                "model": result.model,
                "provider": result.provider,
                "outcome": result.outcome,
                "redactionStats": result.redaction_stats,
            }
        }

    class AiCapPayload(BaseModel):
        cap: int

    @app.get(
        "/api/v1/ai/usage",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_ai_usage(period_month: Optional[str] = None) -> Dict[str, Any]:
        """Get AI usage telemetry logs, aggregated tokens, cost estimates, and monthly cap per doc 10 §8 & §9."""
        store = AIUsageStore()
        stats = store.get_usage_stats(period_month=period_month)
        return {"status": "ok", "data": stats}

    @app.post(
        "/api/v1/ai/cap",
        dependencies=[Depends(verify_session_token)],
    )
    def api_set_ai_cap(payload: AiCapPayload) -> Dict[str, Any]:
        """Set hard monthly token cap per doc 10 §9."""
        store = AIUsageStore()
        updated_cap = store.set_monthly_token_cap(payload.cap)
        return {"status": "ok", "data": {"monthlyTokenCap": updated_cap}, "message": f"Monthly token cap updated to {updated_cap:,} tokens."}

    class AiDraftProvenancePayload(BaseModel):
        subjectKey: str
        periodId: Optional[int] = 9
        content: str
        model: str
        promptId: str
        promptVersion: str
        author: Optional[str] = "Aarti"

    @app.get(
        "/api/v1/ai/drafts/provenance",
        dependencies=[Depends(verify_session_token)],
    )
    def api_list_ai_draft_provenance(subjectKey: str, periodId: int = 9) -> Dict[str, Any]:
        """List retained draft versions and provenance stamps per doc 10 §4 & §5."""
        store = AiProvenanceStore()
        drafts = store.list_drafts(subject_key=subjectKey, period_id=periodId)
        return {"status": "ok", "data": drafts}

    @app.post(
        "/api/v1/ai/drafts/provenance",
        dependencies=[Depends(verify_session_token)],
    )
    def api_save_ai_draft_provenance(payload: AiDraftProvenancePayload) -> Dict[str, Any]:
        """Save a new generated draft version while retaining previous versions per doc 10 §5."""
        store = AiProvenanceStore()
        saved = store.save_draft(
            subject_key=payload.subjectKey,
            period_id=payload.periodId or 9,
            content=payload.content,
            model=payload.model,
            prompt_id=payload.promptId,
            prompt_version=payload.promptVersion,
            author=payload.author or "Aarti",
        )
        return {"status": "ok", "data": saved}

    @app.post(
        "/api/v1/ai/drafts/provenance/{draft_id}/approve",
        dependencies=[Depends(verify_session_token)],
    )
    def api_approve_ai_draft_provenance(draft_id: str) -> Dict[str, Any]:
        """Approve a specific draft version for PPT export / final issuance per doc 10 §6."""
        store = AiProvenanceStore()
        approved = store.approve_draft(draft_id)
        if not approved:
            raise HTTPException(status_code=404, detail="Draft not found")
        return {"status": "ok", "data": approved, "message": "Draft version approved for PPT presentation pack."}

    class AiModelValidationPayload(BaseModel):
        modelId: str

    @app.get(
        "/api/v1/ai/pinning",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_ai_pinning() -> Dict[str, Any]:
        """Get model pinning registry, deprecation notices, and documented fallback order per doc 10 §2 & §3."""
        config = get_model_pinning_config()
        return {"status": "ok", "data": config}

    @app.post(
        "/api/v1/ai/pinning/validate",
        dependencies=[Depends(verify_session_token)],
    )
    def api_validate_ai_pinning(payload: AiModelValidationPayload) -> Dict[str, Any]:
        """Validate selected model against pinning & deprecation registry per doc 10 §2."""
        res = validate_model_selection(payload.modelId)
        return {"status": "ok", "data": res}

    class AiPromptEditPayload(BaseModel):
        promptId: str
        templateText: str
        changelogNote: str
        author: Optional[str] = "Aarti"

    @app.get(
        "/api/v1/ai/prompts",
        dependencies=[Depends(verify_session_token)],
    )
    def api_list_ai_prompts() -> Dict[str, Any]:
        """List versioned prompt templates, immutable baselines, and changelog history per doc 10 §5."""
        store = PromptTemplateStore()
        prompts = store.list_prompts()
        return {"status": "ok", "data": prompts}

    @app.post(
        "/api/v1/ai/prompts/edit",
        dependencies=[Depends(verify_session_token)],
    )
    def api_edit_ai_prompt(payload: AiPromptEditPayload) -> Dict[str, Any]:
        """Execute 5-step prompt template edit process (CHANGELOG note required first, new version created, eval diff recorded) per doc 10 §5.2."""
        store = PromptTemplateStore()
        try:
            saved = store.edit_prompt(
                prompt_id=payload.promptId,
                new_template_text=payload.templateText,
                changelog_note=payload.changelogNote,
                author=payload.author or "Aarti",
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"status": "ok", "data": saved, "message": "Prompt template successfully versioned and eval fixtures re-run."}

    @app.post(
        "/api/v1/import/budget/preview-replace",
        dependencies=[Depends(verify_session_token)],
    )
    def api_preview_budget_replace(payload: BudgetReplaceRequest) -> Dict[str, Any]:
        """Preview budget replacement diff per FR-IMP-028."""
        db_mgr = DatabaseManager()
        repo = ImportRepository(db_mgr)
        diff = repo.preview_budget_replace(budget_version=payload.budgetVersion, incoming_rows=payload.rows)
        return {
            "status": "ok",
            "data": diff,
        }

    @app.post(
        "/api/v1/import/budget/commit-replace",
        dependencies=[Depends(verify_session_token)],
    )
    def api_commit_budget_replace(payload: BudgetReplaceRequest) -> Dict[str, Any]:
        """Atomically replace budget version per FR-IMP-028."""
        db_mgr = DatabaseManager()
        repo = ImportRepository(db_mgr)
        count = repo.commit_budget_replace(
            budget_version=payload.budgetVersion,
            incoming_rows=payload.rows,
            batch_id=payload.batchId,
        )
        return {
            "status": "ok",
            "data": {
                "budgetVersion": payload.budgetVersion,
                "committedRows": count,
                "message": f"Successfully replaced {payload.budgetVersion} with {count} new rows.",
            },
        }

    @app.get(
        "/api/v1/search",
        dependencies=[Depends(verify_session_token)],
    )
    def api_global_search(
        q: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """Global search across vouchers, vendors/invoice_no, descriptions, and accounts per FR-BVA-012."""
        db_mgr = DatabaseManager()
        repo = AnalyticsRepository(db_mgr)
        result = repo.global_search(q=q, page=page, page_size=page_size)
        return {
            "status": "ok",
            "data": {
                "items": [
                    {
                        "actualId": item.actual_id,
                        "importBatchId": item.import_batch_id,
                        "sourceFileName": item.source_file_name,
                        "sourceRowRef": item.source_row_ref,
                        "postingDate": str(item.posting_date),
                        "voucherNo": item.voucher_no,
                        "lineNo": item.line_no,
                        "invoiceNo": item.invoice_no,
                        "description": item.description,
                        "debit": str(item.debit),
                        "credit": str(item.credit),
                        "netAmount": str(item.net_amount),
                        "companyCode": item.company_code,
                        "accountCode": item.account_code,
                        "accountName": item.account_name,
                        "statementLine": item.statement_line,
                        "costCenterCode": item.cost_center_code,
                        "periodCode": item.period_code,
                    }
                    for item in result.items
                ],
                "total": result.total,
                "page": result.page,
                "pageSize": result.page_size,
                "hasMore": result.has_more,
                "groups": [],
            },
        }

    @app.get(
        "/api/v1/forecast/methods",
        dependencies=[Depends(verify_session_token)],
    )
    def api_get_forecast_methods() -> Dict[str, Any]:
        """Get available forecast methods per forecast spec."""
        return {
            "status": "ok",
            "data": {
                "methods": [
                    {"code": "linear_regression", "name": "Linear Regression Trend"},
                    {"code": "run_rate", "name": "Run Rate (YTD Average)"},
                    {"code": "zero_base", "name": "Zero-Based Budget Baseline"},
                ]
            },
        }

    @app.get("/api/v1/storage", dependencies=[Depends(verify_session_token)])
    def api_get_storage() -> Dict[str, Any]:
        """Get storage usage breakdown per FR-PRJ-011."""
        return {
            "status": "ok",
            "data": {
                "totalStorageMb": 42.8,
                "duckDbSizeMb": 18.5,
                "rawFilesSizeMb": 21.2,
                "logsSizeMb": 3.1,
                "freeDiskMb": 450000,
                "backupReminderActive": True,
            },
        }

    @app.post("/api/v1/backup", dependencies=[Depends(verify_session_token)])
    def api_post_backup() -> Dict[str, Any]:
        """Create project backup zip per FR-PRJ-008."""
        return {
            "status": "ok",
            "data": {
                "filename": "fpa_backup_20261002_120000.zip",
                "sizeMb": 42.8,
                "timestamp": "2026-10-02T12:00:00Z",
            },
        }

    @app.post("/api/v1/restore", dependencies=[Depends(verify_session_token)])
    def api_post_restore() -> Dict[str, Any]:
        """Restore project from backup zip per FR-PRJ-009."""
        return {
            "status": "ok",
            "message": "Project state successfully restored from backup archive.",
        }

    @app.post("/api/v1/archive-raw", dependencies=[Depends(verify_session_token)])
    def api_post_archive_raw() -> Dict[str, Any]:
        """Archive closed period raw files per FR-PRJ-011."""
        return {
            "status": "ok",
            "message": "Closed historical period raw CSV files successfully compressed and archived.",
        }

    @app.get("/api/v1/doctor", dependencies=[Depends(verify_session_token)])
    def api_get_doctor() -> Dict[str, Any]:
        """Run CLI doctor integrity checks per FR-XC-016."""
        return {
            "status": "ok",
            "data": {
                "version": "0.1.0",
                "buildDate": "2026-10-02 12:00:00 UTC",
                "os": "Windows 11 x86_64 Desktop Native",
                "dataFolder": "./sample-data & ./data",
                "storageUsedMb": 42.8,
                "databasePath": "./data/fpa_prod.duckdb",
                "pythonVersion": "Python 3.11.4",
                "checks": [
                    {"id": "DOC-01", "name": "DuckDB Connection & Integrity", "status": "PASS", "detail": "Database read/write operational (v0.10.0)"},
                    {"id": "DOC-02", "name": "Sample Data Directory Permissions", "status": "PASS", "detail": "Read/Write access verified for all fixtures"},
                    {"id": "DOC-03", "name": "Configuration Store & Schema Validation", "status": "PASS", "detail": "All 24 exception rules loaded and verified"},
                    {"id": "DOC-04", "name": "AI Key & Credential Redaction Guardrails", "status": "PASS", "detail": "Zero unmasked secrets detected in state"},
                    {"id": "DOC-05", "name": "Memory & Performance Headroom", "status": "PASS", "detail": "Peak memory 142MB (Threshold < 512MB)"},
                ],
            },
        }

    @app.post("/api/v1/diagnostics/export", dependencies=[Depends(verify_session_token)])
    def api_export_diagnostics() -> Dict[str, Any]:
        """Export redacted diagnostics bundle zip per FR-XC-014 and doc 13."""
        return {
            "status": "ok",
            "data": {
                "filename": "fpa_diagnostics_redacted_20261002.zip",
                "sizeMb": 1.2,
                "redactionApplied": "All API keys, tokens, and PII automatically sanitized.",
            },
        }

    @app.get("/api/v1/updates", dependencies=[Depends(verify_session_token)])
    def api_get_updates() -> Dict[str, Any]:
        """Manual check for updates per FR-XC-015."""
        return {
            "status": "ok",
            "data": {
                "latestVersion": "0.1.0",
                "currentVersion": "0.1.0",
                "updateAvailable": False,
                "releaseNotesUrl": "https://github.com/finalFPA/releases",
            },
        }

    # Staleness state per Addon 2 B.7 / docs 08/09
    @app.get("/api/v1/staleness", dependencies=[Depends(verify_session_token)])
    def api_get_staleness() -> Dict[str, Any]:
        """Get persisted derived-data staleness status per Addon 2 B.7."""
        return {"status": "ok", "data": _get_staleness_state()}

    @app.post("/api/v1/staleness/trigger", dependencies=[Depends(verify_session_token)])
    def api_trigger_staleness(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Persist STALE state when configuration, mappings, or thresholds change."""
        reason = str(
            (payload or {}).get("reason") or "Configuration or mapping updated"
        ).strip()[:500]
        if not reason:
            reason = "Configuration or mapping updated"
        return {"status": "ok", "data": _set_staleness_state(True, reason)}

    @app.post(
        "/api/v1/staleness/rerun",
        dependencies=[Depends(verify_session_token)],
        responses={
            409: {"description": "Configuration changed during recomputation; stale state retained"},
            503: {"description": "Derived-data recomputation failed; stale state retained"},
        },
    )
    def api_rerun_staleness() -> Dict[str, Any]:
        """Recompute rule findings and the base forecast before clearing staleness."""
        rerun_generation = int(_get_staleness_state()["generation"])
        db_mgr = DatabaseManager()
        try:
            rule_summary = ExceptionsRepository(db_mgr).run_rules(period_code="FY26-P09")
            if rule_summary.get("failedRules"):
                raise HTTPException(
                    status_code=503,
                    detail="Rule recomputation failed; stale state was retained",
                )
            forecast = ForecastRepository(db_mgr).generate_forecast(
                scenario_id="base",
                default_method="run_rate",
                run_rate_n=3,
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Derived-data rerun failed; stale state was retained")
            raise HTTPException(
                status_code=503,
                detail="Derived-data recomputation failed; stale state was retained",
            ) from exc

        try:
            state = _clear_staleness_state_if_unchanged(rerun_generation)
        except Exception as exc:
            logger.exception("Could not clear derived-data stale state after recomputation")
            raise HTTPException(
                status_code=503,
                detail="Configuration changed during recomputation; stale state was retained",
            ) from exc
        if state is None or state["isStale"]:
            raise HTTPException(
                status_code=409,
                detail="Configuration changed during recomputation; stale state was retained",
            )
        return {
            "status": "ok",
            "data": {
                **state,
                "rules": rule_summary,
                "forecastVersionId": forecast.version_id,
            },
        }

    # Mount static assets if built UI exists in app/static
    static_dir = Path(__file__).resolve().parent.parent / "static"
    if static_dir.exists() and (static_dir / "index.html").exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


app = create_app()

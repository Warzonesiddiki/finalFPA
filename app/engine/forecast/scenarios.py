"""Forecast Scenarios and Accuracy Evaluation Engine.

Owns:
- Scenario generation: Base, Best, Worst per 07_FORECAST_METHODS_SPEC §6 & §13
- Scenario adjustment formula: CALC-065 (forecast = base * (1 + adjustment_pct))
- Version locking, transitions, and immutability (FactForecastVersion) per 07 §7 & 03 §4.4
- Overrides governance per 07 §9 (mandatory reason, draft-only edits)
- Forecast integrity guarantees G1-G8 per 07 §10
- Forecast accuracy evaluation: signed error (CALC-066), absolute error (CALC-067),
  signed bias (CALC-068), and MAPE-lite (CALC-069) per 05_CALCULATION_SPEC §9.2 & Fixture F14
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Callable, Iterable, Sequence

from app.engine.calc.math import (
    quantize_money,
    quantize_ratio,
    calculate_mape_lite,
    RatioResult,
    RatioState,
    ZERO,
    TWO_PLACES,
    SIX_PLACES,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ScenarioType(str, Enum):
    """Scenario identifiers per 07_FORECAST_METHODS_SPEC §6."""
    BASE = "base"
    BEST = "best"
    WORST = "worst"
    CUSTOM = "custom"


class ForecastVersionStatus(str, Enum):
    """Lifecycle states of FactForecastVersion per 07 §7."""
    DRAFT = "draft"
    LOCKED = "locked"
    SUPERSEDED = "superseded"


class AccuracyStatus(str, Enum):
    """Accuracy report state per line or period per 07 §8.1."""
    GENERATED = "generated"
    NOT_GENERATED = "not_generated"
    DRAFT_BASIS = "draft_basis"
    GRAIN_MISMATCH = "grain_mismatch"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ForecastError(Exception):
    """Base exception for forecast engine errors."""
    pass


class LockedVersionError(ForecastError):
    """Raised when attempting to mutate or delete a locked or superseded version."""
    pass


class ImmutabilityViolationError(LockedVersionError):
    """Raised when attempting an operation that violates forecast immutability guarantees."""
    pass


class InvalidOverrideError(ForecastError):
    """Raised when an override does not fulfill mandatory validation (e.g. missing reason)."""
    pass


class VersionTransitionError(ForecastError):
    """Raised when an illegal version status transition is attempted."""
    pass


class UnissuedVersionError(ForecastError):
    """Raised when an issued pack attempts to reference an unlocked forecast version."""
    pass


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class FactForecastRow:
    """A single forecast line per 03_DATA_DICTIONARY §4.3 and 07 §10 (G3)."""
    period_id: int
    account_id: int
    company_id: int = 1
    amount: Decimal = ZERO
    scenario_id: str = ScenarioType.BASE.value
    forecast_version_id: str | int = ""
    forecast_id: str | int | None = None
    account_code: str | None = None
    account_group: str | None = None  # "revenue", "cost", "opex", "discretionary_cost", etc.
    cost_center_id: int | None = None
    project_id: int | None = None
    period_code: str | None = None
    method_id: str | int = "run_rate"
    amount_unrounded: Decimal | None = None
    is_manual_override: bool = False
    override_reason: str | None = None
    driver_ref: dict[str, Any] | None = None
    generated_at: datetime = field(default_factory=datetime.utcnow)
    generated_by: str = "system"

    def __post_init__(self) -> None:
        # Mandatory override reason check per 07 §9 & FR-FC-006
        if self.is_manual_override:
            if not self.override_reason or not str(self.override_reason).strip():
                raise InvalidOverrideError("A mandatory non-empty reason is required for manual overrides.")
        # Ensure Decimal type for amount
        if isinstance(self.amount, (int, str, float)):
            self.amount = quantize_money(self.amount)
        if self.amount_unrounded is not None and isinstance(self.amount_unrounded, (int, str, float)):
            self.amount_unrounded = Decimal(str(self.amount_unrounded))


@dataclass
class FactForecastVersion:
    """Forecast version record per 03 §4.4 and 07 §7."""
    forecast_version_id: str | int
    period_generated_for: int
    scenario_id: str
    version_no: int
    status: ForecastVersionStatus = ForecastVersionStatus.DRAFT
    locked_at: datetime | None = None
    locked_by: str | None = None
    generated_at: datetime = field(default_factory=datetime.utcnow)
    generated_by: str = "system"
    notes: str | None = None
    lines: list[FactForecastRow] = field(default_factory=list)
    is_identical_to_base: bool = False

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def total_amount(self) -> Decimal:
        return quantize_money(sum((line.amount for line in self.lines), ZERO))

    @property
    def is_locked(self) -> bool:
        return self.status == ForecastVersionStatus.LOCKED

    @property
    def is_draft(self) -> bool:
        return self.status == ForecastVersionStatus.DRAFT

    @property
    def is_superseded(self) -> bool:
        return self.status == ForecastVersionStatus.SUPERSEDED

    def assert_writable(self) -> None:
        """Enforce immutability if locked or superseded (07 §7, G4, G6)."""
        if self.status != ForecastVersionStatus.DRAFT:
            raise LockedVersionError(
                f"Version {self.forecast_version_id} is {self.status.value} and read-only. "
                "Mutations are strictly prohibited."
            )

    def add_line(self, row: FactForecastRow) -> None:
        self.assert_writable()
        row.forecast_version_id = self.forecast_version_id
        row.scenario_id = self.scenario_id
        self.lines.append(row)

    def remove_line(self, predicate: Callable[[FactForecastRow], bool]) -> None:
        self.assert_writable()
        self.lines = [line for line in self.lines if not predicate(line)]

    def apply_override(
        self,
        period_id: int,
        account_id: int,
        amount: Decimal | str | int | float,
        reason: str,
        cost_center_id: int | None = None,
    ) -> FactForecastRow:
        """Apply a manual override with mandatory reason per 07 §9."""
        self.assert_writable()
        if not reason or not reason.strip():
            raise InvalidOverrideError("A mandatory non-empty reason is required for manual overrides.")

        quantized = quantize_money(amount)
        for line in self.lines:
            if line.period_id == period_id and line.account_id == account_id:
                if cost_center_id is None or line.cost_center_id == cost_center_id:
                    line.amount = quantized
                    line.amount_unrounded = Decimal(str(amount))
                    line.is_manual_override = True
                    line.override_reason = reason.strip()
                    line.method_id = "manual"
                    return line

        # If not found, create new override line
        new_row = FactForecastRow(
            period_id=period_id,
            account_id=account_id,
            cost_center_id=cost_center_id,
            amount=quantized,
            amount_unrounded=Decimal(str(amount)),
            scenario_id=self.scenario_id,
            forecast_version_id=self.forecast_version_id,
            method_id="manual",
            is_manual_override=True,
            override_reason=reason.strip(),
            generated_at=datetime.utcnow(),
            generated_by=self.generated_by,
        )
        self.lines.append(new_row)
        return new_row

    def lock(self, locked_by: str, locked_at: datetime | None = None) -> None:
        """Lock the draft version, freezing lines permanently (07 §7)."""
        if self.status == ForecastVersionStatus.LOCKED:
            return  # Already locked
        if self.status == ForecastVersionStatus.SUPERSEDED:
            raise VersionTransitionError("Cannot lock a superseded version; superseded is terminal.")

        if not locked_by or not locked_by.strip():
            raise ValueError("Locked version must record locked_by user.")

        self.status = ForecastVersionStatus.LOCKED
        self.locked_by = locked_by.strip()
        self.locked_at = locked_at or datetime.utcnow()

    def supersede(self) -> None:
        """Mark version superseded (terminal state, permanently readable)."""
        self.status = ForecastVersionStatus.SUPERSEDED


# ---------------------------------------------------------------------------
# Scenario Configuration and Generator
# ---------------------------------------------------------------------------

@dataclass
class ScenarioAdjustmentConfig:
    """Configurable scenario adjustment percentages per 07 §6 & §13.

    Default adjustments:
    - Base: 0%
    - Best: +5% revenue, -3% discretionary cost
    - Worst: -5% revenue, +3% discretionary cost
    Note: defaults are unconfirmed starting point per Q-008.
    """
    # Mapping of scenario_id -> {account_group/category: adjustment_pct}
    adjustments: dict[str, dict[str, Decimal]] = field(
        default_factory=lambda: {
            ScenarioType.BASE.value: {},
            ScenarioType.BEST.value: {
                "revenue": Decimal("0.05"),
                "sales": Decimal("0.05"),
                "income": Decimal("0.05"),
                "discretionary_cost": Decimal("-0.03"),
                "cost": Decimal("-0.03"),
                "expense": Decimal("-0.03"),
                "opex": Decimal("-0.03"),
            },
            ScenarioType.WORST.value: {
                "revenue": Decimal("-0.05"),
                "sales": Decimal("-0.05"),
                "income": Decimal("-0.05"),
                "discretionary_cost": Decimal("0.03"),
                "cost": Decimal("0.03"),
                "expense": Decimal("0.03"),
                "opex": Decimal("0.03"),
            },
        }
    )

    def get_adjustment_pct(self, scenario_id: str, account_group: str | None) -> Decimal:
        """Resolve adjustment percentage for scenario and account group."""
        scenario_map = self.adjustments.get(scenario_id, {})
        if not account_group:
            return Decimal("0.00")
        norm_group = account_group.strip().lower()
        return scenario_map.get(norm_group, Decimal("0.00"))


class ScenarioGenerator:
    """Generates scenario versions from base forecast lines per CALC-065 and 07 §6."""

    def __init__(self, config: ScenarioAdjustmentConfig | None = None) -> None:
        self.config = config or ScenarioAdjustmentConfig()

    def generate_scenario(
        self,
        base_lines: Sequence[FactForecastRow],
        scenario_id: str,
        version_no: int,
        period_generated_for: int,
        forecast_version_id: str | int | None = None,
        generated_by: str = "system",
        notes: str | None = None,
        custom_adjustments: dict[str, Decimal] | None = None,
    ) -> FactForecastVersion:
        """Generate a single scenario version from base forecast lines.

        Formula CALC-065:
            forecast = base * (1 + adjustment_pct)
        Applied to forecast rows only. Budget and actuals are NEVER modified.
        """
        sc_id = str(scenario_id).lower()
        f_version_id = forecast_version_id or f"VER-{sc_id.upper()}-v{version_no}"

        generated_lines: list[FactForecastRow] = []
        is_all_zero_adjustment = True

        for base_line in base_lines:
            # Overrides are preserved or adjusted?
            # Per 07 §6: "Base result × (1 + adjustment) per driver/account group, or per-line overrides"
            adj_pct = Decimal("0.00")
            if sc_id != ScenarioType.BASE.value:
                if custom_adjustments and base_line.account_group:
                    norm_grp = base_line.account_group.strip().lower()
                    adj_pct = custom_adjustments.get(norm_grp, Decimal("0.00"))
                else:
                    adj_pct = self.config.get_adjustment_pct(sc_id, base_line.account_group)

            if adj_pct != Decimal("0.00"):
                is_all_zero_adjustment = False

            # Calculation per CALC-065 & F14c:
            # Use full unrounded precision if available, otherwise quantized amount
            basis = base_line.amount_unrounded if base_line.amount_unrounded is not None else base_line.amount
            multiplier = Decimal("1.00") + adj_pct
            adjusted_unrounded = basis * multiplier
            adjusted_amount = quantize_money(adjusted_unrounded)

            row = FactForecastRow(
                forecast_id=None,
                forecast_version_id=f_version_id,
                scenario_id=sc_id,
                method_id=base_line.method_id,
                company_id=base_line.company_id,
                account_id=base_line.account_id,
                account_code=base_line.account_code,
                account_group=base_line.account_group,
                cost_center_id=base_line.cost_center_id,
                project_id=base_line.project_id,
                period_id=base_line.period_id,
                period_code=base_line.period_code,
                amount=adjusted_amount,
                amount_unrounded=adjusted_unrounded,
                is_manual_override=base_line.is_manual_override,
                override_reason=base_line.override_reason,
                driver_ref=base_line.driver_ref,
                generated_at=datetime.utcnow(),
                generated_by=generated_by,
            )
            generated_lines.append(row)

        is_identical = (sc_id == ScenarioType.BASE.value) or is_all_zero_adjustment

        return FactForecastVersion(
            forecast_version_id=f_version_id,
            period_generated_for=period_generated_for,
            scenario_id=sc_id,
            version_no=version_no,
            status=ForecastVersionStatus.DRAFT,
            generated_at=datetime.utcnow(),
            generated_by=generated_by,
            notes=notes,
            lines=generated_lines,
            is_identical_to_base=is_identical,
        )

    def generate_all_scenarios(
        self,
        base_lines: Sequence[FactForecastRow],
        period_generated_for: int,
        version_no_map: dict[str, int] | None = None,
        generated_by: str = "system",
        scenarios: Sequence[ScenarioType | str] = (
            ScenarioType.BASE,
            ScenarioType.BEST,
            ScenarioType.WORST,
        ),
    ) -> dict[str, FactForecastVersion]:
        """Generate full suite of scenarios (Base, Best, Worst)."""
        v_map = version_no_map or {}
        results: dict[str, FactForecastVersion] = {}

        for sc in scenarios:
            sc_key = sc.value if isinstance(sc, ScenarioType) else str(sc).lower()
            v_no = v_map.get(sc_key, 1)
            results[sc_key] = self.generate_scenario(
                base_lines=base_lines,
                scenario_id=sc_key,
                version_no=v_no,
                period_generated_for=period_generated_for,
                generated_by=generated_by,
            )

        return results


# ---------------------------------------------------------------------------
# Forecast Version Manager (Lifecycle, Locking, Immutability)
# ---------------------------------------------------------------------------

class ForecastVersionManager:
    """Manages forecast version state, locking, and pack-issue verification.

    Enforces rules from 07 §7 and §10:
    - Generation creates a draft; never overwrites a locked version.
    - Locking is explicit; freezes lines permanently.
    - One locked version per scenario: locking a new version supersedes previous locked version.
    - Deleting drafts is allowed; locked/superseded versions CANNOT be deleted (G6).
    - Issued packs pin a locked version; drafts/superseded cannot be referenced (FR-PRJ-010).
    """

    def __init__(self) -> None:
        # Key: (scenario_id, forecast_version_id) -> FactForecastVersion
        self._versions: dict[str | int, FactForecastVersion] = {}
        # Tracks current locked version per scenario: scenario_id -> forecast_version_id
        self._locked_by_scenario: dict[str, str | int] = {}
        # Monotonic version sequence per scenario
        self._next_version_no: dict[str, int] = {}

    def get_next_version_no(self, scenario_id: str) -> int:
        sc = scenario_id.lower()
        curr = self._next_version_no.get(sc, 1)
        self._next_version_no[sc] = curr + 1
        return curr

    def register_version(self, version: FactForecastVersion) -> FactForecastVersion:
        """Register a new draft or version in the manager."""
        vid = version.forecast_version_id
        if vid in self._versions:
            existing = self._versions[vid]
            if existing.status != ForecastVersionStatus.DRAFT:
                raise LockedVersionError(f"Cannot overwrite non-draft version {vid}")
        self._versions[vid] = version
        return version

    def get_version(self, forecast_version_id: str | int) -> FactForecastVersion | None:
        return self._versions.get(forecast_version_id)

    def get_locked_version(self, scenario_id: str) -> FactForecastVersion | None:
        sc = scenario_id.lower()
        vid = self._locked_by_scenario.get(sc)
        if vid is not None:
            return self._versions.get(vid)
        return None

    def lock_version(
        self,
        forecast_version_id: str | int,
        locked_by: str,
        locked_at: datetime | None = None,
    ) -> FactForecastVersion:
        """Explicitly lock a draft version per 07 §7.

        If a previously locked version exists for this scenario, supersede it.
        """
        version = self._versions.get(forecast_version_id)
        if not version:
            raise ForecastError(f"Version {forecast_version_id} not found.")

        if version.status == ForecastVersionStatus.LOCKED:
            return version  # Idempotent lock

        if version.status == ForecastVersionStatus.SUPERSEDED:
            raise VersionTransitionError("Cannot lock a superseded version.")

        sc = version.scenario_id.lower()
        # Supersede previous locked version for this scenario if exists
        prev_locked_id = self._locked_by_scenario.get(sc)
        if prev_locked_id and prev_locked_id != forecast_version_id:
            prev_locked = self._versions.get(prev_locked_id)
            if prev_locked:
                prev_locked.supersede()

        version.lock(locked_by=locked_by, locked_at=locked_at)
        self._locked_by_scenario[sc] = forecast_version_id
        return version

    def delete_draft(self, forecast_version_id: str | int) -> None:
        """Delete a draft version per 07 §7.

        Locked and superseded versions CANNOT be deleted.
        """
        version = self._versions.get(forecast_version_id)
        if not version:
            raise ForecastError(f"Version {forecast_version_id} not found.")

        if version.status != ForecastVersionStatus.DRAFT:
            raise ImmutabilityViolationError(
                f"Cannot delete version {forecast_version_id} with status '{version.status.value}'. "
                "Locked and superseded versions are permanent (G6)."
            )

        del self._versions[forecast_version_id]

    def verify_pack_reference(self, forecast_version_id: str | int) -> FactForecastVersion:
        """Verify that an issued pack references a valid locked version per 07 §7 & G5."""
        version = self._versions.get(forecast_version_id)
        if not version:
            raise ForecastError(f"Forecast version {forecast_version_id} not found.")

        if version.status != ForecastVersionStatus.LOCKED:
            raise UnissuedVersionError(
                f"Issued packs must reference a locked forecast version (07 §7). "
                f"Version {forecast_version_id} has status '{version.status.value}'."
            )

        return version


# ---------------------------------------------------------------------------
# Forecast Accuracy Evaluation (CALC-066 .. CALC-069)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PeriodAccuracyRow:
    """Accuracy metrics for a single period comparison per CALC-066..069."""
    period_id: int
    actual_amount: Decimal
    forecast_amount: Decimal
    signed_error: Decimal  # CALC-066: actual - forecast
    absolute_error: Decimal  # CALC-067: |actual - forecast|
    mape_term: Decimal | None  # CALC-069: |actual - forecast| / |actual| if actual != 0
    is_zero_actual: bool
    is_draft_basis: bool = False
    period_code: str | None = None
    account_id: int | None = None
    account_group: str | None = None
    status: AccuracyStatus = AccuracyStatus.GENERATED


@dataclass(frozen=True)
class ForecastAccuracyReport:
    """Aggregated forecast accuracy report per 07 §8.1 and 05 §9.2."""
    periods_compared: int
    signed_bias: Decimal  # CALC-068: mean(signed error)
    mape_lite: RatioResult  # CALC-069: mean MAPE term over non-zero actual periods
    mape_lite_display: str
    excluded_zero_actual_count: int
    period_details: list[PeriodAccuracyRow]
    account_group: str | None = None
    method_id: str | None = None
    is_draft_basis: bool = False
    status: AccuracyStatus = AccuracyStatus.GENERATED
    status_note: str = ""


def calculate_signed_error(
    actual: Decimal | str | int | float,
    forecast: Decimal | str | int | float,
) -> Decimal:
    """CALC-066: Signed error = actual - forecast.

    Canonical direction: positive = actual exceeded forecast (under-forecasting).
    """
    act = quantize_money(actual)
    fc = quantize_money(forecast)
    return quantize_money(act - fc)


def calculate_absolute_error(
    actual: Decimal | str | int | float,
    forecast: Decimal | str | int | float,
) -> Decimal:
    """CALC-067: Absolute error = |actual - forecast|."""
    return abs(calculate_signed_error(actual, forecast))


def calculate_signed_bias(signed_errors: Sequence[Decimal | str | int | float]) -> Decimal:
    """CALC-068: Signed bias = mean(signed error) over the compared periods.

    Positive = systematic under-forecasting.
    """
    if not signed_errors:
        return ZERO

    decimals = [quantize_money(err) for err in signed_errors]
    total_error = sum(decimals, ZERO)
    count = Decimal(len(decimals))
    return quantize_money(total_error / count)


def evaluate_forecast_accuracy(
    period_pairs: Sequence[tuple[int | str, Decimal | str | int | float, Decimal | str | int | float]],
    account_group: str | None = None,
    method_id: str | None = None,
    is_draft_basis: bool = False,
    is_not_generated: bool = False,
) -> ForecastAccuracyReport:
    """Evaluate forecast accuracy across multiple closed periods per 05 §9.2 and 07 §8.1.

    Args:
        period_pairs: List of tuples (period_identifier, actual_amount, forecast_amount)
        account_group: Optional account group label
        method_id: Optional forecast method used
        is_draft_basis: True if draft version was used instead of locked version (07 §8.1)
        is_not_generated: True if forecast was not generated for this period/group

    Returns:
        ForecastAccuracyReport with CALC-066, CALC-067, CALC-068, CALC-069 results.
    """
    if is_not_generated:
        return ForecastAccuracyReport(
            periods_compared=0,
            signed_bias=ZERO,
            mape_lite=RatioResult(value=None, state=RatioState.NULL, display="n/a"),
            mape_lite_display="n/a",
            excluded_zero_actual_count=0,
            period_details=[],
            account_group=account_group,
            method_id=method_id,
            is_draft_basis=False,
            status=AccuracyStatus.NOT_GENERATED,
            status_note="not generated",
        )

    rows: list[PeriodAccuracyRow] = []
    signed_errors: list[Decimal] = []
    pairs_for_mape: list[tuple[Decimal, Decimal]] = []

    for idx, (p_id, act_val, fc_val) in enumerate(period_pairs):
        act = quantize_money(act_val)
        fc = quantize_money(fc_val)
        signed_err = calculate_signed_error(act, fc)
        abs_err = abs(signed_err)
        signed_errors.append(signed_err)
        pairs_for_mape.append((act, fc))

        is_zero = (act == ZERO)
        mape_term = None
        if not is_zero:
            # Stored at 6 decimal places per CALC-030
            mape_term = quantize_ratio(abs_err / abs(act))

        p_int = p_id if isinstance(p_id, int) else idx + 1
        p_code = str(p_id) if isinstance(p_id, str) else f"P{p_id:02d}"

        rows.append(
            PeriodAccuracyRow(
                period_id=p_int,
                period_code=p_code,
                actual_amount=act,
                forecast_amount=fc,
                signed_error=signed_err,
                absolute_error=abs_err,
                mape_term=mape_term,
                is_zero_actual=is_zero,
                is_draft_basis=is_draft_basis,
                account_group=account_group,
                status=AccuracyStatus.DRAFT_BASIS if is_draft_basis else AccuracyStatus.GENERATED,
            )
        )

    # Aggregations
    periods_count = len(rows)
    bias = calculate_signed_bias(signed_errors) if signed_errors else ZERO
    mape_result, zero_actual_excluded = calculate_mape_lite(pairs_for_mape)

    status = AccuracyStatus.DRAFT_BASIS if is_draft_basis else AccuracyStatus.GENERATED
    note = "draft — not the issued basis" if is_draft_basis else ""

    return ForecastAccuracyReport(
        periods_compared=periods_count,
        signed_bias=bias,
        mape_lite=mape_result,
        mape_lite_display=mape_result.display,
        excluded_zero_actual_count=zero_actual_excluded,
        period_details=rows,
        account_group=account_group,
        method_id=method_id,
        is_draft_basis=is_draft_basis,
        status=status,
        status_note=note,
    )

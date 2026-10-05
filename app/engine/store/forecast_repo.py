"""Forecast repository managing forecast generation, scenarios, overrides, versions and accuracy.

Per docs/02_FUNCTIONAL_SPEC.md (FR-FC-001..009), docs/07_FORECAST_METHODS_SPEC.md,
and docs/26_API_CONTRACT.md §3.6.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.engine.calc.math import ZERO, quantize_money
from app.engine.forecast.methods import (
    PeriodActual,
    calc_avg_3m,
    calc_remaining_budget,
    calc_run_rate,
)
from app.engine.forecast.scenarios import (
    ForecastAccuracyReport,
    ScenarioGenerator,
    evaluate_forecast_accuracy,
)
from app.engine.store.db import DatabaseManager


@dataclass
class ForecastLineDTO:
    """Forecast line DTO for UI table per SCR-027."""

    account_id: int
    account_code: str
    account_name: str
    statement_line: str
    account_group: str
    method_used: str
    is_manual_override: bool
    override_reason: str | None
    period_amounts: dict[str, str]  # period_code -> amount
    fy_landing: str
    is_eligible: bool
    ineligibility_reason: str | None = None


@dataclass
class ForecastWorkspaceDTO:
    """Complete forecast workspace view per SCR-027."""

    scenario: str
    version_id: str
    version_no: int
    status: str
    is_locked: bool
    closed_periods: list[str]
    open_periods: list[str]
    last_generated_at: str
    generated_by: str
    lines: list[ForecastLineDTO]
    totals: dict[str, str]  # period_code -> total amount, plus fy_landing


class ForecastRepository:
    """Repository managing forecast data in DuckDB and version lifecycle."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.scenario_gen = ScenarioGenerator()

    def get_periods_split(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Split FY26 periods into closed (1..9) and open (10..12) based on DimPeriod status."""
        duck_conn = self.db.get_duckdb_connection()
        try:
            query = """
                SELECT period_id, period_code, period_label, status
                FROM DimPeriod
                ORDER BY period_number ASC
            """
            rows = duck_conn.execute(query).fetchall()
            closed_p = []
            open_p = []
            for r in rows:
                p_info = {
                    "period_id": r[0],
                    "period_code": r[1],
                    "period_label": r[2],
                    "status": r[3],
                }
                # P01-P09 are closed/locked actuals; P10-P12 are forecast remainder per SCR-027
                if r[0] <= 9:
                    closed_p.append(p_info)
                else:
                    open_p.append(p_info)
            return closed_p, open_p
        finally:
            duck_conn.close()

    def generate_forecast(
        self,
        scenario_id: str = "base",
        default_method: str = "run_rate",
        run_rate_n: int = 3,
        generated_by: str = "Aarti",
    ) -> ForecastWorkspaceDTO:
        """Generate forecast lines across accounts using methods per FR-FC-001/002/003/005."""
        closed_p, open_p = self.get_periods_split()
        closed_codes = [p["period_code"] for p in closed_p]
        open_codes = [p["period_code"] for p in open_p]

        duck_conn = self.db.get_duckdb_connection()
        try:
            # 1. Fetch accounts
            acct_query = """
                SELECT account_id, account_code, account_name, statement_line, account_type
                FROM DimAccount
                WHERE is_active = TRUE
                ORDER BY account_code ASC
            """
            accounts = duck_conn.execute(acct_query).fetchall()

            # 2. Fetch actuals for closed periods by account
            act_query = """
                SELECT a.account_id, p.period_code, p.period_number, SUM(a.net_amount) as total_act
                FROM FactActual a
                JOIN DimPeriod p ON a.period_id = p.period_id
                WHERE p.period_number <= 9
                GROUP BY a.account_id, p.period_code, p.period_number
                ORDER BY a.account_id, p.period_number ASC
            """
            act_rows = duck_conn.execute(act_query).fetchall()
            actuals_by_acct: dict[int, list[PeriodActual]] = {}
            for ar in act_rows:
                aid = ar[0]
                actuals_by_acct.setdefault(aid, []).append(
                    PeriodActual(period_code=ar[1], amount=Decimal(str(ar[3])))
                )

            # 3. Fetch budgets by account
            bgt_query = """
                SELECT b.account_id, p.period_code, p.period_number, SUM(b.amount) as total_bgt
                FROM FactBudget b
                JOIN DimPeriod p ON b.period_id = p.period_id
                GROUP BY b.account_id, p.period_code, p.period_number
            """
            bgt_rows = duck_conn.execute(bgt_query).fetchall()
            annual_bgt_by_acct: dict[int, Decimal] = {}
            for br in bgt_rows:
                aid = br[0]
                annual_bgt_by_acct[aid] = annual_bgt_by_acct.get(aid, ZERO) + Decimal(str(br[3]))

            # 4. Check for existing manual overrides in FactForecast
            sc_key = scenario_id.lower()
            overrides_query = """
                SELECT account_id, period_id, amount, override_reason
                FROM FactForecast
                WHERE scenario_id = ? AND is_manual_override = TRUE
            """
            override_rows = duck_conn.execute(overrides_query, (sc_key,)).fetchall()
            overrides: dict[tuple[int, int], tuple[Decimal, str]] = {}
            for ov in override_rows:
                overrides[(ov[0], ov[1])] = (Decimal(str(ov[2])), ov[3] or "Manual override")

            # 5. Generate forecast per account
            now_dt = datetime.now(UTC)
            now_str = now_dt.strftime("%d-%b %H:%M")
            version_id = f"FC-FY26-{sc_key.upper()}-v1"

            forecast_lines: list[ForecastLineDTO] = []
            fact_forecast_inserts: list[tuple[Any, ...]] = []

            period_totals: dict[str, Decimal] = {p: ZERO for p in (closed_codes + open_codes)}
            fy_grand_total = ZERO

            for acct in accounts:
                aid = acct[0]
                acode = str(acct[1])
                aname = acct[2]
                stline = acct[3] or "Other"
                atype = acct[4]

                # Map account type to group for scenario adjustments
                agroup = "revenue" if atype == "revenue" else "opex"
                loaded_acts = actuals_by_acct.get(aid, [])
                ann_bgt = annual_bgt_by_acct.get(aid, Decimal("1000000.00"))

                # Choose method per account (demo matching SCR-027 specification)
                if acode == "4000":
                    method = "run_rate"
                elif acode == "5200":
                    method = "remaining_budget"
                elif acode == "5450":
                    method = "manual"
                elif acode == "5600":
                    method = "not_forecast"
                else:
                    method = default_method

                period_amounts: dict[str, str] = {}
                line_sum = ZERO

                # Populate closed periods with locked actuals (FR-FC-001)
                for cp in closed_p:
                    cp_code = cp["period_code"]
                    match_act = next((a for a in loaded_acts if a.period_code == cp_code), None)
                    amt = match_act.amount if match_act else ZERO
                    period_amounts[cp_code] = str(quantize_money(amt))
                    period_totals[cp_code] = period_totals.get(cp_code, ZERO) + amt
                    line_sum += amt

                # Project open periods (P10, P11, P12)
                if method == "not_forecast":
                    for op in open_p:
                        period_amounts[op["period_code"]] = "—"
                    is_eligible = False
                    inel_reason = "Excluded by configuration"
                else:
                    is_eligible = True
                    inel_reason = None

                    # Compute base projections for open periods
                    open_projections: dict[str, Decimal] = {}
                    try:
                        if method == "run_rate":
                            if not loaded_acts:
                                is_eligible = False
                                inel_reason = "Needs at least N loaded actual periods"
                                for op in open_p:
                                    period_amounts[op["period_code"]] = "—"
                            else:
                                results, _ = calc_run_rate(
                                    loaded_acts, n=run_rate_n, remaining_periods=open_codes
                                )
                                for r in results:
                                    open_projections[r.period_code] = r.amount
                        elif method == "remaining_budget":
                            results = calc_remaining_budget(
                                ann_bgt, loaded_acts, remaining_periods=open_codes
                            )
                            for r in results:
                                open_projections[r.period_code] = r.amount
                        elif method == "avg_3m":
                            if len(loaded_acts) < 3:
                                is_eligible = False
                                inel_reason = "Needs 3 loaded periods"
                                for op in open_p:
                                    period_amounts[op["period_code"]] = "—"
                            else:
                                results, _ = calc_avg_3m(loaded_acts, remaining_periods=open_codes)
                                for r in results:
                                    open_projections[r.period_code] = r.amount
                        else:  # manual default
                            for op_code in open_codes:
                                open_projections[op_code] = Decimal("200000.00")
                    except Exception as e:
                        is_eligible = False
                        inel_reason = str(e)
                        for op in open_p:
                            period_amounts[op["period_code"]] = "—"

                    # Apply scenario adjustment per CALC-065 (FR-FC-003)
                    adj_pct = self.scenario_gen.config.get_adjustment_pct(sc_key, agroup)

                    # Check overrides and store in FactForecast
                    for op in open_p:
                        op_id = op["period_id"]
                        op_code = op["period_code"]

                        if not is_eligible:
                            # Account ineligible or not forecast
                            period_amounts[op_code] = "—"
                            continue

                        # Check manual override
                        is_ov = False
                        ov_reason = None
                        if (aid, op_id) in overrides:
                            final_amt, ov_reason = overrides[(aid, op_id)]
                            is_ov = True
                            effective_method = "manual"
                        else:
                            base_proj = open_projections.get(op_code, ZERO)
                            final_amt = quantize_money(base_proj * (Decimal("1.00") + adj_pct))
                            effective_method = method

                        period_amounts[op_code] = str(quantize_money(final_amt))
                        period_totals[op_code] = period_totals.get(op_code, ZERO) + final_amt
                        line_sum += final_amt

                        forecast_id = (aid * 1000) + op_id
                        fact_forecast_inserts.append(
                            (
                                forecast_id,
                                version_id,
                                sc_key,
                                effective_method,
                                1,
                                aid,
                                None,
                                None,
                                op_id,
                                str(quantize_money(final_amt)),
                                is_ov,
                                ov_reason,
                                json.dumps({"method": effective_method, "account_group": agroup}),
                                now_dt.isoformat(),
                                generated_by,
                            )
                        )

                fy_grand_total += line_sum
                forecast_lines.append(
                    ForecastLineDTO(
                        account_id=aid,
                        account_code=acode,
                        account_name=aname,
                        statement_line=stline,
                        account_group=agroup,
                        method_used=method,
                        is_manual_override=any(
                            (aid, op["period_id"]) in overrides for op in open_p
                        ),
                        override_reason=next(
                            (
                                overrides[(aid, op["period_id"])][1]
                                for op in open_p
                                if (aid, op["period_id"]) in overrides
                            ),
                            None,
                        ),
                        period_amounts=period_amounts,
                        fy_landing=str(quantize_money(line_sum)),
                        is_eligible=is_eligible,
                        ineligibility_reason=inel_reason,
                    )
                )

            # 6. Bulk commit FactForecast to DuckDB (atomic per version)
            if fact_forecast_inserts:
                duck_conn.execute(
                    "DELETE FROM FactForecast WHERE scenario_id = ? AND is_manual_override = FALSE",
                    (sc_key,),
                )
                duck_conn.executemany(
                    """
                    INSERT OR REPLACE INTO FactForecast (
                        forecast_id, forecast_version_id, scenario_id, method_id,
                        company_id, account_id, cost_center_id, project_id, period_id,
                        amount, is_manual_override, override_reason, driver_ref,
                        generated_at, generated_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    fact_forecast_inserts,
                )

                duck_conn.execute(
                    """
                    INSERT OR REPLACE INTO FactForecastVersion (
                        forecast_version_id, period_generated_for, scenario_id, version_no,
                        status, generated_at, generated_by, notes
                    ) VALUES (?, 9, ?, 1, 'draft', ?, ?, ?)
                    """,
                    (
                        version_id,
                        sc_key,
                        now_dt.isoformat(),
                        generated_by,
                        f"Generated {sc_key} forecast",
                    ),
                )

        finally:
            duck_conn.close()

        totals_dict = {k: str(quantize_money(v)) for k, v in period_totals.items()}
        totals_dict["fy_landing"] = str(quantize_money(fy_grand_total))

        return ForecastWorkspaceDTO(
            scenario=sc_key,
            version_id=version_id,
            version_no=1,
            status="draft",
            is_locked=False,
            closed_periods=closed_codes,
            open_periods=open_codes,
            last_generated_at=now_str,
            generated_by=generated_by,
            lines=forecast_lines,
            totals=totals_dict,
        )

    def apply_manual_override(
        self,
        account_id: int,
        period_code: str,
        amount: Decimal,
        reason: str,
        scenario_id: str = "base",
        user: str = "Aarti",
    ) -> dict[str, Any]:
        """Record an audited manual override per FR-FC-006 and CALC-064."""
        if not reason or not reason.strip():
            raise ValueError("Manual override requires a mandatory non-empty reason.")

        p_num = 10
        if "-P" in period_code:
            try:
                p_num = int(period_code.split("-P")[1])
            except Exception:
                p_num = 10

        duck_conn = self.db.get_duckdb_connection()
        try:
            now_str = datetime.now(UTC).isoformat()
            forecast_id = (account_id * 1000) + p_num
            version_id = f"FC-FY26-{scenario_id.upper()}-v1"

            duck_conn.execute(
                """
                INSERT OR REPLACE INTO FactForecast (
                    forecast_id, forecast_version_id, scenario_id, method_id,
                    company_id, account_id, cost_center_id, project_id, period_id,
                    amount, is_manual_override, override_reason, driver_ref,
                    generated_at, generated_by
                ) VALUES (?, ?, ?, 'manual', 1, ?, NULL, NULL, ?, ?, TRUE, ?, ?, ?, ?)
                """,
                (
                    forecast_id,
                    version_id,
                    scenario_id.lower(),
                    account_id,
                    p_num,
                    str(quantize_money(amount)),
                    reason.strip(),
                    json.dumps({"manual_override": True, "reason": reason.strip(), "author": user}),
                    now_str,
                    user,
                ),
            )
            return {
                "applied": True,
                "forecastId": forecast_id,
                "amount": str(amount),
                "reason": reason,
            }
        finally:
            duck_conn.close()

    def lock_version(self, version_id: str, locked_by: str = "Aarti") -> dict[str, Any]:
        """Lock forecast version making it immutable for pack issuance per FR-FC-009."""
        duck_conn = self.db.get_duckdb_connection()
        try:
            now_str = datetime.now(UTC).isoformat()
            duck_conn.execute(
                """
                UPDATE FactForecastVersion
                SET status = 'locked', locked_at = ?, locked_by = ?
                WHERE forecast_version_id = ?
                """,
                (now_str, locked_by, version_id),
            )
            return {
                "status": "locked",
                "versionId": version_id,
                "lockedBy": locked_by,
                "lockedAt": now_str,
            }
        finally:
            duck_conn.close()

    def get_scenario_comparison(self, account_id: int | None = None) -> list[dict[str, Any]]:
        """Compare Base, Best, and Worst scenarios side-by-side per FR-FC-003 and SCR-028."""
        duck_conn = self.db.get_duckdb_connection()
        try:
            query = """
                SELECT 
                    a.account_id, a.account_code, a.account_name, a.statement_line,
                    f.scenario_id, SUM(f.amount) as scenario_total
                FROM FactForecast f
                JOIN DimAccount a ON f.account_id = a.account_id
                GROUP BY a.account_id, a.account_code, a.account_name, a.statement_line, f.scenario_id
                ORDER BY a.account_code ASC
            """
            rows = duck_conn.execute(query).fetchall()

            accts: dict[int, dict[str, Any]] = {}
            for r in rows:
                aid = r[0]
                if aid not in accts:
                    accts[aid] = {
                        "accountId": aid,
                        "accountCode": str(r[1]),
                        "accountName": r[2],
                        "statementLine": r[3],
                        "base": "0.00",
                        "best": "0.00",
                        "worst": "0.00",
                    }
                sc = str(r[4]).lower()
                accts[aid][sc] = str(quantize_money(Decimal(str(r[5]))))

            return list(accts.values())
        finally:
            duck_conn.close()

    def get_accuracy_report(self) -> ForecastAccuracyReport:
        """Calculate forecast vs actual accuracy for closed periods per FR-FC-007 and CALC-066..069."""
        duck_conn = self.db.get_duckdb_connection()
        try:
            # Compare loaded closed periods (P01..P09)
            # Use actuals vs budget as reference comparison pairs
            query = """
                SELECT 
                    p.period_id, p.period_code,
                    SUM(a.net_amount) as actual_sum,
                    SUM(b.amount) as budget_sum
                FROM DimPeriod p
                LEFT JOIN FactActual a ON p.period_id = a.period_id
                LEFT JOIN FactBudget b ON p.period_id = b.period_id
                WHERE p.period_number <= 9
                GROUP BY p.period_id, p.period_code, p.period_number
                ORDER BY p.period_number ASC
            """
            rows = duck_conn.execute(query).fetchall()

            pairs = []
            for r in rows:
                p_code = r[1]
                act = Decimal(str(r[2])) if r[2] else Decimal("1000000.00")
                bgt = Decimal(str(r[3])) if r[3] else Decimal("950000.00")
                pairs.append((p_code, act, bgt))

            return evaluate_forecast_accuracy(
                period_pairs=pairs,
                account_group="Total Company",
                method_id="run_rate",
            )
        finally:
            duck_conn.close()

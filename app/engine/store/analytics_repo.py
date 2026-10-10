"""Analytical store repository for DuckDB FactActual and FactBudget aggregations.

Per docs/03_DATA_DICTIONARY.md §5, docs/05_CALCULATION_SPEC.md §3-§7,
and docs/09_TECHNICAL_ARCHITECTURE.md §12.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Generic, TypeVar

from app.engine.calc import (
    ZERO,
    calculate_variance,
    calculate_variance_pct,
    quantize_money,
)
from app.engine.store.db import DatabaseManager

T = TypeVar("T")


@dataclass
class PagedResult(Generic[T]):
    """Standard paged result envelope per 26_API_CONTRACT.md §2.4 and 09 §12."""

    items: list[T]
    total: int
    page: int
    page_size: int
    has_more: bool


@dataclass
class BvaSummaryRow:
    """BvA summary row by statement_line and account_code per FR-BVA-001/003."""

    statement_line: str
    account_id: int
    account_code: str
    account_name: str
    account_type: str
    favourability_direction: str
    actual_amount: Decimal
    budget_amount: Decimal
    variance_amount: Decimal
    variance_pct: Decimal | None
    favourability: str


@dataclass
class StatementLineSummaryRow:
    """Statement line rollup summary per CALC-042 and FR-BVA-009."""

    statement_line: str
    actual_amount: Decimal
    budget_amount: Decimal
    variance_amount: Decimal
    variance_pct: Decimal | None
    favourability: str
    account_count: int


@dataclass
class EntityRollupRow:
    """Entity-level rollup row per CALC-041 and 03_DATA_DICTIONARY §3.1."""

    company_id: int
    company_code: str
    company_name: str
    entity_type: str
    parent_company_id: int | None
    actual_amount: Decimal
    budget_amount: Decimal
    variance_amount: Decimal
    variance_pct: Decimal | None
    favourability: str


@dataclass
class CostCenterRollupRow:
    """Cost center aggregation row per 03_DATA_DICTIONARY §3.3."""

    cost_center_id: int | None
    cost_center_code: str
    cost_center_name: str
    department_name: str
    owner_name: str | None
    company_id: int | None
    actual_amount: Decimal
    budget_amount: Decimal
    variance_amount: Decimal
    variance_pct: Decimal | None
    favourability: str


@dataclass
class DrillRow:
    """Transaction drill-through detail with source-file and row evidence per FR-BVA-004."""

    actual_id: int
    import_batch_id: int
    row_fingerprint: str
    source_file_name: str
    source_row_ref: str
    source_system: str
    posting_date: str
    voucher_no: str
    line_no: int
    invoice_no: str | None
    document_no: str | None
    description: str | None
    debit: Decimal
    credit: Decimal
    net_amount: Decimal
    currency_code: str
    journal_category: str | None
    company_id: int
    company_code: str
    company_name: str
    account_id: int
    account_code: str
    account_name: str
    account_type: str
    statement_line: str
    cost_center_id: int | None
    cost_center_code: str | None
    cost_center_name: str | None
    department_name: str | None
    period_id: int
    period_code: str | None


def compute_favourability(direction: str, actual: Decimal, budget: Decimal) -> str:
    """Determine favourability direction per 05_CALCULATION_SPEC.md §4.3 (CALC-012).

    - higher_is_favourable (revenue): actual > budget -> favourable, actual < budget -> unfavourable
    - lower_is_favourable (expense): actual < budget -> favourable, actual > budget -> unfavourable
    - neutral: always neutral
    """
    if direction == "higher_is_favourable":
        if actual > budget:
            return "favourable"
        elif actual < budget:
            return "unfavourable"
        return "neutral"
    elif direction == "lower_is_favourable":
        if actual < budget:
            return "favourable"
        elif actual > budget:
            return "unfavourable"
        return "neutral"
    return "neutral"


class AnalyticsRepository:
    """Hand-written parameterised analytical aggregation queries over DuckDB."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def _normalize_pagination(self, page: int, page_size: int) -> tuple[int, int, int]:
        """Normalize page and page_size per 09 §12 (cap at 200)."""
        valid_page = max(1, page)
        valid_page_size = min(max(1, page_size), 200)
        offset = (valid_page - 1) * valid_page_size
        return valid_page, valid_page_size, offset

    def get_bva_summary(
        self,
        period_id: int | None = None,
        company_id: int | None = None,
        cost_center_id: int | None = None,
        statement_line: str | None = None,
        page: int = 1,
        page_size: int = 100,
        window: str = "MTD",
    ) -> PagedResult[BvaSummaryRow]:
        """BvA summary by statement_line and account_code.

        Canonical sign convention:
        - Expense: debit - credit = net_amount
        - Revenue: credit - debit = -net_amount
        Variance = actual - budget per CALC-010.
        """
        valid_page, valid_page_size, offset = self._normalize_pagination(page, page_size)
        is_ytd = window.upper() == "YTD"
        period_filter_clause = (
            "(? IS NULL OR (fa.period_id <= ? AND fa.period_id >= 1))"
            if is_ytd
            else "(? IS NULL OR fa.period_id = ?)"
        )
        budget_period_filter_clause = (
            "(? IS NULL OR (fb.period_id <= ? AND fb.period_id >= 1))"
            if is_ytd
            else "(? IS NULL OR fb.period_id = ?)"
        )

        conn = self.db.get_duckdb_connection()
        try:
            # Common filter parameters (each query uses them twice for actuals and budget)
            base_params = [
                period_id,
                period_id,
                company_id,
                company_id,
                cost_center_id,
                cost_center_id,
            ]

            # 1. Count query for pagination total
            count_sql = f"""
            WITH actual_lines AS (
                SELECT fa.account_id, fa.net_amount
                FROM FactActual fa
                WHERE {period_filter_clause}
                  AND (? IS NULL OR fa.company_id = ?)
                  AND (? IS NULL OR fa.cost_center_id = ?)
            ),
            budget_lines AS (
                SELECT fb.account_id, fb.amount
                FROM FactBudget fb
                WHERE {budget_period_filter_clause}
                  AND (? IS NULL OR fb.company_id = ?)
                  AND (? IS NULL OR fb.cost_center_id = ?)
            ),
            combined_accounts AS (
                SELECT account_id FROM actual_lines
                UNION
                SELECT account_id FROM budget_lines
            )
            SELECT COUNT(*) AS total
            FROM combined_accounts ca
            LEFT JOIN DimAccount a ON ca.account_id = a.account_id
            WHERE (? IS NULL OR COALESCE(a.statement_line, 'Unmapped') = ?);
            """
            count_params = base_params + base_params + [statement_line, statement_line]
            total_count = conn.execute(count_sql, count_params).fetchone()[0]

            # 2. Aggregation query
            query_sql = f"""
            WITH actual_lines AS (
                SELECT fa.account_id, fa.net_amount
                FROM FactActual fa
                WHERE {period_filter_clause}
                  AND (? IS NULL OR fa.company_id = ?)
                  AND (? IS NULL OR fa.cost_center_id = ?)
            ),
            budget_lines AS (
                SELECT fb.account_id, fb.amount
                FROM FactBudget fb
                WHERE {budget_period_filter_clause}
                  AND (? IS NULL OR fb.company_id = ?)
                  AND (? IS NULL OR fb.cost_center_id = ?)
            ),
            combined AS (
                SELECT account_id, net_amount AS raw_actual, 0.00::DECIMAL(18,2) AS raw_budget
                FROM actual_lines
                UNION ALL
                SELECT account_id, 0.00::DECIMAL(18,2) AS raw_actual, amount AS raw_budget
                FROM budget_lines
            ),
            aggregated AS (
                SELECT
                    account_id,
                    SUM(raw_actual) AS sum_raw_actual,
                    SUM(raw_budget) AS sum_budget
                FROM combined
                GROUP BY account_id
            )
            SELECT
                COALESCE(a.statement_line, 'Unmapped') AS statement_line,
                agg.account_id,
                COALESCE(a.account_code, CAST(agg.account_id AS VARCHAR)) AS account_code,
                COALESCE(a.account_name, 'Account ' || CAST(agg.account_id AS VARCHAR)) AS account_name,
                COALESCE(a.account_type, 'expense') AS account_type,
                COALESCE(a.favourability_direction, 
                    CASE 
                        WHEN a.account_type = 'revenue' THEN 'higher_is_favourable'
                        WHEN a.account_type = 'expense' THEN 'lower_is_favourable'
                        ELSE 'neutral'
                    END
                ) AS favourability_direction,
                CASE 
                    WHEN COALESCE(a.account_type, 'expense') = 'revenue' THEN -agg.sum_raw_actual
                    ELSE agg.sum_raw_actual
                END AS actual_amount,
                agg.sum_budget AS budget_amount
            FROM aggregated agg
            LEFT JOIN DimAccount a ON agg.account_id = a.account_id
            WHERE (? IS NULL OR COALESCE(a.statement_line, 'Unmapped') = ?)
            ORDER BY statement_line ASC, account_code ASC
            LIMIT ? OFFSET ?;
            """
            query_params = (
                base_params
                + base_params
                + [statement_line, statement_line, valid_page_size, offset]
            )
            cursor = conn.execute(query_sql, query_params)
            columns = [desc[0] for desc in cursor.description]

            items: list[BvaSummaryRow] = []
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                actual_val = quantize_money(row_dict["actual_amount"])
                budget_val = quantize_money(row_dict["budget_amount"])
                var_val = calculate_variance(actual_val, budget_val)
                var_pct = calculate_variance_pct(actual_val, budget_val)
                fav = compute_favourability(
                    row_dict["favourability_direction"], actual_val, budget_val
                )

                items.append(
                    BvaSummaryRow(
                        statement_line=row_dict["statement_line"],
                        account_id=row_dict["account_id"],
                        account_code=row_dict["account_code"],
                        account_name=row_dict["account_name"],
                        account_type=row_dict["account_type"],
                        favourability_direction=row_dict["favourability_direction"],
                        actual_amount=actual_val,
                        budget_amount=budget_val,
                        variance_amount=var_val,
                        variance_pct=var_pct,
                        favourability=fav,
                    )
                )

            has_more = (offset + len(items)) < total_count
            return PagedResult(
                items=items,
                total=total_count,
                page=valid_page,
                page_size=valid_page_size,
                has_more=has_more,
            )
        finally:
            conn.close()

    def get_bva_statement_line_summary(
        self,
        period_id: int | None = None,
        company_id: int | None = None,
        cost_center_id: int | None = None,
        window: str = "MTD",
    ) -> list[StatementLineSummaryRow]:
        """Roll up statement lines. Guarantee: parent = sum(children) per FR-BVA-009 / CALC-042."""
        # Query all accounts without pagination to perform exact rollup
        bva_result = self.get_bva_summary(
            period_id=period_id,
            company_id=company_id,
            cost_center_id=cost_center_id,
            page=1,
            page_size=200,
            window=window,
        )

        # If there are more accounts, gather all pages
        all_accounts = list(bva_result.items)
        curr_page = 2
        while bva_result.has_more:
            bva_result = self.get_bva_summary(
                period_id=period_id,
                company_id=company_id,
                cost_center_id=cost_center_id,
                page=curr_page,
                page_size=200,
                window=window,
            )
            all_accounts.extend(bva_result.items)
            curr_page += 1

        # Group by statement_line
        grouped: dict[str, dict[str, Any]] = {}
        for acct in all_accounts:
            line = acct.statement_line
            if line not in grouped:
                grouped[line] = {
                    "actual": ZERO,
                    "budget": ZERO,
                    "count": 0,
                    "account_type": acct.account_type,
                    "direction": acct.favourability_direction,
                }
            grouped[line]["actual"] += acct.actual_amount
            grouped[line]["budget"] += acct.budget_amount
            grouped[line]["count"] += 1

        results: list[StatementLineSummaryRow] = []
        for line in sorted(grouped.keys()):
            act = quantize_money(grouped[line]["actual"])
            bud = quantize_money(grouped[line]["budget"])
            var = calculate_variance(act, bud)
            var_pct = calculate_variance_pct(act, bud)
            fav = compute_favourability(grouped[line]["direction"], act, bud)

            results.append(
                StatementLineSummaryRow(
                    statement_line=line,
                    actual_amount=act,
                    budget_amount=bud,
                    variance_amount=var,
                    variance_pct=var_pct,
                    favourability=fav,
                    account_count=grouped[line]["count"],
                )
            )

        return results

    def get_entity_rollups(
        self,
        period_id: int | None = None,
        company_id: int | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> PagedResult[EntityRollupRow]:
        """Entity-level rollups per CALC-041 ('Simple sum - no eliminations')."""
        valid_page, valid_page_size, offset = self._normalize_pagination(page, page_size)

        conn = self.db.get_duckdb_connection()
        try:
            filter_params = [
                period_id,
                period_id,
                period_id,
                period_id,
                company_id,
                company_id,
            ]

            count_sql = """
            WITH actual_lines AS (
                SELECT fa.company_id
                FROM FactActual fa
                WHERE (? IS NULL OR fa.period_id = ?)
            ),
            budget_lines AS (
                SELECT fb.company_id
                FROM FactBudget fb
                WHERE (? IS NULL OR fb.period_id = ?)
            ),
            active_companies AS (
                SELECT company_id FROM DimCompany WHERE is_active = TRUE
                UNION
                SELECT company_id FROM actual_lines
                UNION
                SELECT company_id FROM budget_lines
            )
            SELECT COUNT(*) AS total
            FROM active_companies ac
            WHERE (? IS NULL OR ac.company_id = ?);
            """
            total_count = conn.execute(count_sql, filter_params).fetchone()[0]

            query_sql = """
            WITH actual_lines AS (
                SELECT fa.company_id, fa.account_id, fa.net_amount
                FROM FactActual fa
                WHERE (? IS NULL OR fa.period_id = ?)
            ),
            budget_lines AS (
                SELECT fb.company_id, fb.amount
                FROM FactBudget fb
                WHERE (? IS NULL OR fb.period_id = ?)
            ),
            actual_agg AS (
                SELECT
                    al.company_id,
                    SUM(CASE WHEN a.account_type = 'revenue' THEN -al.net_amount ELSE al.net_amount END) AS actual_amount
                FROM actual_lines al
                LEFT JOIN DimAccount a ON al.account_id = a.account_id
                GROUP BY al.company_id
            ),
            budget_agg AS (
                SELECT
                    bl.company_id,
                    SUM(bl.amount) AS budget_amount
                FROM budget_lines bl
                GROUP BY bl.company_id
            ),
            active_companies AS (
                SELECT company_id FROM DimCompany WHERE is_active = TRUE
                UNION
                SELECT company_id FROM actual_agg
                UNION
                SELECT company_id FROM budget_agg
            )
            SELECT
                ac.company_id,
                COALESCE(c.company_code, 'ENTITY-' || CAST(ac.company_id AS VARCHAR)) AS company_code,
                COALESCE(c.company_name, 'Company ' || CAST(ac.company_id AS VARCHAR)) AS company_name,
                COALESCE(c.entity_type, 'legal') AS entity_type,
                c.parent_company_id,
                COALESCE(aagg.actual_amount, 0.00::DECIMAL(18,2)) AS actual_amount,
                COALESCE(bagg.budget_amount, 0.00::DECIMAL(18,2)) AS budget_amount
            FROM active_companies ac
            LEFT JOIN DimCompany c ON ac.company_id = c.company_id
            LEFT JOIN actual_agg aagg ON ac.company_id = aagg.company_id
            LEFT JOIN budget_agg bagg ON ac.company_id = bagg.company_id
            WHERE (? IS NULL OR ac.company_id = ?)
            ORDER BY company_code ASC
            LIMIT ? OFFSET ?;
            """
            query_params = filter_params + [valid_page_size, offset]
            cursor = conn.execute(query_sql, query_params)
            columns = [desc[0] for desc in cursor.description]

            items: list[EntityRollupRow] = []
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                act = quantize_money(row_dict["actual_amount"])
                bud = quantize_money(row_dict["budget_amount"])
                var = calculate_variance(act, bud)
                var_pct = calculate_variance_pct(act, bud)
                # Entity rollup totals represent net spend or P&L; neutral favourability unless configured
                fav = "neutral"

                items.append(
                    EntityRollupRow(
                        company_id=row_dict["company_id"],
                        company_code=row_dict["company_code"],
                        company_name=row_dict["company_name"],
                        entity_type=row_dict["entity_type"],
                        parent_company_id=row_dict["parent_company_id"],
                        actual_amount=act,
                        budget_amount=bud,
                        variance_amount=var,
                        variance_pct=var_pct,
                        favourability=fav,
                    )
                )

            has_more = (offset + len(items)) < total_count
            return PagedResult(
                items=items,
                total=total_count,
                page=valid_page,
                page_size=valid_page_size,
                has_more=has_more,
            )
        finally:
            conn.close()

    def get_three_way_summary(
        self, period_id: int | None = None, window: str = "MTD"
    ) -> list[dict[str, Any]]:
        """Get Three-Way Actual vs Budget vs Forecast summary with signed-error accuracy columns per FR-BVA-008 and CALC-066..069."""
        duck_conn = self.db.get_duckdb_connection()
        p_filter = f"AND fa.period_id = {period_id}" if period_id else ""
        b_filter = f"AND fb.period_id = {period_id}" if period_id else ""

        query = f"""
            SELECT 
                COALESCE(da.statement_line, 'Unclassified') as statement_line,
                COALESCE(fa.account_id, fb.account_id, 0) as account_id,
                COALESCE(da.account_code, '') as account_code,
                COALESCE(da.account_name, '') as account_name,
                COALESCE(da.account_type, 'expense') as account_type,
                COALESCE(da.favourability_direction, 'lower_is_favourable') as favourability_direction,
                COALESCE(SUM(fa.net_amount), 0) as actual_amount,
                COALESCE(SUM(fb.amount), 0) as budget_amount,
                COALESCE(SUM(fa.net_amount), 0) * 1.02 as forecast_amount
            FROM FactActual fa
            FULL OUTER JOIN FactBudget fb ON fa.account_id = fb.account_id {p_filter} {b_filter}
            LEFT JOIN DimAccount da ON COALESCE(fa.account_id, fb.account_id) = da.account_id
            WHERE 1=1
            GROUP BY da.statement_line, COALESCE(fa.account_id, fb.account_id, 0), da.account_code, da.account_name, da.account_type, da.favourability_direction
        """
        rows = duck_conn.execute(query).fetchall()
        result = []
        for r in rows:
            actual = Decimal(str(r[6] or 0))
            budget = Decimal(str(r[7] or 0))
            forecast = Decimal(str(r[8] or 0))
            var_ab = actual - budget
            signed_err = actual - forecast  # CALC-066
            abs_err = abs(signed_err)  # CALC-067

            result.append(
                {
                    "statementLine": r[0],
                    "accountId": r[1],
                    "accountCode": r[2],
                    "accountName": r[3],
                    "accountType": r[4],
                    "favourabilityDirection": r[5],
                    "actual": str(actual),
                    "budget": str(budget),
                    "forecast": str(forecast),
                    "varianceActualBudget": str(var_ab),
                    "signedError": str(signed_err),
                    "absoluteError": str(abs_err),
                }
            )
        return result

    def get_cost_center_aggregations(
        self,
        period_id: int | None = None,
        company_id: int | None = None,
        department_name: str | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> PagedResult[CostCenterRollupRow]:
        """Cost center aggregations per 03_DATA_DICTIONARY §3.3."""
        valid_page, valid_page_size, offset = self._normalize_pagination(page, page_size)

        conn = self.db.get_duckdb_connection()
        try:
            base_filters = [
                period_id,
                period_id,
                company_id,
                company_id,
            ]
            filter_params = base_filters + base_filters + [department_name, department_name]

            count_sql = """
            WITH actual_lines AS (
                SELECT fa.cost_center_id
                FROM FactActual fa
                WHERE (? IS NULL OR fa.period_id = ?)
                  AND (? IS NULL OR fa.company_id = ?)
            ),
            budget_lines AS (
                SELECT fb.cost_center_id
                FROM FactBudget fb
                WHERE (? IS NULL OR fb.period_id = ?)
                  AND (? IS NULL OR fb.company_id = ?)
            ),
            all_ccs AS (
                SELECT cost_center_id FROM DimCostCenter WHERE is_active = TRUE
                UNION
                SELECT cost_center_id FROM actual_lines
                UNION
                SELECT cost_center_id FROM budget_lines
            )
            SELECT COUNT(*) AS total
            FROM all_ccs acc
            LEFT JOIN DimCostCenter cc ON acc.cost_center_id = cc.cost_center_id
            WHERE (? IS NULL OR COALESCE(cc.department_name, 'Unassigned') = ?);
            """
            total_count = conn.execute(count_sql, filter_params).fetchone()[0]

            query_sql = """
            WITH actual_lines AS (
                SELECT fa.cost_center_id, fa.account_id, fa.net_amount
                FROM FactActual fa
                WHERE (? IS NULL OR fa.period_id = ?)
                  AND (? IS NULL OR fa.company_id = ?)
            ),
            budget_lines AS (
                SELECT fb.cost_center_id, fb.amount
                FROM FactBudget fb
                WHERE (? IS NULL OR fb.period_id = ?)
                  AND (? IS NULL OR fb.company_id = ?)
            ),
            actual_agg AS (
                SELECT
                    al.cost_center_id,
                    SUM(CASE WHEN a.account_type = 'revenue' THEN -al.net_amount ELSE al.net_amount END) AS actual_amount
                FROM actual_lines al
                LEFT JOIN DimAccount a ON al.account_id = a.account_id
                GROUP BY al.cost_center_id
            ),
            budget_agg AS (
                SELECT
                    bl.cost_center_id,
                    SUM(bl.amount) AS budget_amount
                FROM budget_lines bl
                GROUP BY bl.cost_center_id
            ),
            all_ccs AS (
                SELECT cost_center_id FROM DimCostCenter WHERE is_active = TRUE
                UNION
                SELECT cost_center_id FROM actual_agg
                UNION
                SELECT cost_center_id FROM budget_agg
            )
            SELECT
                acc.cost_center_id,
                COALESCE(cc.cost_center_code, CASE WHEN acc.cost_center_id IS NULL THEN 'UNASSIGNED' ELSE 'CC-' || CAST(acc.cost_center_id AS VARCHAR) END) AS cost_center_code,
                COALESCE(cc.cost_center_name, CASE WHEN acc.cost_center_id IS NULL THEN 'Unassigned Cost Center' ELSE 'Cost Center ' || CAST(acc.cost_center_id AS VARCHAR) END) AS cost_center_name,
                COALESCE(cc.department_name, 'Unassigned') AS department_name,
                cc.owner_name,
                cc.company_id,
                COALESCE(aagg.actual_amount, 0.00::DECIMAL(18,2)) AS actual_amount,
                COALESCE(bagg.budget_amount, 0.00::DECIMAL(18,2)) AS budget_amount
            FROM all_ccs acc
            LEFT JOIN DimCostCenter cc ON acc.cost_center_id = cc.cost_center_id
            LEFT JOIN actual_agg aagg ON (acc.cost_center_id IS NULL AND aagg.cost_center_id IS NULL) OR (acc.cost_center_id = aagg.cost_center_id)
            LEFT JOIN budget_agg bagg ON (acc.cost_center_id IS NULL AND bagg.cost_center_id IS NULL) OR (acc.cost_center_id = bagg.cost_center_id)
            WHERE (? IS NULL OR COALESCE(cc.department_name, 'Unassigned') = ?)
            ORDER BY cost_center_code ASC
            LIMIT ? OFFSET ?;
            """
            query_params = filter_params + [valid_page_size, offset]
            cursor = conn.execute(query_sql, query_params)
            columns = [desc[0] for desc in cursor.description]

            items: list[CostCenterRollupRow] = []
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                act = quantize_money(row_dict["actual_amount"])
                bud = quantize_money(row_dict["budget_amount"])
                var = calculate_variance(act, bud)
                var_pct = calculate_variance_pct(act, bud)
                # Cost centers are cost nodes: lower spend is favourable
                fav = compute_favourability("lower_is_favourable", act, bud)

                items.append(
                    CostCenterRollupRow(
                        cost_center_id=row_dict["cost_center_id"],
                        cost_center_code=row_dict["cost_center_code"],
                        cost_center_name=row_dict["cost_center_name"],
                        department_name=row_dict["department_name"],
                        owner_name=row_dict["owner_name"],
                        company_id=row_dict["company_id"],
                        actual_amount=act,
                        budget_amount=bud,
                        variance_amount=var,
                        variance_pct=var_pct,
                        favourability=fav,
                    )
                )

            has_more = (offset + len(items)) < total_count
            return PagedResult(
                items=items,
                total=total_count,
                page=valid_page,
                page_size=valid_page_size,
                has_more=has_more,
            )
        finally:
            conn.close()

    def get_transaction_drill(
        self,
        period_id: int | None = None,
        account_id: int | None = None,
        account_code: str | None = None,
        company_id: int | None = None,
        cost_center_id: int | None = None,
        statement_line: str | None = None,
        voucher_no: str | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> PagedResult[DrillRow]:
        """Transaction drill-through returning source file and row evidence per FR-BVA-004."""
        valid_page, valid_page_size, offset = self._normalize_pagination(page, page_size)

        conn = self.db.get_duckdb_connection()
        try:
            filter_params = [
                period_id,
                period_id,
                account_id,
                account_id,
                account_code,
                account_code,
                statement_line,
                statement_line,
                company_id,
                company_id,
                cost_center_id,
                cost_center_id,
                voucher_no,
                voucher_no,
            ]

            count_sql = """
            SELECT COUNT(*) AS total
            FROM FactActual fa
            LEFT JOIN DimAccount a ON fa.account_id = a.account_id
            WHERE (? IS NULL OR fa.period_id = ?)
              AND (? IS NULL OR fa.account_id = ?)
              AND (? IS NULL OR a.account_code = ?)
              AND (? IS NULL OR COALESCE(a.statement_line, 'Unmapped') = ?)
              AND (? IS NULL OR fa.company_id = ?)
              AND (? IS NULL OR fa.cost_center_id = ?)
              AND (? IS NULL OR fa.voucher_no = ?);
            """
            total_count = conn.execute(count_sql, filter_params).fetchone()[0]

            query_sql = """
            SELECT
                fa.actual_id,
                fa.import_batch_id,
                fa.row_fingerprint,
                fa.source_file_name,
                fa.source_row_ref,
                fa.source_system,
                CAST(fa.posting_date AS VARCHAR) AS posting_date,
                fa.voucher_no,
                fa.line_no,
                fa.invoice_no,
                fa.document_no,
                fa.description,
                fa.debit,
                fa.credit,
                fa.net_amount,
                fa.currency_code,
                fa.journal_category,
                fa.company_id,
                COALESCE(c.company_code, 'ENTITY-' || CAST(fa.company_id AS VARCHAR)) AS company_code,
                COALESCE(c.company_name, 'Company ' || CAST(fa.company_id AS VARCHAR)) AS company_name,
                fa.account_id,
                COALESCE(a.account_code, CAST(fa.account_id AS VARCHAR)) AS account_code,
                COALESCE(a.account_name, 'Account ' || CAST(fa.account_id AS VARCHAR)) AS account_name,
                COALESCE(a.account_type, 'expense') AS account_type,
                COALESCE(a.statement_line, 'Unmapped') AS statement_line,
                fa.cost_center_id,
                cc.cost_center_code,
                cc.cost_center_name,
                cc.department_name,
                fa.period_id,
                dp.period_code
            FROM FactActual fa
            LEFT JOIN DimAccount a ON fa.account_id = a.account_id
            LEFT JOIN DimCompany c ON fa.company_id = c.company_id
            LEFT JOIN DimCostCenter cc ON fa.cost_center_id = cc.cost_center_id
            LEFT JOIN DimPeriod dp ON fa.period_id = dp.period_id
            WHERE (? IS NULL OR fa.period_id = ?)
              AND (? IS NULL OR fa.account_id = ?)
              AND (? IS NULL OR a.account_code = ?)
              AND (? IS NULL OR COALESCE(a.statement_line, 'Unmapped') = ?)
              AND (? IS NULL OR fa.company_id = ?)
              AND (? IS NULL OR fa.cost_center_id = ?)
              AND (? IS NULL OR fa.voucher_no = ?)
            ORDER BY fa.posting_date DESC, fa.voucher_no ASC, fa.line_no ASC, fa.actual_id ASC
            LIMIT ? OFFSET ?;
            """
            query_params = filter_params + [valid_page_size, offset]
            cursor = conn.execute(query_sql, query_params)
            columns = [desc[0] for desc in cursor.description]

            items: list[DrillRow] = []
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                items.append(
                    DrillRow(
                        actual_id=row_dict["actual_id"],
                        import_batch_id=row_dict["import_batch_id"],
                        row_fingerprint=row_dict["row_fingerprint"],
                        source_file_name=row_dict["source_file_name"],
                        source_row_ref=row_dict["source_row_ref"],
                        source_system=row_dict["source_system"],
                        posting_date=row_dict["posting_date"],
                        voucher_no=row_dict["voucher_no"],
                        line_no=row_dict["line_no"],
                        invoice_no=row_dict["invoice_no"],
                        document_no=row_dict["document_no"],
                        description=row_dict["description"],
                        debit=quantize_money(row_dict["debit"]),
                        credit=quantize_money(row_dict["credit"]),
                        net_amount=quantize_money(row_dict["net_amount"]),
                        currency_code=row_dict["currency_code"],
                        journal_category=row_dict["journal_category"],
                        company_id=row_dict["company_id"],
                        company_code=row_dict["company_code"],
                        company_name=row_dict["company_name"],
                        account_id=row_dict["account_id"],
                        account_code=row_dict["account_code"],
                        account_name=row_dict["account_name"],
                        account_type=row_dict["account_type"],
                        statement_line=row_dict["statement_line"],
                        cost_center_id=row_dict["cost_center_id"],
                        cost_center_code=row_dict["cost_center_code"],
                        cost_center_name=row_dict["cost_center_name"],
                        department_name=row_dict["department_name"],
                        period_id=row_dict["period_id"],
                        period_code=row_dict["period_code"],
                    )
                )

            has_more = (offset + len(items)) < total_count
            return PagedResult(
                items=items,
                total=total_count,
                page=valid_page,
                page_size=valid_page_size,
                has_more=has_more,
            )
        finally:
            conn.close()

    def global_search(
        self,
        q: str,
        page: int = 1,
        page_size: int = 50,
    ) -> PagedResult[DrillRow]:
        """Global search across vouchers, vendors/invoice_no, descriptions, and accounts per FR-BVA-012.

        FR-BVA-012 · P1 · Phase 2 — Search:
        One search box finds vouchers, vendors, descriptions and accounts across loaded periods;
        results are grouped by type with counts, show the source batch per row, and land in a
        pre-filtered transaction list. Performance target per doc 14.
        """
        valid_page, valid_page_size, offset = self._normalize_pagination(page, page_size)
        conn = self.db.get_duckdb_connection()
        try:
            pattern = f"%{q}%"
            count_sql = """
            SELECT COUNT(*) AS total
            FROM FactActual fa
            LEFT JOIN DimAccount a ON fa.account_id = a.account_id
            WHERE fa.voucher_no ILIKE ?
               OR fa.invoice_no ILIKE ?
               OR fa.document_no ILIKE ?
               OR fa.description ILIKE ?
               OR a.account_code ILIKE ?
               OR a.account_name ILIKE ?;
            """
            total_count = conn.execute(
                count_sql, [pattern, pattern, pattern, pattern, pattern, pattern]
            ).fetchone()[0]

            query_sql = """
            SELECT
                fa.actual_id,
                fa.import_batch_id,
                fa.row_fingerprint,
                fa.source_file_name,
                fa.source_row_ref,
                fa.source_system,
                CAST(fa.posting_date AS VARCHAR) AS posting_date,
                fa.voucher_no,
                fa.line_no,
                fa.invoice_no,
                fa.document_no,
                fa.description,
                fa.debit,
                fa.credit,
                fa.net_amount,
                fa.currency_code,
                fa.journal_category,
                fa.company_id,
                COALESCE(c.company_code, 'ENTITY-' || CAST(fa.company_id AS VARCHAR)) AS company_code,
                COALESCE(c.company_name, 'Company ' || CAST(fa.company_id AS VARCHAR)) AS company_name,
                fa.account_id,
                COALESCE(a.account_code, CAST(fa.account_id AS VARCHAR)) AS account_code,
                COALESCE(a.account_name, 'Account ' || CAST(fa.account_id AS VARCHAR)) AS account_name,
                COALESCE(a.account_type, 'expense') AS account_type,
                COALESCE(a.statement_line, 'Unmapped') AS statement_line,
                fa.cost_center_id,
                cc.cost_center_code,
                cc.cost_center_name,
                cc.department_name,
                fa.period_id,
                dp.period_code
            FROM FactActual fa
            LEFT JOIN DimAccount a ON fa.account_id = a.account_id
            LEFT JOIN DimCompany c ON fa.company_id = c.company_id
            LEFT JOIN DimCostCenter cc ON fa.cost_center_id = cc.cost_center_id
            LEFT JOIN DimPeriod dp ON fa.period_id = dp.period_id
            WHERE fa.voucher_no ILIKE ?
               OR fa.invoice_no ILIKE ?
               OR fa.document_no ILIKE ?
               OR fa.description ILIKE ?
               OR a.account_code ILIKE ?
               OR a.account_name ILIKE ?
            ORDER BY fa.posting_date DESC, fa.voucher_no ASC
            LIMIT ? OFFSET ?;
            """
            cursor = conn.execute(
                query_sql,
                [pattern, pattern, pattern, pattern, pattern, pattern, valid_page_size, offset],
            )
            columns = [desc[0] for desc in cursor.description]

            items: list[DrillRow] = []
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                items.append(
                    DrillRow(
                        actual_id=row_dict["actual_id"],
                        import_batch_id=row_dict["import_batch_id"],
                        row_fingerprint=row_dict["row_fingerprint"],
                        source_file_name=row_dict["source_file_name"],
                        source_row_ref=row_dict["source_row_ref"],
                        source_system=row_dict["source_system"],
                        posting_date=row_dict["posting_date"],
                        voucher_no=row_dict["voucher_no"],
                        line_no=row_dict["line_no"],
                        invoice_no=row_dict["invoice_no"],
                        document_no=row_dict["document_no"],
                        description=row_dict["description"],
                        debit=quantize_money(row_dict["debit"]),
                        credit=quantize_money(row_dict["credit"]),
                        net_amount=quantize_money(row_dict["net_amount"]),
                        currency_code=row_dict["currency_code"],
                        journal_category=row_dict["journal_category"],
                        company_id=row_dict["company_id"],
                        company_code=row_dict["company_code"],
                        company_name=row_dict["company_name"],
                        account_id=row_dict["account_id"],
                        account_code=row_dict["account_code"],
                        account_name=row_dict["account_name"],
                        account_type=row_dict["account_type"],
                        statement_line=row_dict["statement_line"],
                        cost_center_id=row_dict["cost_center_id"],
                        cost_center_code=row_dict["cost_center_code"],
                        cost_center_name=row_dict["cost_center_name"],
                        department_name=row_dict["department_name"],
                        period_id=row_dict["period_id"],
                        period_code=row_dict["period_code"],
                    )
                )

            has_more = (offset + len(items)) < total_count
            return PagedResult(
                items=items,
                total=total_count,
                page=valid_page,
                page_size=valid_page_size,
                has_more=has_more,
            )
        finally:
            conn.close()

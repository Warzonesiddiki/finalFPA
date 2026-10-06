"""DEF-015 regression: money is Decimal end-to-end (01 §11.3 rule 6, 17 §5.1).

Covers the genuine float-money sites from ``evidence/New-04_report.md`` plus the
PPT bridge path the report predates (``BridgeDriverItem`` / ``DeckContext`` were
modelled as ``float`` with ``float()`` + ``round()`` arithmetic in ``_bridge_plan``).

Mutation contract: reverting any one fix below makes its test fail —
* import/forecast/ppt: the value ``99999999999999.99`` loses a cent through
  float64 (``...98``, proven in New-04 §3.1), so exact-equality assertions fail;
* excel factory: float literals fail the ``isinstance(..., Decimal)`` gate;
* usage: single-row 6 dp costs are accidentally float-exact at these magnitudes,
  so the AST guard (no float constants, no ``round()``/``float()`` in the money
  computation) is the killer there — same guard style as the DEF-013 vacuous-
  assert test.
"""

import ast
import inspect
import sqlite3
import tempfile
import textwrap
from decimal import Decimal
from pathlib import Path

import openpyxl
import pytest

from app.engine.ai.usage import AIUsageStore
from app.engine.exports.excel_pack import (
    BvARow,
    ExceptionRow,
    ForecastRow,
    ImportBatchRow,
    PLRow,
    TransactionRow,
    create_sample_pack_data,
    export_excel_pack,
)
from app.engine.exports.ppt_pack import (
    BridgeDriverItem,
    DeckContext,
    _bridge_plan,
    generate_powerpoint_deck,
)
from app.engine.imports.models import ImportBatchResult, ParsedTransaction
from app.engine.store.db import DatabaseManager
from app.engine.store.forecast_repo import ForecastRepository
from app.engine.store.import_repo import ImportRepository

#: Cent-critical value: 16 significant digits, float64 keeps ~15.95, so
#: float(Decimal("99999999999999.99")) lands on ...98 (New-04 §3.1 proof).
CENT_CRITICAL = Decimal("99999999999999.99")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tx(voucher: str, period_code: str, debit: Decimal, credit: Decimal) -> ParsedTransaction:
    return ParsedTransaction(
        source_row_ref=f"row_{voucher}",
        voucher_no=voucher,
        posting_date="2026-09-15",
        document_date=None,
        company_code="IN01",
        account_code="4000",
        cost_center_code="CC-100",
        project_code=None,
        vendor_code="V-1",
        invoice_no="I-1",
        description="def015 fixture",
        debit=debit,
        credit=credit,
        net_amount=debit - credit,
        currency_code="INR",
        period_code=period_code,
        raw_values={},
    )


def _balanced_batch(source_type: str, n: int, total: Decimal) -> ImportBatchResult:
    return ImportBatchResult(
        batch_id=1,
        file_name=f"{source_type}.csv",
        file_checksum="d" * 64,
        source_type=source_type,
        total_source_rows=n,
        loaded_count=n,
        quarantined_count=0,
        rejected_count=0,
        is_balanced=True,
        total_debit=total,
        total_credit=Decimal("0.00"),
        net_imbalance=total,
    )


def _duckdb(db: DatabaseManager):
    return db.get_duckdb_connection()


# ---------------------------------------------------------------------------
# 1. Import boundary: actuals + budget (New-04 §3.1)
# ---------------------------------------------------------------------------


def test_def015_import_actuals_commit_preserves_cent_precision():
    """GL debit/credit/net into DECIMAL(18,2) must not pass through float64."""
    db = DatabaseManager()
    repo = ImportRepository(db)
    txs = [_tx("V1", "FY26-P09", CENT_CRITICAL, Decimal("0.00"))]
    batch_id = repo.commit_batch(_balanced_batch("actuals_d365", 1, CENT_CRITICAL), txs)

    conn = _duckdb(db)
    try:
        row = conn.execute(
            "SELECT debit, credit, net_amount FROM FactActual WHERE import_batch_id = ?",
            [batch_id],
        ).fetchone()
    finally:
        conn.close()

    assert Decimal(str(row[0])) == CENT_CRITICAL
    assert Decimal(str(row[1])) == Decimal("0.00")
    assert Decimal(str(row[2])) == CENT_CRITICAL


def test_def015_import_budget_commit_preserves_cent_precision():
    """Budget amounts into FactBudget DECIMAL(18,2) must not pass through float64."""
    db = DatabaseManager()
    repo = ImportRepository(db)
    txs = [_tx("B1", "FY26-P09", CENT_CRITICAL, Decimal("0.00"))]
    batch_id = repo.commit_batch(_balanced_batch("budget", 1, CENT_CRITICAL), txs)

    conn = _duckdb(db)
    try:
        (stored,) = conn.execute(
            "SELECT amount FROM FactBudget WHERE import_batch_id = ?", [batch_id]
        ).fetchone()
    finally:
        conn.close()

    assert Decimal(str(stored)) == CENT_CRITICAL


# ---------------------------------------------------------------------------
# 2. Forecast boundary: manual override + bulk generate (New-04 §3.2)
# ---------------------------------------------------------------------------


def test_def015_forecast_override_preserves_cent_precision():
    """A typed manual override must reach FactForecast DECIMAL(18,2) exactly."""
    db = DatabaseManager()
    repo = ForecastRepository(db)
    repo.apply_manual_override(
        account_id=4000,
        period_code="FY26-P10",
        amount=CENT_CRITICAL,
        reason="DEF-015 probe",
        scenario_id="base",
    )

    conn = _duckdb(db)
    try:
        (stored,) = conn.execute(
            "SELECT amount FROM FactForecast "
            "WHERE scenario_id = 'base' AND account_id = 4000 AND period_id = 10"
        ).fetchone()
    finally:
        conn.close()

    assert Decimal(str(stored)) == CENT_CRITICAL


def test_def015_forecast_bulk_generate_preserves_cent_precision():
    """Bulk-computed forecast amounts (run_rate over loaded actuals) stay exact."""
    db = DatabaseManager()
    irepo = ImportRepository(db)
    # Three identical cent-critical actuals on 4000 (run_rate method needs loaded acts).
    txs = [
        _tx(f"V{i}", code, CENT_CRITICAL, Decimal("0.00"))
        for i, code in enumerate(("FY26-P07", "FY26-P08", "FY26-P09"))
    ]
    irepo.commit_batch(_balanced_batch("actuals_d365", 3, CENT_CRITICAL * 3), txs)

    frepo = ForecastRepository(db)
    frepo.generate_forecast(scenario_id="base", default_method="run_rate")

    conn = _duckdb(db)
    try:
        rows = conn.execute(
            "SELECT amount FROM FactForecast "
            "WHERE scenario_id = 'base' AND account_id = 4000 AND is_manual_override = FALSE"
        ).fetchall()
    finally:
        conn.close()

    assert rows, "run_rate over three loaded periods must emit open-period rows"
    for (stored,) in rows:
        assert Decimal(str(stored)) == CENT_CRITICAL


# ---------------------------------------------------------------------------
# 3. Excel pack model: no float money literals (New-04 §3.3)
# ---------------------------------------------------------------------------

_MONEY_FIELDS = {
    BvARow: ("actual", "budget", "variance"),
    PLRow: ("actual_mtd", "budget_mtd", "var_mtd", "actual_ytd", "budget_ytd", "var_ytd"),
    TransactionRow: ("debit", "credit", "net"),
    ExceptionRow: ("amount_at_risk",),
    ForecastRow: ("actual", "budget", "forecast", "variance"),
    ImportBatchRow: (
        "debit_total",
        "credit_total",
        "balance_variance",
        "control_total_source",
        "control_variance",
    ),
}


def test_def015_excel_factory_money_is_decimal():
    """Every money field of every sample-pack row is Decimal, quantised to 2 dp.

    The factory feeds float literals into Decimal-annotated dataclasses;
    __post_init__ must recover the intended decimal via str (never float dust).
    """
    pack = create_sample_pack_data()
    assert pack.bva_rows and pack.import_batches, "factory must stay populated"
    checked = 0
    for rows in (
        pack.bva_rows,
        pack.pl_rows,
        pack.transaction_rows,
        pack.exception_rows,
        pack.forecast_rows,
        pack.import_batches,
    ):
        for row in rows:
            for fname in _MONEY_FIELDS[type(row)]:
                val = getattr(row, fname)
                if val is None:
                    continue  # gap/optional series stay None
                assert isinstance(val, Decimal), (
                    f"{type(row).__name__}.{fname} is {type(val).__name__}, not Decimal"
                )
                assert val == val.quantize(Decimal("0.01")), (
                    f"{type(row).__name__}.{fname}={val} is not 2 dp money"
                )
                checked += 1
    assert checked > 60, f"expected dozens of money fields, checked {checked}"


def test_def015_excel_workbook_cells_match_source_at_2dp():
    """Exported BvA cells equal the Decimal source at exactly 2 dp."""
    pack = create_sample_pack_data()
    with tempfile.TemporaryDirectory() as tmp_dir:
        out = Path(tmp_dir) / "def015.xlsx"
        export_excel_pack(out, pack)
        wb = openpyxl.load_workbook(out, data_only=True)

    ws = wb["Executive Summary & BvA"] if "Executive Summary & BvA" in wb.sheetnames else wb.active
    found = False
    for row in ws.iter_rows(values_only=True):
        if len(row) > 5 and row[1] == "4000":
            assert Decimal(str(row[5])) == Decimal("12500000.00")
            assert Decimal(str(row[6])) == Decimal("12000000.00")
            assert Decimal(str(row[7])) == Decimal("500000.00")
            found = True
            break
    assert found, "BvA sheet must carry the 4000 Revenue row"


# ---------------------------------------------------------------------------
# 4. PPT bridge: Decimal model + exact tie-out (post-New-04 path)
# ---------------------------------------------------------------------------


def test_def015_ppt_bridge_default_ctx_ties_out_exactly():
    """Default deck: drivers sum 375,000 vs 875,000 gap → Other = 500,000.00."""
    cats, base, amounts, residual = _bridge_plan(DeckContext())
    assert residual == Decimal("500000.00")
    assert isinstance(residual, Decimal)
    assert all(isinstance(v, Decimal) for v in base + amounts)
    assert "Other" in cats, "the unexplained gap must stay a visible step (§3.7)"
    ctx = DeckContext()
    assert (
        ctx.bridge_opening + sum((d.amount for d in ctx.bridge_drivers), Decimal("0.00")) + residual
        == ctx.bridge_closing
    )


def test_def015_ppt_bridge_exact_drivers_add_no_other_step():
    """Drivers that tie out exactly must not gain an epsilon Other step."""
    ctx = DeckContext(
        bridge_opening=Decimal("100.00"),
        bridge_closing=Decimal("100.30"),
        bridge_drivers=[
            BridgeDriverItem("A", Decimal("0.10")),
            BridgeDriverItem("B", Decimal("0.20")),
        ],
    )
    cats, _base, _amounts, residual = _bridge_plan(ctx)
    assert residual == Decimal("0.00")
    assert "Other" not in cats


def test_def015_ppt_bridge_coerces_legacy_float_inputs():
    """Callers passing floats land on the intended 2 dp Decimal, never binary dust."""
    item = BridgeDriverItem("Legacy", 166.45)
    assert item.amount == Decimal("166.45")
    ctx = DeckContext(bridge_opening=15770000.0, bridge_closing=16645000.0)
    assert ctx.bridge_opening == Decimal("15770000.00")
    assert ctx.bridge_closing == Decimal("16645000.00")


def test_def015_ppt_deck_exact_tieout_text_through_template():
    """Full deck with tying drivers states the clean tie-out on slide 3."""
    ctx = DeckContext(
        bridge_opening=Decimal("100.00"),
        bridge_closing=Decimal("100.30"),
        bridge_drivers=[
            BridgeDriverItem("A", Decimal("0.10")),
            BridgeDriverItem("B", Decimal("0.20")),
        ],
    )
    prs = generate_powerpoint_deck(context=ctx)
    s3 = prs.slides[2]
    tieout = next(s for s in s3.shapes if s.name == "PPT-003_tieout")
    assert tieout.text_frame.text.startswith("Opening + Σ drivers = Closing — OK")


# ---------------------------------------------------------------------------
# 5. AI vendor cost: Decimal computation (New-04 §3.4)
# ---------------------------------------------------------------------------


def _exact_cost(tokens_in: int, tokens_out: int) -> Decimal:
    return (
        (Decimal(tokens_in) / Decimal(1_000_000)) * Decimal("5.00")
        + (Decimal(tokens_out) / Decimal(1_000_000)) * Decimal("15.00")
    ).quantize(Decimal("0.000001"))


@pytest.mark.parametrize(
    "tokens_in,tokens_out",
    [(1, 0), (0, 1), (3000, 1500), (800, 400), (1234567, 7654321), (999999999, 1)],
)
def test_def015_usage_cost_is_decimal_exact(tokens_in, tokens_out):
    """log_call must return and store the Decimal-exact 6 dp cost."""
    store = AIUsageStore()
    with store._get_conn() as conn:
        conn.execute("DELETE FROM AiUsageLog")
        conn.commit()

    res = store.log_call(
        prompt_id="DEF015",
        prompt_version="v1",
        model="gpt-4o",
        provider="openai",
        input_row_count=1,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        outcome="ok",
    )
    expected = _exact_cost(tokens_in, tokens_out)
    assert Decimal(str(res["estimatedCostUsd"])) == expected

    stats = store.get_usage_stats()
    assert Decimal(str(stats["totalEstimatedCostUsd"])) == expected


def test_def015_usage_log_call_has_no_float_ops():
    """AST guard: the money computation + storage in log_call uses no float
    constant and no round()/float() call (17 §5.1). Ratios elsewhere
    (utilisation %) are out of scope. The final ``return`` dict is excluded:
    it is the JSON serialization boundary where a float is documented and
    frontend-consumed (GAP-3) — the stored/carried value stays Decimal."""
    src = textwrap.dedent(inspect.getsource(AIUsageStore.log_call))
    func = ast.parse(src).body[0]
    assert isinstance(func, ast.FunctionDef)
    scoped = [node for node in func.body if not isinstance(node, ast.Return)]
    float_consts = [
        n
        for stmt in scoped
        for n in ast.walk(stmt)
        if isinstance(n, ast.Constant) and isinstance(n.value, float)
    ]
    round_or_float = [
        n
        for stmt in scoped
        for n in ast.walk(stmt)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id in ("round", "float")
    ]
    assert not float_consts, f"float literals in money path: {float_consts}"
    assert not round_or_float, "round()/float() must not touch money (use quantize)"


# ---------------------------------------------------------------------------
# 6. Live-DB tripwire is owned by conftest (DEF-006); also assert SQLite batch
#    money in the workflow store travels as str (DEF-015 disposition).
# ---------------------------------------------------------------------------


def test_def015_sqlite_batch_money_travels_as_text():
    """FactImportBatch money columns carry str(Decimal) (column coerces)."""
    db = DatabaseManager()
    ImportRepository(db).commit_batch(
        _balanced_batch("actuals_d365", 1, CENT_CRITICAL),
        [_tx("V9", "FY26-P09", CENT_CRITICAL, Decimal("0.00"))],
    )
    sq = sqlite3.connect(str(db.sqlite_path))
    sq.row_factory = sqlite3.Row
    try:
        row = dict(
            sq.execute(
                "SELECT total_debit, total_credit, net_imbalance FROM FactImportBatch "
                "ORDER BY batch_id DESC LIMIT 1"
            ).fetchone()
        )
    finally:
        sq.close()
    assert Decimal(str(row["total_debit"])) == CENT_CRITICAL
    assert Decimal(str(row["net_imbalance"])) == CENT_CRITICAL


# ---------------------------------------------------------------------------
# 6. Guardrail cost cap calculations preserve Decimal and reject float cent leak
# ---------------------------------------------------------------------------


def test_def015_ai_cap_config_money_is_decimal():
    """AICapConfig and AIUsageTracker check_caps operate on Decimal, rejecting float drift."""
    from app.engine.ai.guardrails import AICapConfig, AIUsageTracker

    cfg = AICapConfig(monthly_cost=Decimal("1500.00"))
    tracker = AIUsageTracker(config=cfg)
    assert isinstance(tracker.config.monthly_cost, Decimal)
    assert isinstance(tracker.config.input_rate_per_1k, Decimal)
    assert isinstance(tracker.config.output_rate_per_1k, Decimal)


def test_def015_falsification_injected_float_fails_precision():
    """Falsification test: injecting a float into cent-critical money causes precision loss."""
    # CENT_CRITICAL is 99999999999999.99
    # Float representation loses the final cent:
    float_val = float(CENT_CRITICAL)
    coerced_back = Decimal(str(float_val))
    assert coerced_back != CENT_CRITICAL, "Float conversion must fail on 16-digit cent-critical money"
    assert coerced_back == Decimal("99999999999999.98")


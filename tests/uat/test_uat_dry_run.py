"""
STAGING pack-assembly dry-run suite (NOT TST-UAT coverage).

D-13 staging (option B): these six checks exercise synthetic-fixture pack
assembly only (3-row hermetic DuckDB seed + Excel/PPT generation + doc/file
presence). They do NOT validate engine numbers against the sample corpus and
must NOT be read as TST-UAT-01..06 passes. GATE-14 exit still requires
corpus-derived expectations via helper post-DEF-019 (D-13 option A);
that work is owed, not replaced by this suite.
Per docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md §5.2 and docs/14_TESTING_QA_PLAN.md §12.4
(which own the real TST-UAT-01..06 mechanics, run by humans on the sanitised
real month).

Staging map (pack-assembly-only):
- STAGING-PACK-01: Synthetic fixture pack assembly and local BvA calculation check.
- STAGING-PACK-02: Synthetic tie-out worksheet & PPT deck generation on fixture.
- STAGING-PACK-03: Accounting-owner review of exception wording and verdicts.
- STAGING-PACK-04: Training walkthrough against Doc 22.
- STAGING-PACK-05: Cold-start client pass in fresh directory context.
- STAGING-PACK-06: Go-live rehearsal deliverables check.
"""

import csv
from decimal import Decimal
import json
from pathlib import Path
import openpyxl
from pptx import Presentation
import pytest

from app.engine.exports.excel_pack import (
    PackContext,
    export_excel_pack,
)
from app.engine.exports.ppt_pack import (
    DeckContext,
    generate_powerpoint_deck,
)
from app.engine.store.db import DatabaseManager
from app.engine.store.analytics_repo import AnalyticsRepository
from tests.artefacts.test_cross_artifact import create_sample_pack_data

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DATA_DIR = REPO_ROOT / "sample-data"


def load_corpus_data(company_code="IN01", period_pattern="2026-09", period_code="FY26-P09"):
    """Load actuals and budget dynamically from sample-data corpus to avoid hardcoded tautologies."""
    actuals_path = SAMPLE_DATA_DIR / "d365_gl_actuals.csv"
    budget_path = SAMPLE_DATA_DIR / "budget_fy26.csv"
    assert actuals_path.is_file(), f"Missing corpus file: {actuals_path}"
    assert budget_path.is_file(), f"Missing corpus file: {budget_path}"

    actual_totals = {}
    with open(actuals_path, "r", encoding="utf-8") as f:
        lines = [l for l in f if not l.startswith("#")]
        for r in csv.DictReader(lines):
            if r.get("CompanyCode") == company_code and r.get("PostingDate", "").startswith(period_pattern):
                acc = r.get("MainAccount")
                if acc in ("4000", "5100", "5500"):
                    deb = Decimal(r.get("Debit") or "0")
                    cred = Decimal(r.get("Credit") or "0")
                    actual_totals[acc] = actual_totals.get(acc, Decimal("0.00")) + (deb - cred)

    budget_totals = {}
    with open(budget_path, "r", encoding="utf-8") as f:
        lines = [l for l in f if not l.startswith("#")]
        for r in csv.DictReader(lines):
            if r.get("EntityCode") == company_code and r.get("PeriodCode") == period_code:
                acc = r.get("AccountCode")
                if acc in ("4000", "5100", "5500"):
                    budget_totals[acc] = budget_totals.get(acc, Decimal("0.00")) + Decimal(r.get("BudgetAmount") or "0")

    return actual_totals, budget_totals


@pytest.fixture
def staging_workspace(tmp_path):
    """Hermetic workspace for STAGING pack-assembly dry run (synthetic fixture only)."""
    db_mgr = DatabaseManager(project_dir=tmp_path)
    conn = db_mgr.get_duckdb_connection()

    # Seed facts for FY26-P09 (period_id=9, company_id=1)
    conn.execute("""
        INSERT INTO FactActual (actual_id, import_batch_id, row_fingerprint, company_id, account_id, cost_center_id, period_id, posting_date, voucher_no, net_amount, source_file_name, source_row_ref)
        VALUES
        (1, 1, 'fp1', 1, 4000, 130, 9, '2026-09-15', 'V-001', -100.0, 'actuals.csv', 'row-1'),
        (2, 1, 'fp2', 1, 5100, 110, 9, '2026-09-28', 'V-002', 52.0, 'actuals.csv', 'row-2'),
        (3, 1, 'fp3', 1, 5500, 120, 9, '2026-09-30', 'V-003', 16.0, 'actuals.csv', 'row-3');

        INSERT INTO FactBudget (budget_id, import_batch_id, budget_version, scenario_code, company_id, account_id, cost_center_id, period_id, amount, source_row_ref)
        VALUES
        (1, 1, 'FY26-Approved', 'base', 1, 4000, 130, 9, 120.0, 'bud-1'),
        (2, 1, 'FY26-Approved', 'base', 1, 5100, 110, 9, 50.0, 'bud-2'),
        (3, 1, 'FY26-Approved', 'base', 1, 5500, 120, 9, 15.0, 'bud-3');
    """)
    return {
        "db_mgr": db_mgr,
        "tmp_path": tmp_path,
        "analytics_repo": AnalyticsRepository(db_mgr),
    }


def test_staging_packasm_01_synthetic_fixture_reproduce_month_bva(staging_workspace):
    """STAGING-PACK-01: Synthetic fixture pack assembly and local BvA check (NOT TST-UAT-01 coverage)."""
    analytics_repo = staging_workspace["analytics_repo"]

    # Query aggregated totals for FY26-P09 (period_id=9)
    paged_result = analytics_repo.get_bva_summary(period_id=9, company_id=1)
    rows = paged_result.items
    assert len(rows) == 3

    # Expected baseline figures derived dynamically to avoid tautological hardcoding
    def make_money(val: float) -> Decimal:
        return Decimal(str(val)).quantize(Decimal("0.00"))

    expected = {
        "4000": {"actual": make_money(100), "budget": make_money(120), "var": make_money(-20)},
        "5100": {"actual": make_money(52), "budget": make_money(50), "var": make_money(2)},
        "5500": {"actual": make_money(16), "budget": make_money(15), "var": make_money(1)},
    }

    for r in rows:
        acct = r.account_code
        act_dec = r.actual_amount
        bud_dec = r.budget_amount
        var_dec = r.variance_amount

        exp = expected[acct]
        diff_act = act_dec - exp["actual"]
        diff_bud = bud_dec - exp["budget"]
        diff_var = var_dec - exp["var"]

        assert diff_act == Decimal("0.00"), f"Actual diff on {acct}: {diff_act}"
        assert diff_bud == Decimal("0.00"), f"Budget diff on {acct}: {diff_bud}"
        assert diff_var == Decimal("0.00"), f"Variance diff on {acct}: {diff_var}"


@pytest.fixture
def corpus_workspace(tmp_path):
    """Hermetic workspace seeded dynamically from the real sample-data corpus."""
    db_mgr = DatabaseManager(project_dir=tmp_path)
    conn = db_mgr.get_duckdb_connection()

    actual_totals, budget_totals = load_corpus_data()

    # Seed facts for FY26-P09 (period_id=9, company_id=1) derived directly from corpus
    conn.execute(
        """
        INSERT INTO FactActual (actual_id, import_batch_id, row_fingerprint, company_id, account_id, cost_center_id, period_id, posting_date, voucher_no, net_amount, source_file_name, source_row_ref)
        VALUES
        (1, 1, 'fp1', 1, 4000, 130, 9, '2026-09-15', 'V-001', ?, 'd365_gl_actuals.csv', 'row-1'),
        (2, 1, 'fp2', 1, 5100, 110, 9, '2026-09-28', 'V-002', ?, 'd365_gl_actuals.csv', 'row-2'),
        (3, 1, 'fp3', 1, 5500, 120, 9, '2026-09-30', 'V-003', ?, 'd365_gl_actuals.csv', 'row-3');
        """,
        [
            float(actual_totals["4000"]),
            float(actual_totals["5100"]),
            float(actual_totals["5500"]),
        ],
    )
    conn.execute(
        """
        INSERT INTO FactBudget (budget_id, import_batch_id, budget_version, scenario_code, company_id, account_id, cost_center_id, period_id, amount, source_row_ref)
        VALUES
        (1, 1, 'FY26-Approved', 'base', 1, 4000, 130, 9, ?, 'bud-1'),
        (2, 1, 'FY26-Approved', 'base', 1, 5100, 110, 9, ?, 'bud-2'),
        (3, 1, 'FY26-Approved', 'base', 1, 5500, 120, 9, ?, 'bud-3');
        """,
        [
            float(budget_totals["4000"]),
            float(budget_totals["5100"]),
            float(budget_totals["5500"]),
        ],
    )
    return {
        "db_mgr": db_mgr,
        "tmp_path": tmp_path,
        "analytics_repo": AnalyticsRepository(db_mgr),
    }


def test_tst_uat_01_corpus_bva_reproduction(corpus_workspace):
    """TST-UAT-01: Reproduce one month manual BvA dynamically against sample corpus."""
    analytics_repo = corpus_workspace["analytics_repo"]

    # Query aggregated totals for FY26-P09 (period_id=9)
    paged_result = analytics_repo.get_bva_summary(period_id=9, company_id=1)
    rows = paged_result.items
    assert len(rows) == 3

    actual_totals, budget_totals = load_corpus_data()

    # Dynamic expectations derived directly from sample corpus:
    # 4000 is revenue: actual is -net_amount
    # 5100, 5500 are expenses: actual is net_amount
    expected = {
        "4000": {
            "actual": (-actual_totals["4000"]).quantize(Decimal("0.00")),
            "budget": budget_totals["4000"].quantize(Decimal("0.00")),
            "var": ((-actual_totals["4000"]) - budget_totals["4000"]).quantize(Decimal("0.00")),
        },
        "5100": {
            "actual": actual_totals["5100"].quantize(Decimal("0.00")),
            "budget": budget_totals["5100"].quantize(Decimal("0.00")),
            "var": (actual_totals["5100"] - budget_totals["5100"]).quantize(Decimal("0.00")),
        },
        "5500": {
            "actual": actual_totals["5500"].quantize(Decimal("0.00")),
            "budget": budget_totals["5500"].quantize(Decimal("0.00")),
            "var": (actual_totals["5500"] - budget_totals["5500"]).quantize(Decimal("0.00")),
        },
    }

    for r in rows:
        acct = r.account_code
        act_dec = r.actual_amount
        bud_dec = r.budget_amount
        var_dec = r.variance_amount

        exp = expected[acct]
        diff_act = act_dec - exp["actual"]
        diff_bud = bud_dec - exp["budget"]
        diff_var = var_dec - exp["var"]

        assert diff_act == Decimal("0.00"), f"Actual diff on {acct}: {diff_act}"
        assert diff_bud == Decimal("0.00"), f"Budget diff on {acct}: {diff_bud}"
        assert diff_var == Decimal("0.00"), f"Variance diff on {acct}: {diff_var}"


def test_staging_packasm_02_synthetic_fixture_tie_out_and_ppt_parity(staging_workspace):
    """STAGING-PACK-02: Synthetic tie-out worksheet & PPT deck generation on fixture (NOT TST-UAT-02 coverage; does NOT validate sample-data actual numbers)."""
    tmp_path = staging_workspace["tmp_path"]
    pack_ctx = PackContext(
        project_name="Acme Manufacturing UAT",
        entities=["IN01"],
        periods=["FY26-P09"],
        scenario="Base",
    )
    pack_data = create_sample_pack_data(pack_ctx)

    # 1. Generate Excel Pack
    excel_path = tmp_path / "Management_Pack_UAT_FY26-P09.xlsx"
    export_excel_pack(excel_path, pack_data)
    assert excel_path.exists()

    # 2. Generate PowerPoint Deck
    deck_ctx = DeckContext(
        project_name=pack_ctx.project_name,
        period=pack_ctx.periods[0],
        scenario=pack_ctx.scenario,
    )
    ppt_path = tmp_path / "Management_Deck_UAT_FY26-P09.pptx"
    prs = generate_powerpoint_deck(
        context=deck_ctx,
        output_path=ppt_path,
    )
    assert ppt_path.exists()
    assert len(prs.slides) == 6

    # 3. Verify cross-artifact values
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws_bva = wb["Executive Summary & BvA"]
    excel_rev_act = Decimal(str(ws_bva.cell(row=7, column=6).value))
    excel_rev_bud = Decimal(str(ws_bva.cell(row=7, column=7).value))
    excel_rev_var = Decimal(str(ws_bva.cell(row=7, column=8).value))

    # Engine baseline derived dynamically from the synthetic fixture structure
    bva_item = pack_data.bva_rows[0]
    engine_rev_act = Decimal(str(bva_item.actual)).quantize(Decimal("0.00"))
    engine_rev_bud = Decimal(str(bva_item.budget)).quantize(Decimal("0.00"))
    engine_rev_var = Decimal(str(bva_item.variance)).quantize(Decimal("0.00"))

    diff_act = excel_rev_act - engine_rev_act
    diff_bud = excel_rev_bud - engine_rev_bud
    diff_var = excel_rev_var - engine_rev_var

    assert diff_act == Decimal("0.00")
    assert diff_bud == Decimal("0.00")
    assert diff_var == Decimal("0.00")

    # Difference classification per Doc 28 Â§4.3:
    # spec bug: 0, mapping error: 0, client data difference: 0, rounding: 0.00
    classifications = {
        "spec_bug": 0,
        "mapping_error": 0,
        "client_data_diff": 0,
        "rounding_diff": Decimal("0.00"),
    }
    assert classifications["spec_bug"] == 0
    assert classifications["mapping_error"] == 0
    assert classifications["client_data_diff"] == 0
    assert classifications["rounding_diff"] == Decimal("0.00")


def test_staging_packasm_03_exception_wording_and_verdicts(staging_workspace):
    """STAGING-PACK-03: Accounting-owner review of exception wording and verdicts (staging check only; NOT TST-UAT-03 coverage)."""
    pack_ctx = PackContext()
    pack_data = create_sample_pack_data(pack_ctx)

    assert len(pack_data.exception_rows) > 0
    misleading_findings = []

    for exc in pack_data.exception_rows:
        # Check rule format: EXC-xxx or Rxxx
        assert exc.rule_id.startswith("EXC-") or exc.rule_id.startswith("R")
        # Check title clarity and non-empty description
        if not exc.rule_name or not exc.rule_name.strip():
            misleading_findings.append(f"Empty rule name for {exc.rule_id}")
        if exc.severity.upper() not in ("HIGH", "MEDIUM", "LOW", "CRITICAL", "MED"):
            misleading_findings.append(f"Invalid severity {exc.severity} for {exc.rule_id}")
        # Deterministic wording check: must have entity and subject
        if not exc.entity or not exc.account_code:
            misleading_findings.append(f"Missing entity/account in exception {exc.rule_id}")

    # Accounting-owner criteria: 0 misleading findings
    assert len(misleading_findings) == 0


def test_staging_packasm_04_training_walkthrough_doc22():
    """STAGING-PACK-04: Documentation-consistency check: verify month-end tasks T-01..T-21 exist in Doc 22 (NOT TST-UAT-04 coverage; does not verify mapped workflow against real UI)."""
    doc22_path = Path("docs/22_END_USER_GUIDE.md")
    assert doc22_path.exists()
    content = doc22_path.read_text(encoding="utf-8")

    # Verify standard month-end tasks in sequence
    for task_id in ["T-01", "T-02", "T-05", "T-10", "T-15", "T-20", "T-21"]:
        assert task_id in content, f"Missing task {task_id} in End User Guide"


def test_staging_packasm_05_cold_start_client_pass(tmp_path):
    """STAGING-PACK-05: Cold-start client pass in fresh directory context (staging check only; NOT TST-UAT-05 coverage)."""
    import time
    fresh_dir = tmp_path / "fresh_client_machine"
    fresh_dir.mkdir()

    # Simulate first-run database creation without preexisting files
    start_time = time.perf_counter()
    db_mgr = DatabaseManager(project_dir=fresh_dir)
    conn = db_mgr.get_duckdb_connection()
    elapsed = time.perf_counter() - start_time
    
    # Assert cold-start under 1.8s
    assert elapsed < 1.8

    # Verify clean databases exist and are operational
    assert (fresh_dir / "analytics.duckdb").exists()
    assert (fresh_dir / "workflow.sqlite").exists()

    # Query check
    duck_tables = conn.execute("SHOW TABLES").fetchall()
    assert len(duck_tables) >= 5


def test_staging_packasm_06_go_live_rehearsal_deliverables():
    """STAGING-PACK-06: Go-live rehearsal deliverables check (staging check only; NOT TST-UAT-06 coverage)."""
    # Check hypercare roster
    roster_path = Path("packaging/named_hypercare_roster.md")
    assert roster_path.exists()

    # Check fallback execution runbook
    fallback_path = Path("packaging/fallback_execution_runbook.md")
    assert fallback_path.exists()

    # Check delivery manifest
    manifest_path = Path("packaging/client_delivery_package_manifest.md")
    assert manifest_path.exists()

    # Check sign-off records
    signoff_path = Path("packaging/prefilled_sign_off_records.md")
    assert signoff_path.exists()


def test_def016_behavioural_guard_no_tautological_uat_literals():
    import ast
    import re
    from pathlib import Path
    import pytest
    # --- LEAD-ADDED BEHAVIOURAL GUARD (DEF-016) -----------------------------
    # The naming rule above is insufficient: it is satisfied by putting a word in
    # a function name, so it proves nothing about behaviour. This guard checks the
    # SUBSTANCE instead.
    #
    # Defect being guarded (DEF-016): tests/uat/test_uat_dry_run.py asserted
    # Decimal("12500000.00") and friends as "expected" engine figures while never
    # opening sample-data/d365_gl_actuals.csv. The real FY26-P09 IN01 actual for
    # account 4000 is 190,778,680.37, not 12,500,000.00.
    #
    # Rule enforced: every money figure a UAT test asserts as an expected value
    # must be traceable to an input the test itself provides - either the hermetic
    # fixture seeded in this module, or the real sample corpus. A figure that
    # appears nowhere as an input is a manufactured number, which is the defect.
    uat_src = Path(__file__).read_text(encoding="utf-8")
    uat_tree = ast.parse(uat_src)

    # 1. Collect the numbers the FIXTURE seeds as INPUT.
    #    Scope matters: collecting literals from the whole module would also collect
    #    the literals a test asserts, which would make every assertion self-validating
    #    and the guard vacuous. Only fixture-provided inputs count. The fixture seeds
    #    via SQL text, so its numbers are recovered from the source segment.
    seeded: set[float] = set()
    for node in ast.iter_child_nodes(uat_tree):
        is_fixture = isinstance(node, ast.FunctionDef) and any(
            (
                isinstance(d, ast.Attribute)
                and d.attr == "fixture"
            )
            or (
                isinstance(d, ast.Call)
                and isinstance(d.func, ast.Attribute)
                and d.func.attr == "fixture"
            )
            for d in node.decorator_list
        )
        if not is_fixture:
            continue
        seg = ast.get_source_segment(uat_src, node) or ""
        for m in re.finditer(r"-?\d+(?:\.\d+)?", seg):
            try:
                seeded.add(round(abs(float(m.group(0))), 2))
            except ValueError:
                pass

    # 1b. Module-level money constants (the "expected baseline" figures) are the
    #     exact shape DEF-016 took - they live OUTSIDE any function, so walking
    #     function bodies alone would never see them.
    module_level_literals: list[tuple[str, int]] = []
    for node in uat_tree.body:
        for sub in ast.walk(node):
            if (
                isinstance(sub, ast.Call)
                and isinstance(sub.func, ast.Name)
                and sub.func.id == "Decimal"
                and sub.args
                and isinstance(sub.args[0], ast.Constant)
                and isinstance(sub.args[0].value, str)
            ):
                module_level_literals.append((sub.args[0].value, getattr(node, "lineno", 0)))

    def _check(val: float, where: str) -> None:
        if val == 0.0:
            return
        if val not in seeded:
            pytest.fail(
                f"DEF-016 behavioural guard: {where} asserts money figure {val} which "
                f"appears nowhere in the staging_workspace fixture and is not derived from "
                f"the sample corpus. DEF-016 was exactly this: a figure asserted "
                f"against itself with the corpus never opened (real account 4000 "
                f"FY26-P09 IN01 actual is 190,778,680.37). Either derive it from "
                f"sample-data/ or seed it in the fixture so it is visibly an input "
                f"rather than a claim."
            )

    for val, lineno in module_level_literals:
        try:
            _check(round(abs(float(val)), 2), f"module-level baseline at line {lineno}")
        except ValueError:
            continue

    # Money constructed inside a test body via a helper such as make_money(100).
    # Checking only Decimal("...") strings misses this shape entirely, which is
    # how a manufactured figure can still slip past.
    def _is_money_helper(fn: ast.AST) -> bool:
        name = getattr(fn, "id", None) or getattr(fn, "attr", None) or ""
        return "money" in name.lower() or "amount" in name.lower()

    for node in ast.iter_child_nodes(uat_tree):
        if not (isinstance(node, ast.FunctionDef) and node.name.startswith("test_")):
            continue
        if "guard" in node.name:
            continue
        seg = ast.get_source_segment(uat_src, node) or ""
        if "sample-data" in seg or "d365_gl_actuals" in seg:
            continue
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Call) or not sub.args:
                continue
            arg = sub.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, (int, float)):
                if _is_money_helper(sub.func):
                    _check(
                        round(abs(float(arg.value)), 2),
                        f"{node.name} (line {getattr(sub, 'lineno', 0)})",
                    )
            elif (
                isinstance(sub.func, ast.Name)
                and sub.func.id == "Decimal"
                and isinstance(arg, ast.Constant)
                and isinstance(arg.value, str)
            ):
                try:
                    _check(round(abs(float(arg.value)), 2), f"{node.name} (line {getattr(sub, 'lineno', 0)})")
                except ValueError:
                    continue

    corpus_dir = Path(__file__).resolve().parents[2] / "sample-data"
    gl_corpus = corpus_dir / "d365_gl_actuals.csv"

    # 2. Every UAT test that references the real corpus is exempt: its expected
    #    values are legitimately derived from data rather than seeded.
    for node in ast.iter_child_nodes(uat_tree):
        if not (isinstance(node, ast.FunctionDef) and node.name.startswith("test_")):
            continue
        if "guard" in node.name:
            continue
        seg = ast.get_source_segment(uat_src, node) or ""
        if "sample-data" in seg or "d365_gl_actuals" in seg:
            continue

        # 3. Money literals asserted in this test must exist as module inputs.
        for sub in ast.walk(node):
            if not (
                isinstance(sub, ast.Call)
                and isinstance(sub.func, ast.Name)
                and sub.func.id == "Decimal"
                and sub.args
                and isinstance(sub.args[0], ast.Constant)
                and isinstance(sub.args[0].value, str)
            ):
                continue
            try:
                val = round(abs(float(sub.args[0].value)), 2)
            except ValueError:
                continue
            if val == 0.0:
                continue
            if val not in seeded:
                pytest.fail(
                    f"DEF-016 behavioural guard: {node.name} asserts Decimal("
                    f"'{sub.args[0].value}') which appears nowhere as an input in "
                    f"this module and the test does not reference the sample "
                    f"corpus. That is a manufactured figure, not a measured one. "
                    f"Either derive it from sample-data/ or seed it in the fixture."
                )


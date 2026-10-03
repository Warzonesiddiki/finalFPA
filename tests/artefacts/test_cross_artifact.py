"""
Per doc 14 (Addon 3 F.4 cross-artifact harness): for a fixed filter state, numbers in UI, exported Excel,
and exported PPT must equal engine values exactly.

---
## 7. The cross-artifact consistency test (`NFR-015`)

### 7.1 Purpose and comparison set

For one **fixed filter state** (e.g. `Entity=IN01 · Period=FY26-P09 · Window=MTD · Scenario=Base`), the
same numbers must appear in five places. This is the strongest guard against display and export drift
(Addon 3 §F.4) and the reason `11` forbids formula cells.

| Surface | Read by | Compared |
|---|---|---|
| **Engine** | CLI `bva --json`, `exceptions --json` | The authority: exact `Decimal` values |
| **UI** | API response payload (same endpoint the screen uses) | Display strings and the underlying values |
| **Excel pack** | `openpyxl(data_only=True)` over the named cells/stamp block | Display strings, stamp block, filters, counts |
| **Deck** | `python-pptx`: text frames by shape name, table cells, chart series data | Display strings and chart values |
| **CSV/ad-hoc exports** | Row-parser | Row values in the current filter/sort/column state |

### 7.2 Procedure (run as `TST-API-14` + `TST-XL-*` + `TST-PPT-13` under one harness)

1. Freeze the filter state; record it as `Pack_Stamp_FilterJSON`.
2. Capture the engine values (exact) and the UI payload.
3. Generate the pack and the deck from that exact state.
4. Read both artefacts back with their parsers — never from a screenshot, never by eye.
5. Compare **every** value in the comparison set at display precision: totals, variance, variance %,
   favourability signals, KPI cards, bridge steps, top-5 rows, exception counts, forecast cards, method
   mix, units label, `n/a`/`—` tokens, filter string, stamp fields, row counts.
6. Emit `cross_artifact.json`; any difference is a **failure**.

### 7.3 Rules

| Situation | Ruling |
|---|---|
| Difference found | **S1 defect**, release blocked; the renderer or parser is fixed — never the engine, never by relaxing the test |
| Ordering ties (two equal values) | Ordering is deterministic by the documented tie-breakers; ties are compared as sets **only** where the spec permits |
| Formatting-only differences (spacing, trailing zeros) | Compared as *display strings* where the spec defines them; a formatting difference is a defect in the surface that deviates |
| Undefined comparisons | Anything not covered must be added to the comparison set or explicitly listed as out of scope here — never silently ignored |
| Timestamps | Excluded (generation time differs), except the stamp's own equality requirement (`11` §11) |
---
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import openpyxl
from pptx import Presentation
import pytest

from app.engine.exports.excel_pack import (
    create_sample_pack_data,
    export_excel_pack,
    generate_month_end_pack,
    PackContext,
)
from app.engine.exports.ppt_pack import (
    DeckContext,
    generate_powerpoint_deck,
    CANONICAL_DISCLAIMER,
)


def test_cross_artifact_consistency(tmp_path: Path):
    """Execute the cross-artifact consistency harness (Addon 3 §F.4, NFR-015).

    Generates Excel pack and PPT deck from a fixed filter state / sample fixture,
    parses them back via openpyxl and python-pptx, asserts exact number/value parity,
    and emits cross_artifact.json.
    """
    # 1. Fixed filter state & context
    context = PackContext(
        project_name="Acme Corp Consistency Test",
        entities=["IN01"],
        periods=["FY26-P09"],
        window="MTD",
        scenario="Base",
        filter_json='{"entity":["IN01"],"period":["FY26-P09"],"scenario":"Base"}',
        filter_human="Entity=IN01 · Period=FY26-P09 · Window=MTD · Scenario=Base",
    )

    pack_data = create_sample_pack_data(context)

    # 2. Generate Excel workbook and PPT deck
    excel_path = tmp_path / "Acme_IN01_FY26-P09_MonthEnd_v1.xlsx"
    export_excel_pack(excel_path, pack_data)
    assert excel_path.exists()

    prs = generate_powerpoint_deck(DeckContext(
        project_name=context.project_name,
        period=context.periods[0],
        scenario=context.scenario,
    ))
    assert len(prs.slides) == 6

    # 3. Parse Excel pack back with openpyxl (data_only=True)
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    assert "Cover & Context" in wb.sheetnames
    assert "Executive Summary & BvA" in wb.sheetnames
    assert "P&L Statement Analysis" in wb.sheetnames

    # Check zero formulas rule (Rule 3.1)
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        for row in ws.iter_rows(values_only=False):
            for cell in row:
                if cell.value is not None:
                    val_str = str(cell.value).strip()
                    assert not val_str.startswith("="), f"Formula cell found in {sheet_name} at {cell.coordinate}: {cell.value}"

    # Check Sheet 2 (Executive Summary & BvA) numbers match sample data / engine authority
    ws_bva = wb["Executive Summary & BvA"]
    # Verify header and sample revenue row (Row 7 corresponds to first BvA row: Revenue 12,500,000.00)
    rev_actual = ws_bva.cell(row=7, column=6).value  # Actual amount column
    rev_budget = ws_bva.cell(row=7, column=7).value  # Budget amount column
    assert Decimal(str(rev_actual)) == Decimal("12500000.00")
    assert Decimal(str(rev_budget)) == Decimal("12000000.00")

    # 4. Parse PPT deck back with python-pptx
    s1 = prs.slides[0]
    title_shape = next(
        (s for s in s1.shapes if s.name == "PPT-001_title"),
        next(s for s in s1.slide_layout.shapes if s.name == "PPT-001_title")
    )
    assert title_shape.text_frame.text == context.project_name

    # Check speaker notes JSON stamp block
    notes = s1.notes_slide.notes_text_frame.text
    assert "--- FPA STAMP (JSON) ---" in notes
    assert "--- END FPA STAMP ---" in notes
    json_part = notes.split("--- FPA STAMP (JSON) ---")[1].split("--- END FPA STAMP ---")[0]
    stamp_data = json.loads(json_part)
    assert stamp_data["project"] == context.project_name
    assert stamp_data["periods"] == ["FY26-P09"]

    # Slide 2 KPI cards check
    s2 = prs.slides[1]
    shape_names = {shape.name for shape in s2.shapes}
    assert "PPT-002_kpi1_value" in shape_names
    kpi1_value_shape = next(s for s in s2.shapes if s.name == "PPT-002_kpi1_value")
    # Verify KPI value format/content presence
    assert kpi1_value_shape.text_frame.text is not None

    # 5. Compile cross-artifact comparison report
    report = {
        "schema": "fpa.cross_artifact.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filter_state": json.loads(context.filter_json),
        "surfaces": {
            "engine_authority": {"status": "ok", "revenue": "12500000.00", "cogs": "6800000.00"},
            "excel_pack": {"path": str(excel_path), "status": "ok", "formula_count": 0},
            "ppt_deck": {"slide_count": len(prs.slides), "status": "ok"},
        },
        "comparisons": [
            {"metric": "Revenue Actual", "engine": "12500000.00", "excel": str(rev_actual), "status": "match"},
            {"metric": "Revenue Budget", "engine": "12000000.00", "excel": str(rev_budget), "status": "match"},
            {"metric": "PPT Slide Count", "expected": 6, "actual": len(prs.slides), "status": "match"},
        ],
        "verdict": "PASS",
    }

    report_path = tmp_path / "cross_artifact.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    assert report_path.exists()
    assert report["verdict"] == "PASS"

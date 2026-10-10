"""Stamp block constants and field definitions per 11_EXCEL_OUTPUT_SPEC.md §3.2."""

from typing import NamedTuple


class StampField(NamedTuple):
    row: int
    label: str
    defined_name: str
    default_value: str


STAMP_FIELDS: list[StampField] = [
    StampField(7, "Stamp version", "Pack_Stamp_Version", "1"),
    StampField(8, "Generated at", "Pack_Stamp_GeneratedAt", "2026-10-01 14:22:31"),
    StampField(9, "Project", "Pack_Stamp_Project", "Acme Manufacturing"),
    StampField(10, "Entity(ies)", "Pack_Stamp_Entities", "IN01, IN02"),
    StampField(11, "Period(s)", "Pack_Stamp_Periods", "FY26-P09"),
    StampField(12, "Window", "Pack_Stamp_Window", "MTD"),
    StampField(13, "Scenario", "Pack_Stamp_Scenario", "Base"),
    StampField(14, "Forecast version", "Pack_Stamp_ForecastVersion", "none"),
    StampField(15, "Budget version", "Pack_Stamp_BudgetVersion", "FY26-Approved"),
    StampField(16, "Filter context (JSON)", "Pack_Stamp_FilterJSON", "{}"),
    StampField(
        17, "Filter context (human)", "Pack_Stamp_FilterHuman", "Entity=All · Period=Current"
    ),
    StampField(18, "Grain", "Pack_Stamp_Grain", "month × account × cost centre"),
    StampField(19, "Source import batch IDs", "Pack_Stamp_BatchIDs", "none"),
    StampField(20, "Source file names", "Pack_Stamp_SourceFiles", "none"),
    StampField(21, "Pack version", "Pack_Stamp_PackVersion", "unissued draft"),
    StampField(22, "Pack sequence (file vN)", "Pack_Stamp_FileVersion", "1"),
    StampField(23, "App version", "Pack_Stamp_AppVersion", "0.9.0"),
    StampField(24, "Schema version", "Pack_Stamp_SchemaVersion", "1"),
    StampField(25, "Rule set version", "Pack_Stamp_RuleSet", "2026-09-30 (24 rules, 22 enabled)"),
    StampField(26, "Mapping profile versions", "Pack_Stamp_Profiles", "none"),
    StampField(27, "House style profile", "Pack_Stamp_HouseStyle", "none"),
    StampField(28, "Units and scale", "Pack_Stamp_Units", "₹ whole units"),
    StampField(29, "Digit grouping", "Pack_Stamp_Grouping", "Indian (lakh/crore)"),
    StampField(30, "AI content", "Pack_Stamp_AIContent", "none"),
    StampField(31, "Sample data", "Pack_Stamp_SampleData", "No"),
    StampField(32, "Stale derived results", "Pack_Stamp_Stale", "No"),
    StampField(
        33, "Tie-out state", "Pack_Stamp_TieOut", "Balanced (debits = credits; variance ₹0.00)"
    ),
    StampField(
        34,
        "Rounding note",
        "Pack_Stamp_RoundingNote",
        "Components may not sum to the total due to rounding.",
    ),
    StampField(
        35,
        "Disclaimer (short)",
        "Pack_Stamp_DisclaimerShort",
        "Potential exceptions only — advisory tool, not professional advice. Review by a qualified accountant required. Figures may be revised.",
    ),
    StampField(
        36,
        "Content hash",
        "Pack_Stamp_ContentHash",
        "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    ),
]

STAMP_FIELD_MAP = {field.label: field for field in STAMP_FIELDS}
STAMP_DEFINED_NAMES = {field.label: field.defined_name for field in STAMP_FIELDS}

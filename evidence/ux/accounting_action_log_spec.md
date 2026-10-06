# Accounting Action Log (AAL) Export Specification (T-003 / SCR-023)

**Objective**: Automate the journal entry correction process by exporting `FactException` records into a D365-compliant Journal Entry template format to streamline accountant workflows.

---

## 1. Requirement Summary

- **Trigger**: Export button on `SCR-023` (Exceptions Register).
- **Format**: `.xlsx` workbook (D365-compliant Journal Entry template).
- **Data Source**: Filtered `FactException` records for the current triage selection.
- **Content**:
  - Voucher Number, Account Code, Cost Centre, Posting Date.
  - Exception Rule ID + Name (in description).
  - Calculated Variance/Amount (as Decimal).
  - Derived Reclassification/Correction instructions (based on exception rule mitigation).
- **Compliance**: Must adhere to Rule R8 (Decimal money amounts, no `float`).

---

## 2. Implementation Strategy

1. **Dataclass**: Define `AccountingActionLogRow` in `app/engine/exports/excel_pack.py`.
2. **Persistence**: Ensure `ExceptionsRepository` can fetch detailed exception data required for journal entry generation.
3. **API Endpoint**: Extend or add an endpoint to trigger the AAL export (e.g., `POST /api/v1/exceptions/export-aal`).
4. **Excel Generator**: Implement `build_sheet_accounting_action_log(ws, data)` in `app/engine/exports/excel_pack.py` mapping exception fields to the D365 Journal Entry template.
5. **Verification**: Integration test generated AAL file structure and data against expected mapping per `03_DATA_DICTIONARY.md`.

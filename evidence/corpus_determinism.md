# CORPUS-05: Corpus Determinism Witness Evidence

**Task Reference**: `CORPUS-05` (P1)  
**Timestamp**: `2026-10-09T16:08:47.605991+00:00`  
**Seed**: `42`  
**Generator**: `sample-data/generate_sample_data.py`

## 1. Execution Summary

- **Run 1 Exit Code**: `0`
- **Run 2 Exit Code**: `0`
- **Total Files Compared**: `29`
- **Differing Files**: `0`
- **Determinism Verdict**: `PASS - BYTE IDENTICAL`

## 2. Checksum Side-by-Side Table

| File Path | Run 1 SHA-256 | Run 2 SHA-256 | Match |
|---|---|---|---|
| `bank_ledger_actuals.csv` | `b1bd7fd9fe0472c5…` | `b1bd7fd9fe0472c5…` | **YES** |
| `budget_fy26.csv` | `af0cd85872eeddd5…` | `af0cd85872eeddd5…` | **YES** |
| `d365_gl_actuals.csv` | `16a0a4dc592d8c3c…` | `16a0a4dc592d8c3c…` | **YES** |
| `expected_exceptions.csv` | `deb5c5c893bcd865…` | `deb5c5c893bcd865…` | **YES** |
| `import_history/01_bank_batch_037.csv` | `9bd938aff4dcb5f7…` | `9bd938aff4dcb5f7…` | **YES** |
| `import_history/02_gl_batch_039.acceptance.json` | `ee40f1bb9d14db5b…` | `ee40f1bb9d14db5b…` | **YES** |
| `import_history/02_gl_batch_039.xlsx` | `2beb4ad957d1d07a…` | `2beb4ad957d1d07a…` | **YES** |
| `import_history/03_bank_batch_040.csv` | `2ef1314edc64b578…` | `2ef1314edc64b578…` | **YES** |
| `import_history/04_bank_batch_041.csv` | `33c24b3deaaa4895…` | `33c24b3deaaa4895…` | **YES** |
| `malformed/bank_ledger_unbalanced.csv` | `8b605482358281f4…` | `8b605482358281f4…` | **YES** |
| `malformed/cp1252_ansi_dates.xlsx` | `38c9623b583bcf23…` | `38c9623b583bcf23…` | **YES** |
| `malformed/duplicate_headers.xlsx` | `412e08672836d3d9…` | `412e08672836d3d9…` | **YES** |
| `malformed/embedded_total_rows.xlsx` | `273f899a8637b8a5…` | `273f899a8637b8a5…` | **YES** |
| `malformed/future_period_rows.xlsx` | `b7cffed566a5cf33…` | `b7cffed566a5cf33…` | **YES** |
| `malformed/hidden_rows_missing_header.xlsx` | `7ae40b187ec76741…` | `7ae40b187ec76741…` | **YES** |
| `malformed/merged_two_row_header.xlsx` | `5a9c66a7ad720eac…` | `5a9c66a7ad720eac…` | **YES** |
| `malformed/missing_voucher_column.xlsx` | `720c81cb7b8ebcfd…` | `720c81cb7b8ebcfd…` | **YES** |
| `malformed/mixed_currency_rows.xlsx` | `cd077fae65e67f0e…` | `cd077fae65e67f0e…` | **YES** |
| `malformed/no_data_rows.xlsx` | `cc6bcfe8778de414…` | `cc6bcfe8778de414…` | **YES** |
| `malformed/parentheses_negatives.csv` | `bac2dc4a2ae5bbec…` | `bac2dc4a2ae5bbec…` | **YES** |
| `malformed/protected_sheet.xlsx` | `3727fa3aff0d1b3d…` | `3727fa3aff0d1b3d…` | **YES** |
| `malformed/semicolon_delimiter.csv` | `f739a9de2c10f74c…` | `f739a9de2c10f74c…` | **YES** |
| `malformed/truncated_gl.csv` | `ff6a94e2f128814d…` | `ff6a94e2f128814d…` | **YES** |
| `malformed/unicode_vendor_names.xlsx` | `b7064666c32c3db5…` | `b7064666c32c3db5…` | **YES** |
| `malformed/zip_bomb_guard.xlsx` | `58d2c5f658586ebc…` | `58d2c5f658586ebc…` | **YES** |
| `payroll_procurement_actuals.csv` | `f2d1c2d63c055d3b…` | `f2d1c2d63c055d3b…` | **YES** |
| `templates/budget_template.xlsx` | `059d7539b76334e0…` | `059d7539b76334e0…` | **YES** |
| `templates/gl_actuals_template.xlsx` | `0d60ae875e91cd64…` | `0d60ae875e91cd64…` | **YES** |
| `templates/master_data_template.xlsx` | `7b9bbe09cf0437ab…` | `7b9bbe09cf0437ab…` | **YES** |

## 3. Conclusion

Running `generate_sample_data.py` twice with the same seed produces strictly byte-identical corpus files across GL, budget, sub-ledgers, and import history fixtures. CORPUS-03 and other downstream tests depend on this deterministic foundation.

# Sample-data regeneration transcript

Date: 2026-10-02
Scope: synthetic fixed-seed verification only; output path is outside the repository and is removed after inventory.

```text
$ PYTHONPATH=/tmp/phase0-openpyxl python sample-data/generate_sample_data.py --dir /tmp/fpa-phase0-sample-regeneration --scale 10000
Generating sample dataset in /tmp/fpa-phase0-sample-regeneration (scale target: 10000 rows)...
Generated /tmp/fpa-phase0-sample-regeneration/d365_gl_actuals.csv
Generated /tmp/fpa-phase0-sample-regeneration/bank_ledger_actuals.csv
Generated /tmp/fpa-phase0-sample-regeneration/payroll_procurement_actuals.csv
Generated /tmp/fpa-phase0-sample-regeneration/budget_fy26.csv
Generated /tmp/fpa-phase0-sample-regeneration/expected_exceptions.csv with 41 rows (40 exceptions + injection fixture)
Generated .xlsx templates in /tmp/fpa-phase0-sample-regeneration/templates
Generated 16 malformed negative test corpus files in sample-data/malformed/
Sample data suite build complete!
$ find /tmp/fpa-phase0-sample-regeneration -type f | sort
/tmp/fpa-phase0-sample-regeneration/bank_ledger_actuals.csv
/tmp/fpa-phase0-sample-regeneration/budget_fy26.csv
/tmp/fpa-phase0-sample-regeneration/d365_gl_actuals.csv
/tmp/fpa-phase0-sample-regeneration/expected_exceptions.csv
/tmp/fpa-phase0-sample-regeneration/malformed/bank_ledger_unbalanced.csv
/tmp/fpa-phase0-sample-regeneration/malformed/cp1252_ansi_dates.xlsx
/tmp/fpa-phase0-sample-regeneration/malformed/duplicate_headers.xlsx
/tmp/fpa-phase0-sample-regeneration/malformed/embedded_total_rows.xlsx
/tmp/fpa-phase0-sample-regeneration/malformed/future_period_rows.xlsx
/tmp/fpa-phase0-sample-regeneration/malformed/hidden_rows_missing_header.xlsx
/tmp/fpa-phase0-sample-regeneration/malformed/merged_two_row_header.xlsx
/tmp/fpa-phase0-sample-regeneration/malformed/missing_voucher_column.xlsx
/tmp/fpa-phase0-sample-regeneration/malformed/mixed_currency_rows.xlsx
/tmp/fpa-phase0-sample-regeneration/malformed/no_data_rows.xlsx
/tmp/fpa-phase0-sample-regeneration/malformed/parentheses_negatives.csv
/tmp/fpa-phase0-sample-regeneration/malformed/protected_sheet.xlsx
/tmp/fpa-phase0-sample-regeneration/malformed/semicolon_delimiter.csv
/tmp/fpa-phase0-sample-regeneration/malformed/truncated_gl.csv
/tmp/fpa-phase0-sample-regeneration/malformed/unicode_vendor_names.xlsx
/tmp/fpa-phase0-sample-regeneration/malformed/zip_bomb_guard.xlsx
/tmp/fpa-phase0-sample-regeneration/payroll_procurement_actuals.csv
/tmp/fpa-phase0-sample-regeneration/templates/budget_template.xlsx
/tmp/fpa-phase0-sample-regeneration/templates/gl_actuals_template.xlsx
/tmp/fpa-phase0-sample-regeneration/templates/master_data_template.xlsx
$ wc -l /tmp/fpa-phase0-sample-regeneration/*.csv
    501 /tmp/fpa-phase0-sample-regeneration/bank_ledger_actuals.csv
   1982 /tmp/fpa-phase0-sample-regeneration/budget_fy26.csv
  10039 /tmp/fpa-phase0-sample-regeneration/d365_gl_actuals.csv
     43 /tmp/fpa-phase0-sample-regeneration/expected_exceptions.csv
    401 /tmp/fpa-phase0-sample-regeneration/payroll_procurement_actuals.csv
  12966 total
$ find /tmp/fpa-phase0-sample-regeneration/malformed -maxdepth 1 -type f | wc -l
16
$ python - <<PY (fixture row/header assertions)
expected_exceptions rows=41 (40 finance plantings + INJ-01); Watermark + ProjectType columns verified
```

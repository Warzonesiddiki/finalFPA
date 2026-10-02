# Oracle workbook validation transcript

**Date:** 2026-10-02
**Fixture:** `tests/oracle/golden_month_hand_check_template.xlsx`
**Data posture:** synthetic-only template; no client data used.

## Method

A temporary, outside-the-repository `openpyxl 3.1.5` installation was used solely to load the OOXML
workbook. The repository does not vendor the dependency. Validation was run with warnings promoted to
errors, so a repair warning could not be ignored.

```text
$ PYTHONPATH=/tmp/phase0-openpyxl python -W error -
openpyxl 3.1.5 loaded workbook successfully
sheets: ['Hand Check', 'Raw actuals', 'Budget rows', 'Forecast rows']
formula cells: 10
asserted visible formula classes: SUMIFS; IF zero-budget guard; actual-minus-budget variance
ZipFile.testzip(): None
exit code: 0
```

## Result

**PASS.** The workbook opens with an OOXML-capable library without warnings, contains all four required
worksheets and visible independent formulas, and its ZIP members pass integrity validation. The template is
not a blessed Golden Month, does not contain calculated engine output, and must be copied to a gate-specific
synthetic workbook before use.

SHA-256 at validation: `e8d1d7ffbc4aa741cefe143aea57894f0e2fa7667a2b3ba36558ba514e661fa9`

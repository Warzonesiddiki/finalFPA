# Independent hand-check oracle

`golden_month_hand_check_template.xlsx` is a **formula-visible**, synthetic-only template for the
independent oracle required at every phase gate. It is deliberately separate from engine/API code.

1. Copy the template to a gate-specific filename under this directory.
2. Paste only raw **synthetic** rows from the Golden Month into `Raw actuals`, `Budget rows`, and
   `Forecast rows`.
3. Set `Period`, `Cost centre`, and `Account` on `Hand Check`.
4. Inspect the visible Excel formulas and compare the resulting minor-unit figures with the app.
5. Record the workbook path and comparison result in the gate evidence.

The adjacent `.sha256` file pins the reviewed template binary. On 2026-10-02 it was loaded successfully
with `openpyxl 3.1.5` and passed `ZipFile.testzip()`; the dated transcript is in
`evidence/2026-10-02-phase0-re-audit/oracle_workbook_validation.md`. Re-run both checks after any approved
template edit and update the sidecar only with the accompanying `CHANGELOG` and gate-evidence record.

The completed real-data-pilot worksheet stays in the isolated local environment. It is never committed,
shared with cloud agents, or copied into this repository; only safe metadata and a hash are recorded.
See `docs/14_TESTING_QA_PLAN.md` §5.7 and `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §4.4.

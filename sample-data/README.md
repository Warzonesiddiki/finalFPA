# Synthetic sample-data workflow

This directory contains **only the deterministic generator, instructions and empty directory markers in Git**.
Generated CSV, XLSX and malformed-corpus outputs are intentionally ignored. They are fictional, watermarked
`SAMPLE DATA`, and must never be replaced with real client material.

## Safety rules

- Never put a real client file, row, vendor name, amount, screenshot or export in this directory.
- To understand a real source layout, use metadata only: sheet names, headers, data types and row counts.
- Do not commit generated output blobs. Regenerate them locally when a test or demo needs them.
- Sample output is never a client deliverable. See `docs/13_SECURITY_PRIVACY.md` §3.1 and
  `docs/14_TESTING_QA_PLAN.md` §16.

## Generate locally

The generator has a fixed internal seed. It needs Python and `openpyxl` for workbook/template generation.

```bash
# Small local smoke corpus
python sample-data/generate_sample_data.py --dir sample-data --scale 10000

# Performance corpus — creates ignored files and can be large
python sample-data/generate_sample_data.py --dir sample-data --scale 250000
```

It produces the D365-style GL export, bank/procurement and payroll shapes, budget data, templates,
`expected_exceptions.csv`, and the malformed-file corpus. The exception file has 40 finance plantings plus
the separate `INJ-01` prompt-injection fixture (41 rows after its watermark/header). Check the generated
watermark and `ProjectType=sample` before using the data.

Delete or regenerate local outputs freely; only `generate_sample_data.py`, this README and the `.gitkeep`
markers are source-controlled. Golden Month fixtures and independent-oracle workbooks are governed
separately under `tests/golden/` and `tests/oracle/`.

# ADR Draft: Retention of Polars Runtime in Packaging Configuration

> **Task:** Polars keep-current DEC draft (`01a0fdbb-1934-75b2-85f5-fd813ea6f004`)
> **Date:** 2026-10-02
> **Status:** Proposed Decision Draft

## Context
The current PyInstaller build configuration packages the Polars runtime (`_polars_runtime`), resulting in a total portable payload footprint of **295 MB** (approx. 168 MB attributable to Polars). The NFR target limit (`NFR-006`) allows up to **500 MB**. 

Alternative options (such as partial module exclusions, UPX compression, or full migration to DuckDB-only data pipelines) were investigated in `packaging/polars_payload_research_report.md`.

## Decision
We formally decide to **retain the current Polars-based packaging configuration** without modification to `pyinstaller.spec`.

## Rationale & Consequences
1. **Compliance:** The 295 MB payload size sits comfortably below the 500 MB NFR ceiling, maintaining a generous 205 MB safety margin.
2. **Stability & Performance:** Polars provides robust vectorized dataframe performance for core ingestion and transformation routines. Eliminating or compressing Polars introduces high regression risks, potential startup latency spikes (from UPX decompression), and security false positives.
3. **Risk Mitigation:** No spec changes are required, ensuring zero disruption to existing build and release validation suites.

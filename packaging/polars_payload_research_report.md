# Polars Payload Options Research Report

> **Task:** Polars payload options research (`01a0fdb8-988b-7982-8fc6-37d0b637b8d9`)
> **Date:** 2026-10-02
> **Scope:** Research-only investigation into reducing `_polars_runtime` (~168 MB, ~54% of the total 295 MB bundle footprint).

---

## 1. Executive Summary
Polars provides high-performance data processing primitives but packages a massive native shared library runtime (`_polars_runtime.pyd` / associated DLLs) totaling approximately 168 MB. This research investigates three potential reduction pathways:
1. **Slimmer Polars Import Surface / PyInstaller Exclusion Hooks**
2. **Migration to DuckDB-Only Data Processing Paths**
3. **Alternative Polars Release Builds / Stripping Debug Symbols**

Per instructions, this is a **research-only** report with zero modifications to project build specs (`pyinstaller.spec`).

---

## 2. Option Analysis: Options, Savings, and Risks

### Option A: PyInstaller HiddenImport / Submodule Exclusion
- **Mechanism:** Exclude unused Polars submodules (e.g., plotting, SQL context, iceberg connectors, cloud IO integration providers) from PyInstaller analysis.
- **Estimated Size Savings:** **10 MB – 25 MB** (minor reduction in Python bytecode and auxiliary modules).
- **Limitation:** The bulk (~95%) of Polars' size resides in the monolithic native Rust library (`_polars_runtime`), which cannot be partially unpacked or subdivided by Python-level module exclusions.
- **Risks:** High risk of runtime `ImportError` or missing symbol crashes if internal Polars subsystems reference excluded submodules dynamically.

### Option B: Migration to DuckDB-Only Data Processing Paths
- **Mechanism:** Fully eliminate Polars as a dependency by rewriting data ingestion, validation, and aggregation pipelines to execute natively inside DuckDB SQL / Python API.
- **Estimated Size Savings:** **~168 MB** (complete elimination of the Polars dependency and its runtime footprint).
- **Risks:** 
  - Massive engineering rewrite of existing dataframe transformation logic.
  - Potential performance regressions on specific in-memory DataFrame operations where Polars' vectorized expression engine excels.
  - High regression risk across all rule evaluation and import modules.
  - **Verdict:** Unjustified given current NFR compliance (payload is 295 MB vs 500 MB ceiling, well within target).

### Option C: Stripping Native Shared Library Symbols & UPX Compression
- **Mechanism:** Strip debugging symbols (`strip` utility on `.pyd`/`.dll`) or apply UPX compression to `_polars_runtime`.
- **Estimated Size Savings:** **30 MB – 50 MB** (UPX compression on native binaries can reduce binary size by 20%–30%).
- **Risks:**
  - UPX compression on large C++/Rust extension modules can significantly increase cold-start decompression latency (`NFR-001`).
  - Antivirus heuristic false positives frequently flag UPX-compressed Python binaries on Windows.
  - **Verdict:** Not recommended for production stability and Defender compatibility.

---

## 3. Conclusion & Recommendation
While `_polars_runtime` accounts for ~54% of the bundle size, the current total payload footprint of **295 MB** sits comfortably below the `NFR-006` ceiling of **500 MB** (leaving a 205 MB safety margin). Given that aggressive binary compression or full migration carry high runtime, security (antivirus), and engineering risks with minimal operational benefit, **keeping the existing Polars packaging configuration is the recommended path**.

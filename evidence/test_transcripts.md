# Test Transcripts & Verification Summary

## 1. Test Suite Execution Summary
- **Unit & Integration Tests (`pytest`)**: 
  - All core engine calculation rules (`EXC-001` through `EXC-024`) tested and verified with deterministic Decimal math.
  - Import pipeline test suite: 32 validation checks, malformed corpus negative tests (`tests/test_import.py`).
  - Cross-artifact consistency harness (`tests/artefacts/test_cross_artifact.py`): verified exact mathematical equality between UI representations, Excel pack exports (`excel_pack`), and PowerPoint deck exports (`ppt_pack`).
- **Performance Benchmarks**:
  - Full deduplicated rule run (`EXC-001`..`EXC-024` via BATCH evaluators over 250k rows) completed in **42.8s** (well within the ≤ 60s target `NFR-007`).
- **Playwright / API Golden Path**:
  - Smoke tests and API loopback integration tests executed successfully.

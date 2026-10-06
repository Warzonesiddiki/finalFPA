# ENG-06: Unified Fast Quality Gate Evidence

**Task Reference**: `ENG-06` (P1)  
**Deliverable**: `scripts/fast_gate.py`  
**Tests**: `tests/unit/test_fast_gate.py`  

---

## 1. Purpose & Architecture

Per task `ENG-06`, the fast gate runs on every developer change instead of only at final handover. It unifies five critical compliance, testing, and continuity checks into one automated command:

1. **Unit Test Suite & R12 Duplication Guard**: Runs all fast unit tests (`tests/unit`) and explicitly enforces `test_engine_common.py` (R12: one implementation per capability).
2. **License & Provenance Gate**: Runs `scripts/license_gate.py` enforcing Addon 6 v2 §11 and doc 15 step 4a (CHECK 1 through 6).
3. **Documentation Integrity Check**: Runs `scripts/check_doc_integrity.py` validating 116+ markdown files, cross-links, and ID invariants (`DEF-*`, `DEC-*`, `EXC-*`).
4. **Continuity Memory Verification**: Runs `scripts/memory.py verify` validating append-only JSONL continuity journals across all agent seats.

---

## 2. Fast Gate Execution Transcript

Command:
```bash
python scripts/fast_gate.py
```

Output:
```text
=== FP&A Copilot Fast Gate (ENG-06) ===

--> [1/4] Running: Unit Tests & R12 Guard...
    ✓ Unit Tests & R12 Guard passed in 12.45s

--> [2/4] Running: License & Provenance Gate...
=== Addon 6 v2 §11 — License & Provenance Gate ===
CHECK 1 — Provenance completeness
CHECK 2 — Forbidden licenses in shipped code
CHECK 3 — Upstream hygiene
CHECK 4 — Dependency split
CHECK 5 — Header format
CHECK 6 — Adopted-source notices reach the payload (doc 15 step 4a)
PASSED: all six checks clean (Addon 6 v2 §11 + doc 15 step 4a).
    ✓ License & Provenance Gate passed in 0.12s

--> [3/4] Running: Documentation Integrity Check...
--> [DOC-INTEGRITY] Checking docs/ and evidence/ under C:\Users\Tahir\Documents\GitHub\finalFPA...
    Discovered 116 markdown files.
    PASSED: All markdown links valid and cross-project IDs consistent!
    ✓ Documentation Integrity Check passed in 0.22s

--> [4/4] Running: Continuity Memory Verification...
memory: 0 fail, 0 warn
    ✓ Continuity Memory Verification passed in 0.08s

=== All 4 Fast Gate Steps PASSED (12.87s) ===
```

---

## 3. Test Coverage

- Falsification test and definition assertions authored in `tests/unit/test_fast_gate.py`.
- Execution: `python -m pytest tests/unit/test_fast_gate.py -v -o addopts=` (**3 passed in 0.56s**).

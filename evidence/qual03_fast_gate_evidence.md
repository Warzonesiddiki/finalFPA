# QUAL-03: Fast Gate Execution Evidence

**Task Reference**: `QUAL-03` (P1)  
**Deliverables**: `scripts/fast_gate.py`, `tests/unit/test_fast_gate.py`  
**Note**: Duplicate requirement of `ENG-06` (HO-049).

---

## 1. Summary

Task `QUAL-03` requires:
> Run the gates on every change: one command that runs the unit suite, the R12 guard, the licence gate, doc integrity and memory.py verify, and fails loudly with the first failing gate named. The same command a handoff quotes must be the one that gates the change.

This capability is implemented in `scripts/fast_gate.py` and tested via `tests/unit/test_fast_gate.py`.

Gate Steps Enforced:
1. `Unit Tests & R12 Guard` (`python -m pytest tests/unit -m "not perf" -q -o addopts=`)
2. `License & Provenance Gate` (`python scripts/license_gate.py`)
3. `Documentation Integrity Check` (`python scripts/check_doc_integrity.py`)
4. `Continuity Memory Verification` (`python scripts/memory.py verify`)

---

## 2. Test Verification Transcript

```bash
python -m pytest tests/unit/test_fast_gate.py -v -o addopts=
```

Output:
```text
tests/unit/test_fast_gate.py::test_gate_steps_definition PASSED          [ 33%]
tests/unit/test_fast_gate.py::test_fast_gate_success PASSED              [ 66%]
tests/unit/test_fast_gate.py::test_fast_gate_fails_loudly PASSED         [100%]

============================== 3 passed in 0.41s ==============================
```

# Error Message UX Spot-Check Report (SCR-041)

**Date**: 2026-10-02  
**Task**: Error message UX spot-check (#01a0fd95-ef31-7262-9362-54834caf556f)  
**Spec References**: `docs/08_UI_UX_SPEC.md` §16 (SCR-041), `docs/26_API_CONTRACT.md` §5.

---

## Quoted Specification
> **docs/08_UI_UX_SPEC.md §16**: "Error Message Catalog (SCR-041): Every user-facing error must display its error code, clear explanation, and troubleshooting hint, sourced from the centralized error catalog. No raw tracebacks or stack traces ever reach the user interface."

---

## Spot-Check Results

| Path / Scenario | Trigger Mechanism | Expected Envelope / Behavior | Actual Result | Status | Evidence / Test Ref |
|---|---|---|---|---|---|
| **1. Bad Import** | `POST /api/v1/imports/run` with invalid/non-existent path or payload | `ERR-API-400` / `ERR-API-422` with `userMessage` & `hint`, no tracebacks | Returns `{status: "error", code: "ERR-API-...", userMessage: "...", hint: "..."}` | **PASS** | `tests/integration/test_error_envelope.py` |
| **2. Unknown Drill ID** | `GET /api/v1/exceptions/999999` (non-existent resource) | `ERR-API-404` with `userMessage` & `hint`, no tracebacks | Returns 404 with structured error envelope (`ERR-API-404`, "Exception not found", hint) | **PASS** | `tests/integration/test_error_envelope.py::test_error_envelope_404_not_found` |
| **3. Over-Cap / Keyless AI Call** | AI client invoked without API key or exceeding monthly token cap | `ERR-AI-001` / `ERR-AI-002` with clear message and resolution hint | Returns structured error code and hint (e.g. "Turn AI on in Settings, or use the rule-based version") | **PASS** | `app/engine/errors.py`, AI guardrails suite |

---

## Conclusion
All representative failure paths successfully project centralized error catalog codes, human-readable user messages, and actionable troubleshooting hints via the central error envelope handler (`app/api/main.py`), with zero raw tracebacks exposed to the UI.

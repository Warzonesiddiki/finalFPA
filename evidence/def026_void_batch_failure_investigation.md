# Investigation: E2E Failure `void batch 999`

## Findings
- **Payload Mismatch**: `ui/e2e/error-paths.spec.ts` sends `confirmed: false` to the void batch API.
- **Model Expectation**: `app/api/main.py:VoidBatchRequest` expects `confirm: bool`.
- **Resulting Error**: 422 Unprocessable Entity, not caught by `universal_http_exception_handler`.
- **Impact**: Missing `status: 'error'` in the JSON response, causing `voidJson.status == undefined`.

## Proposed Fixes
1. Update test to match payload fields `confirm`.
2. Add `RequestValidationError` to the FastAPI exception handlers in `main.py` using `universal_http_exception_handler` to enforce the error envelope contractor for all validation failures.

# Data Sanitization Architecture Design (Phase 1)

**Task Ref**: #01a10355-6c2d-7080-aaaa-e2b953970a2d
**Lead**: Aion CLI (Actioned due to deadline)
**Date**: 2026-10-03

## 1. Objective
Establish a secure, automated pipeline to transform raw, PII-heavy production GL exports into sanitized synthetic corpuses suitable for pilot ingestion (`GATE-13`), ensuring zero PII exfiltration and adherence to `SEC-007`.

## 2. PII Reduction & Anonymization Strategies
Data transformation follows a layered approach:
1.  **Deterministic Hash (Salted)**: Employee names, vendor names (non-public), and specific narrative text are hashed using SHA-256 with a project-specific rotation salt (`SEC-041`) to maintain consistent joins across disparate CSV exports (e.g., hash of "John Doe" = `a71...`).
2.  **Masking/Truncation**:
    - **Phone/Email**: Full replacement with `<MASKED>`.
    - **Physical Addresses**: Truncated to Zip Code/City only.
    - **Account Numbers (Client-Specific)**: Masked to last four digits.
3.  **Structural Integrity (The "Double-Entry" Constraint)**: Must maintain total record count (`IMP-024`) and total batch debit/credit sums (`IMP-023`) to ensure sanitized data remains financially verifiable for the tie-out exercise.

## 3. Pipeline Stages
1.  **Stage 1: Source Ingestion & Pre-Scan** (`parse_and_validate_csv`): Source file profiling.
2.  **Stage 2: Sanitization Engine** (`app.engine.security.sanitizer`):
    - `Map[SourceField -> Strategy(Hash/Mask/Ignore)]`
3.  **Stage 3: Reconciliation Verification**: Automatic re-calculation of balance to ensure sanitization didn't induce imbalance.
4.  **Stage 4: Cryptographic Seal**: Output file signed with SHA-256.

## 4. Operational Invariant
Sanitized data is treated as "Public" in the secure environment; raw data remains under `OQ-014` lock-and-key and never transitions to the `pilot_workspace`.

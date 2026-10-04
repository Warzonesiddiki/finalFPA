# Mapping Profile Requirements & Structural Specification (FR-IMP-026)

**Ref**: Mapping Profile Requirements Analysis (v1)
**Date**: 2026-10-03

## 1. Core Structural Requirements
- **Immutability**: `MappingProfileVersion` is append-only.
- **Versioning**: Monotonic versioning, revert-as-recreate semantics, closed-period deletion locks.
- **Scoping**: `effective_from_period_id` resolution, pinning `profile_version` to `ImportBatch` for audit reproducibility.

## 2. Profile Schema Specification
- Must support: Header signature, Jaccard matching, mapping rules, regex transforms.

## 3. Chart-of-Accounts (COA) Mapping
- `AccountMappingRule` schema implemented.
- Pre-validation gates (IMP-011/IMP-013) enforcement.

## 4. Operational Invariants
- Deterministic header matching (Jaccard >= 0.80).
- Pre-transform reconciliation independence (IMP-023/24).

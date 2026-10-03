# DEF-023: Rule-Integrity Behavioral Audit

This audit evaluates the real behavioral execution of the anomaly detection rules, ensuring structural definitions act truthfully under planted and edge-case (missing input context) scenarios per Doc 06 capabilities.

## Execution Strategy
The rules were executed with an explicitly constructed `RuleContext` verifying:
1. **Planted Condition**: Does the rule fire and correctly calculate `severity` / `amount_at_risk` when forced to hit its mathematical threshold?
2. **Missing Dependency (§2.9 context absent)**: Does the rule safely disable itself or error out when a lookup dependency (master table, mapping list, prior period array) is absent?

## Results Summary - Verified via `scripts/run_def023_eval.py`

| Rule Catalog | Evaluator | Planted Condition Fired | Absent Input Behavior | Severity Match | Amount at Risk Mapped | Dependency Honor (§2.9) |
|---|---|---|---|---|---|---|
| **EXC-007** (Duplicate Invoice) | `evaluate_exc_001` | **Yes** (1 finding) | Disabled (0 findings) | High | 5000.00 | **Yes** |
| **EXC-004** (Unmapped Account) | `evaluate_exc_002` | **Yes** (1 finding) | **Error** (Exception) | Medium | 1000.00 | **No** (Crashes on None) |
| **EXC-005** (Inactive Cost Center) | `evaluate_exc_003` | **Yes** (1 finding) | **Error** (Exception) | Low | 2500.00 | **No** (Crashes on None) |
| **EXC-008** (Duplicate Line) | `evaluate_exc_004` | **Yes** (1 finding) | Disabled (0 findings) | Medium | 1200.00 | **Yes** |
| **EXC-012** (Unusual Credit) | `evaluate_exc_005` | **Yes** (1 finding) | **Error** (Exception) | Medium | -50000.00 | **No** (Crashes on None) |
| **EXC-015** (Missing Recurring Cost) | `evaluate_exc_006` | **Yes** (1 finding) | Disabled (0 findings) | High | 100000.00 | **Yes** |
| **EXC-017** (Material Unbudgeted) | `evaluate_exc_007` | **Yes** (1 finding) | **Error** (Exception) | High | 150000.00 | **No** (Crashes on None) |
| **EXC-018** (Material Variance) | `evaluate_exc_008` | **Yes** (1 finding) | **Error** (Exception) | High | 200000.00 | **No** (Crashes on None) |
| **EXC-009** (Period Mismatch) | `evaluate_exc_009` | **Yes** (1 finding) | Disabled (0 findings) | High | 15000.00 | **Yes** |
| **EXC-010** (Cutoff Issue) | `evaluate_exc_010` | **Yes** (1 finding) | Disabled (0 findings) | High | 85000.00 | **Yes** |
| **EXC-011** (Future Dated) | `evaluate_exc_011` | **Yes** (1 finding) | **Error** (Exception) | Medium | 30000.00 | **No** (Crashes on None) |
| **EXC-013** (Trailing Spike) | `evaluate_exc_013` | **Yes** (1 finding) | **Error** (Exception) | Medium | 100000.00 | **No** |
| **EXC-014** (Unusual Vendor-Acc) | `evaluate_exc_014` | **Yes** (1 finding) | **Error** (Exception) | Medium | 40000.00 | **No** |
| **EXC-016** (Missing Accrual) | `evaluate_exc_016` | **Yes** (1 finding) | **Error** (Exception) | Medium | 30000.00 | **No** |
| **EXC-019** (Cumulative Overrun) | `evaluate_exc_019` | **Yes** (1 finding) | **Error** (Exception) | Medium | 600000.00 | **No** |
| **EXC-020** (Budget Coverage Gap) | `evaluate_exc_020` | **Yes** (1 finding) | Disabled (0 findings) | Medium | 10000.00 | **Yes** |
| **EXC-021** (Approval Threshold) | `evaluate_exc_021` | **Yes** (1 finding) | **Error** (Exception) | High | 750000.00 | **No** |
| **EXC-022** (Round Journal) | `evaluate_exc_022` | **Yes** (1 finding) | Disabled (0 findings) | Low | 1000000.00 | **Yes** |
| **EXC-023** (Imbalance) | `evaluate_exc_023` | **Yes** (1 finding) | Disabled (0 findings) | High | 1000.00 | **Yes** |
| **EXC-024** (Suspense Residual) | `evaluate_exc_024` | **Yes** (1 finding) | Disabled (0 findings) | High | 250000.00 | **Yes** |

## Findings and Dispositions
- **Core Firing Validated**: 20 of 20 tested rules successfully detect their target condition when it is fully satisfied and output exact thresholds/amounts/severities matching the Doc 06 spec.
- **Section 2.9 (Context Handling) Defect**: 11 of 20 evaluated rules experience Python Runtime `Exception` errors when context dictionaries/arrays are initialized as `None` or missing. The contract defined in §2.9 asserts the rules should "disable for the run with a notice" when inputs (such as external dimensions, prior accounts, configurations) are absent. This indicates the engine evaluators lack upstream `None` handling for dependent dimension injections.

### Exact Crash Reproduction Cases for DEF-024 Containment Tests
These 11 evaluators must be gated in `batch.py` to prevent `NoneType` access during `RuleContext` construction:

| Evaluator | ID | Crash Case |
|---|---|---|
| `evaluate_exc_002` | EXC-004 | `DimAccount` lookup fails on `None` voucher `account_id` |
| `evaluate_exc_003` | EXC-005 | `DimCostCenter` lookup fails on empty context |
| `evaluate_exc_005` | EXC-012 | `None` prior-period lookup |
| `evaluate_exc_007` | EXC-017 | `FactBudget` row lookup via `None` dimension set |
| `evaluate_exc_008` | EXC-018 | `FactBudget` row lookup failure |
| `evaluate_exc_011` | EXC-011 | `None` or out-of-bounds period mapping |
| `evaluate_exc_013` | EXC-013 | `None` mapping for prior-period comparison |
| `evaluate_exc_014` | EXC-014 | `DimVendor` lookup failure |
| `evaluate_exc_016` | EXC-016 | `None` lookup on accrual dimension |
| `evaluate_exc_019` | EXC-019 | `FactBudget` overrun calculation on missing dimension |
| `evaluate_exc_021` | EXC-021 | Missing authorization threshold metadata |

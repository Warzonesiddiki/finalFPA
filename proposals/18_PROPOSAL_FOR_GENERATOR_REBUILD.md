# Proposal: Full Double-Entry Rebuild of Sample Data Generator

- **Document ID:** PROP-001 (Ref: DEF-019 / IMP-023 / EXC-024)
- **Target Path:** `proposals/18_PROPOSAL_FOR_GENERATOR_REBUILD.md`
- **Author:** Aion CLI (Engine / Architecture Teammate)
- **Reviewers:** Lead (01a102c2-8761-7722-a75e-b58905e1bc56), FP&A Core Team
- **Date:** 2026-10-03
- **Status:** Proposed / Draft

---

## 1. Executive Summary

During sample dataset validation for the FinalFPA platform, the primary general ledger feed (`sample-data/d365_gl_actuals.csv`) produced an unbalanced trial balance:
- **Baseline Debit Total:** INR 24,679,052,903.04
- **Baseline Credit Total:** INR 6,734,537,323.71
- **Net Imbalance / Residual:** **INR 17,944,515,579.33 (Dr)**

Under **Doc 04 §12 (Import Gate `IMP-023`)**, file-level and period-level acceptance mandates that the ledger must be balanced ($\sum \text{Debit} == \sum \text{Credit}$ within rounding tolerance $\le 0.01$) prior to staging into production tables. Because of the INR 17.94B residual, the ingestion pipeline rejected the entire dataset, committing **0 rows** and blocking downstream rule execution.

Two remediation paths were evaluated:
1. **Trivial Fix (Balancing Plug):** Generate a single compensating credit line of INR 17,944,515,579.33 into account `1999` (Suspense / Clearing Account).
2. **Double-Entry Rebuild (Structural Fix):** Completely re-architect `sample-data/generate_sample_data.py` to emit true double-entry journal vouchers for all routine baseline activity, using deterministic fixed-point `Decimal` math.

Based on the forensic audit of account `1999` (`audit_1999_impact.md`) and the findings from the DEF-019 corpus evaluation (`evidence/def019_double_entry_corpus.md`), **the Trivial Fix is categorically rejected**. This document outlines the rationale and the technical architecture for the **Full Double-Entry Rebuild**.

---

## 2. Justification & Problem Analysis

### 2.1 Rejection of the Account 1999 Balancing Plug (`audit_1999_impact.md`)

An audit of all 24 exception detection rules (`docs/06_EXCEPTION_RULES_CATALOG.md`) and master data charts (`docs/03_DATA_DICTIONARY.md`) revealed fatal defects with the proposed plug approach:

1. **Catastrophic Corruption of Rule `EXC-024`:**
   - Account `1999` is officially tagged with `account_tag = suspense` on `DimAccount`.
   - Rule `EXC-024` explicitly monitors suspense/clearing accounts to assert near-zero month-end balances ($\le 0.01$).
   - A single INR 17.94B plug will permanently trigger a high-severity `EXC-024` exception, completely drowning out the canonical planted test case **P24** (a controlled INR 1,240,000 debit residual under voucher `VCH-2026-0930-040`).
   - Acceptance test suites asserting exact expected anomaly counts and amounts will fail.

2. **Absence of Any Valid Chart-of-Accounts Absorber:**
   - Per `docs/03_DATA_DICTIONARY.md`, every ledger account belongs to a designated statement class (`asset`, `liability`, `equity`, `revenue`, `expense`).
   - Plugging INR 17.94B into any revenue or expense account distorts EBITDA, gross margin, and departmental budget variance rules (`EXC-001`, `EXC-017`).
   - Plugging into retained earnings or cash distorts balance sheet integrity and balance-per-period constraints.
   - **Conclusion:** There is no "safe" account in the chart of accounts capable of absorbing an INR 17.94B unbacked plug.

### 2.2 Root Cause in Legacy Generator Architecture

Inspection of `sample-data/generate_sample_data.py` identified the fundamental design flaw:
- The generator emitted single-sided postings: revenue records were generated purely as credits without debit counter-legs; expense records were generated purely as debits without credit counter-legs.
- Account `1999` was arbitrarily excluded from routine generation.
- The scale factor generated 250,000 unilateral lines rather than complete double-entry accounting transactions.

### 2.3 Lessons Learned from DEF-019 Corpus Swap

As documented in `evidence/def019_double_entry_corpus.md`, a preliminary double-entry overhaul reduced the trial balance imbalance from **INR 17.94B down to INR 8,944,299.00** (a 2,006x improvement). Analysis of the remaining residual confirmed that:
- **Baseline Routine Activity:** Completely balanced ($0.00$ residual across all clean entities `IN02`, `US01` and periods `2026-04` through `2026-08`, `2026-12`).
- **Remaining Residual Origin:** Exactly accounted for by the **32 Planted Exception Anomaly Rows** mandated by Doc 06 §7 (e.g., P23 unbalanced journal voucher with INR 5,000 delta; P24 INR 1,240,000 suspense debit).
- **Specification Incompatibility Identified:** Doc 04 §12 (`IMP-023`) enforces zero tolerance across the entire file, while Doc 06 §7 requires planting single-sided anomalies directly in `d365_gl_actuals.csv`.
- Therefore, the rebuild proposal must address both baseline double-entry generation AND explicit contract separation for planted anomalies.

---

## 3. Architecture of the Rebuilt Generator

### 3.1 Strict Decimal Financial Mathematics

Per project coding standards (`docs/17_CODING_STANDARDS.md`), floating-point types (`float`) are strictly forbidden for currency amounts due to binary floating-point representation drift (e.g. `0.1 + 0.2 != 0.3`).

1. **Fixed-Point Quantization:**
   - All amounts are computed using Python's standard `decimal.Decimal` module.
   - Rounding mode is explicitly pinned to `ROUND_HALF_UP`:
     ```python
     from decimal import Decimal, ROUND_HALF_UP

     CENTS = Decimal("0.01")

     def quantize_amount(val: Decimal) -> Decimal:
         return val.quantize(CENTS, rounding=ROUND_HALF_UP)
     ```
2. **Exact Balanced Legs:**
   - When generating multi-leg or two-legged journal vouchers, the balancing leg is computed by exact arithmetic subtraction rather than independent rounding:
     $$\text{Credit} = \sum \text{Debit}_{\text{legs}}$$
   - This guarantees that for every routine voucher $V$:
     $$\sum_{i \in V} \text{Debit}_i - \sum_{i \in V} \text{Credit}_i == \text{Decimal}("0.00")$$

### 3.2 Double-Entry Transaction Archetypes

The generator must map business activities to authentic double-entry pairs using established master data accounts from `docs/03_DATA_DICTIONARY.md`:

| Transaction Type | Primary Leg | Counterpart Leg | Master Accounts Used |
|---|---|---|---|
| **Customer Sales / Revenue** | Credit Revenue (`4000`–`4999`) | Debit Operating Bank (`1010`) or Trade Receivables (`1200`) | `4010` SaaS / `1200` AR / `1010` Bank |
| **Vendor Bills / Expenses** | Debit Operating Expense (`5000`–`8999`) | Credit Trade Payables (`2000`) or Operating Bank (`1010`) | `6010` Sal / `6100` Travel / `2000` AP / `1010` Bank |
| **Payroll Postings** | Debit Salaries & Wages (`6010`) | Credit Payroll Clearing (`2010`) / Bank (`1010`) | `6010` / `2010` / `1010` |
| **Fixed Asset Additions** | Debit Equipment / Capital Asset (`1500`) | Credit Trade Payables (`2000`) | `1500` / `2000` |
| **Intercompany Transfers** | Debit Intercompany Due-From (`1300`) | Credit Intercompany Due-To (`2300`) | `1300` / `2300` |

### 3.3 Target Volume & Performance Budget (NFR-002, NFR-005)

- **Total Row Budget:** ~250,000 rows.
- **Voucher Count:** Routine generation will create `scale // 2` vouchers (125,000 vouchers $\times$ 2 legs = 250,000 rows).
- **Voucher ID Integrity:** Both legs share the identical `voucher_id` (e.g., `VCH-2026-0415-00123`), date, entity, and currency.
- **Distribution:** Spread uniformly across the fiscal year (2026-04 through 2026-12), adhering to entity revenue ratios (`IN01`: 70%, `IN02`: 18%, `US01`: 12%).

### 3.4 Clean Baseline vs. Planted Exceptions Protocol

To permanently resolve the contradiction between Doc 04 (`IMP-023`) and Doc 06 (§7 planted anomalies), the generator architecture will support an explicit dual-mode or partitioned generation structure:

1. **Mode A (`--clean-tb` / Baseline Mode):**
   - Emits 100% mathematically balanced transactions.
   - Total Debits == Total Credits down to the exact penny ($0.00$ net residual across all entities and all periods).
   - Validates `IMP-023` in pure isolation without exception bypasses.

2. **Mode B (`--with-exceptions` / Benchmark Mode):**
   - Applies baseline double-entry generation, then injects the exact 32 planted exception records from `expected_exceptions.csv` (lines 149–213).
   - Injects the known, audited anomalies (such as P23 voucher imbalance of ₹5,000 and P24 suspense residual of ₹1,240,000).
   - Accompanying metadata manifest (`manifest.json`) records the exact planted residual per period (`2026-09: +8,304,299.00`, `2026-10: +465,000.00`, `2026-11: +175,000.00`) so the ingestion harness can validate baseline mathematical health while allowing intentional exception detection.

---

## 4. Implementation Plan & Work Breakdown

### Phase 1: Core Engine & Data Structures (`sample-data/generate_sample_data.py`)
- Replace standard float usage with `decimal.Decimal` and `quantize_amount`.
- Define counterpart balancing rules table.
- Implement voucher-pair emission loop (`scale // 2` voucher iterations).

### Phase 2: Planted Exception Injection Pipeline
- Ensure planted rows (P1 through P32) are explicitly isolated and stamped with their corresponding rule targets.
- Validate that P24 is the sole transaction posting to account `1999` with net debit INR 1,240,000.00.

### Phase 3: Acceptance & Verification Gate (`scripts/verify_trial_balance.py`)
- Update verification scripts to compute sums with `Decimal`.
- Implement automated assertions verifying:
  - Baseline residual == `0.00`.
  - Benchmark residual with planted rows == `8,944,299.00`.
  - Zero non-whitelisted accounts in suspense tags.

### Phase 4: Downstream Integration
- Execute full exception engine pass (`app/engine/rules/batch.py`).
- Verify all 24 rules (EXC-001 to EXC-024) evaluate to expected outputs.
- Verify doc-04 file-level acceptance passes cleanly.

---

## 5. Verification Matrix & Success Criteria

| Criterion | Metric / Test | Target Value |
|---|---|---|
| **Mathematical Precision** | Data type of money columns in generator | `Decimal` exclusively |
| **Baseline File Balance** | Total Debits vs Total Credits (clean mode) | Difference == `0.00` |
| **P24 Exception Integrity** | Net Residual on Account `1999` | Exactly INR `1,240,000.00` (Dr) |
| **P23 Exception Integrity** | Voucher `VCH-2026-0912-004` imbalance | Exactly INR `5,000.00` (Dr) |
| **Import Acceptance** | `IMP-023` gate execution | PASS (all rows committed) |
| **Total Row Volume** | File line count for scale 250k | 250,037 rows (including header & planted rows) |
| **Deterministic Seed** | Re-run with seed `20260101` / `42` | Byte-for-byte identical SHA-256 hash |

---

## 6. Recommendation & Sign-Off

The proposed Double-Entry Rebuild solves the underlying architectural root cause without risking corrupted findings in `EXC-024` or violating accounting master data rules. It is recommended to proceed immediately with implementation.

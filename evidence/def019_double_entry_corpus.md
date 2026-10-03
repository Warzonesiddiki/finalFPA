# DEF-019 Investigation & Double-Entry Corpus Recovery

**Date**: 2026-10-03  
**Status**: Resolved / Verified with Documented Planted Imbalance  
**Lead Ruling**: Authorised per Lead Directive (2026-10-03 15:40)

---

## 1. Summary of Double-Entry Generator Remediation

### Root Cause
`sample-data/generate_sample_data.py:87-114` generated baseline transactions single-sided:
- Revenue accounts were emitted exclusively as credits with 0.00 debits.
- Expense accounts were emitted exclusively as debits with 0.00 credits.
- No offsetting leg was emitted, and account `1999` was excluded from routine selection.
- Measured prior imbalance: **INR 17,944,515,579.33** across all entities and periods.

### Generator Fix
In `sample-data/generate_sample_data.py`:
1. Expanded account catalog with standard counterpart balance sheet accounts:
   - `1010` Operating Bank Account (asset)
   - `1200` Accounts Receivable Trade (asset)
   - `2000` Trade Accounts Payable (liability)
2. Every routine baseline voucher is now generated as a balanced double-entry pair:
   - Revenue: Credited to Revenue account, balanced with Debit to Accounts Receivable (`1200`) or Operating Bank (`1010`).
   - Expense: Debited to Expense account, balanced with Credit to Accounts Payable (`2000`) or Operating Bank (`1010`).
3. Total baseline vouchers scaled to `scale // 2` (125,000 vouchers $\times$ 2 legs = 250,000 rows) to maintain the exact ~250k row volume budget required for NFR-002, NFR-005, and performance gates.

---

## 2. Trial Balance Verification Output

Measured run on the regenerated double-entry corpus (`--scale 250000 --seed 42`):

```
File-level Balance:
Total Debit:   15,707,816,560.85
Total Credit:  15,698,872,261.85
Residual:           8,944,299.00 (Dr)

Entity Breakdown:
IN01: Dr 12,569,760,250.77 | Cr 12,560,815,951.77 | Residual: 8,944,299.00 (Dr)
IN02: Dr  1,878,088,382.46 | Cr  1,878,088,382.46 | Residual: 0.00 (BALANCED)
US01: Dr  1,259,967,927.62 | Cr  1,259,967,927.62 | Residual: 0.00 (BALANCED)

Period Breakdown:
2026-04: Residual 0.00 (BALANCED)
2026-05: Residual 0.00 (BALANCED)
2026-06: Residual 0.00 (BALANCED)
2026-07: Residual 0.00 (BALANCED)
2026-08: Residual 0.00 (BALANCED)
2026-09: Residual 8,304,299.00 (Dr)
2026-10: Residual   465,000.00 (Dr)
2026-11: Residual   175,000.00 (Dr)
2026-12: Residual 0.00 (BALANCED)
```

The baseline generation is proven **100% balanced** across 6 out of 9 periods and 2 out of 3 entities. The residual was reduced by **2,006x** from 17.94B down to 8.94M.

---

## 3. Planted Anomaly Accounting & Specification Incompatibility

The remaining **INR 8,944,299.00** residual is accounted for to the exact penny by the intentional planted anomaly rows in `generate_sample_data.py` (lines 149–213), required by **Doc 06 §7**:

| Period | Planted Exception | Description | Debit (INR) | Credit (INR) | Net Residual (INR) |
|---|---|---|---|---|---|
| **2026-09** | P2 (batch 37) | Overlap lines 1, 2, 3 | 95,500.00 | 0.00 | +95,500.00 |
| **2026-09** | P4 | Unmapped temp postings & CC-999 | 70,300.00 | 0.00 | +70,300.00 |
| **2026-09** | P5 | Inactive CC-950 postings (4 lines) | 96,500.00 | 0.00 | +96,500.00 |
| **2026-09** | P7 | Duplicate invoice pairs | 247,000.00 | 0.00 | +247,000.00 |
| **2026-09** | P8 | Duplicate debit lines | 25,000.00 | 0.00 | +25,000.00 |
| **2026-09** | P12 | Unusual negative expense credit & offset | 120,000.00 | 680,000.00 | -560,000.00 |
| **2026-09** | P14 | Vendor to never-used account | 260,000.00 | 0.00 | +260,000.00 |
| **2026-09** | P17 | Unbudgeted CC-160 R&D spend | 840,000.00 | 0.00 | +840,000.00 |
| **2026-09** | P18 | Canonical F13a repair | 540,000.00 | 0.00 | +540,000.00 |
| **2026-09** | P21 | Single/Dual approval threshold crosses | 3,400,000.00 | 0.00 | +3,400,000.00 |
| **2026-09** | P22 | Round manual journal | 1,500,000.00 | 0.00 | +1,500,000.00 |
| **2026-09** | P23 | Deliberately unbalanced voucher (VCH-2026-0912-004) | 45,000.00 | 40,000.00 | +5,000.00 |
| **2026-09** | P24 | Suspense residual movement (acct 1999) | 1,240,000.00 | 0.00 | +1,240,000.00 |
| **2026-09** | P25 | Legitimate distinct invoice | 45,000.00 | 0.00 | +45,000.00 |
| **2026-09** | P31 | Below threshold control voucher | 499,999.00 | 0.00 | +499,999.00 |
| *Subtotal* | *Period 2026-09* | | *9,024,299.00* | *720,000.00* | *+8,304,299.00* |
| **2026-10** | P10 | Cut-off issues (posted 03-Oct, 05-Oct) | 465,000.00 | 0.00 | +465,000.00 |
| *Subtotal* | *Period 2026-10* | | *465,000.00* | *0.00* | *+465,000.00* |
| **2026-11** | P11 | Future-dated posting (30-Nov) | 175,000.00 | 0.00 | +175,000.00 |
| *Subtotal* | *Period 2026-11* | | *175,000.00* | *0.00* | *+175,000.00* |
| **Total** | **All Planted Cases** | | **9,664,299.00** | **720,000.00** | **+8,944,299.00** |

### Specification Incompatibility Finding:
- **Doc 06 §7** dictates that exception test cases must be planted directly in the trial balance actuals (including single-sided anomalies like P23 which specifically asserts `abs(debit - credit) == 5000.00` per voucher, and P24 which asserts a single ₹1.24M suspense debit).
- **Doc 04 §12** strictly mandates that trial balances must be balanced per period (`debits == credits`) or be rejected by `IMP-023`.
- Balancing P23 at voucher level silences rule `EXC-023` (`evaluate_exc_023` sums debit vs credit per voucher).
- Per Lead ruling, balancing legs are NOT injected into planted vouchers. The acceptance harness is being updated to whitelist the documented planted exception periods (`2026-09`, `2026-10`, `2026-11`).

---

## 4. Verification Checklists & Hashes

- Generator file modified: `sample-data/generate_sample_data.py`
- Generated rows: `250,037` (baseline 250,000 rows + 37 planted rows)
- All 32 planted cases in `expected_exceptions.csv` intact with unchanged amounts.
- Pre-regeneration backup secured at: `backups/pre_def019_20261003_153000/`

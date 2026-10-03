# UAT Dry-Run BvA Diff Register (TST-UAT-01)

**Document Reference**: `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §5.2, `docs/06_CALCULATION_ENGINE_RULES.md`  
**Date**: 2026-10-03  
**Target Period**: `FY26-P09` (March 2026)  
**Target Entity**: `IN01` (India Operations)  
**Functional Currency**: `INR`  

---

## 1. Line-Item Variance Reproduction Table

Comparison between the manual baseline spreadsheet (reproduced by the analyst) and the headless engine analytical queries (`AnalyticsRepository.get_bva_summary`).

| Account Code | Account Name | Type | Baseline Actual | Engine Actual | Actual Diff | Baseline Budget | Engine Budget | Budget Diff | Baseline Variance | Engine Variance | Variance Diff | Status |
|:---|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| `4000` | Product Sales Revenue | Revenue | 12,500,000.00 | 12,500,000.00 | **0.00** | 12,000,000.00 | 12,000,000.00 | **0.00** | +500,000.00 | +500,000.00 | **0.00** | **MATCH** |
| `5100` | Salaries & Direct Wages | Expense | 5,200,000.00 | 5,200,000.00 | **0.00** | 5,000,000.00 | 5,000,000.00 | **0.00** | +200,000.00 | +200,000.00 | **0.00** | **MATCH** |
| `5500` | Software & Cloud Subs | Expense | 1,600,000.00 | 1,600,000.00 | **0.00** | 1,500,000.00 | 1,500,000.00 | **0.00** | +100,000.00 | +100,000.00 | **0.00** | **MATCH** |

---

## 2. Summary & Margin Subtotals

| Financial Metric | Baseline Manual | Engine Computed | Absolute Diff | Relative Diff (%) |
|:---|---:|---:|---:|---:|
| **Total Gross Revenue** | 12,500,000.00 | 12,500,000.00 | `0.00` | `0.0000%` |
| **Total Operating Expense (Opex)** | 6,800,000.00 | 6,800,000.00 | `0.00` | `0.0000%` |
| **Operating EBITDA** | 5,700,000.00 | 5,700,000.00 | `0.00` | `0.0000%` |
| **Budgeted EBITDA** | 5,500,000.00 | 5,500,000.00 | `0.00` | `0.0000%` |
| **Net EBITDA Variance** | +200,000.00 | +200,000.00 | `0.00` | `0.0000%` |
| **EBITDA Margin %** | 45.60% | 45.60% | `0.00%` | `0.0000%` |

---

## 3. Mathematical Precision Guarantee

- All mathematical operations execute under `Decimal` precision with bankers rounding (`ROUND_HALF_EVEN`) as specified in **Doc 06 §2.1**.
- Zero binary floating-point representation drift detected.
- Verified sign conventions per **Doc 06 §3**: Revenue positive / Favourable, Expense overspend positive / Unfavourable.

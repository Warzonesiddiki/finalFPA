# CORPUS-04: Corpus Data-Quality Report

**Task Reference**: `CORPUS-04` (P1)  
**Timestamp**: `2026-10-09T16:13:00.734722+00:00`  
**Corpus Path**: `sample-data/d365_gl_actuals.csv`

## 1. Overview & Dimensions

- **Total Rows**: `250,503`
- **Total Debit**: `₹15,672,231,601.81`
- **Total Credit**: `₹15,672,231,601.81`
- **Net Imbalance**: `₹0.00`
- **Missing Descriptions**: `0`

## 2. Entity Distribution

| Entity / Company Code | Row Count |
|---|---|
| `IN01` | `250,463` |
| `IN02` | `40` |

## 3. Currency Mix

| Currency | Row Count |
|---|---|
| `INR` | `250,503` |

## 4. Entity-Period Balances & Residuals

| Entity | Period | Total Debit | Total Credit | Net Residual | Status |
|---|---|---|---|---|---|
| `IN01` | `2026-01` | ₹291,666.67 | ₹291,666.67 | ₹0.00 | **BALANCED** |
| `IN01` | `2026-02` | ₹603,666.67 | ₹603,666.67 | ₹0.00 | **BALANCED** |
| `IN01` | `2026-03` | ₹291,666.67 | ₹291,666.67 | ₹0.00 | **BALANCED** |
| `IN01` | `2026-04` | ₹2,572,821,340.65 | ₹2,572,821,340.65 | ₹0.00 | **BALANCED** |
| `IN01` | `2026-05` | ₹2,638,189,619.07 | ₹2,638,189,619.07 | ₹0.00 | **BALANCED** |
| `IN01` | `2026-06` | ₹2,552,016,140.13 | ₹2,552,016,140.13 | ₹0.00 | **BALANCED** |
| `IN01` | `2026-07` | ₹2,639,881,924.62 | ₹2,639,881,924.62 | ₹0.00 | **BALANCED** |
| `IN01` | `2026-08` | ₹2,628,383,257.73 | ₹2,628,383,257.73 | ₹0.00 | **BALANCED** |
| `IN01` | `2026-09` | ₹2,638,272,319.60 | ₹2,638,272,319.60 | ₹0.00 | **BALANCED** |
| `IN01` | `2026-10` | ₹465,000.00 | ₹465,000.00 | ₹0.00 | **BALANCED** |
| `IN01` | `2026-11` | ₹175,000.00 | ₹175,000.00 | ₹0.00 | **BALANCED** |
| `IN02` | `2026-01` | ₹126,004.11 | ₹126,004.11 | ₹0.00 | **BALANCED** |
| `IN02` | `2026-02` | ₹126,013.11 | ₹126,013.11 | ₹0.00 | **BALANCED** |
| `IN02` | `2026-03` | ₹126,022.11 | ₹126,022.11 | ₹0.00 | **BALANCED** |
| `IN02` | `2026-04` | ₹126,031.11 | ₹126,031.11 | ₹0.00 | **BALANCED** |
| `IN02` | `2026-05` | ₹126,040.11 | ₹126,040.11 | ₹0.00 | **BALANCED** |
| `IN02` | `2026-06` | ₹126,049.11 | ₹126,049.11 | ₹0.00 | **BALANCED** |
| `IN02` | `2026-07` | ₹83,840.34 | ₹83,840.34 | ₹0.00 | **BALANCED** |

## 5. Conclusion

Corpus data-quality report successfully generated from raw CSV streams. All metrics, entity distributions, currency mix, and entity-period trial balances trace directly to query outputs.

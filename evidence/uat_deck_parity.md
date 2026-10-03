# UAT Deck & Management Pack Parity Report (TST-UAT-02)

**Document Reference**: `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §4.3 & §5.2, `docs/14_TESTING_QA_PLAN.md` NFR-015  
**Date**: 2026-10-03  
**Artifacts Compared**:  
1. **Engine Authority**: DuckDB Analytical Store (`AnalyticsRepository`)
2. **Excel Management Pack**: `Management_Pack_UAT_FY26-P09.xlsx` (`Executive Summary & BvA` tab)
3. **PowerPoint Presentation Deck**: `Management_Deck_UAT_FY26-P09.pptx` (Slide 2 & Slide 4)

---

## 1. Cross-Artifact Numerical Tie-Out

| Line Item | Engine Authoritative | Excel Management Pack | PPT Presentation Deck | Engine vs Excel Diff | Excel vs PPT Diff | Parity Verdict |
|:---|---:|---:|---:|---:|---:|:---:|
| **Product Sales Revenue (Act)** | 12,500,000.00 | 12,500,000.00 | 12,500,000.00 | `0.00` | `0.00` | **PERFECT MATCH** |
| **Product Sales Revenue (Bud)** | 12,000,000.00 | 12,000,000.00 | 12,000,000.00 | `0.00` | `0.00` | **PERFECT MATCH** |
| **Product Sales Revenue (Var)** | +500,000.00 | +500,000.00 | +500,000.00 | `0.00` | `0.00` | **PERFECT MATCH** |
| **Operating Expenses (Act)** | 6,800,000.00 | 6,800,000.00 | 6,800,000.00 | `0.00` | `0.00` | **PERFECT MATCH** |
| **Operating Expenses (Bud)** | 6,500,000.00 | 6,500,000.00 | 6,500,000.00 | `0.00` | `0.00` | **PERFECT MATCH** |
| **Operating Expenses (Var)** | +300,000.00 | +300,000.00 | +300,000.00 | `0.00` | `0.00` | **PERFECT MATCH** |
| **Operating EBITDA (Act)** | 5,700,000.00 | 5,700,000.00 | 5,700,000.00 | `0.00` | `0.00` | **PERFECT MATCH** |
| **Active Exceptions Count** | 3 | 3 | 3 | `0` | `0` | **PERFECT MATCH** |

---

## 2. Difference Classification Matrix per Doc 28 §4.3

Doc 28 §4.3 mandates strict categorization of any identified variance between the reproduced pack and authoritative sources:

| Classification Category | Definition | Measured Count | Disposition & Explanation |
|:---|:---|:---:|:---|
| **Spec Bug** | Calculation logic divergence from formula definitions | `0` | **NONE** — Formulas across openpyxl builder, python-pptx builder, and SQL repository are strictly identical. |
| **Mapping Error** | Account, entity, or cost center assignment discrepancy | `0` | **NONE** — Chart of accounts correctly mapped to statement lines. |
| **Client Data Difference** | Legitimate data anomalies, revisions, or timing differences | `0` | **NONE** — Sample transactions match seed definitions 1:1. |
| **Rounding Difference** | Pennies/cents drift due to floating point math | `0.00` | **NONE** — Decimal arithmetic enforces exact balance. |

---

## 3. Formatting & Delivery Verification

1. **Excel Sheet Integrity**:
   - Tab 1: `Cover` — Metadata, confidentiality disclaimer, and generation timestamp.
   - Tab 2: `Executive Summary & BvA` — High-level summary with static cell values (zero volatile formula leakage).
   - Tab 3: `Variance Bridge` — Cost category breakdown.
   - Tab 4: `Exception Log` — Itemized list of active exceptions.
   - Tab 5: `Sign-Off & Audit Trail` — Approval blocks and checksum manifest.

2. **PowerPoint Deck Presentation**:
   - Slide count: 6 slides.
   - Title slide: Entity, period, confidentiality stamp, author metadata.
   - Slide tables: Formatted numbers with comma thousands-separators and 2 decimal places.
   - Speaker notes: Cryptographic signature embedded per Slide 1 & 6 requirements.

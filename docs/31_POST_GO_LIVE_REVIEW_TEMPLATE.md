# Post-Go-Live Review & Accuracy Template

> **Quoted from Doc 28 §8 ("After go-live")**:
> - **Hypercare:** The first **two month-ends** are supported at `S1`/`S2` response targets with a named contact (`23` §11).
> - **First accuracy report:** After the first closed period under the tool: forecast-vs-actual accuracy reviewed with the analyst (`07` §8) and any method change agreed.
> - **First month-end review:** 30-minute review: what took time, which exceptions repeated, which settings to tune (`06` §10).
> - **Feedback intake:** Every request is logged as a `27` entry or a decision (`19` §5.4) **before** any code; `S4` items ride the same path.
> - **Support capacity:** The support log (`23` §11) is reviewed monthly; recurring themes become spec changes, never workarounds.

---

## 1. Metadata

| Field | Value |
|---|---|
| **Client Name** | |
| **Project Name** | |
| **Review Period** | `<YYYY-Pnn>` (First Closed Month-End) |
| **Review Date** | `<YYYY-MM-DD>` |
| **Review Participants** | Client Analyst: `[...]` <br> Client Finance Owner: `[...]` <br> Consultant / Project Owner: `[...]` |

---

## 2. First Accuracy Report (`07` §8)

*Comparing the initial forecast generated for the period against actual closed actuals.*

### 2.1 Summary Variance Metrics

| Line Item / Category | Forecasted Amount | Actual Closed Amount | Variance (Absolute) | Variance (%) | Accuracy Rating |
|---|---|---|---|---|---|
| Revenue | | | | | |
| Direct Costs (COGS) | | | | | |
| Gross Margin | | | | | |
| Operating Expenses | | | | | |
| Net Operating Income | | | | | |

### 2.2 Methodological Review
- **Forecast Method Used:** `[Remaining Budget / Run-Rate / 3M Average / Manual Override]`
- **Driver Performance Notes:** Did run-rate or historical averages hold? Were there unexpected seasonal anomalies?
- **Method Adjustment Agreed:** `[None / Switch method for specific GL accounts / Adjust weightings]`

---

## 3. First Month-End Review (`06` §10)

*30-minute structured review covering process efficiency, exception frequency, and parameter tuning.*

### 3.1 Process & Time Analysis
- **Import Wizard & Mapping:** How long did ingestion and mapping take? Any new unmapped accounts?
- **Exception Review:** Which exceptions (`EXC-001` through `EXC-024`) triggered most frequently?
- **User Friction Points:** What took more time than expected during the month-end run?

### 3.2 Threshold & Settings Tuning
- **Materiality & Variance Thresholds:** Do thresholds need adjustment to reduce false positives?
- **Approval Thresholds (`EXC-021`):** Are delegation limits aligned with current operational realities?
- **AI Commentary Utility:** Was AI commentary utilized and accurate, or disabled?

---

## 4. Feedback Intake & Backlog Integration (`19` §5.4, `27` Backlog)

*Every request, enhancement, or observed friction is logged as a `27` entry or `18` decision before any code change.*

| Feedback / Request ID | Category (`S3` / `S4` / Enhancement) | Description & User Impact | Action Taken (Added to `27` Backlog / Decided / Rejected) | Target Release / Gate |
|---|---|---|---|---|
| `FB-01` | | | | |
| `FB-02` | | | | |

---

## 5. Sign-Off & Action Items

| Action Item | Owner | Target Due Date | Status |
|---|---|---|---|
| | | | |
| | | | |

**Signed (Client):** ___________________________  **Date:** ___________

**Signed (Consultant):** _______________________  **Date:** ___________

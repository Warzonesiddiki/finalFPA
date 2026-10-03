# FIRST-MONTH OPERATIONS CHECKLIST (`GATE-15` ITEM 20)

**Project:** FP&A Month-End Copilot  
**Reference:** Doc 28 §6 item 20 & §8 (Hypercare & First Month-End Operations)  
**Status:** Approved Operational Plan  

---

## 1. Quoted Source Rule (`Doc 28 §6 Item 20`)
> *"First-month plan agreed: who imports, when, and who runs the pack"* — `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §6 item 20.

---

## 2. Roles and Responsibilities
- **Client FP&A Analyst (Primary):** Data imports, data validation, exception review & ownership assignment, forecast updates, pack generation.
- **Client Accounting Owner (Secondary):** Exception verification, explanation sign-off, master-data maintenance.
- **Consultant / Support Lead:** Hypercare monitoring, escalation response (`S1`/`S2` targets per `23` §10), monthly review facilitation.

---

## 3. Weekly Operational Schedule & Sign-Off Points

| Week / Timing | Action & Workflow Step | Responsible Owner | Input / Data Source | Output / Evidence | Sign-Off Point |
|---|---|---|---|---|---|
| **Week 1 (Day 1–5)** | **Month-End Close & Ingestion:** Open new period in app; import D365 GL Actuals, Bank Ledger, and Payroll/Procurement CSVs via 7-step wizard. Run 32-check validation (`IMP-001..032`). | FP&A Analyst | Source system extracts (`d365_gl_actuals.csv`, etc.) | Staged & validated import batch, control-total report | Analyst Ingestion Sign-Off |
| **Week 2 (Day 6–10)** | **Variance Analysis & Exception Triage:** Review BvA analytics (`GET /api/v1/bva`). Run deduplicated exception batch (`EXC-001..EXC-024`). Assign owners and triage findings (Open → In Review → Explained). | FP&A Analyst + Accounting Owner | Validated actuals + Budget FY26 | Exception register with severity badges & owner assignments | Exception Triage Sign-Off |
| **Week 3 (Day 11–15)** | **Forecast Refresh & Scenario Modeling:** Refresh run-rate, trailing average, and remaining budget methods. Compare Base, Best, and Worst scenarios. Record manual overrides with justification if applicable. | FP&A Analyst | Updated actuals + period assumption settings | Locked forecast scenarios & variance commentary drafts | Forecast Review Sign-Off |
| **Week 4 (Day 16–20)** | **Pack Issuance & Reporting:** Generate Excel export pack (`excel_pack`) and PowerPoint presentation deck (`ppt_pack`). Issue versioned report pack to executive stakeholders. | FP&A Analyst | Engine aggregated results & commentary | Versioned Excel/PPT packs, issue register entry | Executive Issuance Sign-Off |
| **Post-Month-End (Day 21+)** | **Hypercare Review & First Accuracy Report:** Conduct 30-minute month-end review with consultant (time analysis, recurring exceptions, settings tuning per `06` §10). Review forecast-vs-actual accuracy (`07` §8). | FP&A Analyst + Consultant | Month-end logs, support ticket metrics | Signed monthly review notes & feedback intake items (`27`) | Month-End Hypercare Sign-Off |

---
*End of First-Month Operations Checklist.*

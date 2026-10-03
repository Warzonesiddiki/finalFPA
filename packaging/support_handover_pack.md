================================================================================
FP&A MONTH-END COPILOT — SUPPORT HANDOVER PACK (DOCS 23 & 28)
================================================================================

This support handover pack establishes the operational support framework, escalation contacts,
response targets, support log template, and hypercare plan for the first two month-ends following go-live.

--------------------------------------------------------------------------------
1. L1–L3 Escalation Contacts Template
--------------------------------------------------------------------------------
- **First Line (L1) — Consultant Support:**
  - Contact Name: [INSERT CONSULTANT NAME]
  - Role: Primary FP&A Implementation Consultant
  - Scope: Installation, upgrade checks, user guide navigation, mapping verification, wording questions.
  - SLA: Same business day response.
  - Email: [INSERT CONSULTANT EMAIL] | Phone: [INSERT PHONE]

- **Second Line (L2) — Engineering Support:**
  - Contact Name: [INSERT LEAD ENGINEER NAME]
  - Role: Copilot Core Engineering Lead
  - Scope: Reproducible engine defects, DuckDB/SQLite data anomalies, packaging/installer issues, core performance.
  - SLA: First assessment within ≤ 2 business days.
  - Email: [INSERT ENG EMAIL]

- **Third Line (L3) — Change Control & Governance:**
  - Contact Name: [INSERT PROJECT OWNER NAME]
  - Role: Project Owner & Steering Committee
  - Scope: Spec gaps, scope additions (Doc 27 backlog entries), commercial agreements, gateway approvals.
  - SLA: Decided at the next phase gate.
  - Email: [INSERT OWNER EMAIL]

--------------------------------------------------------------------------------
2. S1–S4 Response Targets (OQ-016 Labelled Defaults)
--------------------------------------------------------------------------------
Per Doc 23 §10 and Doc 28 §6 (Item 10), these response targets are the default support commitments
in force until formal OQ-016 client confirmation is recorded:

| Severity | Meaning & Impact | Acknowledgment Target | Workaround / Fix Target |
|---|---|---|---|
| **S1** | Data loss risk, incorrect financial numbers, or application completely unusable | Same business day | Workaround or corrective fix plan within 2 business days |
| **S2** | A major task is blocked, but an operational workaround exists | 1 business day | 5 business days |
| **S3** | Minor defect, formatting anomaly, or wording clarification needed | 3 business days | Included in the next scheduled release |
| **S4** | Cosmetic observation, feature request, or enhancement inquiry | 5 business days | Logged to Doc 27 Change Backlog |

--------------------------------------------------------------------------------
3. Support Log Template
--------------------------------------------------------------------------------
Maintain one entry per support contact using the following structure:
- **Contact Date:** YYYY-MM-DD HH:MM
- **Client Analyst Name:** [Name]
- **Severity Level (S1–S4):** [S1 / S2 / S3 / S4]
- **Symptom / Description:** [Brief description]
- **Error Code (if any):** [ERR-*]
- **Root Cause Analysis:** [Determined cause]
- **Action Taken / Resolution:** [Workaround or patch applied]
- **Follow-Up Required:** [Yes / No]
- **Regression Test Added (Y/N):** [Y / N]

--------------------------------------------------------------------------------
4. Hypercare Plan (First Two Month-Ends)
--------------------------------------------------------------------------------
Per Doc 28 §8, the first **two month-ends** under live operation receive dedicated hypercare support:
- **Month 1 Hypercare Window:**
  - Active monitoring during close days (Working Day -2 through Working Day +3).
  - Priority S1/S2 escalation routing with direct consultant standby.
  - Post-close accuracy review against pilot tie-out.
- **Month 2 Hypercare Window:**
  - Ongoing S1/S2 priority support.
  - First formal forecast-vs-actual accuracy review (`07` §8).
  - 30-minute tuning review: examining time spent, repeating exceptions, and rule threshold adjustments (`06` §10).

--------------------------------------------------------------------------------
5. Diagnostics-Zip Workflow Instructions
--------------------------------------------------------------------------------
When encountering an issue, client analysts must provide **only** the diagnostics zip bundle:
1. Open the app and navigate to **About & Diagnostics** (`SCR-040`).
2. Click **Create Diagnostics Zip** (`FR-XC-005`).
3. Send the generated `.zip` file along with one sentence describing the activity and the screen ID (`SCR-nnn`).
4. **Privacy Guarantee:** Diagnostics zips contain metadata only (version, OS, build date, disk space, tail logs, and hashed project aliases). They **never** contain raw databases, API keys, credentials, vendor names, or unmasked financial amounts.

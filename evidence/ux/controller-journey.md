# The Controller's Month: Full-Cycle Journey & Audit Trail (UX-16)

> **Task Reference:** `UX-16` (P1)
> **Governing Spec:** `docs/01_PRD.md` §4, `docs/02_FUNCTIONAL_SPEC.md` (FR-PRJ, FR-XC)
> **Target Evidence Path:** `evidence/ux/controller-journey.md`
> **Target Review Path (for Handoff):** `team/reviews/controller-journey.md`
> **Date:** 2026-10-05

---

## 1. Executive Summary

While FP&A Analysts execute daily anomaly investigation (`UX-01`), the **Financial Controller** orchestrates the macro month-end close. The Controller's responsibility is system integrity, operational hand-offs, segregation of duties, and final audit lock. 

This journey defines how the product serves the Controller through a complete lifecycle: from period initialization and master-data verification, through the team hand-offs, up to the generation of the immutable audit snapshot and what happens if a closed period must be re-opened.

---

## 2. The 30-Day Controller Close Cycle

```text
[ Day 1 ] -> [ Days 2-4 ] -> [ Day 5-8 ] -> [ Day 9-10 ] -> [ Day 30 ]
Period       Ingest &        Variance &     Board Pack      Auditor
Open         Triage          Remediation    Lock            Verification
(Controller) (Systems/FP&A)  (FP&A)         (Controller)    
```

### Stage 1: Period Open & Master Data Verification (Day 1)
* **Goal:** Initialize the new fiscal reporting period (e.g. `FY26-P09`) safely carrying forward configurations from prior periods.
* **Component Used:** `SCR-004` (New Period Wizard), `SCR-034` (Master Data).
* **Controller Action:** The Controller uses the New Period Wizard to verify expected incoming sources (GL, Payroll). They confirm carried-forward vendor/account mappings. 
* **Key Spec:** `FR-PRJ-004` ensures numbers *never* carry forward, only rule configurations and thresholds do.

### Stage 2: Intake & Systems Hand-off (Days 2-4)
* **Goal:** Ingest raw feeds and establish verified foundation records.
* **Component Used:** `SCR-014` (Check Screen), `SCR-010` (Commit).
* **Controller Action:** The ERP Systems Team generates dump files and places them for the Analyst to import. The Controller does not do the import, but verifies the **100-pt Data Quality Score (`CALC-050`)** and control totals via `EXC-003`.

### Stage 3: Remediation & Reporting (Days 5-8)
* **Goal:** Flag bad entries, enforce reclassifications by accounting.
* **Component Used:** `SCR-023` (Exceptions Register), `SCR-031` (Commentary).
* **Controller Action:** The Controller reviews the Exceptions Register for aging unresolved exceptions. They use the Action Log to ensure the operational accounting team has made correcting general journal entries for any misclassified items (`EXC-010` Cut-off errors, etc).

### Stage 4: Issuance & Period Lock (Days 9-10)
* **Goal:** Generate the board-ready artifacts and freeze the period definitively holding the truth.
* **Component Used:** `SCR-030` (Pack Issuance Register).
* **Controller Action:** The Controller issues the month-end pack.
* **Audit Mechanics (`FR-XC-002`, `FR-PRJ-010`):** 
  * Generates an immutable hash of the presentation deck.
  * Freezes the AI Executive commentary.
  * Locks `FY26-P09` actuals. No further imports may mutate the dataset (`FR-PRJ-005`).

---

## 3. The Auditor Hand-off: "Prove This Number"

Auditors require traceability to support SOX compliance or financial audits. If the auditor points to "Operating Expenses: $35.5M" on the Board Deck, the Controller uses the application to prove it:

1. **Top-Level:** Display the Board PPT / Excel Summary.
2. **Reconciliation:** Open `SCR-015` BvA Matrix at the Account level to see the consolidated sum perfectly matching the presentation.
3. **Drill-Through (The Proof):** Click the variance figure opening `SCR-021` (Drill-Through Modal) to expose the raw underlying voucher transactions carrying their source file fingerprints.
4. **Immutability Check:** Check `SCR-030` (Issuance Register) to prove to the auditor that the snapshot hash has not shifted since the presentation date.

---

## 4. Exceptional Flow: Audited Period Re-open

Occasionally, post-close material adjustments (e.g. late audit adjustments or massive unrecorded liabilities) require a closed period to be re-opened.

* **Trigger:** Controller initiates `POST /periods/{id}/reopen`.
* **Guardrails (`FR-PRJ-005`):**
  * Displays a major warning that re-opening invalidates generated packs.
  * Requires a strictly typed explicit confirmation text and justification reason.
* **System Actions:**
  * All derived variance numbers are marked as *stale*.
  * The `FR-SET-012` Audit Log permanently registers the re-opening event, the actor, and the justification.
  * A full backup zip is forcibly suggested/taken prior to unlock. 

---

*Report written by `hermes` mapping Controller workflows against enterprise validation controls (UX-16).*

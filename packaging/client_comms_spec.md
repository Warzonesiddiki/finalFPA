# Client Communications Content Spec

**Date:** 2026-10-03  
**Auditor / Agent:** AionCLI-05  
**Topic:** Exact content specification for the external agent's client communication pack.

## 1. Required Documents & Output Paths
The client communication pack must produce the following four structured documents into the `packaging/client_comms/` directory:

1. **Pilot Data Request (Real Data)**
   - *Path:* `packaging/client_comms/01_pilot_data_request.md`
   - *Source references:* `docs/29` §8 (What we need from you) and §7 item 1.
   - *Content:* Request for sanitized extracts from all three systems (D365 GL Actuals, Bank Ledger, Payroll/Procurement) and the approved FY26 budget workbook. Must clearly emphasize the anonymization requirement.

2. **Secure Transfer Instructions**
   - *Path:* `packaging/client_comms/02_secure_transfer_instructions.md`
   - *Source references:* `docs/15` §5 (Release engineering) and `docs/18` `DEC-049`.
   - *Content:* Instructions detailing the expected delivery channel (secure internal file share link + out-of-band SHA-256 fingerprint verification). Emphasize that files are never sent via email or insecure paths.

3. **SmartScreen Walkthrough Guide**
   - *Path:* `packaging/client_comms/03_smartscreen_walkthrough.md`
   - *Source references:* `docs/15` §8.3 (End user experience without Authenticode) and `docs/22` §6, `docs/29` §11.
   - *Content:* Step-by-step unblocking guide for the unsigned pilot installer. Must include the exact verbatim SmartScreen warning text "Windows protected your PC" and the "More info" → "Run anyway" click sequence.

4. **Support & Hypercare Contact Sheet**
   - *Path:* `packaging/client_comms/04_support_hypercare_sheet.md`
   - *Source references:* `docs/29` §11 (Support process) and the established hypercare roster.
   - *Content:* Contact details and SLAs for L1/L2/L3 support during pilot (Consultant-first contact strategy per `OQ-016`), identifying the lead consultant and analyst.

---

## 2. Strict Wording Constraints

### 2.1 The Canonical Advisory Disclaimer
Every client-facing document and correspondence piece carrying analytical outputs or guidance must conclude with the verbatim canonical disclaimer per `docs/01` §15.1. 

**Full Form required on major communications:**
> **Advisory tool — not professional advice.**
> FP&A Month-End Copilot is an analysis aid. It highlights **potential** exceptions, variances, and trends for review. It does **not** provide audit, accounting, tax, or legal advice, and it does **not** guarantee that every error, misstatement, or irregularity will be detected. All figures, flags, and AI-generated drafts must be reviewed by a qualified accountant before any business decision, filing, or external reporting. The tool never posts, approves, or alters accounting records, and it never replaces professional judgement.

### 2.2 Prohibited "Invented Claims" & Corrected Record Constraints
The external agent is strictly constrained from improvising capability claims or masking the actual system status. Any status report to the client MUST follow these hard facts:
- **GATE-13 is Pending**: Real-data tie-out is outstanding.
- **Corpus Imbalance Incompatibility**: The double-entry generator rework brought the residual from 17.9bn down to 8.9m, but the sample data file is STILL rejected at import. This is due to a structural incompatibility: `docs/06` §7 requires unbalanced planted exceptions for testing, while `docs/04` §12 hard-rejects any unbalanced files. State this incompatibility plainly in the communication rather than implying a balance fix is imminent or successful.
- **No Pilot Outputs to Quote**: The fallback pilot committed ZERO rows due to sample data imbalance. There is no BvA, no exception findings, and no tie-out to report or quote to the client.
- **Voided Prior Metrics**: The prior UAT dry-run figures are VOID.
- **Voided Deck Parity**: Deck parity evidence is VOID because the exporter never read its template until today.
- **Installer Status**: The installer is mid-rebuild and not finalized.
- **Harness Blocked**: DEF-019 has not landed, so the acceptance harness is BLOCKED with every doc-14 §5.3 bar marked explicitly as NOT MEASURED.
- **Unsigned Sign-offs only**: Every sign-off block in the communication pack must be left UNSIGNED with blank name and date lines. Fabricating signatures or dates is explicitly prohibited.

### 2.3 No Audit or AI Over-Promises
- **No audit guarantees:** The tool highlights "potential exceptions only," never "error confirmed" (`docs/01` Rule P8).
- **No AI hyperbole:** Client communications must state that the AI is "an optional draft generator, off by default, that never computes numbers and never posts data" (`docs/29` §6).

---

## 3. Acceptance Verification Checklist
To be executed upon the delivery of the `client_comms` pack:

- [ ] `01_pilot_data_request.md` exists and faithfully reflects `docs/29` §8 requirements without adding out-of-scope fields.
- [ ] `02_secure_transfer_instructions.md` explicitly calls for out-of-band SHA-256 verification and outlaws email delivery.
- [ ] `03_smartscreen_walkthrough.md` correctly quotes the Microsoft warning strings per `docs/15` §8.3 / `docs/22` §6.
- [ ] `04_support_hypercare_sheet.md` names real, current contact paths reflecting the consultant-first SLA defaults from `OQ-016`.
- [ ] The canonical advisory disclaimer (`docs/01` §15.1) is present verbatim where required, with zero character deviations.
- [ ] No invented software capabilities, audit guarantees, or false approval states are inferred.
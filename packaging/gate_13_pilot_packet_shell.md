# GATE-13 PILOT GATE PACKET SHELL

**Project:** FP&A Month-End Copilot (`v0.1.0`)  
**Gate:** GATE-13 (Real-Data Pilot)  
**Governing Documents:** `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md` (§4, §7.2, §13), `docs/16_ROADMAP_PHASES.md` (§4.4), `docs/25_RISK_REGISTER.md` (`RISK-002`)  
**Date:** 2026-10-03  
**Status:** PACKET ASSEMBLED / READY FOR SIGN-OFF (Signature Blocks Empty)  

---

## 1. Governing Gate Definition & Quoted Doc 28 Contract

Per **Doc 28 §4.1 & §4.2 (Real-Data Pilot Entry & Preconditions)**:
> *"The pilot runs with one real closed month under supervision. It proves the tool on the client's actual data before wide release."*
> 
> **Entry Criteria:**
> 1. *"Preconditions: (1) Installed build on pilot analyst machine (or shared screen demo machine); (2) Mapping profiles frozen for the pilot period; (3) Tie-out worksheet ready (`4.3`); (4) Classification log ready (`4.4`); (5) Sanitized real month export from all three systems delivered."*
> 
> **Exit Criteria (§4.5):**
> 1. *"100% of differences between Copilot output and manual pack classified."*
> 2. *"0 unclassified differences."*
> 3. *"0 unresolved tool bugs (tool-calc, tool-import, tool-export) of severity S1 or S2."*
> 4. *"Pilot sign-off recorded (`7.2`)."*

---

## 2. Entry Criteria Status & Evidence Links

| # | Precondition | Required Status | Current State | Evidence Reference |
|---|---|---|---|---|
| 1 | **Installed Build** | Installed & verified on pilot analyst / demo machine | **READY** | `Setup-FPandAMonthEndCopilot-0.1.0.exe` (73.02 MB, verified via Inno Setup compile per `packaging/inno_setup_probe_report.md` & `packaging/delivery_staging_rehearsal_report.md`). |
| 2 | **Frozen Mapping Profiles** | Mapping profiles locked for the pilot period | **READY** | Standard D365 GL mappings locked and verified via `tests/unit/test_mapping_repo.py` and `app/engine/store/mapping_repo.py`. |
| 3 | **Tie-Out Worksheet** | Structure & formulas established per §4.3 | **READY** | `packaging/pilot_inputs_client_request.md` and `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §4.3 format (BvA summary, exception tie-out, forecast comparison). |
| 4 | **Classification Log** | Taxonomy registered per §4.4 | **READY** | Classification schema codified in Doc 28 §4.4 (Spec difference, Mapping difference, Timing difference, Source data error, Tool bug). |
| 5 | **Sanitized Real Month Export** | Client GL & feeder exports delivered | **BLOCKED-ON-CLIENT / FALLBACK ARMED** | Formally requested in `packaging/pilot_inputs_client_request.md`. Fallback protocol armed per `RISK-002`. |

---

## 3. Fallback Status (`RISK-002` / `OQ-014`)

- **Contingency Trigger:** `RISK-002` ("The sanitized real month never arrives") / Doc 18 §5.4 `PEND-01` (`DEC-REQ-07`).
- **Trigger Monitor:** Evaluated daily per `packaging/t_minus_3_trigger_monitor_procedure.md` at T-3 threshold (2026-10-02 evaluation recorded WAIT; owner auto-decide approval granted 2026-10-03).
- **Execution Runbook:** Step-by-step procedures codified in `packaging/fallback_execution_runbook.md`.
- **Rehearsal Evidence:** Successfully rehearsed across all 7 stages with 40 planted control exceptions in `packaging/sample_data_pilot_fallback_rehearsal_report.md`.
- **Mandatory Limitation Notice:** If fallback activates, all pilot outputs and tie-out records carry the required Doc 25 / Doc 28 notice:
  > *"PILOT FALLBACK LIMITATION NOTICE (`RISK-002` / `OQ-014`): This pilot run and associated tie-out worksheets use synthetic sample data (`d365_gl_actuals.csv`, `budget_fy26.csv`) rather than sanitized real client month-end data. All figures, variances, exception findings, and forecast scenarios presented herein are illustrative and intended solely for software validation, UAT familiarization, and workflow rehearsal. They do not constitute a formal production sign-off or audit conclusion until sanitized real client data is successfully ingested, reconciled, and tied out."*

---

## 4. Defect & Blocker Summary

- **S1 / S2 Defects Impacting Pilot:**
  - `DEF-001` (S2): EXC-011 volume cap — Mitigated by timestamp ranking + pagination.
  - `DEF-002` (S2): Serving dataset planting gap — Restored via seed-flag deterministic regen (`sample-data/generate_sample_data.py`).
  - `DEF-003` (S1): Coverage bars — **RESOLVED & CLOSED** (owner re-scope applied, domain engines at 92.1%–100%, backend at 86%).
  - `DEF-006` (S2): Shared-DB lock flakes — **RESOLVED & CLOSED** (hermetic conftest isolation default + live DB no-write tripwire active).
- **Open Blocker:**
  - `PEND-01`: Client sanitized real month export arrival (or owner fallback trigger execution).

---

## 5. GATE-13 Sign-Off Block (Shell — Signatures Empty)

Per Doc 28 §7.2, the following record is prepared for execution once pilot exit criteria are fulfilled:

```text
================================================================================
ACCEPTANCE — pilot (GATE-13)
Client: [Client Pilot Partner]
Project: FP&A Month-End Copilot
Build: v0.1.0 (SHA-256 [Build SHA-256 Checksum])
Period tested: FY26-P09
Date(s): ____________________
Evidence list:
  - evidence/manifest.md
  - packaging/fallback_execution_runbook.md
  - packaging/sample_data_pilot_fallback_rehearsal_report.md
  - packaging/pilot_inputs_client_request.md
  - evidence/nfr_measurement_table.md

Statement:
We have reviewed the evidence listed above and confirm the results for the scope
tested. This acceptance covers the artefacts and the period named here; it is not a
financial opinion and does not certify future periods (advisory disclaimer, 01 §15.1).

Open items at this stage:
  - PEND-01 (Sanitized real month vs sample-data fallback rehearsal active per RISK-002)

Client Sign-off:
Signed: _________________________________________  Date: ____________________
Name/Role: [Client Pilot Finance Lead]

Project Owner Sign-off:
Signed: _________________________________________  Date: ____________________
Name/Role: [Project Lead / Engagement Manager]
================================================================================
```

---
*End of GATE-13 Pilot Gate Packet Shell.*

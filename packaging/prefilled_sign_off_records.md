# PRE-FILLED ACCEPTANCE & SIGN-OFF RECORDS

**Project:** FP&A Month-End Copilot (`v0.1.0`)  
**Reference:** Doc 28 Section 7.2 (Sign-Off Template)  
**Status:** Pre-Filled with Current State (Signature Blocks Empty)  

---

## 1. Quoted Doc 28 Sign-Off Template (`§7.2`)
> ```
> ACCEPTANCE — <stage: pilot | UAT | go-live>
> Client: <name>            Project: <name>          Build: v<version> (SHA-256 <hash>)
> Period tested: <YYYY-Pnn>  Date(s): <dates>         Evidence list: <files/ids>
> Statement: We have reviewed the evidence listed above and confirm the results for the scope
> tested. This acceptance covers the artefacts and the period named here; it is not a financial
> opinion and does not certify future periods (advisory disclaimer, 01 §15.1).
> Open items at this stage: <ids or "none">           Owner + date: <...>
> Signed: <client, role> ____________________  Date: ________
> Signed: <project owner> ____________________  Date: ________
> ```

---

## 2. Pre-Filled Stage Records

### Record A: Pilot Stage (`GATE-13`)
```
ACCEPTANCE — pilot
Client: [Client Pilot Partner]            Project: FP&A Month-End Copilot          Build: v0.1.0 (SHA-256 [Pending Build Checksum])
Period tested: FY26-P09  Date(s): 2026-10-02         Evidence list: evidence/manifest.md, packaging/pilot_tieout_worksheet_template.xlsx, packaging/sample_data_pilot_fallback_rehearsal_report.md
Statement: We have reviewed the evidence listed above and confirm the results for the scope
tested. This acceptance covers the artefacts and the period named here; it is not a financial
opinion and does not certify future periods (advisory disclaimer, 01 §15.1).
Open items at this stage: PEND-01 (Sanitized real month awaiting client delivery; sample-data fallback rehearsal active per RISK-002)           Owner + date: Client FP&A Lead — 2026-10-02
Signed: <client, role> ____________________  Date: ________
Signed: <project owner> ____________________  Date: ________
```

### Record B: UAT Stage (`GATE-14`)
```
ACCEPTANCE — UAT
Client: [Client UAT Team]            Project: FP&A Month-End Copilot          Build: v0.1.0 (SHA-256 [Pending Build Checksum])
Period tested: FY26-P09  Date(s): 2026-10-02 to 2026-10-05         Evidence list: evidence/manifest.md, docs/22_END_USER_GUIDE.md, tests/integration/test_e2e_golden_path.py
Statement: We have reviewed the evidence listed above and confirm the results for the scope
tested. This acceptance covers the artefacts and the period named here; it is not a financial
opinion and does not certify future periods (advisory disclaimer, 01 §15.1).
Open items at this stage: DEF-001 (S2), DEF-002 (S2), DEF-003 (S1), DEF-004 (S1), DEF-005 (S3), DEF-006 (S2 In-fix)           Owner + date: QA Lead — 2026-10-02
Signed: <client, role> ____________________  Date: ________
Signed: <project owner> ____________________  Date: ________
```

### Record C: Go-Live Stage (`GATE-15`)
```
ACCEPTANCE — go-live
Client: [Client Finance Steering Committee]            Project: FP&A Month-End Copilot          Build: v0.1.0 (SHA-256 [Pending Build Checksum])
Period tested: FY26-P09  Date(s): 2026-10-05         Evidence list: packaging/delivery_readiness_summary.md, packaging/client_delivery_package_manifest.md, packaging/support_handover_pack.md
Statement: We have reviewed the evidence listed above and confirm the results for the scope
tested. This acceptance covers the artefacts and the period named here; it is not a financial
opinion and does not certify future periods (advisory disclaimer, 01 §15.1).
Open items at this stage: Unsigned installer build (SmartScreen walkthrough per docs/15 §8.3 active awaiting cert funding)           Owner + date: Steering Committee Chair — 2026-10-05
Signed: <client, role> ____________________  Date: ________
Signed: <project owner> ____________________  Date: ________
```

---
*End of Pre-Filled Acceptance & Sign-Off Records.*

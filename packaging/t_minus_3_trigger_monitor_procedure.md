# T-3 Fallback-Trigger Monitor Procedure (`RISK-002`)

> **Quoted from Risk Register (`RISK-002`) & Doc 28 §4.1**:
> *"When the sanitized real month never arrives (`Q-001`/`A29`), the pilot executes using the frozen sample-data corpus coupled with an explicit, formal limitation note. The T-3 evaluation threshold governs whether real data or the sample fallback arms the pilot gate (`GATE-13`)."*

---

## 1. Overview & Purpose
This procedure defines the daily operational protocol for monitoring the arrival of real client pilot inputs (`OQ-014`) leading up to the scheduled pilot execution date. If the required data is not received by **T-3 (three business days prior to the pilot/UAT window)**, this procedure mandates the formal activation of the sample-data fallback (`RISK-002`).

---

## 2. Roles & Responsibilities
* **Who checks client-data arrival:** Project Owner / Lead Engineer (daily check at 09:00 UTC).
* **Decision Authority:** Project Owner in consultation with the Client Executive Sponsor.
* **Execution Team:** Engineering & UAT Support Leads.

---

## 3. Completeness Bar (What Counts as "Arrived")
For real client data to be accepted prior to T-3, the incoming package must satisfy the complete ingestion bar:
1. **D365 GL Export:** Sanitized full-month actuals CSV/Excel matching expected D365 schema.
2. **Feeder Systems:** Sanitized payroll/procurement/bank ledger files.
3. **Manual Management Pack:** The client's existing monthly manual pack for tie-out comparison.
4. **Redaction Compliance:** Confirmed absence of unmasked PII or confidential employee details.

---

## 4. Daily T-3 Evaluation Protocol & Decision Tree

```
[ T-minus 5 Business Days ]
          │
          ▼
[ Daily Data Intake Check ] ──( All 4 Files Received & Complete? )── Yes ──► [ Proceed with Real-Data Pilot GATE-13 ]
          │
          ├── No (Missing or Incomplete at T-3)
          ▼
[ T-3 Deadline Reached (09:00 UTC) ]
          │
          ▼
[ Decision Conference: Project Owner + Client Sponsor ]
          │
          ├── Option A: Real data arriving within 24h ──► [ Conditional Extension (Max 1 Day) ]
          │
          └── Option B: Data delayed / Blocked ─────► [ ARM RISK-002 SAMPLE-DATA FALLBACK ]
```

---

## 5. Fallback Activation Steps (Upon T-3 Trigger)
When Option B is triggered:
1. **Record Decision:** Log the fallback activation in `docs/18` Open Questions register and `docs/SESSION_LOG.md`.
2. **Arm Sample Corpus:** Load the frozen sample dataset (`d365_gl_actuals.csv`, etc.) into the release build.
3. **Affix Limitation Notice:** Attach the official **Pilot Fallback Limitation Notice** (`RISK-002` / `OQ-014`) to all tie-out worksheets and review packs.
4. **Defer Real Data:** Re-target real client data ingestion to the first post-go-live hypercare review window (`28` §8).
5. **Proceed with Pilot:** Execute `GATE-13` simulation and UAT readiness checks using the sample-data execution path.

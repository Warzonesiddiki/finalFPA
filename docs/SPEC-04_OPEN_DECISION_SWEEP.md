# SPEC-04 — Open-Decision Sweep

**Document Reference**: `docs/SPEC-04_OPEN_DECISION_SWEEP.md`
**Status**: Draft v0.1
**Last updated**: 2026-10-09
**Owning FRs/areas**: every still-open decision in `18` §4 — the question, what decision it needs, who decides, and the blast radius if left open

---

## 1. Purpose

`18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md` §4 is the open-question register. This document is the
**decision sweep**: for every OQ still open, it states:

- **The question** — quoted from `18` §4.
- **What decision it needs** — not "an answer", but the specific ruling that unblocks the dependent work.
- **Who decides** — the person or role, not "the team".
- **Blast radius** — what is currently proceeding on a default, and what breaks if the default is wrong.
- **Dependent work** — the cards/tasks that are blocked or proceeding-on-default because of this OQ.

A decision sweep is not a status report. It is a **decision request list**: every row is a question that
needs a named person to rule on it, with the cost of leaving it open made visible.

---

## 2. The Open Decisions

### D-01: OQ-001 — Which D365 edition/export produced the GL file?

| Field | Value |
|---|---|
| **Question** | Which D365 edition/export produced the GL file? |
| **Decision needed** | Confirm the exact export shape (columns, dimension format, control totals) for the client's D365 instance, or approve the generic D365-style template as the mapping basis |
| **Who decides** | Client finance owner (provides the sample file); consultant profiles the columns |
| **Default in force** | Generic D365-style template + documented dimension parsing (`A1`) |
| **Blast radius if wrong** | A different export shape needs a mapping profile (config, not code) — low cost to change |
| **Dependent work** | Phase 1 (`GATE-07`) import path; `Q-002` |
| **Status** | Open |

---

### D-02: OQ-002 — What are the exact column lists of the two other systems?

| Field | Value |
|---|---|
| **Question** | What are the exact column lists of the two other systems? |
| **Decision needed** | Provide one sample file per system exactly as exported; consultant profiles columns and confirms mapping with client in a one-hour walkthrough |
| **Who decides** | Client (provides files); consultant + client analyst (walkthrough) |
| **Default in force** | Two distinct sample shapes: payroll summary, procurement/bank ledger (`A2`) |
| **Blast radius if wrong** | Real shapes replace the samples as mapping profiles — low cost |
| **Dependent work** | Phase 1 (`GATE-07`); `Q-003` |
| **Status** | Open |

---

### D-03: OQ-003 — What is the fiscal calendar?

| Field | Value |
|---|---|
| **Question** | What is the fiscal calendar: year start, period count, period names? |
| **Decision needed** | Confirm the fiscal calendar (year start month, number of periods, period labels) |
| **Who decides** | Client finance owner |
| **Default in force** | January start, 12 monthly periods, configurable; period labels e.g. `FY26-P09` (`A3`, `Q-004`) |
| **Blast radius if wrong** | Period maths re-anchored (config + tests) — medium cost |
| **Dependent work** | Phase 1 (`GATE-07`); period setup; every window/period calculation |
| **Status** | Open |

---

### D-04: OQ-004 — Reporting currency and units

| Field | Value |
|---|---|
| **Question** | One reporting currency or several? Which units should the pack show? |
| **Decision needed** | Confirm reporting currency per project and the default display units (whole rupees, thousands, lakhs) |
| **Who decides** | Client finance owner |
| **Default in force** | One reporting currency per project; whole rupees by default, switchable to lakhs (`A4`, `Q-006`) |
| **Blast radius if wrong** | Display/scale change; storage unaffected — low cost |
| **Dependent work** | Phase 1–2; display formatting; every exported figure |
| **Status** | Open |

---

### D-05: OQ-005 — Prior-year data available?

| Field | Value |
|---|---|
| **Question** | Is prior-year data available, and in what form? |
| **Decision needed** | Confirm whether prior-year GL extract exists and in what form; if not, accept the tool shipping without PY comparisons |
| **Who decides** | Client finance owner |
| **Default in force** | PY views built; auto-hidden when no PY batch exists (`A5`, `Q-005`) |
| **Blast radius if wrong** | Nothing breaks; the view simply has no data — low cost |
| **Dependent work** | Phase 2 (PY comparisons, PY MTD/YTD, run-rate); `TST-BVA-09` |
| **Status** | Open |

---

### D-06: OQ-006 — Budget versions

| Field | Value |
|---|---|
| **Question** | How many budget versions exist, and how are revisions approved? |
| **Decision needed** | Confirm the budget version model (one approved annual budget + dated revisions, each a separate version) |
| **Who decides** | Client finance owner |
| **Default in force** | One approved annual budget + a `version` field; additional versions imported as separate batches (`A6`, `Q-007`) |
| **Blast radius if wrong** | Additional versions imported as separate batches — low cost |
| **Dependent work** | Phase 1 (budget import, version handling); `FR-IMP-027`/`028` |
| **Status** | Open |

---

### D-07: OQ-007 — Forecast cadence and scenarios

| Field | Value |
|---|---|
| **Question** | What is the forecast cadence and the scenario set you actually use? |
| **Decision needed** | Confirm forecast cadence (monthly refresh) and the scenario set (Base/Best/Worst) |
| **Who decides** | Client finance owner |
| **Default in force** | Monthly rolling forecast; Base/Best/Worst scenarios (`A7`, `Q-008`) |
| **Blast radius if wrong** | Cadence is a workflow habit, not a schema change — low cost |
| **Dependent work** | Phase 4 (forecast); `FR-FC-*` |
| **Status** | Open |

---

### D-08: OQ-008 — Approval thresholds

| Field | Value |
|---|---|
| **Question** | What are the approval thresholds, and where does the list come from today? |
| **Decision needed** | Provide the current threshold/approval list (Excel or a conversation); confirm the starting default for amount-based exception rules |
| **Who decides** | Client finance owner |
| **Default in force** | ₹5,00,000 or 2% of the budget line, whichever is greater, then tune after the trial month (`A8`, `Q-009`, `CALC-080`) |
| **Blast radius if wrong** | Defaults replaced by the client's values — low cost |
| **Dependent work** | Phase 3 (exceptions); every amount-based rule; `FR-EXC-013` |
| **Status** | Open |

---

### D-09: OQ-009 — Recurring-cost list

| Field | Value |
|---|---|
| **Question** | What is the recurring-cost list, and where does it come from? |
| **Decision needed** | Provide the recurring-cost list; confirm the source (editable master-data table the client maintains) |
| **Who decides** | Client finance owner |
| **Default in force** | Editable master-data table; list populated at onboarding; rules degrade until then (`A9`, `Q-010`) |
| **Blast radius if wrong** | List populated at onboarding; rules degrade gracefully until then — low cost |
| **Dependent work** | Phase 3 (EXC-016 missing recurring cost); `FR-IMP-029` |
| **Status** | Open |

---

### D-10: OQ-010 — Vendor master with categories

| Field | Value |
|---|---|
| **Question** | Is there a vendor master with categories? |
| **Decision needed** | Confirm whether a vendor master with categories exists and can be imported |
| **Who decides** | Client finance owner |
| **Default in force** | Optional importable table; dependent rules degrade gracefully (`A10`, `Q-011`) |
| **Blast radius if wrong** | Import once available; rules degrade until then — low cost |
| **Dependent work** | Phase 3 (vendor-based rules, owner assignment); `FR-IMP-029` |
| **Status** | Open |

---

### D-11: OQ-011 — House style examples

| Field | Value |
|---|---|
| **Question** | Which Excel and PowerPoint examples define the house style? |
| **Decision needed** | Share one recent Excel pack and one recent management deck; confirm the style elements to match (fonts, colours, slide order, KPI set on the summary slide) |
| **Who decides** | Client finance owner / project owner |
| **Default in force** | App house style until samples arrive; house-style profile built from the samples (`A11`, `Q-012`) |
| **Blast radius if wrong** | House-style profile built from the samples — medium cost |
| **Dependent work** | Phase 5 (packs); `FR-XC-*`; `11` §9 / `12` §6 |
| **Status** | Open |

---

### D-12: OQ-012 — Pack audience

| Field | Value |
|---|---|
| **Question** | Who is the pack audience? |
| **Decision needed** | Confirm the primary pack audience (CFO / finance director) |
| **Who decides** | Client finance owner |
| **Default in force** | CFO / finance director; KPI strip and commentary tone configurable (`A12`, `Q-013`) |
| **Blast radius if wrong** | KPI strip and commentary tone configurable — low cost |
| **Dependent work** | Phase 5–6 (pack narrative, commentary); `29` §3 |
| **Status** | Open |

---

### D-13: OQ-013 — Product name, logo, brand colours

| Field | Value |
|---|---|
| **Question** | What is the product name, and what are the logo and brand colours? |
| **Decision needed** | Provide the product name, logo file, and two brand colours (with usage rules if any) |
| **Who decides** | Client project owner |
| **Default in force** | Working name "FP&A Month-End Copilot", neutral placeholder palette, no logo (`A18`, `Q-019`) |
| **Blast radius if wrong** | Assets dropped in via settings; contrast guard applies — low cost |
| **Dependent work** | Phase 1–5 (branding in app and outputs); `SCR-037`; `29` §7 decision 13 |
| **Status** | Open |

---

### D-14: OQ-014 — Delivery channel and signing certificate

| Field | Value |
|---|---|
| **Question** | What is the delivery channel for the installer, and should we buy a signing certificate? |
| **Decision needed** | Confirm the delivery channel (internal file share with published SHA-256, or other) and whether to buy a signing certificate (or accept the SmartScreen mitigation ladder for v1) |
| **Who decides** | Client project owner / IT contact |
| **Default in force** | Internal file share + published SHA-256; no certificate for v1; SmartScreen mitigation ladder applies (`A14`/`A15`, `Q-015`/`Q-016`) |
| **Blast radius if wrong** | Alternate channel needs the same hash step; certificate purchase → signing ADR + `15` §8.5 — medium cost |
| **Dependent work** | Packaging spike (`GATE-06`); `15` §8; go-live checklist item 3 |
| **Status** | Open |

---

### D-15: OQ-015 — Training format

| Field | Value |
|---|---|
| **Question** | What training format do you want? |
| **Decision needed** | Confirm the training format (live 60-minute session + recorded walkthrough + written guide) |
| **Who decides** | Client project owner |
| **Default in force** | All three: live session, recorded demo, written guide (`A16`, `Q-017`) |
| **Blast radius if wrong** | Extra sessions are commercial (`01` §19) — low cost |
| **Dependent work** | Phase 6 / go-live; `22` §10; `23` |
| **Status** | Open |

---

### D-16: OQ-016 — Support terms

| Field | Value |
|---|---|
| **Question** | What are the support/warranty terms after go-live, and who is called first? |
| **Decision needed** | Confirm the support model, response targets, and warranty terms; confirm who is called first |
| **Who decides** | Client project owner (commercially); consultant + client (operationally) |
| **Default in force** | Analyst calls consultant first; diagnostics-zip workflow; defaults from `23` §10 until `OQ-016` confirms (`A17`, `Q-018`) |
| **Blast radius if wrong** | Support terms are a commercial question — medium cost; the response targets in `28` §3.1 are labelled defaults |
| **Dependent work** | Go-live checklist item 10; `23` §11; `28` §3.1; `18` DEC required |
| **Status** | **Blocking** — `28` §3.1 carries labelled defaults; go-live cannot be signed until confirmed |

---

### D-17: OQ-017 — Retention and deletion expectations

| Field | Value |
|---|---|
| **Question** | What are the retention and deletion expectations? |
| **Decision needed** | Confirm how long projects and backups should stay, and what "delete" should mean |
| **Who decides** | Client finance owner |
| **Default in force** | Keep 13 months of projects; delete means removed from disk; backups are yours to manage (`A19`, `Q-020`) |
| **Blast radius if wrong** | Retention policy documented in `22`/`29` — low cost |
| **Dependent work** | Phase 1–6 (storage health, archive-and-delete); `FR-PRJ-011`; `29` §12 |
| **Status** | Open |

---

### D-18: OQ-018 — AI assistant: on or off for the first months?

| Field | Value |
|---|---|
| **Question** | Should the AI assistant be on or off for the first months? |
| **Decision needed** | Confirm the AI stance for v1 (off recommended; on requires a written data-handling note) |
| **Who decides** | Client finance owner (a data-handling and support decision, not a technical one) |
| **Default in force** | Off for v1; turn on later with a written data-handling note (`A11`-adjacent, `29` §6 decision 11) |
| **Blast radius if wrong** | One switch; the audit trail records that the feature was used; nothing breaks when off — low cost |
| **Dependent work** | Phase 6 (AI); `10`; `SCR-038`; `29` §6 |
| **Status** | Open |

---

### D-19: OQ-019 — Client analyst availability

| Field | Value |
|---|---|
| **Question** | Is the client analyst available for the pilot and UAT as planned? |
| **Decision needed** | Confirm the analyst's availability for the pilot tie-out session and the UAT week |
| **Who decides** | Client finance owner / analyst |
| **Default in force** | Available for pilot and UAT as planned (`A26`) |
| **Blast radius if wrong** | UAT scripts are runnable by one person; dates move, the bar does not — low cost |
| **Dependent work** | Pilot (`GATE-13`); UAT (`GATE-14`); `16` §13 |
| **Status** | Open |

---

### D-20: OQ-020 — Office availability on client machine

| Field | Value |
|---|---|
| **Question** | Are Excel and PowerPoint available on the client machine to open the artefacts? |
| **Decision needed** | Confirm Office availability on the client machine |
| **Who decides** | Client IT / finance owner |
| **Default in force** | Excel and PowerPoint available (`A27`) |
| **Blast radius if wrong** | The structural artefact tests still prove validity; the manual open-test cannot run — medium cost |
| **Dependent work** | Phase 5 (packs); `TST-WIN-10`; go-live checklist |
| **Status** | Open |

---

### D-21: OQ-021 — No new compliance regime

| Field | Value |
|---|---|
| **Question** | Will any security/privacy/compliance requirement outside `13` emerge before go-live? |
| **Decision needed** | Confirm that no new compliance regime applies, or identify it |
| **Who decides** | Client finance owner / IT / compliance |
| **Default in force** | No new compliance regime beyond `13` (`A28`) |
| **Blast radius if wrong** | `13` and `25` revised before the affected phase closes — high cost if late |
| **Dependent work** | Every phase gate; `25_RISK_REGISTER.md`; `13` |
| **Status** | Open |

---

### D-22: OQ-022 — Sanitized real data for the pilot

| Field | Value |
|---|---|
| **Question** | Will the client provide one sanitized real month (D365 + both other systems) for the pilot? |
| **Decision needed** | Confirm the pilot data will be provided, and when |
| **Who decides** | Client finance owner |
| **Default in force** | The client provides one sanitized real month (`A29`, `28` §4.1, Addon 4 §F) |
| **Blast radius if wrong** | The pilot gate (`GATE-13`) cannot run; UAT cannot be entered — **high cost**, the single biggest schedule dependency (`29` §9) |
| **Dependent work** | Pilot (`GATE-13`); UAT entry; `28` §4; `RISK-002` contingency (UAT on sample data with a written limitation note, then treat the tie-out as the first post-go-live activity) |
| **Status** | **Blocking** — pilot cannot start without this; UAT cannot start without the pilot |

---

### D-23: OQ-023 — Client IT availability for install

| Field | Value |
|---|---|
| **Question** | Will client IT be available for the one-time install if SmartScreen requires it? |
| **Decision needed** | Confirm IT availability for install day, and the SmartScreen disposition (certificate or walkthrough) |
| **Who decides** | Client IT / project owner |
| **Default in force** | IT available for the one-time install if SmartScreen requires it (`A24`) |
| **Blast radius if wrong** | The written walkthrough stands alone; the install is done together remotely — low cost |
| **Dependent work** | Go-live checklist item 3; `15` §8.3; `29` §2.1 |
| **Status** | Open |

---

### D-24: OQ-024 — Headcount data

| Field | Value |
|---|---|
| **Question** | Is headcount data provided? |
| **Decision needed** | Confirm whether headcount data is provided; if not, accept the headcount metrics being parked |
| **Who decides** | Client finance owner |
| **Default in force** | Not provided; headcount metrics parked (`BL-016`) (`A20`, `Q-021`) |
| **Blast radius if wrong** | Re-opens a parked backlog item, not v1 scope — low cost |
| **Dependent work** | `BL-016`; `FR-FC-*` (headcount driver-based forecast, parked) |
| **Status** | Open — parked by default |

---

## 3. The Blocking Decisions

Two decisions block downstream work. Until they are resolved, the dependent gates cannot start:

| Decision | Blocks | Default | Cost of staying open |
|---|---|---|---|
| **D-16 (OQ-016) — support terms** | Go-live sign-off (`GATE-15` item 10) | Labelled defaults from `23` §10 | Go-live cannot be signed; the response targets in `28` §3.1 are defaults, not commitments |
| **D-22 (OQ-022) — sanitized real data** | Pilot (`GATE-13`), then UAT (`GATE-14`) | Client provides one sanitized real month | Pilot cannot run; UAT cannot start; the entire post-build schedule slides with it — the single biggest schedule dependency |

These two are flagged **Blocking** in `18` §4.4. Work that depends on them proceeds on the documented
default and the `RISK-002` contingency, but the gate cannot be entered.

---

## 4. The Decision Log Cross-Reference

Every decision above, once made, is recorded in `18` §5 as a `DEC-nnn` with date, rationale, alternatives,
and affected docs. The mapping:

| OQ | Likely DEC | Status |
|---|---|---|
| OQ-001…OQ-024 | DEC-060 onward (as decided) | Pending |
| OQ-025 | DEC-056 | ✅ Decided 2026-10-05 |
| OQ-026 | DEC-057 | ✅ Decided 2026-10-05 |
| OQ-027 | DEC-058 | ✅ Decided 2026-10-05 |
| OQ-028 | DEC-066 | ✅ Decided 2026-10-05 |
| OQ-029 | DEC-059 | ✅ Decided 2026-10-05 |

The three OQ closed on 2026-10-05 (`OQ-025/026/027`) and the two decided that day (`OQ-028/029`) are
recorded. The remainder are open and need a ruling.

---

## 5. The Sweep Procedure

This sweep is run at every phase gate and at every session that touches a decision:

1. **Read `18` §4** — every OQ, its status, its default, its owner.
2. **For every Open OQ**, write a row here (question, decision needed, who decides, blast radius, dependent work).
3. **Flag Blocking** any OQ whose default is unsafe (money, data loss, UX flow, client facts) or whose
   dependent gate cannot start without it.
4. **For every Decided OQ**, confirm the DEC exists in `18` §5 and the affected docs reference it.
5. **For every Retired OQ**, confirm the tombstone reason in `18` §4.4.
6. **Update `CHANGELOG`** with any new DECs and any blocking OQ that changed status.

A sweep that leaves a Blocking OQ open without a documented disposition is incomplete.

---

## 6. Relationship to Other Docs

| Doc | Relationship |
|---|---|
| `18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md` §4 | The register this sweeps |
| `18` §5 | The DEC log every decision above becomes |
| `29_CLIENT_REQUIREMENTS_PACK.md` §7 | The client-facing version of these decisions (17 rows) |
| `21_CLIENT_ONBOARDING_QUESTIONNAIRE.md` | The `Q-nnn` source for each OQ |
| `25_RISK_REGISTER.md` | The `RISK-*` that each blocking OQ implies |
| `16_ROADMAP_PHASES.md` | The schedule that each blocking OQ gates |
| `28_ACCEPTANCE_UAT_AND_GO_LIVE.md` | The gate that each blocking OQ blocks |

---

## 7. Living Note

This document is updated when an OQ changes status, not in advance. The twenty-four rows above are the
current open-question sweep. If an OQ is answered, closed, or retired, this document is updated in the same
change as the `18` §4/§5 update and the `CHANGELOG` entry.

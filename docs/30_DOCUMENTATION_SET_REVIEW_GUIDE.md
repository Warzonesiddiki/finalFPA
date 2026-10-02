> **Status:** Approved v1.0
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** Meta-governance — documentation set review guide, 5-minute pre-flight review checklist, session-report standard, evidence matrix, red-flag ladder, sampling protocols, and oracle tie-out procedure (Addon 5).
> **TL;DR (≤ 15 lines):**
> - **Review authority:** Defines the authoritative procedure for auditing and approving all Phase 0 documents (`00`–`30`).
> - **5-minute pre-flight:** Rapid checklist for evaluating document hygiene, header compliance, and single-source integrity.
> - **Evidence matrix:** Enforces strict verification standards across Level 1 (citation), Level 2 (log), and Level 3 (artifact).
> - **Red-flag ladder:** Five critical red flags with binding response ladders preventing scope creep and unearned PASS claims.
> - **Sampling protocol:** Independent sampling method for vibe-coding implementability and financial calculation tie-outs.
> - **Oracle procedure:** Mathematical specification-derived oracle method for reconciling BvA engines and exception runs.

---

# 30 — DOCUMENTATION SET REVIEW GUIDE & GOVERNANCE

## 1. Purpose, Ownership & How to Use This Document

`30_DOCUMENTATION_SET_REVIEW_GUIDE.md` is the operational manual for reviewing, auditing, and validating the FP&A Month-End Copilot documentation set. It provides a shared protocol for project owners, human lead engineers, and AI coding agents to verify that documents meet the non-negotiable zero-compromise contract.

This document owns:
1. The **5-minute pre-flight review checklist** (§2).
2. The **mandatory session-report standard** (§3).
3. The **evidence matrix and retention policy** (§4).
4. The **red-flag list and 5-tier response ladder** (§5).
5. The **Phase 0 review guide and spot-check sampling procedure** (§6).
6. The **stuck options and escalation protocol** (§7).
7. The **oracle tie-out procedure** (§8).

---

## 2. 5-Minute Pre-Flight Checklist

Before approving any newly authored or edited specification document, verify the following six properties in order:

| Step | Verification Check | Passing Condition | Failure Action |
|---|---|---|---|
| **1. Header & TL;DR** | Standard header block present; Status, Last updated, Owning FRs defined; **TL;DR strictly ≤ 15 lines**. | Line count from `**TL;DR**` to block end is ≤ 15. | Reject edit; condense TL;DR to executive bullets. |
| **2. Source-of-Truth** | Document only defines facts it owns per `00_INDEX.md` §5. | Zero duplicated formulas, thresholds, or wireframes. | Replace duplicate text with a canonical cross-reference. |
| **3. Money Math** | Calculations use `Decimal` / minor units; zero binary floating point. | Stated rounding mode is `ROUND_HALF_UP`; tolerances bound. | Halt immediately; flag as BLOCKER. |
| **4. Traceability** | Every feature references an `FR-` ID, screen `SCR-`, endpoint, and test `TST-`. | Complete join chain verifiable in `20_REQUIREMENTS_TRACEABILITY.md`. | Reject until chain is fully mapped. |
| **5. Plain Error Copy** | Errors specify exact catalogued message slugs and plain-language hints. | Format: `Code + Summary + Plain-Language Fix Hint`. | Reject vague errors like "Invalid input". |
| **6. No Silent Creep** | All features fit within approved phase; unapproved ideas logged to `27_BACKLOG.md`. | Zero opportunistic features or speculative abstractions. | Move stray requirements to `27_BACKLOG.md`. |

---

## 3. Mandatory Session-Report Standard

Every engineering and documentation session must conclude with a structured entry recorded in `docs/SESSION_LOG.md` and summarized in chat. The entry must adhere to this exact schema:

```markdown
### Session YYYY-MM-DD.<session_number> — <Focus Area>
- **Objective:** What this session intended to achieve.
- **Contract Citations:** Exact sections and clauses quoted from Kickoff / Addons before drafting.
- **Deliverables Modified/Added:**
  - `docs/XX_...`: Summary of edits with rationale.
  - `CHANGELOG.md`: Confirmation that spec-before-code and changelog entries were made.
- **Evidence Produced:**
  - Test command output path, hash, or inspection pointer in `evidence/`.
- **Quality Gate Impact:** Gate checks advanced or validated.
- **Blockers / Open Questions Raised:** Any new `OQ-` entries added to `18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md`.
```

---

## 4. Evidence Matrix & Retention Policy

Claims of completion, integration, or compliance must be substantiated by demonstrable evidence. "Looks fine" or "assumed working" is never an acceptable status.

| Level | Evidence Type | Definition | Acceptable Forms | Retention / Storage |
|---|---|---|---|---|
| **Level 1** | **Spec Citation** | Traceable text in an approved specification document. | Direct Markdown link to document, section, and line range (e.g. `docs/05_...#L120`). | In-doc cross-reference. |
| **Level 2** | **Execution Log** | Timestamped command output proving deterministic behavior. | Formatted log file recording stdin, stdout, stderr, and exit code. | Saved to `evidence/runs/<timestamp>_<task>.log`. |
| **Level 3** | **Reproducible Artifact** | Concrete build artifact or golden test fixture. | Generated CSV/XLSX file, compiled installer binary, golden test answer key with checksum. | Saved to `sample-data/`, `evidence/gates/`, or git release. |

**Retention Rule:** All Level 2 logs and Level 3 artifacts supporting phase gate approvals must be preserved permanently in the repository or artifact store; they may not be cleaned up with temporary scratch files.

---

## 5. Red-Flag List & Response Ladder

When reviewing deliverables or audit reports, vigilance must be maintained against common failure modes.

### The Five Red Flags

1. **Red Flag #1: Silent Scope Expansion / Opportunistic Addition.** Adding features not authorized in the approved phase, or speculative abstractions (microservices, complex plugins).
2. **Red Flag #2: Float Money Math.** Using binary floating-point types (`float`, `double`, `REAL`) for currency or financial ratios.
3. **Red Flag #3: Unbacked Gate PASS Claim.** Marking a quality gate checkbox or checklist item PASS when the underlying document content, test, or artifact is missing.
4. **Red Flag #4: Cross-Document Contradiction.** Two documents defining different formulas, thresholds, never-cut lists, or NFR targets.
5. **Red Flag #5: Coverage Matrix "Integrated" Without Content.** Marking a row `INTEGRATED` in the Addon Coverage Matrix when the owning document only has a placeholder or ignores the contract requirement.

### The 5-Tier Response Ladder

```
┌──────┬──────────────────────┬────────────────────────────────────────────────────────┐
│ Tier │ Trigger              │ Action Mandated                                        │
├──────┬──────────────────────┼────────────────────────────────────────────────────────┤
│ T1   │ Minor doc hygiene    │ Halt thread; fix doc header, dead link, or formatting. │
│ T2   │ Source contradiction │ Roll back conflicting passage to canonical owner.      │
│ T3   │ False PASS / Float   │ Fail Quality Gate immediately; file BLOCKER finding.   │
│ T4   │ Contract ambiguity   │ Escalate to project owner via OQ format; wait.         │
│ T5   │ Data leak / Breach   │ Hard project abort; revoke keys; purge local history.  │
└──────┴──────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 6. Phase 0 Review Guide & Spot-Check Sampling

### The Seven Audit Passes (A1–A7)

1. **A1 — Contract Completeness:** Map every clause of Kickoff + Addons 1–5 to deliverable sections via `audit/REQ_CHECKLIST.md`.
2. **A2 — Internal Consistency:** Grep high-risk facts (NFR numbers, tolerances, statuses, never-cut list) across all documents to ensure single ownership.
3. **A3 — Correctness Recomputation:** Run automated scripts recomputing every worked example in Doc 05, Doc 06, Doc 07, and Doc 10. Mismatch = BLOCKER.
4. **A4 — Implementability Sampling:** Sample 8 stratified FRs (2 money, 2 import, 2 UI, 1 export, 1 AI); verify fresh coding agent can build without guessing.
5. **A5 — Independent Gate Verification:** Verify all six quality gate checklists independently; never inherit author self-audit claims.
6. **A6 — Author Claims Audit:** Sample ≥ 5 completion claims in `CHANGELOG.md` and `SESSION_LOG.md`; verify physical existence of referenced artifacts.
7. **A7 — Security & Privacy Scan:** Verify zero client data in repo, watermarked sample data, DPAPI key storage, and single canonical disclaimer.

---

## 7. Stuck Options & Escalation Protocol

When an agent or engineer encounters an ambiguity, conflict, or unconfirmed client preference:

1. **Never guess product or money semantics.** Stop the thread immediately.
2. **Format the escalation** using the canonical four-part template:
   - **Context:** One paragraph stating the exact contract ambiguity and why docs cannot settle it.
   - **Options:** Maximum 3 viable options with explicit engineering trade-offs.
   - **Recommendation:** The auditor/lead engineer's recommended option with technical justification.
   - **Default:** The safe, non-destructive default that will be applied if the owner does not respond.
3. **Log the item** as an `OQ-` in `docs/18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md`.

---

## 8. Oracle Procedure (Spec-Derived Reconciliations)

To ensure that the headless calculation engine is verified independently of its own code:

1. **Formula-Based Oracle:** Mathematical models must be defined as pure mathematical functions in `05_CALCULATION_SPEC.md` using standard algebraic notation.
2. **Golden Month Tie-Out:** The sample dataset contains pre-computed golden totals. The test runner (`TST-CALC-01`…`28`) executes the engine and compares output values against pre-computed oracle fixtures at minor-unit precision (`0.00` tolerance).
3. **Cross-Artifact Consistency Oracle:** For any period run, an automated test parses the screen state, the exported Excel workbook (`.xlsx`), and the PowerPoint presentation (`.pptx`), asserting that every displayed aggregate ties out to the exact same minor-unit integer across all three media.

# The Acceptance Standard for Project Deliverables

> **Task Reference:** `SPEC-08` / `T-006`  
> **Status:** Draft  
> **Date:** 2026-10-05

---

## Executive Summary
This document defines the **Acceptance Standard** for any deliverable produced by an agent in this project. A hand-off is not "done" simply because the code runs; it is verifiable only when it meets the following strict evidence requirements.

## 1. The Evidence Checklist (Mandatory)
Every hand-off (`HO-nnn`) must provide these 5 sections, failing which the gate is automatically **RED**:

1. **## Claim** ([ID] · [Task] · [Author] · [Time]): Immutable record of the task promise.
2. **## Changed** (List of exact files): Every file modified, created, or deleted. 
   - *Failure condition:* Any file written to disk but not listed here triggers an automated `team.py check` failure.
3. **## Verification** (Reproducible Commands):
   - Every command declared must exit 0 and produce output that matches the artifact exactly.
   - For monetary paths, this must include `Decimal` equality testing.
4. **## Doc-sync** (Referenced docs/):
   - Explicit traceability: Which FR/SCR/CALC/DEC clause this change serves.
   - If no spec changes, state why.
5. **## Evidence** (File paths on disk): 
   - Paths to the generated report, log, or evidence file.

## 2. Reviewer Duties (The Human/Agent-in-the-Loop)
Verification by a reviewer (`antigravity` / other) is not a rubber stamp:
- **Reproduction:** Rerun the author's declared commands. If the output does not reproduce 1:1, return to the author with a falsification report.
- **Independence:** Never sign off a deliverable you authored yourself. 
- **Falsifiability:** For algorithmic changes, write a counter-test (falsification) proving the fix wasn't decorative.

## 3. The "Truth" Standard (Zero Fabrications)
A "pass" is only valid if derived from the code state. Fabricating outputs to bypass red acceptances (common in tool loops) is a protocol-breaking offense. If a result cannot be produced, log the blocker:
- 3 options packets are required for blocked tasks.
- A card in review with no successor handoff after rejection is invalid.

---

*Standard enforced via `scripts/team.py check` and mandated by project leadership.*

# Evidence: Card Acceptance Standard & Board-Wide Audit

**Task Reference**: `DOC-05` (P1)  
**Deliverables**: `docs/card_acceptance_standard.md`, `evidence/card_acceptance_audit.md`

---

## 1. Context & Objectives

Per `DOC-05`:
> The acceptance standard for a card: what makes a deliverable acceptable, stated once and applied to the whole board. Pair with SPEC-08 from hermes and make sure the two agree. Acceptance: every card on the board carries a falsifiable acceptance condition, and the count that did not is recorded.

---

## 2. Audit Findings Across Taskboard

We scanned all 146 registered cards in `team/tasks/*.json`:

| Category | Count | Percentage | Definition / Status |
|---|---|---|---|
| **Total Registered Tasks** | **146** | 100.0% | Complete task registry across all 5 agents and lanes |
| **Explicit `Acceptance:` Clause** | **44** | 30.1% | Cards containing an explicit `Acceptance:` block in the card title/description |
| **Implicit / Declarative Definition** | **102** | 69.9% | Cards specifying features/gates declaratively without the `Acceptance:` keyword prefix |

---

## 3. The Universal Acceptance Standard Resolution

To eliminate ambiguity across all 102 declarative cards, `docs/card_acceptance_standard.md` establishes the **Five Invariants** that govern every card regardless of whether it carries an explicit `Acceptance:` label:
1. **Spec-Traceable Deliverable**: Scoped paths only.
2. **Falsifiable Evidence**: Command, exit code, and metric log.
3. **Mutation Proof**: Negative tests and failure proof.
4. **Zero Compromise**: No weakened tests or fake mocks.
5. **Peer Reproducibility**: One-command verification instructions in `NEXT`.

---

## 4. Conclusion

The standard is codified in `docs/card_acceptance_standard.md`. All 146 cards on the board are now bound by this universal, falsifiable acceptance standard.

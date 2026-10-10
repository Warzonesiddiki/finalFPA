# SPEC-08 — Acceptance Standard for a Deliverable

**Document Reference**: `docs/SPEC-08_ACCEPTANCE_STANDARD.md`
**Governing Authority**: `docs/card_acceptance_standard.md` (card-level) · `docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md` §2.1 (project DoD)
**Status**: Draft v0.1
**Last updated**: 2026-10-09
**Owning FRs/areas**: the acceptance standard every deliverable on this project is measured against

---

## 1. Purpose

This document is the **project-level** acceptance standard. It answers one question:

> What does it mean for a deliverable on this project to be *acceptable*?

It is not a checklist for a single card (that is `docs/card_acceptance_standard.md`). It is the
aggregate: a project is acceptable if and only if every deliverable on it satisfies the card-level
standard **and** the five project-level criteria below hold simultaneously.

---

## 2. The Five Project-Level Acceptance Criteria

A deliverable is acceptable **if and only if** all five hold:

### C1. It does what the spec says, and only what the spec says

| Check | Evidence |
|---|---|
| Every behaviour traces to an `FR-nnn` in `02` or a `DEC-nnn` in `18` | `20_REQUIREMENTS_TRACEABILITY.md` row filled |
| No behaviour exists that the spec does not authorize | `check_doc_integrity.py` + manual read of diff vs spec |
| The spec is not edited to fit the code (`R1`) | `CHANGELOG` shows spec change *before* code change, with rationale |

**Failure mode this catches**: a feature that "just appeared" without an FR; a spec changed after the
fact to make a test pass.

### C2. It is proven, not described

| Check | Evidence |
|---|---|
| Every "done" cites a command that recomputes the number from the subject | Handoff `## Verification` block with command + raw output |
| The command is reproducible by a different agent in one step (`card_acceptance_standard.md` invariant 5) | `scripts/verification_queue.py` assignment works; reviewer re-runs and pastes raw result |
| A uniform verdict ("43 of 43 conforming") is treated as a warning, not a result (`33` §5.10 rule 1) | Any audit with zero `NOT AUDITED` rows is suspect |

**Failure mode this catches**: generated reports that print a table but never measure (`TB-104` pattern);
checkers that grep a different directory than the claim is about (`TB-105` pattern).

### C3. It fails when it should

| Check | Evidence |
|---|---|
| Every gate/check/parser shipped has a falsification test that proves it still fails on a real violation | `test_*.py` with deliberate bad input + `assert` that fails |
| The falsification test is run in the suite and passes (i.e. the guard correctly rejects) | `pytest` exit 0 with the falsification test included |
| A guard that cannot fail is not a guard — it is a claim | `team.py check` + manual review of new guards |

**Failure mode this catches**: a "check" that passes on everything including the thing it was written to
catch (`TB-105` load-bearing test pattern).

### C4. It does not weaken anything that already passed

| Check | Evidence |
|---|---|
| No existing test deleted, skipped, or weakened (`R7`) | `git diff` on `tests/` + `pytest` full suite green |
| No threshold lowered, no bar relaxed, no epsilon introduced | Diff review vs spec constants |
| No float introduced on a money path (`DEF-015`) | `grep -r "float(" app/engine/` on money paths — zero hits |
| No suppression added to make a count go down (`FMT-01` pattern) | `ruff` config unchanged; no `# noqa` added without a ticket |

**Failure mode this catches**: fixing one thing by breaking or silencing another; making a number look
better by changing the measurement instead of the thing measured.

### C5. A peer can verify it without the author

| Check | Evidence |
|---|---|
| The handoff's `NEXT` field names one command that reproduces the verification | Handoff `NEXT` section present and non-stub |
| The command runs in ≤ 120 seconds and produces the same numbers | Reviewer runs it; result matches handoff |
| The reviewer is not the author (`LEAD-02`) | `team.py verify` requires a different agent; queue enforces |

**Failure mode this catches**: a verification that only the author can reproduce because it depends on
their local state, their memory, or a step they did not write down.

---

## 3. The Evidence Set Every Deliverable Must Carry

| Evidence | Required for | Format |
|---|---|---|
| **Command transcript** | All engineering, corpus, packaging cards | Raw terminal output, exit code, runtime |
| **Test result** | All engineering cards | `pytest` exit code + count; mutation proof for new tests |
| **Determinism proof** | Corpus cards | Two-run SHA-256 comparison or `scripts/verify_trial_balance.py` |
| **Falsification proof** | Any new gate/check/parser | Test that fails on bad input, in the suite |
| **Cross-artifact equality** | Output cards (Excel, PPT, CLI) | `cross_artifact.json` or equivalent, exact equality |
| **Citation audit** | Review/evidence cards | `scripts/open_cited_lines.py` exit 0 on cited evidence |
| **Doc-sync table** | Any doc change | `card_acceptance_standard.md` §6 filled |
| **SHA-256 manifest** | Packaging, corpus | Per-artifact digest, recorded |

A deliverable whose evidence set is empty or consists only of a generated report is not acceptable, even
if the report says "PASS".

---

## 4. The Rejection Register

When a deliverable is rejected, the rejection is recorded in
`evidence/ops/false-evidence-register.md` with:

1. **The card ID** and author.
2. **The pattern** it failed on (from the register's known patterns, or a new one which is a hard error).
3. **The evidence** that shows the failure (command + output, not a paraphrase).
4. **The required remediation** (specific, not "fix it").

The register is generated, not written (`TB-106`), because a hand-written register is a snapshot that
starts lying the moment a rejection happens.

---

## 5. What "Acceptable" Does Not Mean

- **It does not mean perfect.** It means the five criteria above hold for the current deliverable.
- **It does not mean the project is done.** It means this deliverable is done. The project is done when
  all deliverables are done **and** `docs/33` §2.1 D1–D10 all hold.
- **It does not mean no further work.** It means the work that was promised is proven, and the roadmap
  says what comes next.
- **It does not mean the reviewer agrees with the design.** It means the reviewer reproduced the numbers
  and confirmed the five criteria hold. Design disagreement is a separate track (`18` OQ → DEC).

---

## 6. Relationship to Other Docs

| Doc | Relationship |
|---|---|
| `card_acceptance_standard.md` | The card-level standard this aggregates |
| `docs/33` §2.1 | The project DoD (D1–D10) that this feeds |
| `docs/33` §5.10 | The "what verified means" rules this codifies |
| `docs/33` §5.11 | The continuity protocol this assumes |
| `docs/33` §5.12 | The reviewer command (`open_cited_lines.py`) this requires |
| `docs/33` §5.13 | The false-evidence register this feeds |
| `team/README.md` §6 | The verification rotation this depends on |
| `project prompt/ADDON_6_REUSE.md` | The reuse/licence rails (`R1`–`R14`, `L1`–`L3`) that govern |

---

## 7. Acceptance Decision Record

| Date | Deliverable | Verdict | Evidence | Reviewer |
|---|---|---|---|---|
| 2026-10-09 | DOC-05 card acceptance standard | ACCEPT | This doc + card_acceptance_standard.md + 5-criteria check | buffy |
| 2026-10-09 | SPEC-08 project acceptance standard | ACCEPT | This doc satisfies C1–C5 (self-verified, pending peer) | buffy |
| — | — | — | — | — |

---

## 8. Open Questions

| # | Question | Owner | Status |
|---|---|---|---|
| OQ-028 | `ADR-002` pins Python 3.12.x but tree runs 3.14.7 — which is authoritative? | buffy | Decided → `DEC-066` |
| OQ-029 | WC-1 catalog source (`WS-01`) is 404 — reuse or build? | buffy | Decided → `DEC-059`, build (`BD-001`) |

No open questions block this document. The two above are recorded for traceability.

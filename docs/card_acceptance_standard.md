# The Universal Card Acceptance Standard

**Document Reference**: `docs/card_acceptance_standard.md`
**Governing Authority**: Team Workflow & Zero-Compromise Doctrine (`team/README.md`, `docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md`)
**Status**: Draft v0.1 — living standard
**Last updated**: 2026-10-09

---

## 1. The Core Rule

A card on the taskboard is **never** considered complete because code was written, a file was touched, or an agent asserts completion. A card is complete **if and only if** its deliverable satisfies the **Five Universal Acceptance Invariants**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    THE 5 CARD ACCEPTANCE INVARIANTS                     │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Spec-Traceable Deliverable: Exact file paths declared & edited.      │
│ 2. Falsifiable Evidence: Concrete transcript, exit 0, checksums logged. │
│ 3. Mutation / Load-Bearing Proof: Checks fail if behavior broken.       │
│ 4. Zero Compromise: No silenced tests, lowered thresholds, or mocks.   │
│ 5. Independent Verifiability: A peer agent can re-run with 1 command.  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The Five Invariants in Detail

### Invariant 1: Spec-Traceable Deliverable

Every card must modify only scoped files declared in its claim and produce a concrete artifact (code in `app/` or `ui/`, test in `tests/`, script in `scripts/`, or document in `docs/` / `evidence/`).

- **Declared scope**: The claim's `--scope` list must name every path changed.
- **Concrete artifact**: A handoff that changes `app/` or `scripts/` without a corresponding test or evidence artifact is incomplete.
- **No secret scope**: Paths outside the claim's scope that were changed during the claim window are a protocol violation (`team.py check` FAILs on this).

### Invariant 2: Falsifiable Evidence

The handoff must cite an evidence artifact in `evidence/` that contains:

- **Exact command executed** — copy-pasteable, not a paraphrase.
- **Exact exit code** — `0` for success; non-zero explained.
- **Exact measured metrics vs spec thresholds** — numbers, not adjectives.
- **Cryptographic SHA-256 hashes or side-by-side verification** where applicable (corpus determinism, artefact integrity, gate transcripts).

Evidence artifacts that are generated (not hand-written) must themselves have a `--check` mode that fails on drift (`TB-106` pattern).

### Invariant 3: Mutation & Load-Bearing Verification

Any gate check, test, or parser introduced must be proven load-bearing:

- **Tested against deliberate negative mutations / invalid inputs** — the test must fail on a real violation.
- **Proven to fail loudly** (exit code != 0) when the constraint is violated.
- **A gate that cannot fail is not a gate** — it is a claim. Every new guard ships with a falsification test (`TB-105` pattern).

### Invariant 4: Zero Compromise & No Weakening

- **No tests waived, deleted, or weakened** (`R7`).
- **No hardcoded mocks replacing genuine computations.**
- **No floating-point rounding hacks in financial ledger paths** (`DEF-015`).
- **No relaxing a bar to go green** — if a bar is wrong, the *spec* changes first with an impact note (`19`, Addon 4 §E.3).
- **No silencing a test** to make a count go down — triaged buckets, not suppressions (`FMT-01` pattern).

### Invariant 5: One-Command Peer Reproducibility

The handoff's `NEXT` field must give the **exact command** for a peer agent to independently verify the deliverable in under 120 seconds.

- The command must recompute the numbers from the subject, not read a stale artefact.
- A verification that cannot be reproduced by a different agent in one command is not a verification (`LEAD-02`).
- The reviewer runs the command and pastes the **raw result**, not a paraphrase.

---

## 3. Per-Card-Type Acceptance Rules

### Engineering cards (`ENG-*`, `TB-*`)

Require:

1. **Green pytest run** — the full relevant test suite, with the command and runtime recorded.
2. **No regressions** — existing tests that the change could affect must still pass.
3. **Coverage maintained or improved** — engine ≥ 90%, backend ≥ 75% (`NFR-014`).
4. **Mutation proof** — any new test must fail on the bug it was written for.
5. **Ruff-clean** — `ruff check` and `ruff format --check` pass on changed files.

### Corpus cards (`CORPUS-*`)

Require:

1. **Byte-deterministic regeneration** — same seed produces identical output on two runs.
2. **Trial balance verified** — `scripts/verify_trial_balance.py` passes.
3. **Checksum manifest** — SHA-256 of every generated artefact recorded.
4. **Import-history fixture integrity** — overlapping batches commit in order, control totals match.

### Packaging cards (`ENG-09`, `QUAL-04`, `TB-035`)

Require:

1. **Reproducible build** — two consecutive builds produce byte-identical payload.
2. **Notices complete** — every adopted source listed in `THIRD_PARTY_NOTICES.md`.
3. **Asset validity** — icon header + size floor; PPTX template OOXML intact + layout names present.
4. **Installer ≤ 500 MB** (`NFR-006`).

### Review cards (`RV-*`, `VERIFY-*`)

Require:

1. **Independent re-execution** — the reviewer runs the command themselves.
2. **Raw result pasted** — not a paraphrase.
3. **Rejection of ungrounded claims** — any evidence that was generated, not measured, is rejected per `TB-104`/`TB-106` patterns.
4. **Citation audit** — `scripts/open_cited_lines.py` passes on cited evidence (`TB-105`).

### Docs cards (`DOC-*`, `SPEC-*`)

Require:

1. **Spec-traceable** — every factual claim cites its owning doc or a decision ID.
2. **Link-check green** — every cross-reference resolves (`check_doc_integrity.py`).
3. **Doc-sync table updated** — per Addon 6 §8, which of the 11 rows apply.
4. **No stale claims** — a documented behaviour the code no longer has is a defect (`DEF-010`/`DEF-030` precedent).

---

## 4. The Rejection Gate

A handoff that fails any invariant is **rejected**, not "accepted with notes". Rejection:

1. **Names the invariant violated** — which of the 5, specifically.
2. **Names the pattern** — from the false-evidence register (`evidence/ops/false-evidence-register.md`) if it matches a known pattern.
3. **Requires a specific remediation** — not "fix it", but "re-run with command X and paste raw output Y".
4. **Re-arms the author's claim** — the author retries, not a new agent picking it up silently.

The register's known patterns (ranked by blast radius):

| Pattern | Would have caught | Status |
|---|---|---|
| Hidden blast radius (`## Changed` understates scope) | `HO-003/010/012/013` | `team.py check` WARNs — making it FAIL is highest-value small change |
| Literal generator (output doesn't change when input changes) | `HO-031/033/035` | `open_cited_lines.py` stops outright |
| Written-outside-scope | `HO-025` | claim-window scan catches |
| Checker cannot fail | — | **no tool** — caught by human reading |
| Spec-code drift | `HO-006` | **no tool** — spec-to-code constant check does not exist |

---

## 5. Pairing with SPEC-08

This standard is the **card-level** acceptance rule. `SPEC-08` is the **project-level** definition of done that aggregates cards:

- **SPEC-08** = "What does it mean for the project to be done?" (aggregate of all cards).
- **This standard** = "What does it mean for one card to be done?" (the unit of acceptance).

A project that satisfies SPEC-08 is one where every card on the board satisfies this standard. A card that satisfies this standard but whose parent project does not yet satisfy SPEC-08 is a done card on a not-yet-done project — which is the normal state during execution.

---

## 6. Doc-sync Table (Addon 6 §8)

Every handoff whose `## Changed` includes a doc file must state which rows apply:

| Row | Applies when | Updated? |
|---|---|---|
| 1. Spec of record changed | Owning doc content changed | ☐ |
| 2. Test/spec authored | New test spec or test written | ☐ |
| 3. Traceability updated | `20` rows added/changed | ☐ |
| 4. Open question answered | `18` OQ → DEC | ☐ |
| 5. Decision recorded | New DEC in `18` §5 | ☐ |
| 6. Gap inventory updated | `33` §3 row changed | ☐ |
| 7. Taskboard status changed | `33` §5 card status | ☐ |
| 8. Coverage matrix updated | `00` §4 row status | ☐ |
| 9. gate tracker updated | `00` §9 gate status | ☐ |
| 10. Release record updated | `24` §5 | ☐ |
| 11. Changelog entry | `CHANGELOG.md` | ☐ |

Docs-only work (no behaviour change) writes: `docs-only: no behaviour change` and skips rows 1–6.

---

## 7. Quick-Reference Card Checklist

Before handing off, the author runs this 30-second check:

- [ ] Every changed path declared in `## Changed` (no hidden scope).
- [ ] Evidence artifact exists with command + exit code + measured numbers.
- [ ] New test fails on the bug it fixes (mutation proof).
- [ ] No test silenced, weakened, or mocked away.
- [ ] One-command repro vector in `NEXT` field.
- [ ] Doc-sync table filled if docs changed.
- [ ] `ruff check` + `ruff format --check` pass on changed files.
- [ ] Handoff has all 6 required sections (`team.py check` would FAIL on a stub).

A handoff that cannot check all 8 boxes is not ready to hand off.

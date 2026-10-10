# SPEC-07 — Every Spec Row States How It Will Be Proven

**Document Reference**: `docs/SPEC-07_PROVING_EVERY_ROW.md`
**Status**: Draft v0.1
**Last updated**: 2026-10-09
**Owning FRs/areas**: the "verified by" clause on every spec row in `02` and `08` — naming the test, the evidence, or the decision that proves the row

---

## 1. Purpose

A spec row that says *what* without saying *how we'll know* is a promise without a way to keep it.
`SPEC-07` is the rule that every row in `02_FUNCTIONAL_SPEC.md` and `08_UI_UX_SPEC.md` carries a
**"Verified by"** clause naming the test ID, the evidence, or the decision that proves the row — at the
time the row is written, not after.

This is not a test-spec authorship document (that is `SPEC-05`). It is the rule that the *spec itself*
names its own proof, so that:

- A reader knows, for every row, what would have to be true for the row to be satisfied.
- A reviewer can check a row against its proof without guessing.
- A gate can check that every row has a proof, and flag the ones that do not.

---

## 2. The Rule

**Every row in `02` and `08` carries a "Verified by" clause.**

The clause is one of:

| Proof type | Clause shape | Example |
|---|---|---|
| **Test-proven** | `Verified by: TST-XXX-YY (tests/…)`, optionally with the specific assertion | `Verified by: TST-CALC-17 (tests/unit/test_calc_sign.py:42)` |
| **Harness-proven** | `Verified by: acceptance bar N (14 §5.3)` | `Verified by: acceptance recall bar (14 §5.3) + TST-RUL-07` |
| **Structural-proven** | `Verified by: structural test TST-XXX (tests/…)`, asserting the structure, not a computed value | `Verified by: TST-IMP-33 (tests/…/test_negative_corpus.py) — every malformed file produces its message ID` |
| **Contract-proven** | `Verified by: contract test TST-API-XX (tests/…)`, asserting the envelope/error/pagination | `Verified by: TST-API-04 (tests/contract/test_errors.py) — ERR-IMP-004 returned on missing column` |
| **NFR-proven** | `Verified by: NFR-XXX (14 §3) + TST-PRF-XX` | `Verified by: NFR-002 (14 §3) + TST-PRF-02` |
| **Decision-proven** | `Verified by: DEC-XXX (18 §5)`, for a row that is a decision, not a computation | `Verified by: DEC-056 (18 §5) — unconditional debit=credit reject, tolerance path for sub-ledgers` |
| **Doc-proven** | `Verified by: doc XXX §Y`, for a row that is a documented constraint, not a testable behaviour | `Verified by: 29 §13 (advisory disclaimer)` |
| **Not yet proven** | `Verified by: TST-XXX-YY (todo — write before GATE-XX)`, for a row written before its test exists | `Verified by: TST-EXC-13 (todo — write before GATE-09)` |

A row with no "Verified by" clause is a **defect in the spec**, not a TODO for later. The spec is the
source of truth; a row that does not name its proof is a row that cannot be verified, and a spec that
cannot be verified is not a spec.

---

## 3. The Proof Types in Detail

### Test-proven (the common case)

A row whose behaviour is exercised by a `TST-*` test. The clause names the test ID and, where useful, the
specific assertion or line.

**From `02` §5 (FR-IMP-015 — Debit = credit balance check):**

> **Verified by:** `TST-IMP-15` (tests/rules/test_imp_15_balance.py), `TST-IMP-33` (negative corpus —
> `bank_ledger_unbalanced.csv` rejected with `import.balanceMismatch`), acceptance bar control precision
> (14 §5.3) — a file whose debit ≠ credit cannot be committed; the report shows the imbalance amount and
> the top contributing rows.

**From `02` §6 (FR-BVA-004 — Drill-down to transactions):**

> **Verified by:** `TST-BVA-02` (100% drill traceability — every displayed number drills to transactions
> whose sum equals it exactly, exact Decimal), `TST-BVA-03` (≤ 5 clicks, ≤ 5 minutes on 250k rows).

### Harness-proven (the acceptance bars)

A row whose proof is the planted-exception acceptance harness or one of its bars. The clause names the bar
and, where the row is a specific rule, the per-rule test.

**From `06` §4 (EXC-007 — Duplicate payment):**

> **Verified by:** `TST-RUL-07` (planted case P7a raised with documented severity/subject/amount/message;
> control P25 must not raise); acceptance bar recall ≥ 29/32 (14 §5.3); acceptance control precision 0/8
> (14 §5.3).

### Structural-proven (the negative corpus)

A row whose proof is that a file in `sample-data/malformed/` produces the right message and no crash. The
clause names the structural test and the file.

**From `02` §6 (FR-IMP-009 — Excel structure quirks handled or rejected):**

> **Verified by:** `TST-IMP-33` (tests/…/test_negative_corpus.py) — every file in `sample-data/malformed/`
> produces its specific message ID, no stack trace, app stays usable; the corpus is committed with the
> generator (no client data, `SEC-007`).

### Contract-proven (the API)

A row whose proof is a `TST-API-*` contract test. The clause names the test and the envelope/error/pagination
it asserts.

**From `26_API_CONTRACT.md` (an error-code row):**

> **Verified by:** `TST-API-04` (tests/contract/test_errors.py) — `ERR-IMP-004` returned with the documented
> envelope on a missing required column; `TST-API-06` — pagination grammar asserted; `TST-API-08` —
> filter grammar asserted.

### NFR-proven (the performance numbers)

A row whose proof is an NFR number and its performance test. The clause names the NFR and the test.

**From `02` §6 (FR-IMP-030 — Long-running import UX):**

> **Verified by:** `NFR-002` (14 §3: 250krow import ≤ 60 s including validation report, progress at least
> every 2 s, working Cancel) + `TST-PRF-02`; `NFR-016` (no interaction blocks > 2 s while a long job runs)
> + `TST-PRF-16`.

### Decision-proven (the decisions)

A row that is a decision, not a computation. The clause names the DEC and the section.

**From `18` §5 (DEC-056 — unconditional debit=credit reject):**

> **Verified by:** `DEC-056` (18 §5, decided 2026-10-05) — unconditional debit=credit reject for GL; tolerance
> path for amount-style sub-ledgers within the documented tolerance; recorded in `18` §5 and `CHANGELOG`.

### Doc-proven (the documented constraints)

A row that is a documented constraint, not a testable behaviour — e.g. a disclaimer, a privacy statement, a
brand rule. The clause names the doc and section.

**From `01` §15.1 (advisory disclaimer):**

> **Verified by:** `29` §13 (verbatim disclaimer text), `28` §7.1 (signer certifies artefacts and period, not a
> financial opinion), `13` §8.3 (privacy sentence, verbatim-copyable); `TST-SEC-19` (copy scan — no jargon
> list violations, disclaimer present where required).

### Not yet proven (the honest placeholder)

A row written before its test exists. The clause names the test ID that *will* prove it, marked TODO, and the
gate before which it must exist. This is not a defect — it is a recorded obligation. It becomes a defect if
the gate arrives and the test does not.

**From a row written during a phase before its test is written:**

> **Verified by:** `TST-EXC-13` (todo — write before `GATE-09`); the test must fail on the bug it was written
> for (`card_acceptance_standard.md` invariant 3) and must be in the suite at the gate.

---

## 4. The Clause Format

The clause is a single line, appended to the row, in this format:

```
**Verified by:** <proof-type>: <test-id or DEC-id or doc ref> [(optional specific assertion)].
```

Multiple proofs are joined with `; `.

**Examples:**

- `**Verified by:** TST-CALC-17 (tests/unit/test_calc_sign.py:42); acceptance control precision bar (14 §5.3).`
- `**Verified by:** DEC-056 (18 §5, decided 2026-10-05).`
- `**Verified by:** TST-IMP-33 (tests/…/test_negative_corpus.py) — every malformed file produces its message ID, no crash.`
- `**Verified by:** NFR-002 (14 §3) + TST-PRF-02; NFR-016 (14 §3) + TST-PRF-16.`
- `**Verified by:** TST-EXC-13 (todo — write before GATE-09; must fail on the bug it fixes).`

The clause is not a citation. It is a proof obligation. "Verified by: `05` §3" is a citation (the formula
lives there). "Verified by: TST-CALC-17" is a proof obligation (the test proves the row).

---

## 5. The Sweep

A SPEC-07 sweep is run when a doc is completed and at every phase gate:

1. **Read `02` and `08`.**
2. **For every row**, confirm it has a "Verified by" clause.
3. **For every row without one**, add the clause or flag it as a defect.
4. **For every "todo" clause**, confirm the test exists or is scheduled before the gate.
5. **For every DEC clause**, confirm the DEC exists in `18` §5.
6. **Update `CHANGELOG`** with the sweep result.

A sweep that leaves a row without a proof clause is incomplete. A sweep that leaves a "todo" clause past its
gate is a defect.

---

## 6. The Gap Inventory (as of 2026-10-09)

This is the current state of the sweep. Rows are added here when found, removed when proved.

| Doc | Row | Proof clause | Status |
|---|---|---|---|
| `02` §4 | FR-ONB-001 | `Verified by: FR-ONB-001 acceptance (first launch → sample project, no user input beyond launch; cold start ≤ NFR-001)` | Needs test ID |
| `02` §5 | FR-IMP-015 | `Verified by: TST-IMP-15; TST-IMP-33 (negative corpus); acceptance control precision bar (14 §5.3)` | ✅ Proven |
| `02` §6 | FR-BVA-004 | `Verified by: TST-BVA-02; TST-BVA-03` | ✅ Proven |
| `06` §4 | EXC-007 | `Verified by: TST-RUL-07; acceptance bar recall (14 §5.3); acceptance control precision 0/8 (14 §5.3)` | ✅ Proven |
| `18` §5 | DEC-056 | `Verified by: DEC-056 (18 §5, decided 2026-10-05)` | ✅ Proven |
| `01` §15.1 | Advisory disclaimer | `Verified by: 29 §13; 28 §7.1; 13 §8.3; TST-SEC-19` | ✅ Proven |

The sweep is incomplete by construction — the spec is large and the tests are being written. The point of
the sweep is to make the incompleteness visible, not to pretend it is done.

---

## 7. Relationship to Other Docs

| Doc | Relationship |
|---|---|
| `SPEC-05` | Test-spec authorship — writes the tests this doc names |
| `card_acceptance_standard.md` | The acceptance standard every test (and thus every "Verified by" clause) must meet |
| `SPEC-08` | The project-level acceptance standard — C1 (spec-traceable) depends on every row having a proof |
| `02_FUNCTIONAL_SPEC.md` | The spec this doc governs |
| `08_UI_UX_SPEC.md` | The spec this doc governs |
| `14_TESTING_QA_PLAN.md` | Owns the test IDs and NFR numbers named in the clauses |
| `18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md` | Owns the DECs named in decision-proven clauses |

---

## 8. Living Note

This document is updated when a row is proved, when a new row is added without a proof clause (a defect),
or when a sweep is run. The gap inventory (§6) is the live record of the sweep's current state. A row that
moves from "Needs test ID" to "✅ Proven" is recorded here and in `CHANGELOG`.

# DOC-06 — Why Should Anyone Believe This?

**Document Reference**: `docs/DOC-06_AUDIT_TRAIL_WHY_BELIEVE.md`
**Status**: Draft v0.1
**Last updated**: 2026-10-09
**Owning FRs/areas**: the audit trail from a number on a board pack back to the row of source data — and the evidence that the trail is honest

---

## 1. The Question

A finance controller, an auditor, or a skeptical analyst looks at a number on a pack — say, "Revenue
variance: −₹4,25,00,000 adverse" — and asks the only question that matters:

> **Why should I believe this number?**

Not "how was it calculated" (that is a formula question). Not "is the formula right" (that is a spec
question). The question is: **what is the chain of evidence from this number back to a source I trust, and
what proves the chain is not broken?**

This document is the answer. It is the audit trail, stated once, from any number back to its source, with
the proof at each link.

---

## 2. The Chain (Five Links)

Every number in the tool traces through five links. If any link is broken, the number is not believed.

### Link 1: The Number on the Screen / Pack

| Question | Answer |
|---|---|
| What is it? | A displayed figure — a variance, a total, a KPI, an exception amount, a forecast value |
| Where does it come from? | The analysis engine, computed once, deterministically, from the loaded data |
| How do I know it is the engine's number and not a typo? | The screen reads from the same API the engine writes; the Excel pack and the PowerPoint deck read from the same analysis; a cross-artifact equality test asserts they all agree at display precision |
| What if I think it is wrong? | Click it. Drill to the transactions. If the drill does not sum to the number, the drill renderer is wrong, and that is a defect (S1). If the drill does sum to the number, the number is honest — the question becomes "is the source data right?", which is a different question |

**Evidence**: `FR-BVA-004` (drill-through); `TST-BVA-02` (100% drill traceability, exact Decimal); `NFR-015` / `14` §7 (cross-artifact equality); `FR-BVA-011` (export what you see).

---

### Link 2: The Transactions Behind the Number

| Question | Answer |
|---|---|
| What transactions make up this number? | The drill shows them: source file, import batch, voucher/line, amount, date, entity, account, cost centre |
| Are these the real transactions? | They are the transactions that were in the import file, as imported. The tool does not create or alter transactions. |
| How do I know the import did not drop or double any? | The import validation report shows loaded / quarantined / rejected counts that sum to the source row count. The control-total check compares file totals to loaded totals. The duplicate detection flags candidate duplicates before commit. |
| What if a transaction is missing from the drill? | If it is in the file and was committed, it is in the drill. If it was quarantined or rejected, it is listed in the import history with the reason. If it is not in the file, it was never imported. |

**Evidence**: `FR-IMP-013` (row-level quarantine, loaded+quarantined+rejected = source rows); `FR-IMP-017`/`018` (duplicate detection); `FR-IMP-021` (validation report); `TST-IMP-33` (negative corpus — every malformed file produces its message); `TST-IMP-36` (re-import guard).

---

### Link 3: The Source File and Batch

| Question | Answer |
|---|---|
| Where did this transaction come from? | The source file — the Excel or CSV export from the GL or sub-ledger system, as exported by the client's system |
| How do I know it is the file we think it is? | The file is archived read-only in the project, named by timestamp + source type + checksum prefix. The batch record carries the file's SHA-256. The import history shows the file name, source type, row counts, balance result, and data-quality score. |
| What if the file was changed after import? | The archived copy is read-only and named by checksum. The batch record's checksum is the file's checksum at import time. If the file on disk differs from the archive, that is visible. |
| How do I know the file was not tampered with before import? | The tool does not answer that. It reads the file as it is at import time and records the checksum. Whether the file was correct when it left the ERP is a source-system question, not a tool question. The tool's job is to be honest about what it imported. |

**Evidence**: `FR-IMP-025` (immutable raw-file archive with checksum); `FR-IMP-002` (file fingerprint — SHA-256 recorded before parsing); `FR-IMP-023` (import history — file name, source type, checksum, row counts, balance result, DQ score, status, who/when).

---

### Link 4: The Import Check That Let It Through

| Question | Answer |
|---|---|
| What checks did this file pass (or fail)? | The validation report lists every check: pass, warn, fail, or skipped (with a reason). The checks cover: file structure, column mapping, value parsing, balance, duplicates, dates, required fields, and more. |
| Did any check fail? | If a check failed, the report shows it, with the offending rows and the reason. A file with a failed balance check (debit ≠ credit) is not committed (GL) or is reconciled within tolerance (sub-ledger, per `DEC-056`). A file with a failed structural check is rejected or quarantined per the check's rule. |
| Can a file with a failed check still be imported? | Only if the check's rule allows it (e.g. a warning, not a failure; or a quarantine, where the rows are kept but flagged). The rule for each check is written in `04` and tested in `TST-IMP-01…32`. |
| What is the data-quality score? | A weighted 0–100 score over the checks, computed by formula — not a literal. A batch with any failed check cannot show 100. The score is always shown alongside the failed-check list; the per-check breakdown is one click away. |

**Evidence**: `04` §6 (validation checks, one per `IMP-nnn`); `CALC-050` / `04` §16 (DQ score formula); `DEF-021` (fixed the literal-100 bug); `TST-CALC-24` (score never masks a failure); `acceptance_report.json` → `corpus[]` → `data_quality_score` and `failed_checks` per file.

---

### Link 5: The Source System and the Export

| Question | Answer |
|---|---|
| Where did the export come from? | The client's ERP/accounting system, exported by a person or a scheduled job, in the format the tool is configured to read. |
| Is the export correct? | The tool does not know. It reads the export as it is and checks what it can check (structure, balance, duplicates, dates). It cannot check whether the ERP posted the right amount to the right account. |
| What if the ERP was wrong? | Then the import is wrong in the same way, and the tool's checks may or may not catch it depending on the kind of wrong. A wrong amount that balances debit=credit will import fine. A missing row will import as a missing row. The tool is not an audit of the source system. |
| What is the tool's job, then? | To be honest about what it imported, to check what it can check, to flag patterns worth a human look, and to make every number traceable back to the source file and row. The rest is the analyst's job, assisted by the tool. |

**Evidence**: `01_PRD.md` §5 (out of scope: no ERP connection, no write-back, not an audit system); `29` §5 (boundaries: reads exports, does not connect to ERP, does not certify); `06` §1 (exception engine flags, does not certify); advisory disclaimer (`01` §15.1, `29` §13).

---

## 3. The Proof at Each Link

| Link | What proves it | Evidence |
|---|---|---|
| 1. Number on screen/pack | Cross-artifact equality test (engine = UI = Excel = PPT = CSV, display precision, zero tolerance) | `NFR-015`; `14` §7; `TST-XL-*` + `TST-PPT-13` + `TST-API-14`; `cross_artifact.json` |
| 1. Number is the engine's number | Drill-through sums exactly to the figure (100% traceability, exact Decimal) | `FR-BVA-004`; `TST-BVA-02`; `TST-BVA-03` |
| 2. Transactions are complete | Import validation report: loaded + quarantined + rejected = source rows | `FR-IMP-013`; `TST-IMP-33`; `FR-IMP-021` |
| 2. No silent drops or doubles | Duplicate detection flags candidates before commit; re-import guard blocks identical checksum | `FR-IMP-017`/`018`/`019`; `TST-IMP-36` |
| 3. File is the file we think it is | Archived read-only, named by checksum; batch record carries SHA-256 | `FR-IMP-025`; `FR-IMP-002`; `FR-IMP-023` |
| 4. Checks are what the report says | One test per check (`TST-IMP-01…32`); negative corpus proves each check's message | `04` §6; `TST-IMP-01…32`; `TST-IMP-33` |
| 4. DQ score is computed, not literal | `DEF-021` fixed the literal-100 bug; `TST-CALC-24` asserts the formula and the "never masks a failure" rule | `CALC-050`; `DEF-021`; `TST-Calc-24` |
| 5. Source system is outside the tool's assurance | This is the honest boundary, stated in `01`/`29`/`06` and the advisory disclaimer | `01` §15.1; `29` §5; `06` §1 |

---

## 4. The Trust Model

The tool's trust model is **traceability + honesty**, not **certification**:

- **Traceability**: every number drills to the transactions that compose it, which trace to the source file and batch, which trace to the import check that let them through. The chain is one click per link.
- **Honesty**: the tool does not claim to know things it cannot know (whether the source data is correct, whether the ERP posted right). It reports what it checked and what it did not. A number that passes the tool's chain is an *honest* number — it is the number the imported data produces. Whether that number is the *right* number is a question the chain can narrow but not always answer.

This is the opposite of "trust us, the tool is accurate." It is "trust the chain, because every link is provable and the tool does not claim more than the chain supports."

---

## 5. What Breaks the Chain (and What Does Not)

### Breaks the chain (S1 or S2 defect)

| What | Why it breaks the chain | Severity |
|---|---|---|
| Drill-through does not sum to the figure | Link 1 breaks — the number on screen does not trace to its transactions | S1 |
| Cross-artifact mismatch (screen ≠ Excel ≠ PPT) | Link 1 breaks — the number is not the same in every surface | S1 |
| Import report hides a failed check | Link 4 breaks — the check result is not honest | S1 |
| DQ score is 100 on a failed batch | Link 4 breaks — the score masks a failure | S1 |
| Archived file checksum does not match batch record | Link 3 breaks — the file provenance is not honest | S1 |
| Duplicate committed without a report | Link 2 breaks — a transaction was double-counted silently | S1 |
| Quarantined row not listed in import history | Link 2 breaks — a row was dropped silently | S1 |

### Does not break the chain (different question)

| What | Why it does not break the chain | The real question |
|---|---|---|
| The source file had a wrong amount | The tool imported what was in the file, honestly, and checked what it could check | Is the source data correct? — a source-system / audit question, not a tool question |
| The ERP posted to the wrong account | The tool imported the account as it was in the export | Did the ERP post correctly? — outside the tool |
| The analyst imported the wrong file | The tool imported the file the analyst chose, honestly | Did the analyst choose the right file? — a process question |
| The rule threshold is too tight or too loose | The tool raised what the rule defines; the threshold is tunable and versioned | Is the rule tuned right? — a tuning question, addressed in the trial month |

The chain is about **provable honesty**, not **guaranteed correctness**. A broken chain is a defect. A
correct chain with wrong source data is a different problem, with a different owner.

---

## 6. The Audit Procedure (for a controller or auditor)

When you want to believe a number, do this:

1. **Pick the number** on the pack or screen.
2. **Drill it.** Confirm the transactions sum to it exactly. If they do not, stop — the chain is broken.
3. **Pick a transaction.** Note the source file, batch, and row.
4. **Open Import History.** Find the batch. Confirm the file name, checksum, row counts, balance result, and DQ score.
5. **Open the validation report.** Confirm the checks that ran and their results. Confirm the file was balanced (or reconciled within tolerance) before commit.
6. **Open the archived file.** Confirm the checksum matches the batch record.
7. **Ask the source question.** If the number still looks wrong, the question is now "is the source data right?" — and that is a question for the ERP, the export, and the person who exported it, not for this tool.

A number that passes steps 1–6 is a number the tool is honest about. Whether it is the right number is the
next question, and the tool has been honest about where to ask it.

---

## 7. The Limits (stated honestly)

- **The tool does not audit the source system.** It reads exports. If the export is wrong, the tool's output
  is wrong in the same way, and the tool's checks may or may not catch it.
- **The tool does not certify numbers.** It flags patterns worth a human look. The advisory disclaimer appears
  in the app, the packs, and the client pack.
- **The tool does not replace professional judgement.** It is an analysis aid. Every exception is a
  "potential exception — requires accounting review," never an "error" or "wrong entry."
- **The tool does not prove the export was exported correctly.** It records the checksum of the file it
  received. Whether the file was correctly exported from the source system is a source-system question.
- **The tool does not guarantee the analyst chose the right file.** It imports the file the analyst chose and
  reports on it honestly.

These limits are not hidden. They are the reason the tool's promises are honest. An auditor who understands
the limits is in a better position to use the tool's evidence than one who expects the tool to answer
questions it does not claim to answer.

---

## 8. Relationship to Other Docs

| Doc | Relationship |
|---|---|
| `29_CLIENT_REQUIREMENTS_PACK.md` | The client-facing version of the boundaries |
| `28_ACCEPTANCE_UAT_AND_GO_LIVE.md` | The acceptance and UAT mechanics that exercise the chain |
| `14_TESTING_QA_PLAN.md` | The tests that prove each link |
| `04_SOURCE_MAPPING_AND_IMPORT_SPEC.md` | The import checks that are Link 4 |
| `05_CALCULATION_SPEC.md` | The formulas that are Link 1's engine side |
| `06_EXCEPTION_RULES_CATALOG.md` | The rules that flag, not certify |
| `card_acceptance_standard.md` | The acceptance standard every link's proof must meet |
| `SPEC-08_ACCEPTANCE_STANDARD.md` | The project-level acceptance standard |
| `SPEC-07_PROVING_EVERY_ROW.md` | The rule that every spec row names its proof — including these chain links |

---

## 9. Living Note

This document is updated when a new link is added, when a link's proof changes, or when a limit is found to
be stated unclearly. The chain itself (5 links) is stable by construction — it is the shape of any number's
trace from screen to source. What changes is the proof at each link, as the tests and evidence mature.

# Wave 5 — REQ_CHECKLIST Downgrade Draft (subagent: req-downgrades) — READ-ONLY output

Target file: `audit/REQ_CHECKLIST.md` (lead auditor applies; this file is draft only).
No `docs/`, `sample-data/` or `audit/REQ_CHECKLIST.md` content was modified.

Rules applied:
- Requirement text (column 3) is **byte-identical** in every replacement — downgrades reflect unmet
  contract, never a weakened requirement (non-weakening rule).
- Every `file:line` / contract line cited below was re-read at source this wave (see §D).
- Only the **Audit Status** and **Evidence / Audit Pointer** cells change.

---

## A. Exact row replacements (old row → new row)

### A1. `REQ-KCK-11` — Kickoff §5 quality gate (line 29)

**Old:**

```
| `REQ-KCK-11` | Kickoff §5 (L109-124) | Kickoff Quality Gate (9 checks) self-audited with evidence before approval | `00_INDEX.md` §9; `14_TESTING_QA_PLAN.md` §15 | `VERIFIED` | Quality Gate 1 verified 9/9 green (installer runbook verified in `15`, `sample-data/` generated) |
```

**New:**

```
| `REQ-KCK-11` | Kickoff §5 (L109-124) | Kickoff Quality Gate (9 checks) self-audited with evidence before approval | `00_INDEX.md` §9; `14_TESTING_QA_PLAN.md` §15 | `GAP` | Wave-5 independent run: 8/9 — K2 (contract L112 "each forecast method") fails: locked actuals (`CALC-060`), 3-month average (`CALC-063`), manual override (`CALC-064`) are defined only (`05:284`, `05:287`, `05:288`) with no worked example in `05` §12 (F1–F14) or `07` §11 (`07:216`–`221` = F14a–F14d only; fixture register `05:602` covers F14a–c) — `14:680` `GATE-01-02` ✅ is false (`F-023`) |
```

> Rationale: `REQ-A1-16`/GATE-02 passed literal 12/12; the row that must move is the Kickoff gate row.
> Wave-5 gate verdict: `GATE-01` **FAIL 8/9** (`F-023`; contract L164 "each with a worked example in
> doc 07", contract L112 "and each forecast method").

---

### A2. `REQ-KCK-15` — exception rules / planted cases (line 33)

**Old:**

```
| `REQ-KCK-15` | Kickoff §9 (L168-177) | Exception engine: >=15 rules, ID, intent, logic, thresholds, severity, owner, FP mitigation, planted case | `06_EXCEPTION_RULES_CATALOG.md` §3, §4 | `VERIFIED` | 24 rules specified with all required fields |
```

**New:**

```
| `REQ-KCK-15` | Kickoff §9 (L168-177) | Exception engine: >=15 rules, ID, intent, logic, thresholds, severity, owner, FP mitigation, planted case | `06_EXCEPTION_RULES_CATALOG.md` §3, §4 | `CONTRADICTION` | 24 rules specified with all required fields, but the canonical planted case contradicts across docs: `05:524` (F13a golden fixture) verdict says `EXC-010` (cut-off/timing rule per `06:214`) while owner `06:738` maps F13a/P18 to `EXC-018` (material variance per `06:222`); `14:279` and `expected_exceptions.csv` P18 also say `EXC-018` — 4 of 5 sources agree (`F-020`) |
```

> Rationale: the assignment said "add caveat" — the caveat is now in the evidence cell, **and** the
> status moves to `CONTRADICTION` because the checklist's own definition ("Target deliverable
> contradicts another document") fits exactly: `06` (target) and `05` contradict on a money fact, and
> `F-020` is an open BLOCKER. Requirement text untouched. If the lead prefers the literal
> "caveat-only" reading, keep `VERIFIED` with this same evidence cell — but do not drop the caveat.

---

### A3. `REQ-A3-05` — four prompt texts with worked examples (line 98)

**Old:**

```
| `REQ-A3-05` | Addon 3 §D (L747-755) | AI feature depth: four full prompt texts with schemas and sample-data worked examples | `10_AI_INTEGRATION_SPEC.md` §5.1–§5.4 | `VERIFIED` | PROMPT-01 to PROMPT-04 complete with schemas and examples |
```

**New:**

```
| `REQ-A3-05` | Addon 3 §D (L747-755) | AI feature depth: four full prompt texts with schemas and sample-data worked examples | `10_AI_INTEGRATION_SPEC.md` §5.1–§5.4 | `GAP` | Texts and schemas present, but contract L749/L807 require worked example **input/output** on sample data: P2/P3/P4 are output-only (`10:487`, `10:634`, `10:747` — no input payload anywhere in §5); P1's input (`10:323`–`326`) is internally impossible — YTD actual ₹61,80,000 < Sep MTD ₹1,05,40,000 (both measures) — and `10:336` driver cites prior-month budget data the payload lacks (`F-024`, `F-028`); `14:729` `GATE-04-03` ✅ is false |
```

---

### A4. `REQ-A3-08` — acceptance / UAT / go-live (line 101)

**Old:**

```
| `REQ-A3-08` | Addon 3 §G (L775-784) | Acceptance, UAT & go-live (project DoD, UAT mechanics, defect severities S1–S4, 22-item go-live checklist) | `28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §2, §5, §6 | `VERIFIED` | DoD, defect severities, 6 UAT scripts, go-live checklist complete |
```

**New:**

```
| `REQ-A3-08` | Addon 3 §G (L775-784) | Acceptance, UAT & go-live (project DoD, UAT mechanics, defect severities S1–S4, 22-item go-live checklist) | `28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §2, §5, §6 | `GAP` | DoD, S1–S4, 6 UAT scripts and the 22-item checklist are present, but the mandated UAT entry criterion "entry = features demoed" (contract L778, required present by L815) is missing from `28` §5 (`28:142`–`173`; §5.1 table has no entry row; word "entry" occurs only at `28:81`, `:82`, `:239`, `:241`, all unrelated); additionally `28:46` cites a non-existent §5.5 exit record (§5 ends at §5.3) — `F-025` |
```

---

### A5. `REQ-A3-11` — Addon 3 §J quality gate (line 104)

**Old:**

```
| `REQ-A3-11` | Addon 3 §J (L803-819) | Phase 0 quality gate deltas (12 checks) | `00_INDEX.md` §9 (`GATE-04`); `14` §15 | `VERIFIED` | Quality Gate 4 verified 12/12 green (`GATE-04-02` and `GATE-04-07` green post-data generation) |
```

**New:**

```
| `REQ-A3-11` | Addon 3 §J (L803-819) | Phase 0 quality gate deltas (12 checks) | `00_INDEX.md` §9 (`GATE-04`); `14` §15 | `GAP` | Wave-5 independent gate run: 10/12 — A3J-3 (`GATE-04-03`, contract L807: prompt worked-example inputs missing, `F-024`) and A3J-11 (`GATE-04-11`, contract L815: UAT entry criterion missing, `F-025`) fail; `14:729` and `14:737` ✅ are false |
```

---

### A6. `REQ-A4-11` — edge-case matrix / message IDs (line 123)

**Old:**

```
| `REQ-A4-11` | Addon 4 §G.2 (L959-978) | Edge-case data matrix (13 rows with canonical behavior and error message IDs) | `02_FUNCTIONAL_SPEC.md` §16; `14_TESTING_QA_PLAN.md` §5.2 | `VERIFIED` | 13 edge cases catalogued with slugs and error messages |
```

**New:**

```
| `REQ-A4-11` | Addon 4 §G.2 (L959-978) | Edge-case data matrix (13 rows with canonical behavior and error message IDs) | `02_FUNCTIONAL_SPEC.md` §16; `14_TESTING_QA_PLAN.md` §5.2 | `CONTRADICTION` | The two mandated matrices disagree on message IDs: `02` §16 (13 rows `E1`–`E13`, `02:1258`–`1270`) vs `14` §6.2 (16 rows, `14:313`–`328`) — rows 1/2/4/11/13 carry different slugs, rows 14–16 have no `02` counterpart, and 8 slugs used in `14` (`import.budgetCoverageGap`, `import.mappingIncomplete`, `import.parenthesesUnresolved`, `import.numberUnparsed`, `import.signRuleApplied`, `import.encryptedFile`, `import.fileLocked`, `import.formulaNoCachedValue`) exist nowhere in `02`; contract L1014 requires the matrix "with message IDs" in both docs — `14:753` `GATE-05-10` ✅ is false (`F-022`) |
```

---

### A7. `REQ-A4-12` — sample-data watermark / project type (line 124)

**Old:**

```
| `REQ-A4-12` | Addon 4 §H (L979-986) | Sample-data integrity: watermark, project_type flag, no interleave with real data, non-delivery rule | `14_TESTING_QA_PLAN.md` §4; `16` §10.3 | `VERIFIED` | Spec rules defined; physical dataset generation pending |
```

**New:**

```
| `REQ-A4-12` | Addon 4 §H (L979-986) | Sample-data integrity: watermark, project_type flag, no interleave with real data, non-delivery rule | `14_TESTING_QA_PLAN.md` §4; `16` §10.3 | `GAP` | Spec rules defined, but the generated corpus violates contract L981/L1015/L1029: `sample-data/expected_exceptions.csv` has no `Watermark` column and no watermark string anywhere; the project-type flag exists only in `d365_gl_actuals.csv` (column `ProjectType`, values `sample`) and is absent from `bank_ledger_actuals.csv`, `budget_fy26.csv`, `payroll_procurement_actuals.csv` (no CSV uses the literal name `project_type`) — 1 of 5 CSVs carries it (`F-034`; Wave-4 "present in all CSVs" log claim corrected per `F-033`) |
```

---

### A8. `REQ-A4-15` — Addon 4 §K quality gate (line 127)

> Added by parity with A1/A5 (not in the original list): Wave 5 verdict is `GATE-05` **FAIL 12/13**,
> so the GATE-05 row must move just as the GATE-01 and GATE-04 rows do. `REQ-A2-15` (GATE-03) and
> `REQ-A1-16` (GATE-02) pass in Wave 5 and stay unchanged.

**Old:**

```
| `REQ-A4-15` | Addon 4 §K (L1003-1020) | Phase 0 quality gate deltas (13 checks) | `00_INDEX.md` §9 (`GATE-05`); `14` §15 | `VERIFIED` | Quality Gate 5 verified 13/13 green (`GATE-05-02` green post-header cleanup) |
```

**New:**

```
| `REQ-A4-15` | Addon 4 §K (L1003-1020) | Phase 0 quality gate deltas (13 checks) | `00_INDEX.md` §9 (`GATE-05`); `14` §15 | `GAP` | Wave-5 independent gate run: 12/13 — K10 (`GATE-05-10`, contract L1014) fails: `02` §16 vs `14` §6.2 message-ID contradictions (`F-022`); `14:753` ✅ is false |
```

---

### A9. `REQ-A4-16` — Phase 0 completion workflow / PHASE0_SUMMARY readiness (line 128)

**Old:**

```
| `REQ-A4-16` | Addon 4 §L (L1021-1035) | Phase 0 completion workflow: repo skeleton, docs 00–29, sample-data build, all 5 gates green, approval before code | `PHASE0_SUMMARY.md`; `00_INDEX.md` | `VERIFIED` | Workflow complete: skeleton active, 31 docs complete, sample data generated, all 6 gates green |
```

**New:**

```
| `REQ-A4-16` | Addon 4 §L (L1021-1035) | Phase 0 completion workflow: repo skeleton, docs 00–29, sample-data build, all 5 gates green, approval before code | `PHASE0_SUMMARY.md`; `00_INDEX.md` | `GAP` | Artifacts exist (skeleton, 31 docs, sample data) but the green claim is false: Wave-5 independent run = 62/66 with 3 of 6 gates FAIL — `GATE-01` K2 (`F-023`), `GATE-04` A3J-3 + A3J-11 (`F-024`, `F-025`), `GATE-05` K10 (`F-022`); `PHASE0_SUMMARY:108` "66 ✅ / 0 ⬜ — 100% PASS" and `PHASE0_SUMMARY:12` readiness overstated (`F-029`), and the page carries no `F-015` Addon-5-source caveat |
```

---

### A10. `REQ-A5-07` — Coverage Matrix rows (line 144)

**Old:**

```
| `REQ-A5-07` | Addon 5 (Audit §2.2, provisional) | Coverage Matrix covers all six contract documents with all rows verified | `00_INDEX.md` §4 | `VERIFIED` | Addon Coverage Matrix covers all 6 contract docs (85 expanded rows over 72 sections); 100% verified `INTEGRATED` |
```

**New:**

```
| `REQ-A5-07` | Addon 5 (Audit §2.2, provisional) | Coverage Matrix covers all six contract documents with all rows verified | `00_INDEX.md` §4 | `GAP` | All 6 contract docs covered and every row `INTEGRATED`, but the count claim is false: actual 86 data rows (15+17+17+17+12+8) — `00:109` claims "85 expanded rows" and `00:136` §4.2 header claims "16 rows" while the table holds 17 (`00:140`–`156`, `A1-C` split into `C.1`/`C.2`); Addon 2 §A.3 gate rule cannot be checked against a false denominator (`F-027`, reopens `F-016`) |
```

---

## B. Wave 5 status-change log

| # | Req ID | Old → New | One-line rationale | Finding |
|---|---|---|---|---|
| 1 | `REQ-KCK-11` | `VERIFIED` → `GAP` | Kickoff quality gate independently re-run at 8/9; K2 "each forecast method" has no worked example for locked actuals / 3-month average / manual override | `F-023` |
| 2 | `REQ-KCK-15` | `VERIFIED` → `CONTRADICTION` | Canonical planted case F13a carries two different rule IDs across `05:524` (`EXC-010`) and owner `06:738` (`EXC-018`) — caveat added to evidence as instructed | `F-020` |
| 3 | `REQ-A3-05` | `VERIFIED` → `GAP` | Contract L749/L807 demand worked-example input/output; P2–P4 are output-only and P1's input is arithmetically impossible | `F-024`, `F-028` |
| 4 | `REQ-A3-08` | `VERIFIED` → `GAP` | UAT entry criterion ("entry = features demoed") absent from `28` §5; `28:46` cites non-existent §5.5 | `F-025` |
| 5 | `REQ-A3-11` | `VERIFIED` → `GAP` | Addon 3 gate independently re-run at 10/12 (A3J-3 prompt inputs, A3J-11 UAT entry) | `F-024`, `F-025` |
| 6 | `REQ-A4-11` | `VERIFIED` → `CONTRADICTION` | `02` §16 (13 rows) and `14` §6.2 (16 rows) contradict on message IDs; 8 `14`-slugs absent from `02`; `GATE-05-10` ✅ false | `F-022` |
| 7 | `REQ-A4-12` | `VERIFIED` → `GAP` | Watermark missing from `expected_exceptions.csv`; `ProjectType` flag present in only 1 of 5 CSVs vs contract L981/L1015/L1029 | `F-034` |
| 8 | `REQ-A4-15` | `VERIFIED` → `GAP` | Addon 4 gate independently re-run at 12/13 (K10 fails on the same matrix contradictions) | `F-022` |
| 9 | `REQ-A4-16` | `VERIFIED` → `GAP` | "All 6 gates green" / "66 ✅ — 100% PASS" is false: 62/66, 3 of 6 gates FAIL, no `F-015` caveat on the approval page | `F-029` |
| 10 | `REQ-A5-07` | `VERIFIED` → `GAP` | Coverage Matrix count claim 85 is wrong (actual 86; §4.2 header 16 vs 17 rows) — gate denominator false | `F-027` (reopens `F-016`) |

**Considered, deliberately NOT changed (for the lead's record):**

- `REQ-A1-16` (GATE-02) — unchanged. GATE-02 **passes literal 12/12**: contract L474 requires only that
  the injection *test case* exists in `14` (it does, `14:700`). `F-026`'s fixture-existence claims
  (`02:1012`, `10:815`, `13:431`, `13:527`, `14:525`) are recorded as a BLOCKER finding and the
  strict-vs-literal reading is escalated to the owner; if the owner adopts the strict reading,
  `GATE-02-08` flips and this row becomes `GAP`.
- `REQ-A2-15` (GATE-03) — unchanged. Wave-5 verdict: PASS 12/12; the matrix row-count defect is
  charged against `REQ-A5-07` / `F-027`, not against GATE-03.
- `REQ-A5-04` (provisional `GATE-05B` 8/8) — unchanged. No `GATE-05B` check failed in Wave 5; the
  `F-015` provisional-source caveat already sits in the §6 section preamble.
- **Flagged for lead decision (not drafted):** `REQ-KCK-14` evidence says "Formally specified with
  formulas and golden fixtures" while two open BLOCKERs sit in those very fixtures (`05:524` rule-ID
  → `F-020`; `05:419` 6dp truncation → `F-021`). Consider the same caveat treatment once the lead
  rules on A2.

---

## C. What was NOT touched

`audit/REQ_CHECKLIST.md` (read-only), `docs/`, `sample-data/`, `evidence/`. This draft contains no
requirement-text edits — every replacement preserves columns 1–4 verbatim.

## D. Verification record (every cite re-read at source this wave)

- **Contract** (`project prompt/# FP&A MONTH-END COPILOT — AGENTIC.txt`): L112 (K2 "each forecast
  method") ✓, L113 + L172 (planted sample case per rule) ✓, L164 (five methods, worked example in
  `07`) ✓, L474 (Addon 1 §O item 8, injection test case in `14`) ✓, L749 (input/output using sample
  data) ✓, L778 (`entry = features demoed`) ✓, L807 ✓, L815 ✓, L981/L1015/L1029 (watermark +
  project-type) ✓, L1014 (edge-case matrix with message IDs) ✓.
- **Docs:** `05:284`/`:287`/`:288` (CALC-060/063/064 defined) ✓, `05:524` (`EXC-010`) ✓, `05:602`
  (fixture register F14a–c) ✓, `05` §12 heading line 340 ✓, `06:738` (`EXC-018` = F13a/P18) ✓,
  `06:214`/`:222` ✓, `07:208`–`221` (no example for the three methods) ✓, `10:323`–`326` (P1 input,
  YTD < Sep) ✓, `10:336` ✓, `10:487`/`10:634`/`10:747` (output-only) ✓, `10:638`–`643` (two-timing-
  issues vs count 1) ✓, `14:680`/`:700`/`:729`/`:737`/`:753` (gate rows ✅) ✓, `14:307`–`328` (16
  rows) ✓, `02:1251`–`1270` (13 rows `E1`–`E13`) ✓, `28:46` (§5.5) ✓, `28:142`–`173` + "entry" grep
  (only `:81`, `:82`, `:239`, `:241`) ✓, `00:109` ("85 expanded rows") ✓, `00:136` + `:140`–`:156`
  (17 data rows) ✓, `PHASE0_SUMMARY:12`, `:96`, `:100`–`:108` ("66 ✅ / 0 ⬜") ✓.
- **Sample-data:** headers of all 5 CSVs read — `expected_exceptions.csv` no `Watermark`; only
  `d365_gl_actuals.csv` carries `ProjectType`; the other three carry `Watermark` only ✓.
- **Checklist rows:** `audit/REQ_CHECKLIST.md` lines 29, 33, 62, 98, 101, 104, 123, 124, 127, 128,
  144 read verbatim; old rows above are byte-exact copies ✓.

## E. Summary (10 status changes)

1. `REQ-KCK-11` — `VERIFIED` → **`GAP`** (F-023: Kickoff gate 8/9, K2 forecast-method examples missing)
2. `REQ-KCK-15` — `VERIFIED` → **`CONTRADICTION`** (F-020: F13a `EXC-010` in `05:524` vs `EXC-018` in `06:738`)
3. `REQ-A3-05` — `VERIFIED` → **`GAP`** (F-024/F-028: P2–P4 no input payloads; P1 input impossible)
4. `REQ-A3-08` — `VERIFIED` → **`GAP`** (F-025: UAT entry criterion missing; `28:46` dead §5.5 pointer)
5. `REQ-A3-11` — `VERIFIED` → **`GAP`** (F-024/F-025: `GATE-04` independent run 10/12)
6. `REQ-A4-11` — `VERIFIED` → **`CONTRADICTION`** (F-022: `02` §16 vs `14` §6.2 message-ID conflicts)
7. `REQ-A4-12` — `VERIFIED` → **`GAP`** (F-034: watermark absent in `expected_exceptions.csv`; `ProjectType` in 1 of 5 CSVs)
8. `REQ-A4-15` — `VERIFIED` → **`GAP`** (F-022: `GATE-05` independent run 12/13, K10 fails)
9. `REQ-A4-16` — `VERIFIED` → **`GAP`** (F-029: 62/66, 3 of 6 gates FAIL, approval page overstates readiness)
10. `REQ-A5-07` — `VERIFIED` → **`GAP`** (F-027: matrix actual 86 rows vs claimed 85; §4.2 header 16 vs 17)

# Scratch — Wave 5 A4 Sampling Record (draft for `audit/SAMPLING.md`)

> Status: DRAFT assembled by the A4 subagent. Intended destination: append §5 to `audit/SAMPLING.md`
> and replace the stale final paragraph of §4 (exact old → new text in Part B below).
> All file:line references and all fixture counts in this draft were re-measured/re-opened by the
> subagent during Wave 5 (2026-10-01). Nothing in `docs/`, `sample-data/` or `audit/SAMPLING.md`
> was modified by this draft.

---

## PART A — Proposed append to `audit/SAMPLING.md`: new section 5

## 5. Wave 5 A4 Re-Verification (Traceability Chain)

**Method:** subagent-run re-check of 4 stratified FRs across money/import/AI/export areas, chain
verified hop-by-hop as `FR (20) → spec section (02/05/06/10/11) → screen (08) → endpoint (26) →
test (14)`; the lead auditor then personally spot-checked **2 complete chains end-to-end** (hop-by-hop
evidence in §5.2). Every citation below was opened in the file, not inherited from a prior wave.

**FRs re-checked (all confirmed present in `docs/20_REQUIREMENTS_TRACEABILITY.md`):**

| Area | FR ID | FR row in `20` | Spec cells | Screen | Endpoint | Tests |
|---|---|---|---|---|---|---|
| Money-calculation | `FR-BVA-001` | `20:348` | `02` §7; `05` §4; `08` §9.2 | `SCR-015` | `GET /analysis/bva` | `TST-BVA-01/02`, `TST-PRF-03`, `TST-UAT-02` |
| Import / AI | `FR-IMP-008` | `20:319` | `02` §6; `10` §5.2/§11; `08` §7.4 | `SCR-008` | `POST`+`GET /ai/mapping-suggestions` | `TST-AI-13`, `TST-AI-14` |
| Exceptions / rule run | `FR-EXC-001` | `20:369` | `02` §8; `06` §2; `08` §14 | `SCR-014`, `SCR-023` | `POST /rules/run` | `TST-RUL-25`, `TST-PRF-07`, `TST-UI-13` |
| Export | `FR-XL-001` | `20:408` | `02` §10; `11` §2/§4 | `SCR-029` | `POST /packs/excel` | `TST-XL-01`, `TST-XL-02`, `TST-WIN-10` |

### 5.1 Result

- **Chains complete: 4/4.** Every hop resolves to a real section/screen/endpoint/test in the cited
  document. **0 implementer guesses** — no hop required an unstated product decision.
- **5 non-blocking link recommendations**, recorded under **`F-036`** (they map onto the existing
  `F-036` item letters; each was re-verified this wave, see §5.3):
  1. `docs/04_SOURCE_MAPPING_AND_IMPORT_SPEC.md:343` cites "`05` §tolerance" → owner is **`05` §13**
     (`05_CALCULATION_SPEC.md:574` "## 13. Tolerance policy (binding — Addon 4 §G.1)") — `F-036(a)`.
  2. `docs/03_DATA_DICTIONARY.md:41` cites "Addon 4 §G.1" (external contract) → in-set owner is
     **`05` §13** (`05:574`) — `F-036(b)`.
  3. `docs/20_REQUIREMENTS_TRACEABILITY.md:71` cites "`16` §14" for never-cut semantics → actual owner
     is **`16` §9.2** (`16_ROADMAP_PHASES.md:536` "The never-cut list…"); `16` §14 is "Change control
     and cross-document obligations" (`16:635`) — `F-036(d)`.
  4. `docs/07_FORECAST_METHODS_SPEC.md:195` labels its guarantees "never-cut list items" with no owner
     pointer → add canonical pointer **`02` §3.3 / `16` §9.2** (`16:536` states "verbatim from `02` §3.3")
     — `F-036(e)`.
  5. `docs/00_INDEX.md:367` points to "`18_...OPEN_QUESTIONS.md` §Open" (no such section) → real
     register is **`18` §4** (`18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md:235` "The open-question
     register (`OQ-`)") — `F-036(f)`.

  All five are **non-blocking**: they repair pointers/wording, weaken no checklist item, and require
  no product decision.

### 5.2 Personal end-to-end spot-checks (lead auditor, hop-by-hop evidence)

**Chain 1 — `FR-BVA-001` (money-calculation): COMPLETE, 0 guesses**

| # | Hop | Evidence (file:line → content) |
|---|---|---|
| 1 | FR row in `20` (with TST link) | `docs/20_REQUIREMENTS_TRACEABILITY.md:348` — `FR-BVA-001` \| "BvA matrix at the lowest shared grain" \| P0 \| cells `02` §7; `05` §4; `08` §9.2 \| `SCR-015` \| `GET /analysis/bva` \| `TST-BVA-01`, `TST-BVA-02`, `TST-PRF-03`, `TST-UAT-02` \| Spec'd |
| 2 | Spec section | `docs/02_FUNCTIONAL_SPEC.md:494` — "## 7. `FR-BVA` — Budget vs actual analysis (16 FRs)"; `docs/05_CALCULATION_SPEC.md:98` — "## 4. Variance, variance % and favour*ability* (CALC-010 … CALC-013)"; screen spec `docs/08_UI_UX_SPEC.md:416` — "### 9.2 BvA matrix (`SCR-015`)" |
| 3 | Screen ID in `08` | `docs/08_UI_UX_SPEC.md:127` — registry row `SCR-015` "Analyze — BvA matrix" lists `FR-BVA-001`; wireframe section at `08:416`; screen index also at `20:552` |
| 4 | Endpoint in `26` | `docs/26_API_CONTRACT.md:301` — `GET /analysis/bva` row cites `SCR-015` and `FR-BVA-001`; reverse index `26:783` — `GET /analysis/bva` → `FR-BVA-001` … `SCR-015`, `SCR-022` |
| 5 | Test in `14` | `docs/14_TESTING_QA_PLAN.md:192` — `TST-BVA-01` (total row = Σ visible rows); `:193` — `TST-BVA-02` (100% drill traceability); `:81` — `TST-PRF-03` (NFR-003 ≤ 2 s, ID rule `:399` `TST-PRF-01…16` ↔ `NFR-001…016`); `:593` — `TST-UAT-02` (tie-out worksheet) |

**Chain 2 — `FR-XL-001` (export): COMPLETE, 0 guesses**

| # | Hop | Evidence (file:line → content) |
|---|---|---|
| 1 | FR row in `20` (with TST link) | `docs/20_REQUIREMENTS_TRACEABILITY.md:408` — `FR-XL-001` \| "Generate the Excel pack" \| P0 \| cells `02` §10; `11` §2/§4 \| `SCR-029` \| `POST /packs/excel` \| `TST-XL-01`, `TST-XL-02`, `TST-WIN-10` \| Spec'd |
| 2 | Spec section | `docs/02_FUNCTIONAL_SPEC.md:826` — "## 10. `FR-XL` — Excel output pack (9 FRs)"; `docs/11_EXCEL_OUTPUT_SPEC.md:39` — "## 2. The workbook family"; `docs/11_EXCEL_OUTPUT_SPEC.md:453` — "## 4. The month-end pack, sheet by sheet" |
| 3 | Screen ID in `08` | `docs/08_UI_UX_SPEC.md:141` — registry row `SCR-029` "Reports — Generate pack" lists `FR-XL-001`; wireframe section `08:553` "### 11.1 Generate pack (`SCR-029`)"; screen index also at `20:566` |
| 4 | Endpoint in `26` | `docs/26_API_CONTRACT.md:345` — `POST /packs/excel` row cites `SCR-029` and `FR-XL-001`; reverse index `26:806` — `POST /packs/excel` → `FR-XL-001` … `SCR-029` |
| 5 | Test in `14` | `docs/14_TESTING_QA_PLAN.md:127` — inventory row `TST-XL-01…26` (26 tests, "Reserved and fully specified by `11`"); individual definitions `docs/11_EXCEL_OUTPUT_SPEC.md:1284` ("## 13. Test contract"), `:1288` (`TST-XL-01`), `:1289` (`TST-XL-02`); `docs/14_TESTING_QA_PLAN.md:481` — `TST-WIN-10` (Office opens every artefact without a repair prompt) |

**Chains 3–4 (subagent-checked, key hops re-opened during this spot-check):**

- `FR-EXC-001` — FR row `20:369`; spec `02:627` ("## 8. `FR-EXC` …"), `06:45` ("## 2. The engine
  model"); screen `08:126` (`SCR-014` registry, lists `FR-EXC-001`) + wireframe `08:380` ("## 8. Check
  (`SCR-014`)"); endpoint `26:286` (`POST /rules/run` cites `FR-EXC-001`, `SCR-014`) + reverse index
  `26:775`; tests `14:171` (`TST-RUL-25`), `14:85` (`TST-PRF-07`), `14:503` (`TST-UI-13`) — **COMPLETE**.
- `FR-IMP-008` — FR row `20:319`; spec `02:251` ("## 6. `FR-IMP` …"), `10:348` ("### 5.2 `PROMPT-02` —
  Mapping suggestion with evidence"), `10:966` ("## 11. Keyless mode and the rule-based fallback"),
  `08:296` ("### 7.4 Step 4 — Map columns (`SCR-008`)"); screen `08:120` (registry, lists `FR-IMP-008`);
  endpoints `26:366` + `26:367` (`POST`/`GET /ai/mapping-suggestions` both cite `FR-IMP-008`, `SCR-008`)
  + reverse index `26:820`/`26:821`; tests inventory `14:126` (`TST-AI-01…14`, "Reserved and fully
  specified by `10`") + definitions `10:1045` (`TST-AI-13` mapping queue), `10:1046` (`TST-AI-14`
  labelling) — **COMPLETE**.

### 5.3 The 5 link recommendations re-verified (recorded under `F-036`)

| # | Cited location (re-opened) | Defect as found | Recommended target (re-opened) | `F-036` item |
|---|---|---|---|---|
| 1 | `04:343` | "…exact … per file, per entity… (`05` §tolerance)" — `05` has no §tolerance | `05:574` §13 "Tolerance policy" | (a) |
| 2 | `03:41` | "…no epsilon (Addon 4 §G.1)" — points outside the set | `05:574` §13 (heading itself binds Addon 4 §G.1) | (b) |
| 3 | `20:71` | "never-cut semantics in `02` §3 and `16` §14" | `16:536` §9.2 "The never-cut list" (`16:635` = §14, unrelated) | (d) |
| 4 | `07:195` | "## 10. Forecast integrity guarantees (never-cut list items)" — label, no owner pointer | add `02` §3.3 / `16:536` §9.2 pointer | (e) |
| 5 | `00:367` | "Tracked in `18_...OPEN_QUESTIONS.md` §Open" — no §Open exists | `18:235` §4 "The open-question register" | (f) |

### 5.4 Verdict

**A4 PASS (0 guesses) — Wave 5.** 4/4 chains complete; 5 non-blocking link recommendations filed
under `F-036` (items a, b, d, e, f — pointer/wording fixes only).

> **Caveat:** A4 passing does **not** lift the overall **NOT READY** verdict for Phase 0 — the overall
> verdict remains blocked by `F-015` (Addon 5 contract absent / escalated) and by `F-020`–`F-026`,
> `F-029` (owned by the other Wave-5 subagents). A4 speaks only to implementability/traceability.

**Chain note (observation, not counted among the 5 recommendations):** `20:369` cites "`08` §14`" as an
owning screen section for `FR-EXC-001`, but `08` §14 is "Centralized conditional formatting" (`08:620`);
the `SCR-014` wireframe lives at `08` §8 (`08:380`). The chain still completes (spec hop is carried by
`02` §8 / `06` §2, screen hop by the `08:126` registry + `08:380` wireframe); flagged for lead-auditor
judgement — likely folds into `F-036` or is intentional (severity formatting for rule-run output).

---

## PART B — Replacement of the stale final paragraph of §4 (old → new)

**Location:** `audit/SAMPLING.md`, `## 4. Sampling Conclusion`, final sentence (currently line 118).

**OLD (stale — factually false as of Wave 4):**

```markdown
However, because underlying test fixtures (`sample-data/`, `expected_exceptions.csv`, `scripts/`) are not physically created on disk, execution of these tests is currently blocked.
```

**NEW (proposed):**

```markdown
Execution status (Wave 5 re-measurement): the test fixtures are now physically on disk — `sample-data/` contains `d365_gl_actuals.csv` (10,037 data rows), `bank_ledger_actuals.csv` (499), `payroll_procurement_actuals.csv` (399), `budget_fy26.csv` (1,980), `expected_exceptions.csv` (40 rows), `malformed/` (16 files) and `templates/` (3 xlsx), all counts re-measured with Python line counts this wave. Execution of these tests is therefore **no longer blocked by missing fixtures**. One gap remains and it is explicitly *not* a Phase-0 blocker: `scripts/` still contains only `.gitkeep` — no test harness exists yet; building the harness is Phase 1 work.
```

### Fixture counts actually measured this wave (Python line counts, `C:\Python314\python.exe`)

| Artifact | Total lines (incl. header) | Data rows / count |
|---|---|---|
| `sample-data/d365_gl_actuals.csv` | 10,038 | **10,037** |
| `sample-data/bank_ledger_actuals.csv` | 500 | **499** |
| `sample-data/payroll_procurement_actuals.csv` | 400 | **399** |
| `sample-data/budget_fy26.csv` | 1,981 | **1,980** |
| `sample-data/expected_exceptions.csv` | 41 | **40** |
| `sample-data/malformed/` | — | **16 files** (excl. `.gitkeep`) |
| `sample-data/templates/` | — | **3 xlsx** (excl. `.gitkeep`) |
| `scripts/` | — | **only `.gitkeep`** (no harness) |

---

## PART C — Verdict line (for `audit/SAMPLING.md` §5 close / Wave-5 roll-up)

```markdown
**Verdict: A4 PASS (0 guesses) — Wave 5.** 4/4 traceability chains complete (FR-BVA-001, FR-IMP-008, FR-EXC-001, FR-XL-001), 5 non-blocking link recommendations recorded under F-036 (a, b, d, e, f). Caveat: A4 passing does not lift the overall NOT READY verdict, which remains blocked by F-015 / F-020–F-026 / F-029.
```

# IMPLEMENTABILITY SAMPLING AUDIT (THE VIBE-CODING TEST)

_Pass A4: Independent evaluation of 8 stratified requirements simulating a fresh coding agent implementing with zero guessing and zero improvised product decisions._

---

## 1. Sampling Strategy

Eight Functional Requirements (FRs) were selected across all critical functional dimensions:
- **Money-calculation (2):** `FR-BVA-001` (BvA matrix at lowest shared grain), `FR-BVA-003` (Variance, variance % and favourability)
- **Import/data (2):** `FR-IMP-001` (Multi-format import entry), `FR-IMP-020` (Atomic staged commit)
- **UI/workflow (2):** `FR-EXC-002` (Exception register), `FR-PRJ-001` (Home screen dashboard)
- **Export/reporting (1):** `FR-XL-001` (Board-ready Excel pack generation)
- **AI feature (1):** `FR-AI-001` (Optional, off-by-default, keyless-capable AI)

---

## 2. Full Traceability Chain Verification

| FR ID | Priority | Owning Spec Sections | Screen ID (`08`) | HTTP API Route (`26`) | Test IDs (`14`) | Chain Status |
|---|---|---|---|---|---|---|
| `FR-BVA-001` | P0 | `02` §7, `05` §4, `08` §9.2 | `SCR-015` | `GET /analysis/bva` | `TST-BVA-01`, `TST-BVA-02`, `TST-PRF-03`, `TST-UAT-02` | **COMPLETE** |
| `FR-BVA-003` | P0 | `02` §7, `05` §4.2 | `SCR-015` | `GET /analysis/bva` | `TST-CALC-18`, `TST-CALC-19`, `TST-CALC-20` | **COMPLETE** |
| `FR-IMP-001` | P0 | `02` §6, `04` §3, `08` §7.1 | `SCR-005` | `POST /imports/pre-scan` | `TST-UI-01`, `TST-E2E-01` | **COMPLETE** |
| `FR-IMP-020` | P0 | `02` §6, `04` §15 | `SCR-010` | `POST /imports/{batch}/commit` | `TST-IMP-35`, `TST-WIN-09` | **COMPLETE** |
| `FR-EXC-002` | P0 | `02` §8, `08` §10.1 | `SCR-023` | `GET /exceptions` | `TST-EXC-07`, `TST-EXC-09` | **COMPLETE** |
| `FR-PRJ-001` | P0 | `02` §5, `08` §5.3 | `SCR-001` | `GET /projects/{id}`, `GET /checks` | `TST-UI-01`, `TST-E2E-01` | **COMPLETE** |
| `FR-XL-001` | P0 | `02` §10, `11` §2, §4 | `SCR-029` | `POST /packs/excel` | `TST-XL-01`, `TST-XL-02`, `TST-WIN-10` | **COMPLETE** |
| `FR-AI-001` | P0 | `02` §12, `10` §1 | `SCR-038` | `GET /settings` | `TST-AI-10`, `TST-AI-11` | **COMPLETE** |

---

## 3. Implementability & Zero-Guess Assessment

### Sample 1: `FR-BVA-001` (BvA Matrix at Lowest Shared Grain)
- **Specification Text:**
  > "The primary matrix shows Actual, Budget, Variance (amount and %), and favourability at the lowest grain where both sides exist (typically period × entity × cost centre × GL account). Rows and columns are expandable across the account hierarchy and cost-centre tree; every cell is drillable."
- **Edge Cases Defined:** Budget exists only at GL/month level while actuals are transaction-level → UI must not imply transaction-level budget matching (`FR-BVA-013`); cell with budget but no actual shows explicitly as "no actuals loaded", not as zero.
- **Acceptance Criteria:** Every matrix total equals the sum of its drilled rows exactly (no rounding drift, per `05` §rounding).
- **Implementer Guess Check:** Zero open questions. The star schema (`03`), aggregation formulas (`05`), and wireframe (`08` `SCR-015`) provide exact column layouts, rollups, and drill paths.
- **Verdict:** **PASS (Zero Guesses)**

---

### Sample 2: `FR-BVA-003` (Variance, Variance % and Favourability)
- **Specification Text:**
  > "Variance = Actual − Budget (canonical sign convention, `05`); variance % computed per the documented zero-budget rule; favourability is direction-aware by statement-line type (revenue/expense/memo). Favourability is shown as colour plus a +/- sign or a Fav/Adv label so it survives black-and-white printing and colour blindness."
- **Edge Cases Defined:** Zero budget, negative budget, zero actuals, memo lines (neutral). All mapped to `CALC-010`–`013` and Golden Fixtures F1–F5 in `05`.
- **Acceptance Criteria:** Must match `05` golden fixtures exactly; black-and-white accessible text label required.
- **Implementer Guess Check:** Fully deterministic; zero ambiguity.
- **Verdict:** **PASS (Zero Guesses)**

---

### Sample 3: `FR-IMP-001` (Import Entry: Drag-and-Drop and File Picker)
- **Specification Text:**
  > "Files can be dropped anywhere on the Import screen (with a visible drop zone and drag-over state) or chosen via a file picker. Both paths converge on the same pipeline."
- **Edge Cases Defined:** Unsupported file extension, zero-byte file, folder dropped, multiple files dropped at once (queued sequentially with per-file status).
- **Acceptance Criteria:** Emits `ERR-IMP-001` on unsupported extension, `ERR-IMP-002` on empty file, displays staging progress modal.
- **Implementer Guess Check:** Detailed screen wireframe in `08` `SCR-005` and request payload in `26` `POST /imports/pre-scan`.
- **Verdict:** **PASS (Zero Guesses)**

---

### Sample 4: `FR-IMP-020` (Atomic Staged Commit)
- **Specification Text:**
  > "Rows are staged, fully validated, and only then committed in a single transaction; crash, cancel, power loss, or a bad file never leaves half-loaded data. Interrupted staging areas are detected on next launch and offered for discard or resume; the app states clearly that no batch was committed."
- **Edge Cases Defined:** SQLite/DuckDB lock conflict, application killed during write, user cancellation.
- **Acceptance Criteria:** Crash-during-import test in `14` leaves the project with either 0% or 100% of the batch committed.
- **Implementer Guess Check:** Database transaction semantics, staging tables, and rollback locks explicitly detailed in `09_TECHNICAL_ARCHITECTURE.md` §7 and `04` §15.
- **Verdict:** **PASS (Zero Guesses)**

---

### Sample 5: `FR-EXC-002` (Exception Register)
- **Specification Text:**
  > "A sortable, filterable register showing: rule ID and name (with severity), period, entity, subject (account/cost centre/vendor/voucher), amount at risk, owner, status, days open, first-seen and last-seen dates, evidence link, and notes count. Filters include severity, status, owner, rule, entity, period and aging bucket."
- **Edge Cases Defined:** Zero exceptions, 10,000+ exceptions (virtualized scrolling per `08`), exceptions with missing optional master data.
- **Acceptance Criteria:** Every raised exception visible with working drill path to subject rows; counts on screen match export counts.
- **Implementer Guess Check:** Register UI layout specified in `08` `SCR-023`; data fields defined in `03` `FactException`.
- **Verdict:** **PASS (Zero Guesses)**

---

### Sample 6: `FR-PRJ-001` (Home Screen Dashboard)
- **Specification Text:**
  > "Home shows: open/recent project, current period with status (Open/Closed), last import summary (file, batch, rows, balance result, when), a KPI strip for the current period, quick actions (Import / Check / Analyze / Generate pack), and health warnings (failed checks, stale derived results, low storage, pending quarantine rows)."
- **Edge Cases Defined:** No project open (offer sample, create, open recent); zero periods loaded; stale results banner.
- **Acceptance Criteria:** Every warning links directly to the screen that resolves it.
- **Implementer Guess Check:** Complete ASCII wireframe in `08` `SCR-001`; endpoints `GET /projects/{id}` and `GET /checks` in `26`.
- **Verdict:** **PASS (Zero Guesses)**

---

### Sample 7: `FR-XL-001` (Generate the Excel Pack)
- **Specification Text:**
  > "Generates one workbook from the current filter context containing: BvA summary, transaction detail (drill of the summary), exception register, forecast summary, import reconciliation, and audit-trail sheet. The sheet set matches `11` exactly, and any sheet omitted is omitted for a stated, documented reason."
- **Edge Cases Defined:** Openpyxl memory budget on large transactions (switches to streaming writer per `09` §10), missing forecast data (sheet omitted with note).
- **Acceptance Criteria:** Generated workbook opens in Excel with zero repair prompts; formats, frozen panes, filters, print areas, and disclaimer footer match `11` layout contract.
- **Implementer Guess Check:** `11_EXCEL_OUTPUT_SPEC.md` provides cell-by-cell coordinate maps, openpyxl formatting styles, and tab orders.
- **Verdict:** **PASS (Zero Guesses)**

---

### Sample 8: `FR-AI-001` (Optional, Off-by-Default, Keyless-Capable AI)
- **Specification Text:**
  > "AI is disabled until a key is configured. With no key, every AI surface still works using the deterministic rule-based narrative generated from the same driver data (FR-AI-013)."
- **Edge Cases Defined:** Network offline, invalid key, rate limit reached, malformed LLM response.
- **Acceptance Criteria:** Full sample-project walkthrough passes with AI never enabled; keyless fallback produces deterministic commentary.
- **Implementer Guess Check:** Rule-based template fallback engine specified in `10_AI_INTEGRATION_SPEC.md` §11; UI toggle in `08` `SCR-038`.
- **Verdict:** **PASS (Zero Guesses)**

---

## 4. Sampling Conclusion

All 8 sampled requirements pass the implementability test with zero open product or engineering questions. The full traceability chains (`FR → spec → screen → endpoint → test`) exist and resolve cleanly.
Execution status (Wave 5 re-measurement): the test fixtures are now physically on disk — `sample-data/` contains `d365_gl_actuals.csv` (10,037 data rows), `bank_ledger_actuals.csv` (499), `payroll_procurement_actuals.csv` (399), `budget_fy26.csv` (1,980), `expected_exceptions.csv` (40 rows), `malformed/` (16 files) and `templates/` (3 xlsx), all counts re-measured with Python line counts this wave. Execution of these tests is therefore **no longer blocked by missing fixtures**. One gap remains and it is explicitly *not* a Phase-0 blocker: `scripts/` still contains only `.gitkeep` — no test harness exists yet; building the harness is Phase 1 work.

---

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

**Verdict: A4 PASS (0 guesses) — Wave 5.** 4/4 traceability chains complete (FR-BVA-001, FR-IMP-008, FR-EXC-001, FR-XL-001), 5 non-blocking link recommendations recorded under F-036 (a, b, d, e, f). Caveat: A4 passing does not lift the overall NOT READY verdict, which remains blocked by F-015 / F-020–F-026 / F-029.

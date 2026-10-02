# Wave 5 — Draft BLOCKER Finding Entries (subagent: blockers) — READ-ONLY output

Target file: `audit/FINDINGS.md` (lead auditor applies; this file is draft only). Format copied from
`audit/FINDINGS.md` §1–§3 (Wave 3+ entry shape: `### \`F-0xx\` — Title — SEVERITY` with
**Severity / Location / Quotes / Contract Basis / Required Fix / Status**). No `docs/` or
`sample-data/` content was modified.

---

## 0. Re-verification report — mismatches vs. the assignment (read first)

Every cited `file:line` was re-read this wave. **All verbatim quotes matched.** Four reference-level
corrections were found; the entries below are drafted with the corrected references:

1. **F-022 — `docs/02_FUNCTIONAL_SPEC.md:1268` is E11, not E13.** The assignment cites ":1268 E13
   `import.ambiguousValue`". Reality: `:1268` = `| E11 | Amount exceeding display precision … |
   \`calc.displayRounding\` |`; **E13 `import.ambiguousValue` is at `docs/02_FUNCTIONAL_SPEC.md:1270`**
   (`:1269` = E12, no slug by design). Entry drafted with `:1270` for E13.
2. **F-022 — the count is 8 slugs, not 7.** Message slugs used in `docs/14_TESTING_QA_PLAN.md` §6.2
   (lines 313–328) that do **not** occur in `docs/02` §16 — in fact they do not occur *anywhere* in
   `docs/02` (full-file scan) — are **8 distinct slugs**:
   `import.budgetCoverageGap` (:313), `import.mappingIncomplete` (:314, :320),
   `import.parenthesesUnresolved` (:325), `import.numberUnparsed` (:325),
   `import.signRuleApplied` (:325), `import.encryptedFile` (:326), `import.fileLocked` (:327),
   `import.formulaNoCachedValue` (:328). Entry drafted with **8** and the full list.
3. **F-022 — row 12 is *not* a contradiction.** The assignment lists "rows 4/11/12 show `—` where 02
   has slugs". `docs/14:324` (row 12, single-row/tiny files) shows `—`, but `docs/02:1269` (E12) is
   itself "`— (no slug by design: success path, no error emitted)`" — the two matrices **agree** on
   row 12. Only **row 4** (`docs/02:1261` `import.zeroAmountRows` vs `docs/14:316` `—`) and **row 11**
   (`docs/02:1268` `calc.displayRounding` vs `docs/14:323` `—`) are `—`-vs-slug mismatches. Entry
   drafted accordingly (row 12 dropped from the contradiction list).
4. **F-024 — minor cite precision.** The literal `*Input (abridged):*` sits at
   `docs/10_AI_INTEGRATION_SPEC.md:323` (inside the cited 321–326 range); PROMPT-01's input block spans
   `:321`–`:326`. Entry cites `:323`.

Confirmations (assignment shorthand → verified contract source, used in `F-029`):
`K2` = Kickoff §5 quality-gate checklist item 2 (`project prompt/# FP&A MONTH-END COPILOT — AGENTIC.txt:112`
→ `GATE-01-02`); `A3J-3` = Addon 3 §J item 3 (contract `:807` → `GATE-04-03`); `A3J-11` = Addon 3 §J
item 11 (contract `:815` → `GATE-04-11`); `K10` = Addon 4 §K item 10 (contract `:1014` → `GATE-05-10`).
Everything else — `docs/05:524/:419/:182/:602/:284-289`, `docs/06:738/:222/:214`, `docs/14:279/:313-328/:680/:700/:729/:737/:753/:525`, `docs/07:208-221`, `docs/10:321-326/:487/:634/:700-716/:747/:425-447/:815`, `docs/28:46/:142-173` + entry-wording grep (only `:81`, `:82`, `:239`, `:241`), `docs/13:431/:527`, `docs/02:1012/:1258/:1259`, `docs/PHASE0_SUMMARY.md:12/:96/:100-108`, contract `:164/:474/:749/:778/:807/:815/:1014`, `docs/30:113`, `sample-data/expected_exceptions.csv:26`, `audit/recompute_wave5.log` (74 checks / 1 mismatch), and the `sample-data/**/*.{csv,py,md,txt}` injection scan (0 hits) — matched verbatim.

---

## PART A — Detailed findings entries (insert after the `F-019` entry)

### `F-020` — Wrong Exception ID on Canonical Material-Variance Case (F13a) — BLOCKER
- **Severity:** `BLOCKER` (docs contradict on a money fact; owner doc `06` and every other artifact say `EXC-018`, only `05` says `EXC-010`)
- **Location / Quotes:**
  - `docs/05_CALCULATION_SPEC.md:524` — F13a row verdict: "**Yes** (`EXC-010`, High)" (full row:
    "| F13a | `10,000,000.00` | `10,540,000.00` (var `+540,000.00`, `+5.4%`) | `max(500,000, 200,000) = 500,000` | `540,000 ≥ 500,000` ✓ | `5.4% ≥ 5%` ✓ | **Yes** (`EXC-010`, High) |")
  - `docs/06_EXCEPTION_RULES_CATALOG.md:738` (owner doc, planted-case register) — "| `P18` | `EXC-018` | 1 | High | Canonical case F13a (`+540,000.00`, `+5.4%`) |"
  - `docs/06_EXCEPTION_RULES_CATALOG.md:222` — "| `EXC-018` | Material variance (amount **and** %) | Budget relationship | High | fuzzy | FP&A Analyst | Budget |"
  - `docs/06_EXCEPTION_RULES_CATALOG.md:214` — "| `EXC-010` | Potential cut-off issue | Timing | High | exact | GL Accountant | — |" (i.e. `EXC-010` is a *Timing*/cut-off rule — a different rule family and a different owner)
  - `docs/14_TESTING_QA_PLAN.md:279` — "| `TST-RUL-18` | `EXC-018` | `P18` (F13a) | `P29` (F13b), `P30` (F13c) |"
  - `sample-data/expected_exceptions.csv:26` — "P18,EXC-018,Raised,IN01|5200|CC-100,High,540000.00,FY26-P09,Canonical case F13a: Var +₹540000.00 (+5.4%) satisfies materiality AND-test"
  - Consensus: 4 of 5 sources (`06` owner ×2, `14` test mapping, `sample-data` expected output) = `EXC-018`; only `05:524` = `EXC-010`. A test-fixture run asserting `EXC-018` would fail against the golden fixture printed in `05`.
- **Contract Basis:** Addon 4 §C (Source-of-Truth Matrix, contract `:864`: "Each fact lives in full in exactly one owning doc; everywhere else it is a one-line cross-reference." and `:873`: "Exception rule logic + thresholds | `06_EXCEPTION_RULES_CATALOG`") — one owner per fact, and `05` may only cross-reference. Severity definition (`FINDINGS.md` §1): docs contradicting = `BLOCKER`. Non-weakening rule: the stricter/owner value wins (`EXC-018`), never the reverse.
- **Required Fix (remediation window only):** In `docs/05_CALCULATION_SPEC.md:524` change the F13a verdict to "**Yes** (`EXC-018`, High)" (keep the row arithmetic untouched — it is correct), and keep `06` as the single owner with a one-line cross-reference rather than restating rule semantics. Do **not** edit `docs/06`, `docs/14`, or `sample-data/expected_exceptions.csv`. Record in `CHANGELOG.md`, then re-run `audit/recompute_wave5.py` (F13a checks) and an A2 contradiction grep for `EXC-010` vs `F13a`.
- **Status:** `OPEN`

---

### `F-021` — F6 YTD Variance % Truncated, Violating the Doc's Own Half-Up Rule — BLOCKER
- **Severity:** `BLOCKER` (stated intermediate value is wrong; recompute pass A3 = "Mismatch = BLOCKER")
- **Location / Quotes:**
  - `docs/05_CALCULATION_SPEC.md:419` — "- YTD variance % (full precision) = `95,801.00 / 3,000,000.00 = 0.031933` → displayed **`3.2%`**."
  - `docs/05_CALCULATION_SPEC.md:182` — "| Rounding mode | **Half-up** (banker's rounding is explicitly not used, so the rule is explainable to a finance user) |"
  - Independent recomputation (`audit/recompute_wave5.py` → `audit/recompute_wave5.log`): `MISMATCH  F6 pct_full(6dp): computed=0.031934 doc=0.031933`; log footer "TOTAL CHECKS: 74  MISMATCHES: 1". Exact value `95,801 / 3,000,000 = 0.0319336666…`; half-up at 6 dp = **`0.031934`** — `0.031933` is truncation, which `:182` explicitly prohibits.
  - Unaffected: `MATCH  F6 pct_disp(1dp): computed=3.2 doc=3.2` — the displayed **`3.2%`** stays correct; the *stated full-precision intermediate* is the defect (an implementer copying `0.031933` into code/tests gets a value the doc's own rounding rule forbids).
- **Contract Basis:** `docs/30_DOCUMENTATION_SET_REVIEW_GUIDE.md:113` — "3. **A3 — Correctness Recomputation:** Run automated scripts recomputing every worked example in Doc 05, Doc 06, Doc 07, and Doc 10. Mismatch = BLOCKER." Plus `05`'s own frozen constant `05:182` (half-up) — the example violates the rule the same document mandates.
- **Required Fix (remediation window only):** In `docs/05_CALCULATION_SPEC.md:419` replace `0.031933` with `0.031934` (half-up 6 dp), optionally showing the exact repeating value `0.0319336666…` and the rounding step; leave the displayed `3.2%` and the inputs (`95,801.00`, `3,000,000.00`) unchanged. Re-run `audit/recompute_wave5.py` and require 74/74 MATCH before closing; record in `CHANGELOG.md`. Do not weaken `05:182` or `30:113`.
- **Status:** `OPEN`

---

### `F-022` — Edge-Case Matrix Message-ID Contradictions Between `02` §16 and `14` §6.2 + False `GATE-05-10` ✅ — BLOCKER
- **Severity:** `BLOCKER` (two mandated matrices contradict on the message IDs the contract requires; gate check cannot honestly pass)
- **Location / Quotes:**
  - Contract `project prompt/# FP&A MONTH-END COPILOT — AGENTIC.txt:1014` (Addon 4 §K item 10, `K10`) — "- [ ] Tolerance policy (G.1) in doc 05; full edge-case matrix (G.2) in docs 02/14 with message IDs."
  - `docs/02_FUNCTIONAL_SPEC.md:1251` — "## 16. Edge-case matrix (Addon 4 §G.2 — canonical behaviour + message slug)" — **13 rows**, `E1`–`E13` (`:1258`–`:1270`):
    - `:1258` E1 → "`bva.firstPeriod`, `fc.insufficientHistory`"; `:1259` E2 → "`bva.noBudget`"; `:1261` E4 → "`import.zeroAmountRows`"; `:1268` E11 → "`calc.displayRounding`"; `:1270` E13 → "`import.ambiguousValue`".
  - `docs/14_TESTING_QA_PLAN.md:307` — "### 6.2 Edge-case data matrix (Addon 4 §G.2 — behaviour and message IDs)" — **16 rows** (`:313`–`:328`). Row-by-row contradictions with `02` §16:
    - `:313` row 1 (first-ever period) → "`import.budgetCoverageGap` (info), forecast hint" — vs `02` E1 "`bva.firstPeriod`, `fc.insufficientHistory`" (neither `02` slug appears anywhere in `14` §6.2).
    - `:314` row 2 (no budget loaded) → "`import.mappingIncomplete` family + screen copy" — vs `02` E2 "`bva.noBudget`".
    - `:316` row 4 (zero-amount rows) → "—" where `02` E4 (`:1261`) has "`import.zeroAmountRows`".
    - `:323` row 11 (display precision) → "—" where `02` E11 (`:1268`) has "`calc.displayRounding`".
    - `:325` row 13 (parentheses/`Cr-Dr`/text numbers) → "`import.parenthesesUnresolved`, `import.numberUnparsed`, `import.signRuleApplied`" — vs `02` E13 (`:1270`) "`import.ambiguousValue`" (none of the three exists in `02`).
    - Rows 14–16 (`:326` "`import.encryptedFile`", `:327` "`import.fileLocked` / `ERR-EXP-002`", `:328` "`import.formulaNoCachedValue`") have **no counterpart row at all** in `02` §16 (16 rows vs 13). Row 12 (`:324` "—") *agrees* with `02` E12 `:1269` "— (no slug by design…)" and is **not** a contradiction.
  - **8 message slugs used in `14` §6.2 do not exist anywhere in `docs/02`:** `import.budgetCoverageGap`, `import.mappingIncomplete`, `import.parenthesesUnresolved`, `import.numberUnparsed`, `import.signRuleApplied`, `import.encryptedFile`, `import.fileLocked`, `import.formulaNoCachedValue`.
  - `docs/14_TESTING_QA_PLAN.md:753` — "| `GATE-05-10` | Tolerance policy in `05`; full edge-case matrix in `02`/`14` with message IDs | `05` §6, this doc §6 | ✅ |" — marked green while the two matrices it certifies disagree on IDs and on row coverage.
- **Contract Basis:** Contract Addon 4 §K item 10 (contract `:1014`, quoted above) requires the matrix "with message IDs" in **both** `02` and `14`; Addon 4 §C one-owner-per-fact (contract `:864`) forbids two live definitions of the same slug; severity definition (`FINDINGS.md` §1): docs contradicting = `BLOCKER`; `GATE-05-10` "cannot honestly pass" while un-reconciled.
- **Required Fix (remediation window only):** Reconcile `docs/02` §16 and `docs/14` §6.2 **row by row** — the owner decides which ID is canonical per edge case (never the auditor, never by guessing); then (a) make both matrices carry identical row coverage (16 rows: add the three missing rows to `02`, or record in `02` why a row is `14`-only — no row is ever deleted), (b) propagate one slug per row to both docs, (c) list every slug in the `08`/`26` message catalog as required, (d) flip `docs/14:753` `GATE-05-10` to open until the reconciliation is re-verified, and (e) record the decision in `CHANGELOG.md`. Never resolve by deleting message IDs or by weakening the `with message IDs` requirement.
- **Status:** `OPEN`

---

### `F-023` — Forecast-Method Worked Examples Missing for Locked Actuals / 3-Month Average / Manual Override + False `GATE-01-02` ✅ — BLOCKER
- **Severity:** `BLOCKER` (contract requirement unimplemented — no worked example exists for three mandated methods; gate check cannot honestly pass)
- **Location / Quotes:**
  - Contract `project prompt/# FP&A MONTH-END COPILOT — AGENTIC.txt:164` (Kickoff §8) — "- Forecast methods (all deterministic): locked actuals; remaining-budget; run-rate; 3-month average; manual override — each with a worked example in doc 07."
  - Contract `:112` (Kickoff §5 checklist item 2, `K2`) — "- [ ] `05_CALCULATION_SPEC` contains worked examples with exact numbers for: MTD/YTD variance, variance %, favorability rules (…), prior-year comparison, rounding, **and each forecast method**."
  - `docs/07_FORECAST_METHODS_SPEC.md:208-221` (§11 "Worked end-to-end example (uses `05` fixtures)") contains only: `:216` "Remaining-budget spread … F14a", `:217` "Run-rate on the last 3 actuals … F14b", `:218` base-scenario run-rate F14b, `:219` "Best scenario (+5% revenue) … F14c", `:220` "Locked version at P09 close … F14d" (accuracy), `:221` guidance-panel note. **No worked example for locked actuals (`CALC-060`), 3-month average (`CALC-063`), or manual override (`CALC-064`).**
  - `docs/05_CALCULATION_SPEC.md:602` (fixture register) — "| `CALC-060`…`CALC-065` | Forecast methods | §9.1 | F14a, F14b, F14c |" — registers only three fixtures for six rules; `docs/05:528-560` confirms the fixture blocks are F14a (`CALC-061`), F14b (`CALC-062`), F14c (`CALC-065`), F14d (`CALC-066…069`) — `CALC-060`/`063`/`064` have no F-block anywhere in `05` or `07`.
  - `docs/05_CALCULATION_SPEC.md:284` — "| `CALC-060` | **Locked actuals** | Closed periods take their actual values; no forecast is generated for them | Closed period with no actuals → treated as `0` **and** flagged in the forecast summary as \"no actuals\" |" (defined, never worked).
  - `docs/05:287` — "| `CALC-063` | **3-month average** | Identical arithmetic to `CALC-062` with `N = 3` fixed | … |"; `docs/05:288` — "| `CALC-064` | **Manual override** | The user-supplied value | Override requires a reason (enforced); recorded as method `manual` with `override_reason` |" — both defined, neither worked with exact numbers.
  - `docs/14_TESTING_QA_PLAN.md:680` — "| `GATE-01-02` | `05` has worked examples with exact numbers: MTD/YTD variance, variance %, favourability, PY comparison, rounding, **every forecast method** | `05` §12 (F1–F14) | ✅ |" — green despite three methods having no example.
- **Contract Basis:** Kickoff §8 (contract `:164`, quoted above — "each with a worked example in doc 07") and Kickoff §5 checklist (contract `:112` — "and each forecast method"); audit severity definition: contract requirement unimplemented / gate that cannot honestly pass = `BLOCKER`. Non-weakening rule: the fix may never narrow `:164`'s five methods or `:112`'s "each forecast method".
- **Required Fix (remediation window only):** Add exact-number worked examples for the three missing methods — **locked actuals (`CALC-060`)**, **3-month average (`CALC-063`)**, **manual override (`CALC-064`)** — in `docs/07_FORECAST_METHODS_SPEC.md` §11 (reusing the §11 inputs: FY26, P01–P09 actuals, budget `12,000,000.00`, and the existing `05` fixture numbers so arithmetic stays single-sourced), and register each new fixture (e.g. F14e–F14g) in the `docs/05` fixture register (`:602`) with the corresponding `05` §12 block. Then re-verify `GATE-01-02` (`docs/14:680`) item by item against contract `:112` before leaving it ✅; record in `CHANGELOG.md`. Do **not** weaken contract `:164`/`:112`, and do not mark the gate green by rewording the check.
- **Status:** `OPEN`

---

### `F-024` — Prompt Worked Examples P2–P4 Lack Input Payloads (Contract Demands Input/Output) + False `GATE-04-03` ✅ — BLOCKER
- **Severity:** `BLOCKER` (contract requirement half-implemented — "worked example input/output" is input/output, and the gate check claims it exists for all four prompts)
- **Location / Quotes:**
  - Contract `project prompt/# FP&A MONTH-END COPILOT — AGENTIC.txt:749` (Addon 3 §D) — "**Four initial prompt texts written in Phase 0** (real text with placeholders, not outlines): (a) variance commentary, (b) mapping suggestion with evidence, (c) exception grouping/summary for the period, (d) follow-up message draft for an accounting owner. Each has: system prompt, input schema, output JSON schema, guardrails, **worked example input/output using sample data**."
  - Contract `:807` (Addon 3 §J item 3, `A3J-3`) — "- [ ] Four full initial prompt texts exist in doc 10 with worked examples on sample data."
  - `docs/10_AI_INTEGRATION_SPEC.md:321-326` (PROMPT-01) — "**Worked example (sample data, the `EXC-018` canonical case):**" with "*Input (abridged):* subject account `5200` / `CC-100` / `IN01`; measures actual ₹1,05,40,000.00, budget" (`:323`) … → **input present ✓**.
  - `docs/10_AI_INTEGRATION_SPEC.md:487` (PROMPT-02) — "**Worked example:**" followed only by the ` ```json ` output block `:489-503` (`"suggestions": [ … ]`) — **output only; no sample input payload.**
  - `docs/10_AI_INTEGRATION_SPEC.md:634` (PROMPT-03) — "**Worked example (excerpt):**" followed only by the output JSON `:636-648` — **output only.**
  - `docs/10_AI_INTEGRATION_SPEC.md:747` (PROMPT-04) — "**Worked example (excerpt):**" followed only by the output JSON `:749-756`; the input schema at `:700-716` is a bare JSON-Schema ("**Input schema (`input_schema`):**" … `"required": ["owner_name", "period_label", "tone", "section_name", "owner_exceptions_json"]`), and the blocks at `:425-447` are labelled "**`unmapped_columns_json` shape (engine-assembled):**" / "**`accepted_mappings_json` shape (evidence):**" — field *shape* fragments, not an example input.
  - Full-doc scan: the string "Input" occurs in `10` only at `:230`, `:323`, `:407`, `:558`, `:700`, `:876` — i.e. four schema headings plus PROMPT-01's single worked input; **no sample payload exists for P2, P3, P4 anywhere in §5.**
  - `docs/14_TESTING_QA_PLAN.md:729` — "| `GATE-04-03` | Four full initial prompt texts exist in `10` with worked examples | `10` §4/§5 | ✅ |" — green while three of the four examples cannot be exercised as specified.
- **Contract Basis:** Contract Addon 3 §D (contract `:749`, quoted above — "worked example input/output using sample data") and Addon 3 §J item 3 (contract `:807`); audit severity definition: contract requirement unimplemented/unverifiable + gate that cannot honestly pass = `BLOCKER`.
- **Required Fix (remediation window only):** Add a concrete sample-data **input payload** to each of the P2, P3 and P4 worked examples in `docs/10_AI_INTEGRATION_SPEC.md` (an "*Input:*" block mirroring PROMPT-01's `:323-326`, showing the exact engine-assembled input the JSON output was produced from — owner may reuse engine-shaped inputs such as the `unmapped_columns_json` / `accepted_mappings_json` values and the `ex-1…ex-3` / `owner_name` payload actually referenced by the outputs). Keep each existing output block intact. Then re-verify `GATE-04-03` (`docs/14:729`) against contract `:749`/`:807` before leaving it ✅; record in `CHANGELOG.md`. Do not weaken contract `:749`'s "input/output" to output-only.
- **Status:** `OPEN`

---

### `F-025` — UAT Entry Criterion Missing in Doc 28 + False `GATE-04-11` ✅ — BLOCKER
- **Severity:** `BLOCKER` (mandated UAT mechanic absent from the owning doc; the gate check that cites `28` §5 cannot honestly pass)
- **Location / Quotes:**
  - Contract `project prompt/# FP&A MONTH-END COPILOT — AGENTIC.txt:778` (Addon 3 §G) — "**UAT mechanics:** environment = installed build + sample project + one sanitized real month of client data; participants = FP&A analyst + at least one accounting-owner representative; duration ≤ 5 business days; **entry = features demoed**; exit = no open S1/S2 defects + sign-off template signed."
  - Contract `:815` (Addon 3 §J item 11, `A3J-11`) — "- [ ] Project DoD, UAT mechanics, defect severities, go-live checklist, and sign-off template present in doc 28."
  - `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md:142-173` (§5) — `:142` "## 5. UAT (`GATE-14`, Addon 3 §G.2)"; `:144` "### 5.1 Environment, participants and timing" (rows Build/Data/Participants/Duration/Fallback/Facilitation/Capture — **no entry row**); `:156` "### 5.2 The six scripts and their pass criteria"; `:167` "### 5.3 Exit criteria (`GATE-14`)" (5 exit items `:169-173`). **§5 ends at §5.3 — there is no entry criterion anywhere in the document.**
  - Word-grep across all 281 lines of `28` for `entry`: only `:81` ("…becomes a `27` entry…"), `:82` ("…a `27` entry…"), `:239` ("…logged as a `27` entry…"), `:241` ("Re-entry | A later phase…") — all unrelated to UAT admission.
  - `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md:46` — "| 7 | UAT closed with no open `S1`/`S2` and all `S3` decisions recorded (`GATE-14`) | §5.5 exit record |" — cites a **§5.5 that does not exist** (§5 has only §5.1–§5.3), a second pointer defect in the same section.
  - `docs/14_TESTING_QA_PLAN.md:737` — "| `GATE-04-11` | Project DoD, UAT mechanics, defect severities, go-live checklist and sign-off template in `28` | `28` | ✅ (`28` §2 DoD · §3 `S1`–`S4` + `DEF-` log · §4 pilot · **§5 UAT** · §6 the 22-item go-live checklist · §7 sign-off) |" — green on the strength of a §5 that omits a mandated mechanic.
- **Contract Basis:** Contract Addon 3 §G (contract `:778`, quoted above — "entry = features demoed") and Addon 3 §J item 11 (contract `:815` — "UAT mechanics … present in doc 28"); audit severity definition: contract requirement unimplemented + gate that cannot honestly pass = `BLOCKER`.
- **Required Fix (remediation window only):** Add an explicit **entry criterion** to `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §5 — "entry = features demoed" per contract `:778` — as a new row of §5.1 (or a §5.1.x "Entry criteria" line immediately before §5.2), stating what must be true/demoed before the ≤ 5-business-day UAT window opens. Also fix the `docs/28:46` pointer "§5.5 exit record" to the section that actually holds the exit record (§5.3 / §7). Then re-verify `GATE-04-11` (`docs/14:737`) against contract `:778`/`:815`; record in `CHANGELOG.md`. Do not delete or weaken the existing exit criteria.
- **Status:** `OPEN`

---

### `F-026` — Injection Fixture Physically Absent While Four Docs Claim It Exists + `GATE-02-08` ✅ — BLOCKER
- **Severity:** `BLOCKER` (false existence claims in four docs; the specified security test `TST-SEC-14` is unexecutable as written — a security requirement cannot be closed by prose)
- **Location / Quotes:**
  - **Measured absence (this wave):** recursive full-text scan of `sample-data/**/*.{csv,py,md,txt}` for `inject|malicious|ignore previous` (case-insensitive) returns **0 hits**. No planted payload, no injection fixture file, no "ignore previous instructions" sample anywhere in `sample-data/` (including `sample-data/malformed/` and `expected_exceptions.csv` — the latter's 40 rows are `EXC-001`…`EXC-024` control/exception plantings, none injection-related).
  - Claims of existence:
    - `docs/02_FUNCTIONAL_SPEC.md:1012` — "lengths capped. A planted malicious description in the sample data must not alter behaviour."
    - `docs/10_AI_INTEGRATION_SPEC.md:815` — "**Regression requirement:** the injection fixtures run on every AI-related change (`14` §AI tests) and are" (…run — fixtures that do not exist cannot run).
    - `docs/13_SECURITY_PRIVACY.md:431` — "| Evidence | The fixture set in `14` plants a malicious description in the sample data and asserts: the payload excludes it, the model output validates or falls back, no data was changed, and the flag is recorded | `TST-SEC-14` |"
    - `docs/13_SECURITY_PRIVACY.md:527` — "| `TST-SEC-14` | Injection fixture: malicious description → excluded from payload, flagged, schema-valid output or fallback, no data mutation | `SEC-025`, `026`, `027`, `044` |"
    - `docs/14_TESTING_QA_PLAN.md:525` — "| Injection defence | `TST-SEC-14` | pytest with the planted malicious description (`sample-data`) |"
    - `docs/14_TESTING_QA_PLAN.md:700` — "| `GATE-02-08` | Injection test case (planted malicious description) exists in `14` | `TST-SEC-14` | ✅ |"
- **Contract Basis:** Contract Addon 1 §O item 8 (`:474`) — "- [ ] Injection test case (planted malicious description) exists in doc 14." — that literal check is **PASS-literal** (the *test case* does exist in `14`), so `GATE-02-08`'s wording is not itself false; the BLOCKER is the four docs' **fixture-existence claims** (`02:1012`, `10:815`, `13:431`, `13:527`, `14:525`) asserting a `sample-data` artifact that does not exist — audit charter A6 / Addon 5 §C-D (every done/green claim needs an existing artifact; false = BLOCKER) plus severity definition "contract requirement unimplemented or unverifiable". `TST-SEC-14` as specified ("pytest with the planted malicious description (`sample-data`)") is unexecutable: pytest has nothing to plant.
- **Required Fix (remediation window only):** Owner decision (both options acceptable; auditor may not edit `sample-data/`): **(A, preferred — never dilute the security test)** add the planted injection fixture row(s) to `sample-data/` — either rows in `sample-data/expected_exceptions.csv` with a documented expectation (payload must exclude the planted description; output schema-valid or fallback; no mutation; flag recorded) or a dedicated fixture file (e.g. `sample-data/injection_fixture.*`) referenced by name from `14` §AI tests — so `TST-SEC-14` becomes executable; **or (B)** correct the five claims in `02:1012`, `10:815`, `13:431`, `13:527`, `14:525` to state the fixture is created by the test harness at runtime (if that is the true design) and keep `TST-SEC-14` executable against it. Whichever is chosen, re-run the `sample-data` scan for zero-vs-nonzero hits as evidence, record in `CHANGELOG.md`, and only then re-verify `GATE-02-08`. Never "fix" by deleting/weakening `TST-SEC-14`, §7 of `10`, or the SEC rows.
- **Status:** `OPEN`

---

### `F-029` — `PHASE0_SUMMARY.md` Overstates Readiness (False Green Claims on the Approval-Facing Page) — BLOCKER
- **Severity:** `BLOCKER` (unevidenced/false "done" claims on the page the owner signs off from)
- **Location / Quotes:**
  - `docs/PHASE0_SUMMARY.md:12` — "> - **Phase readiness:** All structural, documentation, and sample data requirements remediated for owner sign-off."
  - `docs/PHASE0_SUMMARY.md:96` — "| **Sample Data Deliverable** — `sample-data/` corpus & templates | Implemented | **Complete in Phase 0** — full synthetic dataset generated (10k GL rows, 16 malformed negative corpus files, templates, expected_exceptions.csv) | Verified green in `14` §15.4 (`GATE-04-02`, `GATE-04-07`); ready for packaging spike |" — no mention of this wave's `sample-data` gaps (injection fixture absent, `F-026`; watermark/`ProjectType` coverage findings).
  - `docs/PHASE0_SUMMARY.md:100-108` gate table — `:102` "**9 ✅** — 100% verified", `:103` "**12 ✅** — tabletop walkthrough…", `:104` "**12 ✅** — 100% verified", `:105` "**12 ✅** — 100% verified", `:106` "**13 ✅** — 100% verified", `:107` "**8 ✅** — 100% verified (`14` §15.6; Doc 30, evidence ladder, review guide locked)", and `:108` "| **Total** | **66** | **66 ✅ / 0 ⬜** (`14` §15) — 100% PASS |".
  - Nothing on the page qualifies those greens: **no `F-015` caveat** (grep of `PHASE0_SUMMARY.md` for `F-015`/Addon 5 absence → 0 hits; `:107` says only "provisional number", not "source missing/unverifiable"), and **no reference to this wave's failing checks** — `K2` (`GATE-01-02`, `F-023`), `A3J-3` (`GATE-04-03`, `F-024`), `A3J-11` (`GATE-04-11`, `F-025`), `K10` (`GATE-05-10`, `F-022`) — i.e. **62 of 66 at best, with 4 checks that cannot honestly pass**, plus `F-020`/`F-021` (money/rule-ID defects) and `F-029` itself.
- **Contract Basis:** Audit charter A6 (every done/green/integrated claim needs an artifact pointer; a false claim = `BLOCKER`) and severity definitions §1; precedent `F-005` (premature completion claim) and `F-007` (unsettled gate checks while requesting approval), both `BLOCKER` and both about this same page/table.
- **Required Fix (remediation window only):** On `docs/PHASE0_SUMMARY.md`: (1) rewrite `:12` so readiness is accurate (structural/doc/sample-data work *submitted* with open `BLOCKER` findings listed, sign-off pending remediation — not "all … remediated for owner sign-off"); (2) correct the gate table `:102-108` to **62 of 66 with the 4 failing checks** named (`GATE-01-02`/`K2`, `GATE-04-03`/`A3J-3`, `GATE-04-11`/`A3J-11`, `GATE-05-10`/`K10`) and add the `GATE-05B` provisional note (Addon 5 source still missing — `F-015` escalation); (3) add the `F-015` escalation caveat wherever "verified/locked" is claimed for Doc 30 / `GATE-05B`; (4) align `:96` with the actual `sample-data` state once `F-026` is resolved. All edits are owner-side in the remediation window; record in `CHANGELOG.md`. Never "fix" by lowering the standard or by deleting gate rows.
- **Status:** `OPEN`

---

**Total finding entries in this file: 8 (F-020, F-021, F-022, F-023, F-024, F-025, F-026, F-029) — all `BLOCKER`, all Status: `OPEN`.**

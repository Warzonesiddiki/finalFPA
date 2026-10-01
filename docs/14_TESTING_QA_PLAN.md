> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** the whole test system: levels, the canonical **`NFR-001`…`NFR-016`** targets and
> their measurement protocol, the `TST-*` catalogue, golden-file policy, planted-exception acceptance,
> the edge-case and tolerance matrices, the cross-artifact consistency test, performance baselines, CI and
> `scripts/check`, defect management, and the **authoritative checkbox lists for all five quality gates**
> (58 checks)
> **TL;DR (≤ 15 lines):**
> - **No test, no feature.** A feature closes only with its tests, its SCR-ID, its error messages and its
>   3–6 step demo recipe (`Addon 2 §F.5`); a red suite means the session is not done.
> - Tests are named by family and are **traceable one-to-one to FRs** (`20` owns the chain; this document
>   owns the families and the rules).
> - **86 tests are already reserved by other docs** (`TST-AI-01…14`, `TST-XL-01…26`, `TST-PPT-01…24`,
>   `TST-SEC-01…22`); this document adds the engine, UI, API, E2E, performance, Windows and UAT families
>   and defines how every one of them runs.
> - **Golden files are sacred.** Exact numbers come from `05` §12 (`F1`…`F14`); expectations are never
>   edited to make a build pass — the spec changes first.
> - **Planted-exception acceptance** is the headline bar: ≥ 90 % of the 32 planted raises detected, all
>   18 High-severity plantings found, and **zero** of the 8 precision controls raised (`06` §8.3); every
>   extra finding is justified in the false-positive log.
> - **Cross-artifact equality** (UI = Excel = deck = CLI = engine, zero tolerance at display precision) is
>   the single strongest guard against drift and is an S1 class when it fails.
> - `NFR-001`…`NFR-016` are the only numbers anyone may quote; each has a measurement method, a fixture,
>   a script and a recorded baseline re-measured at every gate.
> - The five gates (kickoff, Addon 1 §O, Addon 2 §I, Addon 3 §J, Addon 4 §K) are reproduced here as
>   **58 individually identified checks** with evidence and proving tests; Phase 0 approval needs all green.
> - Manual evidence on **real Windows 11** is mandatory where automation cannot prove it (SmartScreen,
>   Office files opening, DPI, sleep/standby, Playwright runs).

# 14 — Testing & QA Plan

## 1. Purpose, ownership and the quality contract

### 1.1 What this document owns

| Fact | Owner |
|---|---|
| Test levels, families, naming, runners, when each runs | **`14` (this document)** |
| The canonical NFR numbers and their measurement protocol | **`14`** (this document) |
| Golden fixtures' exact numbers | `05` §12 |
| Per-rule planted cases and expected verdicts | `06` |
| Screen state expectations (empty/loading/error) | `08` §17 |
| Test IDs reserved by the output, AI and security docs | `10`, `11`, `12`, `13` |
| The FR → spec → screen → API → test chain | `20` |
| Gate checklists' authoritative text | **`14` §15** (sourced from the five gate sections) |
| Defect severities, UAT mechanics, go-live | `28` |

### 1.2 The quality contract (binding rules)

1. **No test, no feature.** `Addon 3 §I.5`: a feature ships with its tests, its `SCR-ID`, its error
   messages in the catalog, and its demo recipe — otherwise it does not close.
2. **A red suite ends the session.** Any session that touched calculation, import, rule, export or
   migration code must run the full suite (golden files included) before it is considered finished
   (`Addon 1 §M.2`).
3. **Expectations are never edited to pass.** `expected_exceptions.csv` and every golden file are frozen;
   changing an expectation requires a spec change first, with `CHANGELOG` evidence (`Addon 1 §M.5`).
4. **Every number quoted in a gate comes from a test artefact** — a transcript, a JSON report or a signed
   checklist. No "it felt fast".
5. **Automate the deterministic, checklist the physical.** Anything that can be asserted in code must be
   (contracts, structures, files, arithmetic); things that require Windows, Office or human judgement have
   explicit manual checklists with named evidence.
6. **Coverage is a gate, not a report.** Engine ≥ 90 % statements, backend ≥ 75 % (`NFR-014`); lowering
   either is a spec change requiring an entry here and in `CHANGELOG`.
7. **Test data never mixes with client data.** The sample project is synthetic, watermarked and flagged;
   fixture files are sanitised; no client artefact ever enters `tests/` or `sample-data/` (`SEC-007`).
8. **Failures are first-class.** A test that fails only on a specific machine, or that is skipped, is
   reported at the gate with its reason — never silently skipped (`pytest -ra`, skip inventory in the gate
   evidence).

## 2. Test strategy: levels, taxonomy and what each proves

| # | Level | Proves | Runs on | Typical runtime |
|---|---|---|---|---|
| L1 | **Unit** (pytest) | Pure functions and engine internals behave exactly as specified — arithmetic, parsers, formatters, guards | Any OS, no I/O | seconds |
| L2 | **Golden arithmetic** | End-to-end numbers for a fixed input equal the values in `05` §12 exactly | Any OS (+ DuckDB) | seconds |
| L3 | **Rule acceptance** | Planted exceptions are found (or not) exactly as `06` documents | Any OS | ≤ 2 min |
| L4 | **Contract** | API envelope, error mapping, pagination, filter grammar, OpenAPI/type drift | Any OS | seconds |
| L5 | **Structural artefact** | Generated `.xlsx` / `.pptx` / `.csv` / `.zip` / `.json` parse and match their layout contract (openpyxl, python-pptx, zipfile, JSON Schema) | Any OS | ≤ 2 min |
| L6 | **Integration** | Stores, migrations, jobs, backup/restore, atomicity, synced-path and lock behaviour | Windows preferred | minutes |
| L7 | **E2E (Playwright)** | The user journey works in the real UI against the real API on Windows | Windows VM/runner | minutes |
| L8 | **Performance** | The `NFR-001`…`NFR-016` numbers are met on the reference machine and do not regress | Windows, reference machine | ≤ 15 min |
| L9 | **Manual / real-Windows / UAT** | What code cannot see: Office opening the files, SmartScreen, DPI, sleep/standby, human wording, tie-out to the client's own pack | Windows 11 + human | per checklist |

**Runner map:** L1–L6 = `pytest`; L7 = `npx playwright test`; L8 = `scripts/perf` (pytest-driven, `--scale 250000`); L9 = the manual checklists in §9 and `28` plus the UAT scripts in §12.4. Every level's output is an artefact attached to the gate (`scripts/check` transcript, `perf.json`, `acceptance_report.json`, Playwright HTML report, signed checklist).

## 3. The canonical NFR numbers

**These sixteen numbers are the only performance and quality targets in the product.** A number quoted
anywhere else must be one of these (or a fixture value from `05`). `09` §14 carries the engineering
strategies; this table carries the target, the measurement and the evidence.

| ID | Target | Measurement method | Fixture / tool | Evidence |
|---|---|---|---|---|
| `NFR-001` | Cold start ≤ **10 s** to an interactive Home with the sample project open | Stopwatch from process start to the Home screen's first interactive frame; median of 5 runs after a reboot | `sample-data` sample project; app timing log (`job.cold_start`) | `TST-PRF-01` + `perf.json` |
| `NFR-002` | 250k-row import ≤ **60 s** including the validation report, with progress at least every 2 s and a working Cancel | Timed `funa import` from file open to committed batch; progress cadence read from the job event log | `sample-data --scale 250000` GL file | `TST-PRF-02` |
| `NFR-003` | Dashboard interaction after load ≤ **2 s** | Time from click to rendered result for six representative interactions (filter, drill, sort, page) | 250k-row project | `TST-PRF-03` |
| `NFR-004` | Deck generation (6 slides) ≤ **15 s** | Timed `fpa export-ppt` end-to-end | 250k-row project | `TST-PRF-04` |
| `NFR-005` | Peak memory ≤ **1.5 GB** during a 250k-row import | Process peak working set sampled at 1 Hz during the import | as `NFR-002` | `TST-PRF-05` |
| `NFR-006` | Installer ≤ **500 MB** | Size of the produced Inno Setup artefact | `scripts/build` output | `TST-PRF-06` |
| `NFR-007` | Full rule run over 250k rows ≤ **60 s** | Timed `fpa exceptions --run` | 250k-row project | `TST-PRF-07` |
| `NFR-008` | Full sample-project walkthrough **passes with the network disabled** (except the marked AI step) | Scripted walkthrough with the adapter disabled | `TST-E2E-03` | E2E transcript |
| `NFR-009` | Excel month-end pack ≤ **120 s** at 250k rows (agreed with `11` §13) | Timed `fpa export-xlsx` | 250k-row project | `TST-PRF-09` |
| `NFR-010` | Diagnostics zip ≤ **20 MB**, redacted | Size + content assertions on a default bundle | `TST-SEC-12` fixture | `TST-PRF-10` |
| `NFR-011` | Logs ≤ **50 MB** per file, **7-day** retention | Rotation test with a log generator | `TST-PRF-11` | rotation transcript |
| `NFR-012` | Crash never yields a raw traceback; recoverable state on next launch | Fault-injection suite: kill the process at each job stage; assert the dialog and recovery | `TST-E2E-04`, `TST-WIN-09` | fault-injection report |
| `NFR-013` | Screen ≥ **1366×768**; 100–150 % scaling correct | Manual matrix at 100/125/150 % on a 1366×768 VM and a 1920×1080 machine | `TST-WIN-02` | signed checklist + screenshots |
| `NFR-014` | Coverage: `app/engine` ≥ **90 %** statements; whole backend ≥ **75 %** | `pytest --cov` thresholds enforced in `scripts/check` | full suite | `coverage.xml` + threshold failure |
| `NFR-015` | Cross-artifact equality: UI = Excel = deck = CLI = engine at display precision, **zero tolerance** | The comparison harness of §7 on a fixed filter state | `TST-XL-*`/`TST-PPT-13`/`TST-API-*` | `cross_artifact.json` |
| `NFR-016` | UI responsiveness: no interaction blocks > **2 s** while a long job runs | Playwright interaction timings during an import and an export | `TST-PRF-16` | Playwright timings |

**Measurement protocol (for every timed NFR).**

| Aspect | Rule |
|---|---|
| Reference machine | 4-core laptop-class CPU, 16 GB RAM, SSD, Windows 11 23H2+, Defender on, no other user load; recorded in `perf.json` (CPU model, RAM, OS build, app version, commit) |
| Repeats | 5 runs; report **median and worst**; a single good run is not evidence |
| Warm/cold | Storage-warm repeats for all except `NFR-001`, which is measured cold after a reboot |
| Comparison | Each gate compares against the recorded baseline; a **> 20 % regression** on any NFR blocks the gate until explained or fixed |
| Environment drift | If the reference machine changes, the baseline is re-recorded with a `CHANGELOG` note; silently re-baselining is a defect |
| Noise | Background tasks (Windows Update, indexing) paused; if the machine cannot be quiet, the run is repeated and the interference noted |
| Small machines | The client's actual laptop is measured once during the real-data pilot (`28`) — the reference machine is a floor, not a guarantee |

## 4. Test inventory: families, counts and where they live

### 4.1 Families

| Family | Count | Level(s) | Scope | Spec source |
|---|---|---|---|---|
| `TST-CALC-01…24` | 24 | L1, L2 | Every formula, window, rounding, scale, KPI, score and materiality rule | `05`, §4.2 |
| `TST-IMP-01…36` | 36 | L1, L3, L6 | The 32 validation checks 1:1 (`TST-IMP-nn` ↔ `IMP-nn`) plus corpus, resumability, atomicity, re-import guard | `04`, §4.3 |
| `TST-RUL-01…28` | 28 | L1, L3 | One test per rule (`EXC-001`…`024`) + scorecard, controls, re-run identity, effectiveness | `06`, §5 |
| `TST-FC-01…14` | 14 | L1, L2, L3 | Methods, scenarios, locks, accuracy, TTM, overrides | `07` |
| `TST-BVA-01…12` | 12 | L1, L6, L7 | BvA views, drill traceability, rollups, parity with exports | `02`/`05`/`08` |
| `TST-EXC-01…12` | 12 | L1, L6 | Register workflow, bulk actions, aging, owner assignment, reopen, evidence | `02`/`06`/`08` |
| `TST-UI-01…20` | 20 | L7 + manual | States, a11y, tokens, wording, jobs, help | `08` |
| `TST-API-01…16` | 16 | L4 | Envelope, errors, pagination, filters, auth, OpenAPI drift, CLI parity | `26`, `09` §5 |
| `TST-E2E-01…08` | 8 | L7 + manual | Golden path, issuance, offline, crash, upgrade, backup/restore, diagnostics, fresh install | this doc |
| `TST-PRF-01…16` | 16 | L8 | One per NFR | this doc |
| `TST-WIN-01…14` | 14 | L9 | Windows environment, DPI, paths, sleep, locks, SmartScreen | Addon 1 §G |
| `TST-UAT-01…06` | 6 | L9 | UAT scripts and tie-out | `28` |
| `TST-AI-01…14` | 14 | L1, L4, L5 | Reserved and fully specified by `10` | `10` |
| `TST-XL-01…26` | 26 | L5 (+14 L1) | Reserved and fully specified by `11` | `11` |
| `TST-PPT-01…24` | 24 | L5 (+17 L1/L8) | Reserved and fully specified by `12` | `12` |
| `TST-SEC-01…22` | 22 | L1–L6, L9 | Reserved and fully specified by `13` | `13` |
| **Total** | **292** (206 owned here + 86 reserved) | | | |

**Naming and location.** `tests/unit/` (L1), `tests/golden/` (L2), `tests/rules/` (L3), `tests/contract/`
(L4), `tests/artefacts/` (L5), `tests/integration/` (L6), `tests/e2e/` (L7), `tests/perf/` (L8),
`tests/manual/` (L9 checklists as markdown + evidence paths). Every test carries its ID in the docstring or
the pytest marker (`@pytest.mark.tst("TST-CALC-04")`) so the report can be mapped back to `20`'s
traceability table mechanically.

### 4.2 `TST-CALC` — arithmetic and display (24)

`TST-CALC-01`…`14` are the golden fixtures `F1`…`F14` from `05` §12, lifted verbatim (one test per
fixture, asserting **every** value in the fixture's expected-output table, including display strings).

| ID | Asserts |
|---|---|
| `TST-CALC-15` | Period assignment across fiscal-year boundaries, odd year starts, and invalid period codes (`CALC-001`/`002`) |
| `TST-CALC-16` | MTD/YTD/PY-MTD/PY-YTD/TTM windows — including "history does not exist yet" behaviour (`CALC-003`…`006`) |
| `TST-CALC-17` | Debit/credit → net sign convention, both directions, zero rows (`CALC-007`) |
| `TST-CALC-18` | Variance % guards: budget 0 → `n/a`; actual 0 and budget 0 → `—`; negative denominators use absolute value (`CALC-011`) |
| `TST-CALC-19` | Favour*ability* per account type, including the balance-sheet/other treatment and its explicit display (`CALC-012`) |
| `TST-CALC-20` | Percentage points vs percent (`CALC-013`) |
| `TST-CALC-21` | KPI library: every `KPI-001`…`006` formula, guard and label, including the "never shown alone" score rule |
| `TST-CALC-22` | Rounding is half-up and display-only; the sum-of-rounded footnote appears whenever a column sums to a different total (`CALC-030`/`031`) |
| `TST-CALC-23` | Scale whole/thousands/lakhs: label always present, values scaled once, negatives in parentheses (`CALC-032`/`033`) |
| `TST-CALC-24` | Data-quality score formula, weight table and the "score never masks a failure" guarantees; materiality default `max(₹500,000, 2 % × \|budget\|)` (`CALC-050`, `CALC-080`) |

### 4.3 `TST-IMP` — import, validation and batches (36)

| ID | Asserts |
|---|---|
| `TST-IMP-01`…`32` | **One test per check:** `TST-IMP-nn` exercises `IMP-nn` in `04` §6 with its documented outcome (pass / warn / reject / confirm), its message slug and its count reporting. A check without its test is a defect in `04` |
| `TST-IMP-33` | **Negative corpus:** every file in `sample-data/malformed/` fails gracefully and specifically — the expected message ID appears, no stack trace, the app stays usable, and a validation report is produced (§6.3) |
| `TST-IMP-34` | Wizard resumability: the 7-step wizard resumes after an app restart mid-step, with the same selections |
| `TST-IMP-35` | Atomicity: cancel and hard-kill at every stage leave **no** committed rows; staging is detectable and cleanable on next launch |
| `TST-IMP-36` | Re-import guards: identical checksum blocked ("already imported on <date>"), different checksum with overlapping vouchers produces the cross-batch duplicate report **before** commit |

### 4.4 `TST-RUL` — exception engine (28)

| ID | Asserts |
|---|---|
| `TST-RUL-01`…`24` | One per rule: the planted case in `06` raises with the documented severity, subject key, owner suggestion, amount and message; the rule's false-positive mitigation behaves as documented |
| `TST-RUL-25` | Scorecard: ≥ 15 rules enabled, ≥ 90 % of planted raises detected, every High-severity planting found (see §5) |
| `TST-RUL-26` | Controls: the 8 control plantings raise **nothing** (or are explained by a documented FP) |
| `TST-RUL-27` | Re-run identity scenario: raise → tune a threshold → re-run → open stays open, closed stays closed, re-flagged items show the "flagged again" badge and never auto-reopen |
| `TST-RUL-28` | Effectiveness analytics: times raised, % closed as explained, average days to close, aging buckets, and the single audit entry per bulk change |

### 4.5 `TST-FC` — forecasting (14)

| ID | Asserts |
|---|---|
| `TST-FC-01`…`08` | One per method: the method's arithmetic on its fixture, the applicability guard, and the "never a silent substitution" rule when the method is unavailable |
| `TST-FC-09` | Scenario create/rename/copy/delete and the default-scenario behaviour |
| `TST-FC-10` | Lock semantics: a locked version is immutable, unlocking is explicit and audited, closed periods cannot receive writes |
| `TST-FC-11` | Accuracy metrics (`CALC-066`…`069`) with worked examples: error, absolute error, signed bias, MAPE-lite, excluded periods, and `min_accuracy_periods = 3` |
| `TST-FC-12` | TTM in forecast context, and run-rate methods disabled with the explanatory hint when no prior-year data exists |
| `TST-FC-13` | Overrides: manual override requires a reason, is audited, and appears in the pack's method-mix line |
| `TST-FC-14` | Three-way view (Actual/Budget/Forecast) and the landing estimate's basis label (`YTD actual + forecast remaining`) |

### 4.6 `TST-BVA` and `TST-EXC` — analysis and register (24)

| ID | Asserts |
|---|---|
| `TST-BVA-01` | Total row = Σ visible rows after every filter and sort (no phantom rows) |
| `TST-BVA-02` | **100 % drill traceability:** every displayed number drills to transactions whose sum equals it exactly (exact `Decimal`, `05` §4) |
| `TST-BVA-03` | Drill performance: variance → transaction list in ≤ 5 clicks and **≤ 5 minutes** end-to-end on 250k rows |
| `TST-BVA-04` | Entity rollup with no eliminations, and the label making that explicit |
| `TST-BVA-05` | Account hierarchy rollups and the "parent = Σ children" check |
| `TST-BVA-06` | Filter state stickiness and the filter string shown on every export ("export what you see") |
| `TST-BVA-07` | Window labels always visible (`MTD`/`YTD`/`TTM`) — no unlabelled totals |
| `TST-BVA-08` | Empty states: no budget, first-ever period, no PY data — explicit messages, no zero masquerade |
| `TST-BVA-09` | Prior-year comparison and the `n/a` vs `—` distinctions |
| `TST-BVA-10` | Control-total variance row (`CALC-070`…`072`) with its own display rules |
| `TST-BVA-11` | Top-N rule: ordered by \|variance\| with ties broken deterministically, and the same rows in app/Excel/deck |
| `TST-BVA-12` | Chart inventory (`CHT-001`…`012`): every chart renders, exposes exact values on hover and has its table view |
| `TST-EXC-01` | Status workflow transitions (Open → In Review → Explained → Corrected → Closed) with the allowed/blocked matrix |
| `TST-EXC-02` | Notes are append-only; editing an earlier note creates a new entry; who/when recorded |
| `TST-EXC-03` | Bulk status/owner change: one audit entry per item, partial failures reported, undo not offered (a new change is the correction) |
| `TST-EXC-04` | Aging and overdue: days-open, buckets 0–7 / 8–30 / 31+, overdue highlight, and the exact dates used |
| `TST-EXC-05` | Owner auto-assign from the mapping, manual override wins and is remembered |
| `TST-EXC-06` | Period close: reopening a closed period warns, is audited, and re-locks cleanly |
| `TST-EXC-07` | Counts chips (total/open/overdue/high/unassigned) match the register exactly after every action |
| `TST-EXC-08` | Wording: "Potential exception — requires accounting review", never "error"/"wrong" (copy scan over the UI strings) |
| `TST-EXC-09` | Register → Excel/CSV parity: same rows, same order, same filter statement (`NFR-015`) |
| `TST-EXC-10` | Evidence bundle (`11` §6) contains subject rows, the rule definition, the validation extract, the mapping version and the audit trail — and nothing else |
| `TST-EXC-11` | Closed items re-flagged show the badge and keep their history; the register never silently re-opens |
| `TST-EXC-12` | SLA timestamps and the ≥ 80 % statused-within-5-days metric are computable from the register |

## 5. Planted-exception acceptance

### 5.1 The corpus

`06` §7 defines 40 plantings in the generated sample dataset, and `sample-data/expected_exceptions.csv` is
the answer key (`planting_id, rule_id, expected_verdict, subject_key, severity, amount, period, notes`).

| Category | Count | Composition |
|---|---|---|
| Expected raises (`P1`…`P24`) | **32** | 18 High · 12 Medium · 2 Low — deliberately weighted so severity filtering is demonstrable |
| Precision controls (`P25`…`P32`) | **8** | Near-misses that must produce **no** exception |
| **Total** | **40** | — |

### 5.2 The harness

`tests/rules/test_acceptance.py` (L3), run by `scripts/acceptance`:

1. **Fresh corpus:** the generator builds the sample project from a fixed seed (`sample-data --seed 20260101`),
   so the corpus is deterministic and reproducible on any machine; the run asserts the generator's own
   checksum before evaluating.
2. **Full engine run** over the sample data with default thresholds, every rule enabled.
3. **Join** raised exceptions to the answer key on `(rule_id, subject_key)`.
4. **Classify** every raise: *expected* (in the key), *control* (a `P25`…`P32` subject), or *extra*.
5. **Report** to `acceptance_report.json` and a human-readable `acceptance_report.md`: counts by severity,
   the miss list with each rule's threshold reasoning, the extra-findings list with the false-positive log
   reference, and the controls result.
6. **Fail the build** when a bar in §5.3 is not met. A red acceptance run is a **release-blocking** defect.

### 5.3 Bars (owned here; `06` §8.3 states the first two)

| Bar | Value | Notes |
|---|---|---|
| Planted-exception recall | **≥ 90 %** of the 32 raises (≥ 29) | `06` §8.3 |
| Control precision | **0 of 8** controls may raise | `06` §8.3 — any control raise is a P0 defect in the rule's precision filter |
| High-severity recall | **18 of 18** High plantings found | `14`-owned stricter bar: a missed High is a control failure, not a statistic |
| Extra findings | Every extra raise justified in the false-positive log | `06` §8.3; a rule with > 3 unexplained findings is tuned or documented before the gate |
| Stability | Two consecutive runs produce identical raise sets | Determinism (no ordering/seed effects) |

### 5.4 Per-rule test map

`TST-RUL-01`…`24` correspond one-to-one with `EXC-001`…`024`, and each asserts that rule's plantings plus
any control assigned to it:

| Test | Rule | Plantings (raises asserted) | Controls (must not raise) |
|---|---|---|---|
| `TST-RUL-01` | `EXC-001` | `P1` | — |
| `TST-RUL-02` | `EXC-002` | `P2` | — |
| `TST-RUL-03` | `EXC-003` | `P3` | — |
| `TST-RUL-04` | `EXC-004` | `P4a`, `P4b` | — |
| `TST-RUL-05` | `EXC-005` | `P5` | — |
| `TST-RUL-06` | `EXC-006` | `P6` | — |
| `TST-RUL-07` | `EXC-007` | `P7a`, `P7b` | `P25` |
| `TST-RUL-08` | `EXC-008` | `P8` | `P26` |
| `TST-RUL-09` | `EXC-009` | `P9` | — |
| `TST-RUL-10` | `EXC-010` | `P10a`, `P10b` | — |
| `TST-RUL-11` | `EXC-011` | `P11` | — |
| `TST-RUL-12` | `EXC-012` | `P12` | `P27` |
| `TST-RUL-13` | `EXC-013` | `P13a`, `P13b` | `P28` |
| `TST-RUL-14` | `EXC-014` | `P14` | — |
| `TST-RUL-15` | `EXC-015` | `P15a`, `P15b` | `P32` |
| `TST-RUL-16` | `EXC-016` | `P16` | — |
| `TST-RUL-17` | `EXC-017` | `P17` | — |
| `TST-RUL-18` | `EXC-018` | `P18` (F13a) | `P29` (F13b), `P30` (F13c) |
| `TST-RUL-19` | `EXC-019` | `P19` | — |
| `TST-RUL-20` | `EXC-020` | `P20` | — |
| `TST-RUL-21` | `EXC-021` | `P21a`, `P21b` | `P31` |
| `TST-RUL-22` | `EXC-022` | `P22` | — |
| `TST-RUL-23` | `EXC-023` | `P23` | — |
| `TST-RUL-24` | `EXC-024` | `P24` | — |

### 5.5 Re-run identity scenario (`TST-RUL-27`, worked)

1. Run rules on the sample data → `P7a` raises; an analyst sets it **Closed (explained)** with a note.
2. Change `EXC-007`'s date tolerance (a versioned threshold change).
3. Re-run the engine.
4. **Expected:** the identity (`rule_id + subject_key`) survives; the exception stays Closed, carries the
   **"flagged again"** badge with the old and new evidence, its history is intact, and no auto-reopen
   occurs. A new occurrence with a different subject key is a new exception with its own history.

## 6. Tolerance, edge cases and the negative corpus

### 6.1 Tolerance policy tests (Addon 4 §G.1)

| Rule | Test |
|---|---|
| Internal money math is **exact Decimal** — no epsilon in any comparison | Property sweep over a fixed boundary table (0, ±0.005, ±0.01, 1 minor unit, large values) asserting exact equality and stable ordering; any float in a money path fails via a `Decimal`-only import rule |
| Display rounding is **half-up**, 2 dp money / 1 dp %, applied once at display time | `TST-CALC-22`/`23` plus a display-boundary table (`0.005`, `0.015`, `99.95`) |
| Cross-artifact values are equal at display precision (zero tolerance) | §7 harness (`NFR-015`) |
| `n/a` (÷0) vs `—` (0/0) are distinct in every surface | `TST-CALC-18` extended to Excel/deck strings (`TST-XL-*`, `TST-PPT-12`) |

### 6.2 Edge-case data matrix (Addon 4 §G.2 — behaviour and message IDs)

Every row is a test; "message ID" is the catalog slug/`ERR-` code the user sees.

| # | Input condition | Required behaviour | Message ID | Test |
|---|---|---|---|---|
| 1 | First-ever period: no prior periods, no PY | BvA works; PY/TTM views hidden; run-rate methods disabled with a hint — never a crash or blank chart | `import.budgetCoverageGap` (info), forecast hint | `TST-BVA-08`, `TST-FC-12` |
| 2 | No budget loaded | BvA shows the explicit empty state + "Import budget" CTA; variance rules disable with a notice — never variance = 0 masquerade | `import.mappingIncomplete` family + screen copy | `TST-BVA-08` |
| 3 | Header-only actuals file (0 data rows) | Reject by default; accept-as-zero only after explicit confirm (zero-activity period) | `import.noDataRows` | `TST-IMP-33` |
| 4 | Rows with zero amounts | Kept; excluded from outlier-type rules; visible in drill | — | `TST-CALC-17`, `TST-BVA-02` |
| 5 | Future-dated transactions | Loaded per the period rule; cut-off exception flags them | `EXC-011` message | `TST-RUL-11` |
| 6 | Dates outside the fiscal year | Quarantined — never assigned to a wrong period | `import.dateOutsideFiscalYear` | `TST-IMP-33` |
| 7 | Duplicate column headers | Import blocked until the profile renames them | `import.duplicateHeaders` | `TST-IMP-33` |
| 8 | ≥ 90 % of rows unmapped | Import blocked with the mapping CTA | `import.unmappedThreshold` + `import.mappingIncomplete` | `TST-IMP-33` |
| 9 | Budget imported mid-period or after actuals | Allowed anytime; stale-derived indicator appears | stale banner (`08` §B.7) | `TST-UI-08` |
| 10 | Mixed-currency rows in a single-currency project | Quarantine with the message (default per `04`) | `import.mixedCurrency` | `TST-IMP-33` |
| 11 | Amount exceeding display precision | Round per §6.1; never truncate silently | — | `TST-CALC-22` |
| 12 | Single-row / tiny files | Fully supported — no size assumptions anywhere | — | `TST-IMP-35` |
| 13 | Amounts in parentheses / `Cr-Dr` / text numbers | Parsed per `04` §5's rules, with the conversion reported | `import.parenthesesUnresolved`, `import.numberUnparsed`, `import.signRuleApplied` | `TST-IMP-33` |
| 14 | Protected/encrypted workbook | Rejected with the plain-language message | `import.encryptedFile` | `TST-IMP-33` |
| 15 | File locked by Excel | Retry offer, then the locked-file message | `import.fileLocked` / `ERR-EXP-002` | `TST-IMP-33` |
| 16 | Formula cells with no cached value | Row flagged; the import cannot invent a value | `import.formulaNoCachedValue` | `TST-IMP-33` |

### 6.3 The negative file corpus (`sample-data/malformed/`)

`TST-IMP-33` walks every file below and asserts three things: the **expected message ID appears**, **no
stack trace or raw exception** reaches the UI/log, and the app remains usable afterwards. The corpus is
committed with the generator (no client data, ever — `SEC-007`).

| File | Planted defect | Expected message ID |
|---|---|---|
| `truncated_gl.csv` | File cut mid-row | `import.raggedRow` |
| `cp1252_ansi_dates.xlsx` | Wrong encoding + text-formatted dates | `import.encodingDetected` / `import.serialDatesConverted` |
| `missing_voucher_column.xlsx` | Required column absent | `import.missingRequiredColumns` |
| `merged_two_row_header.xlsx` | Merged multi-row header | `import.multiRowHeader` |
| `embedded_total_rows.xlsx` | Subtotal rows inside the data | `import.totalRowsIgnored` |
| `semicolon_delimiter.csv` | Wrong delimiter for the profile | `import.delimiterAmbiguous` / `import.delimiterDetected` |
| `parentheses_negatives.csv` | Negative amounts as `(1,234.00)` | `import.signRuleApplied` |
| `duplicate_headers.xlsx` | Two `Amount` columns | `import.duplicateHeaders` |
| `no_data_rows.xlsx` | Header only | `import.noDataRows` |
| `bank_ledger_unbalanced.csv` | Debits ≠ credits by ₹350 | `import.balanceMismatch` (tolerance path) |
| `protected_sheet.xlsx` | Protected worksheet | `import.sheetProtected` |
| `hidden_rows_missing_header.xlsx` | Header hidden by an Excel filter | `import.rowsHiddenInExcel` |
| `future_period_rows.xlsx` | Period outside the calendar | `import.periodNotInCalendar` |
| `mixed_currency_rows.xlsx` | Two currencies in one column | `import.mixedCurrency` |
| `unicode_vendor_names.xlsx` | Devanagari/emoji vendor names, long fields | (accepted; asserts no crash and a correct round-trip) |
| `zip_bomb_guard.xlsx` | High compression ratio | `import.fileTooLarge` / guard message |

Anything the corpus cannot cover is added as a bug-fix test in the same change that fixes it (the corpus
grows; it never shrinks).

## 7. The cross-artifact consistency test (`NFR-015`)

### 7.1 Purpose and comparison set

For one **fixed filter state** (e.g. `Entity=IN01 · Period=FY26-P09 · Window=MTD · Scenario=Base`), the
same numbers must appear in five places. This is the strongest guard against display and export drift
(Addon 3 §F.4) and the reason `11` forbids formula cells.

| Surface | Read by | Compared |
|---|---|---|
| **Engine** | CLI `bva --json`, `exceptions --json` | The authority: exact `Decimal` values |
| **UI** | API response payload (same endpoint the screen uses) | Display strings and the underlying values |
| **Excel pack** | `openpyxl(data_only=True)` over the named cells/stamp block | Display strings, stamp block, filters, counts |
| **Deck** | `python-pptx`: text frames by shape name, table cells, chart series data | Display strings and chart values |
| **CSV/ad-hoc exports** | Row-parser | Row values in the current filter/sort/column state |

### 7.2 Procedure (run as `TST-API-14` + `TST-XL-*` + `TST-PPT-13` under one harness)

1. Freeze the filter state; record it as `Pack_Stamp_FilterJSON`.
2. Capture the engine values (exact) and the UI payload.
3. Generate the pack and the deck from that exact state.
4. Read both artefacts back with their parsers — never from a screenshot, never by eye.
5. Compare **every** value in the comparison set at display precision: totals, variance, variance %,
   favourability signals, KPI cards, bridge steps, top-5 rows, exception counts, forecast cards, method
   mix, units label, `n/a`/`—` tokens, filter string, stamp fields, row counts.
6. Emit `cross_artifact.json`; any difference is a **failure**.

### 7.3 Rules

| Situation | Ruling |
|---|---|
| Difference found | **S1 defect**, release blocked; the renderer or parser is fixed — never the engine, never by relaxing the test |
| Ordering ties (two equal values) | Ordering is deterministic by the documented tie-breakers; ties are compared as sets **only** where the spec permits |
| Formatting-only differences (spacing, trailing zeros) | Compared as *display strings* where the spec defines them; a formatting difference is a defect in the surface that deviates |
| Undefined comparisons | Anything not covered must be added to the comparison set or explicitly listed as out of scope here — never silently ignored |
| Timestamps | Excluded (generation time differs), except the stamp's own equality requirement (`11` §11) |

## 8. Performance testing and baselines

### 8.1 The harness

**ID rule:** `TST-PRF-01`…`16` correspond one-to-one with `NFR-001`…`016`. Where an NFR is proven by a
structural test (12–15), `TST-PRF-nn` asserts the recorded evidence of that proof (the fault-injection
report, the signed scaling checklist, the coverage thresholds, the `cross_artifact.json`), so every NFR
has exactly one measurement entry point.

`scripts/perf` runs the full chain against the generated 250k-row project and writes `perf.json`:

| Step | Measured |
|---|---|
| Generate the 250k dataset (`sample-data --scale 250000`) | generator runtime (informational) |
| Cold start + open the project | `NFR-001` |
| Import the GL file | `NFR-002`, `NFR-005` |
| Run all rules | `NFR-007` |
| Six UI interactions | `NFR-003` (via Playwright) |
| Build the Excel pack | `NFR-009` |
| Build the deck | `NFR-004` |
| Export diagnostics | `NFR-010` |
| Log rotation | `NFR-011` |
| Interaction during jobs | `NFR-016` |

`perf.json` records the machine profile, OS build, app version, commit hash, seed, each NFR's
median/worst/baseline/delta and the pass/fail verdict. It is attached to every gate.

### 8.2 Baselines

Baselines live in `tests/perf/baselines/<nfr>.json` and are **committed**. Phase 0 records the harness
design and the targets only; the first measurements are taken in Phase 1 and re-recorded at every gate.
Re-baselining requires a `CHANGELOG` entry naming the machine change or the approved regression — silent
re-baselining is a defect (`SEC-*`-style honesty applied to performance).

### 8.3 Regression rules

| Rule | Detail |
|---|---|
| Blocking | > 20 % regression on any NFR blocks the gate until fixed or explicitly waived in `CHANGELOG` with the user's approval |
| Noise | Three consecutive runs showing the regression, with background services paused |
| Blame | `perf.json` diffs include the previous commit, so the regression's likely source is visible |
| Environment | A changed reference machine invalidates the comparison; re-record (§8.2) |

## 9. UI, E2E, Windows-environment and manual testing

### 9.1 The golden path (`TST-E2E-01`, Playwright, Windows)

Launch → open the sample project → import a file → pass validation → drill a variance to transactions →
open the exception raised → set a status with a note → refresh the forecast → generate the deck →
generate the Excel pack → issue the pack. Assertions at each step: the expected screen, the expected
numbers, the expected job outcome, and no console errors. Runs before every phase gate on Windows
(`Addon 2 §F.4`).

### 9.2 State sweeps (`TST-UI-01`…`04`)

`08` §17 carries the per-screen state matrix (empty / loading / error / first-run / stale / sample). The
sweep is a data-driven test over that matrix: every screen must render the documented state with the
documented copy and a working action. Targeted tests then cover the six highest-risk screens (Home,
Import, BvA, Drill, Register, Pack) in depth.

### 9.3 Accessibility and wording (`TST-UI-05`…`12`)

| Test | Asserts |
|---|---|
| `TST-UI-05` | Full keyboard path on four critical flows; no keyboard trap; visible focus |
| `TST-UI-06` | ARIA names on every control (automated audit) and a screen-reader pass on Home + BvA |
| `TST-UI-07` | WCAG AA contrast (4.5:1) for every text/fill pair in the default theme |
| `TST-UI-08` | Stale-data banner appears after a mapping/threshold change and disappears after a re-run |
| `TST-UI-09` | No colour-only signal anywhere: every semantic colour is paired with a sign/word (`CF-001`…`012`) |
| `TST-UI-10` | Copy scan: no "error"/"wrong entry" for exceptions; the advisory disclaimer appears where required; no jargon list violations |
| `TST-UI-11` | Charts expose exact values (tooltip/table view) and keyboard access |
| `TST-UI-12` | Theme tokens: no hardcoded hex outside `ui/theme/tokens.ts` (lint) and the app matches `08` §19 |

### 9.4 Windows-environment checklist (`TST-WIN-01`…`14`, manual with evidence)

| ID | Check |
|---|---|
| `TST-WIN-01` | Install per-user with **no admin rights**; uninstall leaves user data unless chosen otherwise |
| `TST-WIN-02` | 1366×768 at 100 %, 125 %, 150 % scaling: no clipped controls, no overlapping text |
| `TST-WIN-03` | Long and Unicode paths (client name, Devanagari) work for projects and exports |
| `TST-WIN-04` | Sleep/standby mid-import: resumes or fails cleanly with recovery on next launch |
| `TST-WIN-05` | Single instance per project: second launch shows the friendly "already open" message |
| `TST-WIN-06` | OneDrive/synced folder: project creation is blocked with the documented message; export warns (`SEC-032`) |
| `TST-WIN-07` | Antivirus/Defender: a locked file produces a readable message, never a raw OS error |
| `TST-WIN-08` | SmartScreen on a fresh machine: the documented "More info → Run anyway" walkthrough works and the SHA-256 matches the published value |
| `TST-WIN-09` | Fault injection: kill during import/rule run/export → next launch reports the interruption with safe choices (`NFR-012`) |
| `TST-WIN-10` | Office opens every artefact without a repair prompt (`TST-XL-01`, `TST-PPT-01`) |
| `TST-WIN-11` | WebView2 present/missing paths behave as documented (`doctor` reports it) |
| `TST-WIN-12` | Storage screen numbers match Explorer within 5 % |
| `TST-WIN-13` | Timezone/locale changes do not alter stored values or period assignment |
| `TST-WIN-14` | Fresh machine, no network, no AI key: the app is fully usable (`NFR-008`) |

### 9.5 Other E2E journeys (`TST-E2E-02`…`08`)

| ID | Journey |
|---|---|
| `TST-E2E-02` | Pack issuance: lock commentary → issue → version increments → recipients recorded → re-issue creates a new version |
| `TST-E2E-03` | Offline walkthrough with the network adapter disabled (`NFR-008`) |
| `TST-E2E-04` | Crash recovery: kill at each job stage, relaunch, resolve the reported interruptions |
| `TST-E2E-05` | Upgrade over a previous version with an existing project (fixture: a real prior-version project, `24`) |
| `TST-E2E-06` | Backup → restore on a clean VM → numbers and workflow state identical |
| `TST-E2E-07` | Diagnostics export: default redaction, manifest hashes, ≤ 20 MB |
| `TST-E2E-08` | First run on a clean Windows 11 VM: install → first-run wizard → sample project → close |

### 9.6 Remaining UI tests (`TST-UI-13`…`20`)

| ID | Asserts |
|---|---|
| `TST-UI-13` | Job drawer: progress, cancel, failure with the code + hint, resume where documented |
| `TST-UI-14` | Search: debounce, keyboard-only use, accent/Unicode handling, no unfiltered-data leak in results |
| `TST-UI-15` | Virtualisation/pagination: 250k-row views stay responsive, page caps hold, "no more rows" is honest |
| `TST-UI-16` | Destructive confirmations: delete project (typed), overwrite export, void batch — each requires the documented confirmation |
| `TST-UI-17` | First-run: wizard validates inline, resumes after restart, sample-project path works, reset sample is safe |
| `TST-UI-18` | Help: every screen links to its topic; jargon tooltips exist where `08` requires them |
| `TST-UI-19` | Print/PDF readiness: per-sheet setup, "Open for printing" action, and no claim of in-app PDF rendering (`DEC-028`) |
| `TST-UI-20` | Settings round-trip: machine vs project settings persist correctly; no secret is ever rendered |

## 10. Security, privacy and supply-chain testing

The 22 `TST-SEC-*` tests are specified row-by-row in `13` §13.2; this section owns how they run and what
else the pipeline must prove.

| Group | Tests | Runner |
|---|---|---|
| Local-only / outbound inventory | `TST-SEC-01`…`03` | pytest + network-off E2E |
| API loopback and token | `TST-SEC-04` | pytest (spawns the API) |
| Source-file immutability | `TST-SEC-05` | pytest (hash comparison) |
| Key handling and storage | `TST-SEC-06`, `08`, `10`, `11` | pytest + a simulated foreign profile |
| Folder permissions | `TST-SEC-07` | manual on Windows (second local user account) |
| Log and diagnostics content | `TST-SEC-09`, `12`, `13` | pytest with planted values + bundle parser |
| Injection defence | `TST-SEC-14` | pytest with the planted malicious description (`sample-data`) |
| Deletion and retention | `TST-SEC-15` | E2E on a copy of the sample project |
| Sync-folder guard | `TST-SEC-16` | integration with a simulated OneDrive path |
| Repo and pipeline hygiene | `TST-SEC-17`, `20` | `scripts/check` (secret scan, license scan, SBOM presence) |
| Crash locality and support mode | `TST-SEC-18` | fault injection |
| Copy audit | `TST-SEC-19` | pytest over the UI string catalogue |
| Payload limits / TLS | `TST-SEC-21` | pytest against a local stub endpoint |
| Audit integrity | `TST-SEC-22` | pytest + E2E attempt to tamper |

**Fault-injection set (feeds `NFR-012`):** kill during import staging, import commit, rule run, forecast
generation, Excel build, deck build, issuance, migration and backup; disk-full during each write; locked
target file; read-only project folder; corrupt `state.sqlite`; truncated DuckDB file. Every case asserts:
a plain-language dialog, no traceback, no partial artefact, no silent data change, and a recovery path on
next launch.

## 11. Data integrity, migration and upgrade tests

| Test | Asserts |
|---|---|
| `TST-E2E-05` | **Upgrade over a previous version**: a real prior-version project fixture migrates forward, numbers unchanged (hash-compared before/after), no manual step (`24`) |
| `TST-E2E-06` | Backup → restore round trip on a clean VM: every table, setting and workflow state identical; secrets absent (`SEC-035`) |
| `TST-API-15` | Idempotency: repeated GETs change nothing; repeated POSTs with the same key do not double-apply |
| `TST-IMP-35` | Atomicity: import crash/cancel leaves no committed rows; staging cleaned on next launch |
| `TST-EXC-06` | Period close/reopen: closed actuals immutable; reopen warned, audited, re-locked cleanly |
| `TST-WIN-09` | Crash recovery: interrupted jobs are listed with safe choices (resume/discard) |
| Migration guard | A project whose schema is **newer** than the app refuses to open with the documented message (no silent downgrade) |
| Migration determinism | Applying migrations twice is a no-op; the migration log is append-only |
| Integrity check | `doctor` detects and reports DB integrity problems, disk pressure and profile mismatches (`FR-XC-004`) |
| Cross-batch identity | `FactException` identity survives re-import, threshold change and mapping version change (`SEC`-style data integrity) |

## 12. Contract, API, CLI and UAT scripts

### 12.1 API contract tests (`TST-API-01`…`16`)

| Test | Asserts |
|---|---|
| `TST-API-01` | The standard envelope on every endpoint (`{status, data, warnings[], errors[]}` shape) |
| `TST-API-02` | Error mapping: every engine error maps to a catalog code + hint; no stack traces, no secrets, no raw paths |
| `TST-API-03` | Pagination: caps honoured, stable ordering, `has_more` correct, page-size abuse rejected |
| `TST-API-04` | Filter grammar parity with the UI (same filter → same rows) |
| `TST-API-05` | Loopback-only binding and per-launch token required on every endpoint (`SEC-004`/`008`) |
| `TST-API-06` | CORS/origin closed to the app origin; DNS-rebinding style requests refused |
| `TST-API-07` | **OpenAPI drift:** the generated spec matches the handlers; a changed route without a spec change fails |
| `TST-API-08` | Generated TS types compile and are used by the UI (no hand-written duplicates) |
| `TST-API-09` | Response size budget: payloads over the documented limit fail the test (`09` §11) |
| `TST-API-10` | Long-running jobs: `202` + poll contract, progress, cancel, terminal states |
| `TST-API-11` | CSV/stream downloads: correct BOM/line endings, correct row counts, cancel works |
| `TST-API-12` | `doctor`/health endpoints expose only non-sensitive information |
| `TST-API-13` | **CLI smoke:** every command runs with `--json`; exit codes `0`/`2`/`3`/`4` behave as documented; output is deterministic |
| `TST-API-14` | The cross-artifact harness endpoints return exactly the engine values (§7) |
| `TST-API-15` | GET has no side effects; POST idempotency keys behave |
| `TST-API-16` | Validation failures return field-level pointers, not prose only |

### 12.2 Non-functional API checks

Response-time budget per endpoint family (dashboard reads ≤ 2 s, drill ≤ 3 s, jobs enqueue < 500 ms),
plus a **no-N+1** check on grid endpoints (query counting), and an NFR-016 interaction check during jobs.

### 12.3 Contract with `26`

Every endpoint listed in `26` must have: a contract test, a generated type, a screen that consumes it,
and an entry in the OpenAPI document. An endpoint without a consumer is deleted, not shipped.

### 12.4 UAT scripts (`TST-UAT-01`…`06`, run by humans, `28` owns the mechanics)

| ID | Script |
|---|---|
| `TST-UAT-01` | The analyst reproduces one month's **manual BvA** in the app on the sanitised real month and diffs the two |
| `TST-UAT-02` | Tie-out worksheet: BvA totals, key account balances, and the exception list versus their current pack; differences classified per `28` (spec bug / mapping error / client data / rounding) |
| `TST-UAT-03` | The accounting-owner representative reviews exception wording and verdicts; any "this would mislead us" finding is an S2 or better |
| `TST-UAT-04` | Training walkthrough: a first-time user completes the month-end flow using only `22` |
| `TST-UAT-05` | Cold-start client pass: a fresh machine with only `22`/`29` — no author present |
| `TST-UAT-06` | Go-live rehearsal: installer + SHA-256 delivered, backup/restore verified on the client machine, diagnostics flow tested, rollback plan stated, support contact agreed |

## 13. CI, `scripts/check` and coverage

### 13.1 `scripts/check` — the gate command (exact composition)

| Step | Command (indicative) | Fails when |
|---|---|---|
| Format | `ruff format --check .` | Any file would be reformatted |
| Lint | `ruff check .` | Any rule violation |
| Types | `mypy app/engine` (strict) + `mypy app` | Any error |
| Import boundary | import-linter contract | `app/engine/**` imports the API/UI or a store handle |
| Unit + golden + rules + contract | `pytest -q --cov=app --cov-report=xml` | Any test failure |
| Coverage | thresholds in `pyproject.toml` | `app/engine` < 90 % or `app` < 75 % |
| UI types/lint | `tsc --noEmit`, `eslint .` | Any error |
| Secret scan | `scripts/check-secrets` | A candidate secret or key file appears |
| License scan | `scripts/check-licenses` | A dependency outside the allow-list |
| Docs link-check | `scripts/check-docs` | A dead cross-reference between docs |
| SBOM presence | `scripts/check-sbom` | The release SBOM artefact is missing at a release step |

`scripts/check --fast` skips coverage and the docs check for the inner dev loop; **the release and gate
run is always the full form**. The transcript is attached to every gate (`Addon 2 §F.2`, `Addon 3 §G.6`).

### 13.2 Coverage rules

| Rule | Detail |
|---|---|
| Engine bar | ≥ 90 % statements — money, rules, forecasts and parsers are all engine code, so this is where the bar matters |
| Backend bar | ≥ 75 % statements overall |
| Exclusions | Only generated migrations and `TYPE_CHECKING` blocks may be excluded, each listed in `pyproject.toml` with a comment; excluding an engine module is a spec change |
| Trend | Coverage is reported at every gate; a drop of > 2 points must be explained in the gate evidence |
| New code | Every new engine function arrives with its test in the same change |

### 13.3 CI

| Aspect | Rule |
|---|---|
| Where | A Windows runner where available (the artefact targets Windows); otherwise local execution with the transcript attached (`Addon 2 §F.3`) |
| What | `scripts/check` on every push; the perf harness nightly/weekly; Playwright on Windows before gates |
| Secrets | CI fails on a committed secret (`Addon 1 §I`); the scan is the same script as local |
| Artefacts | Coverage XML, `perf.json`, `acceptance_report.json`, Playwright report — retained per build and attached to the gate summary |
| Fresh clone | A clean `git clone` + documented bootstrap must build and pass `scripts/check` with no machine-local state (`Addon 3 §G.2`, `Addon 4 §I.2`) — a gate item, not a nice-to-have |

## 14. Defect management, evidence and the definition of done for a feature

### 14.1 Severities (`28` owns the workflow; this document owns the test response)

| Severity | Meaning | Test response |
|---|---|---|
| **S1** | Wrong numbers, crash, data loss, cross-artifact mismatch, secret exposure | Fix immediately; release blocked; the failing test is added **before** the fix |
| **S2** | A documented feature is broken; a workaround exists | Fix before release; regression test added |
| **S3** | Cosmetic or wording | Fix or defer with a recorded rationale |
| **S4** | Enhancement | Moves to `27` with a trigger |

### 14.2 Evidence formats (what a gate accepts)

| Evidence | Format | Produced by |
|---|---|---|
| Test run | `scripts/check` transcript + `pytest -ra` summary | local/CI |
| Coverage | `coverage.xml` + threshold result | pytest-cov |
| Rule acceptance | `acceptance_report.json`/`.md` | `scripts/acceptance` |
| Performance | `perf.json` + baseline diff | `scripts/perf` |
| Cross-artifact | `cross_artifact.json` | §7 harness |
| E2E | Playwright HTML report + video/screenshots | Playwright |
| Windows manual | Signed checklist with screenshots | §9.4 |
| Migration | Before/after hashes + migration log | `TST-E2E-05` |

### 14.3 Demo recipe (Definition of Done, `Addon 2 §F.5`)

Every feature's `SESSION_LOG` entry includes a 3–6 step recipe on sample data (steps + expected result)
so a reviewer can verify it in minutes. A feature without its recipe does not close.

## 15. The five quality gates — authoritative checklists (58 checks)

These restate the five gate sources **exactly in substance**, each with an ID, the artefact that proves
it and the status as of this draft. `00_INDEX` §9 is the tracker of record; `CHANGELOG` records approvals
(`Addon 4 §E.2`). Status legend: `✅` met by a written doc · `⬜` open at the time of writing.

### 15.1 `GATE-01` — Kickoff §5 checklist (9 checks)

| ID | Check | Provable by | Status |
|---|---|---|---|
| `GATE-01-01` | Every FR is numbered, testable, with acceptance criteria; zero blocking TBDs | `02` + `20` | ✅ |
| `GATE-01-02` | `05` has worked examples with exact numbers: MTD/YTD variance, variance %, favourability, PY comparison, rounding, every forecast method | `05` §12 (F1–F14) | ✅ |
| `GATE-01-03` | `06` has ≥ 15 fully specified rules, each with a planted test case | `06` (24 rules, 40 plantings) | ✅ |
| `GATE-01-04` | `08` covers every screen incl. empty/loading/error/first-run, written for a non-technical user | `08` (43 screens, §17 matrix) | ✅ |
| `GATE-01-05` | `12` defines 4–6 slides exactly, slide by slide, editable/native, brand handling | `12` (6 slides, 29 placeholders) | ✅ |
| `GATE-01-06` | `15` is a step-by-step script producing a working installer on a clean Windows 11 machine | `15` | ⬜ |
| `GATE-01-07` | NFR numbers stated | `14` §3 (`NFR-001`…`016`) | ✅ |
| `GATE-01-08` | `18` lists every unconfirmed item | `18` (with `21` `Q-` items) | ✅ (doc side; `Q-` items with `21`) |
| `GATE-01-09` | `20` links every FR to at least one future test | `20` (156 rows; every FR ≥ 1 test) + `14` §4 | ✅ |

### 15.2 `GATE-02` — Addon 1 §O deltas (12 checks)

| ID | Check | Provable by | Status |
|---|---|---|---|
| `GATE-02-01` | Docs 21–25 exist and are complete; every questionnaire item has a decision or a labelled default | `21`–`25` | ✅ (docs `21`–`25` exist with the standard headers; all 21/21 `Q-` items carry a labelled default; `25` registers the consequences) |
| `GATE-02-02` | All Addon 1 §C.2 additions are present in the owning docs; `CHANGELOG` shows the integration | `CHANGELOG` + docs | ✅ (through `13`) |
| `GATE-02-03` | Tabletop walkthrough executed and recorded — every month-end step maps to a screen/rule/export | `SESSION_LOG` entry (Phase 0 close) | ✅ (`SESSION_LOG` "Tabletop walkthrough": 24 steps, each mapped to its screen, rule, output and owning section, through pack issuance and re-issue) |
| `GATE-02-04` | Excel hardening list: each quirk has a documented handle-or-reject behaviour with error copy | `04` (32 checks, 59 messages) | ✅ |
| `GATE-02-05` | OneDrive/storage decision made, with its test case listed in `14` | `09` `ADR-004` + `TST-WIN-06` | ✅ |
| `GATE-02-06` | SmartScreen/signing decision is an ADR with a non-technical-user mitigation path | `09` `ADR-003` | ✅ |
| `GATE-02-07` | Upgrade/migration test case exists and names the fixture (a real prior-version project) | `TST-E2E-05`, `24` | ✅ (`24` §6.3 names the fixture path, creation/refresh rules and the never-edit rule; the first fixture is created from the first released build) |
| `GATE-02-08` | Injection test case (planted malicious description) exists in `14` | `TST-SEC-14` | ✅ |
| `GATE-02-09` | License allow-list, secret-scan and SBOM steps documented; `THIRD_PARTY_LICENSES.txt` planned in the installer manifest | `13` §12, `15`, `24` | ✅ (doc side) |
| `GATE-02-10` | End-user guide outline (task-structured) approved-ready; training outline exists | `22`, `23` | ✅ (`22`: 21 tasks, 43-screen map, 60-min training outline, screenshot contract; `23`: diagnostics workflow, incident playbook, escalation ladder) |
| `GATE-02-11` | Backlog list (Addon 1 §N) recorded in PRD/roadmap so nothing is dropped | `27`, `01` §5 | ✅ (every Addon 1 §N item maps to a `27` row: connectors `BL-008`, Power BI `BL-009`, email/Teams distribution `BL-019`, advanced forecast methods `BL-018`, headcount/FTE `BL-016`, budget version-compare `BL-020`, commentary carry-forward `BL-021`, multi-client licensing `BL-023`, RBAC `BL-004`/`BL-035`, localisation `BL-022`, auto-update `BL-007`, dashboard PDF export `BL-036` — the one §N item with no `01` §6.2 twin, added in the approval pass) |
| `GATE-02-12` | NFR numbers from Addon 1 §L present and agreed in-doc | `14` §3 | ✅ |

### 15.3 `GATE-03` — Addon 2 §I deltas (12 checks)

| ID | Check | Provable by | Status |
|---|---|---|---|
| `GATE-03-01` | Addon Coverage Matrix exists; every kickoff + Addon 1 + Addon 2 row is integrated | `00_INDEX` §4 | ✅ (kickoff + Addon 1 rows; all Addon 2 rows integrated — `A2-E` through the `08`/`12` token contract) |
| `GATE-03-02` | `26` complete; OpenAPI-as-source-of-truth and type generation documented; error envelope + pagination | `26` | ✅ (`26` §2 envelope/pagination/filters, §5 catalogue, §6 generation workflow, §7 contract tests, §10 reverse index) |
| `GATE-03-03` | Engine-boundary rule and CLI command list documented in `09` with exit codes | `09` §4/§5 | ✅ |
| `GATE-03-04` | `ADR-002` written; every library traceable to `ADR-001`/`002` | `09` | ✅ |
| `GATE-03-05` | Data-volume rule and config layering documented with test cases in `14` | `09` §11/§12 + `TST-API-09`, `TST-UI-15`, `TST-UI-20` | ✅ |
| `GATE-03-06` | Exception identity/re-run semantics fully specified with a worked scenario | `06` §D.1 + §5.5 here | ✅ |
| `GATE-03-07` | Forecast-accuracy and TTM formulas have worked examples in `05` | `05` §9 | ✅ |
| `GATE-03-08` | Screen inventory exists in `08`; the traceability chain includes screen IDs and API endpoints | `08`, `20` (chain complete), `26` (endpoint catalogue) | ✅ (chain in `20`; the 95-endpoint catalogue and its reverse index are final in `26` §3/§10) |
| `GATE-03-09` | PPT character budgets defined per placeholder | `12` §3.4 | ✅ |
| `GATE-03-10` | Coverage bars, `scripts/check` contents and the E2E list recorded in `14` | this document §9, §13 | ✅ |
| `GATE-03-11` | PRD scope decisions and disclaimer text resolved | `01` §15, `DEC-*` | ✅ |
| `GATE-03-12` | AI usage log + draft provenance + number-mismatch stance specified | `10` §10/§11 | ✅ |

### 15.4 `GATE-04` — Addon 3 §J deltas (12 checks)

| ID | Check | Provable by | Status |
|---|---|---|---|
| `GATE-04-01` | Docs 27 and 28 exist and are complete; backlog seeded from Addon 1 §N + §E.3 | `27`, `28` | ✅ (`27` seeds all 34 items from `01` §6.2 / `11` §14 / `13` §15; `28` carries the DoD, the three gates and the sign-off) |
| `GATE-04-02` | Coverage Matrix extended with Addon 3 rows; all integrated | `00_INDEX` §4 | ⬜ (every Addon 3 row integrated except `A3-F`'s `sample-data/malformed/` corpus; `A3-B`/`A3-G`/`A3-H` complete with `27`/`28`) |
| `GATE-04-03` | Four full initial prompt texts exist in `10` with worked examples | `10` §4/§5 | ✅ |
| `GATE-04-04` | Mapping Review Queue, commentary lock-on-issue and the issuance register fully specified | `02`, `03`, `08` | ✅ |
| `GATE-04-05` | Chart inventory and centralized conditional-format rules present in `08` | `08` §13/§14 | ✅ |
| `GATE-04-06` | Output conventions present in `11` and `12`; cross-artifact test specified in `14` | `11` §3, `12` §3.9, this doc §7 | ✅ |
| `GATE-04-07` | Negative file corpus exists in `sample-data/malformed/` with expected message IDs | §6.3 (corpus built with sample data) | ⬜ (defined in §6.3 with 16 cases and their expected `import.*` slugs; the files are the Phase 0 build step, deferred by the session's docs-only scope) |
| `GATE-04-08` | Data-quality score formula has a worked example in `05` | `05` §8 | ✅ |
| `GATE-04-09` | Success metrics, IP/licensing stance and the forced in/out list resolved in the PRD | `01` §16, §5 | ✅ |
| `GATE-04-10` | Error-code catalog families defined in `26`; message-catalog rule in `08` | `26`, `08` §16 | ✅ (11 families + codes in `26` §5; shape and wording in `08` §16) |
| `GATE-04-11` | Project DoD, UAT mechanics, defect severities, go-live checklist and sign-off template in `28` | `28` | ✅ (`28` §2 DoD · §3 `S1`–`S4` + `DEF-` log · §4 pilot · §5 UAT · §6 the 22-item go-live checklist · §7 sign-off) |
| `GATE-04-12` | "Decided" section active in `18`; `ADR-000` index lists `ADR-001`/`002` (+ any new) | `18`, `09` | ✅ |

### 15.5 `GATE-05` — Addon 4 §K deltas (13 checks)

| ID | Check | Provable by | Status |
|---|---|---|---|
| `GATE-05-01` | Coverage Matrix has Addon 4 rows; all integrated | `00_INDEX` §4 | ✅ (through `13`) |
| `GATE-05-02` | Standard doc header on every doc; TL;DR ≤ 15 lines | every doc; doc-14 header check script | ✅ |
| `GATE-05-03` | Source-of-Truth Matrix in `00_INDEX`; no duplicated formula/threshold; conflict rule documented | `00_INDEX` §5 + the conflict rule | ✅ |
| `GATE-05-04` | Quote-before-code and FR-citation rules written into `19` | `19` | ✅ |
| `GATE-05-05` | Every FR has P0/P1/P2; never-cut list and cut process in `02`/`16` | `02` priorities, `16` | ✅ (priorities; process with `16`) |
| `GATE-05-06` | Per-phase estimates in `16` | `16` §7 (per-phase + per-epic ideal days) | ✅ |
| `GATE-05-07` | `29_CLIENT_REQUIREMENTS_PACK.md` complete and jargon-free; sign-off block present | `29` | ✅ (`29` §1–§15: plain language with no requirement codes, 17 decisions each with a recommendation, the ask/timing table, timeline, UAT/training, the verbatim disclaimer and the §14 sign-off block) |
| `GATE-05-08` | Approval-recording convention and post-approval impact rule in `19` | `19`, `CHANGELOG` | ✅ |
| `GATE-05-09` | Real-data pilot gate defined in `28` with tie-out worksheet + classification log | `28` | ✅ (`28` §4: `GATE-13` preconditions, the four-class difference taxonomy, the tie-out worksheet template and the exit criteria) |
| `GATE-05-10` | Tolerance policy in `05`; full edge-case matrix in `02`/`14` with message IDs | `05` §6, this doc §6 | ✅ |
| `GATE-05-11` | Sample-data watermark + project-type flag + non-delivery rule specified | `03`/`09` + §16 here | ✅ |
| `GATE-05-12` | Spike policy, fresh-clone gate, code-health rules, storage math in `09`/`14`/`17` | `09` §14–§15, §13 here, `17` | ✅ |
| `GATE-05-13` | Key-rotation procedure in `13` | `13` §5.3 | ✅ |

## 16. Test-data governance and sample-data integrity

| Rule | Detail |
|---|---|
| Synthetic only | `sample-data/` is generated from a fixed seed; no client file ever enters it (`SEC-007`) |
| Watermark and flag | The sample project carries `project_type = sample`, a visible "SAMPLE DATA" banner, and a watermark on every generated artefact (`Addon 4 §H`) |
| Import refusal | Client imports into a sample project are refused (`FR-IMP-031`); sample data is never mixed into a client project |
| Never delivered | Sample files are excluded from every client deliverable, asserted at the go-live checklist (`28`) |
| Golden files | Frozen; changes follow the spec-first rule with `CHANGELOG` evidence (`Addon 1 §M.5`) |
| Fixture hygiene | Every fixture in `tests/` is synthetic or sanitised; accidental client data in a fixture is an S1 process failure and a security incident note |
| Regeneration | `sample-data` is re-generatable at any time; the installed app can restore the bundled sample (`FR-XC-004`) |
| Licence files | Fixture fonts/images must be redistributable; anything else is rejected at review (`SEC-045`) |

## 17. Change control and obligations

### 17.1 Obligations this document places elsewhere

| Obligation | Owner |
|---|---|
| The gate checklist texts stay identical in substance here and in the five gate sources | `00_INDEX` §9 (tracker), this doc (authoritative text) |
| FR → spec → screen → API → test chain filled for every FR using the test IDs of §4 | `20` |
| Every endpoint has a contract test, a type and a consumer | `26` |
| UAT mechanics, defect workflow and go-live use the UAT scripts of §12.4 | `28` |
| `scripts/check` composition, coverage bars and the CLI smoke list implemented as specified | `17`, `09` §5 |
| Fixtures and the negative corpus are generated by `sample-data` with the fixed seed | `sample-data/` (Phase 0 build step) |
| Manual Windows checklist executed and signed at each gate | `15` |
| Prior-version project fixture maintained for upgrade tests | `24` |
| Every feature's demo recipe recorded | `19` (DoD) |

### 17.2 Changes to this document

| Change | Requires |
|---|---|
| A new test family or a renumbering | `00_INDEX` §8 registry update first; `20` and the owning doc updated in the same pass |
| An NFR number change | Explicit justification in-doc plus a `CHANGELOG` entry (the spec allows adjustment only with recorded justification) |
| A coverage-bar change | A spec change with the user's recorded approval — never a code change |
| A gate checklist wording change | The source gate (kickoff/Addon) is authoritative; a divergence is fixed in `14`, and `00_INDEX` §9 is updated |
| A new golden fixture | `05` §12 first, then the test; the fixture is committed with its expected values |
| A manual checklist item removal | Rationale + replacement automation evidence, recorded in `CHANGELOG` |

**Frozen constants owned by this document:** the `NFR-001`…`016` targets and measurement protocol (§3) ·
the family counts and naming (§4) · the acceptance bars (§5.3) · the edge-case matrix rows and message
IDs (§6) · the cross-artifact comparison set and failure class (§7) · the regression threshold (§8.3) ·
the `scripts/check` composition and coverage bars (§13.1/§13.2) · the evidence formats (§14.2) · the 58
gate checks (§15).



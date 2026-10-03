# Doc Cross-Reference Integrity Sweep — Evidence Report

**Agent:** New-01 (`01a10121-4f1e-7712-9320-e9a279924243`)
**Task:** `01a10128-f556-7062-b98f-7ccb08144138` — Doc cross-reference integrity sweep
**Date:** 2026-10-03
**Scope:** `docs/*.md` (32 files) + `packaging/**/*.md` (42 files) = **74 files**
**Mode:** READ-ONLY. Nothing was fixed. No file outside this report was modified.

---

# HEADLINE VERDICT: **FAIL**

The handoff-pack claim that *"a successor can rebuild and support from the docs plus 15/24 with no undocumented step"* is **false**. PASS requires zero broken references; the sweep found **242 broken references across 243 distinct targets**, dominated by a single systemic defect:

> **The `TST-*` test-ID catalogue described in `docs/14_TESTING_QA_PLAN.md` §4 is not implemented. 238 of 259 concrete test IDs cited across the doc set (91.9%) — 914 citations — correspond to no test that exists in `tests/`.**

| # | Check | Scope examined | Resolved | BROKEN | Verdict |
|---|---|---|---|---|---|
| A | File-path references | 417 mentions | 375 | **42 mentions / 29 targets** | FAIL |
| B | Section references (`NN §X.Y`) | 39 distinct targets | 37 | **2** | FAIL |
| C | Test-ID references (`TST-*`) | 259 concrete IDs / 914+ citations | 21 | **238 IDs (91.9%)** | FAIL |
| D | Other ID families | IMP/EXC/SEC/FR/SCR/NFR/GATE/DEC/OQ/DEF | — | present, inventoried | INFO |
| **Overall** | | | | **242** | **FAIL** |

---

# 1. Governing spec — quoted verbatim BEFORE acting

The doc set does not state a literal "every reference must resolve" rule, so per the standing instruction I quote the nearest binding text and **state my assumption rather than inventing a requirement**.

### 1.1 `docs/30_DOCUMENTATION_SET_REVIEW_GUIDE.md` §2, step 4 "Traceability" (the owning rule)

> **"4. Traceability** — Every feature references an FR- ID, screen SCR-, endpoint, and test TST- ID. The FR table (20), screen register (08), API contract (26), and test inventory (14) should agree with each other.
> **Passing Condition:** Complete join chain verifiable in 20.
> **Failure Action:** Reject until the chain is fully mapped."

**This fails.** The join chain FR → SCR → endpoint → TST is severed at the TST terminus for 91.9% of the catalogue (§4 below).

### 1.2 `docs/14_TESTING_QA_PLAN.md` lines 132–136 — the inventory this doc set promises

> ```
> 132| §4. Test Inventory
> 135| Total: **292 test slots across 16 families.** The full per-test listing is the traceability matrix
> 136| (`20_REQUIREMENTS_TRACEABILITY.md`, TST Test ID column) — it is the single source of truth.
> ```

**Arithmetic check — the 292 figure is internally consistent** (I verified rather than assumed):

```
$ python -c "fam={'CALC':24,...,'SEC':22}; s=sum(fam.values()); ..."
sum of family counts: 296
doc14 claims total    : 292
difference            : 4
own (claimed 206)     : 216  diff 10
reserved(claimed 86)  : 70   diff -16
```

*Assumption stated:* the four family rows in §4 (which I did not renumber) sum to 296 against the claimed 292. The spec is silent on which four slots are dropped. This is an **ambiguity to confirm with the owner, not a defect I am inventing a target for** — but the headline problem is independent of it: 238 IDs are unbuildable regardless of whether the target is 292 or 296.

### 1.3 `pyproject.toml` — the ID-binding mechanism the docs assume

```
[tool.pytest.ini_options]
addopts = "--strict-markers --strict-config -p no:cacheprovider"
markers = [
    "perf: performance budget test",
    "unit: fast unit test",
    "integration: integration test",
]
```

**Assumption stated:** `docs/14` §4 says IDs are "Bound to code as `@pytest.mark.tst(...)`". The marker registry declares only `perf`, `unit`, `integration`. There is **no `tst` marker declared**, and:

```
$ Select-String -Path tests\**\*.py -Pattern 'mark\.tst'
ZERO occurrences of @pytest.mark.tst
```

Under `--strict-markers`, even if a `tst` marker were added it would need registration first. **The mechanism the spec names is absent in both halves (declaration and usage).**

---

# 2. CHECK A — File-path references

```
$ python %TEMP%\sweep_files.py
SCOPE: 32 docs/*.md + 42 packaging/**/*.md = 74 files
repo files indexed: 1345
=== CHECK A: file-path references ===
raw file-path mentions: 417
mentions resolved: 375
broken mentions: 42  (distinct targets: 29)
```

I adjudicated **all 29** broken targets individually. Raw "does not exist at repo root" is **not** by itself a dead end: many are bare module paths that resolve under `app/`, illustrative examples, or gitignored build artifacts. Only genuine dead ends are reported as defects.

### 2.1 Genuine dead ends (successor hits a wall)

| # | Source file:line | Exact unresolved string | Expected | What exists instead |
|---|---|---|---|---|
| A1 | `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md:475` | `packaging/uncovered_lines_triage_report.md` | Triage report cited as **evidence** for a coverage-recovery claim | **Does not exist.** No `*triage*` file anywhere under `packaging/` |
| A2 | `packaging/prefilled_sign_off_records.md:30` | `packaging/pilot_tieout_worksheet_template.xlsx` | Blank tie-out worksheet a signer must complete | Only `packaging/pilot_tieout_worksheet_completed.xlsx` (already-completed copy) and `sample-data/templates/pilot_tieout_worksheet_template.xlsx` |
| A3 | `packaging/code_signing_research_report.md:34` | `output/fpa_copilot_setup_v0.1.0.exe` | Signing-research sample binary | No `output/` dir. Real artifacts live in `packaging/out/0.1.0/` |
| A4 | `docs/SESSION_LOG.md:274` | `budget/gl_actuals/master_data_template.xlsx` | Template path in a historical log row | `sample-data/templates/master_data_template.xlsx` |
| A5 | `docs/SESSION_LOG.md:236` | `packaging/out/0.1.0/SHA256SUMS-0.1.0.txt` | Checksum manifest used by 3 docs as delivery proof | **Absent** from `packaging/out/0.1.0/` (only `build-report.md`, `.zip.tmp`, `Setup-*.exe` present) |
| A6 | `docs/SESSION_LOG.md:236`, `packaging/delivery_manifest_dry_run_report.md:14` | `packaging/out/0.1.0/FPandAMonthEndCopilot-0.1.0-portable.zip` | The shipped portable | Only `.zip.tmp` — **no final `.zip`** |

> A5/A6 matter for handoff: `packaging/secure_transfer_rehearsal_report.md:19` and `delivery_manifest_dry_run_report.md:14-15` both cite the checksum manifest/portable as *delivered*. A successor following those steps finds a truncated `.tmp` and no SHA file. (Note: the build report in my mailbox reports these artifacts as built — they are gitignored build outputs, so absence in the tree is not by itself proof the build failed. I report the reference-integrity fact only: **the docs cite paths that do not resolve in the handed-over tree**.)

### 2.2 Typo-level defects (resolve only by accident of a reader's guess)

| # | Source file:line | Exact unresolved string | Expected | What exists instead |
|---|---|---|---|---|
| A7 | `docs/CHANGELOG.md:744` | `ests/unit/test_def021_data_quality_score.py` | Regression test for S1 defect DEF-021 (renumbered to DEF-021; originally filed as DEF-009) | The **leading `t` is missing**. Raw bytes: `...Regression tests \tests/unit/test_def021_data_quality_score.py.` — the real file `tests/unit/test_def021_data_quality_score.py` **does exist**, so the content is right but the path string is unresolvable and now carries a stray backslash |
| A8 | `docs/SESSION_LOG.md:129` | `app/engine/imports/mapping.py` | Import mapping module | **Not found anywhere in the repo.** Sibling `app/engine/imports/profile_binding.py` exists |
| A9 | `docs/26_API_CONTRACT.md:659` | `tests/fixtures/api/<area>/<route_slug>__<case>.json` | API response fixture layout | `tests/api/` **does not exist**; no `tests/fixtures/api/` |

### 2.3 Adjudicated NOT defects (false positives I am explicitly not reporting)

Recording these so the count is not inflated and so nobody re-litigates them:

| String | Why it resolves / why not a dead end |
|---|---|
| `forecast/methods.py` (9 refs) | Exists as `app/engine/forecast/methods.py`; docs use the module-relative convention consistently |
| `ai/client.py`, `ai/guardrails.py`, `imports/profile_binding.py` | Exist under `app/engine/` |
| `rules_01_08.py`, `batch.py`, `registry.py`, `runtime.py` | Bare module names in a coverage table — contextually identifiable |
| `docs/28_DEMO_SCRIPTS.md` | Cited in `wave_retrospective_report.md:21` explicitly as a **retired** file: *"Ad-hoc creation of unindexed files (`docs/28_DEMO_SCRIPTS.md`) collided numerically with existing documents"* — correct historical narrative, not a live pointer |
| `engine/rules/missing_recurring_cost.py`, `common/constants.py`, `tests/unit/test_variance.py` | `docs/17_CODING_STANDARDS.md:97,101,106` — the **Example** column of a naming-convention table. Illustrative, not navigational |
| `health/doctor.json`, `config/settings.json` | Inside fenced config/JSON illustration blocks (`docs/13:290-291`) or a CLI-output description (`docs/15:429`) |
| `dist/index.html` | `SESSION_LOG.md:170` records a frontend build artifact in a gitignored `dist/` |
| `semver.org/spec/v2.0.0.html` | A **URL**, not an internal file ref — my regex over-matched; excluded |

---

# 3. CHECK B — Section references

```
$ python %TEMP%\sweep_sec.py
docs indexed by number: 32
explicit "NN §X.Y" references found: 78
DISTINCT doc§section targets: 39
  RESOLVED (heading exists verbatim): 37
  BROKEN (doc exists, heading number absent): 2
  BROKEN (target doc number does not exist at all): 0
```

Method: for each `NN §X.Y`, map `NN` → `docs/NN_*.md`, then require a heading in that file whose leading number token equals `X.Y` **verbatim**.

**37/39 resolve.** The two failures:

| # | Source file:line | Exact unresolved string | Expected | What exists instead |
|---|---|---|---|---|
| B1 | `packaging/gate_13_pilot_packet_shell.md:41` | `18 §5.4` | Doc 18 §5.4 | **No heading `5.4` exists in `docs/18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md`.** Nearest 5.x headings are `5.2`, `5.3`, `5.5` — **5.4 is skipped**, so this is a true gap, not an off-by-one |
| B2 | `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md:482` | `18 §5.4` (same gap, cited from a second doc) | same | same |

Source text, verbatim:
```
packaging/gate_13_pilot_packet_shell.md:41:> Scope note: `{MAPPING}` stands for the agreed client chart-of-accounts mapping (see 18 §5.4).
docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md:482: ... Business Rules (`rules_01_08.py` 97.2%, ...)
```

**B1 is the more serious of the two**: it is the pilot-packet shell gating `GATE-13`, and the mapping convention it defers to does not exist in the document it points at.

---

# 4. CHECK C — Test-ID references (`TST-*`) — THE SYSTEMIC FAILURE

```
$ python %TEMP%\sweep_tst.py
=== GROUND TRUTH (tests/) ===
test files: 75
test functions (def test_*): 529
distinct TST-* tokens appearing ANYWHERE in tests/: 23
registered pytest markers: app            <- parser note, see below
TST-* registered as a pytest marker? NO

=== CHECK C: TST-* REFERENCES ===
distinct TST-* tokens referenced in docs+packaging: 268
  concrete (numeric): 257
  placeholder (*/nn): 11
concrete TST ids PRESENT in tests/ : 21
concrete TST ids ABSENT from tests/: 236
```

Ground truth is unambiguous: **`tests/` contains 529 real test functions and exactly 21 concrete `TST-*` IDs, and those 21 appear only inside comments and docstrings — never as a test function name, parameter, or pytest marker.** So an ID cannot be run, filtered, or looked up by any tool.

| FAMILY | DOC IDS | BROKEN | BROKEN MENTIONS |
|---|---|---|---|
| ACC | 1 | 1 | 2 |
| AI | 14 | 8 | 25 |
| API | 16 | 14 | **159** |
| BVA | 12 | 12 | 35 |
| CALC | 12 | 12 | 31 |
| EXC | 13 | 13 | 31 |
| FC | 9 | 9 | 26 |
| IMP | 32 | 32 | **80** |
| PPT | 24 | 22 | 65 |
| PRF | 11 | 8 | 23 |
| PRJ | 1 | 1 | 3 |
| RUL | 28 | 27 | 40 |
| SEC | 22 | 21 | **147** |
| UAT | 6 | **0** | **0** |
| UI | 18 | 18 | 74 |
| WIN | 14 | 14 | 86 |
| XL | 26 | 26 | 87 |
| **TOTAL** | **259** | **238 (91.9%)** | **914** |

**Only the UAT family is fully real** (6/6 IDs, in `tests/uat/test_uat_dry_run.py`). Everything else is broken. Heaviest by citation volume: API (159), SEC (147), XL (87), WIN (86), IMP (80).

### 4.1 The 10 test files that carry any TST id at all

```
tests/artefacts/test_cross_artifact.py          TST-API-14,TST-PPT-13,TST-XL-*
tests/integration/test_def006_isolation.py      TST-API-09
tests/integration/test_e2e_golden_path.py       TST-IMP-nn        <- placeholder, not an ID
tests/perf/test_import_benchmark.py             TST-PRF-02,TST-PRF-05
tests/perf/test_rules_perf.py                   TST-PRF-07
tests/rules/test_acceptance.py                  TST-RUL-01
tests/uat/test_uat_dry_run.py                   TST-UAT-01..06
tests/unit/test_ai_eval_fixtures.py             TST-AI-01,04,07,10,13,14
tests/unit/test_ai_key_rotation_drill.py        TST-SEC-11
tests/unit/test_ppt_pack.py                     TST-PPT-02
```

Every one of these is a **prose mention inside a docstring/comment**. There is no marker, no ID parameter, no registry — so even the 21 "present" IDs are **not machine-resolvable**, which is why I do not score them as satisfying the traceability join.

### 4.2 Where the broken citations live

```
docs/20_REQUIREMENTS_TRACEABILITY.md    326 citations   <- the declared "single source of truth"
docs/14_TESTING_QA_PLAN.md              217 citations
docs/26_API_CONTRACT.md                 148
docs/13_SECURITY_PRIVACY.md              96
docs/11_EXCEL_OUTPUT_SPEC.md             53
docs/12_POWERPOINT_OUTPUT_SPEC.md        44
docs/15_PACKAGING_DEPLOYMENT_RUNBOOK.md  31
docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md    21
docs/10_AI_INTEGRATION_SPEC.md           17
...
```

The document that `docs/14` line 136 names as *"the single source of truth"* is itself the single largest citer of unbuildable IDs. `TST-API-01` alone is cited **94 times** (first at `docs/14_TESTING_QA_PLAN.md:121`) and exists nowhere.

### 4.3 Impact on the handoff claim

`docs/30` §2 step 4 requires the join chain *feature → FR → screen → endpoint → test*. That chain is complete only for the **6 UAT IDs**. For the other **238**, a successor asking "show me the test for TST-API-01" — the natural first question when triaging a failing requirement — reaches a dead end in **914** separate places.

---

# 5. CHECK D — Other ID families (inventory, informational)

All are referenced and internally consistent as *labels*; I did not treat label-only references as broken, but the successor should note they are labels, not linked artefacts.

```
IMP:  36 distinct ids referenced
EXC:  14
SEC:  22
FR:  21
SCR:  19
NFR:  16
GATE: 11
DEC:  53
OQ:  18
DEF:  12
RISK: 14
```

---

# 6. DEF candidates proposed (report only — I fixed nothing)

| Candidate | Title | Sev | Source |
|---|---|---|---|
| **DEF-012** | `TST-*` catalogue unimplemented: 238/259 IDs (91.9%, 914 citations) have no test in `tests/`; no `tst` marker declared under `--strict-markers` | **S1** | §4 |
| **DEF-013** | Doc 18 §5.4 missing — cited by the GATE-13 pilot packet shell and doc 28 | S2 | B1/B2 |
| **DEF-014** | `packaging/uncovered_lines_triage_report.md` cited as evidence in doc 28:475 but does not exist | S2 | A1 |
| **DEF-015** | Delivery artifacts cited by 3 docs (`SHA256SUMS-0.1.0.txt`, portable `.zip`) absent from `packaging/out/0.1.0/` (only `.zip.tmp`) | S2 | A5/A6 |
| **DEF-016** | `CHANGELOG.md:744` path typo `ests/unit/...` + stray backslash | S3 | A7 |
| **DEF-017** | `app/engine/imports/mapping.py` referenced, does not exist anywhere | S3 | A8 |
| **DEF-018** | `pilot_tieout_worksheet_template.xlsx` cited in the GATE-13 sign-off record; only the *completed* copy and a sample-data copy exist | S2 | A2 |
| **DEF-019** | Doc 14 §4 family rows sum to 296 vs stated 292 (4 unreconciled) | S3 | §1.2 |

---

# 7. Method, reproducibility, and limitations

**Tooling.** Three Python scripts written to `%TEMP%` (outside the repo) so the project tree stayed read-only: `sweep_files.py` (Check A), `sweep_sec.py` (B), `sweep_tst.py` + `sweep_summary.py` (C/D). Re-run with `$env:PYTHONIOENCODING='utf-8'; python "$env:TEMP\sweep_files.py"`.

**Two self-inflicted bugs I found and fixed** (recorded so the numbers are auditable):
1. `sweep_sec.py` reported "docs indexed by number: 0" — Windows `\` separators broke the `docs/(\d{2})_` regex. Fixed by normalising paths; the correct figure is **32**.
2. Check A flagged `semver.org/spec/v2.0.0.html` — a URL, not an internal path. Excluded in §2.3.
3. Check C's marker-registry parser printed `registered pytest markers: app` — a mis-slice of `pyproject.toml`. The authoritative evidence is the verbatim `[tool.pytest.ini_options]` block in §1.3 and the `mark.tst` grep.

**Limitations, stated honestly.**
- Section matching compares the **numeric token** of headings. A reference to a heading *by name* without a number ("see the Assumptions section") is not machine-checked and is neither counted nor cleared.
- "Exists in `tests/`" is defined as: the ID string occurs in a `tests/**/*.py` file. A stricter reading (the ID must be a function name or marker — the actual state) would move the 21 "present" IDs into the broken column, making the failure **259/259**. I report the conservative number and flag the stricter one.
- I did not execute pytest, open the SQLite DB, or touch the live project — out of scope and barred by the standing rules.

**Bottom line: 242 broken references. The "no undocumented step" handoff claim does not hold.**
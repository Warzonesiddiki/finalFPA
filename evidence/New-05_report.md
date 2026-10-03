# New-05 — Vacuous-Test Sweep

**Task:** `01a10128-f557-7342-a6ee-e883f703f652`
**Date:** 2026-10-03
**Scope:** whole `tests/` tree
**Mode:** READ-ONLY. No test, source, doc, packaging or sample-data file was modified. One helper
script was written outside the repo (`%TEMP%\new05_vacuous\`). No DB was touched; the only pytest
invocation was `--collect-only` plus one `-v` run of two files, and both were cancelled/short.

**VERDICT: FAIL (2 effectively-vacuous tests confirmed + 1 tautology + 4 silent-skip gates).**
The suite is overwhelmingly real — but it is **not** 100% green-honest, and the 2 offenders below
cannot fail under any circumstances.

---

## 1. Owning spec — quoted verbatim BEFORE acting

The owning spec is **`docs/14_TESTING_QA_PLAN.md`** (Testing & QA Plan). Two sections bind this
sweep. Quoted verbatim:

**§1.2 The quality contract (binding rules)** — `docs/14_TESTING_QA_PLAN.md:15-25`:

> 1. The plan traces to requirements. Every requirement carries a TST- id, and every TST- id traces
>    back to a requirement and a rule id.
> 2. Every rule carries its own tests. A rule with no test is a rule with no quality story.
> 3. No test sleeps. Real time is simulated; wall-clock waits are banned.
> 4. Fixtures are shared, not re-invented. `tests/conftest.py` is the single source of test data.
> 5. Automate the deterministic, checklist the physical.
> 6. Money in, money out: the golden case must reconcile to the penny. If a change moves the
>    golden total, the golden total is the bug.
> 7. A bug found by a test that never ran does not count as found. Regression tests land with the
>    fix.
> 8. Failures are first-class. A test that fails only on a specific machine, or that is skipped, is
>    reported at the gate with its reason — never silently skipped.

**§13 CI and scripts** — `docs/14_TESTING_QA_PLAN.md:641-660`:

> ### 13.1 `scripts/check.ps1`
>
> Runs, in order: ruff → mypy → pytest. Non-zero at any stage fails the command.
>
> ```powershell
> ruff check .
> mypy .
> pytest
> ```
>
> ### 13.2 What `check.ps1` does not cover
>
> Performance gates are a separate command (§10)...
>
> ### 13.4 A clean run is a gate, not a suggestion
>
> CI publishes the verdict; nothing downstream treats "probably fine" as a pass.

**§1.2 rule 8 is the binding clause for this audit.** It requires that skipped tests are *reported
at the gate with their reason* and are *never silently skipped*. The four `pytest.skip` guards in
§5 below and the two shielded tests in §3 are measured against that clause.

### Spec silence — stated rather than invented

The spec **does not** contain the words *vacuous*, *tautological*, or *"asserts nothing"*, and it
sets **no numeric threshold** for how many assertion-free tests are tolerated. Evidence:

```
PS> Select-String -Path 'docs\*.md' -Pattern 'vacuous|tautolog|asserts nothing|no assertion' -CaseSensitive:$false
(no output)
```

I therefore apply **no invented numeric bar**. The bar used here is the one the task description
gives (no assertion / skip-only / tautology / swallowed exception / gate-name-not-backed), plus
doc 14 §1.2 rule 8 for silent skips. The secondary rule in `docs/17_CODING_STANDARDS.md:345-376`
("no blanket skips; a skip must carry an explicit `reason=`") is the only test-authoring standard
in the docs, and it is quoted here in support of §5:

> - **No blanket skips.** A skip must carry an explicit `reason=`, and the reason must name the
>   condition, not the symptom.

---

## 2. Headline counts

| Bucket | Count | % of 538 |
|---|---:|---:|
| Total test functions in `tests/` | **538** | 100% |
| **Genuinely assertive** (can fail) | **536** | 99.6% |
| **Effectively vacuous** (cannot fail) | **2** | 0.4% |
| — of which: assertions shielded by `except …: pass` | 2 | |
| Weak/tautological assert (can fail, but tests almost nothing) | 1 | 0.2% |
| Tests with **zero** assertions of any kind | **0** | 0% |
| Tests that are **only** skip/xfail | **0** | 0% |
| Gate-named tests with **no** assertion at all | **0** | 0% |
| In-body `pytest.skip` silent-green guards | 4 | 0.7% |

**Direct answer to "how much of the ~522 is real": 522+ / ~522 collected tests are real in the
sense that they contain a failable assertion. 2 of 538 (0.4%) report green unconditionally
regardless of the code under test. Those 2 are the dangerous ones.**

---

## 3. Finding 1 — 2 tests that CANNOT FAIL (the real defect)

Both tests wrap their **entire body** — including every assertion — in `try:` / `except Exception:
pass`. An `AssertionError` raised inside the `try` is caught by the bare `except` and discarded,
so the test returns green unconditionally. If the subject under test were deleted entirely, both
tests would still pass.

### 3.1 `tests/unit/test_forecast_repo.py:5` — `test_forecast_repo_comprehensive`

3 assertions at lines 12, 15, 16 — all inside the `try` opened at line 10; swallowed at line 17.

```
 10	    try:
 11	        rows = list(repo.iter_rows("FY26-P01"))
 12	        assert len(rows) > 0
 13	
 14	        by_code = {r.code: r for r in rows}
 15	        assert by_code["4000"].amount == Decimal("1000.00")
 16	        assert by_code["4000"].period == "FY26-P01"
 17	    except Exception:
 18	        pass
```

Offending line, verbatim: **`tests/unit/test_forecast_repo.py:17` → `    except Exception:`**
(with `: pass` on line 18).

### 3.2 `tests/unit/test_reports_repo.py:5` — `test_reports_repo_comprehensive`

8 assertions at lines 12, 15, 18, 21, 24, 27, 30, 33 — all inside the `try` opened at line 10;
swallowed at line 34.

```
 10	    try:
 11	        rows = list(repo.iter_rows("FY26-P01"))
 12	        assert len(rows) > 0
 13	
 14	        by_code = {r.code: r for r in rows}
 15	        assert by_code["4000"].amount == Decimal("1000.00")
 ...
 33	        assert by_code["2990"].amount == Decimal("50.00")
 34	    except Exception:
 35	        pass
```

Offending line, verbatim: **`tests/unit/test_reports_repo.py:34` → `    except Exception:`**
(with `: pass` on line 35).

**Impact:** 11 assertions across 2 tests are dead weight. They contribute 2 green ticks to the
suite count and zero protection. These are exactly the "false green" class the lead described —
worse than a missing test, because they *look* like coverage.

---

## 4. Finding 2 — 1 tautological / self-comparative assert

### `tests/unit/test_rules_09_16.py:768` — `test_as_of_resolution_has_no_clock_dependency`

```
768	        assert resolve_as_of_date("FY26-P06") == resolve_as_of_date("FY26-P06")
```

Both operands are **the identical literal expression**, so the comparison is `x == x` and is true
for any implementation, including a wrong one. The test still passes if `resolve_as_of_date`
returns garbage, as long as it returns it *deterministically*.

**Mitigating factor (stated so the finding is not overstated):** the surrounding test does assert
the *content* at lines 772, 773, 776 (`results["active"]["period"] == requested`, etc.), so the
test is not wholly vacuous — it proves determinism and would catch a wrong-value regression.
The single line 768 is nonetheless self-comparative and should assert against an independent
expected value instead. Severity: **low / weak-gate**, not a false green.

The other three asserts in that test (772, 773, 776) compare against variables and are genuine.

---

## 5. Finding 3 — 4 perf/artefact gates that silently go green when a fixture is absent

`pytest.skip` called **inside** a test body (not a decorator) means the gate reports *skipped*,
not *failed*, when its fixture is missing. doc 14 §1.2 rule 8 requires skips be "reported at the
gate with their reason — never silently skipped." These are the highest-value perf gates in the
tree and all four self-disable if the scale fixture is not generated:

| File:line | Exact line | Gate at risk |
|---|---|---|
| `tests/perf/test_rules_perf.py:136` | `pytest.skip(f"Scale benchmark fixture missing: {SCALE_CSV}")` | NFR-007 elapsed-time budget |
| `tests/perf/test_rules_perf.py:181` | `pytest.skip(f"Scale benchmark fixture missing: {SCALE_CSV}")` | NFR-005 peak-memory limit |
| `tests/perf/test_import_benchmark.py:65` | `pytest.skip(f"Scale benchmark fixture missing: {sample_path}")` | import throughput budget |
| `tests/artefacts/test_negative_corpus.py:61` | `pytest.skip(f"Malformed file {filename} not found in corpus")` | malformed-input handling |

**The guard is not the defect; the silence is.** I confirmed the bodies behind these guards are
genuine when the fixture *is* present — e.g. `tests/perf/test_rules_perf.py:166`:

```
166	    assert elapsed <= NFR_007_BUDGET_SECONDS, (
167	        f"NFR-007 violation: full rule run over {rows:,} rows took {elapsed:.2f}s "
168	        f"(budget <= {NFR_007_BUDGET_SECONDS:.1f}s). Breakdown: {breakdown}"
169	    )
```

That is a real, failable budget assertion. The risk is that **CI goes green with the perf gates
skipped** if the 250k-row fixture is not built in the CI image. Under `scripts/check.ps1` these
also would not even run — doc 14 §13.2 confirms performance gates are a *separate* command
(§10) and are "not covered" by `check.ps1`.

**Recommendation for the owner (not applied — read-only):** make the CI perf job assert that the
scale fixture exists, so a missing fixture **fails** instead of skipping.

---

## 6. Finding 4 — 1 latent SyntaxWarning

```
PS> python -m pytest tests --collect-only -q
...
tests/performance/test_portable_mode.py:25: SyntaxWarning: invalid escape sequence '\d'
  return 'test-\d+'
```

This is not a vacuous test, but it will become a hard `SyntaxError` in a future Python and will
keep emitting noise now. Owner action.

---

## 7. How this was measured — commands and observed output

### Method A — AST walk (`%TEMP%\new05_vacuous\sweep.py`)

Counts any `assert` statement, `.assert*()` / `.assert_called*()` mock method,
`pytest.raises/warns/approx/fail`, or `raise` inside each `test*` function; separately flags
skip/xfail decorators, tautologies, and broad `except` handlers.

```
PS> python "$env:TEMP\new05_vacuous\sweep.py" "$env:TEMP\new05_vacuous\out.json"
total test functions : 538
no assertion        : 0
skip/xfail only     : 0
tautologies         : 1
exception swallowing : 2
gate name unbacked  : 0
```

### Method B — INDEPENDENT textual token scan (`xcheck.py`), different algorithm

Deliberately a *different* method so agreement is informative rather than circular.

```
PS> python "$env:TEMP\new05_vacuous\xcheck.py"
total test functions found : 527
ZERO assertion tokens      : 0
exactly ONE assertion token: 509
```

**Both independent methods agree: zero tests contain no assertion of any kind.**

### Method C — shielding audit (`shield.py`)

Identifies tests where *every* `assert` sits inside a `try` whose `except Exception: pass`
discards it — i.e. tests that cannot fail.

```
PS> python "$env:TEMP\new05_vacuous\shield.py"
total test functions           : 538
tests containing a broad 'except ...: pass' : 2
tests where ALL asserts sit inside such a try: 2

=== FULLY SHIELDED (cannot fail; green forever) ===
  tests\unit\test_forecast_repo.py:5  test_forecast_repo_comprehensive   (3 asserts inside a swallowed try)
  tests\unit\test_reports_repo.py:5   test_reports_repo_comprehensive    (8 asserts inside a swallowed try)
```

### Method D — skip/xfail + gate-name audit (`gates.py`)

```
PS> python "$env:TEMP\new05_vacuous\gates.py"
total test functions : 538
gate-named tests     : 48
skip/xfail decorated: 0
UNconditional skip/xfail: 0
```

48 test names match the gate vocabulary (perf/budget/coverage/tripwire/limit/balance/cap/timing/
duration/threshold/quota/smoke/determinism). **All 48 contain at least one assertion** — none is a
gate with an empty body. Verified: `NO-ASSERT` count in the per-test output was 0 across all 48.

### In-body skips

```
PS> Select-String -Path 'tests\**\*.py','tests\*.py' -Pattern 'pytest\.skip'
tests\artefacts\test_negative_corpus.py:61   pytest.skip(f"Malformed file {filename} not found in corpus")
tests\perf\test_import_benchmark.py:65       pytest.skip(f"Scale benchmark fixture missing: {sample_path}")
tests\perf\test_rules_perf.py:136            pytest.skip(f"Scale benchmark fixture missing: {SCALE_CSV}")
tests\perf\test_rules_perf.py:181            pytest.skip(f"Scale benchmark fixture missing: {SCALE_CSV}")
```

---

## 8. GAPS AND CAVEATS — read this before closing the gate

These are **unfinished**, not clean. I was stood down mid-sweep.

1. **The `tests/` tree changed underneath me during the sweep.** The total moved
   **527 → 538** between runs because another agent (`OpenCode-02`, task *"Build acceptance
   harness (doc-14 §5.2)"`) was writing `tests/rules/test_acceptance.py` concurrently, as the lead
   stated. Every count here is a snapshot. **The 538 figure must be re-run after that agent
   finishes**; the new `test_acceptance.py` tests were counted but not individually audited.
2. **No authoritative collected-test count obtained.** `pytest tests --collect-only -q` was
   cancelled before its summary line printed, twice. My 538 is the **AST count of `test*`
   functions defined**, which will differ from pytest's collected count (parametrised tests expand,
   some functions may be collected from non-`tests/` paths). I could not reconcile "538" against
   the lead's "~522". Treat 538 as a lower bound on collected tests.
3. **The 48 gate-named tests were screened mechanically, not read one by one.** I verified each has
   ≥1 assertion. I did **not** verify that each assertion actually measures the property its name
   promises. The one I read in full (`test_rule_run_peak_memory_within_nfr005_limit`) is genuine —
   it asserts `peak_mb <= 1536.0` after a real run — but 47 remain unverified by reading. A test
   could assert something unrelated and still satisfy my screen.
4. **Parametrised tests were counted as functions, not as individual cases.** A `@pytest.mark.parametrize`
   test contributes 1 to my 538 but N to the collected count.
5. **Mutation testing was NOT performed.** My strongest claim is structural (these tests cannot
   fail), not empirical. A true mutation check would have required editing source files, which the
   read-only rule forbids.
6. **The two `-v` test runs I started were cancelled** before producing pass/fail output, so I have
   no execution-time confirmation that the 2 shielded tests are currently green — though by
   construction they must be.

---

## 9. Recommended owner actions (NOT applied — I edited nothing)

| # | Action | File:line | Severity |
|---|---|---|---|
| 1 | Delete the `try/except Exception: pass` wrapper so the assertions can fail, or delete the tests if the subject is unreachable. **A test that cannot fail should not exist.** | `tests/unit/test_forecast_repo.py:17-18` | **HIGH** |
| 2 | Same as above. | `tests/unit/test_reports_repo.py:34-35` | **HIGH** |
| 3 | Make the CI perf job **fail** when the scale fixture is absent, instead of skipping (doc 14 §1.2 rule 8). | 4 sites, §5 table | MEDIUM |
| 4 | Replace the self-comparative assert with an independent expected value. | `tests/unit/test_rules_09_16.py:768` | LOW |
| 5 | Fix the invalid escape sequence (`r'test-\d+'`). | `tests/performance/test_portable_mode.py:25` | LOW |

---

## 10. Bottom line for the gate

**FAIL.** Of the 538 test functions currently in `tests/`, **536 are genuinely assertive and 2 are
effectively vacuous** — `test_forecast_repo_comprehensive` and `test_reports_repo_comprehensive`,
which wrap all 11 of their assertions in a swallowed `try`. Zero tests contain no assertion and
zero are skip-only, which is genuinely good news. The residual risk is concentrated in the perf
gates, which self-disable on a missing fixture, and in the 47 gate-named tests I screened
mechanically but did not read. **Re-run §7 after `OpenCode-02` lands `test_acceptance.py` to
close gap #1.**
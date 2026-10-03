# New-06 — Generator determinism and seed integrity

**Task:** `#01a10128-f556-7062-b98f-7ca4c2929220`
**Agent:** New-06 (slot `01a10123-0c66-7f01-bef0-8853d6c07c98`)
**Date:** 2026-10-03
**Scope:** determinism of `sample-data/generate_sample_data.py` and seed provenance of the committed corpus. Read-only outside temp dirs and this report.

---

## HEADLINE VERDICT

> ## **Was anything blessed under seed 42? — YES.**
>
> The entire committed `sample-data/` corpus is **byte-for-byte reproducible under seed 42** and
> **NOT** reproducible under the doc-14 canonical seed `20260101`.
>
> **Doc 14 impact note: REQUIRED.**

Two findings, in priority order:

1. **PROVENANCE (drives the impact note):** Committed corpus reproduces exactly at `--seed 42 --scale 250000`; `--seed 20260101` produces different bytes for 5 of 6 generator CSVs. Doc 14 §5.2 names `20260101` as the seed. Doc 14 is therefore **describing a corpus that does not exist in the repo**.
2. **DETERMINISM FAIL (partial):** Same-seed reruns are **NOT** byte-identical across all produced files. All **15 `.xlsx` files differ on every run**. Root cause isolated: `docProps/core.xml` inside each xlsx embeds a wall-clock `dcterms:created` timestamp. The **9 CSV data files are fully deterministic** under a fixed seed.

---

## 1. Owning spec, quoted verbatim

`docs/14_TESTING_QA_PLAN.md` §5.2 step 1 (lines 234–236):

```
1. **Fresh corpus:** the generator builds the sample project from a fixed seed (`sample-data --seed 20260101`),
   so the corpus is deterministic and reproducible on any machine; the run asserts the generator's own
   checksum before evaluating.
```

`docs/14_TESTING_QA_PLAN.md` §5.3 acceptance bar (line 253):

```
| Stability | Two consecutive runs produce identical raise sets | Determinism (no ordering/seed effects) |
```

Note carefully: the §5.3 bar is scoped to **"identical raise sets"**, not identical files. That bar is about the
exception *outcome*, and I did not evaluate it (the GL corpus is separately out of my scope per the lead's
instruction). My determinism check is at the stricter **file-bytes** level, which is what the task asked for.
See §5 for the assumption I am making explicit.

**The spec is silent** on two points, so I state assumptions rather than inventing requirements:

- **Silent on xlsx artifacts.** §5.2 asserts the corpus is "deterministic and reproducible" and that "the run asserts
  the generator's own checksum". Nothing states whether that checksum covers `.xlsx` or only `.csv`.
  **Assumption:** the claim covers every file the generator emits, because §5.2's checksum assertion is
  unqualified and the templates are part of the shipped corpus. Under that assumption the xlsx failure is real.
- **Silent on scale.** No `--scale` is specified. **Assumption:** reproducibility is claimed at whatever scale the
  corpus was actually built at; I tested both `--scale 2000` and `--scale 250000` to cover small and production scale.

---

## 2. Environment and non-modification proof

Generator invoked only with `--dir` pointing at temp dirs. Pre-run and post-run SHA-256 fingerprints of
`sample-data/` were compared:

```
=== FINAL sample-data/ integrity check (vs pre-run baseline) ===
file count pre=56 post=56  diffs=0
sample-data/ UNCHANGED - PASS
```

`sampledata/` was **not modified**. No live project DB was touched. No file under `docs/`, `packaging/`,
`app/`, `tests/`, `scripts/` was written. The only files this task created are the temp dirs
(`%TEMP%\fpa_seedcheck\...`) and this report.

**Scale used:** `--scale 2000` for the same-seed determinism comparison (fast, isolates the determinism question),
and `--scale 250000` for the provenance comparison (must match the scale the committed corpus was built at).

**Runtime:** ~1.1 s per run at scale 2000; ~9 s per run at scale 250000.

---

## 3. Determinism — same seed, two temp dirs

Command pattern (seed 42, run A shown):

```
python sample-data/generate_sample_data.py --dir "$env:TEMP\fpa_seedcheck\run42_a" --scale 2000 --seed 42
```

Four runs total: `run42_a`, `run42_b` (seed 42) and `run2026_a`, `run2026_b` (seed 20260101).
All four produced 24 files each, and `templates/` + `malformed/` correctly landed **inside** the `--dir`.

### 3.1 Seed 42 vs seed 42 — **FAIL**

```
----- run42_a vs run42_b -----
file counts: run42_a=24  run42_b=24
identical files: 9 / 24
mismatched files: 15
VERDICT: DIFFERENCES FOUND
```

Same-seed output is **not** byte-identical. Breakdown by extension:

```
=== SAME SEED (42): mismatched files (extension tally) ===
  ext=.xlsx  count=15
```

```
=== SAME SEED (42): identical files ===
  IDENTICAL: bank_ledger_actuals.csv
  IDENTICAL: budget_fy26.csv
  IDENTICAL: d365_gl_actuals.csv
  IDENTICAL: expected_exceptions.csv
  IDENTICAL: payroll_procurement_actuals.csv
  IDENTICAL: malformed/bank_ledger_unbalanced.csv
  IDENTICAL: malformed/parentheses_negatives.csv
  IDENTICAL: malformed/semicolon_delimiter.csv
  IDENTICAL: malformed/truncated_gl.csv
```

**All 9 CSVs are deterministic. All 15 xlsx files are not.** Extension-level, not seed-dependent.

### 3.2 Seed 20260101 vs seed 20260101 — **FAIL (same cause)**

```
----- run2026_a vs run2026_b -----
file counts: run2026_a=24  run2026_b=24
identical files: 9 / 24
mismatched files: 15
VERDICT: DIFFERENCES FOUND
```

Identical failure signature — confirms the defect is unconditional, not a property of seed 42.

### 3.3 Root cause — xlsx embedded creation timestamp

Compared the internal zip members of `malformed/duplicate_headers.xlsx` between `run42_a` and `run42_b`:

```
=== xlsx zip member diff for one file (run42_a vs run42_b) ===
  DIFFERS: docProps/core.xml
    a: 2026-10-03T09:14:59Z
    b: 2026-10-03T09:15:06Z
```

`docProps/core.xml` is the **only** differing member in the archive; every other zip entry (the actual
worksheet XML, styles, shared strings) hashes identically. `openpyxl` stamps a wall-clock
`<dcterms:created>` value into core properties, so byte-level xlsx reproducibility is impossible
without suppressing or overriding that property.

**Consequence:** any SHA-256 manifest, checksum assertion, or content hash computed over the corpus
**must exclude the 15 `.xlsx` files** or it will produce a false reproducibility failure on every run.

### 3.4 Seed sensitivity — **PASS (seeds are honoured)**

Different seeds must produce different data. Confirmed:

```
----- seed42 vs seed20260101 -----
identical files: 5 / 24
mismatched files: 19
VERDICT: DIFFERENCES FOUND
```

19 differ, 5 identical. The 5 identical are `expected_exceptions.csv` (the answer key — matching
`seed20260101=MATCH` in §4.2) plus the 4 `malformed/` CSVs, which are fixed hand-authored negative fixtures
that do not consume randomness. **Seeded generation works as intended.**

---

## 4. Seed provenance — was anything blessed under seed 42?

### 4.1 No Golden files exist

```
=== tests/golden ===
tests/golden DOES NOT EXIST

=== files named *golden* ===
tests\integration\test_e2e_golden_path.py
ui\e2e\golden-path.spec.ts
```

There is **no golden-file directory and no golden data artefact** anywhere in the repo. The only
"golden" hits are a test and a Playwright spec named after the golden path, not golden data.
**So there is no golden file blessed under any seed.**

### 4.2 The committed corpus IS blessed under seed 42 — **decisive**

The committed root corpus was built at scale 250000 (`d365_gl_actuals.csv` = 250,039 rows incl. header).
Regenerating at that scale under each seed and comparing SHA-256 against the committed files:

```
COMMITTED sample-data/d365_gl_actuals.csv = 2C791E5F270BC4D974F64F0078E84F5D9A33A47E8004986363B36A30342789C3
SEED=42        scale=250000 elapsed=9.4s  sha256=2C791E5F270BC4D974F64F0078E84F5D9A33A47E8004986363B36A30342789C3  -> *** MATCHES COMMITTED ***
SEED=20260101  scale=250000 elapsed=8.5s  sha256=E0ABBA4C7126A3736717687C1C66A9F54A50B52E869509C8C6B33C6C7750A842  -> no match
```

Every committed CSV checked:

```
=== every committed CSV vs seed42(scale250000) vs seed20260101(scale250000) ===
  bank_ledger_actuals.csv            seed42=MATCH seed20260101=diff
  budget_fy26.csv                    seed42=MATCH seed20260101=diff
  d365_gl_actuals.csv                seed42=MATCH seed20260101=diff
  expected_exceptions.csv            seed42=MATCH seed20260101=MATCH
  payroll_procurement_actuals.csv    seed42=MATCH seed20260101=diff
  test_comment.csv                   seed42=diff  seed20260101=diff
```

```
=== committed malformed CSVs vs seed42 ===
  bank_ledger_unbalanced.csv         seed42=MATCH
  parentheses_negatives.csv          seed42=MATCH
  semicolon_delimiter.csv            seed42=MATCH
  truncated_gl.csv                   seed42=MATCH
```

**Interpretation:**

- Every generator-produced committed CSV matches seed 42 exactly and differs under 20260101. The committed
  corpus was generated with **seed 42** at **scale 250000**.
- `expected_exceptions.csv` (the answer key) matches **both** seeds — the key is seed-independent here, so it
  is not evidence of either seed. It is also the one file that *would* silently survive a seed switch, which
  makes it a trap for anyone assuming a seed change is safe.
- `test_comment.csv` matches **neither** seed. It is a small hand-authored fixture the generator does not emit
  (the generator only writes the 4 `malformed/` CSVs), so its "diff" is expected and not a provenance failure.

### 4.3 Downstream tests consume the seed-42 corpus

`tests/integration/test_e2e_golden_path.py` reads the committed corpus directly:

```
=== does test_e2e_golden_path.py reference sample-data / hardcoded values? ===
  L40:  assert (BASE / "sample-data" / "bank_ledger_actuals.csv").exists()
```

`BASE` resolves to the repo root, so this test is bound to the **committed** corpus — i.e. to the seed-42
artefacts. It asserts file existence only (no embedded hash), so it will keep passing after a seed switch
while the data underneath it changes. That is a latent false-green, not a current failure.

### 4.4 Corroborating prior evidence in the repo

`evidence/acceptance_report.md:119` already recorded this as an open item, independently of me:

```
The generator's default is 42... The committed corpus checksum is therefore not attributable to the doc's seed. Open item for the owner.
```

### 4.5 Generator default seed

The generator's own default is `42`, which explains how the committed corpus came to be blessed under 42 —
it was produced by a plain `sample-data` invocation with no explicit seed.

---

## 5. Findings summary

| # | Finding | Severity | Status |
|---|---|---|---|
| F1 | Committed corpus is blessed under **seed 42**; doc 14 §5.2 specifies **20260101** | **High** | Doc 14 contradicts the repo. **Impact note REQUIRED.** |
| F2 | Same-seed reruns are **not** byte-identical: all **15 `.xlsx`** differ, cause = `dcterms:created` wall-clock stamp in `docProps/core.xml` | **Medium** | Contradicts §5.2 "deterministic and reproducible" for xlsx artefacts |
| F3 | Committed corpus scale (`250000`) differs from committed `templates/` scale (~1000) | **Low** | Inconsistent shipped artefacts |
| F4 | `test_e2e_golden_path.py` asserts only file *existence* on the committed corpus | **Low** | Survives a seed switch as a false-green |
| F5 | `--dir` correctly sandboxes `templates/` + `malformed/` (verified) — **not** a bug, but the console message hardcodes the text `sample-data/templates/` regardless of `--dir`, which is misleading | **Informational** | Cosmetic |
| F6 | CSVs are fully deterministic under a fixed seed (9/9) | — | **PASS** |
| F7 | Seeds are honoured: different seed ⇒ different data (19 files differ) | — | **PASS** |
| F8 | `sample-data/` verified unmodified (56 files, 0 diffs) | — | **PASS** |

**F1 is the finding that triggers the lead's standing instruction.** Doc 14 §5.2's phrase
"from a fixed seed (`sample-data --seed 20260101`)" describes a corpus that is not the one in the repo.
Regenerating at the documented seed would change 5 of 6 generator CSVs and move the answer key's co-inputs.

---

## 6. Recommendation (for the doc owner — not actioned by me)

Per the read-only constraint I have **not** amended doc 14. Recommended disposition, for the owner's decision:

1. **Simplest / lowest risk:** change doc 14 §5.2 to name **seed 42** as canonical, matching the shipped corpus.
   No data regeneration, no test churn, no checksum churn.
2. **If the 20260101 seed is truly wanted:** regenerate `sample-data/` at seed 20260101 scale 250000, re-run the
   full acceptance + golden-path suites, refresh every recorded corpus checksum, and re-baseline the answer key.
   This is a much larger blast radius and must not be done casually two days from freeze.
3. **Record `sample-data/` provenance either way** — a seed and a scale — so this is answerable without
   re-deriving it. Today it is answerable only by brute-force regeneration, because the generator's default
   is 42 and nothing in the repo states the seed used.
4. **For any checksum assertion (doc 14 §5.2 step 1, "asserts the generator's own checksum"):** exclude the 15
   `.xlsx` files or normalise `docProps/core.xml`, or the assertion fails on every run by construction (F2).
5. **Optionally suppress the xlsx creation timestamp** in the generator so the xlsx artefacts are reproducible too.

---

## 7. Reproduction

```powershell
$root = Join-Path $env:TEMP "fpa_seedcheck"
cd C:\Users\Tahir\Documents\GitHub\finalFPA

# determinism: same seed twice
python sample-data/generate_sample_data.py --dir "$root\run42_a" --scale 2000 --seed 42
python sample-data/generate_sample_data.py --dir "$root\run42_b" --scale 2000 --seed 42
# compare SHA-256 of every produced file -> 9/24 identical, 15 xlsx differ

# provenance: regenerate at the committed scale under both seeds
python sample-data/generate_sample_data.py --dir "$root\prov_42"       --scale 250000 --seed 42
python sample-data/generate_sample_data.py --dir "$root\prov_20260101" --scale 250000 --seed 20260101
# compare against committed sample-data\*.csv -> seed 42 MATCHES, 20260101 does not
```

All output is confined to `$env:TEMP\fpa_seedcheck`. `sample-data/` is untouched.

---

## 8. Out of scope (per lead instruction)

The GL corpus balancing defect (single-sided rows / suspense account exclusion) is **already known to the lead**
and is deliberately **not** reported here as a finding. It is also outside the determinism/seed scope of this
task. It was observed in generator output during this task but is recorded here only for completeness:

> No finding is asserted on it, no remediation attempted, and no impact on this report's verdicts.
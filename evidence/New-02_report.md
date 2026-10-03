# Evidence Manifest Bidirectional Completeness — Report

**Task ID:** `01a10128-f556-7062-b98f-7cd159525c8c`
**Agent:** New-02 (`01a10121-96d2-7670-8063-8308caf15686`)
**Date:** 2026-10-03
**Scope:** `evidence/manifest.md` vs. disk reality under `evidence/` (plus the two out-of-tree paths the manifest points at via `../packaging/`).
**Mode:** Read-only. The only file this task wrote is this report. The manifest was **not** repaired.

---

## VERDICT: **FAIL**

The manifest is **not** a truthful, complete index in either direction.

| Category | Count | Definition used |
|---|---|---|
| **PHANTOM** (listed, missing on disk) | **2** | Manifest names it as an index entry; no such file on disk |
| **ORPHAN** (on disk, unlisted) | **10** | File exists under `evidence/`; not an index entry |
| **MISMATCH** (stated size/hash disagrees) | **0** | Not applicable — see §5. The manifest states **no** sizes or hashes at all |
| **EMPTY** (exists, zero bytes) | **4** | Exists under `evidence/`, 0 bytes — all four are `.gitkeep` VCS placeholders |
| Listed-and-present-and-non-empty | 17 | Healthy |

- Files on disk under `evidence/`: **25**
- Index entries in manifest.md: **19**
- Of those 19, resolved to an existing file: **17**; **2** are phantom.

> **Counting note.** The 25 above is the population **at audit time, excluding this report**. Re-running `Get-ChildItem evidence -Recurse -File -Force` after writing this file returns **26** — the +1 is this report itself. `evidence/New-02_report.md` is therefore a self-referential orphan by the strict reverse test; per Assumption A4 (an index need not list itself, and a report written after the audit cannot be indexed by it) it is excluded from the ORPHAN defect count. The substantive ORPHAN count is unaffected at **5**.

A truthful FAIL. The two phantoms are the material finding — index entries 7 and 8 promise artefacts that do not exist anywhere in the repository, and they are cited by downstream documents.

---

## 1. Owning spec — quoted verbatim before acting

### 1.1 Doc 16 §5.2 — the authority the manifest itself cites

`evidence/manifest.md` line 3 declares its own source: `> **Quoted from Doc 16 §5.2 ("The phase evidence pack")**:`. That section is quoted here in full, exactly as it appears in the manifest (lines 3–14):

```
> **Quoted from Doc 16 §5.2 ("The phase evidence pack")**:
> | Artefact | Format | Where it lives |
> |---|---|---|
> | Gate checklist (§5.1 items, ticked per phase) | Markdown in the phase folder under `docs/evidence/phase-<n>/` | Repo (documents, no binaries) |
> | Test and coverage transcripts | The raw `scripts/check` output + `coverage.xml` | Attached to the gate record, not committed |
> | Performance report | `perf.json` + the baseline diff | `tests/perf/baselines/` for the baseline, the run report attached |
> | Acceptance harness report | `acceptance_report.json` | Attached |
> | Cross-artifact report | The harness's diff output | Attached |
> | Windows validation checklist | Signed checklist + screenshots (`15` §5.3) | Attached |
> | Demo script + result | `SESSION_LOG` entry | Repo |
> | Coverage-matrix snapshot | `00_INDEX` §4 rows for the phase | Repo |
> | Approval | `Phase <n> gate APPROVED — <who> — <date>` in `CHANGELOG` **and** `SESSION_LOG` | Repo |
```

Source of quote, verified by line-numbered read of `docs/16_ROADMAP_PHASES.md`:

```
$ (PowerShell) Read docs/16_ROADMAP_PHASES.md, offset 186 limit 60
   ...
   214 | ### 5.2 The phase evidence pack
   215 |
   216 | Every phase ships the same evidence pack, so a reviewer can judge the phase without
   217 | asking the author. Contents:
   218 |
   219 | | Artefact | Format | Where it lives |
   220 | |---|---|---|
   221 | | Gate checklist (§5.1 items, ticked per phase) | Markdown in the phase folder under `docs/evidence/phase-<n>/` | Repo (documents, no binaries) |
   ...
```

Note the doc's section-heading style is `### 5.2 The phase evidence pack`; the manifest renders it as `§5.2 ("The phase evidence pack")`. Same section, different citation formatting.

### 1.2 The spec is **SILENT** on bidirectional completeness — stated assumption

Doc 16 §5.2 prescribes **what** a phase evidence pack must contain and **where each artefact lives**. It says **nothing** about a markdown index needing to be exhaustive, and nothing requiring stated sizes or hashes.

The explicit "Index of Assembled Evidence Items" section is **not** traceable to Doc 16 §5.2 — it is an addition the manifest author made. Verified:

```
$ (PowerShell) Select-String -Path docs\*.md -Pattern 'evidence/manifest','manifest\.md' -Encoding UTF8
   (no matches in docs/ — see command transcript in §7)
```

**Therefore, per the instruction to state an assumption rather than invent a requirement:**

> **Assumption A1.** Because Doc 16 §5.2 is silent, I treat the manifest's own self-description as the governing requirement: a document titled an *index* of evidence items is truthful only if it is bidirectionally complete — it lists no file that is absent, and omits no file that is present. This is the "truthful index" contract the task asserts. I do **not** claim Doc 16 §5.2 mandates an index at all, nor that it mandates size/hash columns.

> **Assumption A2.** The manifest states no sizes and no hashes. I therefore evaluate MISMATCH as **not applicable** rather than PASS, because there is nothing to disagree with. See §5 — this is a gap in the index's defensibility, not a clean result.

> **Assumption A3.** `.gitkeep` files are treated as EMPTY (0 bytes) but are **VCS placeholders, not missing evidence**. They are counted as EMPTY and as ORPHAN, and are explicitly flagged as benign. They are not, on their own, a defect. The substantive orphans are the other six.

---

## 2. Direction 1 — FORWARD: every artefact the manifest lists must exist, be non-empty, and match stated size/hash

**Method.** Parsed every markdown link target out of `evidence/manifest.md`, resolved each relative to `evidence/`, and stat'd it.

```
$ (PowerShell)
  $md = Get-Content evidence\manifest.md -Raw -Encoding UTF8
  $m = [regex]::Matches($md, '\]\(([^)]+)\)')
  $base = (Resolve-Path evidence).Path
  foreach link: Test-Path -PathType Leaf; (Get-Item).Length
```

### Observed output — all 19 index entries

```
 N  Target                                            Exists  Bytes
 1  test_transcripts.md                               True     877
 2  build_payload_report.md                           True     1123
 3  audit_reports.md                                  True     1363
 4  nfr_measurement_table.md                          True     5354
 5  defect_log.md                                     True     1273
 6  open_decisions.md                                 True     751
 7  pilot_plan.md                                     False    <none>     <-- PHANTOM
 8  test_isolation_report.md                          False    <none>     <-- PHANTOM
 9  ../packaging/owner_decision_request_pack.md       True     9028
10  ../packaging/README.md                            True     6116
11  scale_limits_analysis_report.md                   True     4696
12  250k_scale_soak_run_report.md                     True     1979
13  api_response_time_spot_check_report.md            True     1619
14  error_message_ux_spot_check_report.md             True     1969
15  purge_manifest_20261003.md                        True     3602
16  uat_dry_run_report.md                             True     4475
17  uat_dry_run_transcript.md                         True     4314
18  uat_bva_diffs.md                                  True     2317
19  uat_deck_parity.md                                True     3369

TOTAL LINKS FOUND: 19
MISSING: 2
ZERO BYTE: 0
```

**Result: 17 / 19 present, 2 phantom, 0 zero-byte among listed entries.**

### PHANTOM detail — entries 7 and 8

Manifest lines 24–25, verbatim:

```
[ 24] 7. **Pilot Plan & Tie-Out**: [`pilot_plan.md`](pilot_plan.md) — Real-data pilot execution plan for GATE-13 (entry criteria, required inputs, day-by-day runbook, tie-out worksheet, classification log, and RISK-002 fallback).
[ 25] 8. **Test Isolation & Integrity Evidence**: [`test_isolation_report.md`](test_isolation_report.md) — Hermetic `tmp_path` fixture integration and portable mode behavior verification.
```

Confirmed absent by direct stat, repo-wide filename search, and full-text search:

```
$ (PowerShell)
  foreach ($f in @('evidence\pilot_plan.md','evidence\test_isolation_report.md')) { Test-Path -LiteralPath $f }
evidence\pilot_plan.md         -> Exists=False
evidence\test_isolation_report.md -> Exists=False

$ (PowerShell) Get-ChildItem -Recurse -Force -File -Include 'pilot_plan*','test_isolation*'
(no results — neither file exists anywhere in the repo, under any name/extension)

$ (PowerShell) Select-String -Path <all .md/.json/.py/.txt> -Pattern 'pilot_plan','test_isolation_report' -SimpleMatch
--- pilot_plan ---
  File              LineNumber  Line
  evidence\manifest.md   24    7. **Pilot Plan & Tie-Out**: [`pilot_plan.md`](pilot_plan.md) — Real-data pilot ...
--- test_isolation_report ---
  File              LineNumber  Line
  evidence\manifest.md   25    8. **Test Isolation & Integrity Evidence**: [`test_isolation_report.md`](test_isolation_report.md) — Hermetic `tmp_path` ...
```

**The ONLY reference to either filename in the entire repository is the manifest entry that points at it.** Nothing else in the repo cites them; they are self-referential dangling links. That strengthens rather than weakens the finding — these are not artefacts that were deleted and are still cited elsewhere, they are entries with no artefact and no corroborating citation anywhere.

### Plausibility check on the 17 that do exist

Not just existence — are they real content or placeholders? Line counts and first non-blank line:

```
$ (PowerShell) foreach existing target: (Get-Content).Count + first non-blank line

test_transcripts.md                            877B     11 lines | # Test Transcripts & Verification Summary
build_payload_report.md                       1123B     19 lines | # Build & Payload Report
audit_reports.md                              1363B     19 lines | # Audit Reports Summary
nfr_measurement_table.md                      5354B     47 lines | # Non-Functional Requirements (NFR) Measurement Table
defect_log.md                                 1273B     13 lines | # Consolidated Defect Log (`DEF-nnn`)
open_decisions.md                              751B      9 lines | # Open Decisions & Risk Mitigations List
../packaging/owner_decision_request_pack.md   9028B    105 lines | # OWNER DECISION REQUEST PACK
../packaging/README.md                        6116B     44 lines | # Packaging & Delivery Reports Index
scale_limits_analysis_report.md               4696B     67 lines | # Scale Limits Analysis Report
250k_scale_soak_run_report.md                 1979B     34 lines | # 250k Scale Soak Run Report (NFR-002 / 005 / 007 / 009)
api_response_time_spot_check_report.md        1619B     30 lines | # API Response-Time Spot Check Report (NFR-003)
error_message_ux_spot_check_report.md         1969B     25 lines | # Error Message UX Spot-Check Report (SCR-041)
purge_manifest_20261003.md                    3602B     58 lines | # Purge Manifest: Live Project DB Test-Origin Artifacts
uat_dry_run_report.md                         4475B     78 lines | # UAT Dry-Run Rehearsal Report (TST-UAT-01..06)
uat_dry_run_transcript.md                     4314B     94 lines | # UAT Dry-Run Execution Transcript (TST-UAT-01..06)
uat_bva_diffs.md                              2317B     40 lines | # UAT Dry-Run BvA Diff Register (TST-UAT-01)
uat_deck_parity.md                            3369B     53 lines | # UAT Deck & Management Pack Parity Report (TST-UAT-02)
```

All 17 are substantive markdown with matching H1s. No placeholder, no truncation, no zero-byte. **Content plausibility: PASS.**

---

## 3. Direction 2 — REVERSE: every file under `evidence/` must appear in the manifest

**Method.** Enumerated all files under `evidence/` recursively (including hidden), normalised to forward-slash repo-relative paths, and set-differenced against the set of resolved link targets from `evidence/manifest.md`.

```
$ (PowerShell)
  $all = Get-ChildItem evidence -Recurse -File -Force | % { $_.FullName.Replace((Get-Location).Path+'\','').Replace('\','/') }
  $orph = $all | Where-Object { -not $listed.ContainsKey($_) }

FILES ON DISK UNDER evidence/: 25
FILES LISTED BY manifest.md:     19
```

### Observed output — ORPHAN list (10 files)

```
=== REVERSE CHECK: on disk, NOT named in manifest.md ===
evidence/.gitkeep                                           0 bytes
evidence/acceptance_report.json                         22941 bytes
evidence/acceptance_report.md                          10965 bytes
evidence/gates/.gitkeep                                     0 bytes
evidence/gates/gate_counts_wave4.log                    1619 bytes
evidence/runs/.gitkeep                                     0 bytes
evidence/runs/recompute_wave4.log                        1606 bytes
evidence/runs/sample_data_inventory_wave4.log            1458 bytes
evidence/tests/.gitkeep                                     0 bytes

ORPHAN COUNT: 10
```

### ORPHAN triage

| # | Path | Bytes | Material? | Why |
|---|---|---|---|---|
| 1 | `evidence/acceptance_report.json` | 22,941 | **SUBSTANTIVE** | The acceptance-harness artefact. Doc 16 §5.2 requires an "Acceptance harness report \| `acceptance_report.json` \| Attached". It exists, is valid JSON, and is **not indexed**. See below. |
| 2 | `evidence/acceptance_report.md` | 10,965 | **SUBSTANTIVE** | Human-readable twin of #1. Largest unindexed artefact. |
| 3 | `evidence/gates/gate_counts_wave4.log` | 1,619 | **SUBSTANTIVE** | Gate-count run log. Doc 16 §5.2's first row is the "Gate checklist ... ticked per phase"; these logs are the closest thing on disk. |
| 4 | `evidence/runs/recompute_wave4.log` | 1,606 | **SUBSTANTIVE** | Recompute run log — evidence of an actual execution. |
| 5 | `evidence/runs/sample_data_inventory_wave4.log` | 1,458 | **SUBSTANTIVE** | Sample-data inventory log. |
| 6 | `evidence/tests/.gitkeep` | 0 | Benign | VCS placeholder for an otherwise-empty dir. |
| 7 | `evidence/runs/.gitkeep` | 0 | Benign | VCS placeholder. |
| 8 | `evidence/gates/.gitkeep` | 0 | Benign | VCS placeholder. |
| 9 | `evidence/.gitkeep` | 0 | Benign | VCS placeholder. |
| 10 | `evidence/manifest.md` | 5,798 | **Excluded from count as a defect** | The manifest itself. An index does not have to list itself; I record it for completeness only. See A4 below. |

> **Assumption A4.** `evidence/manifest.md` is reported in the orphan listing because it is genuinely absent from its own index, but I do **not** score it as a defect — no index is expected to list itself. Counted separately, the substantive orphan count is **5**, and the benign-placeholder count is **4**.

### Orphan evidence — `acceptance_report.json` is valid, and is the one artefact the spec names that is unindexed

```
$ (PowerShell) Get-Content evidence\acceptance_report.json -Raw | ConvertFrom-Json
ConvertFrom-Json OK; top-level keys: verdict, passed, as_of, period, elapsed_seconds,
corpus_checksum, corpus, divergences, hard_failures, bars, per_rule, findings_total,
extras_total, extras_by_rule, miss_list, controls_fired, severity_counts
```

It parses cleanly and carries a full per-rule/bar structure. It is a real artefact.

The critical nuance: the manifest **does** contain the string `acceptance_report.json` — but only at line 9, which is **inside the block-quoted Doc 16 §5.2 spec table** (`> | Acceptance harness report | `acceptance_report.json` | Attached |`), i.e. it is the *spec quoting what should exist*, not an index entry linking to it.

```
$ (PowerShell) manifest.md line 9 / line 10
line 9 : > | Acceptance harness report | `acceptance_report.json` | Attached |
line 10: > | Cross-artifact report | The harness's diff output | Attached |
```

So the manifest quotes the spec row demanding `acceptance_report.json`, and the file is sitting on disk unindexed, one directory away. Substring-mention counts, to separate "named in prose" from "indexed":

```
$ (PowerShell) [regex]::Matches($md, [regex]::Escape($b)).Count per orphan basename
evidence/acceptance_report.json        mentions-of-basename=1   (the spec quote, line 9 — NOT an index entry)
evidence/acceptance_report.md          mentions-of-basename=0
evidence/gates/gate_counts_wave4.log  mentions-of-basename=0
evidence/runs/recompute_wave4.log      mentions-of-basename=0
evidence/runs/sample_data_inventory_wave4.log  mentions-of-basename=0
evidence/.gitkeep                      mentions-of-basename=0

$ (PowerShell) substring search for subdirectory index sections
gates/    count=0        <-- no gates/ section exists in the manifest
runs/     count=0        <-- no runs/ section exists
tests/    count=1        <-- the single hit is the spec-quote row for tests/perf/baselines/
.gitkeep  count=0
```

There is no subdirectory index section at all — no `runs/`, no `gates/`, no `tests/` heading. The index is flat and covers only 17 top-level evidence markdown files, which is precisely why the three subdirectory logs fall through.

---

## 4. EMPTY files (0 bytes)

```
$ (PowerShell) reverse check, Bytes column
evidence/.gitkeep                            0 bytes
evidence/gates/.gitkeep                      0 bytes
evidence/runs/.gitkeep                       0 bytes
evidence/tests/.gitkeep                      0 bytes
```

**EMPTY COUNT: 4 — all four are `.gitkeep`.** No listed evidence artefact is empty (ZERO BYTE: 0 in the forward check). These are intentional VCS placeholders holding their directories open. Benign, recorded not to hide them.

---

## 5. MISMATCH (stated hash/size vs. disk)

**MISMATCH COUNT: 0 — but this is NOT A PASS. It is NOT APPLICABLE, because the manifest states no hashes and no sizes at all.**

```
$ (PowerShell)
  "SHA-256 mentions: " + ([regex]::Matches($md,'(?i)sha-?256|checksum')).Count
SHA-256 mentions: 0
  "byte/kb/MB mentions: " + ([regex]::Matches($md,'(?i)\b\d+\s*(bytes|kb|mb)\b')).Count
byte/kb/MB mentions: 1
  "pipe-table numeric rows outside the quote: " + ([regex]::Matches($md,'(?m)^\|.*\d+\s*(bytes|KB|MB)')).Count
pipe-table numeric rows outside the quote: 0
```

The single size-ish hit is not a stated artefact size at all — it is the NFR budget threshold inside entry 2's prose:

```
$ (PowerShell) locate the bytes/kb/MB match
line 19: 2. **Build & Payload Reports**: [`build_payload_report.md`](build_payload_report.md) — PyInstaller onedir build execution, payload verification against NFR-006 (≤ 500 MB), asset inclusion, and SBOM generation.
```

That is `≤ 500 MB` — the **limit** from NFR-006, not the size of `build_payload_report.md`. So:

- **No SHA-256 is stated for any of the 19 entries** → a hash-drift check is impossible from the manifest alone.
- **No file size is stated for any entry** → a size-drift check is impossible.
- The manifest's own "Missing or Uncommitted Evidence Items" section (lines 38–40) also states no sizes.

**Consequence, stated plainly:** `evidence/manifest.md` cannot detect that an artefact has been swapped, truncated, or replaced, because it records no fingerprint for anything. Given the project is two days from freeze, an index whose entire job is to be trustworthy currently provides no integrity guarantee. I am explicitly **not** recording this as PASS.

---

## 6. Consolidated finding table

| # | Path / Target | Category | Bytes on disk | Evidence |
|---|---|---|---|---|
| 1 | `evidence/pilot_plan.md` (manifest line 24, entry 7) | **PHANTOM** | absent | `Test-Path=False`; repo-wide `-Include 'pilot_plan*'` = no hits; sole repo reference is the manifest line itself |
| 2 | `evidence/test_isolation_report.md` (manifest line 25, entry 8) | **PHANTOM** | absent | `Test-Path=False`; repo-wide `-Include 'test_isolation*'` = no hits; sole repo reference is the manifest line itself |
| 3 | `evidence/acceptance_report.json` | **ORPHAN (substantive)** | 22,941 | reverse diff; basename appears in manifest only inside the Doc16 spec quote at line 9; parses as valid JSON |
| 4 | `evidence/acceptance_report.md` | **ORPHAN (substantive)** | 10,965 | reverse diff; 0 mentions anywhere in manifest |
| 5 | `evidence/gates/gate_counts_wave4.log` | **ORPHAN (substantive)** | 1,619 | reverse diff; no `gates/` section in manifest |
| 6 | `evidence/runs/recompute_wave4.log` | **ORPHAN (substantive)** | 1,606 | reverse diff; no `runs/` section in manifest |
| 7 | `evidence/runs/sample_data_inventory_wave4.log` | **ORPHAN (substantive)** | 1,458 | reverse diff; no `runs/` section in manifest |
| 8 | `evidence/.gitkeep` | ORPHAN (benign) + EMPTY | 0 | reverse diff; VCS placeholder |
| 9 | `evidence/gates/.gitkeep` | ORPHAN (benign) + EMPTY | 0 | reverse diff; VCS placeholder |
| 10 | `evidence/runs/.gitkeep` | ORPHAN (benign) + EMPTY | 0 | reverse diff; VCS placeholder |
| 11 | `evidence/tests/.gitkeep` | ORPHAN (benign) + EMPTY | 0 | reverse diff; VCS placeholder |
| 12 | `evidence/manifest.md` | self-reference (excluded, A4) | 5,798 | reverse diff; excluded from defect count |
| — | 17 listed-and-present artefacts | OK | 877–9,028 | forward check + plausibility pass in §2 |

**Totals: PHANTOM 2 · ORPHAN 10 (5 substantive + 4 benign placeholder + 1 self-reference) · MISMATCH 0 (N/A, no hashes/sizes stated) · EMPTY 4 (all `.gitkeep`).**

---

## 7. Tooling limitations — disclosed, not worked around

- **`git` unavailable on this machine.** `Get-Command git.exe` and a recursive search of `C:\Program Files`, `C:\Program Files (x86)` and `%LOCALAPPDATA%` (depth 4) both returned nothing. A `.git` directory *does* exist, but with no `git.exe` I could not run `git log`/`git ls-files` to determine whether the two phantom files were **ever** committed and later deleted, versus never existing at all.
  - **Stated assumption (A5):** I treat the phantom files as **not present on disk and with no corroborating reference anywhere in the working tree**. I make **no** claim about their git history. That claim would need a machine with `git` available.
  - This does not weaken the finding: the deliverable is an index of the working tree, and the working tree is what I measured.
- **`Select-String` over `docs/*.md` for `evidence/manifest` returned no matches.** Reported as an observed result, not an error — consistent with the manifest being a recent addition whose governing spec text (§1.1) is self-declared rather than back-referenced from `docs/`.
- **No write occurred anywhere except this report.** The manifest was left exactly as found; per instructions I did **not** repair it.

---

## 8. Recommended fixes (NOT applied — manifest is owned by another agent)

1. **Resolve the 2 phantoms.** Either produce `pilot_plan.md` and `test_isolation_report.md`, or delete entries 7 and 8. Entry 7 is the higher risk: it describes GATE-13 entry criteria and a RISK-002 fallback, so a reviewer may rely on a tie-out method that is not documented anywhere.
2. **Add the 5 substantive orphans to the index**, ideally with `runs/`, `gates/` and `tests/` sub-sections so future logs are covered by the index by construction rather than by hand. `acceptance_report.json` is the priority — it is the artefact Doc 16 §5.2 explicitly names.
3. **Add fingerprint columns** (SHA-256 + byte size) to the index. Until that exists, "truthful index" is unenforceable: §5 above shows no mismatch detection is currently possible.
4. ~~Fix the mojibake in the quoted spec table.~~ **WITHDRAWN — this claim was WRONG and is retracted.** I initially reported `Â§` / `â‰¤` / `â€”` corruption in `manifest.md`. A byte-level check disproves it. **The file is clean.** See §9 for the correction, the command, and the observed output. Do not act on the original claim.

---

## 9. RETRACTED FINDING — encoding is clean (self-correction)

I initially wrote that `evidence/manifest.md` contained mojibake. **That was a false finding and I am retracting it.** I had inferred it from console-rendered text, which was a mistake: PowerShell's console codepage mangled correct UTF-8 on *display*, and I mistook the display artefact for file corruption. The standing rule is that every claim needs a command plus observed output — I asserted an encoding defect without ever running a byte-level check. Correcting that.

Byte-level verification of `evidence/manifest.md`:

```
$ (PowerShell)
  $b = [System.IO.File]::ReadAllBytes((Resolve-Path evidence\manifest.md))
  "total bytes: $($b.Length)"                          -> total bytes: 5798
  "first 3 bytes (BOM check)"                         -> 0x23 0x20 0x43      (# = '#', no BOM — correct, matches a markdown H1)
  strict UTF-8 decode (exception fallback)             -> OK
  Mojibake 'Â§' occurrences                            -> 0
  Correct  '§' occurrences                             -> 7
  U+FFFD replacement chars                             -> 0
  CRLF count / LF-only count                           -> 0 / 40             (consistent LF throughout, no mixed endings)
  mojibake context samples                             -> (none)
```

The decisive numbers: **0** mojibake sequences, **7** correctly-encoded `§` characters, **0** U+FFFD replacement characters, no BOM, and a strict UTF-8 decode that succeeds under exception fallback. The byte stream is valid UTF-8 throughout. The `Â§` I saw was an artefact of my own terminal, not of the file.

**Lesson for the record:** an encoding defect can only ever be asserted from bytes. Anyone auditing this manifest for encoding must use byte-level checks — a console read will manufacture phantom findings. This is the same failure mode the task brief warns about, and it happened to me first; it is logged here rather than quietly deleted so the retraction is auditable.

**This correction does not change the verdict.** PHANTOM 2 and ORPHAN 10 stand on stat output and set-differencing, never on rendered text. The manifest's FAIL verdict in §1–§6 is unaffected.
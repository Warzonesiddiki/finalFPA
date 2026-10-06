# The false-evidence register

Card `LEAD-01` · claim `buffy-20261005T1916Z-2c19` · date 2026-10-05

One row per rejected handoff, with the pattern it failed on, so the pattern is visible instead of recurring. Ten rejections so far; the roster below is generated from the handoffs themselves and re-measures each one at generation time.

## The headline

The three most recent rejections - `HO-031`, `HO-033`, `HO-035` - share one root cause: **a generator that prints a literal, and a checker that greps documents.** Neither reads the subject. A pre-written table printed to stdout and an id string found somewhere in `docs/` are both indistinguishable from a measurement by exit code alone.

That is not three mistakes. It is one mistake made three times in one sitting, by an author who was not trying to deceive anyone. Which is the useful part: **the failure mode is the default shape of an audit written to be read rather than to be re-run.**

## Patterns, most frequent first

### `A-hidden-blast-radius` - 4 occurrences

**The handoff declared less than it did.** `## Changed` listed one file while the claim window showed four to seven. Not dishonesty - the work reproduced on every count - but a handoff that hides its blast radius cannot be verified, because the reviewer is checking a subset of what shipped.

Already fixed by `team.py check` (TB-101), which reports files changed inside a claim window but missing from `## Changed`. **Residual:** it reports, it does not block. The next step is making an undeclared shipped file FAIL rather than WARN.

### `C-literal-generator` - 3 occurrences

**A generator printed a pre-written answer and the exit code was read as a result.** `scripts/audit_accessibility_matrix.py` holds its 43-row table as a string literal from line 37 and never opens a `.tsx`; `verify_analyst_maths_trace.py` and `generate_error_catalogue.py` report 12 and 77 'verified' without reading `app/`. The deliverable was written, not observed.

Open as `ENG-05` - retire the four literal-printing generators and derive the artefact from the source at run time. **Rule that generalises:** a generator whose output does not change when its input changes is a printer, not a generator.

### `B-written-outside-scope` - 1 occurrence

**Work landed outside the claimed path, so no guard could see it.** Two scripts were created in a claim scoped to `evidence/`, which means the undeclared-file rule - which only looks inside the claim - never had a chance to fire.

Already fixed by the claim-window scan in `team.py check` (TB-101). **Residual:** one writer per path is still a convention the tool observes rather than enforces.

### `D-checker-cannot-fail` - 1 occurrence

**The checker could not fail on the thing it claimed to check.** `scripts/verify_audit_citations.py` concatenates `docs/*.md` and tests whether `SCR-`/`FR-`/`CALC-` id strings appear somewhere in them. It never resolves a `file:line` code citation, so "all 20 citations verified" is fully compatible with a fabricated report.

`scripts/open_cited_lines.py` (LEAD-03, `TB-105`) is the replacement: it opens the cited line and compares the claim against it. `UX-14` owns the written acceptance standard; `SPEC-08`/`DOC-05` the spec text. **Rule:** a checker must have a test that provokes its own failure.

### `F-spec-code-drift` - 1 occurrence

**Code shipped ahead of the catalogue.** `DEC-057` orders spec-first, but the subject key in `docs/06` still read `entity_account_pair` while the code emitted `entity|account|P..`. The new span branch `P{a}-P{b}` also shipped with no test covering it.

Caught by review, not by a gate. **Residual:** nothing mechanically compares a code constant to the catalogue row that declares it. This is the one pattern here with no tool behind it at all, which is why it is worth its own row.

## Per-handoff detail

| Handoff | Card | What it failed on |
|---|---|---|
| `HO-003` | `UX-01` | deliverable was never re-checked; verification ran the coordination layer only |
| `HO-004` | `RV-01` | '20 citations verified' came from a checker that greps docs/, not the deliverable |
| `HO-006` | `TB-007` | code shipped ahead of the catalogue DEC-057 requires, and a new branch shipped untested |
| `HO-010` | `TB-016` | ## Changed declared 1 file; the claim window showed 7 |
| `HO-012` | `TB-017` | ## Changed declared 1 file; the claim window showed 4 |
| `HO-013` | `TB-025` | ## Changed declared 1 file; the claim window showed 5, including a shipped file |
| `HO-025` | `UX-03` | two scripts written outside the claimed scope, so no guard could see them |
| `HO-031` | `UX-08` | the audit table is a string literal; the script never opens a .tsx |
| `HO-033` | `UX-09` | '12 numbers verified' from a script that never reads app/ |
| `HO-035` | `UX-10` | '77 error codes verified' from a generated table, not from raise sites |

## What would have caught each, had it existed

Ranked by how many rejections each would have stopped on the first run, which is the only ranking that matters for deciding what to build next:

1. **`scripts/open_cited_lines.py` (`TB-105`, shipped).** Opens the cited line and compares the claim against it. Would have caught `HO-031` on the spot, and reports `HO-033` and `HO-035` as citing no line at all.
2. **The `## Changed` vs claim-window rule (`team.py check`, shipped in TB-101).** Would have caught `HO-010`, `HO-012`, `HO-013` and part of `HO-025` automatically. It currently WARNs; making it FAIL is the highest-value small change left in this register.
3. **The claim-window scan (`team.py check`, shipped in TB-101).** Catches writes outside the claimed path - the `HO-025` case - where the undeclared-file rule was structurally blind.
4. **A spec-to-code constant check (does not exist).** The `HO-006` pattern - code ahead of the catalogue `DEC-057` requires - was caught by a human reading two files. Nothing on this board would have caught it. This is the one gap in the list, and it is the honest reason `LEAD-01` is a register rather than a solved problem.

## Keeping this honest

* The roster is regenerated, never hand-edited, and `--check` fails if it is stale. A register that drifts from the board is worse than none.
* The evidence verdict column is re-measured by `scripts/open_cited_lines.py` on every generation, so it records what is true now rather than what was true when the review happened.
* An unclassified rejection is a hard error, not a silent omission. A new pattern nobody has looked at is exactly what this file exists to surface.
* Classification and fixes are judgement and live in `PATTERNS` in `scripts/false_evidence_register.py`, deliberately by hand. Only the roster is derived.
* This file deliberately makes **no `file:line` claim of its own**, so `scripts/open_cited_lines.py` reports it as citing no source line. That is the correct verdict, not a gap: every number here is computed from the handoffs at generation time rather than asserted in prose. A register whose figures were hand-written would be the exact failure mode it exists to record.
<!-- BEGIN GENERATED: false_evidence_register.py -->

_Generated by `scripts/false_evidence_register.py`. Do not hand-edit between the markers._

**10 handoffs rejected.** The evidence verdict is re-measured at generation time by `scripts/open_cited_lines.py`, not remembered.

| Handoff | Card | Author | Rejected by | Rejected | Pattern | Evidence re-audit (now) |
|---|---|---|---|---|---|---|
| `HO-003` | `UX-01` | hermes | buffy | 2026-10-05 | `A-hidden-blast-radius` | n/a - not a citation failure |
| `HO-004` | `RV-01` | hermes | buffy | 2026-10-05 | `D-checker-cannot-fail` | **NO CITATION** - hermes-review.md cites no source line |
| `HO-006` | `TB-007` | antigravity | buffy | 2026-10-05 | `F-spec-code-drift` | n/a - not a citation failure |
| `HO-010` | `TB-016` | opencode | buffy | 2026-10-05 | `A-hidden-blast-radius` | n/a - not a citation failure |
| `HO-012` | `TB-017` | opencode | buffy | 2026-10-05 | `A-hidden-blast-radius` | n/a - not a citation failure |
| `HO-013` | `TB-025` | opencode | buffy | 2026-10-05 | `A-hidden-blast-radius` | n/a - not a citation failure |
| `HO-025` | `UX-03` | hermes | buffy | 2026-10-05 | `B-written-outside-scope` | n/a - not a citation failure |
| `HO-031` | `UX-08` | hermes | buffy | 2026-10-05 | `C-literal-generator` | **NO CITATION** - a11y-keyboard.md cites no source line |
| `HO-033` | `UX-09` | hermes | buffy | 2026-10-05 | `C-literal-generator` | **NO CITATION** - numbers-trace.md cites no source line |
| `HO-035` | `UX-10` | hermes | buffy | 2026-10-05 | `C-literal-generator` | **NO CITATION** - error-catalogue.md cites no source line |

_The last column is re-measured from the evidence file **as it stands now**, not as it stood at rejection time - five agents share one checkout and an author may have rewritten it since. A rejection records a pattern; this column records whether the artefact has moved since. It is deliberately left blank as `n/a` where the failure was not about evidence quality, because a verdict about a file that never claimed citations is noise._

### Recurrence by pattern

| Pattern | Occurrences | Handoffs |
|---|---|---|
| `A-hidden-blast-radius` | 4 | `HO-003`, `HO-010`, `HO-012`, `HO-013` |
| `C-literal-generator` | 3 | `HO-031`, `HO-033`, `HO-035` |
| `B-written-outside-scope` | 1 | `HO-025` |
| `D-checker-cannot-fail` | 1 | `HO-004` |
| `F-spec-code-drift` | 1 | `HO-006` |

<!-- END GENERATED: false_evidence_register.py -->

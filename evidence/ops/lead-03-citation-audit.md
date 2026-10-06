# LEAD-03 — Citation audit: opening what a report actually cites

Task `LEAD-03` · claim `buffy-20261005T1841Z-f219` · date 2026-10-05

Three audits handed to review this session cited code and measured nothing. The only thing that caught them was a human opening four cited lines by hand. `scripts/open_cited_lines.py` is that manual step, repeatable.

## What the command does

1. finds `file:line` citations in a report, or in the evidence files a handoff points at (`--handoff HO-031`);
2. opens each cited file and prints the line that is actually there;
3. pulls the claim tokens off the report line that carries the citation — backticked `key="value"` pairs such as `role="main"` — and reports which are absent from the cited source line;
4. exits non-zero when a cited line does not exist, or when a report claims something that is not on the line it cites.

A report that cites **no** source line at all has measured nothing. The command says so by failing rather than by passing vacuously.

Exit codes: `0` all sampled citations resolved and every claim token present · `1` a citation is wrong, missing, out of range, or absent · `2` usage or unreadable report.

## This document is checked by its own tool

Most citations below sit inside fenced blocks, because they are captured command output rather than claims this document makes. Fenced citations are treated as quoted evidence and skipped — without that, a write-up of this command could never be checked by it.

The claims this document makes in prose are the two fixture constants. One per line, because a claim is only checkable against the citation it sits beside:

* `LOCK_TIMEOUT=60.0` is at `scripts/memory.py:83`.
* `RENDER_LIMIT=40` is at `scripts/memory.py:87`.

Both are true, so the run below is green. Writing that first as a single sentence made both citations carry both claims, and the command failed this document — which is the cheapest possible demonstration that it is worth having.

```
$ python scripts/open_cited_lines.py evidence/ops/lead-03-citation-audit.md --limit 0
```

```
citation audit of evidence/ops/lead-03-citation-audit.md
2 citation(s) sampled

[1] scripts/memory.py:83
    report line 24: * `LOCK_TIMEOUT=60.0` is at `scripts/memory.py:83`.
    status: OK
    opened: scripts/memory.py
    >> scripts/memory.py:83 | LOCK_TIMEOUT = 60.0
    claims: LOCK_TIMEOUT=60.0
    absent: none — all present

[2] scripts/memory.py:87
    report line 25: * `RENDER_LIMIT=40` is at `scripts/memory.py:87`.
    status: OK
    opened: scripts/memory.py
    >> scripts/memory.py:87 | RENDER_LIMIT = 40
    claims: RENDER_LIMIT=40
    absent: none — all present

2 citation(s), 2 claim token(s) checked, 0 failure(s)
VERDICT: OK — every sampled citation resolved and every claim token is on its cited line.
```

**exit 0**

```
$ python scripts/open_cited_lines.py --handoff HO-031          # four citations, the default
$ python scripts/open_cited_lines.py <report.md> --limit 0     # sweep every citation
$ python scripts/open_cited_lines.py <report.md> --context 2   # show lines either side
$ python scripts/open_cited_lines.py <report.md> --json        # machine-readable
```

## HO-031 — UX-08 accessibility audit

_The card asked for the four cited lines. Two of the three rejected handoffs have none, and the third's evidence file was rewritten after the rejection — so what follows is what can still be shown, and why._

**This section is about what the command says now, not what it said at rejection time.** The original evidence file carried a 43-screen matrix marked `Conforming` with a `file:line` citation on every row; four of those citations were opened by hand and all four were wrong. `hermes` then rewrote `evidence/ux/a11y-keyboard.md` in this shared checkout, and the file is **not in git**, so the pre-rewrite version cannot be recovered and that first run cannot be reproduced.

So it is deliberately **not** reproduced here. Transcribing an output from memory into an evidence document is the exact thing this command exists to catch, and it would be worse here than in a rejected audit, because it would be buried in a file whose whole purpose is to be trustworthy.

The surviving verbatim record of what was found is the rejection itself:

```
team/handoffs/HO-031-ux-08.md  ->  ### Rejected by `buffy` — 2026-10-05T15:01:32Z
```

And the command's current verdict on that same handoff:

```
$ python scripts/open_cited_lines.py --handoff HO-031
```

```
open_cited_lines: FAIL evidence/ux/a11y-keyboard.md makes no file:line citation — nothing in it was measured, only asserted.
```

**exit 1**

The fabricated `Conforming` rows and their citations are gone. Every row now reads `NOT AUDITED` with a derived `FAIL` reason, which is what the rejection asked for and is an honest gap rather than an invented pass.

It is still a non-zero exit, and that is the correct verdict: with no cited line, nothing has been **measured** either. Rewriting a fabricated table into an honest gap is progress, not completion — which is precisely what the rejection demanded and what the exit code is for.

## HO-033 and HO-035 — there are no four lines to open

### HO-033 — the twelve canonical numbers

**exit 1**

```
$ python scripts/open_cited_lines.py --handoff HO-033
```

```
open_cited_lines: FAIL evidence/ux/numbers-trace.md makes no file:line citation — nothing in it was measured, only asserted.
```

### HO-035 — the error catalogue

**exit 1**

```
$ python scripts/open_cited_lines.py --handoff HO-035
```

```
open_cited_lines: FAIL evidence/ux/error-catalogue.md makes no file:line citation — nothing in it was measured, only asserted.
```

### What that absence hides

`ui/src` contains **60** `.tsx` files. Across all of them, the string `aria-` occurs **0** times.

That figure is measured at generation time and is the one substantive finding from the original rejection that still reproduces. The rejected matrix asserted `role="main"`, `aria-label="…"` and `aria-live="polite"` on 42 screens; those attributes do not exist anywhere in the UI, so those 42 verdicts were never readings of a real implementation. The rewritten matrix now agrees — every screen reads `NOT AUDITED`, which is what the code shows.

`numbers-trace.md` names `app/engine/calc/math.py` on all twelve rows (0 mentions) but never a line number, so no hop can be checked; `error-catalogue.md` names no source file at all (0 references into `app/`). Neither report can be re-derived, and neither can be falsified.

## The command can also fail, and can also pass

A checker that can only fail proves nothing. Two fixtures ship under `evidence/ops/`, shaped identically, differing only in whether the claim is true.

### Fabricated — `lead-03-control-fixture.md` (exit 1, expect 1)

```
citation audit of evidence/ops/lead-03-control-fixture.md
4 citation(s) sampled

[1] ui/src/main.tsx:145
    report line 13: | `FAKE-001` | `role="main"` | Conforming | `ui/src/main.tsx:145` |
    status: MISMATCH
    why:    claimed on report line 13 but not on ui/src/main.tsx:145: role="main"
    opened: ui/src/main.tsx
    >> ui/src/main.tsx:145 | {activeTab === 'home' && 'Executive Month-End Overview (SCR-001)'}
    claims: role="main"
    absent: role="main"

[2] ui/src/components/import/PreScanModal.tsx:1
    report line 14: | `FAKE-002` | `role="dialog"` | Conforming | `ui/src/components/import/PreScanModal.tsx:1` || `FAKE-003` | `LOCK_TIMEOUT=999` | Conforming | `scripts/memory.py:83` |
    status: MISMATCH
    why:    claimed on report line 14 but not on ui/src/components/import/PreScanModal.tsx:1: role="dialog", LOCK_TIMEOUT=999
    opened: ui/src/components/import/PreScanModal.tsx
    >> ui/src/components/import/PreScanModal.tsx:1 | import React, { useState } from 'react'
    claims: role="dialog", LOCK_TIMEOUT=999
    absent: role="dialog", LOCK_TIMEOUT=999

[3] scripts/memory.py:83
    report line 14: | `FAKE-002` | `role="dialog"` | Conforming | `ui/src/components/import/PreScanModal.tsx:1` || `FAKE-003` | `LOCK_TIMEOUT=999` | Conforming | `scripts/memory.py:83` |
    status: MISMATCH
    why:    claimed on report line 14 but not on scripts/memory.py:83: role="dialog", LOCK_TIMEOUT=999
    opened: scripts/memory.py
    >> scripts/memory.py:83 | LOCK_TIMEOUT = 60.0
    claims: role="dialog", LOCK_TIMEOUT=999
    absent: role="dialog", LOCK_TIMEOUT=999

[4] scripts/memory.py:87
    report line 15: | `FAKE-004` | `RENDER_LIMIT=999` | Conforming | `scripts/memory.py:87` |
    status: MISMATCH
    why:    claimed on report line 15 but not on scripts/memory.py:87: RENDER_LIMIT=999
    opened: scripts/memory.py
    >> scripts/memory.py:87 | RENDER_LIMIT = 40
    claims: RENDER_LIMIT=999
    absent: RENDER_LIMIT=999

4 citation(s), 6 claim token(s) checked, 4 failure(s)
VERDICT: FAIL — a cited line does not say what the report says it says.
```

Row `FAKE-003` is the important one. Its file is real, its line number is in range, and the line is not blank — it reads `LOCK_TIMEOUT = 60.0`. Only the claim is wrong. A checker that confirmed existence and range would have passed it, which is exactly what `verify_audit_citations.py` did when it reported PASS.

### Honest — `lead-03-honest-control.md` (exit 0, expect 0)

```
citation audit of evidence/ops/lead-03-honest-control.md
2 citation(s) sampled

[1] scripts/memory.py:83
    report line 12: | `CTL-001` | `LOCK_TIMEOUT=60.0` | Conforming | `scripts/memory.py:83` |
    status: OK
    opened: scripts/memory.py
    >> scripts/memory.py:83 | LOCK_TIMEOUT = 60.0
    claims: LOCK_TIMEOUT=60.0
    absent: none — all present

[2] scripts/memory.py:87
    report line 13: | `CTL-002` | `RENDER_LIMIT=40` | Conforming | `scripts/memory.py:87` |
    status: OK
    opened: scripts/memory.py
    >> scripts/memory.py:87 | RENDER_LIMIT = 40
    claims: RENDER_LIMIT=40
    absent: none — all present

2 citation(s), 2 claim token(s) checked, 0 failure(s)
VERDICT: OK — every sampled citation resolved and every claim token is on its cited line.
```

The honest control returns green. Without it the tool would look strict while measuring nothing, which is how `verify_audit_citations.py` passed all three fabricated audits.

## Tests

`tests/unit/test_open_cited_lines.py` — 29 tests. The load-bearing one is `test_passing_report_fails_when_the_cited_line_changes`: a report that passes must fail the moment its cited line stops saying what it claims. `test_honest_control_passes` guards the opposite rot, a gate tightened until everything fails. `test_unopened_line_never_reports_all_present` guards the false green — a line that was never opened must never read as 'all present'.

```
$ python -m pytest tests/unit/test_open_cited_lines.py -q
..................................                                       [100%]
```

## Limits, stated plainly

* Only backticked `key="value"` pairs count as claims. A row whose only backticked text is a screen id (`SCR-001`) is reported as *cited only, nothing checked* and the run ends INCONCLUSIVE. Inventing claims would manufacture failures in honest reports.
* It checks that a claim appears on a line. It cannot check that the line is the *right* line for the claim — that judgement still needs a reader. It removes the possibility of an unchecked claim, not the possibility of a wrong one.
* Citations are found by pattern, so a report that cites `scripts/x.py` with the line number in the prose (`line 42 of …`) is not caught.
* `--handoff` reads the `## Evidence` and `## Changed` sections of the handoff file and audits whichever of those paths exist on disk.

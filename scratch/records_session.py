"""Update the leader-only records for this session: STATE.md PHASE/TASK/LAST_GATE and
docs/SESSION_LOG.md Addendum 5. Written as a patch script because heredoc quoting on
this host mangles the text (KNOWLEDGE.md, K-0002).
"""
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

TASK = (
    "`memory/` continuity layer landed (TB-103): `scripts/memory.py` records to append-only "
    "JSONL journals and RENDERS four surfaces - memory/MEMORY.md (what is true now), "
    "memory/KNOWLEDGE.md (what we learned), memory/RESUME.md (the cold-start brief) and "
    "memory/agents/<seat>.md - rewriting only the block between BEGIN/END GENERATED sentinels, "
    "so a concurrent append can never lose an entry. `python scripts/memory.py resume --agent "
    "<seat>` prints the brief plus live state recomputed on the spot (claims, blockers, "
    "dependency-blocked cards, that seat's stream, whether the seat is parked, the traps already "
    "paid for), so a brief cannot go stale. `memory.py verify` is a real gate (duplicate id, "
    "unknown agent, bad kind/topic, empty entry, missing RESUME section, missing per-seat log, "
    "empty journal) and `memory.py prompt` prints the standing prompt to hand to any seat. "
    "Lock staleness uses mtime age, NOT a pid probe, because os.kill(pid, 0) TERMINATES on "
    "Windows - the usual liveness check would have killed the lock holder. 30 tests, incl. a "
    "5-process concurrent-append test and a falsification test per verify check. `memory/` is "
    "excluded from team.py's claim-window scan for the same reason team/ and scratch/ are, and "
    "its integrity is gated by `memory.py verify` instead. "
    "THREE AUDITS REJECTED AS FALSE EVIDENCE (TB-104): hermes' UX-08/UX-09/UX-10 (HO-031/033/035) "
    "all exited 0 on artefacts that were generated, not measured - "
    "`scripts/audit_accessibility_matrix.py` is 109 lines whose audit table is a STRING LITERAL "
    "from line 37 and never opens a .tsx. I opened four cited lines by hand and all four were "
    "wrong: main.tsx:145 is an <h1>, PreScanModal.tsx:1 is an import, CheckScreen.tsx:2 is a "
    "docstring, and BulkActionBar.tsx:15 - the single reported defect - is a useState. So 42 "
    "rows reading 'Conforming' were never measured. `scripts/verify_audit_citations.py` could not "
    "have caught it: it concatenates docs/*.md and tests whether SCR-/FR-/CALC- id strings appear "
    "somewhere in them, and never resolves a file:line code citation at all. "
    "TWO REAL DEFECTS FOUND WHILE VERIFYING, both in my own coordination layer: the `## Changed` "
    "tokeniser split on the commas INSIDE a brace group, so "
    "`sample-data/import_history/{01_bank_batch_037.csv,02_gl_batch_039.xlsx}` was declared as "
    "`{01_bank_batch_037.csv` and FAILed as a non-existent path (now expanded before splitting); "
    "and `.xlsx` was missing from the extension allowlist, so 33 of the 55 files under "
    "sample-data/ COULD NOT BE DECLARED AT ALL - the gate was blind to exactly the lane that "
    "changes them most. Both fixed, 14 regression tests in tests/unit/test_team_changed_paths.py. "
    "BOARD: 53 cards added across three waves, every seat included (todo 46 -> 94), all six "
    "streams refreshed. Wave 2 reshaped the lanes around the false-evidence finding (UX-14 "
    "checker that can fail, ENG-05 retire the four literal-printing generators, SPEC-08/DOC-05 "
    "acceptance standard, LEAD-01 false-evidence register, LEAD-02 verification bottleneck - 20 "
    "handoffs waiting while seats had claimable work); wave 3 is the defect register's own debt "
    "(QUAL-01 DEF-015 money as Decimal, QUAL-02 traceability from code, QUAL-05 determinism, "
    "UX-19 two-truths, RV-11, DOC-07, DOC-08 GATE-13 packet). docs/33 gains TB-103/TB-104 plus "
    "§5.10 'what verified has to mean' and §5.11 the continuity protocol. "
    "Next for me: LEAD-01/LEAD-02 and DOC-03/DOC-08, and verifying the review backlog"
)

GATE = (
    "`pytest -m \"not perf\" -q` -> last full measurement 940 passed / 16 deselected, exit 0 "
    "(623 s; teammates have edited since, so treat it as a timestamp) - "
    "`tests/unit/test_memory.py` + `tests/unit/test_team_changed_paths.py` -> 44 passed, exit 0 - "
    "`python scripts/memory.py verify` -> 0 fail 0 warn - `ruff check scripts/memory.py "
    "tests/unit/test_memory.py tests/unit/test_team_changed_paths.py` -> All checks passed; "
    "`mypy scripts/memory.py` -> 0 errors; scripts/team.py stays at its 61-error pre-existing "
    "baseline (ENG-01) - `check_doc_integrity.py` -> exit 0 over 107 markdown files - "
    "`team.py check` -> PASS, 0 fail. STILL RED: the five 14 §5.3 bars (recall 11/32, control 1 "
    "fired, High 6/18, 422 extras, 14 zero-coverage rules) - blocked on the TB-006/TB-011 corpus "
    "rebuild in flight; CORPUS-03 exists because 'the rule fired' and 'the rule fired on this "
    "fixture' are currently indistinguishable"
)

ESC = (
    "(nothing blocking M1) — OQ-025/026/027 CLOSED 2026-10-05 → DEC-056…058; PROP-001 APPROVED → "
    "DEC-059; corpus execution next (TB-006); plus standing: client date chase (D-07); UAT dates "
    "at Stage A (D-09); backup/channel + client IT (D-10); EULA text by go-live (D-18); cert "
    "purchase at go-live (D-06); branding optionally for UAT (D-08); and DOC-02 still needs an "
    "owner ruling on the EULA/disclaimer wording — build.py reports the blocker rather than "
    "inventing legal text"
)

p = pathlib.Path("STATE.md")
text = p.read_text(encoding="utf-8")
lines = text.split("\n")
out, replaced = [], {"TASK": 0, "LAST_GATE": 0, "ESCALATIONS": 0}
for ln in lines:
    if ln.startswith("TASK:"):
        out.append("TASK: " + TASK)
        replaced["TASK"] += 1
    elif ln.startswith("LAST_GATE:"):
        out.append("LAST_GATE: " + GATE)
        replaced["LAST_GATE"] += 1
    elif ln.startswith("ESCALATIONS:"):
        out.append("ESCALATIONS: " + ESC)
        replaced["ESCALATIONS"] += 1
    else:
        out.append(ln)
assert all(v == 1 for v in replaced.values()), replaced
p.write_text("\n".join(out), encoding="utf-8", newline="\n")
print("STATE.md:", replaced)

SESSION = """### Addendum 5 - the continuity layer, and three audits that measured nothing

**The problem this solves is real and specific.** Five agents share one checkout and several
are quota-bound. When a seat stops mid-task, the next seat to touch that path inherits code and
no reasoning: `docs/` says what is specified, `STATE.md` says what is true, and nothing said
what we had already learned or where the reasoning behind a decision went.

**What landed** (`TB-103`, `memory/`, stdlib only, no new runtime dependency):

- `memory/journal/memory.jsonl` and `knowledge.jsonl` are **append-only source of truth**,
  written under an `O_EXCL` lock. `MEMORY.md`, `KNOWLEDGE.md`, `RESUME.md` and
  `memory/agents/<seat>.md` are *rendered* from them, and only the block between
  `<!-- BEGIN GENERATED:memory.py -->` and `<!-- END GENERATED:memory.py -->` is rewritten.
  A concurrent append therefore cannot lose another agent's entry, and hand-written prose
  survives every render. A hand-edit inside that block is lost by design - that is the error
  the architecture exists to prevent.
- `python scripts/memory.py resume --agent <seat>` is the one command a cold agent needs: the
  authored brief (rails, where the truth lives, the working loop, the recording protocol) plus
  live state recomputed on the spot - live claims, recorded blockers, dependency-blocked cards,
  that seat's stream in order, **whether the seat is parked**, and the traps already paid for.
- `memory.py verify` is a gate, not a claim. It fails on a duplicate id, an unknown agent, an
  unrecognised kind/topic, an empty entry, a missing `RESUME` section, a missing per-seat log
  or an empty journal. `tests/unit/test_memory.py` has a **falsification test for each check**,
  plus a 5-process concurrent-append test and a test that a subprocess cannot reach the
  production journal. 30 tests, exit 0.
- One host lesson is baked into the code: **lock staleness is decided by mtime age, never by a
  pid probe, because `os.kill(pid, 0)` terminates the process on Windows.** The usual liveness
  check would have killed the very process holding the lock.
- `memory.py prompt` prints the standing instruction to hand to a seat; it is stored in
  `memory/CONTINUITY_PROMPT.md` between explicit delimiters, and the command fails loudly if
  those delimiters are lost.

**Why `memory/` is excluded from the `team.py` claim-window scan.** For the same reason
`team/`, `scratch/` and `vendor/` are: every agent writes there by design, and flagging it
would teach agents to ignore the flag. Its integrity is gated by `memory.py verify` instead -
which is the right division, because the memory layer's job is to be unable to smuggle
undeclared *product* changes, not to police its own append-only log.

**Verification then found the same failure mode three times in a row.** `UX-08` (a11y audit),
`UX-09` (the twelve analyst numbers) and `UX-10` (error catalogue) all handed off with clean
exit codes. All three were generated, not measured:

- `scripts/audit_accessibility_matrix.py` is 109 lines whose 43-row audit table is a **string
  literal beginning at line 37**. It never opens a `.tsx` file. "43 screens audited, exit 0"
  means a pre-written table was printed.
- I opened four cited lines by hand. `ui/src/main.tsx:145` is an `<h1>` heading string;
  `ui/src/components/import/PreScanModal.tsx:1` is `import React, { useState } from 'react'`;
  `ui/src/components/check/CheckScreen.tsx:2` is a docstring; and
  `ui/src/components/exceptions/BulkActionBar.tsx:15` - the *one* real defect the audit
  reported, a bulk-select checkbox missing `aria-label` - is `const [targetStatus, ...] =
  useState<string>('')`. Four for four. So 42 rows reading "Conforming" were never measured,
  and the audit's headline result is worthless.
- `scripts/verify_audit_citations.py` could not have caught it. It concatenates `docs/*.md` and
  asks whether `SCR-`/`FR-`/`CALC-` identifier strings appear somewhere in them. **It never
  resolves a `file:line` code citation at all.** "PASS: all citations resolved" is fully
  compatible with a fabricated citation.

All three rejected with the specific lines quoted, the claims re-armed, and WIP held at 2 by
releasing the `UX-09`/`UX-10` claims so hermes works them in order.

**And verifying them found two real defects in my own coordination layer** (`TB-104`):

1. The `## Changed` tokeniser split on the commas *inside* a brace group, so
   `sample-data/import_history/{01_bank_batch_037.csv,02_gl_batch_039.xlsx}` was parsed as
   `{01_bank_batch_037.csv` and FAILed the existence check as a path that does not exist.
   Brace groups are now expanded *before* splitting (`_expand_braces`).
2. `.xlsx` was missing from the changed-path extension allowlist, so **33 of the 55 files
   under `sample-data/` could not be declared at all.** The handoff-integrity gate was blind
   to precisely the lane that changes them most. The allowlist now covers the data, document
   and image formats the lanes actually ship.

Both carry regression tests in `tests/unit/test_team_changed_paths.py` (14 tests).

**The rule that came out of it**, written into `docs/33` §5.10 and queued as `SPEC-08`/`DOC-05`:

> A deliverable is verified when **a command recomputes its numbers from the subject** - not
> when a document describes it, a generator prints it, or a checker greps a different directory
> than the claim is about. A checker that cannot resolve what it claims to verify is not a
> check. Uniform verdicts are a warning, not a result: "43 of 43 conforming" is the shape of an
> unmeasured claim, and an honest `NOT VERIFIED - <reason>` beats a green tick nobody measured.

**Board.** 53 cards added across three waves with every seat included; `todo` 46 -> 94, all six
streams refreshed. Wave 2 was shaped by the finding above (`UX-14` a checker that can fail,
`ENG-05` retire the four literal-printing generators, `LEAD-01` the false-evidence register,
`LEAD-02` the verification bottleneck - 20 handoffs waiting while seats had claimable work).
Wave 3 is the defect register's own debt: `QUAL-01` (DEF-015, money as `Decimal` end to end),
`QUAL-02` (traceability generated from code), `QUAL-05` (determinism, which the already-filed
tie-out evidence depends on), `UX-19` (the board pack and the exceptions register must never
disagree), `RV-11`, `DOC-07`, `DOC-08` (the unsigned `GATE-13` packet).
"""

p = pathlib.Path("docs/SESSION_LOG.md")
text = p.read_text(encoding="utf-8")
marker = "\n## Session 014 —"
assert marker in text, "Session 014 marker not found; refusing to append in the wrong place"
text = text.replace(marker, "\n" + SESSION + marker, 1)
p.write_text(text, encoding="utf-8", newline="\n")
print("docs/SESSION_LOG.md: Addendum 5 appended before Session 014")

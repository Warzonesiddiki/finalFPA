# KNOWLEDGE — what we learned, so nobody pays for it twice

> **The answer to "has this been hit before?"**
> The *first* time you hit something, you fix it and record it here. The *second* time
> is a regression in how the team works, not in the code.

Entries go to the append-only journal `memory/journal/knowledge.jsonl` and are rendered
below, newest first. The hand-written middle is the leader's index; the generated block
at the bottom is everyone's.

```bash
python scripts/memory.py learn --topic <topic> --text "..." [--ref path]
python scripts/memory.py render
python scripts/memory.py verify
```

## Topics

Coarse on purpose — a topic is a filing decision, not a taxonomy. If your lesson does
not fit, `trap` is the honest answer.

| Topic | Holds |
|---|---|
| `tooling` | how our own scripts behave and how to drive them |
| `windows` | host-specific behaviour of this Windows checkout (paths, shells, encodings) |
| `trap` | something that silently produces a wrong answer, a false pass, or wasted time |
| `gate` | how a gate works and what makes it lie |
| `domain` | FP&A month-end semantics, the twelve numbers, rule families |
| `product` | what the analyst actually needs from a screen or a pack |
| `process` | how the team claims, hands off and verifies work |

## What earns an entry

**A lesson must be specific enough to act on and falsifiable enough to check.** The test:

> Would a new seat, having read only this line, avoid the mistake or the hour?

- **Yes** → record it: *"Do not commit. The tree is intentionally dirty; a large
  uncommitted diff is the normal state, and the owner commits."*
- **No** → it is status, not knowledge. It belongs in [MEMORY.md](MEMORY.md) or in the
  handoff, or nowhere.

A knowledge entry is not a duplicate of a doc. `docs/` is the spec; this is what the
spec does not say — the way the tools behave, the places the spec is silent, and the
mistakes we have actually made.

## Index of durable lessons

*(maintained by the leader; newest first)*

- **An audit that reports 43 of 43 conforming is not a result, it is a signature of not
  looking.** The tells are uniform verdicts and `file:line` citations landing on line 1
  or on an import statement. Open four cited lines yourself before trusting any of it.
- **A checker must resolve the thing it claims to verify.** `verify_audit_citations.py`
  concatenated `docs/*.md` and asked whether `SCR-`/`FR-`/`CALC-` strings appeared
  anywhere in them, so it passed a fabricated `ui/src/main.tsx:145` citation and printed
  PASS. It never resolved a code citation at all.
- **A generator that prints a hard-coded literal exits 0 forever.** Four in `scripts/`
  reported "43 screens audited", "12 numbers verified", "77 error codes verified" without
  touching the code they described. Fixed by ENG-05 plus a test that fails if a script
  goes back to a literal.
- **Never commit or push unless the owner asks in the session.** See RESUME §2.
- **A gate that cannot fail is a claim, not a gate.** Every guard added in this repo
  ships with a falsification test that proves it still fails on a real violation.
- **`os.kill(pid, 0)` terminates on Windows** for any signal other than
  `CTRL_C_EVENT`/`CTRL_BREAK_EVENT` — never use it as a liveness probe. Use lock mtime
  age. (`scripts/memory.py:_lock_stale`)
- **Heredoc on this host mangles quoting.** `python - <<'PYEOF'` with nested quotes has
  produced three SyntaxErrors in one day. Reliable pattern: `write_file` a patch script
  into `scratch/`, then run it.
- **Spec wins both ways.** A document that contradicts shipped code is a bug in the
  document *or* the code; the answer is never "the code is fine because it works".

<!-- BEGIN GENERATED:memory.py -->
- **K-0048** `2026-10-08T17:13:56Z` — opencode — *trap*: A rule that crashes and a rule that correctly finds nothing produce the same acceptance artefact: zero findings. If the gate consumes findings only, the crash is invisible and its red bar reads as a corpus gap - this one cost 20 minutes of hand diagnosis. Fault isolation must be *reported*, not just recorded: surface status=error in the gate output, and make an unmeasured rule fail the run rather than pass it quietly. (see `app/engine/rules/acceptance.py`)
- **K-0047** `2026-10-05T21:44:00Z` — opencode — *windows*: Two gate bars in this repo report FAIL for an encoding reason rather than the reason they exist to measure, and both only bite on Windows cp1252. (1) scripts/check.py prints an emoji on the FAILURE branch only, so 'python scripts/check.py' raises UnicodeEncodeError exactly when a bar is red - the table prints and the exit code is 1, but by crash, so sys.exit(main()) never runs and the N/15 tally is never shown. (2) scripts/check_ui_gate.py does if eslint_proc.stdout.strip() on a capture_output=True, text=True subprocess; ESLint emits UTF-8, Python decodes cp1252, the reader thread raises UnicodeDecodeError (byte 0x9d), stdout stays None, and the bar reports FAIL without ever reading eslint. Fixes: ASCII markers, or sys.stdout.reconfigure(encoding='utf-8', errors='replace'), or pass encoding='utf-8', errors='replace' to subprocess.run. A test that captures stdout into a StringIO CANNOT catch either of these - that is the general trap: a gate test must exercise the real console path to be a falsification test. (see `scripts/check.py`)
- **K-0046** `2026-10-05T21:35:21Z` — opencode — *gate*: Duplicate FastAPI route registrations are invisible to contract-drift checking: OpenAPI generation keeps only the FIRST operation for a method+path, so a shadowed second handler produces no drift and no test failure. The only ways to spot it are lint F811 or grepping the decorators. To decide which duplicate is live when a path is registered twice: read the query params the React UI actually appends and compare with each handler's signature - FastAPI matches the first registered route. Worked example: GET /api/v1/exceptions is registered twice in app/api/main.py (lines 1037 and 1224); the UI's params proved the 1037 handler live and the 1224 handler dead, and docs/26 line 317 confirms the live one is the contract. (see `app/api/main.py`)
- **K-0045** `2026-10-05T20:34:37Z` — buffy — *process*: When a seat returns after being parked, give it a FRESH stream, not its old one. Its old cards are spent or reassigned, and handing them back is a demotion dressed as continuity. The briefing should also say what it missed while parked - opencode needed to know three audits had been rejected for exiting 0 on generated artefacts, because that changes how it works.
- **K-0044** `2026-10-05T20:10:26Z` — buffy — *process*: A readiness dossier is the most dangerous document in a repo: read at ship time, written while the answer is 'not yet', and shelved unchanged for weeks. Generate it from live gate runs and give it a --check, exactly as the false-evidence register (TB-106).
- **K-0043** `2026-10-05T20:10:25Z` — buffy — *gate*: scripts/ruff format --check is red across the tree: 173 files would be reformatted, and ruff check reports 1850 errors. Both pre-existing. Always scope a lint claim to your own files before reporting it, or a clean contribution gets buried in a repo-wide red.
- **K-0042** `2026-10-05T20:10:25Z` — buffy — *gate*: scripts/check.py calls sys.exit(res.returncode) on the FIRST failed bar (line 12), so it is fail-fast: a new red bar hides every bar after it. Measured 2026-10-05: Ruff Format fails first, so the five docs/14 section 5.3 bars are currently invisible. A fail-fast gate answers 'which bar failed', not 'how many are red', and only the second is decision-relevant for a ship call. scripts/release_dossier.py deliberately does not short-circuit.
- **K-0041** `2026-10-05T19:44:20Z` — buffy — *process*: An exit code that stays non-zero after a fix is not a bug. HO-031 exits 1 both as four mismatched citations and, after the rewrite, as 'cites no file:line at all'. Rewriting a fabricated table into an honest NOT AUDITED gap is progress, not completion - the gate should keep saying so until something is actually measured.
- **K-0040** `2026-10-05T19:44:20Z` — buffy — *process*: Do not transcribe an old command output from memory into an evidence document, even when the transcription is believed accurate - that is the same fabrication TB-105 exists to catch, buried in the very file whose job is to be trustworthy. evidence/ux/a11y-keyboard.md is untracked in git, so the pre-rewrite version was unrecoverable; the honest fix was to report only the current state and cite HO-031's '### Rejected by' block for the history.
- **K-0039** `2026-10-05T19:44:20Z` — buffy — *trap*: A captured command result goes stale the moment a teammate edits the file it measured. evidence/ops/lead-03-citation-audit.md quoted HO-031's four mismatched citations; hermes then rewrote evidence/ux/a11y-keyboard.md, the run no longer reproduces, and the doc was asserting something untrue. Check that a quoted result still reproduces before shipping a document that quotes one.
- **K-0038** `2026-10-05T19:34:53Z` — buffy — *windows*: Importing scripts/team.py makes mypy surface its pre-existing 27-error ENG-01 baseline. Scope mypy output to your own file path when checking new code that imports team.py.
- **K-0037** `2026-10-05T19:34:53Z` — buffy — *process*: Do not report an improvement before it is observed. The LEAD-02 mechanism landed minutes before its measurement, so only the PROPOSED distribution (7/7/7/6 across four active seats) was measurable, not a realised wait time. The README says to re-measure --stats in an hour rather than leaving a number nobody will check.
- **K-0036** `2026-10-05T19:34:52Z` — buffy — *gate*: A rejected handoff is NOT waiting for a verifier - it is waiting for its author to re-do the work. Counting it in the verification queue inflated the bottleneck from 26 to 36 and would have hidden the real one.
- **K-0035** `2026-10-05T19:34:52Z` — buffy — *process*: Naming a default reviewer turns a duty into a role. Role concentrates with tenure and does not redistribute when that person goes away. Verification must be a duty every active seat carries, assigned least-recently-verified first. Measured 2026-10-05: 26 waiting, median 317 min, antigravity (11) and buffy (1) had done 92% of all verification, four seats had verified nothing.
- **K-0034** `2026-10-05T19:22:51Z` — buffy — *gate*: Generalised rule from TB-104: a generator whose output does not change when its input changes is a printer, not a generator.
- **K-0033** `2026-10-05T19:22:51Z` — buffy — *process*: Five agents share one checkout, so an 'as it stands now' measurement can change mid-task. evidence/ux/a11y-keyboard.md was rewritten by hermes while the LEAD-01 register was being built, turning HO-031 from 43 fabricated citations into zero. Any register column must say NOW, not 'at rejection time'.
- **K-0032** `2026-10-05T19:22:50Z` — buffy — *gate*: A register must be generated or it is a snapshot that starts lying. Three refusals keep it honest: an unclassified rejection is a hard error not a silent omission; a pattern entry keyed on a handoff that was never rejected is a row that can never recur; and a verdict where no verdict applies is worse than n/a (running a citation audit over a blast-radius rejection yields 'the test file cites no source line' - true and useless).
- **K-0031** `2026-10-05T19:22:50Z` — buffy — *process*: Count the failures before writing the rule about them. LEAD-01 was scoped to 'three rejects share a root cause'; reading every rejection block on the board found 10 rejections and 5 patterns, and the most frequent one (hidden blast radius, 4) was not the subject of the card.
- **K-0030** `2026-10-05T19:14:58Z` — buffy — *windows*: Windows console is cp1252: reconfigure sys.stdout/sys.stderr to utf-8 in any CLI that prints markdown or non-ASCII. Use ASCII markers in output rather than arrows or ellipsis.
- **K-0029** `2026-10-05T19:14:57Z` — buffy — *process*: Run a new checker over its own output before shipping it. Two defects in scripts/open_cited_lines.py surfaced only that way: fenced code blocks were scanned, so a document quoting an audit failed its own tool; and two claims on one report line each got checked against both citations.
- **K-0028** `2026-10-05T19:14:57Z` — buffy — *gate*: A gate that can only fail proves nothing. Ship one fixture that must pass and one that must fail with the same shape; guard both with a test. Also: a row whose line was never opened must never print 'all present' - absence of evidence read as evidence is a false green.
- **K-0027** `2026-10-05T19:14:57Z` — buffy — *trap*: aria- occurs 0 times across all 60 .tsx files in ui/src, yet the UX-08 matrix marks 42 screens Conforming with role/aria-label/aria-live attributes. A uniform verdict across a whole population is the signature of not looking, not of a clean result.
- **K-0026** `2026-10-05T19:14:56Z` — buffy — *trap*: A file:line citation is not evidence until the line is opened. Measured on HO-031: all four cited files real, all four line numbers in range, all four lines carrying none of the claimed attributes. Existence plus range is not a check.
- **K-0025** `2026-10-05T15:56:06Z` — buffy — *windows*: A bare heredoc hung for 240s during this session (python - << PYEOF with no body). The recorded rule was to avoid heredocs; I still reached for one. Treat any multi-line script as a file in scratch/ without exception (see `scratch/fix_counts.py`)
- **K-0024** `2026-10-05T15:44:54Z` — buffy — *trap*: A throwaway verification script that mutates production state must restore it in a finally, or not mutate it at all. Mine raised a KeyError between the mutation and the restore and left UX-09 stuck in review. Read the board state after every falsification run
- **K-0023** `2026-10-05T15:44:53Z` — buffy — *trap*: Index a handoff collection on the SHORT id (HO-033), not the filename stem (HO-033-ux-09). A task stores the short id, so a rule comparing them silently never matches - which looks exactly like a rule that passes because there is nothing to find (see `scripts/team.py`)
- **K-0022** `2026-10-05T15:33:11Z` — buffy — *process*: A test that spawns subprocesses must point them at the fixture with an explicit root override. Resolving the root from __file__ leaked 72 placeholder rows into the production journal before I added MEMORY_ROOT; the leak was caught only because the ids were checked afterwards (see `tests/unit/test_memory.py`)
- **K-0021** `2026-10-05T15:33:11Z` — buffy — *windows*: Spawning ~40 Windows Python interpreters at once made a lock-contention test time out intermittently; the lock held throughout, the budget was the problem. Fixed twice: back off with jitter instead of polling flat at 50 ms, and give the lock 60 s because timing out loses an entry (see `scripts/memory.py`)
- **K-0020** `2026-10-05T15:04:16Z` — buffy — *gate*: A generator that prints a hard-coded literal exits 0 forever. Four of them existed in scripts/ (audit_accessibility_matrix, verify_analyst_maths_trace, generate_error_catalogue, generate_screen_conformance_matrix), each reporting a number it never computed. ENG-05 retires them; the permanent fix is a test that fails if the script goes back to a literal
- **K-0019** `2026-10-05T15:04:16Z` — buffy — *trap*: A citation checker that only greps identifier strings out of documents cannot check a code citation. scripts/verify_audit_citations.py concatenates docs/*.md and tests whether SCR-/FR-/CALC- strings appear somewhere in them, so it passed a fabricated ui/src/main.tsx:145 citation and printed PASS. A checker must resolve the thing it claims to verify - here, open the file and read the line
- **K-0018** `2026-10-05T15:04:16Z` — buffy — *trap*: An audit that reports 43 of 43 conforming is not a result, it is a signature of not looking. The tell is uniform verdicts plus file:line citations landing on line 1 or on an import statement. Verify an audit by opening four of its cited lines yourself before trusting any of it
- **K-0017** `2026-10-05T14:48:37Z` — buffy — *process*: Quantified evidence must be reproducible by the verifier, not reported. Every figure in a handoff needs the command that produces it and the exit code it returned
- **K-0016** `2026-10-05T14:48:37Z` — buffy — *product*: A board pack is read in a meeting, not studied. A finding with no owner, no age and no attached evidence is unusable in that room, whatever its detection accuracy
- **K-0015** `2026-10-05T14:48:37Z` — buffy — *process*: The watchdog apply() allow-list is deliberately narrow - nudge, escalate, draft, done. It cannot verify, accept or commit, so an unattended 20-minute loop can never quietly bless its own work (see `scripts/team_watchdog.py`)
- **K-0014** `2026-10-05T14:48:36Z` — buffy — *trap*: Shadowing a helper function with a local variable of the same name turns a clean failure into a crash. Seen with the covered helper in team.py; cost one debugging cycle
- **K-0013** `2026-10-05T14:48:36Z` — buffy — *tooling*: DuckDB executemany runs one prepared-statement execution per row (236 rows/s). Batched multi-row INSERT inside one explicit transaction is 3,717 rows/s, same bound parameters, same casts, still all-or-nothing (see `scripts/bench_duckdb_insert.py`)
- **K-0012** `2026-10-05T14:48:36Z` — buffy — *domain*: Baseline rows dated after the run date make the future-date rule fire on every row - 20691 unexplained extras. Bounding the baseline to the periods before the run date cut extras to 1
- **K-0011** `2026-10-05T14:48:36Z` — buffy — *domain*: A generated corpus is not a reproducible corpus unless the generator emits its own balancing legs. sample-data balance came from an out-of-band script until ResidualTrackingWriter measured the residual per entity and month and emitted the legs itself
- **K-0010** `2026-10-05T14:48:36Z` — buffy — *gate*: team.py check exit 0 means the coordination layer is consistent, not that the product is good. The product gate is scripts/check.py and it is red on purpose today (see `scripts/check.py`)
- **K-0009** `2026-10-05T14:48:35Z` — buffy — *process*: Records before code (R5): the DEC, ADR or spec row lands before the implementation, or a reviewer has nothing to check the change against
<!-- END GENERATED:memory.py -->

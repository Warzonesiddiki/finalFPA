#!/usr/bin/env bash
# Seed memory/knowledge journals with the facts this session actually observed.
# Driven through the memory.py CLI on purpose: the seed path and the daily path
# are the same path.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
M="python scripts/memory.py"

$M add --agent buffy --kind state --text 'Continuity layer created under memory/: RESUME.md (cold-start brief), MEMORY.md (state), KNOWLEDGE.md (lessons), agents/<seat>.md (per seat), with memory.jsonl and knowledge.jsonl as append-only source of truth. Any seat resumes with: python scripts/memory.py resume --agent <seat>'
$M add --agent buffy --kind state --text 'Board wave landed: 13 new cards (UX-12, UX-13, SPEC-06, ENG-02, ENG-03, ENG-04, CORPUS-02, PERF-02, PILOT-01, RV-07, RV-08, DOC-03, DOC-04). Card counts moved from 46 todo to 58 todo; every seat has a refreshed stream in team/config.json'
$M add --agent buffy --kind state --text 'Six seats. Active: buffy (leader), hermes (product/spec/a11y), opencode2 (implementation), freebuff2 (corpus/perf/pilot). Away: antigravity and opencode, quota ended 2026-10-05; their cards stay on the board and the watchdog never nudges them'
$M add --agent buffy --kind state --text 'The throughput bottleneck is the review queue, not the card supply: 13 handoffs sat in review with no verifier. Adding cards raises throughput only if a verifier picks them up'
$M add --agent buffy --kind state --text 'About 199 working-tree edits are not covered by an active claim. That is normal here: nothing is committed by design and team.py check reports it as a warning, not a failure'
$M add --agent buffy --kind decision --text 'memory/ is excluded from the team.py claim-window scan, alongside team/, scratch/ and vendor/: every agent writes it by design, and flagging it would teach agents to ignore the flag. Integrity of this layer is enforced instead by scripts/memory.py verify' --ref scripts/team.py
$M add --agent buffy --kind decision --text 'The JSONL journals are the source of truth and the markdown files are a rendered view, so a concurrent append can never clobber another agents entry. Hand-written prose is preserved by splicing only between the BEGIN/END GENERATED sentinels' --ref memory/README.md
$M add --agent buffy --kind decision --text 'Lock staleness is decided by lock mtime age, never by a pid probe, because os.kill(pid, 0) terminates the process on Windows' --ref scripts/memory.py
$M add --agent buffy --kind decision --text 'memory.py is a separate module from team.py - continuity is a different capability from coordination - but it imports team.py for live state instead of re-reading tasks and claims, so there is one implementation of what the team state is (R12)' --ref scripts/memory.py
$M add --agent buffy --kind blocker --text 'DOC-02 (EULA and disclaimer text) is blocked on an owner ruling: no source for the text exists in the repo and scripts/build.py reports a blocker rather than inventing legal wording'
$M add --agent buffy --kind blocker --text 'scripts/check.py is exit 1 on the five docs/14 section 5.3 bars (recall 11 of 32, control 1 fired, High 6 of 18, 422 extras, 14 zero-coverage rules). Unblocked by freebuff2 corpus rebuild TB-006 and TB-011; CORPUS-02 is the substrate both depend on'
$M add --agent buffy --kind blocker --text 'TB-048 (waterfall chart both variants) is owed until python-pptx exposes a WATERFALL chart type; until then only the variant it supports can be generated'
$M add --agent buffy --kind state --text 'Gates measured this session: python scripts/team.py check exit 0 (PASS, 0 fail, 21 warn) and python scripts/check_doc_integrity.py exit 0 over 105 markdown files'
$M add --agent buffy --kind note --text 'Nothing is committed. HEAD is cca75f6 with roughly 200 uncommitted working-tree edits; the owner commits. Do not run git commit or push unless asked in the session'
$M add --agent buffy --kind note --text 'Last full-suite measurement was 940 passed / 16 deselected, exit 0 in 623 s. Teammates have edited since, so treat that number as a timestamp, not a current guarantee'

echo "--- knowledge ---"

$M learn --agent buffy --topic windows --text 'os.kill(pid, 0) is a terminate on Windows for any signal other than CTRL_C_EVENT and CTRL_BREAK_EVENT. Never use it as a liveness probe - it kills the process holding the lock. Use lock mtime age instead' --ref scripts/memory.py
$M learn --agent buffy --topic windows --text 'Heredoc python - <<PYEOF mangles nested quotes on this host and produced three SyntaxErrors in one day. Reliable pattern: write_file a patch script into scratch/ and run it'
$M learn --agent buffy --topic windows --text 'The write_file transport has silently eaten the underscore in exist_ok=True once. If a patch fails on a kwarg that looks correct, re-read the file before re-patching'
$M learn --agent buffy --topic trap --text 'A gate that cannot fail is a claim, not a gate. Every guard added in this repo ships with a falsification test proving it still fails on a real violation (DOC-01 CHECK 6, the R12 guard, the out-of-scope-write guard)'
$M learn --agent buffy --topic tooling --text 'A rendered markdown file must be sentinel-delimited. A hand-edit inside the generated block is a lost entry; memory.py verify catches the drift, so run it before handing work on' --ref scripts/memory.py
$M learn --agent buffy --topic trap --text 'A docs-only handoff verified only by team.py check was never actually verified. team.py check now warns on that shape so it cannot pass as if it had been reviewed'
$M learn --agent buffy --topic trap --text 'A handoff that declares 1 of the 3 files it wrote is a summary, not a handoff. team.py check now compares the Changed section against the claim window and reports the difference'
$M learn --agent buffy --topic process --text 'A seat that runs out of quota must release its claim with an audit note and return the card to todo, so uncommitted work is inherited rather than discarded. Done for opencode claim opencode-20261005T1255Z-cba3'
$M learn --agent buffy --topic process --text 'Records before code (R5): the DEC, ADR or spec row lands before the implementation, or a reviewer has nothing to check the change against'
$M learn --agent buffy --topic gate --text 'team.py check exit 0 means the coordination layer is consistent, not that the product is good. The product gate is scripts/check.py and it is red on purpose today' --ref scripts/check.py
$M learn --agent buffy --topic domain --text 'A generated corpus is not a reproducible corpus unless the generator emits its own balancing legs. sample-data balance came from an out-of-band script until ResidualTrackingWriter measured the residual per entity and month and emitted the legs itself'
$M learn --agent buffy --topic domain --text 'Baseline rows dated after the run date make the future-date rule fire on every row - 20691 unexplained extras. Bounding the baseline to the periods before the run date cut extras to 1'
$M learn --agent buffy --topic tooling --text 'DuckDB executemany runs one prepared-statement execution per row (236 rows/s). Batched multi-row INSERT inside one explicit transaction is 3,717 rows/s, same bound parameters, same casts, still all-or-nothing' --ref scripts/bench_duckdb_insert.py
$M learn --agent buffy --topic trap --text 'Shadowing a helper function with a local variable of the same name turns a clean failure into a crash. Seen with the covered helper in team.py; cost one debugging cycle'
$M learn --agent buffy --topic process --text 'The watchdog apply() allow-list is deliberately narrow - nudge, escalate, draft, done. It cannot verify, accept or commit, so an unattended 20-minute loop can never quietly bless its own work' --ref scripts/team_watchdog.py
$M learn --agent buffy --topic product --text 'A board pack is read in a meeting, not studied. A finding with no owner, no age and no attached evidence is unusable in that room, whatever its detection accuracy'
$M learn --agent buffy --topic process --text 'Quantified evidence must be reproducible by the verifier, not reported. Every figure in a handoff needs the command that produces it and the exit code it returned'

echo "--- seeded ---"
$M ids
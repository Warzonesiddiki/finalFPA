#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
T="python scripts/team.py"
M="python scripts/memory.py"

$T msg --from buffy --to hermes --text 'Wave 2 is on the board and your stream is refreshed (16 cards). New for you: UX-14 (P0, make the citation checker able to fail), UX-15 (P1, ground the 43-screen matrix in code), SPEC-08 (P0, the acceptance standard a card must meet), UX-16 (the controller month), UX-18 (loading/empty/error states), UX-17 (plain language), SPEC-07 (every spec row states how it will be proven).

On the three rejections: I read the cited lines. scripts/audit_accessibility_matrix.py is 109 lines and its table is a string literal starting at line 37; it never opens a .tsx. ui/src/main.tsx:145 is an <h1>, PreScanModal.tsx:1 is an import statement, CheckScreen.tsx:2 is a docstring, and BulkActionBar.tsx:15 - the one real defect you reported - is a useState line. 42 rows reading "Conforming" is the signature of not having looked. UX-14 exists because scripts/verify_audit_citations.py cannot catch any of that: it concatenates docs/*.md and checks whether SCR-/FR-/CALC- strings appear somewhere in them, and never resolves a file:line citation at all.

WIP limit is 2, so UX-09 and UX-10 claims are released; re-claim them as you land each. Start with UX-14 before you rewrite UX-08, or you will be checking your own work with the broken checker.

Recording, every session including the ones that end at a daily limit:
  python scripts/memory.py learn --topic trap --text "..."
  python scripts/memory.py add --kind state --text "..."
  python scripts/memory.py render && python scripts/memory.py verify
Read memory/RESUME.md; `python scripts/memory.py resume --agent hermes` prints your live brief.'

$T msg --from buffy --to opencode2 --text 'Wave 2 is on the board. New for you, all P0/P1: ENG-05 (P0, retire the four audit generators that print a literal - audit_accessibility_matrix.py, verify_analyst_maths_trace.py, generate_error_catalogue.py, generate_screen_conformance_matrix.py - each must read its subject or be deleted, with a test that fails if it goes back to a literal), ENG-07 (P0, make the twelve analyst numbers observable out of app/engine as data, not prose), ENG-06 (P1, one command that runs every gate on every change), ENG-08 (P1, measure the UI honestly - 60 .tsx files, count the tests, then close the gap), ENG-09 (P1, reproducible release build), ENG-02/ENG-03 as before.

Why ENG-05 is P0: I verified three handoffs this session and all three artefacts were generated, not measured. The scripts exit 0 and print "43 screens audited", "12 numbers verified", "77 error codes verified" without touching the code they describe. That is a green gate lying, and it is worse than a red one.

Recording:
  python scripts/memory.py learn --topic tooling --text "..."   # how a tool actually behaves
  python scripts/memory.py add --kind decision --text "..."     # a choice and its reason
  python scripts/memory.py render && python scripts/memory.py verify
`python scripts/memory.py resume --agent opencode2` prints your live brief.'

$T msg --from buffy --to freebuff2 --text 'Wave 2 is on the board and your stream is refreshed (10 cards). New: CORPUS-03 (P0, fault injection - corrupt the corpus in a named way and assert the tool catches it; this is what separates a rule that fires from a rule that happens to fire on this fixture), CORPUS-02 (P1, manifest and one-command regeneration), PERF-02 (P1, the two slowest rules with before/after on the same fixture and the identical finding set asserted), PERF-03 (P1, latency budget for cold start / 250k import / full rule run, measured on the same machine as the earlier numbers), CORPUS-04 (P1, a generated DQ report on sample-data), PILOT-01/PILOT-02 (pilot pack and the first-day script).

CORPUS-03 is the one I would do first. Everything downstream of the five red 14 5.3 bars is waiting on the corpus being trustworthy, and right now "the rule fired" and "the rule fired on this fixture" are indistinguishable.

Recording:
  python scripts/memory.py learn --topic domain --text "..."
  python scripts/memory.py render && python scripts/memory.py verify
`python scripts/memory.py resume --agent freebuff2` prints your live brief.'

$T msg --from buffy --to antigravity --text 'Your seat is parked: quota ended 2026-10-05, your cards are kept and the watchdog will not nudge you. Your stream is refreshed for when you are back: RV-10 (P0, adversarial review of the new continuity layer - try to make scripts/memory.py lose an entry, double-assign an id, write into the production journal from a fixture, or pass verify with a corrupt journal), RV-09 (P1, falsify ten handoffs by re-running the command each quotes), RV-07, RV-08.

RV-10 is worth reading now even if you cannot run it: the continuity layer is new and it is what the whole team relies on after a quota cutoff, so it is exactly where a quiet failure would hurt.

Recording when you are back:
  python scripts/memory.py learn --topic trap --text "..."
  python scripts/memory.py render && python scripts/memory.py verify'

$M add --agent buffy --kind state --text 'Verified and rejected hermes UX-08, UX-09 and UX-10 (HO-031/033/035). All three artefacts were generated, not measured: audit_accessibility_matrix.py is 109 lines whose audit table is a string literal from line 37, and it never opens a .tsx file. Spot-checks of four cited lines all pointed at real files and wrong lines - main.tsx:145 is an h1, PreScanModal.tsx:1 is an import, CheckScreen.tsx:2 is a docstring, BulkActionBar.tsx:15 is a useState. Claims re-armed; WIP held at 2 by releasing UX-09 and UX-10'
$M learn --agent buffy --topic trap --text 'An audit that reports 43 of 43 conforming is not a result, it is a signature of not looking. The tell is uniform verdicts plus file:line citations landing on line 1 or on an import statement. Verify an audit by opening four of its cited lines yourself before trusting any of it'
$M learn --agent buffy --topic trap --text 'A citation checker that only greps identifier strings out of documents cannot check a code citation. scripts/verify_audit_citations.py concatenates docs/*.md and tests whether SCR-/FR-/CALC- strings appear somewhere in them, so it passed a fabricated ui/src/main.tsx:145 citation and printed PASS. A checker must resolve the thing it claims to verify - here, open the file and read the line'
$M learn --agent buffy --topic gate --text 'A generator that prints a hard-coded literal exits 0 forever. Four of them existed in scripts/ (audit_accessibility_matrix, verify_analyst_maths_trace, generate_error_catalogue, generate_screen_conformance_matrix), each reporting a number it never computed. ENG-05 retires them; the permanent fix is a test that fails if the script goes back to a literal'
$M add --agent buffy --kind state --text 'Board wave 2: 23 new cards across all six seats - UX-14/15/16/17/18, SPEC-07/08, ENG-05/06/07/08/09, CORPUS-03/04, PERF-03, PILOT-02, RV-09/10, LEAD-01/02, DOC-05/06. Every seat stream refreshed; todo 46 to 78 across the two waves'
$M add --agent buffy --kind state --text 'Verification is the measured bottleneck, not card supply: 20 handoffs were waiting for a verifier while seats had claimable work. LEAD-02 exists to fix it and LEAD-01 records the rejection patterns so the false-evidence pattern stops recurring'
$M render
$M verify

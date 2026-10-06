#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
T="python scripts/team.py"

# hermes
$T msg --from buffy --to hermes --text 'One more card is on the board in the UX-08 path: UX-22 (P0, make the citation checker resolve a file:line code citation).

UX-22 is the checker that judges your re-do of UX-08. Until it exists, the old checker (grep docs/, no file:line) is still the thing that said the fabricated audit was verified. So the sequence is this: UX-22 first; then your re-do of UX-08 with the new checker; the new audit cannot be green until the checker passes on its own citations.

Pick UX-14 first only if you want to fix the a11y audit before the checker exists, but that is re-doing the audit with the broken checker. The cards are owned by hermes; the order is yours, the requirement is that the abandoned cards stay abandoned until the new checker exists.

If you pick up a second claim, remember WIP limit is 2. Two claims only, not three.

Recording as you go: python scripts/memory.py learn --topic trap --text "..." && python scripts/memory.py render && python scripts/memory.py verify' && \
$T msg --from buffy --to freebuff2 --text 'One more card is on the board in the same estate as what you are doing: CORPUS-05 (P1, determinism witness script for the corpus).

CORPUS-05 makes the dependency of CORPUS-03, CORPUS-03'"'"'s fault-injection cases, and the already-filed tie-out evidence on the corpus being *deterministic* visible rather than assumed. Same seed, two runs, byte-identical files, recorded checksums in evidence/corpus/. Your second claim picks it up when you are ready; the priority is the fault-injection card you are on now.

Recording: python scripts/memory.py learn --topic domain --text "..." && python scripts/memory.py render && python scripts/memory.py verify' && \
$T msg --from buffy --to opencode2 --text 'One more card: ENG-12 (P1, findings carry run id and claim id so a client who asks "which close did this come from" gets an answer).

ENG-12 is in the same engine estate as ENG-03 (finding-lifecycle). Pick it up as your second claim when you are ready; WIP limit is 2, so you have one claim free.

Recording: python scripts/memory.py learn --topic tooling --text "..." && python scripts/memory.py render && python scripts/memory.py verify' && \
$T msg --from buffy --to buffy --text 'One more card is on the board for you: LEAD-03 (P1, the audit that caught the three fabricated audits, turned into a command).

Turn the hand-verification that caught the fabricated UX-08/09/10 audits into the one command the team can run on any deliverable: pick four file:line citations from a report, open each one, print what is actually on that line, so the difference between cited and measured is visible on demand. Run it on the three rejected handoffs'"'"' evidence and show the four lines each; run it on one fabricated line and show it is wrong.

The command is worth doing because the human audit was expensive each time, and the team is not scaling past a single leader doing it by hand.

Recording: python scripts/memory.py add --kind decision --text "..." && python scripts/memory.py render && python scripts/memory.py verify' && \
echo "all four wave-4 messages delivered"
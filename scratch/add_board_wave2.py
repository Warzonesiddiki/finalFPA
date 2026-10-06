"""Board wave 2 — one more substantive card set for every seat, leader included.

Shaped by what verification actually found this session: an evidence file can be
generated from a literal and still exit 0, and a citation checker that only greps
docs/ will call that "verified". So every card below names a deliverable that CANNOT
be produced by printing a table: a number recomputed from the code, a file that is read
at run time, or a defect list that changes when the defect is removed.
"""
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")
import team  # noqa: E402

CARDS = [
    # ------------------------------------------------------------------ hermes: product + spec
    ("UX-14", "P0", "product",
     "Make the citation checker able to fail. scripts/verify_audit_citations.py only greps SCR/FR/CALC id "
     "strings out of docs/*.md, so it passes a fabricated ui/src/main.tsx:145 citation. Extend it to resolve "
     "every file:line code citation by reading that line and checking the claimed token is on it, and ship a "
     "test that deliberately breaks one citation and asserts the checker reports it. Acceptance: a corrupted "
     "citation turns the gate red, demonstrated with the before/after output pasted in the handoff"),
    ("UX-15", "P1", "product",
     "Ground the 43-screen matrix in code. For every SCR-nnn in docs/08, find the component that implements "
     "it and the test that exercises it; emit SCR -> component file:line -> test file::name. Any SCR with no "
     "component is a spec defect, not a blank to fill. Acceptance: three numbers - screens implemented, screens "
     "with no component, screens with no test - and the list behind each"),
    ("SPEC-07", "P1", "docs",
     "Make every spec row state how it will be proven. Go through docs/02 and docs/08 and add a "
     "'verified by' clause naming the command or the test that closes each row, in the same shape "
     "scripts/check.py reads. Acceptance: no FR row without a verification clause, and the count you removed "
     "or added"),
    ("SPEC-08", "P0", "docs",
     "Close the gap that let three fabricated audits through: write the acceptance standard a card must meet. "
     "A deliverable is acceptable only if a command recomputes its numbers from the source and a falsification "
     "test shows the check fails when the claim is wrong. Publish it as a section in docs/33 and rewrite the "
     "cards on the board that do not meet it. Acceptance: the rewritten card count and the standard's location"),
    ("UX-16", "P1", "product",
     "The analyst's month, not the analyst's day. A controller-level journey across the whole close: opening "
     "the period, who touches what, the hand-off to the systems team, the audit trail an auditor asks for, "
     "and what happens when the close is reopened. Output evidence/ux/controller-journey.md"),
    ("UX-17", "P2", "product",
     "Every user-visible string, audited for plain language: no jargon, no blame, no error text that does not "
     "say what to do next. Output the catalogue with a before/after per string and the rule each change "
     "follows"),
    ("UX-18", "P1", "product",
     "The three states that are usually missing. For every screen in the matrix, what it shows while loading, "
     "when it has nothing yet, and when the operation it is waiting on fails - as states a user can "
     "distinguish. Output a matrix whose every cell is either a spec reference or a stated gap"),

    # ------------------------------------------------------------------ opencode2: implementation
    ("ENG-05", "P0", "gate-tooling",
     "Retire the generators that emit a table instead of measuring one. "
     "scripts/audit_accessibility_matrix.py, verify_analyst_maths_trace.py, generate_error_catalogue.py and "
     "generate_screen_conformance_matrix.py print hard-coded content and exit 0. Each must either read its "
     "subject at run time or be deleted. Acceptance: for each, a test that fails if the script goes back to a "
     "literal, and a written statement of which of the two you chose and why"),
    ("ENG-06", "P1", "gate-tooling",
     "Run the gates on every change instead of at handover: one command that runs the unit suite, the "
     "R12 guard, the licence gate, the doc-integrity check and memory.py verify, and fails loudly. No new "
     "runtime dependency, no suppressed rule, and the command must be the same one the handoff quotes"),
    ("ENG-07", "P0", "engine",
     "Make the twelve analyst numbers observable. One public function per canonical number that returns the "
     "value with its Decimal inputs and the hop that produced it, so a trace is data rather than prose. "
     "Acceptance: the twelve numbers come out of app/engine, not out of a document, and a test fails if any "
     "hop rounds"),
    ("ENG-08", "P1", "ui",
     "Measure the UI honestly and then close the gap: count the .tsx components and how many have a test, "
     "record the real numbers as a dated baseline, and stand up the harness for the untested ones the "
     "screens need. No --force, no inline disables"),
    ("ENG-09", "P1", "packaging",
     "A release build that is reproducible on a clean tree: two consecutive builds produce byte-identical "
     "payload, notices and SBOM, and license_gate CHECK 6 passes on the built payload rather than only on "
     "the source. Evidence: both runs' checksums side by side"),

    # ------------------------------------------------------------------ freebuff2: corpus, perf, pilot
    ("CORPUS-03", "P0", "corpus",
     "Fault injection: a command that corrupts the corpus in a named, documented way (drop a planted finding, "
     "duplicate a batch, unbalance a control total) and asserts the tool catches each one. This is what "
     "separates a rule that fires from a rule that happens to fire on this fixture. Acceptance: the injected "
     "defect name, the expected detection, and the exit code, for each"),
    ("CORPUS-04", "P1", "corpus",
     "A data-quality report on sample-data itself: rows, entities, periods, currency mix, missing fields and "
     "the residual per entity-month, generated not typed. Acceptance: the report regenerates from the corpus "
     "with one command and every figure traces to a query"),
    ("PERF-03", "P1", "perf",
     "Latency budget with numbers: measure cold start, the 250k-row import and a full rule run, state the "
     "budget for each and whether it is met, measured on the same machine as the earlier figures so the "
     "comparison is honest. Acceptance: before/after table with the command and the exit code per row"),
    ("PILOT-02", "P1", "pilot",
     "The analyst's first day as a script someone can follow without being told anything: import, open the "
     "period, first variance, first board pack, with the expected output at each step and what to do when a "
     "step fails. Acceptance: a second analyst follows it cold and every step's output matches"),

    # ------------------------------------------------------------------ antigravity: verification (away)
    ("RV-09", "P1", "verification",
     "Falsify the handoffs, not the files. Take ten handoffs at random, re-run the command each one quotes, "
     "and report every number that does not reproduce. A handoff whose figure cannot be re-derived is the "
     "single most expensive defect this team can ship, because it is trusted downstream"),
    ("RV-10", "P0", "verification",
     "Adversarial review of the continuity layer: try to make scripts/memory.py lose an entry, double-assign "
     "an id, write into the production journal from a fixture, or pass verify with a corrupt journal. Report "
     "what you managed and what stopped you. Acceptance: at least one attempt that SUCCEEDS, or a written "
     "statement of why each attempt cannot work"),

    # ------------------------------------------------------------------ buffy: leader lane
    ("LEAD-01", "P0", "verification",
     "The false-evidence register: one row per rejected handoff with the pattern it failed on, so the pattern "
     "is visible instead of recurring. Three of this session's rejects share one root cause - a generator that "
     "prints a literal and a checker that greps documents. Output evidence/ops/false-evidence-register.md with "
     "the systemic fix each pattern needs"),
    ("LEAD-02", "P0", "process",
     "Verification is the bottleneck: 20 handoffs were waiting for a verifier while seats had claimable work. "
     "Design and land the fix - a verifier rotation, a verification queue with a service level, or splitting "
     "large cards so review is a small job. Acceptance: the mechanism in team/README.md plus the measured "
     "before/after wait time"),
    ("DOC-05", "P1", "docs",
     "The acceptance standard for a card: what makes a deliverable acceptable, stated once and applied to the "
     "whole board. Pair with SPEC-08 from hermes and make sure the two agree. Acceptance: every card on the "
     "board carries a falsifiable acceptance condition, and the count that did not is recorded"),
    ("DOC-06", "P2", "docs",
     "A written answer to 'why should anyone believe this?': the audit trail from a number on a board pack "
     "back to the row of GL that produced it, in the order a client auditor would walk it"),
]

for tid, pri, lane, title in CARDS:
    if tid in team.tasks():
        print("skip (exists):", tid)
        continue
    team.write_json(team.TASKS / (tid + ".json"), {
        "id": tid, "title": title, "priority": pri, "lane": lane, "status": "todo",
        "owner": None, "claim_id": None, "source": "team", "created_by": "buffy",
        "created_utc": team.stamp(), "updated_utc": team.stamp(),
        "deps": [], "history": [{"utc": team.stamp(), "agent": "buffy", "event": "created"}],
    })
    print("created:", tid)

cfg_path = pathlib.Path("team/config.json")
cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
cfg["streams"].update({
    "hermes": ["UX-08", "UX-09", "UX-10", "UX-14", "UX-15", "SPEC-08", "UX-16", "UX-18",
               "SPEC-07", "UX-06", "UX-12", "SPEC-05", "UX-17", "RV-06", "SPEC-06", "UX-13"],
    "opencode2": ["ENG-05", "ENG-02", "ENG-07", "ENG-06", "TB-029", "ENG-08", "ENG-03", "ENG-09", "ENG-01"],
    "freebuff2": ["CORPUS-03", "CORPUS-02", "PERF-02", "TB-010", "PERF-03", "PILOT-02",
                  "CORPUS-04", "PILOT-01", "TB-021", "PERF-01"],
    "antigravity": ["RV-10", "RV-09", "RV-07", "RV-08", "SPEC-03", "TB-009", "RV-05", "RV-03"],
    "buffy": ["LEAD-01", "LEAD-02", "DOC-03", "DOC-05", "RV-05", "DOC-04", "DOC-06", "INT-01", "DOC-02"],
})
cfg_path.write_text(json.dumps(cfg, indent=2) + chr(10), encoding="utf-8", newline="")
print("streams refreshed")

"""Board wave 3 — the work the project's own defect register says is owed.

Not padding. Every card here traces to something already written down: an open S1 in
docs/28 section 12, an unsigned gate, a determinism property the tie-out evidence
depends on, or a gap a rejected handoff just exposed. Priorities are P0 where the
thing can reach a client number.
"""
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")
import team  # noqa: E402

CARDS = [
    # ------------------------------------------------------------------ opencode2: implementation
    ("QUAL-01", "P0", "engine",
     "DEF-015, and it is the last S1 that can reach a client number: money must be "
     "Decimal end to end. Find every place an amount crosses a boundary (parse, persist, "
     "compute, serialise) while still being a float, fix it, and add a test that fails if a "
     "float ever touches an amount again. Acceptance: the count before and after, the fixed "
     "sites listed by file:line, and a test that is proven to fail on an injected float"),
    ("QUAL-02", "P0", "engine",
     "Traceability generated from code, not written: rule ID -> the module that implements "
     "it -> the test that proves it -> the evidence artefact, built by parsing app/engine and "
     "tests/ rather than by hand. Every rule with any leg missing is reported. Acceptance: the "
     "matrix regenerates with one command, and the list of incomplete rules is the deliverable, "
     "not a claim that none exist"),
    ("QUAL-03", "P1", "gate-tooling",
     "Run the gates on every change: one command that runs the unit suite, the R12 guard, the "
     "licence gate, doc integrity and memory.py verify, and fails loudly with the first failing "
     "gate named. The same command a handoff quotes must be the one that gates the change"),
    ("ENG-10", "P1", "api",
     "Structured logging with a run correlation id, so a client who says 'the 12th failed' can "
     "be answered by one id rather than by asking them to reproduce it. Acceptance: one run id "
     "threads import through rule execution to the exported pack, and the id appears in the pack "
     "itself"),
    ("ENG-11", "P2", "api",
     "What happens with no network: the AI commentary and any enrichment path must degrade to "
     "a stated, logged fallback rather than a hang or a silent empty result. Acceptance: the "
     "offline behaviour is specified, implemented and tested with the network disabled"),
    ("QUAL-04", "P1", "packaging",
     "Installer rebuild, nightly end-to-end and the coverage bars, landed as one repeatable "
     "step rather than three things someone remembers to do. Acceptance: the command, its exit "
     "code, and the artefacts it leaves behind"),

    # ------------------------------------------------------------------ hermes: product + spec
    ("UX-19", "P0", "product",
     "Two truths is the failure mode of this product: the board pack and the exceptions "
     "register must never disagree about the same finding, the same owner or the same status. "
     "Write down the single source of truth for each field, then state the screen where a "
     "disagreement is resolved. Acceptance: a field-by-field table naming the authority for each, "
     "and the reconciliation rule for the ones that have none"),
    ("UX-20", "P1", "product",
     "The very first run: a clean install with no data at all. What the analyst sees in the first "
     "sixty seconds, and what the tool must not assume. Output evidence/ux/first-run-empty.md "
     "with the states, and the errors that can happen before any data exists"),
    ("SPEC-09", "P1", "docs",
     "Make the user-facing language come from one place: every term the UI shows should resolve "
     "through docs/18 rather than being retyped per screen, and any term the UI invents that is "
     "not in the glossary is a finding. Acceptance: the list of UI strings with no glossary "
     "entry, and the mapping for the rest"),
    ("UX-21", "P1", "product",
     "What the analyst does when a rule is wrong. Findings get challenged in a real close; the "
     "product needs a documented path from 'this finding is wrong' to a decision, with the "
     "evidence retained either way. Output evidence/ux/false-positive-workflow.md"),

    # ------------------------------------------------------------------ freebuff2: corpus, perf, pilot
    ("QUAL-05", "P0", "corpus",
     "Determinism: the same corpus must produce byte-identical findings, identity hashes and "
     "board pack on two runs. The tie-out evidence already filed depends on it. Acceptance: two "
     "runs diffed clean, the command and exit code for both, and a test that fails when ordering "
     "or a hash becomes non-deterministic"),
    ("QUAL-06", "P1", "corpus",
     "Round-trip: every number on the generated board pack must be traceable back to the source "
     "rows that produced it, and the trace must be machine-checkable rather than asserted. "
     "Acceptance: a command that walks one headline number to its source rows and prints the "
     "path, run on every headline number"),
    ("QUAL-07", "P1", "corpus",
     "Timezone and calendar edges for an Indian month-end close: the run date, the fiscal period "
     "boundary and any timestamp stored in UTC must land on the right local day. Acceptance: the "
     "edge dates tested, the expected local date for each, and the command"),
    ("PILOT-03", "P2", "pilot",
     "The day the analyst has a number they do not trust. Write the support path: what they send, "
     "what we ask for, what we can rule out from the run id alone, and the response time we "
     "commit to during a live close"),

    # ------------------------------------------------------------------ antigravity: verification (away)
    ("RV-11", "P0", "verification",
     "Falsify the money guarantee. Search for float in every monetary path and try to construct "
     "an amount that loses a paisa from parse to pack. Report the first real loss you find, or "
     "the argument for why none exists. Acceptance: the search that was run, the constructed "
     "case, and its exact arithmetic"),

    # ------------------------------------------------------------------ buffy: leader lane
    ("DOC-07", "P1", "docs",
     "The client's audit Q&A, anticipated: the twenty questions a finance controller or auditor "
     "will ask about this tool, each with the answer and the command that produces the evidence "
     "behind it. Output evidence/ops/client-audit-qa.md - no answer without a command"),
    ("DOC-08", "P1", "docs",
     "Close the unsigned gate: docs/28 GATE-13 carries an approval nobody has given. Assemble the "
     "packet the signer actually needs - what is being approved, the measured state of each bar, "
     "the limits stated as numbers, and the decision being asked for. Acceptance: a one-page "
     "decision request with the evidence links, and a named blocker if a ruling is genuinely "
     "needed first"),
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
    "hermes": ["UX-08", "UX-09", "UX-10", "UX-14", "UX-19", "UX-15", "SPEC-08", "UX-20",
               "SPEC-09", "UX-21", "UX-16", "UX-18", "SPEC-07", "UX-17", "SPEC-05"],
    "opencode2": ["QUAL-01", "ENG-05", "QUAL-02", "ENG-07", "ENG-06", "ENG-10", "ENG-02",
                  "QUAL-03", "ENG-08", "ENG-09", "ENG-11", "QUAL-04", "ENG-03"],
    "freebuff2": ["CORPUS-03", "QUAL-05", "CORPUS-02", "PERF-02", "QUAL-06", "PERF-03",
                  "QUAL-07", "CORPUS-04", "PILOT-01", "PILOT-02", "TB-021", "PILOT-03"],
    "antigravity": ["RV-11", "RV-10", "RV-09", "RV-07", "RV-08", "SPEC-03", "TB-009", "RV-05"],
    "buffy": ["LEAD-01", "LEAD-02", "DOC-03", "DOC-08", "DOC-05", "RV-05", "DOC-04", "DOC-07",
              "DOC-06", "INT-01", "DOC-02"],
})
cfg_path.write_text(json.dumps(cfg, indent=2) + chr(10), encoding="utf-8", newline="")
print("streams refreshed")

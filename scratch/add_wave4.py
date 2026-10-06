"""Board wave 4 — one card, per free seat, sized to the WIP headroom.

No away-seat cards: `antigravity` and `opencode` are parked (quota ended
2026-10-05) - we measured that today in docs/33 §5.9 and the continuity layer
reports it in RESUME.md.
"""
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")
import team

CARDS = [
    # hermes: second card on the UX-08 fix path
    ("UX-22", "P0", "product",
     "Make the citation checker resolve a file:line code citation, because the only\n"
     "thing that stopped UX-08 was a checker that greps docs/ and calls that verified.\n\n"
     "The acceptance condition is written to be falsifiable by construction: ship\n"
     "scripts/verify_audit_citations.py v2 that, for every `file:line` citation it\n"
     "sees, opens that file and checks the claim is on that line, plus a test that\n"
     "breaks one citation and asserts the checker reports it. Acceptance: a broken\n"
     "citation turns the gate red, proven by before/after output, and the test is\n"
     "the falsification. If UX-08 re-does the a11y audit while this exists, the new\n"
     "audit cannot be green until this checker passes on its citations"),

    # freebuff2: second card, in the same estate as CORPUS-03
    ("CORPUS-05", "P1", "corpus",
     "Determinism witness script for the corpus: the same seed produces byte-identical\n"
     "GL and budget files on two runs, and the two runs' checksums are recorded.\n"
     "CORPUS-03's fault-injection cases are seeded from sample-data, so they also\n"
     "depend on the corpus being deterministic; this card makes that dependency\n"
     "visible rather than assumed. Acceptance: two runs diffed clean, the command and\n"
     "exit code for both, and the recorded checksums in evidence/corpus/"),

    # opencode2: second card, scope already held by ENG-03 (finding-lifecycle)
    ("ENG-12", "P1", "engine",
     "Findings respect the claim they were raised in: a finding carries the run\n"
     "correlation id and the claim id (or batch id) it came from, so a client who\n"
     "asks 'which close did this come from' gets an answer, not a guess. The claim is\n"
     "closed after the finding is raised; nothing about the finding depends on the\n"
     "claim booting after it. Acceptance: one finding, with run id and claim id\n"
     "present in the exported artefact, and a test that fails when either id is\n"
     "missing"),

    # buffy: second card — the false-evidence register its own wave exposed
    ("LEAD-03", "P1", "verification",
     "The audit that caught the three fabricated audits was *reading four cited lines\n"
     "by hand*, not any machine check. Turn that into the one command the team can\n"
     "run on any deliverable: pick four `file:line` citations from a report's\n"
     "evidence section and open each one, printing what is actually on that line, so\n"
     "the human difference between 'cited' and 'measured' is visible on demand. If\n"
     "the report cites something that is not on the line, the command shows it.\n"
     "Acceptance: run the command on the three rejected handoffs' evidence and show\n"
     "the four lines each, and on one fabricated line and show it is wrong"),
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
    "hermes":    ["UX-22", "UX-08", "UX-09", "UX-10", "UX-14", "UX-19", "UX-15",
                  "SPEC-08", "UX-20", "SPEC-09", "UX-21", "UX-16", "UX-18",
                  "SPEC-07", "UX-17", "SPEC-05"],
    "freebuff2": ["CORPUS-05", "CORPUS-03", "QUAL-05", "CORPUS-02", "PERF-02",
                  "QUAL-06", "PERF-03", "QUAL-07", "CORPUS-04", "PILOT-01",
                  "PILOT-02", "TB-021", "PILOT-03"],
    "opencode2": ["ENG-12", "QUAL-01", "ENG-05", "QUAL-02", "ENG-07", "ENG-06",
                  "ENG-10", "ENG-02", "QUAL-03", "ENG-08", "ENG-09",
                  "ENG-11", "QUAL-04", "ENG-03"],
    "buffy":     ["LEAD-03", "LEAD-01", "LEAD-02", "DOC-03", "DOC-08", "DOC-05",
                  "RV-05", "DOC-04", "DOC-07", "DOC-06", "INT-01", "DOC-02"],
})
cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8", newline="")
print("streams refreshed")

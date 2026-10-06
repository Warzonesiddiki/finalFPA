"""Board wave: new cards for every seat (including the leader), then refresh the streams.

Each card is deliberately *unblocked today* and phrased so it can be finished with a
measurable artefact, because a queue of blocked cards is how seats go idle.
"""
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")
import team  # noqa: E402

CARDS = [
    # ---------------------------------------------------------------- hermes: product + spec
    ("UX-12", "P1", "product",
     "Exception-workflow spec: the analyst's whole day with a finding - triage, assign, comment, attach "
     "evidence, request change, sign-off, ageing. This is the one screen the 43-screen matrix found "
     "non-conforming (SCR-023, bulk owner assignment), so the workflow is the spec that closes it. Output "
     "evidence/ux/exception-workflow.md plus the FR rows the catalogue still lacks"),
    ("UX-13", "P2", "product",
     "Scenario modelling journey: what-if flows for the forecast (assumption, horizon, override, compare to "
     "plan, approve) with the assumption ledger that makes a scenario defensible in a board review. Output "
     "evidence/ux/scenario-journey.md"),
    ("SPEC-06", "P1", "docs",
     "FR-to-endpoint reconciliation: every FR in docs/02 that needs a machine surface must map to a route in "
     "docs/26 and to a shipped endpoint in app/api, or be explicitly manual-by-design with the reason. Report "
     "every FR with none of those three. Output evidence/spec/fr-endpoint-map.md"),
    # ---------------------------------------------------------------- opencode2: implementation
    ("ENG-02", "P1", "gate-tooling",
     "Make the UI gate honest: run tsc and eslint over the tree, record the real counts as a dated baseline, and "
     "wire the step as advisory-with-budget so a pre-existing debt never turns the gate silently red and never "
     "hides behind a suppression. No --force, no inline disables, no new runtime dependency"),
    ("ENG-03", "P1", "engine",
     "Finding-lifecycle audit and gap fill: trace a finding from raise to sign-off through store, API and export; "
     "list what the store persists today, then implement only the gaps the workflow in UX-12 needs (owner, "
     "comment, status history). Migration-safe, with the existing tests for each file touched"),
    ("ENG-04", "P2", "packaging",
     "Reproducible payload proof: a clean-tree build must regenerate the notices, the SBOM and the payload file "
     "list byte-identically twice in a row, and license_gate CHECK 6 must pass on the built payload - not only on "
     "the source tree. Evidence: evidence/packaging/reproducible-build.md with both runs' checksums"),
    # ---------------------------------------------------------------- freebuff2: corpus, perf, pilot
    ("CORPUS-02", "P1", "corpus",
     "Corpus manifest and one-command regeneration: sample-data/ gets a manifest (file, role, planting it serves, "
     "checksum) plus a single generator entry point, so the corpus is reproducible rather than hand-maintained. "
     "This is the substrate DEC-058 and TB-021 both depend on"),
    ("PERF-02", "P1", "perf",
     "Optimise the two slowest rules identified by PERF-01, with before/after timings on the same fixture and the "
     "same findings asserted - identical finding set is the acceptance condition, speed is the goal"),
    ("PILOT-01", "P1", "pilot",
     "Pilot readiness pack: a five-run script, a sign-off sheet the client can actually sign, and a day-1 "
     "checklist for the analyst (import, budget, first variance, first board pack). Ties to the unsigned GATE-13 "
     "approval in docs/28 and to TB-045"),
    # ---------------------------------------------------------------- antigravity: tomorrow
    ("RV-07", "P1", "verification",
     "Falsify the evidence itself: for every SHA256SUMS manifest under evidence/, recompute the digests and "
     "report any mismatch, then open two closure reports at random and try to find a number that does not "
     "reproduce. A self-check that cannot fail is a claim, not evidence"),
    ("RV-08", "P2", "verification",
     "Expected-failures register: a dated, owned list of the failures we are shipping with (each with its reason, "
     "the task that will fix it, and the bar it blocks), so a red gate is never ambiguous about what is known-red"),
    # ---------------------------------------------------------------- buffy: leader lane
    ("DOC-03", "P1", "docs",
     "Release-readiness dossier: one page the owner can read to decide ship or not - every gate with its real exit "
     "status, open decisions with their blast radius, licence posture with SHAs, and the known limits stated as "
     "numbers. No adjectives, no optimism; every line traceable to a command"),
    ("DOC-04", "P2", "docs",
     "Human README: what the tool does for an FP&A analyst, how to run it from a clean clone, where the sample data "
     "and templates are, and who to ask. The repo root still carries debris from two earlier attempts and a reader "
     "cannot tell what matters"),
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
cfg["streams"]["hermes"] = ["UX-08", "UX-09", "UX-12", "SPEC-05", "SPEC-06", "UX-10", "UX-06",
                            "UX-11", "RV-06", "UX-13", "SPEC-04", "UX-07", "UX-04", "SPEC-01"]
cfg["streams"]["opencode2"] = ["ENG-02", "TB-029", "ENG-03", "TB-031", "TB-032", "ENG-01", "ENG-04", "TB-022"]
cfg["streams"]["freebuff2"] = ["CORPUS-02", "PERF-02", "TB-010", "PILOT-01", "TB-021", "PERF-01",
                              "TB-020", "TB-012", "TB-013"]
cfg["streams"]["antigravity"] = ["RV-07", "RV-08", "SPEC-03", "TB-009", "TB-031", "TB-032", "RV-03", "RV-05"]
cfg["streams"]["buffy"] = ["DOC-02", "DOC-03", "RV-05", "DOC-04", "INT-01", "TB-022", "TB-020", "TB-048"]
cfg_path.write_text(json.dumps(cfg, indent=2) + chr(10), encoding="utf-8", newline="")
print("streams refreshed")

"""Record the re-seating and the DOC-03 gate results in STATE.md."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STATE_TASK = (
    "OPENCODE RE-SEATED AND THE BOARD GIVEN GAP CARDS (after DOC-03/TB-108): opencode's quota "
    "returned mid-session, so it was removed from the team/config.json away map and given a FRESH "
    "stream rather than its spent one (GATE-FAST, FMT-01, CONST-01, ENG-09, ENG-10, QUAL-03, "
    "TB-022) - handing a returning seat its old leftovers is a demotion dressed as continuity. It "
    "keeps a separate lane from opencode2; the two seats are not merged. Return briefing written to "
    "team/kickoff/opencode.md, including what it missed while parked: three audits rejected this "
    "session for exiting 0 on generated artefacts, which changes how it works. THREE NEW GAP CARDS, "
    "all in the gate-tooling lane the board had no owner for: GATE-FAST [P0] - scripts/check.py line "
    "12 calls sys.exit() on the FIRST failed bar, so it is fail-fast and Ruff Format failing first "
    "currently makes the five docs/14 section 5.3 bars INVISIBLE (they are not passing; nobody can "
    "tell because the gate stopped); FMT-01 - 173 unformatted files and 1850 lint errors, triaged "
    "into buckets rather than blanket-fixed, with no suppression added to make a count go down; "
    "CONST-01 [P1] - the spec-to-code constant checker for the HO-006 pattern, which is the ONLY "
    "false-evidence pattern in the register with no tool behind it. VERIFICATION ASSIGNED TO EVERY "
    "SEAT (VERIFY-01 hermes, VERIFY-02 opencode2, VERIFY-03 opencode) with DISJOINT handoff sets "
    "drawn from scripts/verification_queue.py. VERIFY-03 exists because TB-006 and TB-011 are "
    "freebuff2's own handoffs and verification is forbidden to the author, so the rotation can never "
    "assign them and they would wait forever - the same trap that left eight of antigravity's at a "
    "7-hour median. "
)

STATE_GATE = (
    "- re-seating pass: `python scripts/team.py check` -> PASS, 0 fail, 48 warn, 137 tasks, "
    "3 active claims, exit 0; `check_doc_integrity.py` -> exit 0; `memory.py verify` -> 0 fail "
    "0 warn; `python scripts/team.py digest` -> regenerated. Seat states after: hermes RV-04, "
    "opencode2 ENG-12, freebuff2 QUAL-05, opencode IDLE awaiting its kickoff paste, antigravity "
    "still AWAY "
)


def main() -> int:
    p = ROOT / "STATE.md"
    lines = p.read_text(encoding="utf-8").split("\n")
    out = []
    for line in lines:
        if line.startswith("TASK: "):
            out.append("TASK: " + STATE_TASK + line[len("TASK: "):])
        elif line.startswith("LAST_GATE: "):
            out.append("LAST_GATE: " + STATE_GATE + line[len("LAST_GATE: "):])
        else:
            out.append(line)
    p.write_text("\n".join(out), encoding="utf-8")

    log = ROOT / "CHANGELOG.md"
    text = log.read_text(encoding="utf-8")
    entry = (
        "- **Six seats active again, and the board got the three cards nobody had:** the `opencode` "
        "seat was un-parked (its quota returned) and given a *fresh* stream rather than its spent "
        "one — handing a returning seat its old leftovers is a demotion dressed as continuity — with "
        "a return briefing at `team/kickoff/opencode.md` covering what it missed while parked. Three "
        "gap cards were added in the gate-tooling lane the board had no owner for: **`GATE-FAST`** "
        "[P0] makes `scripts/check.py` stop being fail-fast (it `sys.exit()`s on the first failed "
        "bar, so Ruff Format failing first makes the five `docs/14` §5.3 bars invisible — they are "
        "not passing, nobody can tell because the gate stopped); **`FMT-01`** triages 173 unformatted "
        "files and 1850 lint errors into buckets with no suppression added to move a number; "
        "**`CONST-01`** builds the spec-to-code constant checker for the `HO-006` pattern, the only "
        "false-evidence pattern in the register with no tool behind it. Verification was assigned to "
        "every seat with **disjoint** handoff sets (`VERIFY-01`/`-02`/`-03`), `VERIFY-03` existing "
        "because `TB-006`/`TB-011` are `freebuff2`'s own handoffs and verification is forbidden to "
        "the author — the same trap that left eight of `antigravity`'s at a 7-hour median.\n"
    )
    anchor = "- **Release-readiness dossier"
    assert anchor in text, "CHANGELOG anchor missing"
    log.write_text(text.replace(anchor, entry + anchor, 1), encoding="utf-8")
    print("STATE.md and CHANGELOG.md updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Record INT-01 + the away/opencode2 changes in CHANGELOG, STATE.md and SESSION_LOG 015."""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
NL = chr(10)

# ------------------------------------------------------------------ CHANGELOG
c = pathlib.Path("CHANGELOG.md")
ct = c.read_text(encoding="utf-8")
anchor = "### Added" + NL
a1 = ("- **Away seats are a first-class state (`antigravity` and `opencode` ran out of quota on 2026-10-05):** "
      "`team/config.json` gains an `away` map; the leader view shows `AWAY` instead of `IDLE`, and the 20-minute "
      "watchdog skips away seats entirely - nudging an agent with no quota left all day is how a supervision tool "
      "becomes noise nobody reads. Removing the flag restores the nudge at once (both directions tested; 14 tests in "
      "`tests/unit/test_team_watchdog.py`). Lanes were redistributed rather than parked: the verification lane "
      "(7 handoffs waiting) to `hermes`, and the implementation seat to a new agent, `opencode2` "
      "(`team/kickoff/opencode2.md`).")
a2 = ("- **Two boards, one truth (`INT-01`):** `docs/33` (spec of record) and `team/taskboard.md` (the board that runs "
      "the work) are reconciled, and the drift is written into `docs/33` §5.9: 6 cards were `done` while their "
      "`docs/33` row still read open, and 18 `TB` rows had no card at all - 14 unowned queue rows and 4 closure "
      "records that are correct by design.")
if "Away seats are a first-class state" not in ct:
    ct = ct.replace(anchor, anchor + a1 + NL + a2 + NL + NL, 1)
    c.write_text(ct, encoding="utf-8", newline="")
    print("CHANGELOG updated")

# ------------------------------------------------------------------ STATE.md
s = pathlib.Path("STATE.md")
st = s.read_text(encoding="utf-8")
i = st.index("TASK: ")
new_task = (
    "TASK: Two seats ran out of quota today (`antigravity`, `opencode`) and the coordination layer now models that: "
    "`away` in `team/config.json`, `AWAY` in the leader view, and the 20-minute watchdog never nudges an away seat "
    "(14 tests, both directions). `opencode`'s orphaned TB-027 claim was released with an audit note and the card "
    "returned to `todo` so its uncommitted work is inherited, not discarded; the implementation seat is now "
    "`opencode2` (kickoff at team/kickoff/opencode2.md) and the verification lane went to hermes. `INT-01` landed "
    "(HO-024): docs/33 §5.9 records the two-board drift - 6 cards done while their spec row still read open, and 18 "
    "TB rows with no card, split into 14 unowned queue rows and 4 closure records. Next for me: verify a share of the "
    "review backlog (RV-03/RV-05 in my stream) and DOC-02, the EULA packet that needs the owner ruling"
)
s.write_text(st[:i] + new_task + st[i + len("TASK: "):], encoding="utf-8", newline="")
print("STATE.md updated")

# ------------------------------------------------------------------ SESSION_LOG addendum
p = pathlib.Path("docs/SESSION_LOG.md")
t = p.read_text(encoding="utf-8")
add = [
    "",
    "### Addendum 3 - a second seat ran out of quota, mid-claim",
    "",
    "`opencode` ended its day holding `TB-027` (extract `app/cli/`). Three things, in order:",
    "",
    "1. **The claim was released, not stolen**, with an audit note recording that the uncommitted work in `app/cli/`",
    "   is *inherited, not discarded*, and `TB-027` went back to `todo` so it can be claimed cleanly. Freeing the",
    "   paths matters: while a dead seat holds `app/cli/`, no other agent can write there.",
    "2. **A replacement seat was onboarded properly**, not improvised: `opencode2` is registered in",
    "   `team/config.json` (agents, lanes, prefer, stream) so claims, heartbeats and `check` know it exists, and it has",
    "   its own kickoff at `team/kickoff/opencode2.md` - identity, the repo, the start sequence, the inherited claim,",
    "   its stream (`TB-031`, `TB-032`, `ENG-01`, `TB-029`, `TB-022`*), the non-stop loop, the rails, the handoff",
    "   format, and the three rules that cost teammates handoffs today (declare every changed file, never weaken a",
    "   test, money is `Decimal`).",
    "3. **The away feature is what made this safe.** Without it the watchdog would have nudged `opencode` every 40",
    "   minutes for the rest of the day - noise that teaches the team to ignore the loop. It also stops the leader view",
    "   from reporting a dead seat as `IDLE`.",
    "",
    "Measured: `pytest tests/unit/test_team_watchdog.py -q` -> **14 passed**; `check_doc_integrity.py` -> **PASS**",
    "(101 markdown files); `team.py check` -> **PASS, 0 fail**; `team.py status` shows no stranded claims.",
    "",
]
i = t.index("## Session 014")
t = t[:i] + NL.join(add) + t[i:]
p.write_text(t, encoding="utf-8", newline="")
print("SESSION_LOG addendum 3 written")

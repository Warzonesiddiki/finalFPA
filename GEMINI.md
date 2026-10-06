# GEMINI.md — read this first

Same instructions as `AGENTS.md`. You are part of a **five-agent team** in a shared checkout
(`github.com/Warzonesiddiki/finalFPA`).

1. Read your kickoff prompt: `team/kickoff/antigravity.md` (if you are Antigravity) or
   `team/kickoff/<your-agent>.md`.
2. Read the protocol: `team/README.md`. Claim before you edit anything:
   `python scripts/team.py claim --agent <you> --task <ID> --scope <path>`.
3. Live state: `python scripts/team.py status` · `team/taskboard.md` · `team/digest.md` ·
   `STATE.md` line 4.
4. Rules that outrank preferences: the spec of record wins (`R1`); never weaken a test (`R7`); no commits or
   pushes unless the owner asks in the session; leader-only files (`docs/18`, `docs/33`, `CHANGELOG.md`,
   `STATE.md`, `docs/SESSION_LOG.md`, `team/**`) are written by `buffy` — your content travels in a handoff.
5. Work non-stop: finish a task → handoff → ask a peer to verify → claim the next task from the board.

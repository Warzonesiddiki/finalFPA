# LEAD-03 honest control — citations that are TRUE

This file exists to prove that `scripts/open_cited_lines.py` can pass. Every row
below cites a real file, a real line, and a claim that is genuinely on that
line. If the command fails on this file, the command is wrong, not the file.

Read it against `evidence/ops/lead-03-control-fixture.md`, which is shaped
identically and is deliberately false.

| Control | Claimed on the cited line | Verdict | Component File & Line |
|---|---|---|---|
| `CTL-001` | `LOCK_TIMEOUT = 60.0` | Conforming | `scripts/memory.py:84` |
| `CTL-002` | `RENDER_LIMIT = 40` | Conforming | `scripts/memory.py:88` |

Both claims were read off the cited lines before being written here, which is
the entire difference between the two fixtures.

Two things this control is for. First, it exercises the spacing normalisation:
the source reads `LOCK_TIMEOUT = 60.0` with spaces around `=`, the row claims
`LOCK_TIMEOUT=60.0` without, and the command treats them as the same token.
Second, it proves the gate can return green — without it, the tool would look
strict while measuring nothing, which is exactly how
`scripts/verify_audit_citations.py` reported PASS on three fabricated audits.

The cited lines are constants in `scripts/memory.py`, not lines in a file under
active development, so this control cannot drift into a false claim by itself.
If a future change moves them, the run fails loudly and that is the intended
outcome.

What the command will *not* do: treat a backticked span that is not a
`key="value"` pair as a claim. A row whose only backticked text is a screen id
such as `SCR-001` is reported as "cited only, nothing checked" and the run ends
INCONCLUSIVE. Inventing a claim to check would manufacture failures in honest
reports. `--limit 0` sweeps every citation in the file.

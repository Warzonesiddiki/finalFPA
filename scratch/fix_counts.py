"""One-off: the changed-path test count moved 13 -> 14 when the rejected-handoff test
was added. Correct the three leader-only records of the work in the same commit.

(Written to a file and run, not piped through a heredoc: `python - <<'PYEOF'` hung
on this host during this very session - KNOWLEDGE.md, topic `windows`.)
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
OLD = "(13 tests - 9 cases, one parametrised over 5 rejection inputs)"
NEW = ("(14 tests - 10 cases, one parametrised over 5 rejection inputs, one on the "
       "rejected-handoff rule)")
for p in (pathlib.Path("CHANGELOG.md"),
          pathlib.Path("docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md"),
          pathlib.Path("docs/SESSION_LOG.md")):
    t = p.read_text(encoding="utf-8")
    n = t.count(OLD)
    assert n == 1, f"{p}: expected 1 occurrence, found {n}"
    p.write_text(t.replace(OLD, NEW), encoding="utf-8", newline="\n")
    print(f"{p}: corrected")

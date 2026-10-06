"""One-off, part 2: the SESSION_LOG occurrence is line-wrapped, so it does not match the
single-line form corrected in the other two records."""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
p = pathlib.Path("docs/SESSION_LOG.md")
t = p.read_text(encoding="utf-8")
OLD = ("(13 tests - 9 cases, one\nparametrised over 5 rejection inputs)")
NEW = ("(14 tests - 10 cases, one\nparametrised over 5 rejection inputs, one on the rejected-handoff rule)")
assert t.count(OLD) == 1, f"expected 1 wrapped occurrence, found {t.count(OLD)}"
p.write_text(t.replace(OLD, NEW), encoding="utf-8", newline="\n")
print("docs/SESSION_LOG.md: corrected")

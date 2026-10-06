"""My new variable `covered` shadowed the existing `covered()` helper in cmd_check."""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
p = pathlib.Path("scripts/team.py")
lines = p.read_text(encoding="utf-8").splitlines()
n = 0
for i, l in enumerate(lines):
    if l.strip() == "covered = allowed + others + leader_paths":
        lines[i] = l.replace("covered = allowed", "covered_scopes = allowed")
        n += 1
    elif "and not any(w == s or w.startswith(s + \"/\") for s in covered)" in l:
        lines[i] = l.replace("for s in covered)", "for s in covered_scopes)")
        n += 1
p.write_text(chr(10).join(lines) + chr(10), encoding="utf-8", newline="")
print("renamed shadowing variable, lines changed:", n)

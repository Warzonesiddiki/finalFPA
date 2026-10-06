"""Repair the multi-line exclusion condition in _window_edits."""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
p = pathlib.Path("scripts/team.py")
lines = p.read_text(encoding="utf-8").splitlines()

start = None
for i, l in enumerate(lines):
    if '.ruff_cache/", ".mypy_cache/"' in l:
        start = i - 1
        break
if start is None:
    print("anchor not found")
    raise SystemExit(1)
end = None
for j in range(start, start + 8):
    if 'ui/dist/' in lines[j]:
        end = j
        break
block = [
    '        if rel.startswith((".git/", "scratch/", "team/", "vendor/", "node_modules/",',
    '                           "ui/node_modules/", "ui/dist/", ".ruff_cache/", ".mypy_cache/",',
    '                           ".pytest_cache/", ".vite/", "dist/", "build/", "coverage/",',
    '                           "htmlcov/")) or rel == ".coverage":',
]
lines[start:end + 1] = block
p.write_text(chr(10).join(lines) + chr(10), encoding="utf-8", newline="")
print("repaired lines", start + 1, "-", end + 1)

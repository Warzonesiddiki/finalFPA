"""Exclude tool caches from the claim-window scan; they are not anyone's work."""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
p = pathlib.Path("scripts/team.py")
src = p.read_text(encoding="utf-8")

old = '        if rel.startswith((".git/", "scratch/", "team/", "vendor/", "node_modules/",'
assert src.count(old) == 1, "exclusion anchor"
new = ('        if rel.startswith((".git/", "scratch/", "team/", "vendor/", "node_modules/",\n'
       '                           ".ruff_cache/", ".mypy_cache/", ".pytest_cache/", ".vite/",\n'
       '                           "dist/", "build/", "coverage/", "htmlcov/") or rel == ".coverage":')
src = src.replace(old, new, 1)
p.write_text(src, encoding="utf-8", newline="")
print("cache dirs excluded from the window scan")

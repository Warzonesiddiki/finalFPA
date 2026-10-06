"""Tighten the handoff-integrity helpers: content threshold, tokenising, real extensions."""
import pathlib, re, sys

sys.stdout.reconfigure(encoding="utf-8")
p = pathlib.Path("scripts/team.py")
src = p.read_text(encoding="utf-8")

start = src.index("def _body(text: str, head: str) -> str:")
end = src.index("def cmd_check(args: argparse.Namespace) -> int:")
block = src[start:end]
assert "_declared_changed" in block and "_window_edits" in block, "helper block not as expected"

new_block = '''EXT_RE = re.compile(r"\\.(py|md|json|toml|ini|cfg|yaml|yml|txt|csv|ts|tsx|js|mjs|html|lock|sql|sh)$")


def _body(text: str, head: str) -> str:
    """Content of a `## Heading` section, minus nested headings and the reviewer
    template, so `present` can be told apart from `actually written`."""
    out = []
    for line in _section(text, head).splitlines():
        s = line.strip()
        if s.startswith("#") or s.startswith("_("):
            continue
        out.append(line)
    return "\\n".join(out).strip()


def _declared_changed(text: str) -> set[str]:
    """Repo-relative paths declared under `## Changed` (back-ticked or bare, one per
    line or comma/slash-separated). Non-path tokens (versions, section refs) are
    rejected by the extension allowlist, so `3.14.7` and `docs/18` cannot masquerade."""
    found: set[str] = set()
    for line in _section(text, "## Changed").splitlines():
        s = line.strip()
        if s.startswith("#"):
            continue
        for tok in re.split(r"[`\\s,;]+", s):
            tok = tok.strip(".:()\\"'")
            if not tok or tok.startswith("http"):
                continue
            if "/" in tok and not EXT_RE.search(tok):
                continue          # looks like a path but has no code/doc extension
            if not EXT_RE.search(tok):
                continue          # version, section number, count, flag name
            found.add(norm(tok))
    return found


def _parse_ts(value):
    try:
        return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except Exception:
        return None


def _scope_hit(rel: str, scopes: list[str]) -> bool:
    for s in scopes:
        s = norm(s).rstrip("/")
        if has_glob(s):
            if fnmatch(rel, s):
                return True
        elif rel == s or rel.startswith(s + "/"):
            return True
    return False


def _window_edits(start, end, scopes: list[str]) -> list[str]:
    """Repo files modified inside a claim window that fall under that claim's scopes.

    This is what makes `## Changed` trustworthy: a handoff that declares one file
    while the window touched six is a summary, not a handoff. The coordination layer
    (team/, scratch/, vendor/) is excluded because every agent writes to it."""
    if not start:
        return []
    end = end or now()
    hits = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith((".git/", "scratch/", "team/", "vendor/", "node_modules/",
                           "ui/node_modules/", "ui/dist/")):
            continue
        if rel.endswith((".pyc", ".log")) or "__pycache__" in rel:
            continue
        if not _scope_hit(rel, scopes):
            continue
        m = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        if start <= m <= end + timedelta(minutes=2):
            hits.append(rel)
    return sorted(hits)


'''
src = src[:start] + new_block + src[end:]

# the length floor was tuned against real handoffs: one honest line is ~30 chars
src = src.replace('elif len(_body(text, sec)) < 40:', 'elif len(_body(text, sec)) < 24:')
src = src.replace("# Present but empty is a rubber stamp: each section exists to carry a\n"
                  "                # claim a peer can falsify, so a bare header must not pass the gate.",
                  "# Present but empty is a rubber stamp: each section exists to carry a\n"
                  "                # claim a peer can falsify, so a bare header must not pass.")
p.write_text(src, encoding="utf-8", newline="")
print("helpers replaced; bytes", p.stat().st_size)

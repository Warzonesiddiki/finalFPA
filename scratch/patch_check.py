"""Apply the handoff-integrity hardening to scripts/team.py (exact-string patch)."""
import pathlib, sys

sys.stdout.reconfigure(encoding="utf-8")
p = pathlib.Path("scripts/team.py")
src = p.read_text(encoding="utf-8")

anchor = """        for sec in HANDOFF_SECTIONS:
            if sec not in text:
                fails.append(f"{f.name}: missing required section {sec}")
"""
assert src.count(anchor) == 1, "anchor not unique"

new = '''        for sec in HANDOFF_SECTIONS:
            if sec not in text:
                fails.append(f"{f.name}: missing required section {sec}")
            elif len(_body(text, sec)) < 40:
                # Present but empty is a rubber stamp: each section exists to carry a
                # claim a peer can falsify, so a bare header must not pass the gate.
                fails.append(f"{f.name}: section {sec} is present but empty")
        claim_blk = _section(text, "## Claim")
        cm = re.search(r"claim:\\s*`([^`]+)`", claim_blk)
        claim = claim_by_id(cm.group(1)) if cm else None
        if claim is not None:
            start = _parse_ts(claim.get("opened_utc"))
            hm = re.search(r"handed off:\\s*([0-9T:Z+-]+)", claim_blk)
            end = _parse_ts(hm.group(1)) if hm else _parse_ts(claim.get("closed_utc"))
            touched = _window_edits(start, end, claim.get("scopes", []))
            declared = _declared_changed(text)
            undeclared = [w for w in touched if w not in declared]
            if undeclared:
                (fails if args.strict else warns).append(
                    f"{f.name}: {len(undeclared)} file(s) changed inside the claim window but not "
                    f"declared under '## Changed': {', '.join(undeclared[:6])}")
            ver = _body(text, "## Verification").lower()
            if touched and not [w for w in touched if w.endswith((".py", ".ts", ".tsx", ".js"))] \\
                    and "team.py" in ver and "pytest" not in ver:
                warns.append(f"{f.name}: docs-only handoff verified only by the coordination command "
                             f"(`team.py check`); the deliverable's own content was not re-checked")
        for pth in sorted(_declared_changed(text)):
            if has_glob(pth) or not Path(pth).suffix:
                continue
            if not (ROOT / pth).exists():
                fails.append(f"{f.name}: declared changed path does not exist: {pth}")
'''

p.write_text(src.replace(anchor, new), encoding="utf-8", newline="")
print("patched; bytes", p.stat().st_size)

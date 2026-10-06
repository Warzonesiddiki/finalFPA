"""Final calibration of the section-content floor and the path-existence rule."""
import pathlib, sys

sys.stdout.reconfigure(encoding="utf-8")
p = pathlib.Path("scripts/team.py")
src = p.read_text(encoding="utf-8")

a = """            elif len(_body(text, sec)) < 24:
                # Present but empty is a rubber stamp: each section exists to carry a
                # claim a peer can falsify, so a bare header must not pass.
                fails.append(f"{f.name}: section {sec} is present but empty")"""
b = """            else:
                content = _body(text, sec)
                if len(content) < 12 or content.lower() in PLACEHOLDERS:
                    # Present but empty is a rubber stamp: each section exists to carry a
                    # claim a peer can falsify, so a header or a stub must not pass.
                    fails.append(f"{f.name}: section {sec} is present but empty "
                                 f"({len(content)} chars of content)")"""
assert src.count(a) == 1, "anchor A"
src = src.replace(a, b)

c = """        for pth in sorted(_declared_changed(text)):
            if has_glob(pth) or not Path(pth).suffix:
                continue"""
d = """        for pth in sorted(_declared_changed(text)):
            # A bare file name carries no directory, so it cannot be resolved from the
            # repo root; the claim-window rule above is what proves the list is complete.
            if has_glob(pth) or "/" not in pth:
                continue"""
assert src.count(c) == 1, "anchor C"
src = src.replace(c, d)

e = "EXT_RE = re.compile("
f = ('PLACEHOLDERS = {"tbd", "n/a", "na", "none", "-", "--", "todo", "see above",\n'
     '               "same as above", "no spec change", "none needed",\n'
     '               "no doc-sync needed", "docs-only: no behaviour change"}\n\n'
     'EXT_RE = re.compile(')
assert src.count(e) == 1, "anchor E"
src = src.replace(e, f, 1)
p.write_text(src, encoding="utf-8", newline="")
print("ok", p.stat().st_size)

import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
from app.engine.pptx_fill import open_template  # noqa: E402
from app.engine.pptx_fill.ppt_spec import DECK_SLIDES, layout_for  # noqa: E402

prs = open_template()
NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
for sid in DECK_SLIDES:
    lay = next(l for l in prs.slide_layouts if l.name == layout_for(sid))
    print(f"\n=== {sid}")
    for sh in lay.shapes:
        if not sh.has_text_frame:
            print(f"  {sh.name:34s} <no text> ({sh.shape_type})")
            continue
        xml = sh._element.xml
        rpr = re.search(r"<a:rPr([^>]*)>", xml)
        sz = re.search(r'sz="(\d+)"', rpr.group(1)) if rpr else None
        b = re.search(r'b="(\d)"', rpr.group(1)) if rpr else None
        col = re.search(r'srgbClr val="(\w+)"', xml)
        algn = re.search(r'<a:pPr[^>]*algn="(\w+)"', xml)
        print(f"  {sh.name:34s} sz={int(sz.group(1))/100 if sz else '-':>6} b={b.group(1) if b else '-'} col={col.group(1) if col else '-'} algn={algn.group(1) if algn else '-'} paras={len(sh.text_frame.paragraphs)}")
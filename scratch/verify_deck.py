"""Generate a real deck and verify it end to end: contract names, fill order, text, charts, OPC."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from pptx import Presentation  # noqa: E402

from app.engine.exports.ppt_pack import generate_powerpoint_deck  # noqa: E402
from app.engine.pptx_fill.ppt_spec import DECK_SLIDES, SLIDE_SHAPE_ORDER  # noqa: E402

out = Path("scratch/deck.pptx")
prs = generate_powerpoint_deck(output_path=out)
print("generated:", out, out.stat().st_size, "bytes")

problems = []
for slide_id, slide in zip(DECK_SLIDES, prs.slides, strict=False):
    order = SLIDE_SHAPE_ORDER[slide_id]
    present = [s.name for s in slide.shapes]
    missing = [n for n in order if n not in present]
    if missing:
        problems.append(f"{slide_id}: missing {missing}")
    extra = [n for n in present if n not in order]
    if extra:
        problems.append(f"{slide_id}: not in contract {extra}")
    print(f"{slide_id}: layout={slide.slide_layout.name} shapes={len(present)} missing={missing}")

print("\n--- slide 1 text ---")
s1 = prs.slides[0]
for n in ("PPT-001_title", "PPT-001_sources", "PPT-001_stamp", "PPT-001_footer_left", "PPT-001_footer_right"):
    sh = next(x for x in s1.shapes if x.name == n)
    print(f"  {n}: {sh.text_frame.text[:120]!r}")

print("\n--- slide 2 kpi1/kpi3 ---")
s2 = prs.slides[1]
for n in ("PPT-002_title", "PPT-002_kpi3_value", "PPT-002_kpi6_label", "PPT-002_narrative_label", "PPT-002_footnote"):
    sh = next(x for x in s2.shapes if x.name == n)
    r = sh.text_frame.paragraphs[0].runs[0]
    col = None
    try:
        col = r.font.color.rgb
    except Exception:
        pass
    print(f"  {n}: {sh.text_frame.text[:80]!r} sz={r.font.size.pt if r.font.size else None} col={col}")

print("\n--- slide 3 bridge chart ---")
s3 = prs.slides[2]
ch = next(x for x in s3.shapes if x.name == "PPT-003_chart_bridge").chart
plot = ch.plots[0]
print("  cats:", list(plot.categories))
for se in plot.series:
    print(f"  {se.name}: {[None if v is None else round(v) for v in se.values]}")
print("  title:", repr(ch.chart_title.text_frame.text))
# tie-out check
base = list(plot.series[0].values)
amount = list(plot.series[1].values)
tops = [round(b + a, 2) for b, a in zip(base, amount)]
print("  bar tops:", tops)
print("  drivers text:", next(x for x in s3.shapes if x.name == "PPT-003_drivers").text_frame.text[:200])

print("\n--- slide 4 table ---")
s4 = prs.slides[3]
t = next(x for x in s4.shapes if x.name == "PPT-004_table").table
for i, row in enumerate(t.rows):
    print("  ", [c.text[:18] for c in row.cells])

print("\n--- slide 5 chips+table ---")
s5 = prs.slides[4]
for i in range(1, 5):
    lbl = next(x for x in s5.shapes if x.name == f"PPT-005_chip{i}_label")
    val = next(x for x in s5.shapes if x.name == f"PPT-005_chip{i}_value")
    print(f"  chip{i}: {lbl.text_frame.text}={val.text_frame.text}")
t5 = next(x for x in s5.shapes if x.name == "PPT-005_table").table
print("  rows:", len(t5.rows), "cols:", len(t5.columns))
print("  r0:", [c.text for c in t5.rows[0].cells])

print("\n--- slide 6 forecast chart + gap ---")
s6 = prs.slides[5]
ch6 = next(x for x in s6.shapes if x.name == "PPT-006_chart_forecast").chart
for se in ch6.plots[0].series:
    print(f"  {se.name}: {[None if v is None else round(v, 2) for v in se.values]}")
print("  cats:", list(ch6.plots[0].categories))
print("  legend:", ch6.has_legend, ch6.legend.position)
print("  outlook:", next(x for x in s6.shapes if x.name == "PPT-006_outlook").text_frame.text[:160])

# reopen
r = Presentation(str(out))
print("\nreopened slides:", len(r.slides))
r3 = r.slides[2]
ch3 = next(x for x in r3.shapes if x.name == "PPT-003_chart_bridge").chart
print("reopened bridge cats:", list(ch3.plots[0].categories))
print("reopened bridge series:", [s.name for s in ch3.plots[0].series])

print("\nPROBLEMS:", problems if problems else "none")
"""Probe: can layout shapes be promoted (deep-copied) onto the slide so that they
are real, editable, per-slide shapes -- including charts and pictures whose parts
are related to the LAYOUT part rather than the slide part?"""
import copy
import sys

sys.stdout.reconfigure(encoding="utf-8")
from pptx import Presentation  # noqa: E402
from pptx.oxml.ns import qn  # noqa: E402
from pptx.opc.constants import RELATIONSHIP_TYPE as RT  # noqa: E402

TPL = "packaging/templates/FPAMonthEndCopilot_v1.pptx"


def promote(slide):
    """Deep-copy every layout shape onto the slide, re-pointing graphic/pic rels."""
    spTree = slide.shapes._spTree
    layout_part = slide.slide_layout.part
    for shape in list(slide.slide_layout.shapes):
        el = copy.deepcopy(shape._element)
        for rId_attr in ("r:embed", "r:link", "r:id"):
            attr = qn(rId_attr)
            for node in el.iter():
                old = node.get(attr)
                if not old:
                    continue
                try:
                    target_part = layout_part.rels[old].target_part
                except KeyError:
                    continue
                new_rId = slide.part.relate_to(target_part, RT.CHART if target_part.content_type.startswith("application/vnd.openxmlformats-officedocument.drawingml.chart") else RT.IMAGE)
                node.set(attr, new_rId)
        spTree.append(el)


def main():
    prs = Presentation(TPL)
    layouts = {l.name: l for l in prs.slide_layouts}

    for name in ("FPA-PPT-001", "FPA-PPT-003", "FPA-PPT-006"):
        s = prs.slides.add_slide(layouts[name])
        promote(s)
        print(f"\n=== {name}: slide shapes after promote = {len(s.shapes)}")

    # Fill something in each
    def by_name(slide, n):
        return next(x for x in slide.shapes if x.name == n)

    s1 = prs.slides[0]
    by_name(s1, "PPT-001_title").text_frame.text = "Probe Title"
    by_name(s1, "PPT-001_logo").element  # picture

    s3 = prs.slides[1]
    from pptx.chart.data import CategoryChartData

    cd = CategoryChartData()
    cd.categories = ["Opening (Budget)", "Materials", "Closing (Actual)"]
    cd.add_series("base", (15770000.0, 15848000.0, 0.0))
    cd.add_series("amount", (0.0, 78000.0, 16645000.0))
    ch = by_name(s3, "PPT-003_chart_bridge").chart
    ch.replace_data(cd)
    print("chart_bridge after replace_data:",
          ch.chart_type, len(ch.plots[0].series), len(list(ch.plots[0].categories)))
    by_name(s3, "PPT-003_title").text_frame.text = "BvA bridge"

    s6 = prs.slides[2]
    cd2 = CategoryChartData()
    cd2.categories = ["P01", "P02", "P03"]
    cd2.add_series("Actual", (1.0, 2.0, None))
    cd2.add_series("Forecast", (None, 2.1, 3.0))
    cd2.add_series("Budget", (1.1, 2.2, 3.3))
    ch2 = by_name(s6, "PPT-006_chart_forecast").chart
    ch2.replace_data(cd2)
    print("chart_forecast series:", len(ch2.plots[0].series))

    prs.save("scratch/_promote.pptx")
    print("\nsaved OK")

    # reopen and verify
    r = Presentation("scratch/_promote.pptx")
    for i, s in enumerate(r.slides, 1):
        names = [x.name for x in s.shapes]
        charts = [x.name for x in s.shapes if x.has_chart]
        pics = [x.name for x in s.shapes if x.shape_type == 13]
        tables = [x.name for x in s.shapes if x.has_table]
        print(f"reopened slide {i}: {len(names)} shapes charts={charts} pics={pics} tables={tables}")
    r2 = r.slides[0]
    print("title after reopen:", repr(by_name(r2, "PPT-001_title").text_frame.text))
    c = by_name(r.slides[1], "PPT-003_chart_bridge").chart
    print("bridge chart cats:", list(c.plots[0].categories), "series:", len(c.plots[0].series))
    c2 = by_name(r.slides[2], "PPT-006_chart_forecast").chart
    print("forecast cats:", list(c2.plots[0].categories))


if __name__ == "__main__":
    main()
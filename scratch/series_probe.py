import sys

sys.stdout.reconfigure(encoding="utf-8")
from app.engine.pptx_fill import add_slide_from_layout, replace_chart_data, resolve_shape  # noqa: E402
from app.engine.pptx_fill import open_template  # noqa: E402

prs = open_template()

for lid, shape_name in (("FPA-PPT-003", "PPT-003_chart_bridge"), ("FPA-PPT-006", "PPT-006_chart_forecast")):
    s = add_slide_from_layout(prs, lid)
    sh = resolve_shape(s, shape_name)
    ch = sh.chart
    print(f"\n=== {shape_name}: type={ch.chart_type}")
    plot = ch.plots[0]
    print("  series before:", [se.name for se in plot.series])
    for se in plot.series:
        spPr = se._element.find(
            "{http://schemas.openxmlformats.org/drawingml/2006/chart}spPr")
        print(f"    {se.name}: spPr={'yes' if spPr is not None else 'no'}", end=" ")
        if spPr is not None:
            import re
            x = spPr.xml
            print("noFill" if "noFill" in x else ("srgbClr=" + (re.search(r'srgbClr val="(\w+)"', x).group(1) if re.search(r'srgbClr val="(\w+)"', x) else "?")), end=" ")
            print("prstDash" if "prstDash" in x else "")
        else:
            print()
    print("  has_legend:", ch.has_legend, "legend pos:", ch.legend.position if ch.has_legend else None)
    print("  has_title:", ch.has_title, repr(ch.chart_title.text_frame.text) if ch.has_title else "")

    # now replace data with same series count/names
    if lid == "FPA-PPT-003":
        ch = replace_chart_data(sh, ["A", "B", "C"], [("base", (1, 2, 0)), ("amount", (0, 5, 9))],
                                title="Bridge: FY26-P09", legend=False)
    else:
        ch = replace_chart_data(sh, ["P01", "P02", "P03"],
                                [("Actual", (1, 2, None)), ("Forecast", (None, 2.1, 3)), ("Budget", (1.1, 2.2, 3.3))],
                                title="Forecast", legend=True)
    print("  --- after replace_data ---")
    print("  series after:", [se.name for se in ch.plots[0].series])
    for se in ch.plots[0].series:
        spPr = se._element.find("{http://schemas.openxmlformats.org/drawingml/2006/chart}spPr")
        x = spPr.xml if spPr is not None else ""
        import re
        m = re.search(r'srgbClr val="(\w+)"', x)
        print(f"    {se.name}: spPr={'yes' if spPr is not None else 'no'} noFill={'noFill' in x} rgb={m.group(1) if m else None} dash={'prstDash' in x}")
    print("  title now:", repr(ch.chart_title.text_frame.text))
    print("  legend:", ch.has_legend, ch.legend.position if ch.has_legend else None)
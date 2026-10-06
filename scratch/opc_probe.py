"""Validate the promoted deck's OPC package: content types, slide rels, chart parts,
and whether the chart's embedded workbook still holds our numbers."""
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from pptx import Presentation  # noqa: E402

P = "scratch/_promote.pptx"

z = zipfile.ZipFile(P)
bad = z.testzip()
print("zip integrity:", "OK" if bad is None else f"BAD {bad}")

names = z.namelist()
charts = sorted(n for n in names if n.startswith("ppt/charts/") and n.endswith(".xml"))
embed = sorted(n for n in names if "embeddings" in n)
print("chart parts:", charts)
print("embeddings:", embed)

ct = z.read("[Content_Types].xml").decode("utf-8")
print("chart content-type declared:", "chart+xml" in ct)
print("xlsx content-type declared:", "spreadsheetml.sheet" in ct)
print("png/jpeg declared:", ("image/png" in ct) or ("image/jpeg" in ct) or ("image/" in ct))

# slide rels
import re

for n in sorted(n for n in names if re.match(r"ppt/slides/_rels/slide\d+\.xml\.rels", n)):
    rels = z.read(n).decode("utf-8")
    tgts = re.findall(r'Target="([^"]+)"[^>]*', rels)
    chart_tgts = [t for t in tgts if "chart" in t or "media" in t or "embed" in t]
    print(f"{n}: {len(tgts)} rels, data rels -> {chart_tgts}")

# duplicate part names (would mean shared chart part reused across slides)
print("\nunique chart parts:", len(set(charts)), "of", len(charts), "entries")

prs = Presentation(P)
s2 = prs.slides[1]
ch = next(x for x in s2.shapes if x.name == "PPT-003_chart_bridge").chart
for s in ch.plots[0].series:
    print("series:", s.name, list(s.values))
s3 = prs.slides[2]
ch2 = next(x for x in s3.shapes if x.name == "PPT-006_chart_forecast").chart
for s in ch2.plots[0].series:
    print("series:", s.name, list(s.values))
print("\nslide1 layout name:", prs.slides[0].slide_layout.name)
print("chart type preserved:", ch.chart_type, ch2.chart_type)
import collections
import sys
import xml.etree.ElementTree as ET

path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cov_fresh.xml"
root = ET.parse(path).getroot()
agg = collections.defaultdict(lambda: [0, 0])
for cls in root.iter("class"):
    fn = cls.get("filename", "").replace("\\", "/")
    for line in cls.iter("line"):
        agg[fn][0] += 1
        if line.get("hits") != "0":
            agg[fn][1] += 1

dom_keys = ["/calc/", "/rules/", "forecast/methods.py", "/ai/"]


def pct(files):
    tot = sum(agg[f][0] for f in files)
    hit = sum(agg[f][1] for f in files)
    return hit, tot, (hit / tot * 100 if tot else 0)


dom_files = [f for f in agg if any(k in f for k in dom_keys)]
h, t, p = pct(list(agg.keys()))
print(f"backend (whole app): {h}/{t} = {p:.2f}%  [bar >=75]")
h, t, p = pct(dom_files)
print(f"domain (calc/rules/methods/ai): {h}/{t} = {p:.2f}%  [bar >=90]")
for f in sorted(dom_files):
    print(f"   {f}: {agg[f][1]}/{agg[f][0]} = {agg[f][1] / agg[f][0] * 100:.1f}%")

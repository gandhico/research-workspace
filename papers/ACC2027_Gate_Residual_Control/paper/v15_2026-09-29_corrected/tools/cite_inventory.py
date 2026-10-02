import re
import sys
import io
from collections import OrderedDict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = r"C:\Research\papers\ACC2027_Gate_Residual_Control\paper\v14_2026-09-21_izhikevich"
s = open(D + r"\ACC2027.tex", encoding="utf-8").read()
bib = open(D + r"\references_ACC2027.bib", encoding="utf-8").read()
titles = {}
for m in re.finditer(r"@\w+\{([^,]+),(.*?)\n\}", bib, re.S):
    t = re.search(r"title\s*=\s*[\{\"]+(.*?)[\}\"]+\s*,", m.group(2), re.S)
    titles[m.group(1)] = t.group(1).replace("\n", " ")[:70] if t else ""
cites = OrderedDict()
for m in re.finditer(r"\\cite\{([^}]+)\}", s):
    for k in [x.strip() for x in m.group(1).split(",")]:
        ctx = s[max(0, m.start() - 60):m.start()].replace("\n", " ")
        cites.setdefault(k, []).append(ctx)
print(len(cites), "distinct keys cited;", len(titles), "entries in bib\n")
for i, (k, v) in enumerate(cites.items(), 1):
    print(f"[{i:2d}] {k:26s} x{len(v)}  {titles.get(k, '?')[:48]:48s} | ...{v[0][-46:]}")

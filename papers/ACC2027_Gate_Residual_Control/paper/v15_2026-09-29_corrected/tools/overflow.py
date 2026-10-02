"""How far past the page limit is a build?  Reports pages, bottom of text on the last page, bibliography start."""
import re
import sys
import pymupdf
from pathlib import Path

pdf = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "ACC2027.pdf")
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 7
d = pymupdf.open(pdf)
W = d[0].rect.width
mid, TOP, BOT = W / 2, 49.4, 738.2
FRAME = BOT - TOP
print(f"{pdf.name}: {d.page_count} pages (limit {LIMIT})")
used = []
for p in range(d.page_count):
    ends = []
    for x0, x1 in ((0, mid), (mid, W)):
        ys = [ln["bbox"][3] for b in d[p].get_text("dict")["blocks"] if b["type"] == 0 for ln in b["lines"]
              if x0 <= (ln["bbox"][0] + ln["bbox"][2]) / 2 <= x1]
        ends.append(max(ys) - TOP if ys else 0.0)
    used.append(ends)
    print(f"  p{p+1}: left column used {ends[0]:6.1f} pt, right {ends[1]:6.1f} pt (of {FRAME:.0f})")
full = sum(sum(u) for u in used[:LIMIT])
over = sum(used[LIMIT]) if d.page_count > LIMIT else 0.0
for extra in used[LIMIT + 1:]:
    over += sum(extra)
print(f"\ncontent beyond page {LIMIT}: {over:.0f} pt = {over / FRAME:.2f} columns = {over / (2 * FRAME):.2f} page")
if d.page_count <= LIMIT:
    slack = 2 * FRAME - sum(used[-1])
    print(f"slack on the last page: {slack:.0f} pt")
txt = "\n".join(pg.get_text() for pg in d)
m = re.search(r"\nREFERENCES\n", txt)
print("bibliography present:", bool(m))

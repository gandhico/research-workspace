"""Overleaf package for v14: only what the manuscript needs (derived from the .tex), verified by a clean-room compile."""
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
OUT = SRC / "ACC2027_v14_overleaf.zip"
TEST = Path(__import__("tempfile").gettempdir()) / "overleaf_check_v14"

names = {"ACC2027.tex", "references_ACC2027.bib", "ieeeconf.cls"}
seen, todo = set(), ["ACC2027.tex"]
while todo:
    f = todo.pop()
    if f in seen:
        continue
    seen.add(f)
    txt = (SRC / f).read_text(encoding="utf-8")
    body = "\n".join(l for l in txt.split("\n") if not l.lstrip().startswith("%"))
    for g in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", body):
        names.add(g)
    for i in re.findall(r"\\input\{([^}]+)\}", body):
        i = i if i.endswith(".tex") else i + ".tex"
        names.add(i)
        todo.append(i)
# the vehicle strip sits in an \iffalse block; ship it so it can be restored in one edit
names.add("figures/01_mujoco_missions/fig2_drones_only.pdf")
missing = sorted(n for n in names if not (SRC / n).exists())
if missing:
    sys.exit(f"missing: {missing}")

OUT.unlink(missing_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for n in sorted(names):
        z.write(SRC / n, n)
print(f"zip: {len(names)} files, {OUT.stat().st_size / 1e6:.2f} MB")
for n in sorted(names):
    print("  ", n)

if TEST.exists():
    shutil.rmtree(TEST)
TEST.mkdir(parents=True)
with zipfile.ZipFile(OUT) as z:
    z.extractall(TEST)
for cmd in (["pdflatex", "-interaction=nonstopmode", "ACC2027"], ["bibtex", "ACC2027"],
            ["pdflatex", "-interaction=nonstopmode", "ACC2027"], ["pdflatex", "-interaction=nonstopmode", "ACC2027"]):
    subprocess.run(cmd, cwd=TEST, capture_output=True)
log = (TEST / "ACC2027.log").read_text(encoding="utf-8", errors="ignore")
print([l for l in log.splitlines() if "Output written" in l])
print("undefined:", sum(1 for l in log.splitlines() if "undefined" in l.lower()),
      "| missing graphics:", sum(1 for l in log.splitlines() if "not found" in l),
      "| errors:", [l for l in log.splitlines() if l.startswith("!")][:3])

"""Build the v13 manuscript (pdflatex + bibtex, no latexmk) and report pages, warnings and overflow."""
import re
import subprocess
import sys
from pathlib import Path

D = Path(__file__).resolve().parents[1]
job = sys.argv[1] if len(sys.argv) > 1 else "ACC2027"
for cmd in (["pdflatex", "-interaction=nonstopmode", f"-jobname={job}", "ACC2027"], ["bibtex", job],
            ["pdflatex", "-interaction=nonstopmode", f"-jobname={job}", "ACC2027"],
            ["pdflatex", "-interaction=nonstopmode", f"-jobname={job}", "ACC2027"]):
    subprocess.run(cmd, cwd=D, capture_output=True)
log = (D / f"{job}.log").read_text(encoding="utf-8", errors="ignore")
print([l for l in log.splitlines() if "Output written" in l])
print("undefined refs/cites:", len(re.findall(r"undefined", log)),
      "| overfull boxes:", len(re.findall(r"Overfull", log)),
      "| multiply-defined labels:", len(re.findall(r"multiply", log)))
errs = [l for l in log.splitlines() if l.startswith("!")]
print("errors:", errs[:5])
sys.exit(0)

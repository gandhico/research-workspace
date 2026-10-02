"""Check every \\listing{file}{first}{last} in the companion: file exists, range inside the file, ASCII only."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEX = Path(__file__).resolve().parents[1] / "ACC2027_equation_code_companion.tex"
pattern = re.compile(r"\\listing\{([^}]+)\}\{(\d+)\}\{(\d+)\}")
problems = 0
for f, a, b in pattern.findall(TEX.read_text(encoding="utf-8")):
    path = ROOT / f
    if not path.exists():
        print("MISSING", f)
        problems += 1
        continue
    lines = path.read_text(encoding="utf-8").splitlines()
    a, b = int(a), int(b)
    if b > len(lines) or a > b:
        print(f"BAD RANGE {f}:{a}-{b} (file has {len(lines)} lines)")
        problems += 1
    for i, line in enumerate(lines[a - 1:b], a):
        if any(ord(c) > 127 for c in line):
            print(f"NON-ASCII {f}:{i}: {line.strip()[:80]}")
            problems += 1
print("problems:", problems)
sys.exit(1 if problems else 0)

"""Find LaTeX/mathtext written into non-raw Python strings.

A label like f"$\\theta$" is not what it looks like: \\t is a tab escape, so
matplotlib receives "$<TAB>heta$" and renders "heta". Python only warns for
sequences it does not recognise (\\c, \\p), and stays silent for the ones it
does (\\t, \\n, \\r, \\b, \\a, \\f, \\v) -- which are exactly the dangerous ones.

Reports every string literal that contains a backslash-escape which is both
(a) a valid Python escape and (b) followed by letters, i.e. almost certainly
an intended LaTeX command.

Run:  python scan_latex_strings.py <root>
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

# escapes Python silently consumes, mapped to the LaTeX command they eat
SILENT = {
    "\t": "\\t...", "\n": "\\n...", "\r": "\\r...", "\b": "\\b...",
    "\a": "\\a...", "\f": "\\f...", "\v": "\\v...",
}
# LaTeX commands that begin with those letters and so get destroyed
LATEX_HINTS = ("heta", "au", "imes", "ext", "rac", "ar", "ullet", "eta",
               "ho", "ightarrow", "eft", "ambda", "abla", "u", "ightharpoon")


def suspicious(value: str) -> list[str]:
    hits = []
    for ch, label in SILENT.items():
        idx = 0
        while (idx := value.find(ch, idx)) != -1:
            tail = value[idx + 1: idx + 12]
            if tail[:1].isalpha() and any(tail.startswith(h) for h in LATEX_HINTS):
                hits.append(f"{label} -> {ch!r}+{tail!r}")
            idx += 1
    return hits


def main(root: Path) -> int:
    found = 0
    for f in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(io.open(f, encoding="utf-8").read(), filename=str(f))
        except SyntaxError as e:
            print(f"{f}: cannot parse: {e}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for hit in suspicious(node.value):
                    print(f"{f.relative_to(root)}:{node.lineno}: {hit}")
                    found += 1
    print(f"\n{found} corrupted LaTeX string(s)")
    return found


if __name__ == "__main__":
    raise SystemExit(1 if main(Path(sys.argv[1]).resolve()) else 0)

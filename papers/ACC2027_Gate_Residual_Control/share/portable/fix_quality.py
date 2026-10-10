"""Fix two portability/quality defects in the package copy.

1. Corrupted LaTeX in matplotlib labels. `f"$\\theta_e$"` is not the string it
   looks like: `\\t` is a tab escape, so matplotlib receives `$<TAB>heta_e$`
   and renders "heta_e". Same for `\\r` in `$\\rightarrow$`. Python does not
   warn about these because both escapes are *valid*. The fix is to make the
   f-strings raw.

2. UTF-8 BOMs at the start of five legacy source files. CPython copes, but
   `ast.parse`, some linters, and non-Windows tooling do not.

Run:  python fix_quality.py <package_root>
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

LATEX_FIXES = [
    (   # figure suptitle: \theta -> tab, \rightarrow -> carriage return
        '        f"Quanser 3DOF Hover: {MISSION_LABEL[mission]} "\n'
        '        f"(mean $\\theta_e$: {row[\'pd_mean_deg\']:.3f}$^\\circ$ $\\rightarrow$ "\n'
        '        f"{row[\'cmg_mean_deg\']:.3f}$^\\circ$, {row[\'mean_improvement_pct\']:+.2f}%{qualifier})",',
        '        rf"Quanser 3DOF Hover: {MISSION_LABEL[mission]} "\n'
        '        rf"(mean $\\theta_e$: {row[\'pd_mean_deg\']:.3f}$^\\circ$ $\\rightarrow$ "\n'
        '        rf"{row[\'cmg_mean_deg\']:.3f}$^\\circ$, {row[\'mean_improvement_pct\']:+.2f}%{qualifier})",',
    ),
    (   # summary suptitle: \pm was only warned about, but make it raw too
        '        f"Quanser 3DOF Hover Roll validation: $n=3$ per controller; paired improvement "\n'
        '        f"{mean:.2f}% $\\pm$ {sd:.2f}% (sample SD)",',
        '        rf"Quanser 3DOF Hover Roll validation: $n=3$ per controller; paired improvement "\n'
        '        rf"{mean:.2f}% $\\pm$ {sd:.2f}% (sample SD)",',
    ),
]


def main(pkg: Path) -> int:
    code = pkg / "code"
    problems = []

    # --- 1. LaTeX ----------------------------------------------------------
    target = code / "hover3dof_hardware" / "make_acc_positive_hardware_figures.py"
    text = io.open(target, encoding="utf-8").read()
    for old, new in LATEX_FIXES:
        if old not in text:
            problems.append(f"LaTeX fix did not match in {target.name}:\n{old}")
            continue
        text = text.replace(old, new, 1)
    io.open(target, "w", encoding="utf-8").write(text)
    print(f"  latex   {target.relative_to(code)}")

    # --- 2. BOMs -----------------------------------------------------------
    stripped = 0
    for f in sorted(code.rglob("*.py")):
        raw = f.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            f.write_bytes(raw[3:])
            print(f"  bom     {f.relative_to(code)}")
            stripped += 1

    # --- verify ------------------------------------------------------------
    import ast
    bad = []
    for f in sorted(code.rglob("*.py")):
        src = io.open(f, encoding="utf-8").read()
        try:
            tree = ast.parse(src, filename=str(f))
        except SyntaxError as e:
            bad.append(f"{f.relative_to(code)}: {e}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "\t" in node.value and "heta" in node.value:
                    bad.append(f"{f.relative_to(code)}:{node.lineno}: tab in LaTeX")
                if "\r" in node.value and "ightarrow" in node.value:
                    bad.append(f"{f.relative_to(code)}:{node.lineno}: CR in LaTeX")

    print(f"\n{stripped} BOM(s) stripped")
    print(f"rule problems : {len(problems)}")
    for p in problems:
        print(f"    {p}")
    print(f"remaining     : {len(bad)}")
    for b in bad:
        print(f"    {b}")
    return 1 if (problems or bad) else 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]).resolve()))

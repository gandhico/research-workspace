"""Point older scripts that hard-code the author's project root at the folder this package was extracted to.

  python tools/rebase_paths.py            # list the files that would change (dry run)
  python tools/rebase_paths.py --apply    # rewrite them in place

Only text files under src/, scripts/, experiments/, share_tools/ are touched, and only the exact string of the original root
(in its backslash and forward-slash spellings) is replaced.  The campaign scripts of final_robustness_gating_2026-09-20 use
relative paths and are unaffected.
"""
import os
import sys
from pathlib import Path

OLD = r"C:\Research\papers\ACC2027_Gate_Residual_Control"
NEW = Path(__file__).resolve().parents[1]
apply = "--apply" in sys.argv
pairs = [(OLD, str(NEW)), (OLD.replace("\\", "/"), NEW.as_posix()), (OLD.replace("\\", "\\\\"), str(NEW).replace("\\", "\\\\"))]
n = 0
for sub in ("src", "scripts", "experiments", "share_tools"):
    for dp, dn, fn in os.walk(NEW / sub):
        dn[:] = [d for d in dn if d not in ("__pycache__", ".venv", "results")]
        for f in fn:
            if not f.endswith((".py", ".ps1", ".md", ".yaml", ".toml", ".txt")):
                continue
            p = Path(dp) / f
            try:
                s = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            t = s
            for a, b in pairs:
                t = t.replace(a, b)
            if t != s:
                n += 1
                print(("rewrote " if apply else "would rewrite ") + str(p.relative_to(NEW)))
                if apply:
                    p.write_text(t, encoding="utf-8")
print(f"\n{n} file(s) {'rewritten' if apply else 'would change'}; new root: {NEW}")

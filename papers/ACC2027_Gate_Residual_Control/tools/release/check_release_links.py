"""Check every relative link and image in the release's Markdown files; for code links with #Lx-Ly anchors, check the
line range exists in the file. Prints broken links; exit code 1 if any.
    python tools/release/check_release_links.py <release_root>
"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
bad = 0
pat = re.compile(r'(?:\]\(|src=")([^)"\s]+)')
for md in root.rglob("*.md"):
    if "code" in md.relative_to(root).parts[:1] and md.name not in ("REPRODUCIBILITY.md",):
        continue                                   # copied research notes keep their original (local) links
    for m in pat.finditer(md.read_text(encoding="utf-8")):
        link = m.group(1)
        if link.startswith(("http", "#", "mailto:")):
            continue
        path, _, anchor = link.partition("#")
        target = (md.parent / path).resolve()
        if not target.exists():
            print(f"MISSING  {md.relative_to(root)} -> {link}"); bad += 1
            continue
        a = re.fullmatch(r"L(\d+)(?:-L(\d+))?", anchor)
        if a and target.is_file():
            n = len(target.read_text(encoding="utf-8", errors="replace").splitlines())
            hi = int(a.group(2) or a.group(1))
            if hi > n:
                print(f"BAD LINES {md.relative_to(root)} -> {link} (file has {n} lines)"); bad += 1
print("broken:", bad)
sys.exit(1 if bad else 0)

"""Fold the reproducibility section into the package README, then rebuild
MANIFEST.csv and the zip.

Run:  python finalize.py <package_root>
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(pkg: Path) -> int:
    # --- README ------------------------------------------------------------
    readme = pkg / "README.md"
    text = io.open(readme, encoding="utf-8").read()
    section = io.open(HERE / "readme_section.md", encoding="utf-8").read()

    marker = "## Running this on another machine"
    if marker in text:
        text = text[:text.index(marker)]
    # insert before the closing "Reading the results honestly" section
    anchor = "## Reading the results honestly"
    if anchor in text:
        text = text.replace(anchor, section + "\n" + anchor, 1)
    else:
        text = text.rstrip() + "\n\n" + section
    io.open(readme, "w", encoding="utf-8").write(text)
    print("  README updated")

    # --- also ship the verification tools ----------------------------------
    tools = pkg / "code" / "tools"
    tools.mkdir(exist_ok=True)
    for t in ("scan_latex_strings.py", "test_portability.py", "make_portable.py",
              "rules_extra.py", "fix_quality.py"):
        shutil.copy2(HERE / t, tools / t)
    io.open(tools / "README.md", "w", encoding="utf-8").write(
        "# Build and verification tools\n\n"
        "These produced and checked the distribution; you do not need them to\n"
        "use the package. They are here so the portability claims can be\n"
        "re-checked rather than taken on trust.\n\n"
        "| Script | What it does |\n"
        "|---|---|\n"
        "| `test_portability.py <root>` | copies the package elsewhere, imports "
        "every module from an unrelated working directory, and fails if any path "
        "points back at the original tree |\n"
        "| `scan_latex_strings.py <root>` | finds LaTeX written into non-raw "
        "Python strings, where `\\t` and `\\r` are silently eaten |\n"
        "| `make_portable.py <root>` | the rewrite that replaced every absolute "
        "path with an `acc2027_paths` symbol (with `rules_extra.py`) |\n"
        "| `fix_quality.py <root>` | the LaTeX and BOM fixes |\n")
    print("  tools shipped")

    # --- manifest ----------------------------------------------------------
    rows = []
    for f in sorted(pkg.rglob("*")):
        if not f.is_file() or f.name == "MANIFEST.csv":
            continue
        if "__pycache__" in f.parts:
            f.unlink()
            continue
        rel = str(f.relative_to(pkg)).replace("\\", "/")
        rows.append((rel, f.stat().st_size,
                     hashlib.sha256(f.read_bytes()).hexdigest()))
    with io.open(pkg / "MANIFEST.csv", "w", encoding="utf-8", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(["path", "bytes", "sha256"])
        w.writerows(rows)
    total = sum(r[1] for r in rows)
    print(f"  manifest: {len(rows)} files, {total/1e6:.1f} MB")

    # --- zip ---------------------------------------------------------------
    zip_path = pkg.parent / f"{pkg.name}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(pkg / "MANIFEST.csv", f"{pkg.name}/MANIFEST.csv")
        for rel, _s, _h in rows:
            z.write(pkg / rel, f"{pkg.name}/{rel}")
    print(f"  zip: {zip_path}  ({zip_path.stat().st_size/1e6:.1f} MB)")

    json.dump({"package": str(pkg), "zip": str(zip_path), "files": len(rows) + 1,
               "bytes_uncompressed": total, "bytes_zip": zip_path.stat().st_size},
              io.open(pkg.parent / "BUILD.json", "w", encoding="utf-8"), indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]).resolve()))

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

SOURCE = Path(r"C:\Research\presentations\Resources\Powerpoint Templates\2026_NMSU_Widescreen.potx")
FINAL = Path(r"C:\Research\presentations\ACC2027_CMG_PES_Research_Update_2026-08-28.pptx")


def themes(path: Path) -> dict[str, bytes]:
    with ZipFile(path) as archive:
        return {
            name: archive.read(name)
            for name in archive.namelist()
            if name.startswith("ppt/theme/") and name.endswith(".xml")
        }


source_themes = themes(SOURCE)
final_themes = themes(FINAL)
theme_equal = source_themes == final_themes

print(f"theme_equal={theme_equal}")
for name, data in source_themes.items():
    print("source_theme", name, hashlib.sha256(data).hexdigest())
for name, data in final_themes.items():
    print("final_theme ", name, hashlib.sha256(data).hexdigest())

if not theme_equal:
    fd, temp_name = tempfile.mkstemp(suffix=".pptx", dir=FINAL.parent)
    os.close(fd)
    temp = Path(temp_name)
    with ZipFile(FINAL) as source_zip, ZipFile(temp, "w", ZIP_DEFLATED) as target_zip:
        written = set()
        for item in source_zip.infolist():
            payload = source_themes.get(item.filename, source_zip.read(item.filename))
            target_zip.writestr(item, payload)
            written.add(item.filename)
        for name, payload in source_themes.items():
            if name not in written:
                target_zip.writestr(name, payload)
    os.replace(temp, FINAL)
    print("theme_restored=True")

with ZipFile(FINAL) as archive:
    masters = [n for n in archive.namelist() if re.fullmatch(r"ppt/slideMasters/slideMaster\d+\.xml", n)]
    layouts = [n for n in archive.namelist() if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", n)]
    slides = [n for n in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
    print(f"masters={len(masters)} layouts={len(layouts)} slides={len(slides)}")
    for index in range(1, len(slides) + 1):
        rel_name = f"ppt/slides/_rels/slide{index}.xml.rels"
        rels = archive.read(rel_name).decode("utf-8")
        target = re.search(
            r'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="([^"]+)',
            rels,
        )
        xml = archive.read(f"ppt/slides/slide{index}.xml").decode("utf-8")
        placeholder_count = len(re.findall(r"<p:ph(?:\s|/|>)", xml))
        print(f"slide={index:02d} layout={target.group(1) if target else 'NONE'} placeholders={placeholder_count}")

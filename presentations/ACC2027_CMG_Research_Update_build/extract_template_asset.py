from pathlib import Path
from zipfile import ZipFile

source = Path(r"C:\Research\presentations\Resources\Powerpoint Templates\2026_NMSU_Widescreen.potx")
target = Path(r"C:\Research\presentations\ACC2027_CMG_Research_Update_build\nmsu_logo.png")

with ZipFile(source) as archive:
    target.write_bytes(archive.read("ppt/media/image1.png"))

print(target)

import re
import sys
import zipfile

with zipfile.ZipFile(sys.argv[1]) as archive:
    xml = archive.read("ppt/theme/theme1.xml").decode("utf-8")

print("FONTS", sorted(set(re.findall(r'typeface="([^"]*)"', xml))))
print("COLORS", re.findall(r'<a:(?:srgbClr|sysClr) val="([^"]+)"', xml)[:30])

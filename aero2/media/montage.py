import glob
import os
from PIL import Image, ImageDraw

OUT = r"C:\Research\aero2\media\cutouts"
fs = sorted(glob.glob(os.path.join(OUT, "*_white.png")))
ims = []
for f in fs:
    im = Image.open(f).convert("RGB")
    im.thumbnail((360, 360))
    ims.append((im, os.path.basename(f).replace("_white.png", "")))
cols = 3
rows = (len(ims) + cols - 1) // cols
cw = max(i.size[0] for i, _ in ims) + 10
ch = max(i.size[1] for i, _ in ims) + 22
sheet = Image.new("RGB", (cols * cw, rows * ch), (245, 245, 245))
d = ImageDraw.Draw(sheet)
for k, (im, name) in enumerate(ims):
    r, c = divmod(k, cols)
    x, y = c * cw + 5, r * ch + 5
    sheet.paste(im, (x, y))
    d.text((x + 2, y + im.size[1] + 4), name, fill=(0, 0, 0))
sheet.save(os.path.join(OUT, "montage_cutouts.png"))
print("MONTAGE", os.path.join(OUT, "montage_cutouts.png"))

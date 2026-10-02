import glob
import os
from rembg import remove, new_session
from PIL import Image, ImageDraw

SRC = r"C:\Research\aero2\media\photos"
OUT = os.path.join(SRC, "cutouts")
os.makedirs(OUT, exist_ok=True)
SESSION = new_session("isnet-general-use")
CROP_FRAC = 0.57   # keep top 57% (robot + Quanser base); drop the drawers below

files = sorted(glob.glob(os.path.join(SRC, "photo_*.jpeg")))
whites = []
for f in files:
    img = Image.open(f).convert("RGBA")
    w, h = img.size
    img = img.crop((0, 0, w, int(h * CROP_FRAC)))          # remove drawers
    cut = remove(img, session=SESSION, alpha_matting=True,
                 alpha_matting_foreground_threshold=240,
                 alpha_matting_background_threshold=15)
    name = os.path.splitext(os.path.basename(f))[0]
    cut.save(os.path.join(OUT, name + "_cut.png"))          # transparent (deliverable)
    bg = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    bg.alpha_composite(cut)
    wp = os.path.join(OUT, name + "_white.png")
    bg.convert("RGB").save(wp)
    whites.append(wp)
    print("CUT", name, flush=True)

# montage
ims = []
for wp in sorted(whites):
    im = Image.open(wp).convert("RGB")
    im.thumbnail((300, 300))
    ims.append((im, os.path.basename(wp).replace("_white.png", "")))
cols = 4
rows = (len(ims) + cols - 1) // cols
cw = max(i.size[0] for i, _ in ims) + 10
ch = max(i.size[1] for i, _ in ims) + 20
sheet = Image.new("RGB", (cols * cw, rows * ch), (240, 240, 240))
d = ImageDraw.Draw(sheet)
for k, (im, nm) in enumerate(ims):
    r, c = divmod(k, cols)
    x, y = c * cw + 5, r * ch + 5
    sheet.paste(im, (x, y))
    d.text((x + 2, y + im.size[1] + 3), nm, fill=(0, 0, 0))
sheet.save(os.path.join(OUT, "montage_photos.png"))
print("DONE ->", os.path.join(OUT, "montage_photos.png"), flush=True)

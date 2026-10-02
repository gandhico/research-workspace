import os
import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw

MEDIA = r"C:\Research\aero2\media"
FRAMES = os.path.join(MEDIA, "frames")
VIDS = {
    "v55": r"C:\Users\gandhico\Downloads\WhatsApp Video 2026-08-11 at 4.40.55 PM.mp4",
    "v50": r"C:\Users\gandhico\Downloads\WhatsApp Video 2026-08-11 at 4.40.50 PM.mp4",
}
N = 24

for tag, path in VIDS.items():
    rdr = imageio.get_reader(path)
    meta = rdr.get_meta_data()
    fps = float(meta.get("fps", 30) or 30)
    try:
        nf = rdr.count_frames()
    except Exception:
        dur = float(meta.get("duration", 0) or 0)
        nf = int(dur * fps) if dur else 300
    outdir = os.path.join(FRAMES, tag)
    os.makedirs(outdir, exist_ok=True)
    idxs = np.unique(np.linspace(0, max(nf - 1, 1), N).astype(int))
    thumbs = []
    for i, fi in enumerate(idxs):
        try:
            frame = rdr.get_data(int(fi))
        except Exception:
            continue
        img = Image.fromarray(frame)
        t = fi / fps
        img.save(os.path.join(outdir, f"{tag}_{i:02d}_t{t:04.1f}.png"))
        th = img.copy()
        th.thumbnail((260, 260))
        thumbs.append((th, f"{i:02d}  t={t:.1f}s"))
    rdr.close()

    cols = 6
    rows = (len(thumbs) + cols - 1) // cols
    tw, thh = thumbs[0][0].size
    pad, lab = 6, 16
    sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (thh + lab + pad) + pad), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    for k, (th, label) in enumerate(thumbs):
        r, c = divmod(k, cols)
        x, y = pad + c * (tw + pad), pad + r * (thh + lab + pad)
        sheet.paste(th, (x, y))
        d.text((x + 3, y + thh + 2), label, fill=(255, 255, 0))
    sp = os.path.join(MEDIA, f"contact_{tag}.png")
    sheet.save(sp)
    print(f"SHEET {tag} nframes={nf} fps={fps:.1f} thumbs={len(thumbs)} -> {sp}", flush=True)

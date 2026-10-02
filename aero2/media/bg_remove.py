import glob
import os

from rembg import remove, new_session
from PIL import Image

SESSION = new_session("isnet-general-use")

FR = r"C:\Research\aero2\media\frames"
OUT = r"C:\Research\aero2\media\cutouts"
os.makedirs(OUT, exist_ok=True)

# (video tag, frame index, descriptive name) -> best match to the 6 twin renders
SEL = [
    ("v55", "00", "pose1_pitchup"),
    ("v50", "22", "pose2_pitchup_yaw"),
    ("v50", "09", "pose3_horiz_yaw"),
    ("v50", "04", "pose4_horiz_broadside"),
    ("v50", "16", "pose5_horiz_yaw"),
    ("v50", "13", "pose6_horiz_yaw"),
]

for tag, idx, name in SEL:
    fs = glob.glob(os.path.join(FR, tag, f"{tag}_{idx}_*.png"))
    if not fs:
        print("MISSING", tag, idx, flush=True)
        continue
    img = Image.open(fs[0]).convert("RGBA")
    cut = remove(img, session=SESSION,
                 alpha_matting=True, alpha_matting_foreground_threshold=240,
                 alpha_matting_background_threshold=15)   # transparent background
    base = f"hw_{name}_{tag}{idx}"
    cut.save(os.path.join(OUT, base + ".png"))          # transparent PNG (deliverable)
    bg = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    bg.alpha_composite(cut)
    bg.convert("RGB").save(os.path.join(OUT, base + "_white.png"))   # preview on white
    print("CUTOUT", base, flush=True)

print("DONE", flush=True)

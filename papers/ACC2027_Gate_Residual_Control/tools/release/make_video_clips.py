"""Compress the full mission video and cut one clip per mission (for README embedding, target < 10 MB each).
    python tools/release/make_video_clips.py <release_root>/media
Timeline of the full video: 4-s title card, then five 45-s missions, then the summary card.
"""
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
media = Path(sys.argv[1])
src = media / "missions_x2_cf2_realtime.mp4"
raw = media / "_raw.mp4"
src.replace(raw)
run = lambda *a: subprocess.run([FF, "-y", "-loglevel", "error", *a], check=True)
run("-i", str(raw), "-c:v", "libx264", "-crf", "26", "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(src))
(media / "clips").mkdir(exist_ok=True)
for k, m in enumerate(["roll", "full3", "hard45", "hardstep", "yaw360"]):
    out = media / "clips" / f"{m}.mp4"
    run("-ss", str(4 + 45 * k), "-t", "45", "-i", str(raw), "-vf", "scale=960:540", "-c:v", "libx264", "-crf", "30",
        "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out))
gif = media / "hard45_excerpt.gif"          # Hard45, t = 10-22 s, palette-optimized for the README
run("-ss", str(4 + 90 + 10), "-t", "12", "-i", str(raw), "-vf",
    "fps=8,scale=760:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
    str(gif))
raw.unlink()
print(f"{gif.name}: {gif.stat().st_size / 1e6:.1f} MB")
for p in [src] + sorted((media / "clips").glob("*.mp4")):
    print(f"{p.name}: {p.stat().st_size / 1e6:.1f} MB")

"""Selective event encoding: which signals become events, which stay continuous."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

NL = chr(10)
EV, CT, MIX, HUB, GREY = "#c0533f", "#2f6fa8", "#b8860b", "#6c3f9e", "#3f3f3f"
fig, ax = plt.subplots(figsize=(11.6, 5.9))
ax.set_xlim(0, 128); ax.set_ylim(0, 62); ax.axis("off")

def box(x, y, w, h, t, c, fs=8.3, bold=False, fill="white", ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                 linewidth=1.4, edgecolor=c, facecolor=fill, linestyle=ls))
    ax.text(x+w/2, y+h/2, t, ha="center", va="center", fontsize=fs, color=c,
            fontweight="bold" if bold else "normal", linespacing=1.35)

def arr(x1, y1, x2, y2, c=GREY, lw=1.3, ls="-"):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2), arrowstyle="-|>", mutation_scale=11,
                 linewidth=lw, color=c, linestyle=ls, shrinkA=1, shrinkB=1))

ax.text(1, 58.5, "QCar 2  --  heterogeneous sensor testbed  (record everything, analyse four classes)",
        fontsize=9.6, fontweight="bold", color="black")

rows = [
  (47.0, "A   wheel encoder / tacho", "transition dominated",  "EVENT-DRIVEN",      EV),
  (37.5, "B   IMU  (gyro / accel)",   "smooth + transients",   "BOTH, compared",    MIX),
  (28.0, "C   LiDAR / RGB-D depth",   "sparse geometry change","SELECTIVE events",  MIX),
  (18.5, "D   4x CSI + RGB-D frames", "dense, textured",       "CONTINUOUS frames", CT),
]
for y, name, nature, verdict, c in rows:
    box(1, y, 27, 7.6, name, c, fs=8.4, bold=True)
    box(30, y, 24, 7.6, nature, GREY, fs=8.0)
    box(56, y, 23, 7.6, verdict, c, fs=8.3, bold=True)
    arr(28, y+3.8, 30, y+3.8, GREY); arr(54, y+3.8, 56, y+3.8, c)

hub = NL.join(["hybrid", "representation", "", "single state", "estimate"])
box(84, 26.0, 20, 22.5, hub, HUB, fs=8.8, bold=True, fill="#f7f3fb", ls="--")
for y, _, _, _, c in rows:
    arr(79, y+3.8, 84, 37.0, c, lw=1.1)

met = NL.join(["measured:", "", "information", "retained", "", "events / s", "", "task error", "", "data volume"])
box(108, 26.0, 19, 22.5, met, GREY, fs=8.0, bold=True)
arr(104, 37.2, 108, 37.2, HUB)

eeg = NL.join(["E   EEG, self-recorded (author only):  does the same rule transfer to a broadband biological signal,",
               "or does weak structure demand continuous sampling?    --    validation case, not a BCI"])
box(1, 5.0, 78, 9.0, eeg, HUB, fs=8.2, ls="--")
arr(79, 9.5, 90, 26.0, HUB, lw=1.1, ls="--")

ax.text(1, 1.3, "threshold Delta and word length swept on one representative stream",
        fontsize=8.1, color=GREY, style="italic")
plt.tight_layout()
plt.savefig("figures/architecture.png", dpi=190, bbox_inches="tight", facecolor="white")
print("wrote figures/architecture.png")
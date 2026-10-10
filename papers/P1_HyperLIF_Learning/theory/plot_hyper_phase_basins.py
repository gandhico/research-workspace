"""Finite-time gate-basin map from the streamed Julia CSV."""
import csv
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap

root = Path(__file__).resolve().parent
rows = list(csv.DictReader((root / "results/hyper_phase_basin_map_2026-10-06.csv").open()))
weights = sorted({float(row["theta"]) for row in rows})
phases = sorted({float(row["phase"]) for row in rows})
classes = {"high_low": 0, "high_high": 1, "low_high": 2,
           "low_low": 3, "intermediate": 4}
grid = np.full((len(weights), len(phases)), np.nan)
wi = {v: i for i, v in enumerate(weights)}
pi = {v: i for i, v in enumerate(phases)}
for row in rows:
    grid[wi[float(row["theta"])], pi[float(row["phase"])]] = classes[row["basin"]]

fig, ax = plt.subplots(figsize=(8.4, 4.4), layout="constrained")
cmap = ListedColormap(["#31688e", "#35b779", "#fde725", "#440154", "#db5f57"])
norm = BoundaryNorm(np.arange(-0.5, 5.5, 1), cmap.N)
im = ax.imshow(grid, origin="lower", aspect="auto", cmap=cmap, norm=norm,
               extent=[phases[0] - np.pi/32, phases[-1] + np.pi/32,
                       weights[0] - 0.025, weights[-1] + 0.025])
ax.scatter([0.77, 1.91, 0.77, 1.91],
           [0.30715511, 0.30715511, 0.565657444, 0.565657444],
           facecolors="none", edgecolors="black", s=92, linewidths=1.5)
ax.set(xlabel="Input phase φ (rad)", ylabel="Connection weight θ",
       title="Coupled HyperLIF γ=2: gate state after 4 s")
ax.set_xticks([0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi],
              labels=["0", "π/2", "π", "3π/2", "2π"])
bar = fig.colorbar(im, ax=ax, ticks=list(classes.values()), shrink=0.85)
bar.ax.set_yticklabels(["r₁ high, r₂ low", "both high", "r₁ low, r₂ high",
                        "both low", "intermediate"])
fig.savefig(root / "results/hyper_phase_basin_map_2026-10-06.png", dpi=180)

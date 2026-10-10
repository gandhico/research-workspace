"""Plot empirical ACC basin classes and a finite-rate current sweep."""
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

root = Path(__file__).resolve().parent
rows = list(csv.reader((root / "results/acc_basin_hysteresis_2026-10-06.csv").open(encoding="utf-8-sig")))
basin = [r for r in rows if r[0] == "basin" and r[1] != "current"]
if len(basin) != 121:
    raise RuntimeError(f"Expected 121 basin samples, found {len(basin)}")

v0s = sorted({float(r[2]) for r in basin})
r0s = sorted({float(r[3]) for r in basin})
grid = np.full((len(r0s), len(v0s)), np.nan)
codes = {"low": 0, "high": 1, "unsettled": 2}
for r in basin:
    grid[r0s.index(float(r[3])), v0s.index(float(r[2]))] = codes[r[6]]

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.4, 3.7), layout="constrained")
from matplotlib.colors import ListedColormap

ax1.imshow(grid, origin="lower", extent=(-.06, 1.26, -.05, 1.05),
           aspect="auto", interpolation="nearest",
           cmap=ListedColormap(["#3B7D9A", "#D97842", "#888888"]),
           vmin=-.5, vmax=2.5)
ax1.set(xlabel="Initial voltage $v_0$", ylabel="Initial readiness $r_0$",
        title="ACC at $I=0.87$: sampled attraction basins")
ax1.text(.04, .09, "low gate", transform=ax1.transAxes, color="white", weight="bold")
ax1.text(.73, .89, "high gate", transform=ax1.transAxes, color="white", weight="bold")

for direction, color in (("up", "#3B7D9A"), ("down", "#D97842")):
    sweep = [r for r in rows if r[0] == "sweep" and r[1] == direction]
    ax2.plot([float(r[2]) for r in sweep], [float(r[3]) for r in sweep],
             marker="o", markersize=3.4, linewidth=1.3, color=color,
             label=f"{direction} sweep, 1 s/current")
ax2.axvline(.8888130904381024, color="#555555", linestyle=":", linewidth=1.2,
            label="certified local fold")
ax2.set(xlabel="Constant current $I$", ylabel="Last 0.5 s mean voltage",
        title="History-dependent branch selection", xlim=(.812, 1.028))
ax2.legend(loc="center right", fontsize=8, frameon=False)

out = root / "results/acc_basin_hysteresis_2026-10-06.png"
fig.savefig(out, dpi=180)
print(out)

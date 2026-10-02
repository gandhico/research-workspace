"""Render the cell/seed research screen as a compact explanatory figure."""
from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
SCREEN = ROOT / "output" / "paired_authority_screen_20260910"
NOMINAL = ROOT / "output" / "nominal_500hz_check_20260910"

screen = {x["controller"]: x for x in json.loads((SCREEN/"aggregate.json").read_text())}
nominal = {x["controller"]: x for x in json.loads((NOMINAL/"aggregate.json").read_text())}
labels = ["PD", "CMG actual\n12 células", "CMG revisado\n12 células"]
keys = ["pd", "legacy_12", "cmg_12"]
colors = ["#4C78A8", "#F58518", "#2CA02C"]

fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), constrained_layout=True)
pos = [100*screen[k]["mean_position_RMSE_m"] for k in keys]
att = [screen[k]["mean_attitude_RMSE_deg"] for k in keys]
axes[0].bar(labels, pos, color=colors)
axes[0].set_ylabel("RMSE posición [cm]")
axes[0].set_title("Perturbaciones y modelo incierto")
axes[0].grid(axis="y", alpha=.25)
axes[1].bar(labels, att, color=colors)
axes[1].set_ylabel("RMSE actitud [deg]")
axes[1].set_title("Perturbaciones y modelo incierto")
axes[1].grid(axis="y", alpha=.25)

cell_keys = ["cmg_12", "cmg_48", "cmg_192"]
cells = [screen[k]["cells"] for k in cell_keys]
relative_pos = [screen[k]["mean_position_RMSE_m"]/screen["cmg_12"]["mean_position_RMSE_m"] for k in cell_keys]
relative_att = [screen[k]["mean_attitude_RMSE_deg"]/screen["cmg_12"]["mean_attitude_RMSE_deg"] for k in cell_keys]
axes[2].plot(cells, relative_pos, "o-", label="Posición")
axes[2].plot(cells, relative_att, "s-", label="Actitud")
axes[2].axhline(1., color="black", linewidth=.8, alpha=.6)
axes[2].set_xscale("log", base=2)
axes[2].set_xticks(cells, [str(c) for c in cells])
axes[2].set_ylim(.97, 1.03)
axes[2].set_xlabel("Número total de células CMG")
axes[2].set_ylabel("RMSE relativo a 12 células")
axes[2].set_title("Más células: sin mejora media")
axes[2].grid(alpha=.25)
axes[2].legend()

fig.suptitle("Omnicopter: resultados preliminares CMG-PES\n3 semillas × 2 misiones; screening a 200 Hz")
output = ROOT / "output" / "RESEARCH_SUMMARY_20260910.png"
fig.savefig(output, dpi=180)
plt.close(fig)
print(output)

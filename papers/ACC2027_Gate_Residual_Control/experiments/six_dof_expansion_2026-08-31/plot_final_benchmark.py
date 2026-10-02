"""Final benchmark comparison: classical vs CMG-PES vs CMG-eprop_anneal vs
LIF/ALIF/Izhikevich/LIFRate, X2 6-DOF cascade, full6_stress (the mission
with full coverage across every engine). Last figure of this research phase.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
MISSION = "full6_stress"

ENGINES = ["classical", "cmg_pes", "cmg_eprop", "lifrate", "alif", "lif", "izhikevich"]
COLORS = {"classical": "gray", "cmg_pes": "tab:red", "cmg_eprop": "tab:brown",
          "lifrate": "tab:orange", "alif": "tab:green", "lif": "tab:blue", "izhikevich": "tab:purple"}
LABELS = {"classical": "classical", "cmg_pes": "CMG-PES", "cmg_eprop": "CMG-eprop_anneal",
          "lifrate": "LIFRate-PES", "alif": "ALIF-PES", "lif": "LIF-PES", "izhikevich": "Izhikevich-PES"}
DIRS = {
    "classical": ROOT/"results"/"optionA"/f"{MISSION}_classical",
    "cmg_pes": ROOT/"results"/"optionA"/f"{MISSION}_pes",
    "cmg_eprop": ROOT/"results"/"eprop_x2"/MISSION,
    "lifrate": ROOT/"results"/"nengo_families"/f"x2_lifrate_{MISSION}",
    "alif": ROOT/"results"/"nengo_families"/f"x2_alif_{MISSION}",
    "lif": ROOT/"results"/"nengo_families"/f"x2_lif_{MISSION}",
    "izhikevich": ROOT/"results"/"nengo_families"/f"x2_izhikevich_{MISSION}",
}


def load_trace(run_dir: Path) -> dict[str, np.ndarray]:
    with (run_dir/"trace.csv").open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


if __name__ == "__main__":
    summ = {e: json.loads((d/"summary.json").read_text()) for e, d in DIRS.items()}

    fig = plt.figure(figsize=(12, 9))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.2, 1])

    ax = fig.add_subplot(gs[0])
    x = np.arange(len(ENGINES))
    pos = [summ[e]["pos_err_mean_m"] for e in ENGINES]
    att = [np.rad2deg(summ[e]["qerr_mean_rad"]) for e in ENGINES]
    width = 0.35
    bars1 = ax.bar(x-width/2, pos, width, label="position error (m)", color="steelblue", edgecolor="k")
    ax.set_ylabel("position error mean (m)")
    ax.set_xticks(x); ax.set_xticklabels([LABELS[e] for e in ENGINES], fontsize=9, rotation=15)
    ax2 = ax.twinx()
    bars2 = ax2.bar(x+width/2, att, width, label="attitude error (deg)", color="indianred", edgecolor="k")
    ax2.set_ylabel("attitude error mean (deg)")
    lines = [bars1, bars2]
    ax.legend(lines, [l.get_label() for l in lines], loc="upper right", fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    ax.set_title("FINAL BENCHMARK -- X2 6-DOF cascade, full6_stress: classical vs CMG-PES vs "
                 "CMG-eprop_anneal vs neuron families", fontsize=11, loc="left", fontweight="bold")

    ax = fig.add_subplot(gs[1])
    for e in ENGINES:
        n = load_trace(DIRS[e])
        ax.plot(n["t"], n["pos_err"], color=COLORS[e], lw=1, alpha=0.85, label=LABELS[e])
    ax.set_ylabel("|pos error| (m)")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper left", fontsize=7, ncol=4)
    ax.grid(alpha=0.3)
    ax.set_title("Position-error time series -- both CMG variants (PES, eprop_anneal) track "
                 "almost identically, both far ahead of every spiking family and classical",
                 fontsize=10, loc="left", fontweight="bold")

    fig.suptitle("Last research figure, this phase -- CMG-PES and CMG-eprop_anneal both beat\n"
                 "classical and every spiking neuron family by a wide, consistent margin", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = ROOT/"results"/"plots"/"final_benchmark_full6_stress.png"
    fig.savefig(out, dpi=125)
    plt.close(fig)
    print(f"wrote {out}")

    print("\n=== FINAL BENCHMARK TABLE (full6_stress, X2) ===")
    print(f"{'engine':<20}{'pos err(m)':>12}{'att err(deg)':>14}")
    for e in ENGINES:
        print(f"{LABELS[e]:<20}{summ[e]['pos_err_mean_m']:>12.4f}{np.rad2deg(summ[e]['qerr_mean_rad']):>14.3f}")

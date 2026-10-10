"""Comparison plot: CMG vs LIF/ALIF/Izhikevich/LIFRate on the 6-DOF Option-A
cascade (X2), hover3d (gentle) vs full6_stress (demanding). Two panels:
(1) summary bars, pos/att error per engine per mission; (2) full6_stress
position-error time series overlay, showing CMG staying smooth/bounded
while spiking families show large transient kicks. Reads trace.csv/
summary.json only -- no re-simulation.
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
ENGINES = ["cmg", "lif", "alif", "izhikevich", "lifrate"]
COLORS = {"cmg": "tab:red", "lif": "tab:blue", "alif": "tab:green",
          "izhikevich": "tab:purple", "lifrate": "tab:orange"}
LABELS = {"cmg": "CMG-PES", "lif": "LIF-PES", "alif": "ALIF-PES",
          "izhikevich": "Izhikevich-PES", "lifrate": "LIFRate-PES"}


def load_trace(run_dir: Path) -> dict[str, np.ndarray]:
    with (run_dir/"trace.csv").open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def dirs_for(engine: str, mission: str) -> Path:
    if engine == "cmg":
        return ROOT/"results"/"nengo_x2"/f"{mission}_cmg"
    return ROOT/"results"/"nengo_families"/f"x2_{engine}_{mission}"


if __name__ == "__main__":
    summaries = {}
    for engine in ENGINES:
        for mission in ["hover3d", "full6_stress"]:
            d = dirs_for(engine, mission)
            summaries[(engine, mission)] = json.loads((d/"summary.json").read_text())

    fig = plt.figure(figsize=(12, 9))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.3, 1.1, 1.1])

    ax = fig.add_subplot(gs[0])
    x = np.arange(len(ENGINES))
    width = 0.35
    pos_hover = [summaries[(e, "hover3d")]["pos_err_mean_m"] for e in ENGINES]
    pos_full6 = [summaries[(e, "full6_stress")]["pos_err_mean_m"] for e in ENGINES]
    ax.bar(x-width/2, pos_hover, width, label="hover3d (gentle)", color="lightsteelblue", edgecolor="k")
    ax.bar(x+width/2, pos_full6, width, label="full6_stress (demanding)", color="indianred", edgecolor="k")
    ax.set_xticks(x); ax.set_xticklabels([LABELS[e] for e in ENGINES], fontsize=9)
    ax.set_ylabel("pos error mean (m)")
    ax.axhline(summaries[("cmg", "hover3d")]["pos_err_mean_m"], color="lightsteelblue", ls=":", lw=1, alpha=0.6)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    ax.set_title("SUMMARY -- position error, all neuron families, X2 6-DOF cascade (Option A)",
                 fontsize=10, loc="left", fontweight="bold")

    ax2 = ax.twinx()
    att_hover = [np.rad2deg(summaries[(e, "hover3d")]["qerr_mean_rad"]) for e in ENGINES]
    att_full6 = [np.rad2deg(summaries[(e, "full6_stress")]["qerr_mean_rad"]) for e in ENGINES]

    ax = fig.add_subplot(gs[1])
    for engine in ENGINES:
        n = load_trace(dirs_for(engine, "full6_stress"))
        ax.plot(n["t"], n["pos_err"], color=COLORS[engine], lw=1, alpha=0.85, label=LABELS[engine])
    ax.set_ylabel("|pos error| (m)")
    ax.legend(loc="upper left", fontsize=7, ncol=5)
    ax.grid(alpha=0.3)
    ax.set_title("full6_stress (demanding): position-error time series -- CMG stays smooth/bounded, "
                 "spiking families show large transient kicks", fontsize=10, loc="left", fontweight="bold")

    ax = fig.add_subplot(gs[2])
    for engine in ENGINES:
        n = load_trace(dirs_for(engine, "full6_stress"))
        ax.plot(n["t"], np.rad2deg(n["qerr"]), color=COLORS[engine], lw=1, alpha=0.85, label=LABELS[engine])
    ax.set_ylabel("attitude error (deg)")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper left", fontsize=7, ncol=5)
    ax.grid(alpha=0.3)
    ax.set_title("full6_stress (demanding): attitude-error time series", fontsize=10, loc="left", fontweight="bold")

    fig.suptitle("Neuron-family validation on the 6-DOF realistic cascade (Option A, X2)\n"
                 "CMG-PES at its natural tuning (beta=0.5, lr=8e-4) vs. LIF/ALIF/Izhikevich/LIFRate at "
                 "beta=0.01, lr=1e-4 -- the most conservative setting each survived at (see text)",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out_path = ROOT/"results"/"plots"/"neuron_family_6dof_x2.png"
    fig.savefig(out_path, dpi=125)
    plt.close(fig)
    print(f"wrote {out_path}")

    print("\nSummary table:")
    print(f"{'engine':<14}{'hover pos(m)':>14}{'hover att(deg)':>16}{'full6 pos(m)':>14}{'full6 att(deg)':>16}")
    for e in ENGINES:
        print(f"{LABELS[e]:<14}{summaries[(e,'hover3d')]['pos_err_mean_m']:>14.4f}"
              f"{np.rad2deg(summaries[(e,'hover3d')]['qerr_mean_rad']):>16.3f}"
              f"{summaries[(e,'full6_stress')]['pos_err_mean_m']:>14.4f}"
              f"{np.rad2deg(summaries[(e,'full6_stress')]['qerr_mean_rad']):>16.3f}")

"""CMG-PES ungated vs gated vs Izhikevich-PES on the primary baseline (PD+ff, rho = 3), X2 -- reference figures for the advisors.

Two formats, title-free:
  * attitude detail:  error + roll/pitch/yaw in one window, all arms overlaid (ungated drawn wide and translucent under the
                      gated line, so where the gate is inert the two visibly coincide)
  * neuron activity:  one column per arm (the neuron models have different states), residual and decoder norm on shared axes
Outputs: figures_out/izh_compare/
"""
from __future__ import annotations

import sys
from pathlib import Path

import figlib as F
import figlib_multi as FM

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures_out" / "izh_compare"
R = HERE / "results"
NAMES = {"pdff_rho3": "PD+ff (baseline)", "cmg_pes_table": "CMG-PES, ungated", "cmg_pes_gated": "CMG-PES, gated", "izhikevich_pes": "Izhikevich-PES"}
STYLES = {"pdff_rho3": dict(lw=0.9, alpha=0.85, zorder=2),
          "cmg_pes_table": dict(lw=2.4, alpha=0.40, zorder=2),
          "izhikevich_pes": dict(lw=0.9, zorder=3),
          "cmg_pes_gated": dict(lw=0.9, zorder=4)}


def arms(mission: str) -> dict:
    nom = R / "confirmatory" / "nominal" / "x2" / mission
    runs = {   # dict order = legend order; drawing order is set by the explicit zorder in STYLES
        "pdff_rho3": F.load(nom / "pdff_rho3" / "nominal" / "seed_001")[0],
        "cmg_pes_table": F.load(nom / "cmg_pes_table" / "nominal" / "seed_001")[0],
        "cmg_pes_gated": F.load(nom / "cmg_pes_gated" / "load_1" / "seed_001")[0],
        "izhikevich_pes": FM.load_archived(R / "supplementary_izhikevich" / "x2" / mission / "nengo_izhikevich_pes")[0],
    }
    return runs


def build(mission: str, *, err_unit: str, err_ylim=None, zoom=None, size=(6.2, 5.7)):
    runs = arms(mission)
    for df in runs.values():
        assert F.check_euler_convention(df) < 1e-6
    F.attitude_figure(runs, OUT / f"x2_{mission}_attitude_ungated_gated_izhikevich", size=size, err_unit=err_unit, err_ylim=err_ylim,
                      legend_cols=5, legend_h=0.30, names=NAMES, styles=STYLES)
    if zoom:
        F.attitude_figure(runs, OUT / f"x2_{mission}_attitude_ungated_gated_izhikevich_zoom", size=size, err_unit=err_unit,
                          t_window=zoom, legend_cols=5, legend_h=0.30, names=NAMES, styles=STYLES, err_log=True, err_ylim=(0.02, 200))
    cols = [dict(name="CMG-PES, ungated", df=runs["cmg_pes_table"], family="cmg"),
            dict(name="CMG-PES, gated", df=runs["cmg_pes_gated"], family="cmg"),
            dict(name="Izhikevich-PES", df=runs["izhikevich_pes"], family="izh")]
    FM.neuron_columns_figure(cols, OUT / f"x2_{mission}_neurons_ungated_gated_izhikevich")
    # the Izhikevich residual chatters between its +/- beta*l rails, which is unreadable at 45 s scale: a 6-s window shows it
    z = zoom or (10.0, 16.0)
    FM.neuron_columns_figure(cols, OUT / f"x2_{mission}_neurons_ungated_gated_izhikevich_zoom", t_window=z)


if __name__ == "__main__":
    which = sys.argv[1:] or ["hard45", "hardstep", "roll"]
    OUT.mkdir(parents=True, exist_ok=True)
    if "hard45" in which:
        build("hard45", err_unit="mrad", err_ylim=(0, 30))
    if "hardstep" in which:
        build("hardstep", err_unit="deg", zoom=(9.0, 15.0))
    if "roll" in which:
        build("roll", err_unit="mrad")
    print("done ->", OUT)

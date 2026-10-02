"""A3 reference figures: CMG-PES ungated / gated vs Izhikevich-PES (gated, and ungated where run) under the CMG protocol, both airframes.

Same two title-free formats as before:
  * attitude detail  -- error + roll/pitch/yaw in one window; ungated arms drawn wide and translucent under the gated lines
  * neuron activity  -- one column per arm; residual and decoder norm on shared axes
Every trace comes from the same runner and baseline (PD+ff, rho = 3).  Outputs: figures_out/izh_a3/
"""
from __future__ import annotations

import sys
from pathlib import Path

import figlib as F
import figlib_multi as FM

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures_out" / "izh_a3"
R = HERE / "results"
F.COLORS["izhikevich_pes_gated"] = "#4B1D7A"
F.COLORS["izhikevich_pes"] = "#B58BD4"
NAMES = {"pdff_rho3": "PD+ff (baseline)", "cmg_pes_table": "CMG-PES, ungated", "cmg_pes_gated": "CMG-PES, gated",
         "izhikevich_pes": "Izhikevich-PES, ungated", "izhikevich_pes_gated": "Izhikevich-PES, gated"}
STYLES = {"pdff_rho3": dict(lw=0.9, alpha=0.85, zorder=2),
          "cmg_pes_table": dict(lw=2.4, alpha=0.40, zorder=2),
          "izhikevich_pes": dict(lw=2.4, alpha=0.55, zorder=2),
          "cmg_pes_gated": dict(lw=0.9, zorder=4),
          "izhikevich_pes_gated": dict(lw=0.9, zorder=5)}
BETA_IZH = {"x2": "b0p5", "cf2-rotor": "b0p2"}
TAG = {"x2": "x2", "cf2-rotor": "cf2"}


def run_paths(plat: str, mission: str) -> dict:
    nom = R / "confirmatory" / "nominal" / plat / mission
    izh = R / "izh_a3" / "nominal" / plat / mission
    b = BETA_IZH[plat]
    cmg_gated = (nom / "cmg_pes_gated" / "load_1" / "seed_001") if plat == "x2" else \
        (R / "confirmatory_a2" / "a2_nominal" / plat / mission / "cmg_pes_gated_b02" / "load_1" / "seed_001")
    paths = {"pdff_rho3": nom / "pdff_rho3" / "nominal" / "seed_001",
             "cmg_pes_table": nom / "cmg_pes_table" / "nominal" / "seed_001",
             "cmg_pes_gated": cmg_gated}
    ungated_izh = izh / f"izh_pes_ungated_{b}" / "nominal" / "seed_001"
    if ungated_izh.exists():
        paths["izhikevich_pes"] = ungated_izh
    paths["izhikevich_pes_gated"] = izh / f"izh_pes_gated_{b}" / "load_1" / "seed_001"
    return paths


def arms(plat: str, mission: str) -> dict:
    return {k: F.load(p)[0] for k, p in run_paths(plat, mission).items()}


def build(plat: str, mission: str, *, err_unit: str, err_ylim=None, zoom=None, size=(6.2, 5.9)):
    runs = arms(plat, mission)
    for df in runs.values():
        assert F.check_euler_convention(df) < 1e-6
    n = len(runs)
    common = dict(size=size, err_unit=err_unit, legend_cols=3 if n > 4 else 5, legend_h=0.52 if n > 4 else 0.30, names=NAMES, styles=STYLES)
    stem = f"{TAG[plat]}_{mission}"
    F.attitude_figure(runs, OUT / f"{stem}_attitude", err_ylim=err_ylim, **common)
    if zoom:
        F.attitude_figure(runs, OUT / f"{stem}_attitude_zoom", t_window=zoom, err_log=True, err_ylim=(0.02, 200), **common)
    cols = [dict(name="CMG-PES, ungated", df=runs["cmg_pes_table"], family="cmg"),
            dict(name="CMG-PES, gated", df=runs["cmg_pes_gated"], family="cmg")]
    if "izhikevich_pes" in runs:
        cols.append(dict(name="Izhikevich-PES, ungated", df=runs["izhikevich_pes"], family="izh"))
    cols.append(dict(name="Izhikevich-PES, gated", df=runs["izhikevich_pes_gated"], family="izh"))
    w = 2.45 * len(cols) + 0.3
    FM.neuron_columns_figure(cols, OUT / f"{stem}_neurons", size=(w, 4.7))
    z = zoom or (10.0, 16.0)
    FM.neuron_columns_figure(cols, OUT / f"{stem}_neurons_zoom", size=(w, 4.7), t_window=z)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for plat in ("x2", "cf2-rotor"):
        build(plat, "hard45", err_unit="mrad", err_ylim=(0, 30) if plat == "x2" else None)
        build(plat, "hardstep", err_unit="deg", zoom=(9.0, 15.0))
        build(plat, "roll", err_unit="mrad")
    print("done ->", OUT)

"""v14: the two paper figures (Fig. 2 compact Hard45, Fig. 3 Hardstep gate zoom) at slightly lower height, same content and fonts.

Only the figure height changes (2.10 -> 1.85 in and 2.40 -> 2.15 in) to buy the space the Izhikevich comparison needs inside the
7-page limit; data, panels and text sizes are those of v13.  Writes figures_out/v14/ (the v13 files are untouched).
"""
from __future__ import annotations

from pathlib import Path

import figlib as F
import make_paper_figures as mpf

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures_out" / "v14"
OUT.mkdir(parents=True, exist_ok=True)
mpf.OUT = OUT

runs = {a: F.load(mpf.nominal("x2", "hard45", a))[0] for a in ("pdff_rho3", "cmg_pes_table")}
for df in runs.values():
    assert F.check_euler_convention(df) < 1e-6
F.attitude_figure(runs, OUT / "x2_hard45_attitude_rho3_compact", size=(3.45, 1.85), err_ylim=(0, 25), legend_cols=3, euler_axes=(0,))
mpf.hardstep_gate("x2", axis="z", size=(3.45, 2.15))
print("done ->", OUT)

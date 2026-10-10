"""Paper Fig. 4 (X2 Hard45 baseline ladder, variant C) plus the gated reduced CMG on the tuned baseline, error row only.

Everything else is the original make_ladder_figure.py figure: same six runs, colours, zoom and table check. The extra
trace takes the legend's empty slot, so the figure keeps its size.
Output: analysis/fig4/x2_hard45_ladder_with_reduced.{pdf,png,json}
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FINAL = HERE.parents[0] / "final_robustness_gating_2026-09-20"
sys.path.insert(0, str(FINAL))
import make_ladder_figure as L  # noqa: E402

RED_RUN = HERE / "results" / "confirm" / "x2" / "hard45" / "lpf-logistic"
COLOR = "#5E3C99"            # purple: distinct from the blue PD and red CMG families
EXTRA = L._load_sealed(RED_RUN)

src = inspect.getsource(L.ladder_figure)
plot_extra = (
    "        axs[0, c].plot(EXTRA['t'][m], np.clip(np.degrees(EXTRA['err']), 0.01, None)[m], color=COLOR, "
    "lw=1.05 * (1.1 if zoom else 1.0), ls=(0, (3, 1.3)), alpha=0.95, zorder=9)\n"
    "        # ... and the reference on top of them, opaque"
)
src = src.replace("        # ... and the reference on top of them, opaque", plot_extra, 1)
legend_extra = (
    "    handles.append(Line2D([], [], color=COLOR, lw=2.0, ls=(0, (3, 1.3))))\n"
    "    labels.append(EXTRA_NAME + f\"   {np.degrees(EXTRA['mean']):.2f}°  \" + "
    "f\"({100 * (EXTRA['mean'] - pdr[2]['mean']) / pdr[2]['mean']:+.1f}%)\".replace('-', '−'))"
)
old_empty = '    handles.append(Line2D([], [], color="none"))\n    labels.append("")'
assert old_empty in src
src = src.replace(old_empty, legend_extra, 1)
src = src.replace('_ladder_{variant}{suffix}"', '_ladder_with_reduced"')
L.EXTRA, L.COLOR, L.EXTRA_NAME = EXTRA, COLOR, r"PD+ff $\rho{=}3$ + reduced CMG, gated"
L.OUT = HERE / "analysis" / "fig4"
exec(compile(src, L.__file__, "exec"), L.__dict__)

if __name__ == "__main__":
    stem = L.ladder_figure("x2", "hard45", "C")
    meta = json.loads(stem.with_suffix(".json").read_text())
    meta["extra_trace"] = {"label": "PD+ff rho=3 + reduced CMG, gated", "mean_mrad": EXTRA["mean"] * 1e3, "source": str(RED_RUN)}
    stem.with_suffix(".json").write_text(json.dumps(meta, indent=2))
    print("wrote", stem)

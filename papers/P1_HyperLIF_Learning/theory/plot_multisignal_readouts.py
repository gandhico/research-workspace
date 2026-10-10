"""Scientific figure for cold and settled two-cell readout transfer."""
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

base = Path(__file__).resolve().parent
rows = list(csv.DictReader((base / "results/acc_multisignal_readout_2026-10-06.csv").open(encoding="utf-8-sig")))
names = [
    ("gate_raw", "raw gate"),
    ("gate_clipped", "clipped gate"),
    ("membrane", "membrane"),
    ("conductance_gateonly", "gate-only conductance"),
    ("conductance_full", "full conductance"),
    ("reset_current", "reset current"),
    ("v_plus_gate", "membrane + gate"),
    ("v_plus_conductance", "membrane + conductance"),
    ("v_gate_conductance", "membrane + gate + conductance"),
]
lookup = {(r["gamma"], r["window"], r["readout"]): float(r["test_mean_rmse"]) for r in rows}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
fig, axes = plt.subplots(1, 2, figsize=(11.4, 5.1), sharey=True, layout="constrained")
pos = np.arange(len(names))
for ax, gamma in zip(axes, ("0.000", "2.000")):
    cold = [lookup[(gamma, "cold", key)] for key, _ in names]
    settled = [lookup[(gamma, "settled", key)] for key, _ in names]
    ax.barh(pos - .18, cold, height=.34, color="#3B7D9A", label="cold start")
    ax.barh(pos + .18, settled, height=.34, color="#D97842", label="settled")
    ax.axvline(.205, color="#777777", linestyle=":", linewidth=1, label="target RMS")
    ax.set(xlim=(0,.225), xlabel="Fresh-phase linear-decoder RMSE",
           title=f"ACC gate feedback γ = {float(gamma):g}")
    ax.grid(axis="x", color="#E5E5E5", linewidth=.6)
    ax.set_axisbelow(True)
axes[0].set_yticks(pos, [label for _, label in names])
axes[0].invert_yaxis()
axes[1].legend(loc="lower right", frameon=False, fontsize=8)
fig.suptitle("Two-cell readouts: external sinusoid, train phase 0, two fresh phases")
out = base / "results/acc_multisignal_readout_2026-10-06.png"
fig.savefig(out, dpi=180)
print(out)

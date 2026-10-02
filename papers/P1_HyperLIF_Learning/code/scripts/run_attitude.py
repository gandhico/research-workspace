"""Closed-loop attitude control: PD vs PD+residual, comparing residual readouts
{gate, conductance, hybrid} x neurons {HyperLIF, Adaptive, +origin} across a drive sweep.

Reports % tracking-RMSE improvement over the PD baseline (positive = better). Tests whether the
conductance residual's signal-level selectivity (+64%) converts to a control win, and whether
Adaptive/origin now beat plain HyperLIF (unlike the gate readout, where they're identical).

    python scripts/run_attitude.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adhyperlif_triage.control.attitude import (  # noqa: E402
    Attitude1D, ResidualController, disturbance_profile, pd_gains, reference, run_episode,
)
from adhyperlif_triage.neurons import HyperLIFConfig  # noqa: E402

DT = 5e-4
I_INERTIA = 0.05
T_TOTAL = 6.0
DRIVES = [1.0, 2.0, 3.0]


def ccfg(model, **kw):
    base = dict(tau=0.05, tau_r=0.005, alpha=50.0, gamma=2.0, v_thresh=1.0, v_rest=0.0, v_reset=0.0,
                reset_gain=120.0, base_gain=120.0, gain_scaling=80.0, amplitude=1.0)
    base.update(kw)
    return HyperLIFConfig(model=model, **base)


NEURONS = [("HyperLIF", ccfg("hyperlif")),
           ("Adaptive", ccfg("adaptive_hyperlif")),
           ("Adaptive+origin", ccfg("adaptive_hyperlif", delta_reset=0.5, min_voltage=-2.0))]
MODES = [("gate", 1e5), ("conductance", 1.0), ("hybrid", 1.0)]  # (readout, gate_gain)


def main():
    gains = pd_gains(I_INERTIA, zeta=0.4)  # UNDER-damped PD (overshoots) -> a gain schedule can help
    plant = Attitude1D(I=I_INERTIA, b=0.10, dt=DT, tau_limit=gains["tau_limit"])
    n = int(T_TOTAL / DT)

    dist = disturbance_profile(n, DT, amp=0.4 * gains["tau_limit"])  # unmodeled disturbance (40% authority)
    pd_rmse = {}
    for dr in DRIVES:
        ctrl = ResidualController(ccfg("hyperlif"), DT, mode="none")
        pd_rmse[dr] = run_episode(plant, ctrl, reference(n, DT, dr), gains, disturbance=dist)["rmse"]
    print(f"PD baseline RMSE [rad] (with disturbance): " + "  ".join(f"drive{dr}={pd_rmse[dr]:.4f}" for dr in DRIVES))
    print("(values below = % RMSE improvement over PD; positive=better; act = mean residual activity)\n")

    print(f"{'mode':12s} {'neuron':16s} " + "".join(f"{'d'+str(dr):>8s}" for dr in DRIVES) + f"{'act':>8s}")
    for mode, gg in MODES:
        for nname, cfg in NEURONS:
            cells, acts = "", []
            for dr in DRIVES:
                ctrl = ResidualController(cfg, DT, mode=mode, blend=0.5, gate_gain=gg)
                res = run_episode(plant, ctrl, reference(n, DT, dr), gains, disturbance=dist)
                if res is None:
                    cells += f"{'div':>8s}"; acts.append(float("nan"))
                else:
                    imp = (pd_rmse[dr] - res["rmse"]) / pd_rmse[dr] * 100.0
                    cells += f"{imp:>8.2f}"; acts.append(res["activity"])
            print(f"{mode:12s} {nname:16s} {cells}{np.nanmean(acts):>8.3f}")
        print()


if __name__ == "__main__":
    main()

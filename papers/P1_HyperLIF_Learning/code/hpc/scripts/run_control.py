"""Pendulum control probe: spiking controllers (LIF / HyperLIF / Adaptive / +origin) imitate a PD
controller, then run closed-loop across a drive sweep. Hypothesis: the HyperLIF family tracks
better / stays stable in the HIGH-drive (saturated) band where adaptation is theorized to matter.

    python scripts/run_control.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adhyperlif_triage.control import Pendulum, make_demos, make_reference, rollout_pd, tracking_rmse  # noqa: E402
from adhyperlif_triage.control.control_model import ControlNet, fit_readout_ridge  # noqa: E402
from adhyperlif_triage.neurons import HyperLIFConfig  # noqa: E402

DT = 0.02


def cfg(model, **kw):
    base = dict(tau=0.1, tau_r=0.02, alpha=50.0, gamma=0.2, reset_gain=20.0,
                base_gain=10.0, gain_scaling=40.0, amplitude=1.0)
    base.update(kw)
    return HyperLIFConfig(model=model, **base)


ROSTER = [
    ("LIF", cfg("lif", lif_reset_mode="to_reset", min_voltage=-2.0)),
    ("ALIF", cfg("alif", tau_a=0.5, beta_a=1.0)),
    ("HyperLIF", cfg("hyperlif")),
    ("Adaptive", cfg("adaptive_hyperlif")),
    ("Adaptive+origin", cfg("adaptive_hyperlif", v_reset=-0.6, delta_reset=0.3, min_voltage=-2.0)),
]
DRIVES = [1.0, 2.5, 4.0]
TEST_SEEDS = [100, 101, 102]


def eval_controller(net, plant):
    out = {}
    for dr in DRIVES:
        rmses, div = [], 0
        for s in TEST_SEEDS:
            ref = make_reference(250, DT, drive=dr, kind="sine", seed=s)
            ang, _, diverged = net.rollout(plant, ref)
            if diverged:
                div += 1
            else:
                rmses.append(tracking_rmse(ang, ref))
        out[dr] = (np.mean(rmses) if rmses else float("nan"), div)
    return out


def main():
    plant = Pendulum(dt=DT, u_max=10.0)
    feats_tr, u_tr = make_demos(plant, T=200, n=30, drive=1.8, kind="steps", seed=0)

    pd = {}
    for dr in DRIVES:
        rs = []
        for s in TEST_SEEDS:
            ref = make_reference(250, DT, drive=dr, kind="sine", seed=s)
            _, _, ang = rollout_pd(plant, ref)
            rs.append(tracking_rmse(ang, ref))
        pd[dr] = np.mean(rs)

    print(f"PD demonstrator tracking RMSE (lower=better): " + "  ".join(f"d{dr}={pd[dr]:.3f}" for dr in DRIVES))
    print("(controller RMSE; 'div' = diverged. Closer to PD = better; watch the high-drive d4.0 column.)\n")
    print(f"{'controller':18s} " + "".join(f"{'d'+str(dr):>10s}" for dr in DRIVES) + f"{'imit_MSE':>10s}")
    for name, c in ROSTER:
        net = ControlNet(c, dt=DT, n_res=64, input_scale=1.5, seed=0)
        mse = fit_readout_ridge(net, feats_tr, u_tr)
        res = eval_controller(net, plant)
        cells = ""
        for dr in DRIVES:
            r, div = res[dr]
            cells += (f"{r:.3f}" if np.isfinite(r) else "div").rjust(10) if div == 0 else f"{('div' if not np.isfinite(r) else f'{r:.3f}')+f'/{div}':>10s}"
        print(f"{name:18s} {cells}{mse:>10.3f}")


if __name__ == "__main__":
    main()

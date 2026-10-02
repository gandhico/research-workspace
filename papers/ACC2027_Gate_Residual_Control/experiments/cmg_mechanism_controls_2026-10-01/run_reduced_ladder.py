"""Run the reduced (non-latching) CMG through an archived runner, for the baseline-ladder figure.

The reduced CMG is the canonical Nengo CoupledMembraneGate with gamma = 0, g0 = g1 = 0 (base_gain =
gain_scaling = 0, so c_j = 0) and tau_r = h (so r_k = sigma(alpha_h (v_{k-1} - v_th)) exactly). It therefore
runs the paper's own Nengo neuron + PES graph; only these four parameters differ.

Runners (same arguments as the archived CMG runs drawn in the ladder):
  final  experiments/final_robustness_gating_2026-09-20/run_izh_robustness.py   (PD+ff rho = 3, gated)
  pd     experiments/nengo_nef_replication_2026-08-29/run_mujoco_nef.py         (original fixed PD; matched_45s)
  ff1    experiments/nengo_nef_replication_2026-08-29/run_mujoco_nef_pid.py     (PD+ff rho = 1, --rate-ff left-neg)

Usage:  python run_reduced_ladder.py <final|pd|ff1> -- <runner arguments with --controller nengo-nef-pes>
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FINAL = REPO / "experiments" / "final_robustness_gating_2026-09-20"
UPSTREAM = REPO / "experiments" / "nengo_nef_replication_2026-08-29"
RUNNERS = {"final": FINAL / "run_izh_robustness.py",
           "pd": UPSTREAM / "run_mujoco_nef.py",
           "ff1": UPSTREAM / "run_mujoco_nef_pid.py"}


def install_reduced_cmg(dt: float) -> None:
    import nengo_cmg

    original = nengo_cmg.CoupledMembraneGate

    class ReducedCMG(original):
        """CoupledMembraneGate in the limit gamma -> 0, c_j -> 0, tau_r -> h."""

        def __init__(self, adaptive=True, **kwargs):
            kwargs.update(gamma=0.0, base_gain=0.0, gain_scaling=0.0, tau_r=dt)
            super().__init__(adaptive=adaptive, **kwargs)

    nengo_cmg.CoupledMembraneGate = ReducedCMG


def main() -> None:
    if len(sys.argv) < 3 or sys.argv[1] not in RUNNERS or sys.argv[2] != "--":
        raise SystemExit(__doc__)
    which, runner_args = sys.argv[1], sys.argv[3:]
    if "nengo-nef-pes" not in runner_args:
        raise SystemExit("pass --controller nengo-nef-pes (the reduced CMG replaces the Nengo CMG neuron)")
    dt = float(runner_args[runner_args.index("--dt") + 1]) if "--dt" in runner_args else 0.0005
    for p in (REPO / "src", UPSTREAM, FINAL, HERE):
        sys.path.insert(0, str(p))
    install_reduced_cmg(dt)
    sys.argv = [str(RUNNERS[which]), *runner_args]
    runpy.run_path(str(RUNNERS[which]), run_name="__main__")


if __name__ == "__main__":
    main()

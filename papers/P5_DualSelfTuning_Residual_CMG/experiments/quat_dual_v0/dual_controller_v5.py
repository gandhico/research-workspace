"""v5: generalize the self-tuner S beyond PID, to LQR/backstepping/MPC/NMPC.

Reuses SelfTuner/TunerConfig/PIDBase from dual_controller.py UNCHANGED (mechanism-generic already: 18 CMG
units, 9x18 PES decoder toward hand targets, v2 gating -- see docs/PLAN.md's v5 declaration). Reuses
AdvancedBaseline (ACC2027 repo, run_mujoco_nef_baselines.py, already certified this week in A5) UNCHANGED too:
every new family stores its angle- and rate-error gains as plain mutable instance attributes (k1/k2, or K0 for
MPC), so S's per-step multipliers (mp on the angle gain, md on the rate gain) are applied by mutating those
attributes before calling the untouched .torque(). No control law is reimplemented here.

Scope, adjusted 2026-09-25 while implementing (see report): SMC excluded (its `eta` is a bounded effort limit,
not a smooth gain -- deferred to its own v5.1 declaration). Missions restricted to the 5 standard ones
(roll/full3/hard45/hardstep/yaw360): AdvancedBaseline's feedforward (_wd/_wd_dot) and NMPC's internal rollout
call gra_control.math3d.reference_quat/reference_rate, which only knows those 5 -- extending to P5's held-out
missions would mean editing gra_control, which is imported read-only by rule. mi (integral multiplier) is
computed by S but unused: none of these four families has an integral term in the AdvancedBaseline/A5 form.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np

ACC = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
sys.path.insert(0, str(ACC / "experiments" / "nengo_nef_replication_2026-08-29"))
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from run_mujoco_nef_baselines import AdvancedBaseline  # noqa: E402
from dual_controller import PIDBase, SelfTuner, TunerConfig  # noqa: E402, F401  (re-exported for run_dual_v5)

FAMILIES = ("lqr", "backstepping", "mpc", "nmpc")


def make_args(family: str, mission: str, duration: float, dt: float, bw_scale: float = 3.0):
    """Minimal args namespace matching A5's own certified AdvancedBaseline settings
    (PREREGISTRATION.md sec.14; run_campaign_a5.py FAMILY_ARGS), baseline_rate_hz=0 (full rate,
    per the 2026-09-25 NMPC hold-rate fix -- AUDIT_NMPC_HOLD_RATE_2026-09-25.md)."""
    return types.SimpleNamespace(
        baseline=family, bw_scale=bw_scale, rate_ff="left-neg", no_model_ff=True,
        baseline_rate_hz=0.0, dt=dt, mission=mission, duration=duration,
        mpc_dt=0.02, mpc_horizon=120, mpc_q_rate=0.0,
        nmpc_dt=0.06, nmpc_horizon=5, nmpc_terminal=1.5, nmpc_offset_frac=0.1,
        nmpc_rate_weight=2.0, nmpc_grid=3, nmpc_predict="policy",
        smc_eta_frac=0.5,  # unused (SMC excluded from v5), present for AdvancedBaseline.__init__ uniformity
    )


class TunedBaseline:
    """Wraps one AdvancedBaseline instance; S's (mp, md) multipliers scale its k1/k2 (or K0) each step.

    mp multiplies the angle-error gain (k1 for lqr/backstepping/nmpc; K0[:,0] for mpc).
    md multiplies the rate-error gain (k2; K0[:,1] for mpc). mi (integral) is unused -- no family here
    has an integral term.
    """

    def __init__(self, family: str, mission: str, duration: float, dt: float, inertia: np.ndarray,
                 limits: np.ndarray, wn: np.ndarray, bw_scale: float = 3.0):
        if family not in FAMILIES:
            raise ValueError(f"v5 does not cover {family!r}; see docs/PLAN.md v5 declaration for the excluded scope")
        self.family = family
        self.args = make_args(family, mission, duration, dt, bw_scale)
        self.baseline = AdvancedBaseline(self.args, inertia, limits, wn)
        if family == "mpc":
            self.K0_base = self.baseline.K0.copy()
        else:
            self.k1_base = self.baseline.k1.copy()
            self.k2_base = self.baseline.k2.copy()

    def torque(self, t: float, eq: np.ndarray, omega: np.ndarray, q_meas: np.ndarray,
               mp: np.ndarray, md: np.ndarray) -> np.ndarray:
        if self.family == "mpc":
            self.baseline.K0 = np.stack([self.K0_base[:, 0] * mp, self.K0_base[:, 1] * md], axis=1)
        else:
            self.baseline.k1 = self.k1_base * mp
            self.baseline.k2 = self.k2_base * md
        return self.baseline.torque(t, eq, omega, q_meas)

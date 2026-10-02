"""Why does the gated beta=0.5 residual diverge on CF2 Hardstep under measurement noise?

Compares, for one moderate-noise seed, the PD+ff arm and the gated arm: when the error departs, what the
torque command / rotor allocation do, and whether the gate (torque-box based) can see the saturation.
"""
import sys
from pathlib import Path

import numpy as np

import figlib as F

HERE = Path(__file__).resolve().parent
R = HERE / "results" / "confirmatory" / "noise" / "cf2-rotor" / "hardstep"
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 2
lvl = sys.argv[2] if len(sys.argv) > 2 else "noise_moderate"
b, sb = F.load(R / "pdff_rho3" / lvl / f"seed_{seed:03d}")
g, sg = F.load(R / "cmg_pes_gated" / f"{lvl}__load_1" / f"seed_{seed:03d}")
lim = np.array(sg["actuation"]["torque_limits_Nm"])
print("torque limits [N m]:", lim)
eb, eg = np.degrees(b.qerr_true_rad.to_numpy()), np.degrees(g.qerr_true_rad.to_numpy())
t = g.t.to_numpy()
# first step at which the gated arm is >20 deg worse than baseline while the baseline is < 30 deg
bad = np.flatnonzero((eg - eb > 20) & (t > 1))
t0 = t[bad[0]] if bad.size else None
print("first time gated error exceeds baseline by >20 deg:", t0)
i0 = int(np.searchsorted(t, t0 - 0.3)) if t0 else 0
sl = slice(i0, i0 + 160)  # 0.8 s window at 5 ms
print(f"\n window {t[sl][0]:.2f}-{t[sl][-1]:.2f} s: (every 20 ms)")
print(f"{'t':>6s}{'err_b':>7s}{'err_g':>7s} | {'u0_x/l':>7s}{'raw_x/l':>8s}{'mask':>5s}{'cmd_x/l':>8s} | rotor-sat(g) act_req range")
for k in range(sl.start, sl.stop, 4):
    ax = 0
    print(f"{t[k]:6.3f}{eb[k]:7.1f}{eg[k]:7.1f} | {g['tau0_x'][k]/lim[0]:7.2f}{g['raw_residual_x'][k]/lim[0]:8.2f}"
          f"{int(g['output_gate_mask_x'][k]):5d}{g['tau_command_x'][k]/lim[0]:8.2f} | "
          f"{int(g['rotor_saturated_any'][k])}   {min(g[f'actuator_requested_{i}'][k] for i in range(4)):.3f}..{max(g[f'actuator_requested_{i}'][k] for i in range(4)):.3f}")
print("\nfraction of samples in the window with any rotor saturated  gated:",
      round(float(g.rotor_saturated_any[sl].mean()), 3), " baseline:", round(float(b.rotor_saturated_any[sl].mean()), 3))
# is the torque box the binding constraint or the rotors?  compare command inside the box but rotors saturated
cmd = g[[f"tau_command_{a}" for a in "xyz"]].to_numpy()
inside = np.all(np.abs(cmd) < lim - 1e-12, axis=1)
rot = g.rotor_saturated_any.to_numpy().astype(bool)
print(f"whole run: samples with rotor saturation while the torque command is strictly inside the box: {np.mean(rot & inside):.3f} "
      f"(box-saturated share {np.mean(~inside):.3f}, rotor-saturated {rot.mean():.3f})")

"""Closed-loop bias of the v3/v4 quadrature lock-in estimate (written before any 6-DOF pilot run).

Small-angle axis model at the dither frequency: J th'' + k_w th' + (k_q/2) th = d, since e_q ~ th/2.
With d = A sin wt and z_c = LPF(omega cos wt) -> A Im H(jw)/2, H = jw / (k - J w^2 + j k_w w):
    s_quad = -2 j w z_c / A = j w^2 (J w^2 - k) / ((k - J w^2)^2 + (k_w w)^2)     (k = k_q/2)
Open loop (k = k_w = 0) gives j/J. The known-controller estimate inverts the complex response:
    1/H = k_w + j (J w^2 - k)/w   ->   J = (w Im(1/H) + k) / w^2
"""
from __future__ import annotations

import sys
from pathlib import Path

import mujoco
import numpy as np

sys.path.insert(0, r"C:\Research\papers\ACC2027_Gate_Residual_Control\src")
from gra_control.platforms.drone import SPECS, _free_joint  # noqa: E402

W = 2 * np.pi * np.array([9.0, 11.0, 13.0])
CASES = {"x2": {"quat (wn 4,4,3.5)": (4, 4, 3.5), "6dof tuned (wn 20,20,17.5)": (20, 20, 17.5)},
         "cf2-rotor": {"quat (wn 4,4,3.5)": (4, 4, 3.5), "6dof tuned (wn 24,24,20.4)": (24, 24, 20.4)}}
lines = ["| platform | loop | true j/J (x,y,z) | predicted quadrature s_hat (x,y,z) | v4 target m=1/s_hat | correct m=J/j |",
         "|---|---|---|---|---|---|"]
for p, loops in CASES.items():
    m = mujoco.MjModel.from_xml_path(str(SPECS[p].model))
    _, b, _, _ = _free_joint(m)
    j = m.body_inertia[b].copy()
    R = np.zeros(9)
    mujoco.mju_quat2Mat(R, m.body_iquat[b])
    R = R.reshape(3, 3)
    J = np.diag(R @ np.diag(j) @ R.T)
    for name, wn in loops.items():
        wn = np.asarray(wn, float)
        k = 0.5 * 2.0 * j * wn ** 2
        kw = 2.0 * 0.95 * wn * j
        s = j * W ** 2 * (J * W ** 2 - k) / ((k - J * W ** 2) ** 2 + (kw * W) ** 2)
        f = lambda v: ", ".join(f"{x:.2f}" for x in v)  # noqa: E731
        lines.append(f"| {p} | {name} | {f(j / J)} | {f(s)} | {f(np.clip(1 / s, 0.33, 3.0))} | {f(J / j)} |")
out = "\n".join(lines)
print(out)
Path(__file__).with_name("PREDICTION_dither_bias.md").write_text(
    "# Predicted closed-loop bias of the quadrature dither estimate (pre-run)\n\n" + (__doc__ or "") + "\n\n" + out + "\n",
    encoding="utf-8")

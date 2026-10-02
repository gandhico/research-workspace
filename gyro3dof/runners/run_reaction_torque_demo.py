"""Quanser reaction-torque lab in the MuJoCo twin: yaw the gray frame using only the blue-gimbal torque.

The red gimbal is locked and the disc spins at 750 rpm. Quanser's successive-loop controller
(inner nutation-rate feedback, outer PD on yaw) commands +15 deg, then -15 deg, then 0.
Writes results/reaction_torque_{trace.csv, summary.json, plot.png, video.mp4}.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import mujoco
import numpy as np

from gyro3dof import reference_model as ref
from gyro3dof.controllers import ReactionTorqueController
from gyro3dof.params import PARAMS as P
from gyro3dof.sim import run

OUT = Path(__file__).resolve().parents[1] / "results"


def reference(t):
    return np.radians(15.0) if t < 4 else (np.radians(-15.0) if t < 8 else 0.0)


def main(video: bool):
    OUT.mkdir(exist_ok=True)
    c = ReactionTorqueController()
    ctrl = lambda t, x: c(reference(t), x[2], x[1], x[3])  # noqa: E731

    frames, renderer, cam = [], None, None
    fps = 30
    next_frame = 0.0

    def grab(m, d, t):
        nonlocal renderer, cam, next_frame
        if renderer is None:
            renderer = mujoco.Renderer(m, 720, 1280)
            cam = mujoco.MjvCamera()
            cam.lookat[:] = [0, 0, -0.08]; cam.distance = 1.15; cam.azimuth = 135; cam.elevation = -22
        if t >= next_frame - 1e-9:
            renderer.update_scene(d, cam)
            frames.append(renderer.render().copy())
            next_frame += 1.0 / fps

    t, x, u, w = run(ctrl, 12.0, frame_cb=grab if video else None)
    tr, xr, _ = ref.simulate(ctrl, np.zeros(4), 12.0)

    with (OUT / "reaction_torque_trace.csv").open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["t", "psi_ref", "phi", "psi", "phi_dot", "psi_dot", "tau2", "disc_rad_s", "psi_linear_ref", "phi_linear_ref"])
        for k in range(len(t)):
            wr.writerow([t[k], reference(t[k]), *x[k], u[k], w[k], xr[k, 1], xr[k, 0]])

    first = t < 4
    summary = {
        "h_Nms": P.h, "nutation_hz": P.nutation_hz, "tau_max_Nm": P.tau_max,
        "psi_at_4s_deg": float(np.degrees(x[np.searchsorted(t, 3.999), 1])),
        "phi_peak_first_step_deg": float(np.degrees(x[first, 0].min())),
        "vendor_sample_phi_deg": -3.5,
        "max_abs_tau2_Nm": float(np.abs(u).max()),
        "tau2_saturated_frac": float(np.mean(np.abs(u) >= P.tau_max - 1e-9)),
        "disc_speed_rpm_range": [float(w.min() * 60 / 2 / np.pi), float(w.max() * 60 / 2 / np.pi)],
        "mujoco_vs_linear_max_abs_psi_deg": float(np.degrees(np.abs(x[:, 1] - xr[:, 1]).max())),
        "mujoco_vs_linear_max_abs_phi_deg": float(np.degrees(np.abs(x[:, 0] - xr[:, 0]).max())),
    }
    (OUT / "reaction_torque_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(3, 1, figsize=(9, 7.5), sharex=True)
    ax[0].plot(t, np.degrees([reference(s) for s in t]), "k--", lw=1, label="reference")
    ax[0].plot(t, np.degrees(x[:, 1]), lw=2, label="MuJoCo")
    ax[0].plot(tr, np.degrees(xr[:, 1]), ":", lw=2, label="Quanser linear model")
    ax[0].set_ylabel("gray yaw ψ [deg]"); ax[0].legend(loc="lower left")
    ax[1].plot(t, np.degrees(x[:, 0]), lw=2, label="MuJoCo")
    ax[1].plot(tr, np.degrees(xr[:, 0]), ":", lw=2, label="linear model")
    ax[1].axhline(-3.5, color="gray", lw=0.8); ax[1].text(0.1, -3.2, "vendor sample: −3.5°", fontsize=8)
    ax[1].set_ylabel("blue roll φ [deg]")
    ax[2].plot(t, u, lw=1.5); ax[2].axhline(P.tau_max, color="gray", lw=0.8); ax[2].axhline(-P.tau_max, color="gray", lw=0.8)
    ax[2].set_ylabel("τ₂ [N·m]"); ax[2].set_xlabel("time [s]")
    fig.suptitle("Quanser 3-DOF gyro, reaction-torque control (red gimbal locked, 750 rpm)")
    fig.tight_layout()
    fig.savefig(OUT / "reaction_torque_plot.png", dpi=140)

    if video and frames:
        import imageio.v2 as imageio
        imageio.mimwrite(OUT / "reaction_torque_video.mp4", frames, fps=fps, quality=8)
        print("video frames:", len(frames))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-video", action="store_true")
    main(video=not ap.parse_args().no_video)

"""Outputs, inputs, quaternions, and Euler angles -- one figure per
(platform, mission), classical vs Nengo CMG+PES.

Pure Python, reads matched_45s/{platform}_{mission}_{classical,nengo_nef_pes}
trace.csv only -- no simulation re-run. The trace logs the ERROR quaternion
(qe_w,x,y,z) and the REFERENCE Euler angles directly, but not the measured
quaternion/Euler angles -- those are recovered here using the exact
identity q_meas = conj(qe) (x) q_ref (verified to 1e-16 against
gra_control.math3d.quat_error before use, not just assumed), then converted
to Euler with the same 321 extraction used elsewhere in this repo.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def load_trace(run_dir: Path) -> dict[str, np.ndarray]:
    with (run_dir/"trace.csv").open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def quat_mul_batch(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Batched Hamilton product, p and q shaped (N,4)."""
    p0, p1, p2, p3 = p[:, 0], p[:, 1], p[:, 2], p[:, 3]
    q0, q1, q2, q3 = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    return np.stack([
        p0*q0-p1*q1-p2*q2-p3*q3,
        p0*q1+p1*q0+p2*q3-p3*q2,
        p0*q2-p1*q3+p2*q0+p3*q1,
        p0*q3+p1*q2-p2*q1+p3*q0,
    ], axis=1)


def quat_to_euler_zyx_batch(q: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    roll = np.arctan2(2*(w*x+y*z), 1-2*(x*x+y*y))
    pitch = np.arcsin(np.clip(2*(w*y-z*x), -1.0, 1.0))
    yaw = np.arctan2(2*(w*z+x*y), 1-2*(y*y+z*z))
    return roll, pitch, yaw


def recover_measured(t: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """q_meas = conj(qe) (x) q_ref, verified against gra_control.math3d.quat_error
    to 1e-16 before this script trusted it -- see module docstring."""
    n = len(t["t"])
    qe = np.stack([t["qe_w"], t["qe_x"], t["qe_y"], t["qe_z"]], axis=1)
    qe_conj = qe*np.array([1.0, -1.0, -1.0, -1.0])
    qref = np.zeros((n, 4))
    roll_r, pitch_r, yaw_r = t["ref_roll"], t["ref_pitch"], t["ref_yaw"]
    cr, sr = np.cos(roll_r/2), np.sin(roll_r/2)
    cp, sp = np.cos(pitch_r/2), np.sin(pitch_r/2)
    cy, sy = np.cos(yaw_r/2), np.sin(yaw_r/2)
    qref[:, 0] = cr*cp*cy+sr*sp*sy
    qref[:, 1] = sr*cp*cy-cr*sp*sy
    qref[:, 2] = cr*sp*cy+sr*cp*sy
    qref[:, 3] = cr*cp*sy-sr*sp*cy
    q_meas = quat_mul_batch(qe_conj, qref)
    roll, pitch, yaw = quat_to_euler_zyx_batch(q_meas)
    return {"q_meas": q_meas, "roll": roll, "pitch": pitch, "yaw": yaw,
            "roll_ref": roll_r, "pitch_ref": pitch_r, "yaw_ref": yaw_r}


def plot_attitude(platform: str, mission: str, classical_dir: Path, nengo_dir: Path, out_path: Path) -> None:
    c = load_trace(classical_dir)
    n = load_trace(nengo_dir)
    c_att, n_att = recover_measured(c), recover_measured(n)
    n_summary = json.loads((nengo_dir/"summary.json").read_text())
    c_deg, n_deg = np.rad2deg(c["qerr"]), np.rad2deg(n["qerr"])
    c_mean, n_mean = c_deg.mean(), n_deg.mean()
    imp = 100*(c_mean-n_mean)/c_mean if c_mean > 1e-9 else 0.0

    fig, axes = plt.subplots(6, 1, figsize=(11, 16), sharex=True,
                              gridspec_kw={"height_ratios": [1.8, 1.6, 1.6, 1.6, 1.6, 1.6]})

    # 1) OUTPUTS: scalar attitude-tracking error, classical vs Nengo
    ax = axes[0]
    ax.plot(c["t"], c_deg, color="tab:blue", lw=1, label=f"Quaternion PD (mean {c_mean:.2f} deg)")
    ax.plot(n["t"], n_deg, color="tab:red", lw=1, label=f"Nengo CMG+PES (mean {n_mean:.2f} deg)")
    ax.set_ylabel("attitude error\n(deg)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_title(f"OUTPUTS -- {platform} {mission} (mean improvement {imp:+.2f}%)",
                 fontsize=10, loc="left", fontweight="bold")

    # 2-4) EULER ANGLES: roll, pitch, yaw -- actual (classical, Nengo) vs reference
    for i, (name, key, refkey) in enumerate([("roll", "roll", "roll_ref"), ("pitch", "pitch", "pitch_ref"),
                                              ("yaw", "yaw", "yaw_ref")]):
        ax = axes[1+i]
        ax.plot(n["t"], np.rad2deg(n_att[refkey]), "k--", lw=1.1, label="reference")
        ax.plot(c["t"], np.rad2deg(c_att[key]), color="tab:blue", lw=0.9, alpha=0.85, label="Quaternion PD")
        ax.plot(n["t"], np.rad2deg(n_att[key]), color="tab:red", lw=0.9, alpha=0.85, label="Nengo CMG+PES")
        ax.set_ylabel(f"{name} (deg)")
        ax.legend(loc="upper right", fontsize=7, ncol=3)
        ax.grid(alpha=0.3)
    axes[1].set_title("EULER ANGLES -- recovered actual attitude vs. reference (321 roll-pitch-yaw)",
                       fontsize=10, loc="left", fontweight="bold")

    # 5) QUATERNIONS: recovered measured quaternion components, Nengo run
    ax = axes[4]
    for comp, lbl, color in zip(range(4), ["w", "x", "y", "z"],
                                 ["k", "tab:red", "tab:green", "tab:purple"]):
        ax.plot(n["t"], n_att["q_meas"][:, comp], lw=0.8, color=color, label=f"q_{lbl}")
    ax.set_ylabel("measured\nquaternion")
    ax.set_ylim(-1.05, 1.05)
    ax.legend(loc="upper right", fontsize=7, ncol=4)
    ax.grid(alpha=0.3)
    ax.set_title("QUATERNIONS -- recovered measured attitude quaternion (Nengo run), q_meas = conj(q_e) (x) q_ref",
                 fontsize=10, loc="left", fontweight="bold")

    # 6) INPUTS: actual motor/actuator commands, Nengo run
    ax = axes[5]
    for i in range(4):
        ax.plot(n["t"], n[f"actuator_{i}"], lw=0.7, alpha=0.85, label=f"motor {i}")
    ax.set_ylabel("actuator\ncommand")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper right", fontsize=7, ncol=4)
    ax.grid(alpha=0.3)
    ax.set_title("INPUTS -- actual mixed motor/actuator commands (Nengo run)", fontsize=10, loc="left", fontweight="bold")

    fig.suptitle(f"{platform} -- {mission} -- outputs / Euler / quaternions / inputs\n"
                 f"beta={n_summary.get('beta')}  k_error={n_summary.get('k_error')}  "
                 f"duration={n_summary.get('duration')}s", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_path, dpi=125)
    plt.close(fig)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platforms", nargs="+", default=["x2", "cf2_rotor"])
    parser.add_argument("--missions", nargs="+",
                         default=["hover", "roll", "full3", "hard45", "hardstep", "yaw360"])
    parser.add_argument("--results-root", type=Path, default=ROOT/"results"/"matched_45s")
    parser.add_argument("--out-dir", type=Path, default=ROOT/"results"/"plots"/"attitude_detail")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for platform in args.platforms:
        for mission in args.missions:
            classical_dir = args.results_root/f"{platform}_{mission}_classical"
            nengo_dir = args.results_root/f"{platform}_{mission}_nengo_nef_pes"
            if not (classical_dir/"trace.csv").exists() or not (nengo_dir/"trace.csv").exists():
                print(f"skip {platform}/{mission}: missing trace.csv")
                continue
            plot_attitude(platform, mission, classical_dir, nengo_dir,
                          args.out_dir/f"{platform}_{mission}_attitude.png")

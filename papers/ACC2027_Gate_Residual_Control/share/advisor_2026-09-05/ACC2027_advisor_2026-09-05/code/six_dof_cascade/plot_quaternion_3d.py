"""Quaternion/Euler detail tracking (matching the earlier attitude-detail
style: recover q_meas via q_meas = conj(qe) (x) q_des, plot quaternion
components + Euler angles) plus 3D trajectory plots, for all 4 X2 6-DOF
missions, classical vs CMG-PES vs CMG-eprop_anneal. Reads trace.csv only.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import numpy as np

ROOT = Path(__file__).resolve().parent
MISSIONS = ["hover3d", "waypoint_step", "circle_xy", "full6_stress"]
DIRS = {
    "classical": lambda m: ROOT/"results"/"optionA"/f"{m}_classical",
    "CMG-PES": lambda m: ROOT/"results"/"optionA"/f"{m}_pes",
    "CMG-eprop_anneal": lambda m: ROOT/"results"/"eprop_x2"/m,
}
COLORS = {"classical": "tab:blue", "CMG-PES": "tab:red", "CMG-eprop_anneal": "tab:brown"}
OUT = ROOT/"results"/"plots"
OUT.mkdir(parents=True, exist_ok=True)


def load(d: Path) -> dict[str, np.ndarray]:
    with (d/"trace.csv").open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def quat_mul(p, q):
    p0, p1, p2, p3 = p
    q0, q1, q2, q3 = q
    return np.array([
        p0*q0-p1*q1-p2*q2-p3*q3,
        p0*q1+p1*q0+p2*q3-p3*q2,
        p0*q2-p1*q3+p2*q0+p3*q1,
        p0*q3+p1*q2-p2*q1+p3*q0,
    ])


def quat_to_euler(q):
    w, x, y, z = q
    roll = np.arctan2(2*(w*x+y*z), 1-2*(x*x+y*y))
    sinp = np.clip(2*(w*y-z*x), -1.0, 1.0)
    pitch = np.arcsin(sinp)
    yaw = np.arctan2(2*(w*z+x*y), 1-2*(y*y+z*z))
    return np.array([roll, pitch, yaw])


def recover_q_meas(trace: dict) -> np.ndarray:
    """q_meas = conj(qe) (x) q_des, per eq_x/y/z + qdes_w/x/y/z columns."""
    n = len(trace["t"])
    q_meas = np.zeros((n, 4))
    for i in range(n):
        eq = np.array([trace["eq_x"][i], trace["eq_y"][i], trace["eq_z"][i]])
        qe0 = np.sqrt(max(0.0, 1.0-np.dot(eq, eq)))
        qe = np.array([qe0, eq[0], eq[1], eq[2]])
        qe_conj = np.array([qe[0], -qe[1], -qe[2], -qe[3]])
        q_des = np.array([trace["qdes_w"][i], trace["qdes_x"][i], trace["qdes_y"][i], trace["qdes_z"][i]])
        q_meas[i] = quat_mul(qe_conj, q_des)
    return q_meas


if __name__ == "__main__":
    for mission in MISSIONS:
        traces = {name: load(fn(mission)) for name, fn in DIRS.items()}
        q_meas = {name: recover_q_meas(t) for name, t in traces.items()}
        euler = {name: np.array([quat_to_euler(q) for q in qm]) for name, qm in q_meas.items()}
        q_des_euler = np.array([quat_to_euler(np.array([traces["CMG-PES"]["qdes_w"][i],
                                                          traces["CMG-PES"]["qdes_x"][i],
                                                          traces["CMG-PES"]["qdes_y"][i],
                                                          traces["CMG-PES"]["qdes_z"][i]]))
                                 for i in range(len(traces["CMG-PES"]["t"]))])

        # ---- Figure A: quaternion + Euler detail tracking ----
        fig, axes = plt.subplots(4, 2, figsize=(14, 11), sharex=True)
        qlabels = ["w", "x", "y", "z"]
        for row in range(4):
            ax = axes[row, 0]
            ax.plot(traces["CMG-PES"]["t"], traces["CMG-PES"][f"qdes_{qlabels[row]}"], "k--", lw=1, label="q_des")
            for name in DIRS:
                ax.plot(traces[name]["t"], q_meas[name][:, row], color=COLORS[name], lw=0.7, alpha=0.85, label=name)
            ax.set_ylabel(f"q_{qlabels[row]}")
            if row == 0:
                ax.legend(loc="upper right", fontsize=7, ncol=4)
                ax.set_title(f"QUATERNION TRACKING -- X2, {mission}", fontsize=10, loc="left", fontweight="bold")
        eulerlabels = ["roll", "pitch", "yaw"]
        for row in range(3):
            ax = axes[row, 1]
            ax.plot(traces["CMG-PES"]["t"], np.rad2deg(q_des_euler[:, row]), "k--", lw=1, label="reference")
            for name in DIRS:
                ax.plot(traces[name]["t"], np.rad2deg(euler[name][:, row]), color=COLORS[name], lw=0.7, alpha=0.85, label=name)
            ax.set_ylabel(f"{eulerlabels[row]} (deg)")
            if row == 0:
                ax.legend(loc="upper right", fontsize=7, ncol=4)
                ax.set_title(f"EULER ANGLE TRACKING -- X2, {mission}", fontsize=10, loc="left", fontweight="bold")
        axes[3, 1].plot(traces["CMG-PES"]["t"], traces["CMG-PES"]["pos_err"], color="tab:red", lw=0.8, label="CMG-PES")
        axes[3, 1].plot(traces["classical"]["t"], traces["classical"]["pos_err"], color="tab:blue", lw=0.8, label="classical")
        axes[3, 1].plot(traces["CMG-eprop_anneal"]["t"], traces["CMG-eprop_anneal"]["pos_err"], color="tab:brown", lw=0.8, label="CMG-eprop_anneal")
        axes[3, 1].set_ylabel("|pos err| (m)")
        axes[3, 1].legend(loc="upper right", fontsize=7)
        axes[3, 1].set_xlabel("time (s)")
        axes[3, 0].set_xlabel("time (s)")
        for ax in axes.flat:
            ax.grid(alpha=0.3)
        fig.suptitle(f"X2 6-DOF cascade -- {mission}: quaternion + Euler detail tracking\n"
                     "classical vs CMG-PES vs CMG-eprop_anneal, measured q recovered via q_meas = conj(qe) (x) q_des",
                     fontsize=12)
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        fig.savefig(OUT/f"{mission}_quaternion_detail.png", dpi=125)
        plt.close(fig)
        print(f"wrote {OUT / f'{mission}_quaternion_detail.png'}")

        # ---- Figure B: 3D trajectory ----
        fig = plt.figure(figsize=(10, 9))
        ax = fig.add_subplot(111, projection="3d")
        ax.plot(traces["classical"]["x_ref"], traces["classical"]["y_ref"], traces["classical"]["z_ref"],
                "k--", lw=1.3, label="reference")
        for name in DIRS:
            tr = traces[name]
            ax.plot(tr["x"], tr["y"], tr["z"], color=COLORS[name], lw=1.3, alpha=0.85, label=name)
            ax.scatter([tr["x"][0]], [tr["y"][0]], [tr["z"][0]], color=COLORS[name], marker="o", s=40)
            ax.scatter([tr["x"][-1]], [tr["y"][-1]], [tr["z"][-1]], color=COLORS[name], marker="^", s=50)
        ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)"); ax.set_zlabel("z (m)")
        ax.set_title(f"3D TRAJECTORY -- X2, {mission}\n(o = start, ^ = end)", fontsize=12)
        ax.legend(loc="upper left", fontsize=8)
        fig.tight_layout()
        fig.savefig(OUT/f"{mission}_trajectory_3d.png", dpi=125)
        plt.close(fig)
        print(f"wrote {OUT / f'{mission}_trajectory_3d.png'}")
